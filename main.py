import pygame
import os
import math
from wingedsheep.carcassonne.carcassonne_game import CarcassonneGame
from wingedsheep.carcassonne.objects.actions.action import Action
from wingedsheep.carcassonne.tile_sets.tile_sets import TileSet
from wingedsheep.carcassonne.tile_sets.supplementary_rules import SupplementaryRule
from wingedsheep.carcassonne.objects.side import Side
from wingedsheep.carcassonne.objects.meeple_type import MeepleType
import wingedsheep

TILE_SIZE = 60
WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 1000


PREVIEW_TILE_X = 100
PREVIEW_TILE_Y = 100
SNAP_THRESHOLD = 45  # --- ADDED: How close to snap (px) ---
# --- ADDED: A semi-transparent surface for "ghost" placements ---


meeple_size = 15
big_meeple_size = 25
meeple_image_cache = {}

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


from wingedsheep.carcassonne.objects.meeple_type import MeepleType

# This data, which was part of the class, is now needed to call the function.
meeple_icons = {
    MeepleType.NORMAL: ["blue_meeple.png", "red_meeple.png", "black_meeple.png", "yellow_meeple.png", "green_meeple.png", "pink_meeple.png"],
    MeepleType.ABBOT: ["blue_abbot.png", "red_abbot.png", "black_abbot.png", "yellow_abbot.png", "green_abbot.png", "pink_abbot.png"]
}

def get_meeple_image_path(player: int, 
                          meeple_type: MeepleType, 
                          base_images_path: str) -> str:
    """
    Gets the absolute file path for a given meeple type and player.
    
    :param player: The index of the player (e.g., 0 for "blue").
    :param meeple_type: The MeepleType enum.
    :param meeple_icons_map: The dictionary mapping types to icon lists (like the one above).
    :param base_images_path: The
    :return: A string containing the absolute path to the image file.
    """
    
    # Determine which base icon file to use.
    # All types (NORMAL, BIG, FARMER, BIG_FARMER) use the "NORMAL" icon file.
    # Only ABBOT uses the "ABBOT" icon file.
    icon_type = MeepleType.NORMAL
    if meeple_type == MeepleType.ABBOT:
        icon_type = meeple_type

    # Error checking
    if icon_type not in meeple_icons:
        print(f"Error: Meeple icon type {icon_type} not in meeple_icons map!")
        return "" # Return empty string on failure
        
    if player >= len(meeple_icons[icon_type]):
        print(f"Error: Player index {player} out of range for {icon_type}. Defaulting to 0.")
        player = 0

    # Get the filename and join it with the base image path
    image_filename = meeple_icons[icon_type][player]
    abs_file_path = os.path.join(base_images_path, image_filename)
    
    return abs_file_path





pygame.init()
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Carcassonne – Minimal Pygame UI")

images_path = os.path.join(wingedsheep.__path__[0], 'carcassonne', 'resources', 'images')
tile_cache = {}

ghost_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
ghost_surface.fill((100, 200, 100, 100))  # R, G, B, Alpha (translucent green)
# --- END ADDED ---


meeple_ghost = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
meeple_ghost.fill((100, 50, 50, 100))

font = pygame.font.SysFont(None, 26)



# --- ADDED: Function to load/cache meeple images ---
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

    meep_path = get_meeple_image_path(player_index, meeple_type, images_path)
    
    if not meep_path or not os.path.exists(meep_path):
        meeple_image_cache[key] = None # Cache failure
        return None

    img = pygame.image.load(meep_path).convert_alpha()
    img = pygame.transform.scale(img, (size, size))
    
    if is_ghost:
        img.set_alpha(128) # Make ghosts semi-transparent
    
    meeple_image_cache[key] = img
    return img
# --- END ADDED ---





def load_tile_image(tile):
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

def phase_name_for_state(game_state):
    p = getattr(game_state , 'phase' , None)
    return getattr(p,'name',str(p)).upper() if p is not None else "UNKNOWN"


