from __future__ import annotations
from duel_game.core.essential_types import Action, PlayerState, DataSample
from duel_game.core.ml_model import TrainedModel
from duel_game.core.helpers import break_down_probability, compute_imminent_attack_likely, get_base_path, is_in_bundled
from abc import ABC, abstractmethod
from typing import Callable, TYPE_CHECKING, Dict, Callable, Type
from enum import Enum
import random
from dotenv import load_dotenv
import os

# to prevent circular import errors (ImportError)
if TYPE_CHECKING:
    from duel_game.core.game import DuelGame

if not is_in_bundled():
    # Load environment variables
    load_dotenv(get_base_path() / '.env')

class Player(ABC):
    def __init__(self, rng=random.Random()):
        self.stamina = 100
        self.health = 100
        self.is_shield_available = True
        self.shield_cd = 0
        self.game: DuelGame
        self.opponent: Player
        self.action_in_turn: Action|None = None
        self.rng = rng

    def choose_action(self) -> Action:
        pass

    def set_game(self, gameObject: DuelGame):
        self.game = gameObject

    def set_opponent(self, opponent: Player):
        self.opponent = opponent

    def choose_random_feasible_action(self):
        possible_actions = list(Action)
        if self.stamina < Action.ATTACK.stamina_cost():
            possible_actions.remove(Action.ATTACK)
        if self.stamina < Action.HEAL.stamina_cost():
            possible_actions.remove(Action.HEAL)
        if not self.is_shield_available:
            possible_actions.remove(Action.DEFENSE)
        
        return self.rng.choice(possible_actions)    

    def is_action_feasible(self, action: Action|None):
        if action == Action.HEAL:
            return self.stamina >= Action.HEAL.stamina_cost() and self.health < 100
        elif action == Action.ATTACK:
            return self.stamina >= Action.ATTACK.stamina_cost()
        elif action == Action.DEFENSE:
            return self.is_shield_available
        return True   # Dodge and None are always feasible


    # returns a list of opponent actions like [last_action(0), 2_turns_ago_action,..., n_turns_ago_action]
    def get_opponent_recent_actions(self, turns_number):
        is_history_fully_available = len(self.game.tracker.records) == turns_number
        return [record.player_2.action_in_turn for record in \
            (self.game.tracker.records if is_history_fully_available else self.game.tracker.records[-int(turns_number):])]

    def get_state(self) -> PlayerState:
        return PlayerState(
            health=self.health,
            stamina=self.stamina,
            is_shield_available=self.is_shield_available,
            shield_cd=self.shield_cd,
            action_in_turn=self.action_in_turn
        )
    
class ArtificialPlayer(Player):
    def __init__(self, prediction_model: TrainedModel, rng=random.Random()):
        super().__init__(rng)
        self.model = prediction_model

    def choose_action(self) -> Action:
        last_round_sample: DataSample|None = self.game.tracker.get_last_sample()
        predicted_action: Action|None = self.model.predict(last_round_sample.features if last_round_sample is not None else None)

        if predicted_action == Action.ATTACK and not self.game.player_1.is_action_feasible(predicted_action):
            predicted_action = Action.NONE

        my_action: Action = Action.NONE
        if not self.game.player_1.is_action_feasible(Action.ATTACK) and not self.is_action_feasible(Action.ATTACK):
            my_action = Action.NONE
        else:
            if predicted_action == Action.ATTACK:
                if self.is_action_feasible(Action.DEFENSE):
                    my_action = Action.DEFENSE
                elif self.is_action_feasible(Action.HEAL):
                    my_action = Action.HEAL
                else:
                    my_action = Action.DODGE
            elif predicted_action in [Action.DEFENSE, Action.DODGE, Action.HEAL, Action.NONE]:
                if self.health < 50 and self.is_action_feasible(Action.HEAL) and random.random() > 0.5:
                    my_action = Action.HEAL
                elif self.is_action_feasible(Action.ATTACK):
                    my_action = Action.ATTACK
                else:
                    my_action = Action.DODGE
            else:
                raise ValueError('unexpected predicted_value provided by model.predict(): ', predicted_action)

        return my_action

    
class DummyPlayer(Player):
    def __init__(self, policy: Type[Policy], rng=random.Random()):
        super().__init__(rng)
        self.policy_performer = policy.get_policy_performer()
        self.archtype = policy.archtype
    
    def choose_action(self) -> Action:
        return self.policy_performer(self)


