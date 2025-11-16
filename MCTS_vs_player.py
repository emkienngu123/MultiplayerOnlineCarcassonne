import pygame
import os
import math
import random
from copy import deepcopy
from typing import List, Optional, Tuple

from wingedsheep.carcassonne.carcassonne_game import CarcassonneGame
# --- ADDED: Required imports for MCTS to interact with state copies ---
from wingedsheep.carcassonne.carcassonne_game_state import CarcassonneGameState
from wingedsheep.carcassonne.utils.action_util import ActionUtil
from wingedsheep.carcassonne.utils.state_updater import StateUpdater
# ---------------------------------------------------------------------
from wingedsheep.carcassonne.objects.actions.action import Action
from wingedsheep.carcassonne.tile_sets.tile_sets import TileSet
from wingedsheep.carcassonne.tile_sets.supplementary_rules import SupplementaryRule
from wingedsheep.carcassonne.objects.side import Side
from wingedsheep.carcassonne.objects.meeple_type import MeepleType
import wingedsheep


# --- FIXED MCTS IMPLEMENTATION STARTS HERE ---

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
    def __init__(self, player_id: int, simulations: int = 1000, exploration_factor: float = 1.4):
        self.player_id = player_id
        self.simulations = simulations
        self.exploration_factor = exploration_factor

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
        
        # The game loop uses StateUpdater.apply_action and ActionUtil.get_possible_actions
        while not simulation_state.is_terminated():
            
            possible_actions = ActionUtil.get_possible_actions(simulation_state)
            
            if not possible_actions:
                break 

            # Randomly select and perform an action
            action = random.choice(possible_actions)
            simulation_state = StateUpdater.apply_action(game_state=simulation_state, action=action)
            
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

# --- FIXED MCTS IMPLEMENTATION ENDS HERE ---


TILE_SIZE = 60
WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 1000


PREVIEW_TILE_X = 100
PREVIEW_TILE_Y = 100
SNAP_THRESHOLD = 45 


meeple_size = 15
big_meeple_size = 25
meeple_image_cache = {}

# [meeple_position_offsets and big_meeple_position_offsets remain the same]
meeple_position_offsets = {
    Side.TOP: (TILE_SIZE / 2, (meeple_size / 2) + 3),
    Side.RIGHT: (TILE_SIZE - (meeple_size / 2) - 3, TILE_SIZE / 2),
    Side.BOTTOM: (TILE_SIZE / 2, TILE_SIZE - (meeple_size / 2) - 3),
    Side.LEFT: ((meeple_size / 2) + 3, TILE_SIZE / 2),
    Side.CENTER: (TILE_SIZE / 2, TILE_SIZE / 2),
    Side.TOP_LEFT: (TILE_SIZE / 4, (meeple_size / 2) + 3),
    Side.TOP_RIGHT: ((TILE_SIZE / 4) * 3, (meeple_size / 2) + 3),
    Side.BOTTOM_LEFT: (TILE_SIZE / 4, TILE_SIZE - (meeple_size / 2) - 3),
    Side.BOTTOM_RIGHT: ((TILE_SIZE / 4) * 3, TILE_SIZE - (meeple_size / 2) - 3)
}

big_meeple_position_offsets = {
    Side.TOP: (TILE_SIZE / 2, (big_meeple_size / 2) + 3),
    Side.RIGHT: (TILE_SIZE - (big_meeple_size / 2) - 3, TILE_SIZE / 2),
    Side.BOTTOM: (TILE_SIZE / 2, TILE_SIZE - (big_meeple_size / 2) - 3),
    Side.LEFT: ((big_meeple_size / 2) + 3, TILE_SIZE / 2),
    Side.CENTER: (TILE_SIZE / 2, TILE_SIZE / 2),
    Side.TOP_LEFT: (TILE_SIZE / 4, (big_meeple_size / 2) + 3),
    Side.TOP_RIGHT: ((TILE_SIZE / 4) * 3, (big_meeple_size / 2) + 3),
    Side.BOTTOM_LEFT: (TILE_SIZE / 4, TILE_SIZE - (big_meeple_size / 2) - 3),
    Side.BOTTOM_RIGHT: ((TILE_SIZE / 4) * 3, TILE_SIZE - (big_meeple_size / 2) - 3)
}


from wingedsheep.carcassonne.objects.meeple_type import MeepleType