def draw_phase_indicator(game_state):
    name = phase_name_for_state(game_state)
    text = f"Phase: {name}"
    surf = font.render(text, True, (20, 20, 20))
    window.blit(surf, (10, WINDOW_HEIGHT - 30))

    # contextual hint
    if "MEEP" in name:  # matches MEEPLE or similar
        hint = "Left-click highlighted tile to place meeple. Press P to pass."
    else:
        hint = "Drag tile from preview to board. Right-click preview or while dragging to rotate."
    hint_surf = font.render(hint, True, (60, 60, 60))
    window.blit(hint_surf, (10, WINDOW_HEIGHT - 60))

def draw_ghosts(game_state):
    # Decide which ghosts to draw depending on phase
    name = phase_name_for_state(game_state)
    next_tile = game_state.next_tile
    possible_actions = game.get_possible_actions()

    if "MEEP" in name:
        # Draw meeple placement hints (small circle) on valid tiles
        for action in possible_actions:
            # Meeple actions typically have a coordinate but not tile_rotations
            if  hasattr(action , 'coordinate_with_side') and hasattr(action , 'meeple_type'):

                if action.meeple_type == MeepleType.BIG:
                    ghost_x_px = action.coordinate_with_side.coordinate.column * TILE_SIZE + big_meeple_position_offsets[action.coordinate_with_side.side][0]
                    ghost_y_px = action.coordinate_with_side.coordinate.row * TILE_SIZE + big_meeple_position_offsets[action.coordinate_with_side.side][1]
                else:
                    ghost_x_px = action.coordinate_with_side.coordinate.column * TILE_SIZE + meeple_position_offsets[action.coordinate_with_side.side][0]
                    ghost_y_px = action.coordinate_with_side.coordinate.row * TILE_SIZE + meeple_position_offsets[action.coordinate_with_side.side][1]
                meep_img = get_meeple_image(game_state.current_player, action.meeple_type , is_ghost=True)
                window.blit(meep_img, (ghost_x_px, ghost_y_px))
    else:
        # Tile placement ghosts
        if next_tile is None:
            return

        current_rotation = next_tile.turns

        for action in possible_actions:
            if (hasattr(action,'coordinate') and hasattr(action,'tile_rotations')) and action.tile_rotations == current_rotation:
                ghost_x_px = action.coordinate.column * TILE_SIZE
                ghost_y_px = action.coordinate.row * TILE_SIZE
                window.blit(ghost_surface, (ghost_x_px, ghost_y_px))

def draw_placed_meeples(game_state):
    for player, placed_meeples in enumerate(game_state.placed_meeples):
        for meeple_position in placed_meeples:
            img = get_meeple_image(player, meeple_position.meeple_type)
            x = meeple_position.coordinate_with_side.coordinate.column * TILE_SIZE + meeple_position_offsets[meeple_position.coordinate_with_side.side][0]
            y = meeple_position.coordinate_with_side.coordinate.row * TILE_SIZE
            meep_img = get_meeple_image(player, meeple_position.meeple_type,is_ghost=False)
            window.blit(meep_img, (x, y))




def draw_board(game_state , drag_pos):
    window.fill((240, 240, 240))

    


    for r, row in enumerate(game_state.board):
        for c, tile in enumerate(row):
            if tile is not None:
                img = load_tile_image(tile)
                window.blit(img, (c * TILE_SIZE, r * TILE_SIZE))

    next_tile = game_state.next_tile
    if next_tile is not None:
        img = load_tile_image(next_tile)
        window.blit(img,drag_pos)
    draw_ghosts(game_state)
    draw_placed_meeples(game_state)
    draw_phase_indicator(game_state)


    pygame.display.update()


# --- CREATE GAME ---
game = CarcassonneGame(
    players=2,
    tile_sets=[TileSet.BASE, TileSet.THE_RIVER, TileSet.INNS_AND_CATHEDRALS],
    supplementary_rules=[SupplementaryRule.ABBOTS, SupplementaryRule.FARMERS]
)

clock = pygame.time.Clock()
auto_play = False  # set to False if you want "press space to play move"

is_dragging = False
drag_pos = (PREVIEW_TILE_X, PREVIEW_TILE_Y)
snap_action = None  # --- ADDED: To store the action we are snapping to ---

#play starting tiles



running = True
while running:
    mouse_x , mouse_y = pygame.mouse.get_pos()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                name = phase_name_for_state(game.state)
                if "MEEP" in name:
                    possible = game.get_possible_actions()
                    for a in possible:
                        if not hasattr(a,'coordinate') and not hasattr(a,'tile_rotations'):
                            game.step(game.get_current_player(),a)
                            break
