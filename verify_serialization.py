
import unittest
import json
from enum import Enum
from typing import List, Dict, Any

# --- MOCK CLASSES ---
class Side(Enum):
    TOP = "top"
    RIGHT = "right"
    BOTTOM = "bottom"
    LEFT = "left"
    CENTER = "center"
    def to_json(self): return self.value

class Connection:
    def __init__(self, a: Side, b: Side):
        self.a = a
        self.b = b
    def to_json(self):
        return {"a": self.a.to_json(), "b": self.b.to_json()}
    def __eq__(self, other):
        return self.a == other.a and self.b == other.b

class Tile:
    def __init__(self):
        self.road = []
        self.city = []
        self.grass = []
        self.river = []
        self.description = ""
        self.turns = 0
        self.image = ""
        self.shield = False
        self.chapel = False
        self.flowers = False
        self.cathedral = False
        self.inn = []
        self.unplayable_sides = []

# --- SERVER LOGIC ---
def serialize_tile(tile) -> Dict[str, Any]:
    if not tile: return None
    tile_data = {'turns': getattr(tile, 'turns', 0)}
    if hasattr(tile, 'description'): tile_data['description'] = tile.description
    if hasattr(tile, 'image'): tile_data['image'] = tile.image
    
    # The logic I added to network_server.py
    if hasattr(tile, 'road'):
        tile_data['road'] = [c.to_json() for c in tile.road] if tile.road else []
    if hasattr(tile, 'city'):
        tile_data['city'] = [[s.to_json() for s in city_part] for city_part in tile.city] if tile.city else []
    if hasattr(tile, 'grass'):
        tile_data['grass'] = [s.to_json() for s in tile.grass] if tile.grass else []
    if hasattr(tile, 'river'):
        tile_data['river'] = [c.to_json() for c in tile.river] if tile.river else []
        
    return tile_data

# --- CLIENT LOGIC ---
def str_to_side(side_str: str):
    try:
        for side in Side:
            if side.value == side_str: return side
        return None
    except: return None

def deserialize_connection(conn_data):
    try:
        a = str_to_side(conn_data.get('a'))
        b = str_to_side(conn_data.get('b'))
        if a and b: return Connection(a, b)
        return None
    except: return None

def deserialize_tile(tile_data):
    if not tile_data: return None
    tile = Tile()
    if 'turns' in tile_data: tile.turns = tile_data['turns']
    if 'description' in tile_data: tile.description = tile_data['description']
    
    # The logic I added to multiplayer_manager.py
    if 'road' in tile_data and tile_data['road']:
        tile.road = []
        for conn_data in tile_data['road']:
            conn = deserialize_connection(conn_data)
            if conn: tile.road.append(conn)
            
    if 'city' in tile_data and tile_data['city']:
        tile.city = []
        for city_part in tile_data['city']:
            deserialized_part = []
            for side_str in city_part:
                side = str_to_side(side_str)
                if side: deserialized_part.append(side)
            if deserialized_part: tile.city.append(deserialized_part)
            
    if 'grass' in tile_data and tile_data['grass']:
        tile.grass = []
        for side_str in tile_data['grass']:
            side = str_to_side(side_str)
            if side: tile.grass.append(side)
            
    return tile

# --- TEST CASE ---
class TestSerialization(unittest.TestCase):
    def test_full_cycle(self):
        # 1. Create original tile
        original = Tile()
        original.description = "Test Tile"
        original.road = [Connection(Side.TOP, Side.BOTTOM)]
        original.city = [[Side.LEFT]]
        original.grass = [Side.RIGHT, Side.CENTER]
        
        print("Original:", original.__dict__)
        
        # 2. Serialize (Server)
        serialized = serialize_tile(original)
        print("Serialized:", json.dumps(serialized, indent=2))
        
        # 3. Deserialize (Client)
        restored = deserialize_tile(serialized)
        print("Restored:", restored.__dict__)
        
        # 4. Verify
        self.assertEqual(restored.description, original.description)
        self.assertEqual(len(restored.road), 1)
        self.assertEqual(restored.road[0].a, Side.TOP)
        self.assertEqual(restored.road[0].b, Side.BOTTOM)
        
        self.assertEqual(len(restored.city), 1)
        self.assertEqual(restored.city[0][0], Side.LEFT)
        
        self.assertEqual(len(restored.grass), 2)
        self.assertIn(Side.RIGHT, restored.grass)
        
        print("Verification Successful!")

if __name__ == '__main__':
    unittest.main()
