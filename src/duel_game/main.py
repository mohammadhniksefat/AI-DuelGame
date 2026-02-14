from duel_game.core.game import DuelGame
from duel_game.core.presenter import Presenter
from duel_game.core.player import Player, ArtificialPlayer
from duel_game.core.ml_model import TrainedModel
from duel_game.core.helpers import get_base_path, is_in_bundled
from duel_game.dataset.data_processor import Tracker

from dotenv import load_dotenv
from typing import List
import json
from pathlib import Path 
import os

if not is_in_bundled():
    load_dotenv(get_base_path() / '.env')

default_model_path = os.path.join(get_base_path(), 'default_model.json')

def main():
    a_game_played = False
    lang='en'
    while True:
        presenter = Presenter(lang)

        player = Player()
        model = load_default_model(default_model_path)

        ai_brain = TrainedModel(model["weights"])
        ai_opponent = ArtificialPlayer(ai_brain)
        
        game = DuelGame(player, ai_opponent, headless=False, presenter=presenter)
        tracker = Tracker(game)
        game.set_tracker(tracker)

        player.set_game(game)
        player.set_opponent(ai_opponent)
        ai_opponent.set_game(game)
        ai_opponent.set_opponent(player)
        
        if not a_game_played:
            presenter.intro()
        
        choice = presenter.main_menu()
        if choice == '1':
            game.play_game()
            a_game_played = True
        elif choice == '2':
            presenter.display_help()
        elif choice == '3':
            lang = presenter.change_language()
        elif choice == '4':
            return
        else:
            raise ValueError('unexpected choice value ' + str(choice))

def load_default_model(model_file_path: str) -> dict[int, List[float]]:    
    with open(model_file_path, 'r', encoding='utf-8') as json_file:
        return json.load(json_file)

if __name__ == "__main__":
    main()