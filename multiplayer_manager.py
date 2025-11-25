# multiplayer_manager.py

from typing import Optional, Dict, Any, Callable
from network_server import NetworkServer
from network_client import NetworkClient
from wingedsheep.carcassonne.carcassonne_game import CarcassonneGame
from wingedsheep.carcassonne.tile_sets.tile_sets import TileSet
from wingedsheep.carcassonne.tile_sets.supplementary_rules import SupplementaryRule
from wingedsheep.carcassonne.objects.game_phase import GamePhase

class MultiplayerManager:
    
    def __init__(self):
        self.server: Optional[NetworkServer] = None
        self.client: Optional[NetworkClient] = None
        self.is_host = False
        self.is_connected = False
        self.game: Optional[CarcassonneGame] = None
        self.game_callbacks: Dict[str, Callable] = {}
        
    def set_callback(self, event_type: str, callback: Callable):
        """Đăng ký callback cho các sự kiện game"""
        self.game_callbacks[event_type] = callback
    
    def _trigger_callback(self, event_type: str, data: Any = None):
        """Kích hoạt callback"""
        if event_type in self.game_callbacks:
            try:
                self.game_callbacks[event_type](data)
            except Exception as e:
                print(f"Error in callback {event_type}: {e}")
    
    def host_game(self, port: int = 5000, host_name: str = "Host") -> Dict[str, Any]:
        """Bắt đầu host game - host chỉ là server, không phải player"""
        try:
            self.server = NetworkServer(port)
            game_id = self.server.start_server(host_name)
            
            if game_id:
                self.is_host = True
                self.is_connected = False  # Host chưa connected như player
                self.game = None  # Host không có game local
                
                print(f"Server hosted successfully! Game ID: {game_id}")
                self._trigger_callback('game_hosted', {'game_id': game_id, 'port': port})
                
                return {'success': True, 'game_id': game_id, 'port': port}
            else:
                return {'success': False, 'error': 'Failed to start server'}
                
        except Exception as e:
            print(f"Error hosting game: {e}")
            return {'success': False, 'error': str(e)}
    
    def join_game(self, host_ip: str, game_id: str, player_name: str, port: int = 5000) -> Dict[str, Any]:
        try:
            self.client = NetworkClient()
            
            self.client.set_message_handler('game_started', self._on_game_started)
            self.client.set_message_handler('game_update', self._on_game_update)
            self.client.set_message_handler('game_finished', self._on_game_finished)
            self.client.set_message_handler('player_joined', self._on_player_joined)
            self.client.set_message_handler('player_left', self._on_player_left)
            
            result = self.client.connect_to_game(host_ip, port, game_id, player_name)
            
            if result['success']:
                self.is_connected = True
                self._trigger_callback('game_joined', result)
                return result
            else:
                self.client = None
                return result
                
        except Exception as e:
            print(f"Error joining game: {e}")
            return {'success': False, 'error': str(e)}
    
    def join_own_game(self, player_name: str) -> Dict[str, Any]:
        """Host join vào game của chính mình như một player"""
        if not self.is_host or not self.server:
            return {'success': False, 'error': 'Not hosting a game'}
        
        # Join vào server của chính mình
        return self.join_game('localhost', self.server.game_id, player_name, self.server.port)
    
    def _on_game_started(self, message: Dict[str, Any]):
        print("Multiplayer game started!")
        
        if self.client:
            players = message.get('players', [])
            
            try:
                self.game = CarcassonneGame(
                    players=len(players),
                    tile_sets=[TileSet.BASE, TileSet.THE_RIVER, TileSet.INNS_AND_CATHEDRALS],
                    supplementary_rules=[SupplementaryRule.ABBOTS, SupplementaryRule.FARMERS]
                )
                print(f"Game created with {len(players)} players")
                
                game_state = message.get('game_state')
                if game_state:
                    print("Received game state from server")
                    
            except Exception as e:
                print(f"Error creating game: {e}")
                self.game = CarcassonneGame(
                    players=2,
                    tile_sets=[TileSet.BASE],
                    supplementary_rules=[]
                )
            
        self._trigger_callback('game_started', message)
    
    def _on_game_update(self, message: Dict[str, Any]):
        game_state = message.get('game_state', {})
        
        if self.game and game_state:
            try:
                # Cập nhật current player
                if 'current_player' in game_state:
                    self.game.state.current_player = game_state['current_player']
                    
                # Cập nhật scores
                if 'scores' in game_state:
                    self.game.state.scores = game_state['scores']
                    
                # Cập nhật meeples
                if 'meeples' in game_state:
                    self.game.state.meeples = game_state['meeples']
                
                # Cập nhật phase
                if 'phase' in game_state:
                    phase_str = game_state['phase']
                    print(f">>> Updating phase to: {phase_str}")
                    # Convert string back to Enum
                    if phase_str == "tiles":
                        self.game.state.phase = GamePhase.TILES
                    elif phase_str == "meeples":
                        self.game.state.phase = GamePhase.MEEPLES
                    else:
                        print(f"Warning: Unknown phase string: {phase_str}")
                
                # Cập nhật next_tile - QUAN TRỌNG!
                if 'next_tile' in game_state:
                    next_tile_data = game_state['next_tile']
                    if next_tile_data:
                        print(f">>> Next tile info: {next_tile_data}")
                        # Deserialize next_tile từ server
                        deserialized_next_tile = self._deserialize_tile(next_tile_data)
                        if deserialized_next_tile:
                            self.game.state.next_tile = deserialized_next_tile
                            print("CLIENT: Next tile updated successfully")
                    else:
                        self.game.state.next_tile = None
                        print(">>> No next tile")
                
                # Cập nhật board - QUAN TRỌNG!
                if 'board' in game_state:
                    board_data = game_state['board']
                    print(f"CLIENT: Received board update with {len(board_data)} rows")
                    self._deserialize_board(board_data)
                
                # Cập nhật last_tile_action - QUAN TRỌNG CHO MEEPLE PHASE!
                if 'last_tile_action' in game_state:
                    action_data = game_state['last_tile_action']
                    if action_data:
                        print(f"CLIENT: Updating last_tile_action... Data: {action_data.get('type')}")
                        last_action = self._deserialize_action(action_data)
                        if last_action:
                            self.game.state.last_tile_action = last_action
                            print(f"CLIENT: last_tile_action updated: {type(last_action).__name__}")
                            if hasattr(last_action, 'tile'):
                                print(f"CLIENT: last_tile_action.tile: {last_action.tile}")
                            else:
                                print("CLIENT: last_tile_action HAS NO TILE ATTRIBUTE!")
                        else:
                            print("CLIENT: Failed to deserialize last_tile_action")
                    else:
                        print("CLIENT: last_tile_action data is None")
                        self.game.state.last_tile_action = None
                else:
                    print("CLIENT: 'last_tile_action' key missing in game_state")
                
                # Cập nhật tiles remaining
                if 'tiles_remaining' in game_state:
                    tiles_remaining = game_state['tiles_remaining']
                    print(f">>> Tiles remaining: {tiles_remaining}")
                    # Update deck size if needed
                    
                # Cập nhật placed_meeples - QUAN TRỌNG!
                if 'placed_meeples' in game_state:
                    placed_meeples_data = game_state['placed_meeples']
                    # print(f"CLIENT: Received placed_meeples data: {placed_meeples_data}")
                    if placed_meeples_data:
                        self.game.state.placed_meeples = self._deserialize_placed_meeples(placed_meeples_data)
                        # print(f"CLIENT: Updated placed_meeples. Count: {[len(p) for p in self.game.state.placed_meeples]}")
                
                print(f">>> Game state fully updated. Current player: {self.game.state.current_player}")
                
            except Exception as e:
                print(f"Error updating game state: {e}")
                import traceback
                traceback.print_exc()
        
        self._trigger_callback('game_updated', message)

    def _deserialize_placed_meeples(self, placed_meeples_data):
        """Deserialize list of list of meeple dicts to MeeplePosition objects"""
        from wingedsheep.carcassonne.objects.meeple_position import MeeplePosition
        from wingedsheep.carcassonne.objects.meeple_type import MeepleType
        from wingedsheep.carcassonne.objects.coordinate_with_side import CoordinateWithSide
        from wingedsheep.carcassonne.objects.coordinate import Coordinate
        from wingedsheep.carcassonne.objects.side import Side
        
        deserialized_meeples = []
        
        for player_meeples_data in placed_meeples_data:
            player_meeples = []
            for meeple_data in player_meeples_data:
                try:
                    # Get MeepleType
                    meeple_type_str = meeple_data.get('meeple_type')
                    meeple_type = MeepleType[meeple_type_str] if meeple_type_str else MeepleType.NORMAL
                    
                    # Get CoordinateWithSide
                    cws_data = meeple_data.get('coordinate_with_side', {})
                    coord_data = cws_data.get('coordinate', {})
                    side_str = cws_data.get('side')
                    
                    row = coord_data.get('row', 0)
                    col = coord_data.get('column', 0)
                    
                    coordinate = Coordinate(row, col)
                    side = Side[side_str] if side_str else Side.TOP
                    
                    cws = CoordinateWithSide(coordinate, side)
                    
                    meeple_pos = MeeplePosition(meeple_type, cws)
                    player_meeples.append(meeple_pos)
                    
                except Exception as e:
                    print(f"Error deserializing meeple: {e}")
            
            deserialized_meeples.append(player_meeples)
            
        return deserialized_meeples
    
    def _str_to_side(self, side_str: str):
        """Convert string to Side enum"""
        from wingedsheep.carcassonne.objects.side import Side
        try:
            # Handle special cases if needed, but usually it's direct mapping
            for side in Side:
                if side.value == side_str:
                    return side
            return None
        except:
            return None

    def _deserialize_connection(self, conn_data):
        """Convert dict to Connection object"""
        from wingedsheep.carcassonne.objects.connection import Connection
        try:
            a = self._str_to_side(conn_data.get('a'))
            b = self._str_to_side(conn_data.get('b'))
            if a and b:
                return Connection(a, b)
            return None
        except:
            return None

    def _deserialize_tile(self, tile_data):
        """Deserialize tile from server data"""
        try:
            if not tile_data:
                return None
            
            # print(f"CLIENT: Deserializing tile: {tile_data.get('description', 'Unknown')}")
            
            # Import cần thiết
            from wingedsheep.carcassonne.objects.tile import Tile
            from wingedsheep.carcassonne.objects.farmer_connection import FarmerConnection
            
            tile = Tile()
            
            # Copy basic properties
            if 'turns' in tile_data:
                tile.turns = tile_data['turns']
            
            if 'description' in tile_data:
                tile.description = tile_data['description']
                
            if 'image' in tile_data:
                tile.image = tile_data['image']
            
            if 'shield' in tile_data:
                tile.shield = tile_data['shield']
                
            if 'chapel' in tile_data:
                tile.chapel = tile_data['chapel']
                
            if 'flowers' in tile_data:
                tile.flowers = tile_data['flowers']
                
            if 'cathedral' in tile_data:
                tile.cathedral = tile_data['cathedral']

            # Deserialize complex properties
            
            # 1. Road (List[Connection])
            if 'road' in tile_data and tile_data['road']:
                tile.road = []
                for conn_data in tile_data['road']:
                    conn = self._deserialize_connection(conn_data)
                    if conn:
                        tile.road.append(conn)
            
            # 2. River (List[Connection])
            if 'river' in tile_data and tile_data['river']:
                tile.river = []
                for conn_data in tile_data['river']:
                    conn = self._deserialize_connection(conn_data)
                    if conn:
                        tile.river.append(conn)
                        
            # 3. Grass (List[Side])
            if 'grass' in tile_data and tile_data['grass']:
                tile.grass = []
                for side_str in tile_data['grass']:
                    side = self._str_to_side(side_str)
                    if side:
                        tile.grass.append(side)
                        
            # 4. City (List[List[Side]])
            if 'city' in tile_data and tile_data['city']:
                tile.city = []
                for city_part in tile_data['city']:
                    deserialized_part = []
                    for side_str in city_part:
                        side = self._str_to_side(side_str)
                        if side:
                            deserialized_part.append(side)
                    if deserialized_part:
                        tile.city.append(deserialized_part)
            
            # 5. Inn (List[Side])
            if 'inn' in tile_data and tile_data['inn']:
                tile.inn = []
                for side_str in tile_data['inn']:
                    side = self._str_to_side(side_str)
                    if side:
                        tile.inn.append(side)
                        
            # 6. Unplayable Sides (List[Side])
            if 'unplayable_sides' in tile_data and tile_data['unplayable_sides']:
                tile.unplayable_sides = []
                for side_str in tile_data['unplayable_sides']:
                    side = self._str_to_side(side_str)
                    if side:
                        tile.unplayable_sides.append(side)

            # 7. Farms (List[FarmerConnection]) - Complex!
            # FarmerConnection has 'tile_field' (int) and 'farmer_positions' (List[FarmerPosition])
            # FarmerPosition has 'center' (Side), 'left' (Side), 'right' (Side)
            # For now, we might skip deep farmer deserialization if not strictly needed for placement validation
            # Placement validation mainly uses grass, city, road, river. 
            # Farmers are for scoring/meeple placement.
            # TODO: Implement full farmer deserialization if needed for meeple placement
            
            # print(f"CLIENT: Tile deserialized successfully - desc: {getattr(tile, 'description', 'None')}")
            return tile
            
        except Exception as e:
            print(f"CLIENT: Error deserializing tile: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _deserialize_board(self, board_data):
        """Deserialize board from server data"""
        try:
            print(f"CLIENT: Receiving board data...")
            print(f"CLIENT: Board dimensions: {len(board_data)} x {len(board_data[0]) if board_data else 0}")
            
            tiles_received = 0
            for row_idx, row_data in enumerate(board_data):
                for col_idx, tile_data in enumerate(row_data):
                    if tile_data is not None:
                        tiles_received += 1
                        print(f"CLIENT: Received tile at [{row_idx}][{col_idx}]: {tile_data}")
            
            print(f"CLIENT: Total tiles received: {tiles_received}")
            
            # Cập nhật board state
            if hasattr(self.game.state, 'board'):
                print("CLIENT: Updating local board state...")
                # Clear current board
                for row_idx, row_data in enumerate(board_data):
                    if row_idx < len(self.game.state.board):
                        for col_idx, tile_data in enumerate(row_data):
                            if col_idx < len(self.game.state.board[row_idx]):
                                if tile_data is None:
                                    self.game.state.board[row_idx][col_idx] = None
                                else:
                                    # Deserialize tile object properly
                                    print(f"CLIENT: Processing tile at [{row_idx}][{col_idx}]: {tile_data}")
                                    deserialized_tile = self._deserialize_tile(tile_data)
                                    if deserialized_tile:
                                        self.game.state.board[row_idx][col_idx] = deserialized_tile
                                        print(f"CLIENT: Tile created and placed at [{row_idx}][{col_idx}]")
                                    else:
                                        print(f"CLIENT: Failed to deserialize tile at [{row_idx}][{col_idx}]")
                
                print(f"CLIENT: Board deserialized successfully")
            else:
                print("CLIENT: ERROR - No board attribute in game state")
                
        except Exception as e:
            print(f"CLIENT: Error deserializing board: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_game_finished(self, message: Dict[str, Any]):
        self._trigger_callback('game_finished', message)
    
    def _on_player_joined(self, message: Dict[str, Any]):
        self._trigger_callback('player_joined', message)
    
    def _on_player_left(self, message: Dict[str, Any]):
        self._trigger_callback('player_left', message)
    
    def send_action(self, action) -> bool:
        """Chỉ clients mới có thể gửi action"""
        print(f">>> MultiplayerManager.send_action called")
        print(f">>> Is host: {self.is_host}")
        print(f">>> Is connected: {self.is_connected}")
        print(f">>> Action type: {type(action).__name__}")
        
        if self.is_host:
            print(">>> ERROR: Host cannot send actions - host is server only!")
            return False
        
        if not self.is_connected or not self.client:
            print(">>> ERROR: Not connected as client!")
            return False
        
        # Chỉ clients mới gửi action
        print(">>> Sending action as CLIENT")
        action_data = self._serialize_action(action)
        print(f">>> Serialized action: {action_data}")
        
        message = {
            'type': 'game_action',
            'action': action_data
        }
        
        # THÊM LOG ĐỂ KIỂM TRA DOUBLE SEND
        print(f"🚨 SENDING ACTION - Action ID: {id(action)}")
        print(f"🚨 Message ID: {id(message)}")
        
        result = self.client._send_message(message)
        print(f">>> Client send result: {result}")
        
        print(f"🚨 ACTION SENT COMPLETED - Action ID: {id(action)}")
        return result
    
    def _serialize_action(self, action) -> Dict[str, Any]:
        """Chuyển action thành dict để gửi qua network"""
        import pickle
        import base64
        
        try:
            # Serialize action object bằng pickle
            pickled_action = pickle.dumps(action)
            encoded_action = base64.b64encode(pickled_action).decode('utf-8')
            
            action_data = {
                'type': type(action).__name__,
                'pickled_data': encoded_action
            }
            
            print(f">>> Serialized action with pickle: {type(action).__name__}")
            return action_data
            
        except Exception as e:
            print(f">>> Error serializing action with pickle: {e}")
            return {'type': type(action).__name__, 'error': 'serialization_failed'}

    def _deserialize_action(self, action_data: Dict[str, Any]):
        """Deserialize action from dict using pickle/base64"""
        import pickle
        import base64
        
        action_type = action_data.get('type')
        # print(f">>> CLIENT: Deserializing action type: {action_type}")
        
        if 'pickled_data' in action_data:
            try:
                encoded_data = action_data['pickled_data']
                pickled_data = base64.b64decode(encoded_data.encode('utf-8'))
                action = pickle.loads(pickled_data)
                # print(f">>> CLIENT: Successfully deserialized with pickle: {type(action).__name__}")
                return action
            except Exception as e:
                print(f">>> CLIENT: Error deserializing with pickle: {e}")
                return None
        
        print(f"No pickled data found for action type: {action_type}")
        return None
    
    def get_game(self) -> Optional[CarcassonneGame]:
        return self.game
    
    def get_connection_info(self) -> Dict[str, Any]:
        info = {
            'is_connected': self.is_connected,
            'is_host': self.is_host,
            'has_game': self.game is not None
        }
        
        if self.is_host and self.server:
            info.update(self.server.get_status())
        elif not self.is_host and self.client:
            info.update(self.client.get_status())
        
        return info
    
    def disconnect(self):
        self.is_connected = False
        
        if self.server:
            self.server.stop_server()
            self.server = None
        
        if self.client:
            self.client.disconnect()
            self.client = None
        
        self.game = None
        self.is_host = False
        
        self._trigger_callback('disconnected', {})
        print("Disconnected from multiplayer game")
    
    def is_my_turn(self) -> bool:
        """Kiểm tra có phải lượt của mình không"""
        if self.is_host:
            print(">>> is_my_turn: Host never has turns")
            return False
            
        if not self.game:
            print(">>> is_my_turn: No game object")
            return False
        
        current_player = self.game.state.current_player
        print(f">>> is_my_turn: Current player = {current_player}")
        
        if self.client:
            # Client kiểm tra player_id
            print(f">>> is_my_turn: Client check - current_player == {self.client.player_id}? {current_player == self.client.player_id}")
            return current_player == self.client.player_id
        
        print(">>> is_my_turn: No valid client connection")
        return False
