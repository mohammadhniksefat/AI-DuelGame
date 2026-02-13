from player import Player
from data_processor import Tracker
from essential_types import Action, GameState
from presenter import Presenter
from enum import Enum
import random
import math


class DuelGame:
    attack_damage = 20
    heal_amount = 20
    increase_stamina_each_turn = 20
    sheild_spawn_duration = 5 # turns for shield to get accessible for doing Defense
    dodge_probability = 0.5

    # rng -> Random Number Generator
    def __init__(self, player_1: Player, player_2: Player, max_turns: int = math.inf, rng=random.Random(), headless=True, presenter: Presenter=None) -> None:
        self.player_1, self.player_2 = player_1, player_2
        self.winner = None
        self.records = []
        self.turn = 0
        self.max_turns = max_turns
        self.rng = rng
        self.tracker:Tracker
        self.headless = headless
        if not headless:
            self.presenter = presenter

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
        if self.headless:
            while True:
                self._play_turn()
                if self._check_whether_game_ends():
                    break
        else:
            self.presenter.on_game_starts()
            while True:
                self._play_turn()
                whether_game_ends = self._check_whether_game_ends()
                self.presenter.after_turn(self.player_1.shield_cd, whether_game_ends, player_wins=(self.winner == self.player_1))
                if whether_game_ends:
                    break

    def _play_turn(self):
        if self.headless:
            self.turn += 1
            self._update_player_state_before_turn(self.player_1)
            self._update_player_state_before_turn(self.player_2)

            player_1_action = self.player_1.action_in_turn = self.player_1.choose_action()
            player_2_action = self.player_2.action_in_turn = self.player_2.choose_action()
            self._after_decisions_notification()

            self._update_player_state_based_on_actions(self.player_1, player_1_action, player_2_action)
            self._update_player_state_based_on_actions(self.player_2, player_2_action, player_1_action)

        else:
            self.turn += 1
            self._update_player_state_before_turn(self.player_1)
            self._update_player_state_before_turn(self.player_2)
            player_1_action = self.presenter.on_turn_start(
                GameState(
                    self.turn,
                    self.player_1.get_state(),
                    self.player_2.get_state()
                )
            )

            self.player_1.action_in_turn = player_1_action
            self.presenter.after_player_decision(player_1_action)

            player_2_action = self.player_2.action_in_turn = self.player_2.choose_action()

            self._after_decisions_notification()

            player_result_detail = self._update_player_state_based_on_actions(self.player_1, player_1_action, player_2_action)
            opponent_result_detail = self._update_player_state_based_on_actions(self.player_2, player_2_action, player_1_action)
            
            self.presenter.after_decisions(player_1_action, player_2_action, player_result_detail, opponent_result_detail)


    def _check_whether_game_ends(self):
        is_player_1_died = self.player_1.health <= 0
        is_player_2_died = self.player_2.health <= 0
        if is_player_1_died ^ is_player_2_died:
            self.winner = self.player_1 if is_player_2_died else self.player_2

        is_max_turns_reached = self.turn >= self.max_turns

        return (is_player_1_died or is_player_2_died or is_max_turns_reached)
    

    def _update_player_state_before_turn(self, player: Player):
        player.stamina = min(100, player.stamina + self.increase_stamina_each_turn)
        player.shield_cd = max(0, player.shield_cd - 1)
        player.is_shield_available = player.shield_cd == 0


    def _update_player_state_based_on_actions(self, player: Player, player_action: Action, opponent_action: Action):
        if player.stamina < player_action.stamina_cost():
            raise ValueError(f"selected action {player_action.name} isn't feasible because player stamina({str(player.stamina)}) is less than needed ({str(player_action.stamina_cost())})")
        player.stamina -= player_action.stamina_cost()

        if player_action == Action.HEAL:
            player.health = min(100, player.health + self.heal_amount)

        is_dodge_works = None

        if opponent_action == Action.ATTACK:
            if player_action == Action.DEFENSE:
                if not player.is_shield_available:
                    raise ValueError(f"Selected Action {player_action.name} isn't Feasible because shield isn't available")
                player.is_shield_available = False
                player.shield_cd = self.sheild_spawn_duration
            elif player_action == Action.DODGE:
                is_dodge_works = random.random() > self.dodge_probability
                if not is_dodge_works:
                    player.health = max(0, player.health - self.attack_damage)    
            else:
                player.health = max(0, player.health - self.attack_damage)

        player.action_in_turn = player_action

        return {
            "is_dodge_works": is_dodge_works
        }