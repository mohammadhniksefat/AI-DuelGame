from typing import Dict, List
import random
import numpy as np

from duel_game.core.essential_types import Action

class TrainedModel:
    def __init__(self, weights: Dict[int, List[float]]):
        self.weights = weights

    def predict(self, input: List[float|int]|None):
        classes = list(self.weights.keys())
        if input is None:
            predicted_class = random.choice([Action.ATTACK, Action.DODGE, Action.DEFENSE]).value
        else:
            compute_score = lambda c: self.weights[c][0] + np.dot(input, self.weights[c][1:])
            predicted_class = max(classes, key=compute_score)

        return Action(int(predicted_class))