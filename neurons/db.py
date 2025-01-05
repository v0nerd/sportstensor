import psycopg2
import contextlib
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
import bittensor as bt
import traceback
import time
from typing import Dict, Any
from datetime import datetime as dt

from common.data import Match


class DatabaseManager:
    def __init__(self, db_name, db_user, db_password, table='matches', db_host='localhost', db_port=5432, max_connections=10):
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_port = db_port
        self.max_connections = max_connections
        
        bt.logging.debug("Initializing DatabaseManager")
        bt.logging.debug(f"Checking root user")
        self.is_root = self.check_root_user()
        bt.logging.debug(f"Ensuring database exists")
        self.ensure_database_exists()
        bt.logging.debug(f"Waiting for database")
        self.wait_for_database()
        bt.logging.debug(f"Creating connection pool")
        self.connection_pool = self.create_connection_pool()
        bt.logging.debug(f"Creating tables")
        self.create_tables(table=table)
        bt.logging.debug("DatabaseManager initialization complete")

    def check_root_user(self):
        return self.db_user == 'root'

    def ensure_database_exists(self):
        conn = None
        try:
            # Connect to the default 'postgres' database
            conn = psycopg2.connect(
                dbname='postgres',
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port
            )
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            
            with conn.cursor() as cur:
                # Check if the database exists
                cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (self.db_name,))
                exists = cur.fetchone()
                
                if not exists:
                    bt.logging.debug(f"Creating database {self.db_name}")
                    # Create the database
                    cur.execute(f"CREATE DATABASE {self.db_name}")
                    bt.logging.debug(f"Database {self.db_name} created successfully")
                else:
                    bt.logging.debug(f"Database {self.db_name} already exists")
        
        except psycopg2.Error as e:
            bt.logging.error(f"Error ensuring database exists: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def wait_for_database(self):
        max_retries = 5
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                with psycopg2.connect(
                    host=self.db_host,
                    port=self.db_port,
                    user=self.db_user,
                    password=self.db_password,
                    database=self.db_name
                ) as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT 1")
                        bt.logging.debug("Successfully connected to the database.")
                        return
            except psycopg2.OperationalError:
                if attempt < max_retries - 1:
                    bt.logging.warning(f"Database not ready (attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    bt.logging.error("Failed to connect to the database after multiple attempts.")
                    raise

    def create_connection_pool(self):
        return SimpleConnectionPool(
            1, self.max_connections,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            user=self.db_user,
            password=self.db_password
        )

    def create_tables(self, table='matches'):
        tables = [
            (table, f"""CREATE TABLE IF NOT EXISTS {table} (
            matchId       VARCHAR(50)     PRIMARY KEY,
            matchDate     TIMESTAMP(6)    NOT NULL,
            sport         INTEGER         NOT NULL,
            league        VARCHAR(50)     NOT NULL,
            homeTeamName  VARCHAR(30)     NOT NULL,
            awayTeamName  VARCHAR(30)     NOT NULL,
            homeTeamScore INTEGER         NULL,
            awayTeamScore INTEGER         NULL,
            isComplete    INTEGER         DEFAULT 0,
            lastUpdated   TIMESTAMP(6)    NOT NULL
            )""")
        ]
        
        for table_name, create_query in tables:
            try:
                self.execute_query(create_query)
                bt.logging.debug(f"Created table: {table_name}")
            except Exception as e:
                bt.logging.error(f"Error creating table {table_name}: {e}")

    def check_match(self, matchId: str) -> Match:
        """Check if a match with the given ID exists in the database."""
        query = """
        SELECT EXISTS(SELECT 1 FROM matches WHERE matchId = ?)
        """
        try:
            results = self.execute_query(query, (matchId,))
            if results:
                print(results)
                return True
        except Exception as e:
            bt.logging.error(f"Error getting predictions: {str(e)}")
            bt.logging.error(f"Traceback: {traceback.format_exc()}")
            return False

    def insert_match(self, match: Match, table='matches'):
        is_complete = 0
        current_utc_time = dt.utcnow().isoformat()

        query = f"""
        INSERT INTO {table} (matchId, matchDate, sport, league, homeTeamName, awayTeamName, homeTeamScore, awayTeamScore, isComplete, lastUpdated)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        params = (
            match.matchId,
            match.matchDate,
            match.sport,
            match.league,
            match.homeTeamName,
            match.awayTeamName,
            match.homeTeamScore,
            match.awayTeamScore,
            is_complete,
            current_utc_time
        )

        try:
            bt.logging.debug(f"Executing query: {query}")
            bt.logging.debug(f"Query parameters: {params}")
            result = self.execute_query(query, params)
            if result:
                inserted_row = result[0] if isinstance(result, list) else result
                bt.logging.debug(f"Match added successfully: {inserted_row}")
                return {'status': 'success', 'message': f"Match added successfully", 'data': inserted_row}
            else:
                bt.logging.error("No row returned after insertion")
                bt.logging.error(f"Database result: {result}")
                return {'status': 'error', 'message': "No row returned after insertion"}
        except Exception as e:
            bt.logging.error(f"Error adding match: {str(e)}")
            bt.logging.error(f"Traceback: {traceback.format_exc()}")
            return {'status': 'error', 'message': f"Error adding match: {str(e)}"}

    def execute_query(self, query, params=None):
        # print(f"DatabaseManager: Executing query: {query}")
        # print(f"DatabaseManager: Query parameters: {params}")
        try:
            with self.connection_pool.getconn() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, params)
                    if query.strip().upper().startswith("SELECT"):
                        result = cur.fetchall()
                    else:
                        result = cur.rowcount
                        conn.commit()
                    # print(f"DatabaseManager: Query result: {result}")
                    return result
        except Exception as e:
            # print(f"DatabaseManager: Error executing query: {str(e)}")
            # print(f"DatabaseManager: Traceback: {traceback.format_exc()}")
            raise
        finally:
            self.connection_pool.putconn(conn)

    def execute_batch(self, query, params_list):
        conn, cur = None, None
        try:
            conn = self.connection_pool.getconn()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            bt.logging.debug(f"Executing batch query: {query}")
            bt.logging.debug(f"Number of parameter sets: {len(params_list)}")
            
            cur.executemany(query, params_list)
            conn.commit()
            bt.logging.debug("Batch query executed successfully")
        except Exception as e:
            if conn:
                conn.rollback()
            bt.logging.error(f"Error in execute_batch: {str(e)}")
            bt.logging.error(f"Query: {query}")
            bt.logging.error(f"Params: {params_list}")
            bt.logging.error(f"Traceback: {traceback.format_exc()}")
            raise
        finally:
            if cur:
                cur.close()
            if conn:
                self.connection_pool.putconn(conn)

    def add_prediction(self, prediction: Dict[str, Any]):
        #print(f"DEBUG: Adding prediction: {prediction}")
        # Deduct wager before adding prediction
        is_complete = 0
        current_utc_time = dt.utcnow().isoformat()

        query = """
            UPDATE matches
            SET homeTeamScore = %s, awayTeamScore = %s, isComplete = %s, lastUpdated = %s
            WHERE matchDate = %s
            AND sport = %s
            AND homeTeamName = %s
            AND awayTeamName = %s
            AND league = %s
        """

        params = (
            prediction.homeTeamScore,
            prediction.awayTeamScore,
            is_complete,
            current_utc_time,
            prediction.matchDate,
            prediction.sport,
            prediction.homeTeamName,
            prediction.awayTeamName,
            prediction.league,
        )

        try:
            bt.logging.debug(f"Executing query: {query}")
            bt.logging.debug(f"Query parameters: {params}")
            result = self.execute_query(query, params)
            #print(f"DEBUG: Prediction added, result: {result}")
            if result:
                inserted_row = result[0] if isinstance(result, list) else result
                bt.logging.debug(f"Prediction added successfully: {inserted_row}")
                return {'status': 'success', 'message': f"Prediction added successfully", 'data': inserted_row}
            else:
                bt.logging.error("No row returned after insertion")
                bt.logging.error(f"Database result: {result}")
                return {'status': 'error', 'message': "No row returned after insertion"}
        except Exception as e:
            #print(f"DEBUG: Error adding prediction: {str(e)}")
            bt.logging.error(f"Error adding prediction: {str(e)}")
            bt.logging.error(f"Traceback: {traceback.format_exc()}")
            return {'status': 'error', 'message': f"Error adding prediction: {str(e)}"}

    def get_prediction(self, home_teamname, away_teamname, match_date, table: str):
        current_date = dt.utcnow().isoformat()
        query = f"""
        SELECT *
        FROM {table}
        WHERE hometeamname = %s
        AND awayteamname = %s
        AND matchdate::timestamp = %s
        """
        try:
            print(current_date)
            results = self.execute_query(query, (home_teamname, away_teamname, match_date))
            if results:
                return results[0]
        except Exception as e:
            bt.logging.error(f"Error getting predictions: {str(e)}")
            bt.logging.error(f"Traceback: {traceback.format_exc()}")
            return {}

    def close(self):
        self.connection_pool.closeall()
