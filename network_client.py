# network_client.py

import socket
import threading
import json
import time
from typing import Dict, Any, Optional, Callable

class NetworkClient:
    def __init__(self):
        self.socket = None
        self.is_connected = False
        self.player_id = None
        self.player_name = None
        self.game_state = None
        self.message_handlers: Dict[str, Callable] = {}
        self.receive_thread = None
        
    def set_message_handler(self, message_type: str, handler: Callable):
        self.message_handlers[message_type] = handler
    
    def connect_to_game(self, host: str, port: int, game_id: str, player_name: str) -> Dict[str, Any]:
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)  
            
            print(f"Connecting to {host}:{port}...")
            self.socket.connect((host, port))
            self.is_connected = True
            
            self.receive_thread = threading.Thread(target=self._receive_messages, daemon=True)
            self.receive_thread.start()
            
            join_message = {
                'type': 'join_game',
                'game_id': game_id,
                'player_name': player_name
            }
            
            self._send_message(join_message)
            
            response = self._wait_for_message('join_response', timeout=5)
            
            if response and response.get('success'):
                self.player_id = response.get('player_id')
                self.player_name = response.get('player_name')
                print(f"Successfully joined game as {self.player_name} (ID: {self.player_id})")
                return {'success': True, 'player_id': self.player_id}
            else:
                error = response.get('error', 'Unknown error') if response else 'Connection timeout'
                print(f"Failed to join game: {error}")
                self.disconnect()
                return {'success': False, 'error': error}
                
        except Exception as e:
            print(f"Connection error: {e}")
            self.disconnect()
            return {'success': False, 'error': str(e)}
    
    def _receive_messages(self):
        buffer = ""
        
        while self.is_connected:
            try:
                self.socket.settimeout(1.0)  
                data = self.socket.recv(4096)
                if not data:
                    print(">>> CLIENT: No data received, server disconnected")
                    break
                
                buffer += data.decode('utf-8')
                
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    
                    if line: 
                        try:
                            message = json.loads(line)
                            self._handle_message(message)
                        except json.JSONDecodeError as e:
                            print(f">>> CLIENT: JSON decode error: {e}")
                            
            except socket.timeout:
                continue
            except Exception as e:
                if self.is_connected:
                    print(f"Error receiving message: {e}")
                break
        
        print(">>> CLIENT: Receive thread ending")
        self.is_connected = False
    
    def _handle_message(self, message: Dict[str, Any]):
        msg_type = message.get('type')
        
        if 'game_state' in message:
            self.game_state = message['game_state']
            print(f">>> CLIENT: Game state updated - current_player: {self.game_state.get('current_player')}")
        
        # Gọi handler tương ứng
        if msg_type in self.message_handlers:
            try:
                self.message_handlers[msg_type](message)
            except Exception as e:
                print(f"Error in message handler for {msg_type}: {e}")
        
        # Xử lý một số messages cơ bản
        if msg_type == 'game_started':
            print("Game started!")
            print("Players:", message.get('players', []))
            
        elif msg_type == 'game_update':
            print(">>> CLIENT: Game state updated!")
            game_state = message.get('game_state', {})
            print(f">>> CLIENT: New current player: {game_state.get('current_player')}")
            
        elif msg_type == 'game_finished':
            print("Game finished!")
            final_scores = message.get('final_scores', [])
            for i, score in enumerate(final_scores):
                print(f"Player {i+1}: {score} points")
                
        elif msg_type == 'player_joined':
            print(f"Player joined: {message.get('player_name')}")
            print(f"Total players: {message.get('total_players')}")
            
        elif msg_type == 'player_left':
            print(f"A player left. Total players: {message.get('total_players')}")
            
        elif msg_type == 'error':
            print(f"Server error: {message.get('message')}")
    
    def _send_message(self, message: Dict[str, Any]):
        if not self.is_connected or not self.socket:
            return False
        
        try:
            data = json.dumps(message).encode('utf-8') + b'\n'
            self.socket.send(data)
            return True
            
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    def _wait_for_message(self, message_type: str, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        start_time = time.time()
        received_message = None
        
        def temp_handler(message):
            nonlocal received_message
            received_message = message
        
        old_handler = self.message_handlers.get(message_type)
        self.message_handlers[message_type] = temp_handler
        
        while time.time() - start_time < timeout and received_message is None:
            time.sleep(0.1)
        
        if old_handler:
            self.message_handlers[message_type] = old_handler
        else:
            self.message_handlers.pop(message_type, None)
        
        return received_message
    
    def send_ping(self) -> bool:
        return self._send_message({'type': 'ping'})
    
    def disconnect(self):
        self.is_connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1)
        
        print("Disconnected from server")
    
    def get_status(self) -> Dict[str, Any]:
        return {
            'connected': self.is_connected,
            'player_id': self.player_id,
            'player_name': self.player_name,
            'has_game_state': self.game_state is not None
        }
    
    def get_game_state(self) -> Optional[Dict[str, Any]]:
        return self.game_state
