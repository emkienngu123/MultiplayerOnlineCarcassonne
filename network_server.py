# network_server.py

import socket
import threading
import json
import time
import random
import string
from typing import Dict, List, Any, Optional
from wingedsheep.carcassonne.carcassonne_game import CarcassonneGame
from wingedsheep.carcassonne.tile_sets.tile_sets import TileSet
from wingedsheep.carcassonne.tile_sets.supplementary_rules import SupplementaryRule

class NetworkServer:
    def __init__(self, port: int = 5000):
        self.port = port
        self.host = '0.0.0.0'  
        self.socket = None
        self.clients: Dict[str, socket.socket] = {}  
        self.client_names: Dict[str, str] = {}  
        self.game: Optional[CarcassonneGame] = None
        self.game_id = self._generate_game_id()
        self.is_running = False
        self.max_players = 2
        self.game_started = False
        
    def _generate_game_id(self) -> str:
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    def start_server(self, host_player_name: str = "Host") -> str:
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.is_running = True
            
            print(f"Server started on {self.host}:{self.port}")
            print(f"Game ID: {self.game_id}")
            print(f"Waiting for players to connect...")
            
            threading.Thread(target=self._accept_connections, daemon=True).start()
            
            return self.game_id
            
        except Exception as e:
            print(f"Error starting server: {e}")
            return None
    
    def _accept_connections(self):
        while self.is_running:
            try:
                client_socket, address = self.socket.accept()
                print(f"New connection from {address}")
                
                client_id = f"player_{len(self.clients)}"
                self.clients[client_id] = client_socket
                
                threading.Thread(
                    target=self._handle_client, 
                    args=(client_id, client_socket), 
                    daemon=True
                ).start()
                
            except Exception as e:
                if self.is_running:
                    print(f"Error accepting connection: {e}")
    
    def _handle_client(self, client_id: str, client_socket: socket.socket):
        buffer = ""
        
        try:
            while self.is_running:
                client_socket.settimeout(1.0)  
                
                try:
                    data = client_socket.recv(4096)
                    if not data:
                        print(f">>> SERVER: Client {client_id} disconnected")
                        break
                    
                    buffer += data.decode('utf-8')
                    
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        
                        if line:  
                            try:
                                message = json.loads(line)
                                self._process_message(client_id, message)
                            except json.JSONDecodeError as e:
                                print(f">>> SERVER: JSON decode error from {client_id}: {e}")
                                
                except socket.timeout:
                    continue
                    
        except Exception as e:
            print(f"Error handling client {client_id}: {e}")
        finally:
            self._disconnect_client(client_id)
    
    def _process_message(self, client_id: str, message: Dict[str, Any]):
        msg_type = message.get('type')
        
        if msg_type == 'join_game':
            self._handle_join_game(client_id, message)
        elif msg_type == 'game_action':
            self._handle_game_action(client_id, message)
        elif msg_type == 'ping':
            self._send_to_client(client_id, {'type': 'pong'})
    
    def _handle_join_game(self, client_id: str, message: Dict[str, Any]):
        game_id = message.get('game_id')
        player_name = message.get('player_name', f'Player {len(self.clients)}')
        
        if game_id != self.game_id:
            self._send_to_client(client_id, {
                'type': 'join_response',
                'success': False,
                'error': 'Invalid game ID'
            })
            return
        
        if len(self.clients) > self.max_players:
            self._send_to_client(client_id, {
                'type': 'join_response',
                'success': False,
                'error': 'Game is full'
            })
            return
        
        if self.game_started:
            self._send_to_client(client_id, {
                'type': 'join_response',
                'success': False,
                'error': 'Game already started'
            })
            return
        
        self.client_names[client_id] = player_name
        
        # Player ID là index trong danh sách clients (bắt đầu từ 0)
        client_list = list(self.clients.keys())
        player_id = client_list.index(client_id)
        
        print(f"Player {player_name} joined as player {player_id}")
        
        self._send_to_client(client_id, {
            'type': 'join_response',
            'success': True,
            'player_id': player_id,
            'player_name': player_name
        })
        
        self._broadcast({
            'type': 'player_joined',
            'player_name': player_name,
            'total_players': len(self.clients)
        })
        
        if len(self.clients) >= self.max_players:
            self._start_game()
    
    def _start_game(self):
        if self.game_started:
            return
            
        print("Starting game with players:", list(self.client_names.values()))
        
        self.game = CarcassonneGame(
            players=len(self.clients),
            tile_sets=[TileSet.BASE, TileSet.THE_RIVER, TileSet.INNS_AND_CATHEDRALS],
            supplementary_rules=[SupplementaryRule.ABBOTS, SupplementaryRule.FARMERS]
        )
        
        self.game_started = True
        
        # Noti for all clients
        try:
            game_state_data = self._serialize_game_state()
            game_started_message = {
                'type': 'game_started',
                'players': list(self.client_names.values()),
                'game_state': game_state_data
            }
            self._broadcast(game_started_message)
            print(f"Game started successfully with {len(self.clients)} players")
            
            return game_started_message
            
        except Exception as e:
            print(f"Error starting game: {e}")
            fallback_message = {
                'type': 'game_started',
                'players': list(self.client_names.values())
            }
            self._broadcast(fallback_message)
            return fallback_message
    
    def _handle_game_action(self, client_id: str, message: Dict[str, Any]):
        print(f"🚨 SERVER: RECEIVED ACTION - Client: {client_id}")
        print(f"🚨 Message ID: {id(message)}")
        print(f" SERVER: Received game action from {client_id}")
        print(f" Message: {message}")
        
        if not self.game_started or not self.game:
            print(f" ERROR: Game not started or no game object")
            return
        
        current_player_index = self.game.state.current_player
        client_list = list(self.clients.keys())
        client_index = client_list.index(client_id)
        
        print(f" Current player index: {current_player_index}")
        print(f" Client index: {client_index}")
        print(f" Client list: {client_list}")
        
        if client_index != current_player_index:
            print(f" ERROR: Not client's turn!")
            self._send_to_client(client_id, {
                'type': 'error',
                'message': 'Not your turn'
            })
            return
        
        print(f"🚨 SERVER: PROCESSING ACTION - Client: {client_id}")
        
        try:
            action_data = message.get('action')
            if not action_data:
                raise ValueError("No action data provided")
                
            print(f" Deserializing action: {action_data.get('type', 'unknown')}")
            action = self._deserialize_action(action_data)
            if not action:
                raise ValueError("Failed to deserialize action")
                
            print(f"🚨 SERVER: APPLYING ACTION - Action ID: {id(action)}")
            print(f"Action deserialized: {type(action).__name__}")
            print(f"Game state BEFORE action:")
            print(f"    Current player: {self.game.state.current_player}")
            print(f"    Phase: {self.game.state.phase}")
            print(f"    Scores: {self.game.state.scores}")
            
            current_player = self.game.get_current_player()
            self.game.step(current_player, action)
            
            print(f"🚨 SERVER: ACTION APPLIED - Action ID: {id(action)}")
            print(f"Game state AFTER action:")
            print(f"    Current player: {self.game.state.current_player}")
            print(f"    Phase: {self.game.state.phase}")
            print(f"    Scores: {self.game.state.scores}")
            
            # Serialize game state
            print(f"Serializing game state...")
            game_state = self._serialize_game_state()
            update_message = {
                'type': 'game_update',
                'game_state': game_state
            }
            
            print(f"Broadcasting game update to {len(self.clients)} clients:")
            print(f"    Current player: {game_state.get('current_player')}")
            print(f"    Phase: {game_state.get('phase')}")
            print(f"    Tiles remaining: {game_state.get('tiles_remaining')}")
            print(f"    Board size: {len(game_state.get('board', []))} rows")
            
            print(f"🚨 SERVER: BROADCASTING UPDATE")
            self._broadcast(update_message)
            
            print(f"🚨 SERVER: ACTION COMPLETED - Client: {client_id}")
            print(f"Action processed successfully. New current player: {self.game.state.current_player}")
            
            if self.game.is_finished():
                print(f"Game finished! Sending final scores...")
                final_state = self.game.finalise_game_state()
                self._broadcast({
                    'type': 'game_finished',
                    'final_scores': final_state.scores
                })
                
        except Exception as e:
            print(f"🚨 SERVER: ERROR PROCESSING ACTION - Client: {client_id}")
            print(f"Error processing game action: {e}")
            import traceback
            traceback.print_exc()
            self._send_to_client(client_id, {
                'type': 'error',
                'message': f'Invalid action: {str(e)}'
            })
    
    def _serialize_game_state(self) -> Dict[str, Any]:
        if not self.game:
            print("No game to serialize")
            return {}
        
        print("Serializing game state...")
        state = self.game.state
        
        # Count non-None tiles on board
        board_tiles = 0
        for row in state.board:
            for tile in row:
                if tile is not None:
                    board_tiles += 1
        
        serialized_state = {
            'current_player': state.current_player,
            'scores': state.scores,
            'meeples': state.meeples,
            'phase': str(state.phase),
            'tiles_remaining': len(state.deck),
            'next_tile': self._serialize_tile(state.next_tile) if state.next_tile else None,
            'board': self._serialize_board(state.board),
            'placed_meeples': self._serialize_placed_meeples(state.placed_meeples),
            'last_tile_action': self._serialize_action_data(state.last_tile_action) if state.last_tile_action else None
        }
        
        print(f"Serialized game state:")
        print(f"    Current player: {serialized_state['current_player']}")
        print(f"    Scores: {serialized_state['scores']}")
        print(f"    Phase: {serialized_state['phase']}")
        print(f"    Tiles remaining: {serialized_state['tiles_remaining']}")
        print(f"    Board tiles: {board_tiles}")
        print(f"    Next tile: {'Yes' if serialized_state['next_tile'] else 'None'}")
        print(f"    Last tile action: {'Yes' if serialized_state['last_tile_action'] else 'None'}")
        
        return serialized_state
    
    def _serialize_tile(self, tile) -> Dict[str, Any]:
        if not tile:
            return None
        
        tile_data = {
            'turns': getattr(tile, 'turns', 0),
        }
        
        # Thêm nhiều thông tin hơn về tile
        if hasattr(tile, 'id'):
            tile_data['id'] = tile.id
        elif hasattr(tile, 'tile_id'):
            tile_data['id'] = tile.tile_id
        else:
            tile_data['id'] = str(type(tile).__name__)
        
        # Thêm description để biết loại tile
        if hasattr(tile, 'description'):
            tile_data['description'] = tile.description
            
        # Thêm image path
        if hasattr(tile, 'image'):
            tile_data['image'] = tile.image
            
        # Thêm các thuộc tính khác (Serialize properly!)
        if hasattr(tile, 'road'):
            tile_data['road'] = [c.to_json() for c in tile.road] if tile.road else []
            
        if hasattr(tile, 'city'):
            # City is List[List[Side]]
            tile_data['city'] = [[s.to_json() for s in city_part] for city_part in tile.city] if tile.city else []
            
        if hasattr(tile, 'grass'):
            tile_data['grass'] = [s.to_json() for s in tile.grass] if tile.grass else []
            
        if hasattr(tile, 'river'):
            tile_data['river'] = [c.to_json() for c in tile.river] if tile.river else []
            
        if hasattr(tile, 'inn'):
            tile_data['inn'] = [s.to_json() for s in tile.inn] if tile.inn else []
            
        if hasattr(tile, 'unplayable_sides'):
            tile_data['unplayable_sides'] = [s.to_json() for s in tile.unplayable_sides] if tile.unplayable_sides else []
            
        if hasattr(tile, 'shield'):
            tile_data['shield'] = tile.shield
            
        if hasattr(tile, 'chapel'):
            tile_data['chapel'] = tile.chapel
            
        if hasattr(tile, 'flowers'):
            tile_data['flowers'] = tile.flowers
            
        if hasattr(tile, 'cathedral'):
            tile_data['cathedral'] = tile.cathedral
            
        print(f"    Serialized tile: ID={tile_data['id']}, turns={tile_data['turns']}, desc={tile_data.get('description', 'None')}")
        return tile_data
    
    def _serialize_board(self, board) -> List[List[Any]]:
        print("Serializing board...")
        serialized_board = []
        tiles_count = 0
        
        for row_idx, row in enumerate(board):
            serialized_row = []
            for col_idx, tile in enumerate(row):
                if tile is None:
                    serialized_row.append(None)
                else:
                    tile_data = self._serialize_tile(tile)
                    serialized_row.append(tile_data)
                    tiles_count += 1
                    print(f"  Tile at [{row_idx}][{col_idx}]: {tile_data}")
            serialized_board.append(serialized_row)
        
        print(f"Board serialized: {len(board)} x {len(board[0]) if board else 0} grid, {tiles_count} tiles")
        return serialized_board
    
    def _serialize_placed_meeples(self, placed_meeples) -> List[List[Dict]]:
        serialized_meeples = []
        
        # placed_meeples is a list of lists (one list per player)
        for player_meeples in placed_meeples:
            player_serialized = []
            for meeple_pos in player_meeples:
                try:
                    # MeeplePosition has meeple_type and coordinate_with_side
                    meeple_data = {
                        'meeple_type': meeple_pos.meeple_type.name, # Enum name (NORMAL, BIG, ABBOT)
                        'coordinate_with_side': {
                            'coordinate': {
                                'row': meeple_pos.coordinate_with_side.coordinate.row,
                                'column': meeple_pos.coordinate_with_side.coordinate.column
                            },
                            'side': meeple_pos.coordinate_with_side.side.name # Enum name (TOP, BOTTOM, etc.)
                        }
                    }
                    player_serialized.append(meeple_data)
                except Exception as e:
                    print(f"Error serializing meeple: {e}")
            serialized_meeples.append(player_serialized)
            
        return serialized_meeples

    def _serialize_action_data(self, action) -> Dict[str, Any]:
        """Serialize action object to dict using pickle/base64"""
        import pickle
        import base64
        
        try:
            pickled_action = pickle.dumps(action)
            encoded_action = base64.b64encode(pickled_action).decode('utf-8')
            
            return {
                'type': type(action).__name__,
                'pickled_data': encoded_action
            }
        except Exception as e:
            print(f"Error serializing action: {e}")
            return None
    
    def _deserialize_action(self, action_data: Dict[str, Any]):
        import pickle
        import base64
        
        action_type = action_data.get('type')
        print(f">>> SERVER: Deserializing action type: {action_type}")
        
        if 'pickled_data' in action_data:
            try:
                encoded_data = action_data['pickled_data']
                pickled_data = base64.b64decode(encoded_data.encode('utf-8'))
                action = pickle.loads(pickled_data)
                print(f">>> SERVER: Successfully deserialized with pickle: {type(action).__name__}")
                return action
            except Exception as e:
                print(f">>> SERVER: Error deserializing with pickle: {e}")
                return None
        
        print(f"No pickled data found for action type: {action_type}")
        return None
    
    def _send_to_client(self, client_id: str, message: Dict[str, Any]):
        if client_id not in self.clients:
            print(f"Client {client_id} not found in clients list")
            return
            
        try:
            message_type = message.get('type', 'unknown')
            data = json.dumps(message).encode('utf-8') + b'\n'
            
            print(f"Sending '{message_type}' to {client_id} ({len(data)} bytes)")
            self.clients[client_id].send(data)
            print(f"Message sent successfully to {client_id}")
            
        except Exception as e:
            print(f"Error sending to client {client_id}: {e}")
            self._disconnect_client(client_id)
    
    def _broadcast(self, message: Dict[str, Any]):
        """Gửi message đến tất cả clients"""
        message_type = message.get('type', 'unknown')
        print(f"📡 BROADCASTING '{message_type}' to {len(self.clients)} clients:")
        
        for i, client_id in enumerate(list(self.clients.keys())):
            print(f" Sending to client {i}: {client_id}")
            self._send_to_client(client_id, message)
            
        print(f"Broadcast completed for '{message_type}'")
    
    def _disconnect_client(self, client_id: str):
        if client_id in self.clients:
            try:
                if self.clients[client_id]:
                    self.clients[client_id].close()
            except:
                pass
            del self.clients[client_id]
            
        if client_id in self.client_names:
            del self.client_names[client_id]
        
        print(f"Client {client_id} disconnected")
        
        # Thông báo cho các clients khác
        self._broadcast({
            'type': 'player_left',
            'total_players': len(self.clients)
        })
    
    def stop_server(self):
        """Dừng server"""
        self.is_running = False
        
        # Đóng tất cả client connections
        for client_socket in self.clients.values():
            try:
                client_socket.close()
            except:
                pass
        
        # Đóng server socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        print("Server stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Lấy trạng thái hiện tại của server"""
        return {
            'game_id': self.game_id,
            'port': self.port,
            'connected_players': len(self.clients),
            'max_players': self.max_players,
            'game_started': self.game_started,
            'player_names': list(self.client_names.values())
        }
