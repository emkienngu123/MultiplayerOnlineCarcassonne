from wingedsheep.carcassonne.carcassonne_game_state import CarcassonneGameState
from wingedsheep.carcassonne.objects.coordinate import Coordinate
from wingedsheep.carcassonne.objects.playing_position import PlayingPosition
from wingedsheep.carcassonne.objects.tile import Tile
from wingedsheep.carcassonne.utils.tile_fitter import TileFitter


class TilePositionFinder:

    @staticmethod
    def possible_playing_positions(game_state: CarcassonneGameState, tile_to_play: Tile) -> [PlayingPosition]:
        if game_state.empty_board():
            return [PlayingPosition(coordinate=game_state.starting_position, turns=0)]

        # --- SPEED OPTIMIZATION START: Only check slots adjacent to existing tiles ---

        possible_coordinates_to_check = set()
        
        # 1. Collect all coordinates that currently hold a tile.
        # This initial loop iterates over the game_state's internal board structure 
        # to find coordinates that are already occupied.
        placed_coordinates = []
        for r_idx, r_row in enumerate(game_state.board):
            for c_idx, c_tile in enumerate(r_row):
                if c_tile is not None:
                    placed_coordinates.append(Coordinate(r_idx, c_idx))

        # 2. Find all unique, empty neighbors of placed tiles.
        # This is much faster than checking every empty cell on a large board.
        for coord in placed_coordinates:
            r, c = coord.row, coord.column
            
            # Check the four adjacent neighbors: (Top, Bottom, Left, Right)
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                
                # Use get_tile to check the potential placement slot
                neighbor_tile = game_state.get_tile(nr, nc)
                
                # If the neighbor is empty (None), it is a candidate position.
                if neighbor_tile is None:
                    # Using a set automatically handles duplicates (e.g., a spot adjacent to two tiles)
                    possible_coordinates_to_check.add(Coordinate(nr, nc))

        playing_positions = []
        
        # 3. Iterate ONLY over the set of candidate empty spots (O(T * 4), T = number of tiles)
        for coordinate in possible_coordinates_to_check:
            row_index = coordinate.row
            column_index = coordinate.column

            # Get the neighbors of the empty spot once.
            top = game_state.get_tile(row_index - 1, column_index)
            bottom = game_state.get_tile(row_index + 1, column_index)
            left = game_state.get_tile(row_index, column_index - 1)
            right = game_state.get_tile(row_index, column_index + 1)

            for tile_turns in range(0, 4):
                # Check 4 rotations for the tile in this spot.
                if TileFitter.fits(tile_to_play.turn(tile_turns), top=top, bottom=bottom, left=left, right=right, game_state=game_state):
                    playing_positions.append(PlayingPosition(coordinate=coordinate, turns=tile_turns))

        return playing_positions
        # --- SPEED OPTIMIZATION END ---