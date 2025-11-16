# resources.py

import pygame
import os
import wingedsheep
from wingedsheep.carcassonne.objects.meeple_type import MeepleType
from wingedsheep.carcassonne.objects.side import Side
from wingedsheep.carcassonne.objects.coordinate import Coordinate
from wingedsheep.carcassonne.objects.actions.action import Action
import math
# resources.py

import pygame
import os
import wingedsheep
# ... (rest of imports)
from wingedsheep.carcassonne.objects.actions.action import Action
import math

# --- CORE GAME CONSTANTS ---
TILE_SIZE = 60
WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 1000
PREVIEW_TILE_X = 100
PREVIEW_TILE_Y = 100
SNAP_THRESHOLD = 45
PLAYER_PANEL_WIDTH = 180 # NEW
PLAYER_PANEL_HEIGHT = 100 # NEW



# --- SCREEN CONSTANTS ---
MENU_FONT_SIZE = 40
BUTTON_COLOR = (44, 95, 150)
HOVER_COLOR = (64, 115, 170)
TEXT_COLOR = (255, 255, 255)
BG_COLOR = (120, 60, 30) 

# --- GAME STATE CONSTANTS ---
STATE_PRE_GAME = "PRE_GAME"
STATE_PLAYER_INPUT = "PLAYER_INPUT"
STATE_GAME_RUNNING = "GAME_RUNNING"
STATE_PAUSED = "PAUSED"
STATE_GAME_OVER = "GAME_OVER"
images_path = os.path.join(wingedsheep.__path__[0], 'carcassonne', 'resources', 'images')
MUSIC_FILE = os.path.join(wingedsheep.__path__[0], 'carcassonne', 'resources', 'music', 'medieval-music.mp3')

tile_cache = {}
meeple_image_cache = {}
meeple_size = 15
big_meeple_size = 25

BOARD_CENTER_X = WINDOW_WIDTH // 2
BOARD_CENTER_Y = WINDOW_HEIGHT // 2
CENTER_OFFSET_X = 0
CENTER_OFFSET_Y = 0

PAUSE_BUTTON_WIDTH = 80
PAUSE_BUTTON_HEIGHT = 50
PAUSE_MARGIN = 50 

PAUSE_BUTTON_X = WINDOW_WIDTH - PAUSE_BUTTON_WIDTH - PAUSE_MARGIN  # Anchors to the right side
PAUSE_BUTTON_Y = 100

SLIDER_WIDTH = 200
SLIDER_HEIGHT = 10
SLIDER_KNOB_RADIUS = 10
PAUSE_MENU_CENTER_X = WINDOW_WIDTH // 2
MUSIC_SLIDER_Y = WINDOW_HEIGHT // 2 + 120

meeple_position_offsets = {
    Side.TOP: (TILE_SIZE / 2, (meeple_size / 2) + 3),
    Side.RIGHT: (TILE_SIZE - (meeple_size / 2) - 3, TILE_SIZE / 2),
    Side.BOTTOM: (TILE_SIZE / 2, TILE_SIZE - (meeple_size / 2) - 3),
    Side.LEFT: ((meeple_size / 2) + 3, TILE_SIZE / 2),
    Side.CENTER: (TILE_SIZE / 2, TILE_SIZE / 2),
    Side.TOP_LEFT: (TILE_SIZE / 4, (meeple_size / 2) + 3),
    Side.TOP_RIGHT: ((TILE_SIZE / 4) * 3, (meeple_size / 2) + 3),
    Side.BOTTOM_LEFT: (TILE_SIZE / 4, TILE_SIZE - (meeple_size / 2) - 3),
    Side.BOTTOM_RIGHT: ((TILE_SIZE / 4) * 3, TILE_SIZE - (meeple_size / 2) - 3)
}

big_meeple_position_offsets = {
    Side.TOP: (TILE_SIZE / 2, (big_meeple_size / 2) + 3),
    Side.RIGHT: (TILE_SIZE - (big_meeple_size / 2) - 3, TILE_SIZE / 2),
    Side.BOTTOM: (TILE_SIZE / 2, TILE_SIZE - (big_meeple_size / 2) - 3),
    Side.LEFT: ((big_meeple_size / 2) + 3, TILE_SIZE / 2),
    Side.CENTER: (TILE_SIZE / 2, TILE_SIZE / 2),
    Side.TOP_LEFT: (TILE_SIZE / 4, (big_meeple_size / 2) + 3),
    Side.TOP_RIGHT: ((TILE_SIZE / 4) * 3, (big_meeple_size / 2) + 3),
    Side.BOTTOM_LEFT: (TILE_SIZE / 4, TILE_SIZE - (big_meeple_size / 2) - 3),
    Side.BOTTOM_RIGHT: ((TILE_SIZE / 4) * 3, TILE_SIZE - (big_meeple_size / 2) - 3)
}

meeple_icons = {
    MeepleType.NORMAL: ["blue_meeple.png", "red_meeple.png", "black_meeple.png", "yellow_meeple.png", "green_meeple.png", "pink_meeple.png"],
    MeepleType.ABBOT: ["blue_abbot.png", "red_abbot.png", "black_abbot.png", "yellow_abbot.png", "green_abbot.png", "pink_abbot.png"]
}

# --- ASSET LOADING HELPERS (Original Logic) ---

def get_meeple_image_path(player: int, meeple_type: MeepleType) -> str:
    """
    Gets the absolute file path for a given meeple type and player.
    """
    
    icon_type = MeepleType.NORMAL
    if meeple_type == MeepleType.ABBOT:
        icon_type = meeple_type

    if icon_type not in meeple_icons:
        print(f"Error: Meeple icon type {icon_type} not in meeple_icons map!")
        return ""
        
    if player >= len(meeple_icons[icon_type]):
        print(f"Error: Player index {player} out of range for {icon_type}. Defaulting to 0.")
        player = 0

    image_filename = meeple_icons[icon_type][player]
    abs_file_path = os.path.join(images_path, image_filename)
    
    return abs_file_path


def get_meeple_image(player_index: int, meeple_type: MeepleType, is_ghost: bool = False):
    """
    Loads, scales, and caches meeple images.
    Returns a semi-transparent 'ghost' if is_ghost is True.
    """
    size = big_meeple_size if meeple_type == MeepleType.BIG else meeple_size
    key = f"{player_index}_{meeple_type}_{size}"
    if is_ghost:
        key += "_ghost"

    if key in meeple_image_cache:
        return meeple_image_cache[key]

    meep_path = get_meeple_image_path(player_index, meeple_type)
    
    if not meep_path or not os.path.exists(meep_path):
        meeple_image_cache[key] = None
        return None

    img = pygame.image.load(meep_path).convert_alpha()
    img = pygame.transform.scale(img, (size, size))
    
    if is_ghost:
        img.set_alpha(128)
    
    meeple_image_cache[key] = img
    return img


def load_tile_image(tile):
    """Loads and caches the rotated tile image."""
    name = tile.image
    key = f"{name}_{tile.turns}"

    if key in tile_cache:
        return tile_cache[key]

    abs_path = os.path.join(images_path, name)
    img = pygame.image.load(abs_path).convert_alpha()
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img = pygame.transform.rotate(img, -90 * tile.turns)

    tile_cache[key] = img
    return img