class Policy(ABC):
    @abstractmethod
    def get_policy_performer() -> Callable[[Player], Action]:
        pass


class Aggressive(Policy):
    archtype = 'aggressive'

    @staticmethod
    def get_policy_performer():
        def func(self: DummyPlayer) -> Action:
            EPSILON = float(os.getenv('AGGRESSIVE_EPSILON', '0.1'))
            ATTACK_BIAS = float(os.getenv('AGGRESSIVE_ATTACK_BIAS', '0.7'))
            HEAL_THRESHOLD = float(os.getenv('AGGRESSIVE_HEAL_THRESHOLD', '40'))
            ATTACK_THREAT_THRESHOLD = float(os.getenv('AGGRESSIVE_ATTACK_THREAT_THRESHOLD', '0.6'))
            THREAT_HISTORY_LENGTH = float(os.getenv('AGGRESSIVE_ATTACK_THREAT_HISTORY_LENGTH', '5'))
            
            if self.rng.random() < EPSILON:
                return self.choose_random_feasible_action()
            
            action = None
            if self.health <= HEAL_THRESHOLD:
                if self.stamina >= Action.HEAL.stamina_cost():
                    action = Action.HEAL
                elif self.is_shield_available and \
                    compute_imminent_attack_likely(self ,THREAT_HISTORY_LENGTH) > ATTACK_THREAT_THRESHOLD:
                    action = Action.DEFENSE

            if action is None:
                if self.stamina >= Action.ATTACK.stamina_cost():
                    if self.rng.random() < ATTACK_BIAS:
                        action = Action.ATTACK
                    else:
                        action = Action.DODGE
            
            if action is None or not self.is_action_feasible(action):
                return self.choose_random_feasible_action()

            return action
        return func
    

# Policy 2: Defensive
class Defensive(Policy):
    archtype = 'defensive'

    @staticmethod
    def get_policy_performer():
        def func(self: DummyPlayer) -> Action:
            EPSILON = float(os.getenv('DEFENSIVE_EPSILON', '0.1'))
            ATTACK_PROB_OPP_HP_LOW = float(os.getenv('DEFENSIVE_ATTACK_PROB_OPP_HP_LOW', '0.6'))
            OPP_HP_THRESHOLD = float(os.getenv('DEFENSIVE_OPP_HP_THRESHOLD', '30'))
            HEAL_BIAS = float(os.getenv('DEFENSIVE_HEAL_BIAS', '0.6'))
            DEFENSE_BIAS = float(os.getenv('DEFENSIVE_DEFENSE_BIAS', '0.7'))
            ATTACK_THREAT_THRESHOLD = float(os.getenv('DEFENSIVE_ATTACK_THREAT_THRESHOLD', '0.4'))
            ATTACK_THREAT_HISTORY_LENGTH = float(os.getenv('DEFENSIVE_ATTACK_THREAT_HISTORY_LENGTH', '5'))
            ATTACK_START_TURN_THRESHOLD = int(os.getenv('DEFENSIVE_ATTACK_START_TURN_THRESHOLD', '5'))
            
            if self.rng.random() < EPSILON:
                return self.choose_random_feasible_action()
            
            action = None
            
            # Check opponent's HP for opportunistic attack
            if self.opponent.health < OPP_HP_THRESHOLD and self.rng.random() < ATTACK_PROB_OPP_HP_LOW:
                if self.stamina >= Action.ATTACK.stamina_cost():
                    action = Action.ATTACK
                else:
                    action = Action.DODGE
            else:
                # Defensive logic based on own HP
                if self.health <= 60:
                    if self.rng.random() < HEAL_BIAS and self.stamina >= Action.HEAL.stamina_cost():
                        action = Action.HEAL
                    elif self.rng.random() < DEFENSE_BIAS and self.is_shield_available:
                        action = Action.DEFENSE
                    elif self.rng.random() < 0.2:
                        action = Action.ATTACK
                    else:
                        action = Action.DODGE
                elif self.game.turn > ATTACK_START_TURN_THRESHOLD and \
                     compute_imminent_attack_likely(self, ATTACK_THREAT_HISTORY_LENGTH) < ATTACK_THREAT_THRESHOLD and \
                     self.stamina >= Action.ATTACK.stamina_cost():
                    action = Action.ATTACK
                else:
                    if self.rng.random() < 0.5 and self.is_shield_available:
                        action = Action.DEFENSE
                    else:
                        action = Action.DODGE
            
            if action is None or not self.is_action_feasible(action):
                return self.choose_random_feasible_action()
            
            return action
        return func


