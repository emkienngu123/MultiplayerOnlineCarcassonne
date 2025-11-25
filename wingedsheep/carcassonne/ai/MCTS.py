from wingedsheep.carcassonne.carcassonne_game import CarcassonneGame
from wingedsheep.carcassonne.carcassonne_game_state import CarcassonneGameState
from wingedsheep.carcassonne.objects.actions.action import Action
from wingedsheep.carcassonne.utils.action_util import ActionUtil
from wingedsheep.carcassonne.utils.state_updater import StateUpdater
from copy import deepcopy
from typing import List, Optional
import math
import random

class MCTSNode:
    """A node in the MCTS tree, representing a game state."""
    def __init__(self, state: CarcassonneGameState, parent: 'MCTSNode' = None, action: Action = None):
        self.state: CarcassonneGameState = state
        self.parent: Optional[MCTSNode] = parent
        self.action_from_parent: Optional[Action] = action # Action that led to this state
        
        self.children: List[MCTSNode] = []
        # FIX: Get untried actions directly from ActionUtil on the state
        self.untried_actions: List[Action] = ActionUtil.get_possible_actions(self.state)
        
        self.wins: float = 0
        self.visits: int = 0

class SimpleMCTS:
    """
    A basic implementation of Monte Carlo Tree Search for Carcassonne.
    """
    def __init__(self, player_id: int, simulations: int = 1000, exploration_factor: float = 1.4, max_rollout_depth: int = 30):
        self.player_id = player_id
        self.simulations = simulations
        self.exploration_factor = exploration_factor
        self.max_rollout_depth = max_rollout_depth

    def get_action(self, game_state: CarcassonneGameState) -> Action:
        """
        Runs MCTS simulations and returns the best action from the root.
        """
        # Ensure the state is deep-copied to prevent tree search from altering the actual game state
        root_state = deepcopy(game_state)
        root_node = MCTSNode(state=root_state)
        
        for _ in range(self.simulations):
            node = self._select(root_node)
            
            if not node.state.is_terminated():
                if node.untried_actions:
                    node = self._expand(node)
            
            winner = self._simulate(node.state)
            self._backpropagate(node, winner)
            
        
        if not root_node.children:
            possible = ActionUtil.get_possible_actions(game_state)
            return possible[0] if possible else Action() # Fallback

        # Choose the action leading to the child with the highest visit count
        best_child = max(root_node.children, key=lambda c: c.visits)
        
        return best_child.action_from_parent

    def _select(self, node: MCTSNode) -> MCTSNode:
        """
        Selects a node using the UCB1 formula until an unexpanded or terminal node is reached.
        """
        while not node.state.is_terminated() and not node.untried_actions:
            if not node.children:
                return node
            
            node = max(node.children, key=self._uct_value)
        return node
    
    def _uct_value(self, node: MCTSNode, exploration_factor: float = None) -> float:
        """
        Calculate the UCB1 value for a node.
        """
        if node.visits == 0:
            return float('inf') 
            
        if exploration_factor is None:
            exploration_factor = self.exploration_factor
            
        # Win rate (exploitation)
        exploitation = node.wins / node.visits
        
        # Exploration term
        exploration = exploration_factor * math.sqrt(math.log(node.parent.visits) / node.visits)
        
        return exploitation + exploration

    def _expand(self, node: MCTSNode) -> MCTSNode:
        """
        Selects an untried action, applies it, and adds a new child node.
        """
        action = node.untried_actions.pop(0) 
        new_state = StateUpdater.apply_action(game_state=deepcopy(node.state), action=action)
        
        new_node = MCTSNode(state=new_state, parent=node, action=action)
        node.children.append(new_node)
        return new_node

    def _simulate(self, state: CarcassonneGameState) -> Optional[int]:
        """
        Performs a random rollout (playout) until the game ends.
        Returns the ID of the winner (0 or 1), or None for a tie.
        """
        simulation_state = deepcopy(state)
        move_counter = 0
        # The game loop uses StateUpdater.apply_action and ActionUtil.get_possible_actions
        while not simulation_state.is_terminated():
            if move_counter >= self.max_rollout_depth:
                break
            
            possible_actions = ActionUtil.get_possible_actions(simulation_state)
            
            if not possible_actions:
                break 

            # Randomly select and perform an action
            action = random.choice(possible_actions)
            simulation_state = StateUpdater.apply_action(game_state=simulation_state, action=action)
            move_counter+=1
            
        scores = simulation_state.scores
        if not scores:
            return None
        
        max_score = max(scores)
        winners = [p_id for p_id, score in enumerate(scores) if score == max_score]
        
        if len(winners) == 1:
            return winners[0]
        else:
            return None

    def _backpropagate(self, node: MCTSNode, winner_id: Optional[int]):
        """
        Updates the win/visit counts from the leaf node up to the root.
        """
        current = node
        while current is not None:
            current.visits += 1
            if winner_id == self.player_id:
                current.wins += 1.0 # Win
            elif winner_id is None:
                current.wins += 0.5 # Tie
                
            current = current.parent