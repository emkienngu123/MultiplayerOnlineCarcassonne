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
    draw_pause_button # Correctly imported
)
from game_view import draw_board

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

game = None
is_dragging = False
drag_pos = (PREVIEW_TILE_X, PREVIEW_TILE_Y)
snap_action = None 

# --- RUNNING LOOP ---
play_music() 
pygame.mixer.music.set_volume(music_volume) 
clock = pygame.time.Clock()
running = True

while running:
    mouse_x, mouse_y = pygame.mouse.get_pos()
    
    # 1. CHECK FOR GAME END
    if GAME_STATE == STATE_GAME_RUNNING and game.is_finished():
        game.state = game.finalise_game_state() # Final score calculation
        GAME_STATE = STATE_GAME_OVER
        continue

    # --- 2. EVENT HANDLING ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Escape key for Pause/Resume
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if GAME_STATE == STATE_GAME_RUNNING:
                GAME_STATE = STATE_PAUSED
            elif GAME_STATE == STATE_PAUSED:
                GAME_STATE = STATE_GAME_RUNNING
        
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
                if 'btn_create_game' in player_input_buttons and player_input_buttons['btn_create_game'].collidepoint(mouse_x, mouse_y):
                    GAME_STATE = STATE_PLAYER_INPUT
            
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
            
            elif GAME_STATE == STATE_GAME_OVER:
                if 'btn_menu' in pause_buttons and pause_buttons['btn_menu'].collidepoint(mouse_x, mouse_y):
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
                    for action in possible_actions:
                        if isinstance(action, MeepleAction) and action.coordinate_with_side.side is None:
                            game.step(game.get_current_player(), action)
                            break
                        elif isinstance(action, TileAction) and current_phase == "ABBOT":
                             # This is the "no action" step for the abbot phase
                             if action.coordinate is None:
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
        
    elif GAME_STATE == STATE_GAME_RUNNING and game is not None:
        draw_board(window, font, game.state, drag_pos, game, wood_texture, phase_name_for_state, ghost_surface) 
        draw_player_info(window, font, game.state)
        draw_phase_indicator(window, font, game.state, phase_name_for_state)
        
        # <<< THE FIX >>>: This line ensures the button is drawn.
        draw_pause_button(window, font, (mouse_x, mouse_y)) 
        
        draw_tiles_remaining(window, font, game.state) 
    
    elif GAME_STATE == STATE_PAUSED:
        draw_board(window, font, game.state, drag_pos, game, wood_texture, phase_name_for_state, ghost_surface) 
        draw_player_info(window, font, game.state)
        draw_tiles_remaining(window, font, game.state)
        pause_buttons = draw_pause_menu(window, font, (mouse_x, mouse_y), music_volume)

    elif GAME_STATE == STATE_GAME_OVER:
        pause_buttons = draw_game_over_screen(window, font, game.state, (mouse_x, mouse_y), wood_texture)
        
    pygame.display.update()
    clock.tick(60)

pygame.quit()