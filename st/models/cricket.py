import bittensor as bt
from st.sport_prediction_model import SportPredictionModel
import secrets


class CricketPredictionModel(SportPredictionModel):
    def make_prediction(self):
        bt.logging.info("Handling cricket...")
        self.prediction.homeTeamScore = secrets.SystemRandom().randint(0, 160)
        self.prediction.awayTeamScore = secrets.SystemRandom().randint(0, 160)
