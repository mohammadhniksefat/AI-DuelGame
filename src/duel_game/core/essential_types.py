from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from typing import List, Dict

class Action(IntEnum):
    ATTACK = 1
    DEFENSE = 2
    DODGE = 3
    HEAL = 4
    NONE = 5 

    def stamina_cost(self) -> int:
        """Return stamina cost for this action"""
        costs = {
            Action.ATTACK: 50,
            Action.DEFENSE: 0,
            Action.DODGE: 10,
            Action.HEAL: 60,
            Action.NONE: 0
        }
        return costs[self]

    @classmethod
    def to_string(cls, value: int) -> str:
        """Convert action value to readable string"""
        mapping = {
            1: "ATTACK",
            2: "DEFENSE", 
            3: "DODGE",
            4: "HEAL"
        }
        return mapping.get(value, "UNKNOWN")

@dataclass(frozen=True)
class PlayerState:
    health: int
    stamina: int
    is_shield_available: bool
    shield_cd: int
    action_in_turn: Action

@dataclass(frozen=True)
class GameState:
    turn: int
    player_1: PlayerState
    player_2: PlayerState
    
@dataclass(frozen=True)
class DataSample:
    features: List[float]
    label: Action
    turn: int

@dataclass
class PredictionResult:
    """Container for prediction results"""
    predicted_action: Action
    predicted_action_name: str
    confidence: float
    all_probabilities: Dict[str, float]
    model_used: str
    run_id: int

# Total features: 24
features = [
    # Core State (6)
    "player_hp", "enemy_hp", "player_stamina", "enemy_stamina", 
    "turn", "shield_available",
    
    # Action History (10)
    "count_attack", "count_defense", "count_dodge", "count_heal",
    "last_attack", "last_defense", "last_dodge", "last_heal",
    "stamina_spent_recent", "hp_delta_recent",
    
    # Feasibility (4)
    "can_attack", "can_heal", "can_dodge", "can_defend",
    
    # Risk Context (3)
    "hp_diff", "low_hp", "low_stamina",
    
    # Enemy Prediction (1)
    "enemy_attack_likelihood"
]