# Policy 3: Balanced/Tactical
class Balanced(Policy):
    archtype = 'balanced'

    @staticmethod
    def get_policy_performer():
        def func(self: DummyPlayer) -> Action:
            EPSILON = float(os.getenv('BALANCED_EPSILON', '0.1'))
            DOMINATION_MARGIN = float(os.getenv('BALANCED_DOMINATION_MARGIN', '30'))
            DESPERATION_MARGIN = float(os.getenv('BALANCED_DESPERATION_MARGIN', '-20'))
            
            if self.rng.random() < EPSILON:
                return self.choose_random_feasible_action()
            
            # Calculate HP difference (self - opponent)
            hp_diff = self.health - self.opponent.health
            
            # Domination situation
            if hp_diff >= DOMINATION_MARGIN and self.stamina >= Action.ATTACK.stamina_cost():
                return Action.ATTACK
            
            # Desperation situation
            elif hp_diff <= DESPERATION_MARGIN:
                if self.is_shield_available:
                    return Action.DEFENSE
                elif self.stamina >= Action.HEAL.stamina_cost():
                    return Action.HEAL
                else:
                    return Action.DODGE
            
            # Neutral situation - weighted random choice
            else:
                # Calculate weights based on stamina and health ratios
                stamina_ratio = self.stamina / 100.0
                health_ratio = self.health / 100.0
                
                w_attack = stamina_ratio * health_ratio
                w_defense = (1 - stamina_ratio) * (1 - health_ratio)
                w_heal = 1 - health_ratio
                w_dodge = 1 - abs(stamina_ratio - 0.5)
                
                # Normalize weights
                total_weight = w_attack + w_defense + w_heal + w_dodge
                weights = {
                    Action.ATTACK: w_attack / total_weight,
                    Action.DEFENSE: w_defense / total_weight,
                    Action.HEAL: w_heal / total_weight,
                    Action.DODGE: w_dodge / total_weight
                }
                
                # Filter feasible actions and adjust weights
                feasible_weights = {}
                for action, weight in weights.items():
                    if self.is_action_feasible(action):
                        feasible_weights[action] = weight
                
                if not feasible_weights:
                    return self.choose_random_feasible_action()
                
                # Normalize feasible weights
                total_feasible = sum(feasible_weights.values())
                if total_feasible > 0:
                    for action in feasible_weights:
                        feasible_weights[action] /= total_feasible
                    
                    # Weighted random choice
                    r = self.rng.random()
                    cumulative = 0
                    for action, weight in feasible_weights.items():
                        cumulative += weight
                        if r <= cumulative:
                            return action
                
                return self.choose_random_feasible_action()
        return func


# Policy 4: Healer/Sustain
class Healer(Policy):
    archtype = 'healer'

    @staticmethod
    def get_policy_performer():
        def func(self: DummyPlayer) -> Action:
            EPSILON = float(os.getenv('HEALER_EPSILON', '0.1'))
            HEAL_THRESHOLD = float(os.getenv('HEALER_HEAL_THRESHOLD', '80'))
            HEAL_BIAS = float(os.getenv('HEALER_HEAL_BIAS', '0.8'))
            ATTACK_PROB = float(os.getenv('HEALER_ATTACK_PROB', '0.3'))
            
            if self.rng.random() < EPSILON:
                return self.choose_random_feasible_action()
            
            if self.health < HEAL_THRESHOLD:
                if self.stamina >= Action.HEAL.stamina_cost() and self.rng.random() < HEAL_BIAS:
                    action = Action.HEAL
                elif self.is_shield_available:
                    action = Action.DEFENSE
                else:
                    action = Action.DODGE
            else:
                if self.rng.random() < ATTACK_PROB and self.stamina >= Action.ATTACK.stamina_cost():
                    action = Action.ATTACK
                else:
                    action = Action.DODGE
            
            if action is None or not self.is_action_feasible(action):
                return self.choose_random_feasible_action()
            
            return action
        return func


