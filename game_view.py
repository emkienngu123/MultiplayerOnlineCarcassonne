import pygame
from resources import (
    TILE_SIZE, meeple_position_offsets, big_meeple_position_offsets, 
    CENTER_OFFSET_X, CENTER_OFFSET_Y, get_meeple_image, load_tile_image
)
from wingedsheep.carcassonne.objects.meeple_type import MeepleType

def draw_ghosts(window, game_state, game, phase_name_func, ghost_surface):
    """Draws tile and meeple placement ghosts."""
    name = phase_name_func(game_state)
    next_tile = game_state.next_tile
    possible_actions = game.get_possible_actions()

    if "MEEP" in name:
        # ... (Meeple ghost drawing logic remains the same) ...
        # ... (This block handles meeple placement and is not the issue) ...
        from resources import big_meeple_position_offsets, meeple_position_offsets
        for action in possible_actions:
            if hasattr(action , 'coordinate_with_side') and hasattr(action , 'meeple_type'):
                is_big = (action.meeple_type == MeepleType.BIG)
                offsets = big_meeple_position_offsets if is_big else meeple_position_offsets
                
                ghost_x_px = action.coordinate_with_side.coordinate.column * TILE_SIZE + offsets[action.coordinate_with_side.side][0]
                ghost_y_px = action.coordinate_with_side.coordinate.row * TILE_SIZE + offsets[action.coordinate_with_side.side][1]
                
                meep_img = get_meeple_image(game_state.current_player, action.meeple_type , is_ghost=True)
                
                # APPLY CENTER OFFSET
                window.blit(meep_img, (ghost_x_px + CENTER_OFFSET_X - meep_img.get_width() / 2, ghost_y_px + CENTER_OFFSET_Y - meep_img.get_height() / 2))
    else:
        # FIX: Tile Ghost Logic - Draw for ANY valid coordinate, regardless of current rotation.
        if next_tile is None: return

        # Set to track coordinates where a ghost has been drawn to prevent duplicates
        drawn_coordinates = set()

        for action in possible_actions:
            # Check if the action is a TileAction (has a coordinate)
            if hasattr(action, 'coordinate'):
                coord_tuple = (action.coordinate.column, action.coordinate.row)

                if coord_tuple not in drawn_coordinates:
                    drawn_coordinates.add(coord_tuple)
                    
                    ghost_x_px = action.coordinate.column * TILE_SIZE
                    ghost_y_px = action.coordinate.row * TILE_SIZE
                    
                    # APPLY CENTER OFFSET
                    window.blit(ghost_surface, (ghost_x_px + CENTER_OFFSET_X, ghost_y_px + CENTER_OFFSET_Y))

def draw_placed_meeples(window, game_state):
# ... (function body remains the same) ...
    from resources import big_meeple_position_offsets, meeple_position_offsets
    for player, placed_meeples in enumerate(game_state.placed_meeples):
        for meeple_position in placed_meeples:
            meep_type = meeple_position.meeple_type
            is_big = (meep_type == MeepleType.BIG)
            offsets = big_meeple_position_offsets if is_big else meeple_position_offsets

            col = meeple_position.coordinate_with_side.coordinate.column
            row = meeple_position.coordinate_with_side.coordinate.row
            side = meeple_position.coordinate_with_side.side
            
            meep_img = get_meeple_image(player, meep_type, is_ghost=False)
            
            # Calculate final screen position
            x = col * TILE_SIZE + CENTER_OFFSET_X + offsets[side][0] - (meep_img.get_width() / 2)
            y = row * TILE_SIZE + CENTER_OFFSET_Y + offsets[side][1] - (meep_img.get_height() / 2)
            
            window.blit(meep_img, (x, y))


def draw_board(window, font, game_state, drag_pos, game, wood_texture, phase_name_func, ghost_surface):
    """Main function to draw the game board, tiles, dragging tile, ghosts, and meeples."""
    window.blit(wood_texture, (0, 0))

    # 1. Draw Placed Tiles 
    for r, row in enumerate(game_state.board):
        for c, tile in enumerate(row):
            if tile is not None:
                img = load_tile_image(tile)
                # APPLY CENTER OFFSET
                window.blit(img, (c * TILE_SIZE + CENTER_OFFSET_X, r * TILE_SIZE + CENTER_OFFSET_Y))

    # 2. Draw Ghosts, Placed Meeples (Draws the translucent green squares and placed meeples)
    draw_ghosts(window, game_state, game, phase_name_func, ghost_surface)
    draw_placed_meeples(window, game_state)
    
    # 3. Draw Dragging Tile (Drawn last so it overlaps everything else)
    next_tile = game_state.next_tile
    if next_tile is not None and (phase_name_func(game_state) not in ["MEEPLE", "ABBOT"]):
        img = load_tile_image(next_tile)
        window.blit(img, drag_pos)