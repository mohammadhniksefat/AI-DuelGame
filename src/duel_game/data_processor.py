

class Tracker:
    def __init__(self):
        self.storage = tuple()
        self.data_samples = tuple()


    def record(self, game_state):
        self.storage.add(game_state)
        self.data_samples.add(self._extract_features(game_state))


    def _extract_features(self, game_state):
        pass