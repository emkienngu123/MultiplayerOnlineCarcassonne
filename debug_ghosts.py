
import unittest
from wingedsheep.carcassonne.carcassonne_game import CarcassonneGame
from wingedsheep.carcassonne.objects.tile import Tile
from wingedsheep.carcassonne.objects.side import Side
from wingedsheep.carcassonne.objects.connection import Connection
from wingedsheep.carcassonne.utils.tile_fitter import TileFitter
from wingedsheep.carcassonne.utils.action_util import ActionUtil

class TestGhostTiles(unittest.TestCase):
    def test_ghost_generation(self):
        # 1. Setup Game
        game = CarcassonneGame(players=2)
        state = game.state
        
        # 2. Manually place a tile at (0,0) - simulating deserialized board
        # Tile with Road Top-Bottom, City Left, Grass Right
        center_tile = Tile(description="Center")
        center_tile.road = [Connection(Side.TOP, Side.BOTTOM)]
        center_tile.city = [[Side.LEFT]]
        center_tile.grass = [Side.RIGHT]
        
        # Place it
        state.board[0][0] = center_tile
        
        # 3. Setup Next Tile
        # Tile that matches: Road Bottom-Top (to match Center's Top)
        next_tile = Tile(description="Next")
        next_tile.road = [Connection(Side.BOTTOM, Side.TOP)]
        next_tile.grass = [Side.LEFT, Side.RIGHT, Side.TOP] # Rest grass
        
        state.next_tile = next_tile
        
        # 4. Check Possible Actions
        print("Checking possible actions...")
        actions = ActionUtil.get_possible_actions(state)
        print(f"Found {len(actions)} possible actions")
        
        for action in actions:
            print(f"Action: {action}")
            
        # 5. Verify specific placement at (-1, 0) (Above center)
        # Center is at (0,0). Top of Center is Road.
        # Next tile has Road at Bottom.
        # So Next Tile at (-1, 0) should fit if rotated 0.
        
        # Let's check TileFitter directly for (-1, 0)
        # Position (-1, 0) corresponds to board index... wait, board is a list of lists.
        # CarcassonneGameState handles coordinate mapping.
        # Let's just check if ANY action is at (-1, 0)
        
        found = False
        for action in actions:
            if hasattr(action, 'coordinate'):
                # Note: Coordinate system might be different from array indices
                # Usually (0,0) is center.
                if action.coordinate.row == -1 and action.coordinate.column == 0:
                    found = True
                    print("Found valid placement at (-1, 0)!")
                    break
        
        if not found:
            print("FAILED: No placement found at (-1, 0)")
            
            # Debug why
            print("Debugging TileFitter for (-1, 0)...")
            # Neighbors for (-1, 0):
            # Top: None
            # Right: None
            # Bottom: Center Tile (0,0)
            # Left: None
            
            # Next Tile (rotated 0)
            # Bottom of Next Tile: Road
            # Top of Center Tile: Road
            
            fits = TileFitter.fits(next_tile, bottom=center_tile)
            print(f"TileFitter.fits(next, bottom=center) = {fits}")
            
            if not fits:
                print("Detailed checks:")
                print(f"Roads fit? {TileFitter.roads_fit(next_tile, bottom=center_tile)}")
                print(f"Cities fit? {TileFitter.cities_fit(next_tile, bottom=center_tile)}")
                print(f"Grass fit? {TileFitter.grass_fits(next_tile, bottom=center_tile)}")
                print(f"Rivers fit? {TileFitter.rivers_fit(next_tile, bottom=center_tile)}")

if __name__ == '__main__':
    unittest.main()
