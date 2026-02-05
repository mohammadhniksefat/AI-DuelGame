from duel_game.player import Player
from duel_game.data_processor import Tracker
from duel_game.essential_types import Action, GameState
from enum import Enum
import random
import math


class DuelGame:
    decrease_stamina_amount = {
        Action.ATTACK: 30,
        Action.DEFENSE: 0,
        Action.DODGE: 10,
        Action.HEAL: 45
    }
    attack_damage = 20
    heal_amount = 20
    increase_stamina_each_turn = 20
    sheild_spawn_duration = 5 # turns for shield to get accessible for doing Defense
    dodge_probability = 0.5

    # rng -> Random Number Generator
    def __init__(self, player_1: Player, player_2: Player, tracker: Tracker|None = None, max_turns: int = math.inf, rng=random.Random()) -> None:
        self.player_1, self.player_2 = player_1, player_2
        self.player_1.game = self.player_2.game = self
        self.player_1.rng = self.player_2.rng = rng
        self.winner = None
        self.tracker = tracker
        self.records = []
        self.turn = 0
        self.max_turns = max_turns
        self.rng = rng

    def set_tracker(self, tracker: Tracker):
        self.tracker = tracker

    def _after_decisions_notification(self):
        if not self.tracker:
            return

        self.tracker.record(GameState(
                turn=self.turn,
                player_1=self.player_1.get_state(),
                player_2=self.player_2.get_state()
            )
        )


    def play_game(self):
        while True:
            self._play_turn()
            if self._check_whether_game_ends():
                break


    def _play_turn(self):
        self.turn += 1
        self._update_player_state_before_turn(self.player_1)
        self._update_player_state_before_turn(self.player_2)

        player_1_action: Action = self.player_1.choose_action()
        player_2_action: Action = self.player_2.choose_action()
        self._after_decisions_notification()

        self._update_player_state_based_on_actions(self.player_1, player_1_action, player_2_action)
        self._update_player_state_based_on_actions(self.player_2, player_2_action, player_1_action)


    def _check_whether_game_ends(self):
        is_player_1_died = self.player_1.health <= 0
        is_player_2_died = self.player_2.health <= 0
        if is_player_1_died ^ is_player_2_died:
            self.winner = self.player_1 if is_player_1_died else self.player_2

        is_max_turns_reached = self.turn >= self.max_turns

        return (is_player_1_died or is_player_2_died or is_max_turns_reached)
    

    def _update_player_state_before_turn(self, player):
        player.stamina += self.increase_stamina_each_turn


    def _update_player_state_based_on_actions(self, player: Player, player_action: Action, opponent_action: Action):
        player.stamina -= self.decrease_stamina_amount[player_action]

        if player_action == Action.HEAL:
            player.health += self.heal_amount

        if opponent_action == Action.ATTACK:
            if player_action == Action.DEFENSE:
                player.is_shield_available = False
                player.shield_cd = self.sheild_spawn_duration
            elif player_action == Action.DODGE and random.random() > self.dodge_probability:
                pass
            else:
                player.health -= self.attack_damage        