# [meeple_icons and get_meeple_image_path remain the same]
meeple_icons = {
    MeepleType.NORMAL: ["blue_meeple.png", "red_meeple.png", "black_meeple.png", "yellow_meeple.png", "green_meeple.png", "pink_meeple.png"],
    MeepleType.ABBOT: ["blue_abbot.png", "red_abbot.png", "black_abbot.png", "yellow_abbot.png", "green_abbot.png", "pink_abbot.png"]
}

def get_meeple_image_path(player: int, 
                          meeple_type: MeepleType, 
                          base_images_path: str) -> str:
    
    icon_type = MeepleType.NORMAL
    if meeple_type == MeepleType.ABBOT:
        icon_type = meeple_type

    if icon_type not in meeple_icons:
        print(f"Error: Meeple icon type {icon_type} not in meeple_icons map!")
        return ""
        
    if player >= len(meeple_icons[icon_type]):
        player = 0

    image_filename = meeple_icons[icon_type][player]
    abs_file_path = os.path.join(base_images_path, image_filename)
    
    return abs_file_path


pygame.init()
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Carcassonne – Minimal Pygame UI")

images_path = os.path.join(wingedsheep.__path__[0], 'carcassonne', 'resources', 'images')
tile_cache = {}

ghost_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
ghost_surface.fill((100, 200, 100, 100))

meeple_ghost = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
meeple_ghost.fill((100, 50, 50, 100))

font = pygame.font.SysFont(None, 26)


# [get_meeple_image remains the same]
def get_meeple_image(player_index: int, meeple_type: MeepleType, is_ghost: bool = False):
    
    size = big_meeple_size if meeple_type == MeepleType.BIG else meeple_size
    key = f"{player_index}_{meeple_type}_{size}"
    if is_ghost:
        key += "_ghost"

    if key in meeple_image_cache:
        return meeple_image_cache[key]

    meep_path = get_meeple_image_path(player_index, meeple_type, images_path)
    
    if not meep_path or not os.path.exists(meep_path):
        meeple_image_cache[key] = None
        return None

    img = pygame.image.load(meep_path).convert_alpha()
    img = pygame.transform.scale(img, (size, size))
    
    if is_ghost:
        img.set_alpha(128)
    
    meeple_image_cache[key] = img
    return img

# [load_tile_image remains the same]
def load_tile_image(tile):
    name = tile.image
    key = f"{name}_{tile.turns}"

    if key in tile_cache:
        return tile_cache[key]

    abs_path = os.path.join(images_path, name)
    img = pygame.image.load(abs_path).convert_alpha()
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img = pygame.transform.rotate(img, -90 * tile.turns)

    tile_cache[key] = img
    return img

# [phase_name_for_state remains the same]
def phase_name_for_state(game_state):
    p = getattr(game_state , 'phase' , None)
    return getattr(p,'name',str(p)).upper() if p is not None else "UNKNOWN"


def draw_phase_indicator(game_state):
    name = phase_name_for_state(game_state)
    # --- MODIFIED: Show Current Player and Phase ---
    player_names = {0: "Human (Blue)", 1: "MCTS (Red)"}
    current_player_name = player_names.get(game_state.current_player, f"Player {game_state.current_player}")
    
    text = f"Player {game_state.current_player + 1}: {current_player_name} | Phase: {name}"
    # --- END MODIFIED ---
    surf = font.render(text, True, (20, 20, 20))
    window.blit(surf, (10, WINDOW_HEIGHT - 30))

    # contextual hint
    if "MEEP" in name:  # matches MEEPLE or similar
        hint = "Left-click highlighted tile to place meeple. Press P to pass."
    else:
        hint = "Drag tile from preview to board. Right-click preview or while dragging to rotate."
    hint_surf = font.render(hint, True, (60, 60, 60))
    window.blit(hint_surf, (10, WINDOW_HEIGHT - 60))

