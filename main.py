# main.py

import pygame
import math
import os
import wingedsheep
from wingedsheep.carcassonne.carcassonne_game import CarcassonneGame
from wingedsheep.carcassonne.tile_sets.tile_sets import TileSet
from wingedsheep.carcassonne.tile_sets.supplementary_rules import SupplementaryRule
from wingedsheep.carcassonne.objects.meeple_type import MeepleType
from wingedsheep.carcassonne.objects.actions.meeple_action import MeepleAction
from wingedsheep.carcassonne.objects.actions.tile_action import TileAction

# --- Import all shared CONSTANTS from resources.py ---
from resources import (
    TILE_SIZE, WINDOW_HEIGHT, WINDOW_WIDTH, PREVIEW_TILE_X, PREVIEW_TILE_Y, SNAP_THRESHOLD,
    MENU_FONT_SIZE, BUTTON_COLOR, HOVER_COLOR, TEXT_COLOR, BG_COLOR,
    STATE_PRE_GAME, STATE_PLAYER_INPUT, STATE_GAME_RUNNING, STATE_PAUSED, STATE_GAME_OVER,
    PLAYER_PANEL_WIDTH, PLAYER_PANEL_HEIGHT,
    # Pause Button and Slider Constants
    PAUSE_BUTTON_X, PAUSE_BUTTON_Y, PAUSE_BUTTON_WIDTH, PAUSE_BUTTON_HEIGHT, 
    PAUSE_MENU_CENTER_X, SLIDER_WIDTH, SLIDER_HEIGHT, SLIDER_KNOB_RADIUS, MUSIC_SLIDER_Y,
    CENTER_OFFSET_X, CENTER_OFFSET_Y
)
# --- Import drawing functions from new UI files (Non-circular) ---
from ui_manager import (
    play_music, draw_pre_game_screen, draw_player_input_screen, draw_player_info, 
    draw_phase_indicator, draw_tiles_remaining, draw_pause_menu, draw_game_over_screen,
    draw_pause_button, draw_host_game_screen, draw_join_game_screen # Correctly imported
)
from game_view import draw_board
from multiplayer_manager import MultiplayerManager

# --- COORDINATE & OFFSET LOGIC (FIXED CENTERING) ---
BOARD_CENTER_X = WINDOW_WIDTH // 2
BOARD_CENTER_Y = WINDOW_HEIGHT // 2
# CENTER_OFFSET_X and Y are now imported from resources.
global music_volume 

# --- HELPER FUNCTION (Defined here to be passed to UI/View) ---
def phase_name_for_state(game_state):
    """Gets the name of the current game phase."""
    p = getattr(game_state , 'phase' , None)
    return getattr(p,'name',str(p)).upper() if p is not None else "UNKNOWN"

# --- INITIALIZATION (Pygame Objects defined here) ---
pygame.init()
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Carcassonne – Minimal Pygame UI")

images_path = os.path.join(wingedsheep.__path__[0], 'carcassonne', 'resources', 'images')
# Load wood texture
wood_texture = pygame.image.load(
    os.path.join(images_path, "wood.jpg")
).convert()
wood_texture = pygame.transform.scale(wood_texture, (WINDOW_WIDTH, WINDOW_HEIGHT))

font = pygame.font.SysFont(None, 26)

ghost_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
ghost_surface.fill((100, 200, 100, 100))

# --- GAME STATE VARIABLES ---
GAME_STATE = STATE_PRE_GAME 
selected_player_count = 2
player_input_buttons = {}
pause_buttons = {}
music_volume = 0.5 # Starting volume at 50%
is_dragging_slider = False # Flag for dragging the knob

# Multiplayer states
STATE_HOST_GAME = "HOST_GAME"
STATE_JOIN_GAME = "JOIN_GAME"
STATE_MULTIPLAYER_WAITING = "MULTIPLAYER_WAITING"

# Multiplayer variables
multiplayer_manager = MultiplayerManager()
host_ip_input = ""
game_id_input = ""
player_name_input = "Player"
host_name_input = "Host"
multiplayer_error = ""
current_input_field = None

