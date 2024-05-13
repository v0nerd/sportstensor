import requests
import mysql.connector
import schedule
import time
import logging
from datetime import datetime, timezone

# Setup basic configuration for logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define sport mapping
sport_mapping = {
    'SOCCER': 1,
    'FOOTBALL': 2,
    'BASEBALL': 3,
    'BASKETBALL': 4
}

def fetch_and_store_events():
    logging.info("Fetching data from APIs")
    urls = [
        'https://www.thesportsdb.com/api/v1/json/60130162/eventsseason.php?id=4328&s=2023-2024',
        'https://www.thesportsdb.com/api/v1/json/60130162/eventsseason.php?id=4387&s=2023-2024',
        'https://www.thesportsdb.com/api/v1/json/60130162/eventsseason.php?id=4424&s=2024'
    ]
    
    all_events = []
    
    for url in urls:
        try:
            response = requests.get(url)
            data = response.json()
            if 'events' in data:
                all_events.extend(data['events'])
        except Exception as e:
            logging.error(f"Failed to fetch or parse API data from {url}", exc_info=True)
    
    if not all_events:
        logging.info("No events data found in the API responses")
        return

    current_utc_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

    try:
        conn = mysql.connector.connect(host='localhost', database='sports_events', user='root', password='Cunnaredu1996@')
        c = conn.cursor()
        
        # Create table if it does not exist
        c.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            matchId VARCHAR(50) PRIMARY KEY,
            matchDate TIMESTAMP NOT NULL,
            sport INTEGER NOT NULL,
            homeTeamName VARCHAR(30) NOT NULL,
            awayTeamName VARCHAR(30) NOT NULL,
            homeTeamScore INTEGER,
            awayTeamScore INTEGER,
            matchLeague VARCHAR(50),
            isComplete BOOLEAN DEFAULT FALSE,
            lastUpdated TIMESTAMP NOT NULL
        )
        ''')
        logging.info("Database table ensured")
        
        # Insert or update data into the database
        for event in all_events:
            status = event.get('strStatus')
            is_complete = 0 if status in ('Not Started', 'NS') else 1 if status in ('Match Finished', 'FT') else 0
            sport_type = sport_mapping.get(event.get('strSport').upper(), 0)  # Default to 0 if sport is unknown

            c.execute('''
            INSERT INTO matches (matchId, matchDate, sport, homeTeamName, awayTeamName, homeTeamScore, awayTeamScore, matchLeague, isComplete, lastUpdated) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                matchDate=VALUES(matchDate),
                sport=VALUES(sport),
                homeTeamName=VALUES(homeTeamName),
                awayTeamName=VALUES(awayTeamName),
                homeTeamScore=VALUES(homeTeamScore),
                awayTeamScore=VALUES(awayTeamScore),
                matchLeague=VALUES(matchLeague),
                isComplete=VALUES(isComplete),
                lastUpdated=VALUES(lastUpdated)
            ''',
            (
                event.get('idEvent'),
                event.get('strTimestamp'),
                sport_type,
                event.get('strHomeTeam'),
                event.get('strAwayTeam'),
                event.get('intHomeScore'),
                event.get('intAwayScore'),
                event.get('strLeague'), 
                is_complete,
                current_utc_time
            ))
        conn.commit()
        logging.info("Data inserted or updated in database")
    except Exception as e:
        logging.error("Failed to interact with the database", exc_info=True)
    finally:
        conn.close()

# Schedule the function to run every 10 minutes
schedule.every(10).minutes.do(fetch_and_store_events)

# Initial fetch and store to ensure setup is correct
fetch_and_store_events()

# Run the scheduler in an infinite loop
while True:
    schedule.run_pending()
    time.sleep(1)
