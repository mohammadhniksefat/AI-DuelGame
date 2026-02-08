# Helper function for breaking down probabilities (from previous implementation)
from __future__ import annotations
from typing import Dict, TYPE_CHECKING
from enum import Enum
from essential_types import Action

# to prevent circular import errors (ImportError)
if TYPE_CHECKING:
    from player import DummyPlayer

def break_down_probability(prob_dict: Dict[Enum, float], target_value: Enum, remove_target: bool = True) -> Dict[Enum, float]:
    """
    Break down the probability of a target Enum value and distribute it
    proportionally to other Enum values.
    """
    if target_value not in prob_dict:
        raise ValueError(f"Target value {target_value} not found in probability dictionary")
    
    result = prob_dict.copy()
    target_prob = result[target_value]
    other_values = [key for key in result.keys() if key != target_value]
    
    if not other_values:
        raise ValueError("Cannot break down probability: no other values to distribute to")
    
    total_other_prob = sum(result[key] for key in other_values)
    
    if total_other_prob == 0:
        share = target_prob / len(other_values)
        for key in other_values:
            result[key] = share
    else:
        for key in other_values:
            proportion = result[key] / total_other_prob
            result[key] += target_prob * proportion
    
    if remove_target:
        del result[target_value]
    else:
        result[target_value] = 0.0
    
    return result


def compute_imminent_attack_likely(player: DummyPlayer, history_length):
        """
        Returns a float in [0, 1] representing likelihood of an incoming attack.
        """
        
        opponent_actions_history = player.get_opponent_recent_actions(history_length)
        opponent_stamina = player.opponent.stamina
        opponent_hp = player.opponent.health
        your_hp = player.health
        your_shield_available = player.is_shield_available
        opponent_last_action = player.opponent.action_in_turn


        # -----------------------------
        # 1. Behavioral Threat (history-based)
        # -----------------------------
        attack_count = sum(
            1 for a in opponent_actions_history
            if a == Action.ATTACK
        )
        behavioral_threat = attack_count / history_length

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
        # 3. Opportunity Score
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

        if behavioral_threat >= 0.6:
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