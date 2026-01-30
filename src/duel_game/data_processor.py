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
    MAX_TURN = 50  # normalization cap'
    THREAT_THRESHOLD = 0.5

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

        # ----------------------------
        # E. Estimation of enemy Attack Likelihood
        # ----------------------------

        # --- Parameters ---
        ATTACK_COST = self._stamina_cost(Action.ATTACK)
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
        features["enemy_attack_likelihood"] = (
            0.40 * behavioral_threat +
            0.30 * capability_score +
            0.20 * opportunity_score +
            0.10 * momentum_score
        )

        return features

    @staticmethod
    def _stamina_cost(action: Action) -> int:
        return {
            Action.ATTACK: 30,
            Action.DEFENSE: 0,
            Action.DODGE: 10,
            Action.HEAL: 45
        }[action]
    
    def compute_imminent_attack_likely(
        opponent_actions_history,
        opponent_stamina,
        opponent_hp,
        your_hp,
        your_shield_available,
        opponent_last_action,
        history_length=5,
        threat_threshold=0.5,
    ):
        """
        Returns a float in [0, 1] representing likelihood of an incoming attack.
        """

        # -----------------------------
        # 1. Behavioral Threat (history-based)
        # -----------------------------
        attack_count = sum(
            1 for a in opponent_actions_history[-history_length:]
            if a == Action.ATTACK
        )
        attack_ratio = attack_count / history_length

        behavioral_threat = max(
            0.0,
            (attack_ratio - threat_threshold) / (1.0 - threat_threshold)
        )

        # -----------------------------
        # 2. Capability Score (HARD CONSTRAINT)
        # -----------------------------
        ATTACK_COST = 30
        MAX_STAMINA = 100

        if opponent_stamina < ATTACK_COST:
            capability_score = 0.0
        else:
            stamina_surplus = (
                opponent_stamina - ATTACK_COST
            ) / (MAX_STAMINA - ATTACK_COST)

            hp_confidence = min(opponent_hp / 100.0, 1.0)

            capability_score = 0.7 * stamina_surplus + 0.3 * hp_confidence

        capability_score = min(capability_score, 1.0)

        # -----------------------------
        # 3. Opportunity Score (your vulnerability)
        # -----------------------------
        opportunity_score = 0.0

        if your_hp <= 30:
            opportunity_score += 0.5

        if not your_shield_available:
            opportunity_score += 0.3

        if opponent_last_action == Action.ATTACK:
            opportunity_score += 0.2

        opportunity_score = min(opportunity_score, 1.0)

        # -----------------------------
        # 4. Momentum Score
        # -----------------------------
        momentum_score = 0.0

        if attack_ratio >= 0.6:
            momentum_score += 0.6

        if opponent_last_action == Action.ATTACK:
            momentum_score += 0.4

        momentum_score = min(momentum_score, 1.0)

        # -----------------------------
        # 5. Final Weighted Composition
        # -----------------------------
        imminent_attack_likely = (
            0.40 * behavioral_threat +
            0.30 * capability_score +
            0.20 * opportunity_score +
            0.10 * momentum_score
        )

        return min(max(imminent_attack_likely, 0.0), 1.0)