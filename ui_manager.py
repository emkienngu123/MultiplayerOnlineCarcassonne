# ui_manager.py

import pygame
import os
import wingedsheep
from resources import (
    WINDOW_WIDTH, WINDOW_HEIGHT, BUTTON_COLOR, HOVER_COLOR, TEXT_COLOR, 
    PAUSE_MENU_CENTER_X, SLIDER_WIDTH, SLIDER_HEIGHT, SLIDER_KNOB_RADIUS, MUSIC_SLIDER_Y,
    PLAYER_PANEL_WIDTH, PLAYER_PANEL_HEIGHT, PAUSE_BUTTON_X, PAUSE_BUTTON_Y, PAUSE_BUTTON_HEIGHT, PAUSE_BUTTON_WIDTH
)

# --- RESOURCE PATHS ---
images_path = os.path.join(wingedsheep.__path__[0], 'carcassonne', 'resources', 'images')
MUSIC_FILE = os.path.join(wingedsheep.__path__[0], 'carcassonne', 'resources', 'music', 'medieval-music.mp3')


def play_music():
    """Starts the background music."""
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        if os.path.exists(MUSIC_FILE):
            pygame.mixer.music.load(MUSIC_FILE)
            pygame.mixer.music.play(-1)
        else:
            print(f"Warning: Music file not found at {MUSIC_FILE}")
    except pygame.error as e:
        print(f"Error playing music: {e}")

# --- DRAWING HELPERS ---
def draw_background(window, wood_texture):
    window.blit(wood_texture, (0, 0))

def draw_pause_button(window, font, mouse_pos):
    """Draws the clickable pause button in the corner."""
    
    # Define button rect using constants
    rect = pygame.Rect(PAUSE_BUTTON_X, PAUSE_BUTTON_Y, PAUSE_BUTTON_WIDTH, PAUSE_BUTTON_HEIGHT)
    is_hovered = rect.collidepoint(mouse_pos)
    
    # Draw the button
    draw_button(window, font, "Pause", rect, is_hovered)
    
    return rect
def draw_button(window, font, text, rect, is_hovered):
    color = HOVER_COLOR if is_hovered else BUTTON_COLOR
    pygame.draw.rect(window, color, rect, border_radius=5)
    surf = font.render(text, True, TEXT_COLOR)
    text_rect = surf.get_rect(center=rect.center)
    window.blit(surf, text_rect)

