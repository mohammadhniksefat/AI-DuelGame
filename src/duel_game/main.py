from game import DuelGame
from presenter import Presenter
from player import Player, ArtificialPlayer
from trained_model import TrainedModel, ModelRepository
from data_processor import Tracker

from dotenv import load_dotenv
from typing import Dict, List
import json
from pathlib import Path 
import os

load_dotenv()

def main():
    a_game_played = False
    lang='en'
    while True:
        presenter = Presenter(lang)

        player = Player()
        model = load_default_model(Path(os.path.dirname(__file__)) / (os.getenv('DEFAULT_MODEL_FILE_PATH')))

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