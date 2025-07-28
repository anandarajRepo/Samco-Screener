#!/usr/bin/env python3
"""
EOD Data Update Module

This module handles the updating of End-of-Day (EOD) stock market data
from external APIs to the database.
"""

import json
import traceback
import psycopg2
import pandas as pd
import time
import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta, date
from pathlib import Path
from contextlib import contextmanager

from snapi_py_client.snapi_bridge import StocknoteAPIPythonBridge
from configparser import ConfigParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('eod_update.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configure pandas display options
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)


class DatabaseManager:
    """Handles database connections and operations."""

    def __init__(self, config_path: str = '../config.ini'):
        """Initialize database connection parameters from config file."""
        self.config = ConfigParser()
        self.config.read(config_path)

        self.db_params = {
            'database': self.config.get('Database', 'databaseName'),
            'user': self.config.get('Database', 'user'),
            'password': self.config.get('Database', 'password'),
            'host': self.config.get('Database', 'host'),
            'port': self.config.get('Database', 'port')
        }

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_params)
            yield conn
        except psycopg2.Error as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def get_max_eod_date(self) -> date:
        """Get the maximum date from EOD table."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT max(date) as max_date FROM eod")
                result = cursor.fetchone()

                if not result or not result[0]:
                    # Default to 1 year ago if no data exists
                    return date.today() - timedelta(days=365)
                else:
                    return result[0] + timedelta(days=1)

    def get_instrument_by_symbol(self, symbol: str) -> Optional[Tuple[int, str]]:
        """Get instrument ID and symbol by symbol name."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, symbol FROM instruments WHERE active = TRUE AND symbol = %s",
                    (symbol,)
                )
                return cursor.fetchone()

    def insert_eod_data(self, eod_records: List[Dict]) -> int:
        """Insert EOD data records into database."""
        insert_count = 0

        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                for record in eod_records:
                    try:
                        cursor.execute("""
                            INSERT INTO eod (instruments_id, instrument_symbol, date, open, high, low, close, ltp, volume) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            record['instruments_id'],
                            record['instrument_symbol'],
                            record['date'],
                            record['open'],
                            record['high'],
                            record['low'],
                            record['close'],
                            record['ltp'],
                            record['volume']
                        ))
                        insert_count += 1
                    except psycopg2.Error as e:
                        logger.error(f"Error inserting EOD record for {record['instrument_symbol']}: {e}")
                        continue

                conn.commit()
                logger.info(f"Successfully inserted {insert_count} EOD records")

        return insert_count


class StockDataProvider:
    """Handles external stock data API operations."""

    def __init__(self, config_path: str = '../config.ini'):
        """Initialize the stock data provider with API configuration."""
        self.config = ConfigParser()
        self.config.read(config_path)

        self.samco = StocknoteAPIPythonBridge()
        self.samco.set_session_token(
            sessionToken=self.config.get('Samco', 'token')
        )
        self.api_delay = 0.2  # Delay between API calls to avoid rate limiting

    def get_historical_data(self, symbol: str, from_date: date, to_date: date) -> Optional[Dict]:
        """
        Fetch historical candle data for a given symbol.

        Args:
            symbol: Stock symbol
            from_date: Start date for data
            to_date: End date for data

        Returns:
            Dictionary containing historical data or None if failed
        """
        try:
            time.sleep(self.api_delay)  # Rate limiting

            historical_data = self.samco.get_historical_candle_data(
                symbol_name=symbol,
                exchange=self.samco.EXCHANGE_NSE,
                from_date=from_date.strftime('%Y-%m-%d'),
                to_date=to_date.strftime('%Y-%m-%d')
            )

            return json.loads(historical_data)

        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None


class CompanyDataLoader:
    """Handles loading company data from JSON files."""

    def __init__(self, json_file_path: str = '../Output/EQUITY_L.json'):
        """Initialize with path to company data JSON file."""
        self.json_file_path = Path(json_file_path)

    def load_companies(self) -> List[Dict]:
        """Load company data from JSON file."""
        try:
            with open(self.json_file_path, 'r') as f:
                companies = json.load(f)
                logger.info(f"Loaded {len(companies)} companies from {self.json_file_path}")
                return companies
        except FileNotFoundError:
            logger.error(f"Company data file not found: {self.json_file_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON file: {e}")
            raise


class EODDataUpdater:
    """Main class for coordinating EOD data updates."""

    def __init__(self, config_path: str = '../config.ini'):
        """Initialize the EOD data updater."""
        self.db_manager = DatabaseManager(config_path)
        self.data_provider = StockDataProvider(config_path)
        self.company_loader = CompanyDataLoader()

    @staticmethod
    def get_previous_weekday() -> date:
        """Get the most recent weekday (Monday-Friday)."""
        today = datetime.today()

        while True:
            yesterday = today - timedelta(days=1)
            if yesterday.weekday() < 5:  # Monday to Friday (0-4)
                return yesterday.date()
            today = yesterday

    def update_eod_data(self) -> Dict[str, int]:
        """
        Update EOD data for all companies.

        Returns:
            Dictionary with update statistics
        """
        stats = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'records_inserted': 0
        }

        try:
            # Load company data
            companies = self.company_loader.load_companies()

            # Get date range for updates
            start_date = self.db_manager.get_max_eod_date()
            end_date = self.get_previous_weekday()

            logger.info(f"Updating EOD data from {start_date} to {end_date}")

            if start_date > end_date:
                logger.info("No new data to update")
                return stats

            # Process each company
            eod_records = []

            for company in companies:
                stats['processed'] += 1
                symbol = company['SYMBOL']

                try:
                    # Get instrument info from database
                    instrument = self.db_manager.get_instrument_by_symbol(symbol)

                    if not instrument:
                        logger.warning(f"Instrument not found in database: {symbol}")
                        stats['failed'] += 1
                        continue

                    instrument_id, instrument_symbol = instrument

                    # Fetch historical data
                    historical_data = self.data_provider.get_historical_data(
                        symbol, start_date, end_date
                    )

                    if not historical_data or historical_data.get("status") != "Success":
                        logger.warning(f"No historical data available for {symbol}")
                        stats['failed'] += 1
                        continue

                    # Process each day's EOD data
                    for day_data in historical_data.get('historicalCandleData', []):
                        eod_record = {
                            'instruments_id': instrument_id,
                            'instrument_symbol': instrument_symbol,
                            'date': day_data['date'],
                            'open': day_data['open'],
                            'high': day_data['high'],
                            'low': day_data['low'],
                            'close': day_data['close'],
                            'ltp': day_data['ltp'],
                            'volume': day_data['volume']
                        }
                        eod_records.append(eod_record)

                    stats['successful'] += 1
                    logger.info(f"Processed {symbol}: {company.get('NAMEOFCOMPANY', 'N/A')}")

                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
                    stats['failed'] += 1
                    continue

            # Insert all EOD records
            if eod_records:
                stats['records_inserted'] = self.db_manager.insert_eod_data(eod_records)

        except Exception as e:
            logger.error(f"Error during EOD data update: {e}")
            logger.error(traceback.format_exc())
            raise

        return stats

    def run_update(self) -> None:
        """Run the complete EOD data update process."""
        logger.info("Starting EOD data update process")
        start_time = datetime.now()

        try:
            stats = self.update_eod_data()

            end_time = datetime.now()
            duration = end_time - start_time

            logger.info("EOD data update completed successfully")
            logger.info(f"Statistics: {stats}")
            logger.info(f"Duration: {duration}")

        except Exception as e:
            logger.error(f"EOD data update failed: {e}")
            raise


def main():
    """Main entry point for the script."""
    try:
        updater = EODDataUpdater()
        updater.run_update()
    except Exception as e:
        logger.error(f"Script execution failed: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())