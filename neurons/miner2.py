# The MIT License (MIT)
# Copyright © 2024 sportstensor

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import os
import time
import traceback
import typing
import random
from dotenv import load_dotenv
import bittensor as bt

import base
from base.miner import BaseMinerNeuron

from common import constants
from common.data import League, get_league_from_string, ProbabilityChoice
from common.protocol import GetLeagueCommitments, GetMatchPrediction
from st.sport_prediction_model import make_match_prediction
from neurons.db import DatabaseManager
from vali_utils.scoring_utils import find_extrema


# Define the path to the miner.env file
MINER_ENV_PATH = os.path.join(os.path.dirname(__file__), 'miner2.env')
BOUNDER = 1e-10

class Miner(BaseMinerNeuron):
    """The Sportstensor Miner."""

    def __init__(self, config=None):
        super(Miner, self).__init__(config=config)
        self.league_commitments = []
        self.load_league_commitments()
        db_params = {
            "db_name": "sportstensor",
            "db_user": "root",
            "db_password": "Thunder@517",
            "db_host": "localhost",
            "db_port": 5432,
        }
        self.db_manager = DatabaseManager(**db_params)

    def load_league_commitments(self):
        load_dotenv(dotenv_path=MINER_ENV_PATH, override=True)
        league_commitments = os.getenv("LEAGUE_COMMITMENTS")
        leagues_list = league_commitments.split(",")
        
        leagues = []
        for league_string in leagues_list:
            try:
                league = get_league_from_string(league_string.strip())
                leagues.append(league)
            except ValueError:
                print(f"Warning: Ignoring invalid league '{league_string}'")

        if not leagues or len(leagues) == 0:
            bt.logging.error("No leagues found in the environment variable LEAGUE_COMMITMENTS.")
            self.league_commitments = []
        else:
            self.league_commitments = leagues

    async def get_league_commitments(self, synapse: GetLeagueCommitments) -> GetLeagueCommitments:
        bt.logging.info(
            f"Received GetLeagueCommitments request in forward() from {synapse.dendrite.hotkey}."
        )
        
        # Load our league commitments from the environment variable every time we receive a request. Avoids miners having to restart
        self.load_league_commitments()
        synapse.leagues = self.league_commitments
        synapse.version = constants.PROTOCOL_VERSION

        bt.logging.success(
            f"Returning Leagues to {synapse.dendrite.hotkey}: {[league.value for league in synapse.leagues]}."
        )

        return synapse

    async def get_match_prediction(self, synapse: GetMatchPrediction) -> GetMatchPrediction:
        bt.logging.info(
            f"Received GetMatchPrediction request in forward() from {synapse.dendrite.hotkey}."
        )

        # Make the match prediction based on the requested MatchPrediction object
        # TODO: does this need to by async?

        matchId = synapse.match_prediction.matchId
        bt.logging.debug(f"Looking up prediction for matchId: {matchId}")
        if matchId:
            pred = self.db_manager.get_prediction(synapse.match_prediction.homeTeamName, synapse.match_prediction.awayTeamName, synapse.match_prediction.matchDate, 'matchesreal')
            bt.logging.debug(f"Found prediction: {pred}")
            if pred:
                print("Found prediction")
                print(pred.get("hometeamodds"), pred.get("awayteamodds"))
                if pred.get("hometeamodds") is not None and pred.get("awayteamodds") is not None:
                    home_odds = pred.get("hometeamodds")
                    away_odds = pred.get("awayteamodds")
                    # if random_50_50():
                    if False:
                        if home_odds > away_odds:
                            synapse.match_prediction.probabilityChoice = ProbabilityChoice.HOMETEAM.value
                            c = home_odds
                        elif home_odds < away_odds:
                            synapse.match_prediction.probabilityChoice = ProbabilityChoice.AWAYTEAM.value
                            c = away_odds
                        else:
                            if synapse.match_prediction.sport == "soccer":
                                synapse.match_prediction.probabilityChoice = ProbabilityChoice.DRAW.value
                            else:
                                synapse.match_prediction.probabilityChoice = ProbabilityChoice.HOMETEAM.value
                            c = home_odds
                        
                        (min_y, x_min), (max_y, x_max) = find_extrema(c)
                        left = x_min
                        right = x_min + (float(1 / c) - x_min) / 2.0
                        if right - left <= 0.03:
                            right = 1 / c
                        synapse.match_prediction.probability = random.randint(int(left*10000), int(right*10000)) / 10000
                        synapse.version = constants.PROTOCOL_VERSION
                        bt.logging.success(
                            f"Returning MatchPrediction to {synapse.dendrite.hotkey}: \n{synapse.match_prediction}."
                        )
                        return synapse
                    else:
                        try: 
                            if home_odds > away_odds:
                                synapse.match_prediction.probabilityChoice = ProbabilityChoice.AWAYTEAM.value
                                c = away_odds
                            elif home_odds < away_odds:
                                synapse.match_prediction.probabilityChoice = ProbabilityChoice.HOMETEAM.value
                                c = home_odds
                            else:
                                if synapse.match_prediction.sport == "soccer":
                                    synapse.match_prediction.probabilityChoice = ProbabilityChoice.DRAW.value
                                else:
                                    synapse.match_prediction.probabilityChoice = ProbabilityChoice.HOMETEAM.value
                                c = home_odds
                            
                            (min_y, x_min), (max_y, x_max) = find_extrema(c)
                            left = (1 / c) + (x_max - (1 / c)) / 2.0
                            right = min(x_max + (1 - x_max) / 2.0, 0.89)
                            if right <= left:
                                left = 1 / c
                            if left < 0.33:
                                left = 0.35
                                right = 0.89
                            synapse.match_prediction.probability = random.randint(int(left*10000), int(right*10000)) / 10000
                            synapse.version = constants.PROTOCOL_VERSION
                            bt.logging.success(
                                f"Returning MatchPrediction to {synapse.dendrite.hotkey}: \n{synapse.match_prediction}."
                            )
                            return synapse
                        except Exception as e:
                            bt.logging.error(f"Error: {e}")
                            synapse.match_prediction.probabilityChoice = ProbabilityChoice.HOMETEAM.value
                            synapse.match_prediction.probability = random.randint(int(0.55*10000), int(0.75*10000)) / 10000
                            synapse.version = constants.PROTOCOL_VERSION
                            bt.logging.success(
                                f"Returning MatchPrediction to {synapse.dendrite.hotkey}: \n{synapse.match_prediction}."
                            )
                            return synapse
                else:
                    bt.logging.warning("No odds found in prediction")
                    synapse.match_prediction.probabilityChoice = ProbabilityChoice.HOMETEAM.value
                    synapse.match_prediction.probability = random.randint(int(0.55*10000), int(0.75*10000)) / 10000
                    synapse.version = constants.PROTOCOL_VERSION
                    bt.logging.success(
                        f"Returning MatchPrediction to {synapse.dendrite.hotkey}: \n{synapse.match_prediction}."
                    )
                    return synapse
            else:
                bt.logging.info("Skipping db lookup, no prediction found.")

        # Make the match prediction based on the requested MatchPrediction object
        synapse.match_prediction = make_match_prediction(synapse.match_prediction)
        synapse.version = constants.PROTOCOL_VERSION

        bt.logging.success(
            f"Returning MatchPrediction to {synapse.dendrite.hotkey}: \n{synapse.match_prediction.pretty_print()}."
        )

        return synapse
    
    async def get_league_commitments_blacklist(
        self, synapse: GetLeagueCommitments
    ) -> typing.Tuple[bool, str]:
        return await self.blacklist(synapse)
    
    async def get_match_prediction_blacklist(
        self, synapse: GetMatchPrediction
    ) -> typing.Tuple[bool, str]:
        return await self.blacklist(synapse)

    async def blacklist(self, synapse: bt.Synapse) -> typing.Tuple[bool, str]:
        """
        Determines whether an incoming request should be blacklisted and thus ignored. Your implementation should
        define the logic for blacklisting requests based on your needs and desired security parameters.

        Blacklist runs before the synapse data has been deserialized (i.e. before synapse.data is available).
        The synapse is instead contructed via the headers of the request. It is important to blacklist
        requests before they are deserialized to avoid wasting resources on requests that will be ignored.

        Args:
            synapse (template.protocol.Videos): A synapse object constructed from the headers of the incoming request.

        Returns:
            Tuple[bool, str]: A tuple containing a boolean indicating whether the synapse's hotkey is blacklisted,
                            and a string providing the reason for the decision.

        This function is a security measure to prevent resource wastage on undesired requests. It should be enhanced
        to include checks against the metagraph for entity registration, validator status, and sufficient stake
        before deserialization of synapse data to minimize processing overhead.

        Example blacklist logic:
        - Reject if the hotkey is not a registered entity within the metagraph.
        - Consider blacklisting entities that are not validators or have insufficient stake.

        In practice it would be wise to blacklist requests from entities that are not validators, or do not have
        enough stake. This can be checked via metagraph.S and metagraph.validator_permit. You can always attain
        the uid of the sender via a metagraph.hotkeys.index( synapse.dendrite.hotkey ) call.

        Otherwise, allow the request to be processed further.
        """
        if synapse.dendrite.hotkey == "5GxADSjVkV22Kbi7v4BTFsUzqTavrjkVNmf1zKq6FZLkYJ7H":
            return False, f"Allowing requests from the child hotkey {synapse.dendrite.hotkey}"
        if not synapse.dendrite.hotkey:
            return True, "Hotkey not provided"
        registered = synapse.dendrite.hotkey in self.metagraph.hotkeys
        if self.config.blacklist.allow_non_registered and not registered:
            return False, "Allowing un-registered hotkey"
        elif not registered:
            bt.logging.trace(
                f"Blacklisting un-registered hotkey {synapse.dendrite.hotkey}"
            )
            return True, f"Unrecognized hotkey {synapse.dendrite.hotkey}"

        uid = self.metagraph.hotkeys.index(synapse.dendrite.hotkey)
        if self.config.blacklist.force_validator_permit:
            # If the config is set to force validator permit, then we should only allow requests from validators.
            if not self.metagraph.validator_permit[uid]:
                bt.logging.warning(
                    f"Blacklisting a request from non-validator hotkey {synapse.dendrite.hotkey}"
                )
                return True, "Non-validator hotkey"

        stake = self.metagraph.S[uid].item()
        if (
            self.config.blacklist.validator_min_stake
            and stake < self.config.blacklist.validator_min_stake
        ):
            bt.logging.warning(
                f"Blacklisting request from {synapse.dendrite.hotkey} [uid={uid}], not enough stake -- {stake}"
            )
            return True, "Stake below minimum"

        bt.logging.trace(
            f"Not Blacklisting recognized hotkey {synapse.dendrite.hotkey}"
        )
        return False, "Hotkey recognized!"

    
    async def get_league_commitments_priority(self, synapse: GetLeagueCommitments) -> float:
        return await self.priority(synapse)
    
    async def get_match_prediction_priority(self, synapse: GetMatchPrediction) -> float:
        return await self.priority(synapse)

    async def priority(self, synapse: bt.Synapse) -> float:
        """
        The priority function determines the order in which requests are handled. More valuable or higher-priority
        requests are processed before others. You should design your own priority mechanism with care.

        This implementation assigns priority to incoming requests based on the calling entity's stake in the metagraph.

        Args:
            synapse (template.protocol.Videos): The synapse object that contains metadata about the incoming request.

        Returns:
            float: A priority score derived from the stake of the calling entity.

        Miners may recieve messages from multiple entities at once. This function determines which request should be
        processed first. Higher values indicate that the request should be processed first. Lower values indicate
        that the request should be processed later.

        Example priority logic:
        - A higher stake results in a higher priority value.
        """
        caller_uid = self.metagraph.hotkeys.index(
            synapse.dendrite.hotkey
        )  # Get the caller index.
        prirority = float(
            self.metagraph.S[caller_uid]
        )  # Return the stake as the priority.
        bt.logging.trace(
            f"Prioritizing {synapse.dendrite.hotkey} with value: ", prirority
        )
        return prirority

    def save_state(self):
        """
        We define this function to avoid printing out the log message in the BaseNeuron class
        that says `save_state() not implemented`.
        """
        pass


def random_50_50():
    number = random.randint(1, 99)  # Choose a random integer between 1 and 99
    return number > 50  # Return True if the number is greater than 50, else False


# This is the main function, which runs the miner.
if __name__ == "__main__":
    with Miner() as miner:
        while True:
            bt.logging.info(f"Sportstensor Miner running, committed to leagues: {[league.value for league in miner.league_commitments]}")
            time.sleep(60)