def draw_ghosts(game_state):
    # Only draw ghosts for the human player
    if game_state.current_player != HUMAN_PLAYER_INDEX:
        return

    # Decide which ghosts to draw depending on phase
    name = phase_name_for_state(game_state)
    next_tile = game_state.next_tile
    possible_actions = game.get_possible_actions()

    if "MEEP" in name:
        # Draw meeple placement hints (small circle) on valid tiles
        for action in possible_actions:
            # Meeple actions typically have a coordinate but not tile_rotations
            if  hasattr(action , 'coordinate_with_side') and hasattr(action , 'meeple_type'):
                
                # Use the center of the meeple for drawing the ghost
                if action.meeple_type == MeepleType.BIG:
                    offs = big_meeple_position_offsets[action.coordinate_with_side.side]
                else:
                    offs = meeple_position_offsets[action.coordinate_with_side.side]
                    
                ghost_x_center = action.coordinate_with_side.coordinate.column * TILE_SIZE + offs[0]
                ghost_y_center = action.coordinate_with_side.coordinate.row * TILE_SIZE + offs[1]
                
                meep_img = get_meeple_image(game_state.current_player, action.meeple_type , is_ghost=True)
                
                # Draw using top-left corner
                draw_x = ghost_x_center - meep_img.get_width() // 2
                draw_y = ghost_y_center - meep_img.get_height() // 2
                
                window.blit(meep_img, (draw_x, draw_y))
    else:
        # Tile placement ghosts
        if next_tile is None:
            return

        current_rotation = next_tile.turns

        for action in possible_actions:
            if (hasattr(action,'coordinate') and hasattr(action,'tile_rotations')) and action.tile_rotations == current_rotation:
                ghost_x_px = action.coordinate.column * TILE_SIZE
                ghost_y_px = action.coordinate.row * TILE_SIZE
                window.blit(ghost_surface, (ghost_x_px, ghost_y_px))

# [draw_placed_meeples remains the same]
def draw_placed_meeples(game_state):
    for player, placed_meeples in enumerate(game_state.placed_meeples):
        for meeple_position in placed_meeples:
            img = get_meeple_image(player, meeple_position.meeple_type)
            # Use the correct offset based on meeple size
            if meeple_position.meeple_type == MeepleType.BIG:
                offs = big_meeple_position_offsets[meeple_position.coordinate_with_side.side]
            else:
                offs = meeple_position_offsets[meeple_position.coordinate_with_side.side]

            x = meeple_position.coordinate_with_side.coordinate.column * TILE_SIZE + offs[0] - img.get_width() // 2
            y = meeple_position.coordinate_with_side.coordinate.row * TILE_SIZE + offs[1] - img.get_height() // 2

            window.blit(img, (x, y))




# [draw_board remains the same]
def draw_board(game_state , drag_pos):
    window.fill((240, 240, 240))

    


    for r, row in enumerate(game_state.board):
        for c, tile in enumerate(row):
            if tile is not None:
                img = load_tile_image(tile)
                window.blit(img, (c * TILE_SIZE, r * TILE_SIZE))

    next_tile = game_state.next_tile
    if next_tile is not None:
        # Only draw the tile in the drag position if it's the human's turn
        if game_state.current_player == HUMAN_PLAYER_INDEX:
            img = load_tile_image(next_tile)
            window.blit(img,drag_pos)

    draw_ghosts(game_state)
    draw_placed_meeples(game_state)
    draw_phase_indicator(game_state)


    pygame.display.update()


# --- CREATE GAME AND PLAYERS ---
HUMAN_PLAYER_INDEX = 0
MCTS_PLAYER_INDEX = 1

game = CarcassonneGame(
    players=2,
    tile_sets=[TileSet.BASE, TileSet.THE_RIVER, TileSet.INNS_AND_CATHEDRALS],
    supplementary_rules=[SupplementaryRule.ABBOTS, SupplementaryRule.FARMERS]
)

# Initialize MCTS player
mcts_agent = SimpleMCTS(
    player_id=MCTS_PLAYER_INDEX,
    exploration_factor=1.4, 
    simulations=1
)

clock = pygame.time.Clock()
auto_play = False  

is_dragging = False
drag_pos = (PREVIEW_TILE_X, PREVIEW_TILE_Y)
snap_action = None 

