import pygame
from resources import (
    TILE_SIZE, meeple_position_offsets, big_meeple_position_offsets, 
    CENTER_OFFSET_X, CENTER_OFFSET_Y, get_meeple_image, load_tile_image
)
from wingedsheep.carcassonne.objects.meeple_type import MeepleType

def draw_ghosts(window, game_state, game, phase_name_func, ghost_surface, is_my_turn=True):
    """Draws tile and meeple placement ghosts."""
    if not is_my_turn:
        return

    name = phase_name_func(game_state)
    next_tile = game_state.next_tile
    possible_actions = game.get_possible_actions()

    if "MEEP" in name:
        # Meeple ghost drawing logic
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
        # Tile Ghost Logic - Draw only for valid placements at the CURRENT rotation
        if next_tile is None: 
            return

        # Get the current rotation of the tile
        current_rotation = next_tile.turns
        
        # Debug: count valid positions and show details for first few
        valid_positions = []
        print(f"DEBUG: Next Tile: {next_tile.description}, Rotation: {current_rotation}")
        print(f"DEBUG: Total possible actions: {len(possible_actions)}")

        for action in possible_actions:
            if hasattr(action, 'tile_rotations'):
                print(f"DEBUG: Action rotation: {action.tile_rotations} vs Current: {current_rotation}")

            # Check if the action is a TileAction with matching rotation
            if (hasattr(action, 'coordinate') and 
                hasattr(action, 'tile_rotations') and 
                action.tile_rotations == current_rotation):
                valid_positions.append((action.coordinate.column, action.coordinate.row))
                ghost_x_px = action.coordinate.column * TILE_SIZE
                ghost_y_px = action.coordinate.row * TILE_SIZE
                
                # APPLY CENTER OFFSET
                window.blit(ghost_surface, (ghost_x_px + CENTER_OFFSET_X, ghost_y_px + CENTER_OFFSET_Y))
        
        # Summary output
        if valid_positions:
            print(f"DEBUG: Total {len(valid_positions)} ghost positions for rotation {current_rotation}")
            pass

def draw_placed_meeples(window, game_state):
    """Draws all placed meeples on the board."""
    from resources import big_meeple_position_offsets, meeple_position_offsets
    
    total_meeples = sum(len(player_meeples) for player_meeples in game_state.placed_meeples)
    
    # Only log when there are meeples to draw (reduce spam)
    if total_meeples > 0:
        # Use a simple cache to avoid logging the same count repeatedly
        if not hasattr(draw_placed_meeples, '_last_meeple_count'):
            draw_placed_meeples._last_meeple_count = 0
        
        if draw_placed_meeples._last_meeple_count != total_meeples:
            print(f"DRAW: 🎯 Meeple count changed: {draw_placed_meeples._last_meeple_count} → {total_meeples}")
            draw_placed_meeples._last_meeple_count = total_meeples
    
    meeples_drawn = 0
    for player, placed_meeples in enumerate(game_state.placed_meeples):
        for meeple_idx, meeple_position in enumerate(placed_meeples):
            meep_type = meeple_position.meeple_type
            is_big = (meep_type == MeepleType.BIG)
            offsets = big_meeple_position_offsets if is_big else meeple_position_offsets

            col = meeple_position.coordinate_with_side.coordinate.column
            row = meeple_position.coordinate_with_side.coordinate.row
            side = meeple_position.coordinate_with_side.side
            
            meep_img = get_meeple_image(player, meep_type, is_ghost=False)
            
            if meep_img is None:
                print(f"DRAW: ERROR - No image for player {player} meeple type {meep_type}")
                continue
            
            # Calculate final screen position
            x = col * TILE_SIZE + CENTER_OFFSET_X + offsets[side][0] - (meep_img.get_width() / 2)
            y = row * TILE_SIZE + CENTER_OFFSET_Y + offsets[side][1] - (meep_img.get_height() / 2)
            
            # Only log first few meeples to avoid spam
            if meeples_drawn < 3 and total_meeples > draw_placed_meeples._last_meeple_count:
                print(f"DRAW: Player {player} Meeple at [{row},{col}] {side.name}")
            
            window.blit(meep_img, (x, y))
            meeples_drawn += 1


def draw_board(window, font, game_state, drag_pos, game, wood_texture, phase_name_func, ghost_surface, is_my_turn=True):
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
    draw_ghosts(window, game_state, game, phase_name_func, ghost_surface, is_my_turn)
    draw_placed_meeples(window, game_state)
    
    # 3. Draw Dragging Tile (Drawn last so it overlaps everything else)
    next_tile = game_state.next_tile
    if next_tile is not None and (phase_name_func(game_state) not in ["MEEPLE", "ABBOT"]):
        img = load_tile_image(next_tile)
        window.blit(img, drag_pos)