from __future__ import annotations
from duel_game.essential_types import Action, PlayerState
from abc import ABC, abstractmethod
from typing import Callable, TYPE_CHECKING
import random

# to prevent circular import errors (ImportError)
if TYPE_CHECKING:
    from duel_game.game import DuelGame

class Player(ABC):
    def __init__(self, rng=random.Random()):
        self.stamina = 100
        self.health = 100
        self.is_shield_available = True
        self.shield_cd = 0
        self.game: DuelGame
        self.action_in_turn: Action|None = None

    @abstractmethod
    def choose_action(self) -> Action:
        pass

    def set_game(self, gameObject: DuelGame):
        self.game = gameObject

    def get_state(self) -> PlayerState:
        return PlayerState(
            health=self.health,
            stamina=self.stamina,
            is_shield_available=self.is_shield_available,
            shield_cd=self.shield_cd,
            action_in_turn=self.action_in_turn
        )
    
    
class DummyPlayer(Player):
    def __init__(self, policy, rng=random.Random()):
        super.__init__(self, rng)
        self.choose_action = policy.get_policy_performer()

class Policy(ABC):
    @abstractmethod
    def get_policy_performer() -> Callable[[Player], Action]:
        pass

class Agressive(Policy):
    @staticmethod
    def get_policy_performer():
        def func(self: DummyPlayer) -> Action:
            pass
        return func