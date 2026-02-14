from duel_game.core.essential_types import GameState, Action
from duel_game.core.essential_types import features as feature_names
from duel_game.core.helpers import compute_imminent_attack_likely
from duel_game.core.essential_types import DataSample
from dotenv import load_dotenv
from typing import List, Dict


class Tracker:
    HISTORY_LEN = 5
    MAX_HP = 100
    MAX_STAMINA = 100
    MAX_TURN = 50  # normalization cap'
    THREAT_THRESHOLD = 0.5

    def __init__(self, game):
        self.records: List[GameState] = []
        self.data_samples: List[DataSample] = []
        self.game_ref = game
    
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
     
    def get_last_sample(self) -> DataSample:
        if len(self.data_samples) == 0:
            return None
        else:
            return self.data_samples[-1]

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
        history = self.records[-int(self.HISTORY_LEN):]

        action_counts = {a: 0 for a in Action}
        stamina_spent = 0
        hp_delta = 0

        prev_hp = history[0].player_1.health if len(history) > 1 else p.health

        for state in history:
            action: Action = state.player_1.action_in_turn
            action_counts[action] += 1
            stamina_spent += action.stamina_cost()
            hp_delta += state.player_1.health - prev_hp
            prev_hp = state.player_1.health

        for action, count in action_counts.items():
            features[f"count_{action.name.lower()}"] = count / self.HISTORY_LEN

        last_action = history[-1].player_1.action_in_turn
        for action in [Action(c) for c in [1,2,3,4]]:
            features[f"last_{action.name.lower()}"] = float(action == last_action)

        features["stamina_spent_recent"] = stamina_spent / (self.MAX_STAMINA * self.HISTORY_LEN)
        features["hp_delta_recent"] = hp_delta / self.MAX_HP

        # ----------------------------
        # C. Feasibility Indicators
        # ----------------------------
        features["can_attack"] = float(p.stamina >= Action.ATTACK.stamina_cost())
        features["can_heal"] = float(p.stamina >= Action.HEAL.stamina_cost())
        features["can_dodge"] = float(p.stamina >= Action.DODGE.stamina_cost())
        features["can_defend"] = 1.0 if p.is_shield_available else float(0)

        # ----------------------------
        # D. Risk Context Features
        # ----------------------------
        features["hp_diff"] = (p.health - e.health) / self.MAX_HP
        features["low_hp"] = float(p.health < 0.3 * self.MAX_HP)
        features["low_stamina"] = float(p.stamina < 0.3 * self.MAX_STAMINA)

        # ----------------------------
        # E. Estimation of enemy Attack Likelihood
        # ----------------------------

        # --- Parameters ---
        ATTACK_COST = Action.ATTACK.stamina_cost()
        THREAT_THRESHOLD = self.THREAT_THRESHOLD

        # 1. Behavioral Threat (attack frequency)
        enemy_attack_count = sum(
            1 for state in history
            if state.player_2.action_in_turn == Action.ATTACK
        )
        attack_ratio = enemy_attack_count / self.HISTORY_LEN

        behavioral_threat = max(
            0.0,
            (attack_ratio - THREAT_THRESHOLD) / (1.0 - THREAT_THRESHOLD)
        )

        # 2. Capability Score (HARD mechanical constraint)
        if e.stamina < ATTACK_COST:
            capability_score = 0.0
        else:
            stamina_surplus = (
                (e.stamina - ATTACK_COST)
                / (self.MAX_STAMINA - ATTACK_COST)
            )
            hp_confidence = min(e.health / self.MAX_HP, 1.0)

            capability_score = (
                0.7 * stamina_surplus +
                0.3 * hp_confidence
            )

        capability_score = min(capability_score, 1.0)

        # 3. Opportunity Score (player vulnerability)
        opportunity_score = 0.0

        if p.health <= 0.3 * self.MAX_HP:
            opportunity_score += 0.5

        if not p.is_shield_available:
            opportunity_score += 0.3

        last_enemy_action = history[-1].player_2.action_in_turn
        if last_enemy_action == Action.ATTACK:
            opportunity_score += 0.2

        opportunity_score = min(opportunity_score, 1.0)

        # 4. Momentum Score
        momentum_score = 0.0

        if attack_ratio >= 0.6:
            momentum_score += 0.6

        if last_enemy_action == Action.ATTACK:
            momentum_score += 0.4

        momentum_score = min(momentum_score, 1.0)

        # 5. Final Composition
        features["enemy_attack_likelihood"] = compute_imminent_attack_likely(self.game_ref.player_1, 5)

        return Tracker._enforce_features_order_then_return_as_list(features)
    
    @staticmethod
    def _enforce_features_order_then_return_as_list(features: Dict[str, float]) -> List[float]: 
        features_tuple = []

        for feature_name in feature_names:
            features_tuple.append(features[feature_name])

        return features_tuple