# Policy 5: Opportunist/Counter
class Opportunist(Policy):
    archtype = 'opportunist'

    @staticmethod
    def get_policy_performer():
        def func(self: DummyPlayer) -> Action:
            EPSILON = float(os.getenv('OPPORTUNIST_EPSILON', '0.1'))
            DECISION_THRESHOLD = float(os.getenv('OPPORTUNIST_DECISION_THRESHOLD', '0.5'))
            BASE_TURN_NUMBER = int(os.getenv('OPPORTUNIST_BASE_TURN_NUMBER', '5'))
            HEAL_THRESHOLD = float(os.getenv('OPPORTUNIST_HEAL_THRESHOLD', '35'))
            HEAL_BIAS = float(os.getenv('OPPORTUNIST_HEAL_BIAS', '0.85'))
            
            if self.rng.random() < EPSILON:
                return self.choose_random_feasible_action()
            
            # Analyze opponent's recent actions
            recent_actions = self.get_opponent_recent_actions(BASE_TURN_NUMBER)
            defensive_actions_count = sum(1 for action in recent_actions 
                                        if action in [Action.DEFENSE, Action.DODGE])
            offensive_actions_count = sum(1 for action in recent_actions 
                                        if action == Action.ATTACK)
            
            defensive_ratio = defensive_actions_count / BASE_TURN_NUMBER
            offensive_ratio = offensive_actions_count / BASE_TURN_NUMBER
            
            # Health check first
            if self.health < HEAL_THRESHOLD and self.rng.random() < HEAL_BIAS:
                if self.stamina >= Action.HEAL.stamina_cost():
                    return Action.HEAL
            
            # Pattern-based decision making
            if defensive_ratio > DECISION_THRESHOLD:
                # Opponent is being defensive, attack
                if self.stamina >= Action.ATTACK.stamina_cost():
                    return Action.ATTACK
                else:
                    return Action.DODGE
            elif offensive_ratio > DECISION_THRESHOLD:
                # Opponent is being offensive, defend/dodge
                if self.is_shield_available:
                    return Action.DEFENSE
                else:
                    return Action.DODGE
            else:
                # No clear pattern, random choice between attack, defense, dodge
                feasible_actions = []
                if self.stamina >= Action.ATTACK.stamina_cost():
                    feasible_actions.append(Action.ATTACK)
                if self.is_shield_available:
                    feasible_actions.append(Action.DEFENSE)
                feasible_actions.append(Action.DODGE)  # Always feasible
                
                if not feasible_actions:
                    return self.choose_random_feasible_action()
                
                return self.rng.choice(feasible_actions)
        return func


# Policy 6: Random-biased
class RandomBiased(Policy):
    archtype = 'random-biased'

    @staticmethod
    def get_policy_performer():
        def func(self: DummyPlayer) -> Action:
            # Load weights from environment
            W_ATTACK = float(os.getenv('RANDOM_BIASED_W_ATTACK', '0.25'))
            W_DEFENSE = float(os.getenv('RANDOM_BIASED_W_DEFENSE', '0.25'))
            W_DODGE = float(os.getenv('RANDOM_BIASED_W_DODGE', '0.25'))
            W_HEAL = float(os.getenv('RANDOM_BIASED_W_HEAL', '0.25'))
            
            # Initial weights
            weights = {
                Action.ATTACK: W_ATTACK,
                Action.DEFENSE: W_DEFENSE,
                Action.DODGE: W_DODGE,
                Action.HEAL: W_HEAL
            }
            
            # Check feasibility and adjust weights
            if self.stamina < Action.HEAL.stamina_cost():
                if Action.HEAL in weights:
                    weights = break_down_probability(weights, Action.HEAL)
            
            if not self.is_shield_available:  # Defense requires shield
                if Action.DEFENSE in weights:
                    weights = break_down_probability(weights, Action.DEFENSE)
            
            if self.stamina < Action.ATTACK.stamina_cost():
                if Action.ATTACK in weights:
                    weights = break_down_probability(weights, Action.ATTACK)
            
            # Ensure we have at least one feasible action
            if not weights:
                return self.choose_random_feasible_action()
            
            # Weighted random choice among remaining actions
            actions = list(weights.keys())
            probabilities = list(weights.values())
            
            # Normalize probabilities
            total = sum(probabilities)
            if total > 0:
                probabilities = [p / total for p in probabilities]
                return self.rng.choices(actions, weights=probabilities, k=1)[0]
            else:
                return self.choose_random_feasible_action()
        return func