running = True
while running:
    
    # --- MCTS Player Logic (Runs if it is the MCTS's turn) ---
    current_player = game.state.current_player
    if not game.is_finished() and current_player == MCTS_PLAYER_INDEX:
        
        # 1. Get MCTS action by passing the game state
        print(f"MCTS Player ({MCTS_PLAYER_INDEX}) is thinking (Simulations: {mcts_agent.simulations})...")
        action_to_take = mcts_agent.get_action(game.state)
        
        # 2. Take the step (using the wrapper game.step)
        print(f"MCTS Player ({MCTS_PLAYER_INDEX}) took action: {action_to_take}")
        game.step(current_player, action_to_take)
        
        # 3. Immediately redraw to show the MCTS move
        draw_board(game.state , drag_pos)
        pygame.time.wait(1000) # Pause for 1 second to make the move visible
        
        # Check if the MCTS move ended the game
        if game.is_finished():
            print("Game finished!")
            break
            
        continue # Skip input handling for the MCTS player's turn
    # --- END MCTS Logic ---
    
    # --- Human Player Input Handling ---
    mouse_x , mouse_y = pygame.mouse.get_pos()
    
    # Only process events if it's the human player's turn
    if current_player == HUMAN_PLAYER_INDEX:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    name = phase_name_for_state(game.state)
                    if "MEEP" in name:
                        possible = game.get_possible_actions()
                        # Find the 'pass' action (no coordinate, no tile_rotations)
                        for a in possible:
                            if not hasattr(a,'coordinate') and not hasattr(a,'tile_rotations'):
                                game.step(game.get_current_player(),a)
                                break

            if event.type == pygame.MOUSEBUTTONDOWN:
                preview_rect = pygame.Rect(PREVIEW_TILE_X, PREVIEW_TILE_Y, TILE_SIZE, TILE_SIZE)
                current_phase = phase_name_for_state(game.state)
                

                if event.button == 1:  # Left-click

                    if "MEEP" in current_phase:
                        possible = game.get_possible_actions()
                        clicked = False

                        for a in possible:
                            if hasattr(a, 'tile_rotations'):
                                continue

                            if hasattr(a, 'coordinate_with_side'):
                                cws = a.coordinate_with_side
                                col = cws.coordinate.column
                                row = cws.coordinate.row
                                side = cws.side

                                if getattr(a, 'meeple_type', None) == MeepleType.BIG:
                                    offs = big_meeple_position_offsets[side]
                                    size = big_meeple_size
                                else:
                                    offs = meeple_position_offsets[side]
                                    size = meeple_size
                                
                                center_x = col * TILE_SIZE + offs[0]
                                center_y = row * TILE_SIZE + offs[1]

                                dist = math.hypot(mouse_x - center_x, mouse_y - center_y)

                                if dist <= (size / 2) + 6:
                                    game.step(game.get_current_player(), a)
                                    clicked = True
                                    break

                        continue
                    
                    if not is_dragging and preview_rect.collidepoint(mouse_x, mouse_y) and game.state.next_tile is not None:
                        is_dragging = True
                
                elif event.button == 3: # Right-click
                    if "MEEP" not in current_phase and game.state.next_tile is not None:
                        if is_dragging or preview_rect.collidepoint(mouse_x, mouse_y):
                            game.state.next_tile.turns = (game.state.next_tile.turns + 1) % 4
                            snap_action = None


            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and is_dragging:
                    is_dragging = False

                    if snap_action is not None:
                        game.step(game.get_current_player() , snap_action)
                        snap_action = None      
                    else :
                        print("Invalid move")


    # --- Human Player Position Update with snapping logic ---
    snap_action = None
    closest_action = None
    min_dist = float('inf')
    
    if current_player == HUMAN_PLAYER_INDEX:
        if game.state.next_tile is not None:
            current_rotation = game.state.next_tile.turns
            possible_actions = game.get_possible_actions()
            current_phase = phase_name_for_state(game.state)
            
            # Find the closest valid snap point
            if "MEEP" not in current_phase:
                for action in possible_actions:
                    if (hasattr(action, 'coordinate') and hasattr(action, 'tile_rotations') and
                        action.tile_rotations == current_rotation):
                        
                        target_x_px = action.coordinate.column * TILE_SIZE + TILE_SIZE // 2
                        target_y_px = action.coordinate.row * TILE_SIZE + TILE_SIZE // 2
                        
                        dist = math.dist((mouse_x, mouse_y), (target_x_px, target_y_px))

                        if dist < min_dist and dist < SNAP_THRESHOLD:
                            min_dist = dist
                            closest_action = action

        if is_dragging:
            if closest_action is not None:
                drag_pos = (closest_action.coordinate.column * TILE_SIZE, closest_action.coordinate.row * TILE_SIZE)
                snap_action = closest_action
            else:
                drag_pos = (mouse_x - TILE_SIZE // 2, mouse_y - TILE_SIZE // 2)
                snap_action = None
        else:
            drag_pos = (PREVIEW_TILE_X, PREVIEW_TILE_Y)
            snap_action = None
    
    # Draw board
    draw_board(game.state , drag_pos)

    if game.is_finished():
        print(f"Game Over! Final scores: {game.state.scores}")
        
    clock.tick(60)

pygame.quit()