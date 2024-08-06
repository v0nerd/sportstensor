import bittensor as bt
from st.sport_prediction_model import SportPredictionModel
import secrets


class BaseballPredictionModel(SportPredictionModel):
    def make_prediction(self):
        bt.logging.info("Predicting baseball game...")
        self.prediction.homeTeamScore = secrets.SystemRandom().randint(0, 10)
        self.prediction.awayTeamScore = secrets.SystemRandom().randint(0, 10)
