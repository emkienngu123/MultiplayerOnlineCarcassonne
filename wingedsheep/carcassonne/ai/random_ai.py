from build.lib.wingedsheep.carcassonne.utils.action_util import ActionUtil
import random
import time
from wingedsheep.carcassonne.carcassonne_game_state import CarcassonneGameState
from wingedsheep.carcassonne.objects.actions.action import Action


class RandomAI:
    def __init__(self):
        pass

    def get_action(self, gamestate: CarcassonneGameState) -> Action:
        possible_actions = ActionUtil.get_possible_actions(gamestate)
        if not possible_actions:
            return None
        
        return random.choice(possible_actions)
