import bittensor as bt
from st.sport_prediction_model import SportPredictionModel
import secrets


class FootballPredictionModel(SportPredictionModel):
    def make_prediction(self):
        bt.logging.info("Predicting American football game...")
        self.prediction.homeTeamScore = secrets.SystemRandom().randint(0, 40)
        self.prediction.awayTeamScore = secrets.SystemRandom().randint(0, 40)