# Setup multiplayer callbacks
def on_game_started(data):
    global GAME_STATE, game
    print("=== GAME STARTED CALLBACK ===")
    print(f"Data: {data}")
    game = multiplayer_manager.get_game()
    if game:
        print(f"Game object created successfully: {type(game)}")
        print(f"Current player: {game.state.current_player}")
        print(f"Players count: {len(game.state.scores)}")
        GAME_STATE = STATE_GAME_RUNNING
        print("Switched to GAME_RUNNING state")
    else:
        print("ERROR: No game object received!")
    print("=== END CALLBACK ===")

def on_game_updated(data):
    global game
    print("=== GAME UPDATED CALLBACK ===")
    game = multiplayer_manager.get_game()
    if game:
        print(f"Game updated. Current player: {game.state.current_player}")
        print(f"Scores: {game.state.scores}")
    print("=== END UPDATE CALLBACK ===")

def on_game_finished(data):
    global GAME_STATE
    GAME_STATE = STATE_GAME_OVER

def on_player_joined(data):
    print(f"Player joined: {data}")

def on_player_left(data):
    print(f"Player left: {data}")

def on_disconnected(data):
    global GAME_STATE, game
    print("Disconnected from multiplayer game")
    GAME_STATE = STATE_PRE_GAME
    game = None

multiplayer_manager.set_callback('game_started', on_game_started)
multiplayer_manager.set_callback('game_updated', on_game_updated)
multiplayer_manager.set_callback('game_finished', on_game_finished)
multiplayer_manager.set_callback('player_joined', on_player_joined)
multiplayer_manager.set_callback('player_left', on_player_left)
multiplayer_manager.set_callback('disconnected', on_disconnected)

game = None
is_dragging = False
drag_pos = (PREVIEW_TILE_X, PREVIEW_TILE_Y)
snap_action = None 

# --- RUNNING LOOP ---
#play_music() 
# pygame.mixer.music.set_volume(music_volume) 
clock = pygame.time.Clock()
running = True

