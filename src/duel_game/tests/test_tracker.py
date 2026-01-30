import math
import pytest

# Adjust these imports if your project paths differ.
from duel_game.data_processor import Tracker
from duel_game.game import GameState, Action
from duel_game.player import PlayerState


def make_player(health, stamina, is_shield_available, shield_cd, action):
    return PlayerState(
        health=health,
        stamina=stamina,
        is_shield_available=is_shield_available,
        shield_cd=shield_cd,
        action_in_turn=action
    )


def make_gs(turn, p1_action, p2_action, p1_hp=100, p2_hp=100, p1_stamina=100, p2_stamina=100,
            p1_shield=True, p2_shield=True):
    p1 = make_player(health=p1_hp, stamina=p1_stamina, is_shield_available=p1_shield,
                     shield_cd=0, action=p1_action)
    p2 = make_player(health=p2_hp, stamina=p2_stamina, is_shield_available=p2_shield,
                     shield_cd=0, action=p2_action)
    return GameState(turn=turn, player_1=p1, player_2=p2)


def test_record_and_basic_feature_normalization():
    tracker = Tracker()

    gs = make_gs(turn=1, p1_action=Action.ATTACK, p2_action=Action.DEFENSE,
                 p1_hp=80, p2_hp=40, p1_stamina=50, p2_stamina=20)
    tracker.record(gs)

    samples = tracker.get_samples()
    assert len(samples) == 1

    sample = samples[0]
    f = sample.features

    # normalization checks
    assert f["player_hp"] == pytest.approx(80 / tracker.MAX_HP)
    assert f["enemy_hp"] == pytest.approx(40 / tracker.MAX_HP)
    assert f["player_stamina"] == pytest.approx(50 / tracker.MAX_STAMINA)
    assert f["enemy_stamina"] == pytest.approx(20 / tracker.MAX_STAMINA)

    # label correctness
    assert sample.label == Action.ATTACK
    assert sample.turn == 1


def test_turn_normalization_cap():
    tracker = Tracker()
    # very large turn should be capped to 1.0
    gs = make_gs(turn=9999, p1_action=Action.DEFENSE, p2_action=Action.DEFENSE)
    tracker.record(gs)

    f = tracker.get_samples()[-1].features
    assert f["turn"] == pytest.approx(1.0)


def test_history_action_counts_last_and_stamina_spent_recent():
    tracker = Tracker()
    # Create a 5-step history: ATTACK, ATTACK, DODGE, HEAL, DEFENSE
    actions = [Action.ATTACK, Action.ATTACK, Action.DODGE, Action.HEAL, Action.DEFENSE]
    stamina_values = [100, 70, 60, 30, 10]  # arbitrary valid stamina values

    for i, act in enumerate(actions, start=1):
        gs = make_gs(turn=i, p1_action=act, p2_action=Action.DEFENSE,
                     p1_hp=100, p2_hp=100,
                     p1_stamina=stamina_values[i-1], p2_stamina=100)
        tracker.record(gs)

    f = tracker.get_samples()[-1].features
    # count_attack = 2 out of 5
    assert f["count_attack"] == pytest.approx(2 / tracker.HISTORY_LEN)
    # count_dodge = 1/5, count_heal =1/5, count_defense=1/5
    assert f["count_dodge"] == pytest.approx(1 / tracker.HISTORY_LEN)
    assert f["count_heal"] == pytest.approx(1 / tracker.HISTORY_LEN)
    assert f["count_defense"] == pytest.approx(1 / tracker.HISTORY_LEN)

    # last action flags: last was DEFENSE
    assert f["last_defense"] == pytest.approx(1.0)
    for a in [Action.ATTACK, Action.DODGE, Action.HEAL]:
        assert f[f"last_{a.name.lower()}"] == pytest.approx(0.0)

    # stamina_spent_recent: ATTACK(30)+ATTACK(30)+DODGE(10)+HEAL(45)+DEFENSE(0) = 115
    expected_spent = 30 + 30 + 10 + 45 + 0
    assert f["stamina_spent_recent"] == pytest.approx(expected_spent / (tracker.MAX_STAMINA * tracker.HISTORY_LEN))


def test_hp_delta_recent_computation():
    tracker = Tracker()

    # Create health sequence: 100 -> 90 -> 80 -> 85 -> 75
    hp_sequence = [100, 90, 80, 85, 75]
    for i, hp in enumerate(hp_sequence, start=1):
        gs = make_gs(turn=i, p1_action=Action.DEFENSE, p2_action=Action.DEFENSE,
                     p1_hp=hp, p2_hp=100, p1_stamina=100, p2_stamina=100)
        tracker.record(gs)

    f = tracker.get_samples()[-1].features
    # hp_delta: (100-100) + (90-100) + (80-90) + (85-80) + (75-85) = 0 -10 -10 +5 -10 = -25
    expected_hp_delta = -25
    assert f["hp_delta_recent"] == pytest.approx(expected_hp_delta / tracker.MAX_HP)