def draw_pre_game_screen(window, font, mouse_pos, wood_texture):
    """Draws the main title screen with the 'Create a New Game' button."""
    window.blit(wood_texture, (0, 0))
    logo_path = os.path.join(images_path, 'carcassonne-logo.png')
    
    try:
        logo_img = pygame.image.load(logo_path).convert_alpha()
        logo_rect = logo_img.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 4))
        window.blit(logo_img, logo_rect)
    except pygame.error:
        text_surf = font.render("CARCASSONNE", True, TEXT_COLOR)
        window.blit(text_surf, (WINDOW_WIDTH // 2 - text_surf.get_width() // 2, WINDOW_HEIGHT // 4 - 20))

    btn_rect = pygame.Rect(0, 0, 300, 60)
    btn_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
    is_hovered = btn_rect.collidepoint(mouse_pos)
    draw_button(window, font, "Create a New Game", btn_rect, is_hovered)
    return {'btn_create_game': btn_rect}

def draw_player_input_screen(window, font, mouse_pos, selected_player_count, wood_texture):
    """Draws the screen to select the number of players."""
    window.blit(wood_texture, (0, 0))
    
    text_surf = font.render("Select the number of players", True, TEXT_COLOR)
    window.blit(text_surf, (WINDOW_WIDTH // 2 - text_surf.get_width() // 2, WINDOW_HEIGHT // 2 - 100))
    
    player_options = [2, 3, 4, 5]
    option_width = 50
    option_height = 40
    total_width = len(player_options) * option_width + (len(player_options) - 1) * 10
    start_x = WINDOW_WIDTH // 2 - total_width // 2

    player_count_buttons = {}

    for i, count in enumerate(player_options):
        x = start_x + i * (option_width + 10)
        y = WINDOW_HEIGHT // 2 - 40
        
        option_rect = pygame.Rect(x, y, option_width, option_height)
        is_current = (count == selected_player_count)
        is_hovered = option_rect.collidepoint(mouse_pos)
        
        color = (0, 150, 0) if is_current else (60, 60, 60)
        if is_hovered and not is_current:
            color = (80, 80, 80)
            
        pygame.draw.rect(window, color, option_rect, border_radius=5)
        text_surf = font.render(str(count), True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=option_rect.center)
        window.blit(text_surf, text_rect)
        
        player_count_buttons[count] = option_rect

    btn_rect = pygame.Rect(0, 0, 250, 60)
    btn_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 80)
    is_hovered = btn_rect.collidepoint(mouse_pos)
    draw_button(window, font, "Begin Game", btn_rect, is_hovered)
    
    return {'player_count_buttons': player_count_buttons, 'btn_begin_game': btn_rect}


def draw_pause_menu(window, font, mouse_pos, music_volume):
    """Draws the pause menu with a dark overlay and music controls."""
    # Dark overlay
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180)) 
    window.blit(overlay, (0, 0))

    # Menu Title
    title_surf = font.render("GAME PAUSED", True, TEXT_COLOR)
    window.blit(title_surf, (WINDOW_WIDTH // 2 - title_surf.get_width() // 2, WINDOW_HEIGHT // 2 - 100))

    # Resume Button
    btn_resume = pygame.Rect(0, 0, 200, 50)
    btn_resume.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
    is_hovered = btn_resume.collidepoint(mouse_pos)
    draw_button(window, font, "Resume (ESC)", btn_resume, is_hovered)

    
    # 1. Label
    label_surf = font.render(f"Music Volume: {int(music_volume * 100)}%", True, TEXT_COLOR)
    label_rect = label_surf.get_rect(center=(PAUSE_MENU_CENTER_X, MUSIC_SLIDER_Y - 30))
    window.blit(label_surf, label_rect)
    
    # 2. Slider Track
    slider_x = PAUSE_MENU_CENTER_X - SLIDER_WIDTH // 2
    slider_rect = pygame.Rect(slider_x, MUSIC_SLIDER_Y, SLIDER_WIDTH, SLIDER_HEIGHT)
    pygame.draw.rect(window, (100, 100, 100), slider_rect, border_radius=5)
    
    # 3. Slider Knob (Calculated based on volume 0.0 to 1.0)
    knob_center_x = slider_x + int(music_volume * SLIDER_WIDTH)
    pygame.draw.circle(window, TEXT_COLOR, (knob_center_x, MUSIC_SLIDER_Y + SLIDER_HEIGHT // 2), SLIDER_KNOB_RADIUS)
    
    # Return button and slider rect for handling clicks
    return {'btn_resume': btn_resume, 'slider_rect': slider_rect}

def draw_game_over_screen(window, font, game_state, mouse_pos, wood_texture):
    """Draws the final score screen and determines the winner."""
    window.blit(wood_texture, (0, 0))

    final_scores = game_state.scores
    if not final_scores:
        winner_text = "Game Over"
        winner_score = ""
    else:
        max_score = max(final_scores)
        winners = [i for i, score in enumerate(final_scores) if score == max_score]
        
        if len(winners) == 1:
            winner_text = f"Player {winners[0] + 1} Wins!"
        else:
            winner_text = f"Tie! Players {', '.join([str(w + 1) for w in winners])} Win!"
        winner_score = f"Score: {max_score}"

    # Title
    title_surf = font.render("GAME OVER", True, TEXT_COLOR)
    window.blit(title_surf, (WINDOW_WIDTH // 2 - title_surf.get_width() // 2, 50))
    
    # Winner
    winner_surf = font.render(winner_text, True, (255, 255, 0))
    window.blit(winner_surf, (WINDOW_WIDTH // 2 - winner_surf.get_width() // 2, 100))
    
    score_surf = font.render(winner_score, True, (255, 255, 0))
    window.blit(score_surf, (WINDOW_WIDTH // 2 - score_surf.get_width() // 2, 140))


    # Scoreboard
    start_y = 200
    spacing = 50
    for i, score in enumerate(final_scores):
        text = f"Player {i + 1}: {score} points"
        score_surf = font.render(text, True, TEXT_COLOR)
        window.blit(score_surf, (WINDOW_WIDTH // 2 - score_surf.get_width() // 2, start_y + i * spacing))

    # Main Menu Button
    btn_menu = pygame.Rect(0, 0, 250, 50)
    btn_menu.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 100)
    is_hovered = btn_menu.collidepoint(mouse_pos)
    draw_button(window, font, "Back to Main Menu", btn_menu, is_hovered)
    
    return {'btn_menu': btn_menu}

def draw_phase_indicator(window, font, game_state, phase_name_func):
    """Draws the phase and hint text at the bottom left."""
    name = phase_name_func(game_state)
    text = f"Phase: {name}"
    surf = font.render(text, True, (20, 20, 20))
    window.blit(surf, (10, WINDOW_HEIGHT - 30))

    # contextual hint
    if "MEEP" in name:
        hint = "Left-click highlighted tile to place meeple. Press P to pass."
    else:
        hint = "Drag tile from preview to board. Right-click preview or while dragging to rotate."
    hint_surf = font.render(hint, True, (60, 60, 60))
    window.blit(hint_surf, (10, WINDOW_HEIGHT - 60))


def draw_tiles_remaining(window, font, game_state):
    """Draws the number of remaining tiles above the score panels, centered in the panel area."""
    remaining = len(game_state.deck)
    text = f"Tiles Left: {remaining}"
    surf = font.render(text, True, (255, 255, 255))
    
    x_center = 10 + PLAYER_PANEL_WIDTH // 2
    
    text_rect = surf.get_rect(center=(x_center, 180))
    
    window.blit(surf, text_rect )


def draw_player_info_panel(window, font, x, y, player_index, score, meeples_left, is_current_player):
    """Draws a single player's score and meeple count panel."""
    color_map = [(0, 100, 200), (200, 0, 0), (100, 100, 100), (200, 200, 0), (0, 200, 0), (255, 105, 180)]
    player_color = color_map[player_index % len(color_map)]
    
    # Background rectangle
    rect = pygame.Rect(x, y, PLAYER_PANEL_WIDTH, PLAYER_PANEL_HEIGHT)
    pygame.draw.rect(window, (30, 30, 30), rect, border_radius=5)
    
    # Highlight border for current player
    border_color = (255, 255, 0) if is_current_player else player_color
    pygame.draw.rect(window, border_color, rect, 5, border_radius=5)
    
    # Player indicator color strip
    pygame.draw.rect(window, player_color, pygame.Rect(x + 5, y + 5, 20, PLAYER_PANEL_HEIGHT - 10), border_radius=3)

    # Player Number/Index
    player_surf = font.render(f"P{player_index + 1}", True, TEXT_COLOR)
    window.blit(player_surf, (x + 30, y + 10))

    # Score
    score_text = f"Score: {score}"
    score_surf = font.render(score_text, True, TEXT_COLOR)
    window.blit(score_surf, (x + 40, y + 40))

    # Meeples
    meeple_text = f"Meeples: {meeples_left}"
    meeple_surf = font.render(meeple_text, True, TEXT_COLOR)
    window.blit(meeple_surf, (x + 40, y + 70))


def draw_player_info(window, font, game_state):
    """Draws all player info panels (stacked vertically)."""
    spacing = PLAYER_PANEL_HEIGHT + 15 
    x_pos = 10 

    player_scores = game_state.scores 
    player_meeples = game_state.meeples 
    current_player_index = game_state.current_player
    num_players = len(player_scores)

    top_margin = 200 
    bottom_panel_y_start = top_margin + (num_players - 1) * spacing 

    for i in range(num_players):
        panel_y = bottom_panel_y_start - i * spacing
        
        is_current = (i == current_player_index)
        draw_player_info_panel(
            window, 
            font, 
            x_pos, 
            panel_y, 
            player_index=i, 
            score=player_scores[i], 
            meeples_left=player_meeples[i],
            is_current_player=is_current
        )