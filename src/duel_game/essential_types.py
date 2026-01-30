from dataclasses import dataclass
from enum import Enum

class Action(Enum):
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