def test_can_attack_can_heal_can_dodge_thresholds():
    tracker = Tracker()

    # stamina < 30 -> cannot attack
    gs1 = make_gs(turn=1, p1_action=Action.DEFENSE, p2_action=Action.DEFENSE,
                  p1_hp=100, p2_hp=100, p1_stamina=29)
    tracker.record(gs1)
    f1 = tracker.get_samples()[-1].features
    assert f1["can_attack"] == pytest.approx(0.0)
    assert f1["can_dodge"] == pytest.approx(1.0 if 29 >= 10 else 0.0)
    assert f1["can_heal"] == pytest.approx(0.0)

    # stamina exactly thresholds
    gs2 = make_gs(turn=2, p1_action=Action.DEFENSE, p2_action=Action.DEFENSE,
                  p1_hp=100, p2_hp=100, p1_stamina=30)
    tracker.record(gs2)
    f2 = tracker.get_samples()[-1].features
    assert f2["can_attack"] == pytest.approx(1.0)
    assert f2["can_heal"] == pytest.approx(0.0)
    assert f2["can_dodge"] == pytest.approx(1.0)

    gs3 = make_gs(turn=3, p1_action=Action.DEFENSE, p2_action=Action.DEFENSE,
                  p1_hp=100, p2_hp=100, p1_stamina=45)
    tracker.record(gs3)
    f3 = tracker.get_samples()[-1].features
    assert f3["can_heal"] == pytest.approx(1.0)


# def test_enemy_attack_likelihood_matches_helper_function():
#     tracker = Tracker()

#     # Build enemy action history = all ATTACK for last HISTORY_LEN states
#     enemy_actions = [Action.ATTACK] * tracker.HISTORY_LEN
#     # For reproducibility, create game states whose player_2 has these actions
#     for i, act in enumerate(enemy_actions, start=1):
#         # p1 actions arbitrary
#         gs = make_gs(turn=i,
#                      p1_action=Action.DEFENSE,
#                      p2_action=act,
#                      p1_hp=20,   # make player vulnerable
#                      p2_hp=90,
#                      p1_stamina=50,
#                      p2_stamina=80,
#                      p1_shield=False,  # shield not available -> bigger opportunity
#                      p2_shield=True)
#         tracker.record(gs)

#     # Extract feature
#     features = tracker.get_samples()[-1].features
#     computed_in_features = features["enemy_attack_likelihood"]

#     # Now compute using the helper function with equivalent raw inputs:
#     helper_value = Tracker.compute_imminent_attack_likely(
#         opponent_actions_history=enemy_actions,
#         opponent_stamina=80,
#         opponent_hp=90,
#         your_hp=20,
#         your_shield_available=False,
#         opponent_last_action=Action.ATTACK,
#         history_length=tracker.HISTORY_LEN,
#         threat_threshold=tracker.THREAT_THRESHOLD
#     )

#     # They should be effectively the same (small float diffs possible)
#     assert computed_in_features == pytest.approx(helper_value, rel=1e-6)


# def test_compute_imminent_attack_likely_monotonic_stamina():
#     # Check monotonic behavior vs opponent stamina
#     actions = [Action.ATTACK] * 5
#     low = Tracker.compute_imminent_attack_likely(
#         opponent_actions_history=actions,
#         opponent_stamina=0,
#         opponent_hp=100,
#         your_hp=100,
#         your_shield_available=True,
#         opponent_last_action=Action.DEFENSE,
#     )
#     high = Tracker.compute_imminent_attack_likely(
#         opponent_actions_history=actions,
#         opponent_stamina=100,
#         opponent_hp=100,
#         your_hp=100,
#         your_shield_available=True,
#         opponent_last_action=Action.DEFENSE,
#     )
#     assert 0.0 <= low <= 1.0
#     assert 0.0 <= high <= 1.0
#     assert high >= low


# def test_compute_imminent_attack_likely_edge_values():
#     # Low opportunity (you safe), but enemy very likely by behavior
#     actions_most_attack = [Action.ATTACK] * 5
#     val = Tracker.compute_imminent_attack_likely(
#         opponent_actions_history=actions_most_attack,
#         opponent_stamina=100,
#         opponent_hp=100,
#         your_hp=100,
#         your_shield_available=True,
#         opponent_last_action=Action.ATTACK,
#     )
#     # should be in [0,1] and non-zero
#     assert 0.0 <= val <= 1.0
#     assert val > 0.0
