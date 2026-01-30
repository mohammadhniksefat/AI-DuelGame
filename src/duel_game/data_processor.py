from duel_game.game import GameState, Action
from dataclasses import dataclass
from typing import List, Dict

@dataclass(frozen=True)
class DataSample:
    features: Dict[str, float]
    label: Action
    turn: int


class Tracker:
    HISTORY_LEN = 5
    MAX_HP = 100
    MAX_STAMINA = 100
    MAX_TURN = 50  # normalization cap

    def __init__(self):
        self.records: List[GameState] = []
        self.data_samples: List[DataSample] = []

    def record(self, game_state: GameState):
        """
        Record a game state AFTER players have chosen actions
        but BEFORE combat resolution.
        """
        self.records.append(game_state)

        features = self._extract_features(game_state)
        sample = DataSample(
            features=features,
            label=game_state.player_1.action_in_turn,
            turn=game_state.turn
        )
        self.data_samples.append(sample)

    def get_samples(self) -> List[DataSample]:
        return self.data_samples
    
    def _extract_features(self, game_state: GameState) -> dict:
        p = game_state.player_1
        e = game_state.player_2

        features = {}

        # ----------------------------
        # A. Core State Features
        # ----------------------------
        features["player_hp"] = p.health / self.MAX_HP
        features["enemy_hp"] = e.health / self.MAX_HP
        features["player_stamina"] = p.stamina / self.MAX_STAMINA
        features["enemy_stamina"] = e.stamina / self.MAX_STAMINA
        features["turn"] = min(game_state.turn / self.MAX_TURN, 1.0)
        features["shield_available"] = float(p.is_shield_available)

        # ----------------------------
        # B. Action History Features
        # ----------------------------
        history = self.records[-self.HISTORY_LEN:]

        action_counts = {a: 0 for a in Action}
        stamina_spent = 0
        hp_delta = 0

        prev_hp = history[0].player_1.health if len(history) > 1 else p.health

        for state in history:
            action = state.player_1.action_in_turn
            action_counts[action] += 1
            stamina_spent += self._stamina_cost(action)
            hp_delta += state.player_1.health - prev_hp
            prev_hp = state.player_1.health

        for action, count in action_counts.items():
            features[f"count_{action.name.lower()}"] = count / self.HISTORY_LEN

        last_action = history[-1].player_1.action_in_turn
        for action in Action:
            features[f"last_{action.name.lower()}"] = float(action == last_action)

        features["stamina_spent_recent"] = stamina_spent / (self.MAX_STAMINA * self.HISTORY_LEN)
        features["hp_delta_recent"] = hp_delta / self.MAX_HP

        # ----------------------------
        # C. Feasibility Indicators
        # ----------------------------
        features["can_attack"] = float(p.stamina >= 30)
        features["can_heal"] = float(p.stamina >= 45)
        features["can_dodge"] = float(p.stamina >= 10)
        features["can_defend"] = 1.0

        # ----------------------------
        # D. Risk Context Features
        # ----------------------------
        features["hp_diff"] = (p.health - e.health) / self.MAX_HP
        features["low_hp"] = float(p.health < 0.3 * self.MAX_HP)
        features["low_stamina"] = float(p.stamina < 0.3 * self.MAX_STAMINA)

        return features

    @staticmethod
    def _stamina_cost(action: Action) -> int:
        return {
            Action.ATTACK: 30,
            Action.DEFENSE: 0,
            Action.DODGE: 10,
            Action.HEAL: 45
        }[action]