# --- ADDED: Handle mouse clicks for rotation ---
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Use mouse_x, mouse_y from top of loop
            preview_rect = pygame.Rect(PREVIEW_TILE_X, PREVIEW_TILE_Y, TILE_SIZE, TILE_SIZE)
            current_phase = phase_name_for_state(game.state)
            

            if event.button == 1:  # Left-click

                if "MEEP" in current_phase:
                    possible = game.get_possible_actions()
                    clicked = False

                    # Try to match a click to any meeple action (supports coordinate_with_side or plain coordinate)
                    for a in possible:
                        # ignore tile-placement actions
                        if hasattr(a, 'tile_rotations'):
                            continue

                        # Actions that target a specific side/position on the tile
                        if hasattr(a, 'coordinate_with_side'):
                            cws = a.coordinate_with_side
                            col = cws.coordinate.column
                            row = cws.coordinate.row
                            side = cws.side

                            if getattr(a, 'meeple_type', None) == MeepleType.BIG:
                                offs = big_meeple_position_offsets[side]
                                size = big_meeple_size
                            else:
                                offs = meeple_position_offsets[side]
                                size = meeple_size

                            center_x = col * TILE_SIZE + offs[0]
                            center_y = row * TILE_SIZE + offs[1]
                            dist = math.hypot(mouse_x - center_x, mouse_y - center_y)

                            if dist <= (size / 2) + 6:  # small tolerance
                                game.step(game.get_current_player(), a)
                                clicked = True
                                break

                    # do not start dragging when in meeple phase (click consumed or ignored)
                    continue
                # Check if the click is on the preview tile to START DRAG
                if not is_dragging and preview_rect.collidepoint(mouse_x, mouse_y) and game.state.next_tile is not None:
                    is_dragging = True
            
            elif event.button == 3: # Right-click
                if "MEEP" not in current_phase and game.state.next_tile is not None:
                    # Allow rotation if EITHER we are currently dragging OR we right-click the preview spot
                    if is_dragging or preview_rect.collidepoint(mouse_x, mouse_y):
                        game.state.next_tile.turns = (game.state.next_tile.turns + 1) % 4
                        snap_action = None
# ...existing code...


        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and is_dragging:
                is_dragging = False

                if snap_action is not None:
                    game.step(game.get_current_player() , snap_action)
                    snap_action = None      
                else :
                    print("Invalid move")



    # --- MODIFIED: State-based position update with snapping logic ---
    snap_action = None  # Reset snap action each frame
    closest_action = None
    min_dist = float('inf')

    if game.state.next_tile is not None:
        current_rotation = game.state.next_tile.turns
        possible_actions = game.get_possible_actions()
        current_phase = phase_name_for_state(game.state)
        # Find the closest valid snap point
        if "MEEP" not in current_phase:
            for action in possible_actions:
                if (hasattr(action, 'coordinate') and hasattr(action, 'tile_rotations') and
                    action.tile_rotations == current_rotation):
                    
                    # Calculate center of the target grid cell
                    target_x_px = action.coordinate.column * TILE_SIZE + TILE_SIZE // 2
                    target_y_px = action.coordinate.row * TILE_SIZE + TILE_SIZE // 2
                    
                    # Calculate distance from mouse to target center
                    dist = math.dist((mouse_x, mouse_y), (target_x_px, target_y_px))

                    if dist < min_dist and dist < SNAP_THRESHOLD:
                        min_dist = dist
                        closest_action = action

    if is_dragging:
        if closest_action is not None:
            # Snap to the closest valid spot
            drag_pos = (closest_action.coordinate.column * TILE_SIZE, closest_action.coordinate.row * TILE_SIZE)
            snap_action = closest_action
        else:
            # No snap target, follow the mouse (centered)
            drag_pos = (mouse_x - TILE_SIZE // 2, mouse_y - TILE_SIZE // 2)
            snap_action = None
    else:
        # Not dragging, snap back to preview area
        drag_pos = (PREVIEW_TILE_X, PREVIEW_TILE_Y)
        snap_action = None
    # --- END MODIFIED ---

    # Draw board
    draw_board(game.state , drag_pos)

    clock.tick(60)

pygame.quit()