while running:
    mouse_x, mouse_y = pygame.mouse.get_pos()
    
    # 1. CHECK FOR MULTIPLAYER GAME START (HOST)
    if GAME_STATE == STATE_MULTIPLAYER_WAITING and multiplayer_manager.is_host:
        pass  # Host chỉ chờ players join, không cần check game start
    
    # 2. CHECK FOR GAME END
    if GAME_STATE == STATE_GAME_RUNNING and game and game.is_finished():
        game.state = game.finalise_game_state() # Final score calculation
        GAME_STATE = STATE_GAME_OVER
        continue

    # --- 3. EVENT HANDLING ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Escape key for Pause/Resume
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if GAME_STATE == STATE_GAME_RUNNING:
                GAME_STATE = STATE_PAUSED
            elif GAME_STATE == STATE_PAUSED:
                GAME_STATE = STATE_GAME_RUNNING
        
        # Handle text input for join game screen
        if event.type == pygame.KEYDOWN and GAME_STATE == STATE_JOIN_GAME and current_input_field:
            if event.key == pygame.K_BACKSPACE:
                if current_input_field == 'ip' and host_ip_input:
                    host_ip_input = host_ip_input[:-1]
                elif current_input_field == 'id' and game_id_input:
                    game_id_input = game_id_input[:-1]
                elif current_input_field == 'name' and player_name_input:
                    player_name_input = player_name_input[:-1]
            elif event.unicode.isprintable() and len(event.unicode) == 1:
                if current_input_field == 'ip' and len(host_ip_input) < 15:
                    host_ip_input += event.unicode
                elif current_input_field == 'id' and len(game_id_input) < 6:
                    game_id_input += event.unicode.upper()
                elif current_input_field == 'name' and len(player_name_input) < 20:
                    player_name_input += event.unicode
        
        # Handle text input for host game screen
        if event.type == pygame.KEYDOWN and GAME_STATE == STATE_HOST_GAME and current_input_field == 'host_name':
            if event.key == pygame.K_BACKSPACE:
                if host_name_input:
                    host_name_input = host_name_input[:-1]
            elif event.unicode.isprintable() and len(event.unicode) == 1:
                if len(host_name_input) < 20:
                    host_name_input += event.unicode
        
        # Handle Clicks for Menus/States
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # --- Pause Button Click Handler ---
            if GAME_STATE == STATE_GAME_RUNNING:
                pause_button_rect = pygame.Rect(PAUSE_BUTTON_X, PAUSE_BUTTON_Y, PAUSE_BUTTON_WIDTH, PAUSE_BUTTON_HEIGHT)
                if pause_button_rect.collidepoint(mouse_x, mouse_y):
                    GAME_STATE = STATE_PAUSED
                    continue
            
            # --- PAUSE MENU Click Logic ---
            elif GAME_STATE == STATE_PAUSED:
                # 1. Resume Button
                if 'btn_resume' in pause_buttons and pause_buttons['btn_resume'].collidepoint(mouse_x, mouse_y):
                    GAME_STATE = STATE_GAME_RUNNING
                
                # 2. Volume Slider Start Dragging
                elif 'slider_rect' in pause_buttons:
                    slider_rect = pause_buttons['slider_rect']
                    # Define a slightly larger clickable area around the knob for easy grabbing
                    knob_area = pygame.Rect(
                        slider_rect.x - SLIDER_KNOB_RADIUS, 
                        slider_rect.y - SLIDER_KNOB_RADIUS, 
                        SLIDER_WIDTH + 2 * SLIDER_KNOB_RADIUS, 
                        SLIDER_HEIGHT + 2 * SLIDER_KNOB_RADIUS
                    )
                    
                    if knob_area.collidepoint(mouse_x, mouse_y):
                        is_dragging_slider = True

            if GAME_STATE == STATE_PRE_GAME:
                if 'btn_single_player' in player_input_buttons and player_input_buttons['btn_single_player'].collidepoint(mouse_x, mouse_y):
                    GAME_STATE = STATE_PLAYER_INPUT
                elif 'btn_host_game' in player_input_buttons and player_input_buttons['btn_host_game'].collidepoint(mouse_x, mouse_y):
                    GAME_STATE = STATE_HOST_GAME
                elif 'btn_join_game' in player_input_buttons and player_input_buttons['btn_join_game'].collidepoint(mouse_x, mouse_y):
                    GAME_STATE = STATE_JOIN_GAME
            
            elif GAME_STATE == STATE_PLAYER_INPUT:
                for count, rect in player_input_buttons['player_count_buttons'].items():
                    if rect.collidepoint(mouse_x, mouse_y):
                        selected_player_count = count
                        
                if 'btn_begin_game' in player_input_buttons and player_input_buttons['btn_begin_game'].collidepoint(mouse_x, mouse_y):
                    game = CarcassonneGame(
                        players=selected_player_count,
                        tile_sets=[TileSet.BASE, TileSet.THE_RIVER, TileSet.INNS_AND_CATHEDRALS],
                        supplementary_rules=[SupplementaryRule.ABBOTS, SupplementaryRule.FARMERS]
                    )
                    GAME_STATE = STATE_GAME_RUNNING
            
            elif GAME_STATE == STATE_HOST_GAME:
                if 'btn_start_host' in player_input_buttons and player_input_buttons['btn_start_host'].collidepoint(mouse_x, mouse_y):
                    # Start hosting
                    if host_name_input.strip():
                        result = multiplayer_manager.host_game(host_name=host_name_input.strip())
                        if result['success']:
                            GAME_STATE = STATE_MULTIPLAYER_WAITING
                        else:
                            multiplayer_error = result.get('error', 'Failed to host game')
                    else:
                        multiplayer_error = "Please enter your name"
                elif 'btn_copy' in player_input_buttons and player_input_buttons['btn_copy'].collidepoint(mouse_x, mouse_y):
                    # Copy connection info to clipboard
                    connection_info = multiplayer_manager.get_connection_info()
                    game_id = connection_info.get('game_id', '')
                    
                    # Get IP address
                    import socket
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        s.connect(("8.8.8.8", 80))
                        host_ip = s.getsockname()[0]
                        s.close()
                    except:
                        host_ip = "localhost"
                    
                    copy_text = f"Game ID: {game_id}\nHost IP: {host_ip}\nPort: 5000"
                    
                    # Try to copy to clipboard using tkinter
                    try:
                        import tkinter as tk
                        root = tk.Tk()
                        root.withdraw()  # Hide the window
                        root.clipboard_clear()
                        root.clipboard_append(copy_text)
                        root.update()  # Required to finalize clipboard
                        root.destroy()
                        print("Connection info copied to clipboard!")
                    except:
                        print("Could not copy to clipboard")
                        print(f"Connection info:\n{copy_text}")
                        
                elif 'host_name_input' in player_input_buttons and player_input_buttons['host_name_input'].collidepoint(mouse_x, mouse_y):
                    current_input_field = 'host_name'
                elif 'btn_back' in player_input_buttons and player_input_buttons['btn_back'].collidepoint(mouse_x, mouse_y):
                    GAME_STATE = STATE_PRE_GAME
                    multiplayer_error = ""
                    current_input_field = None
            
            elif GAME_STATE == STATE_JOIN_GAME:
                if 'btn_join' in player_input_buttons and player_input_buttons['btn_join'].collidepoint(mouse_x, mouse_y):
                    # Try to join game
                    if host_ip_input and game_id_input and player_name_input:
                        result = multiplayer_manager.join_game(host_ip_input, game_id_input, player_name_input)
                        if result['success']:
                            GAME_STATE = STATE_MULTIPLAYER_WAITING
                        else:
                            multiplayer_error = result.get('error', 'Failed to join game')
                    else:
                        multiplayer_error = "Please fill in all fields"
                elif 'btn_back' in player_input_buttons and player_input_buttons['btn_back'].collidepoint(mouse_x, mouse_y):
                    GAME_STATE = STATE_PRE_GAME
                    multiplayer_error = ""
                    host_ip_input = ""
                    game_id_input = ""
                    player_name_input = "Player"
                # Handle input field clicks
                elif 'ip_input' in player_input_buttons and player_input_buttons['ip_input'].collidepoint(mouse_x, mouse_y):
                    current_input_field = 'ip'
                elif 'id_input' in player_input_buttons and player_input_buttons['id_input'].collidepoint(mouse_x, mouse_y):
                    current_input_field = 'id'
                elif 'name_input' in player_input_buttons and player_input_buttons['name_input'].collidepoint(mouse_x, mouse_y):
                    current_input_field = 'name'
                else:
                    current_input_field = None
            
            elif GAME_STATE == STATE_MULTIPLAYER_WAITING:
                if 'btn_copy' in player_input_buttons and player_input_buttons['btn_copy'].collidepoint(mouse_x, mouse_y):
                    # Copy connection info to clipboard
                    connection_info = multiplayer_manager.get_connection_info()
                    game_id = connection_info.get('game_id', '')
                    
                    # Get IP address
                    import socket
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        s.connect(("8.8.8.8", 80))
                        host_ip = s.getsockname()[0]
                        s.close()
                    except:
                        host_ip = "localhost"
                    
                    copy_text = f"Game ID: {game_id}\nHost IP: {host_ip}\nPort: 5000"
                    
                    # Try to copy to clipboard using tkinter
                    try:
                        import tkinter as tk
                        root = tk.Tk()
                        root.withdraw()  # Hide the window
                        root.clipboard_clear()
                        root.clipboard_append(copy_text)
                        root.update()  # Required to finalize clipboard
                        root.destroy()
                        print("Connection info copied to clipboard!")
                    except:
                        print("Could not copy to clipboard")
                        print(f"Connection info:\n{copy_text}")
                        
                elif 'btn_back' in player_input_buttons and player_input_buttons['btn_back'].collidepoint(mouse_x, mouse_y):
                    multiplayer_manager.disconnect()
                    GAME_STATE = STATE_PRE_GAME
                    multiplayer_error = ""
            
            elif GAME_STATE == STATE_GAME_OVER:
                if 'btn_menu' in pause_buttons and pause_buttons['btn_menu'].collidepoint(mouse_x, mouse_y):
                    multiplayer_manager.disconnect()
                    GAME_STATE = STATE_PRE_GAME
                    game = None
                    is_dragging = False
                    selected_player_count = 2

        # Left Click Up - Tile Placement End/Slider Drag End
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if is_dragging_slider:
                is_dragging_slider = False # Stop dragging the slider
            
            if GAME_STATE == STATE_GAME_RUNNING and is_dragging:
                is_dragging = False
                if snap_action is not None:
                    if multiplayer_manager.is_connected and not multiplayer_manager.is_my_turn():
                        print("Not your turn!")
                    elif multiplayer_manager.is_host:
                        print("Host cannot play - you are the server!")
                    else:
                        if multiplayer_manager.is_connected:
                            # Chỉ gửi action, KHÔNG thực hiện local
                            print("🚨 UI: TILE DRAG END - Sending action to server...")
                            print(f"🚨 Action ID: {id(snap_action)}")
                            result = multiplayer_manager.send_action(snap_action)
                            print(f"🚨 UI: TILE DRAG END - Send result: {result}")
                        else:
                            # Single player mode - thực hiện local
                            print("🚨 UI: TILE DRAG END - Local game")
                            game.step(game.get_current_player(), snap_action)
                    snap_action = None
            
        # Continuous movement while dragging (Tile or Slider)
        elif event.type == pygame.MOUSEMOTION:
            mouse_x, mouse_y = event.pos

            # --- Slider Dragging Logic ---
            if is_dragging_slider and GAME_STATE == STATE_PAUSED:
                
                slider_x = PAUSE_MENU_CENTER_X - SLIDER_WIDTH // 2
                
                # Clamp the mouse X position to the slider track boundaries
                new_knob_x = max(slider_x, min(mouse_x, slider_x + SLIDER_WIDTH))
                
                # Calculate new volume (0.0 to 1.0)
                music_volume = (new_knob_x - slider_x) / SLIDER_WIDTH
                
                # Apply new volume to Pygame mixer
                pygame.mixer.music.set_volume(music_volume)

        # --- GAME RUNNING EVENTS (Tile Dragging, Rotation, Meeple) ---
        if GAME_STATE == STATE_GAME_RUNNING and game is not None:
            current_phase = phase_name_for_state(game.state)
            preview_rect = pygame.Rect(PREVIEW_TILE_X, PREVIEW_TILE_Y, TILE_SIZE, TILE_SIZE)

            # Left Click - Meeple Placement/Tile Drag Start
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Meeple Placement Logic 
                if "MEEP" in current_phase:
                    from resources import big_meeple_position_offsets, meeple_position_offsets, meeple_size, big_meeple_size
                    possible_actions = game.get_possible_actions()
                    for action in possible_actions:
                        if isinstance(action, MeepleAction):
                            cws = action.coordinate_with_side
                            col = cws.coordinate.column
                            row = cws.coordinate.row
                            side = cws.side

                            is_big = getattr(action, 'meeple_type', None) == MeepleType.BIG
                            offs = big_meeple_position_offsets if is_big else meeple_position_offsets
                            size = big_meeple_size if is_big else meeple_size

                            center_x = col * TILE_SIZE + CENTER_OFFSET_X + offs[side][0]
                            center_y = row * TILE_SIZE + CENTER_OFFSET_Y + offs[side][1]
                            dist = math.hypot(mouse_x - center_x, mouse_y - center_y)

                            if dist <= (size / 2) + 6:
                                # Check if multiplayer and if it's our turn
                                  if multiplayer_manager.is_connected and not multiplayer_manager.is_my_turn():
                                      pass
                                  elif multiplayer_manager.is_host:
                                      print("Host cannot play - you are the server!")
                                  else:
                                      if multiplayer_manager.is_connected:
                                          # Chỉ gửi action, KHÔNG thực hiện local
                                          print("🚨 UI: MEEPLE CLICK - Sending action to server...")
                                          print(f"🚨 Action ID: {id(action)}")
                                          result = multiplayer_manager.send_action(action)
                                          print(f"🚨 UI: MEEPLE CLICK - Send result: {result}")
                                      else:
                                          # Single player mode
                                          print("🚨 UI: MEEPLE CLICK - Local game")
                                          game.step(game.get_current_player(), action)
                                  break
                
                # Tile Drag Start Logic
                elif "MEEP" not in current_phase and game.state.next_tile is not None:
                    if preview_rect.collidepoint(mouse_x, mouse_y):
                        is_dragging = True
            
            # Continuous movement while dragging (Tile)
            elif event.type == pygame.MOUSEMOTION and is_dragging and "MEEP" not in current_phase:
                mouse_x, mouse_y = event.pos
                drag_pos = (mouse_x - TILE_SIZE // 2,
                            mouse_y - TILE_SIZE // 2)

            # Right Click - Rotation 
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                if "MEEP" not in current_phase and game.state.next_tile is not None:
                    if is_dragging or preview_rect.collidepoint(mouse_x, mouse_y):
                        game.state.next_tile.turns = (game.state.next_tile.turns + 1) % 4
                        snap_action = None

            # Key Down - Pass Meeple (P) 
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                
                if "MEEP" in current_phase or current_phase == "ABBOT":
                    possible_actions = game.get_possible_actions()
                    
                    # Pass Meeple/Abbot action
                    for i, action in enumerate(possible_actions):
                        
                        # Check for PassAction directly
                        if type(action).__name__ == 'PassAction':
                            if multiplayer_manager.is_connected and not multiplayer_manager.is_my_turn():
                                pass
                            elif multiplayer_manager.is_host:
                                print("Host cannot play - you are the server!")
                            else:
                                if multiplayer_manager.is_connected:
                                    # Chỉ gửi action, KHÔNG thực hiện local
                                    print("🚨 UI: PASS ACTION (P key) - Sending to server...")
                                    print(f"🚨 Action ID: {id(action)}")
                                    result = multiplayer_manager.send_action(action)
                                    print(f"🚨 UI: PASS ACTION (P key) - Send result: {result}")
                                else:
                                    # Single player mode
                                    print("🚨 UI: PASS ACTION (P key) - Local game")
                                    game.step(game.get_current_player(), action)
                            break
                        
    # --- 3. GAME LOGIC (Drag/Snap Calculations) ---
    snap_action = None 
    
    if GAME_STATE == STATE_GAME_RUNNING and game is not None:
        current_phase = phase_name_for_state(game.state)
        
        if is_dragging and "MEEP" not in current_phase:
            current_rotation = game.state.next_tile.turns
            possible_actions = game.get_possible_actions()
            closest_action = None
            min_dist = float('inf')

            for action in possible_actions:
                if (hasattr(action, 'coordinate') and hasattr(action, 'tile_rotations') and
                    action.tile_rotations == current_rotation):
                    board_mouse_x = mouse_x - CENTER_OFFSET_X
                    board_mouse_y = mouse_y - CENTER_OFFSET_Y
                    target_x_px = action.coordinate.column * TILE_SIZE + TILE_SIZE // 2
                    target_y_px = action.coordinate.row * TILE_SIZE + TILE_SIZE // 2
                    dist = math.dist((board_mouse_x, board_mouse_y), (target_x_px, target_y_px))

                    if dist < min_dist and dist < SNAP_THRESHOLD:
                        min_dist = dist
                        closest_action = action

            if closest_action is not None:
                # Snap to the closest valid spot
                snap_pos_x = closest_action.coordinate.column * TILE_SIZE + CENTER_OFFSET_X
                snap_pos_y = closest_action.coordinate.row * TILE_SIZE + CENTER_OFFSET_Y
                drag_pos = (snap_pos_x, snap_pos_y)
                snap_action = closest_action
            else:
                drag_pos = (mouse_x - TILE_SIZE // 2, mouse_y - TILE_SIZE // 2)
                snap_action = None
        else:
            drag_pos = (PREVIEW_TILE_X, PREVIEW_TILE_Y)


    # --- 4. DRAWING ---
    if GAME_STATE == STATE_PRE_GAME:
        player_input_buttons = draw_pre_game_screen(window, font, (mouse_x, mouse_y), wood_texture)
        
    elif GAME_STATE == STATE_PLAYER_INPUT:
        player_input_buttons = draw_player_input_screen(window, font, (mouse_x, mouse_y), selected_player_count, wood_texture)
    
    elif GAME_STATE == STATE_HOST_GAME:
        connection_info = multiplayer_manager.get_connection_info()
        game_id = connection_info.get('game_id')
        port = connection_info.get('port', 5000)
        connected_players = connection_info.get('connected_players', 0)
        player_names = connection_info.get('player_names', [])
        
        player_input_buttons = draw_host_game_screen(
            window, font, (mouse_x, mouse_y), wood_texture, 
            game_id, port, False, connected_players, player_names, host_name_input
        )
        
        # Display error if any
        if multiplayer_error:
            error_surf = font.render(multiplayer_error, True, (255, 0, 0))
            window.blit(error_surf, (WINDOW_WIDTH // 2 - error_surf.get_width() // 2, WINDOW_HEIGHT - 150))
    
    elif GAME_STATE == STATE_JOIN_GAME:
        player_input_buttons = draw_join_game_screen(window, font, (mouse_x, mouse_y), wood_texture, 
                                                   host_ip_input, game_id_input, player_name_input, multiplayer_error)
    
    elif GAME_STATE == STATE_MULTIPLAYER_WAITING:
        connection_info = multiplayer_manager.get_connection_info()
        if connection_info.get('is_host'):
            game_id = connection_info.get('game_id')
            port = connection_info.get('port', 5000)
            waiting = not connection_info.get('game_started', False)
            connected_players = connection_info.get('connected_players', 0)
            player_names = connection_info.get('player_names', [])
            
            player_input_buttons = draw_host_game_screen(
                window, font, (mouse_x, mouse_y), wood_texture, 
                game_id, port, waiting, connected_players, player_names, host_name_input
            )
        else:
            window.blit(wood_texture, (0, 0))
            wait_text = "Waiting for game to start..."
            wait_surf = font.render(wait_text, True, TEXT_COLOR)
            window.blit(wait_surf, (WINDOW_WIDTH // 2 - wait_surf.get_width() // 2, WINDOW_HEIGHT // 2))
            
            btn_back = pygame.Rect(0, 0, 150, 50)
            btn_back.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 100)
            is_hovered_back = btn_back.collidepoint(mouse_x, mouse_y)
            from ui_manager import draw_button
            draw_button(window, font, "Back", btn_back, is_hovered_back)
            player_input_buttons = {'btn_back': btn_back}
        
    elif GAME_STATE == STATE_GAME_RUNNING and game is not None:
        is_turn = multiplayer_manager.is_my_turn() if multiplayer_manager.is_connected else True
        draw_board(window, font, game.state, drag_pos, game, wood_texture, phase_name_for_state, ghost_surface, is_my_turn=is_turn) 
        draw_player_info(window, font, game.state)
        draw_phase_indicator(window, font, game.state, phase_name_for_state)
        
        # <<< THE FIX >>>: This line ensures the button is drawn.
        draw_pause_button(window, font, (mouse_x, mouse_y)) 
        
        draw_tiles_remaining(window, font, game.state) 
    
    elif GAME_STATE == STATE_PAUSED:
        is_turn = multiplayer_manager.is_my_turn() if multiplayer_manager.is_connected else True
        draw_board(window, font, game.state, drag_pos, game, wood_texture, phase_name_for_state, ghost_surface, is_my_turn=is_turn) 
        draw_player_info(window, font, game.state)
        draw_tiles_remaining(window, font, game.state)
        pause_buttons = draw_pause_menu(window, font, (mouse_x, mouse_y), music_volume)

    elif GAME_STATE == STATE_GAME_OVER:
        pause_buttons = draw_game_over_screen(window, font, game.state, (mouse_x, mouse_y), wood_texture)
        
    pygame.display.update()
    clock.tick(60)

pygame.quit()