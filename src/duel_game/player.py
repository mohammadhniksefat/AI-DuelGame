from abc import ABC, abstractmethod
from duel_game.essential_types import Action, PlayerState

class Player(ABC):
    def __init__(self):
        self.stamina = 100
        self.health = 100
        self.is_shield_available = True
        self.shield_cd = 0
        self.game
        self.action_in_turn: Action|None = None

    @abstractmethod
    def choose_action(self) -> Action:
        pass

    def set_game(self, gameObject):
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
    def __init__(self, policy):
        super.__init__(self)
        self.choose_action = policy.get_policy_performer()

class Policy(ABC):
    @abstractmethod
    def get_policy_performer() -> function:
        pass

class Agressive(Policy):
    @staticmethod
    def get_policy_performer():
        def func(self):
            pass
        return func