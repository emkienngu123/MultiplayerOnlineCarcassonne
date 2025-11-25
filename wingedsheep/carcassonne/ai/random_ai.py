import random
import time
from wingedsheep.carcassonne.carcassonne_game import CarcassonneGame
from wingedsheep.carcassonne.objects.actions.action import Action

class RandomAI:
    def __init__(self):
        pass

    def get_move(self, game: CarcassonneGame) -> Action:
        possible_actions = game.get_possible_actions()
        if not possible_actions:
            return None
        
        return random.choice(possible_actions)
