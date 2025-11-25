from typing import Set

from wingedsheep.carcassonne.carcassonne_game_state import CarcassonneGameState
from wingedsheep.carcassonne.objects.rotation import Rotation
from wingedsheep.carcassonne.objects.side import Side
from wingedsheep.carcassonne.objects.tile import Tile
from wingedsheep.carcassonne.utils.river_rotation_util import RiverRotationUtil


class TileFitter:

    @classmethod
    def grass_fits(cls, center: Tile, top: Tile = None, right: Tile = None, bottom: Tile = None,
                   left: Tile = None) -> bool:
        if left is not None and center.grass.__contains__(Side.LEFT) != left.grass.__contains__(Side.RIGHT):
            return False
        if right is not None and center.grass.__contains__(Side.RIGHT) != right.grass.__contains__(Side.LEFT):
            return False
        if top is not None and center.grass.__contains__(Side.TOP) != top.grass.__contains__(Side.BOTTOM):
            return False
        if bottom is not None and center.grass.__contains__(Side.BOTTOM) != bottom.grass.__contains__(Side.TOP):
            return False
        return True

    @classmethod
    def cities_fit(cls, center: Tile, top: Tile = None, right: Tile = None, bottom: Tile = None, left: Tile = None) -> bool:
        if left is not None and center.get_city_sides().__contains__(Side.LEFT) != left.get_city_sides().__contains__(Side.RIGHT):
            return False
        if right is not None and center.get_city_sides().__contains__(Side.RIGHT) != right.get_city_sides().__contains__(Side.LEFT):
            return False
        if top is not None and center.get_city_sides().__contains__(Side.TOP) != top.get_city_sides().__contains__(Side.BOTTOM):
            return False
        if bottom is not None and center.get_city_sides().__contains__(Side.BOTTOM) != bottom.get_city_sides().__contains__(Side.TOP):
            return False
        return True

    @classmethod
    def roads_fit(cls, center: Tile, top: Tile = None, right: Tile = None, bottom: Tile = None, left: Tile = None) -> bool:
        if left is not None and center.get_road_ends().__contains__(Side.LEFT) != left.get_road_ends().__contains__(Side.RIGHT):
            return False
        if right is not None and center.get_road_ends().__contains__(Side.RIGHT) != right.get_road_ends().__contains__(Side.LEFT):
            return False
        if top is not None and center.get_road_ends().__contains__(Side.TOP) != top.get_road_ends().__contains__(Side.BOTTOM):
            return False
        if bottom is not None and center.get_road_ends().__contains__(Side.BOTTOM) != bottom.get_road_ends().__contains__(Side.TOP):
            return False
        return True

    @classmethod
    def rivers_fit(cls, center: Tile, top: Tile = None, right: Tile = None, bottom: Tile = None, left: Tile = None,
                   game_state: CarcassonneGameState = None) -> bool:
        if len(center.get_river_ends()) == 0:
            # Even if center has no river, we must ensure neighbors don't have rivers pointing to center
            if left is not None and left.get_river_ends().__contains__(Side.RIGHT): return False
            if right is not None and right.get_river_ends().__contains__(Side.LEFT): return False
            if top is not None and top.get_river_ends().__contains__(Side.BOTTOM): return False
            if bottom is not None and bottom.get_river_ends().__contains__(Side.TOP): return False
            return True

        connected_side = None
        unconnected_side = None

        # Check connections and identify connected/unconnected sides
        for side in center.get_river_ends():
            if side == Side.LEFT:
                if left is not None:
                    if not left.get_river_ends().__contains__(Side.RIGHT): return False
                    connected_side = Side.LEFT
                else:
                    unconnected_side = Side.LEFT
            elif side == Side.RIGHT:
                if right is not None:
                    if not right.get_river_ends().__contains__(Side.LEFT): return False
                    connected_side = Side.RIGHT
                else:
                    unconnected_side = Side.RIGHT
            elif side == Side.TOP:
                if top is not None:
                    if not top.get_river_ends().__contains__(Side.BOTTOM): return False
                    connected_side = Side.TOP
                else:
                    unconnected_side = Side.TOP
            elif side == Side.BOTTOM:
                if bottom is not None:
                    if not bottom.get_river_ends().__contains__(Side.TOP): return False
                    connected_side = Side.BOTTOM
                else:
                    unconnected_side = Side.BOTTOM

        # Also check if neighbors have rivers pointing to us that we don't reciprocate
        if left is not None and left.get_river_ends().__contains__(Side.RIGHT) and not center.get_river_ends().__contains__(Side.LEFT): return False
        if right is not None and right.get_river_ends().__contains__(Side.LEFT) and not center.get_river_ends().__contains__(Side.RIGHT): return False
        if top is not None and top.get_river_ends().__contains__(Side.BOTTOM) and not center.get_river_ends().__contains__(Side.TOP): return False
        if bottom is not None and bottom.get_river_ends().__contains__(Side.TOP) and not center.get_river_ends().__contains__(Side.BOTTOM): return False

        if connected_side is None:
            return False

        if unconnected_side is not None and game_state.last_river_rotation is not Rotation.NONE and game_state.last_tile_action is not None:
            last_played_tile: Tile = game_state.last_tile_action.tile
            last_played_river_ends: Set[Side] = last_played_tile.get_river_ends()
            river_ends: Set[Side] = {connected_side, unconnected_side}

            rotation: Rotation = RiverRotationUtil.get_river_rotation_ends(previous_river_ends=last_played_river_ends,
                                                                           river_ends=river_ends)
            if rotation == game_state.last_river_rotation:
                return False

        return True

    @classmethod
    def fits(cls, center: Tile, top: Tile = None, right: Tile = None, bottom: Tile = None, left: Tile = None,
             game_state: CarcassonneGameState = None) -> bool:
        if top is None and right is None and bottom is None and left is None:
            return False

        if not cls.grass_fits(center, top, right, bottom, left):
            return False
        if not cls.cities_fit(center, top, right, bottom, left):
            return False
        if not cls.roads_fit(center, top, right, bottom, left):
            return False
        if not cls.rivers_fit(center, top, right, bottom, left, game_state):
            return False
            
        return True
