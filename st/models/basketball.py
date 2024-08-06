import bittensor as bt
from st.sport_prediction_model import SportPredictionModel
import secrets


class BasketballPredictionModel(SportPredictionModel):
    def make_prediction(self):
        bt.logging.info("Handling basketball...")
        self.prediction.homeTeamScore = secrets.SystemRandom().randint(30, 130)
        self.prediction.awayTeamScore = secrets.SystemRandom().randint(30, 130)
