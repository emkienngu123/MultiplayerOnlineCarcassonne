
import unittest
from wingedsheep.carcassonne.objects.tile import Tile
from wingedsheep.carcassonne.objects.side import Side
from wingedsheep.carcassonne.utils.tile_fitter import TileFitter

class MockTile(Tile):
    def __init__(self, cities=None, roads=None, grass=None):
        self.cities = cities or []
        self.roads = roads or []
        self.grass = grass or []
        self.river = []

    def get_city_sides(self):
        return self.cities

    def get_road_ends(self):
        return self.roads
    
    def get_river_ends(self):
        return self.river

class TestTileFitter(unittest.TestCase):
    def test_one_sided_validation_bug(self):
        # Center tile has NO city (all grass)
        center = MockTile(grass=[Side.TOP, Side.BOTTOM, Side.LEFT, Side.RIGHT])
        
        # Left neighbor has a city on the RIGHT side
        left = MockTile(cities=[Side.RIGHT], grass=[Side.TOP, Side.BOTTOM, Side.LEFT])
        
        # This should return False because Center's Left (Grass) touches Left's Right (City)
        # But if the bug exists, it will return True because it only checks Center's cities
        fits = TileFitter.cities_fit(center, left=left)
        
        print(f"Center (Grass) vs Left (City): fits = {fits}")
        
        # We expect False, but if bug exists, it will be True
        self.assertFalse(fits, "TileFitter should detect mismatch when neighbor has city and center has grass")

if __name__ == '__main__':
    unittest.main()
