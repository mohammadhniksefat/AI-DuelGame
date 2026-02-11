from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from typing import List

class Action(IntEnum):
    ATTACK = 1
    DEFENSE = 2
    DODGE = 3
    HEAL = 4

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