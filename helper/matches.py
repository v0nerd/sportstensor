#!/home/unicorn/sports/sportstensor/venv/bin/env python

from aiohttp import ClientSession
import asyncio

from common.data import Match
from helper.db import DatabaseManager
import time


db_params = {
    "db_name": "sportstensor",
    "db_user": "root",
    "db_password": "Thunder@517",
    "db_host": "localhost",
    "db_port": 5432,
}
storage = DatabaseManager(**db_params)

async def sync_data():
    try:
        api_root = (
            "https://api.sportstensor.com"
        )
        match_data_endpoint = f"{api_root}/matches"

        async with ClientSession() as session:
            # TODO: add in authentication
            async with session.get(match_data_endpoint) as response:
                response.raise_for_status()
                match_data = await response.json()

        if not match_data or "matches" not in match_data:
            print("No match data returned from API")
            return False

        match_data = match_data["matches"]
        print(f"Received {len(match_data)} matches from API.")

        # UPSERT logic
        matches_to_insert = []
        matches_to_update = []
        for item in match_data:
            if "matchId" not in item:
                print(f"Skipping match data missing matchId: {item}")
                continue

            print(item)

            match = Match(
                matchId=item["matchId"],
                matchDate=item["matchDate"],
                sport=item["sport"],
                league=item["matchLeague"],
                homeTeamName=item["homeTeamName"],
                awayTeamName=item["awayTeamName"],
                homeTeamScore=item["homeTeamScore"],
                awayTeamScore=item["awayTeamScore"],
                isComplete=item["isComplete"],
            )
            if not storage.check_match(item["matchId"]):
                storage.insert_match(match)

        return True

    except Exception as e:
        print(f"Error getting match data: {e}")
        return False

async def main():
    while True:
        try:
            current_minute = time.localtime().tm_min
            if current_minute % 10 == 0:
                print("Syncing data...")
                matches = await sync_data()
                print(matches)
                print("Sleeping for 10 minutes...")
                await asyncio.sleep(60)  # Sleep for 1 minute to avoid multiple runs within the same minute
            else:
                # print current time in the format of HH:MM:SS
                print("Current time: ", time.strftime("%H:%M:%S", time.localtime()))
                await asyncio.sleep(30)  # Check again in 30 seconds
        except KeyboardInterrupt:
            print("Exiting...")
            break

if __name__ == "__main__":
    asyncio.run(main())
