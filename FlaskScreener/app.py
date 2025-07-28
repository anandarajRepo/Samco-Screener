
"""
Complete Stock Screener Application
Save this as: FlaskScreener/main.py or FlaskScreener/app.py
"""

import psycopg2
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta, time, date
from contextlib import contextmanager
from dataclasses import dataclass

from flask import Flask, render_template, request, jsonify, redirect, url_for
from configparser import ConfigParser
from psycopg2.extras import RealDictCursor
from jinjasql import JinjaSql

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure pandas display options
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)


@dataclass
class PerformanceMetrics:
    """Data class for storing performance metrics."""
    open_close_percent: float
    high_low_percent: float
    prev_close_percent: Optional[float] = None
    vol_percent: Optional[float] = None
    gap_up: Optional[float] = None
    gap_down: Optional[float] = None


@dataclass
class StockData:
    """Data class for storing stock EOD data."""
    date: date
    open: float
    close: float
    high: float
    low: float
    volume: int
    company_name: str
    sector: str
    subsector: str


class DatabaseManager:
    """Handles database connections and operations."""

    def __init__(self, config_path: str = "../config.ini"):
        """Initialize database connection parameters."""
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


class StockService:
    """Service class for stock-related operations."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize with database manager."""
        self.db_manager = db_manager
        self.jinja_sql = JinjaSql()

    def get_stocks(self, sector_filter: Optional[str] = None,
                   subsector_filter: Optional[str] = None,
                   search_text: Optional[str] = None) -> List[Dict]:
        """Get list of stocks based on filters."""

        instrument_query_template = """
            SELECT id, symbol, nameofcompany, sector, subsector, favourite, dateoflistings, marketcap
            FROM instruments
            WHERE active = TRUE
            {% if searchText %}
                AND nameofcompany ILIKE {{ searchText }}
            {% elif not sectorFilter %}
                AND favourite = true
            {% endif %}
            {% if sectorFilter %}
                AND sector = {{ sectorFilter }}
            {% endif %}
            {% if subSectorFilter %}
                AND subsector = {{ subSectorFilter }}
            {% endif %}
            ORDER BY subsector, nameofcompany ASC
        """

        template_data = {
            "searchText": search_text,
            "sectorFilter": sector_filter,
            "subSectorFilter": subsector_filter,
        }

        query, bind_params = self.jinja_sql.prepare_query(instrument_query_template, template_data)

        with self.db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, bind_params)
                stocks = cursor.fetchall()

                # Process market cap for sorting
                for stock in stocks:
                    stock['marketcapincrs'] = self._convert_market_cap(stock.get('marketcap'))

                return [dict(stock) for stock in stocks]

    def _convert_market_cap(self, market_cap: Optional[str]) -> int:
        """Convert market cap string to integer for sorting."""
        if not market_cap:
            return 0

        try:
            if 'T' in market_cap:
                return int(float(market_cap.replace('T', '')) * 100000)
            elif 'B' in market_cap:
                return int(float(market_cap.replace('B', '')) * 100)
            elif 'M' in market_cap:
                return int(float(market_cap.replace('M', '')) / 10)
            elif 'k' in market_cap:
                return int(float(market_cap.replace('k', '')))
            else:
                return int(float(market_cap))
        except (ValueError, TypeError):
            return 0

    def get_sectors(self) -> List[Dict]:
        """Get list of all sectors."""
        query = """
            SELECT DISTINCT(sector) as sector 
            FROM instruments 
            WHERE sector NOT IN ('', 'None', 'N/A') 
                AND sector IS NOT NULL
                AND active = TRUE
            ORDER BY sector ASC
        """

        with self.db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query)
                return [dict(row) for row in cursor.fetchall()]

    def get_subsectors(self, sector_name: str) -> List[Dict]:
        """Get list of sub-sectors for a given sector."""
        query = """
            SELECT DISTINCT(subsector) as subsector 
            FROM instruments 
            WHERE sector = %s 
                AND subsector IS NOT NULL
                AND subsector NOT IN ('', 'None', 'N/A')
                AND active = TRUE
            ORDER BY subsector ASC
        """

        with self.db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, [sector_name])
                return [dict(row) for row in cursor.fetchall()]

    def update_favourite_status(self, stock_id: int, is_favourite: bool) -> bool:
        """Update favourite status of a stock."""
        query = "UPDATE instruments SET favourite = %s WHERE id = %s"

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, [is_favourite, stock_id])
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error updating favourite status: {e}")
            return False


class PerformanceCalculator:
    """Handles performance metric calculations."""

    @staticmethod
    def calculate_percentage_change(current: float, previous: float) -> float:
        """Calculate percentage change between two values."""
        if previous == 0 or previous is None or current is None:
            return 0.0
        try:
            return round(((current - previous) * 100) / previous, 2)
        except (TypeError, ZeroDivisionError):
            return 0.0

    @staticmethod
    def calculate_basic_metrics(stock_data: StockData) -> PerformanceMetrics:
        """Calculate basic performance metrics for a single day."""
        try:
            open_close_percent = PerformanceCalculator.calculate_percentage_change(
                stock_data.close, stock_data.open
            )

            # For high-low percent, calculate as (high-low)/high * 100
            if stock_data.high > 0:
                high_low_percent = round(((stock_data.high - stock_data.low) * 100) / stock_data.high, 2)
            else:
                high_low_percent = 0.0

            return PerformanceMetrics(
                open_close_percent=open_close_percent,
                high_low_percent=high_low_percent
            )
        except (TypeError, ValueError, ZeroDivisionError) as e:
            logger.warning(f"Error calculating basic metrics for {stock_data.company_name}: {e}")
            return PerformanceMetrics(
                open_close_percent=0.0,
                high_low_percent=0.0
            )

    @staticmethod
    def calculate_advanced_metrics(
        current: StockData,
        previous: Optional[StockData]
    ) -> PerformanceMetrics:
        """Calculate advanced performance metrics comparing with previous day."""
        metrics = PerformanceCalculator.calculate_basic_metrics(current)

        if previous:
            try:
                metrics.prev_close_percent = PerformanceCalculator.calculate_percentage_change(
                    current.close, previous.close
                )

                metrics.vol_percent = PerformanceCalculator.calculate_percentage_change(
                    current.volume, previous.volume
                )

                # Gap up: current open vs previous high
                if current.open > previous.high:
                    metrics.gap_up = PerformanceCalculator.calculate_percentage_change(
                        current.open, previous.high
                    )

                # Gap down: current open vs previous low
                if current.open < previous.low:
                    metrics.gap_down = PerformanceCalculator.calculate_percentage_change(
                        current.open, previous.low
                    )
            except (TypeError, ValueError) as e:
                logger.warning(f"Error calculating advanced metrics for {current.company_name}: {e}")

        return metrics


# Initialize Flask app
app = Flask(__name__)

# Initialize services
db_manager = DatabaseManager()
stock_service = StockService(db_manager)
calculator = PerformanceCalculator()


# Helper functions
def get_eod_data(start_date: str, end_date: str,
                sector: Optional[str] = None, subsector: Optional[str] = None) -> List[StockData]:
    """Fetch EOD data for specified date range and filters."""
    query = """
        SELECT 
            instruments.nameofcompany, 
            instruments.sector, 
            instruments.subsector, 
            eod.date,
            eod.open,
            eod.close,
            eod.high,
            eod.low,
            eod.volume
        FROM 
            eod 
            INNER JOIN instruments ON instruments.id = eod.instruments_id
        WHERE
            eod.date >= %s AND eod.date <= %s
            AND instruments.active = TRUE
    """

    params = [start_date, end_date]

    if sector:
        query += " AND instruments.sector = %s"
        params.append(sector)

    if subsector:
        query += " AND instruments.subsector = %s"
        params.append(subsector)

    query += " ORDER BY instruments.nameofcompany, eod.date ASC"

    with db_manager.get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            records = cursor.fetchall()

            return [
                StockData(
                    date=record['date'],
                    open=float(record['open']),
                    close=float(record['close']),
                    high=float(record['high']),
                    low=float(record['low']),
                    volume=int(record['volume']),
                    company_name=record['nameofcompany'],
                    sector=record['sector'],
                    subsector=record['subsector']
                )
                for record in records
            ]


def get_unique_dates(start_date: str, end_date: str) -> List[date]:
    """Get unique trading dates in the specified range."""
    query = """
        SELECT DISTINCT(date) 
        FROM eod 
        WHERE date >= %s AND date <= %s
        ORDER BY date ASC
    """

    with db_manager.get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, [start_date, end_date])
            records = cursor.fetchall()
            return [record['date'] for record in records]


def group_by_company(stock_data: List[StockData]) -> Dict[str, List[StockData]]:
    """Group stock data by company name."""
    company_data = {}

    for data in stock_data:
        if data.company_name not in company_data:
            company_data[data.company_name] = []
        company_data[data.company_name].append(data)

    # Sort each company's data by date
    for company in company_data:
        company_data[company].sort(key=lambda x: x.date)

    return company_data


def calculate_daily_performance(
    company_data: Dict[str, List[StockData]],
    unique_dates: List[date]
) -> Dict[str, Dict]:
    """Calculate daily performance metrics for all companies."""
    performance_results = {}

    for company_name, data_list in company_data.items():
        company_performance = {}
        previous_data = None

        # Create a lookup for quick date access
        data_by_date = {data.date: data for data in data_list}

        for trading_date in unique_dates:
            if trading_date in data_by_date:
                current_data = data_by_date[trading_date]

                # Calculate metrics
                if previous_data:
                    metrics = calculator.calculate_advanced_metrics(
                        current_data, previous_data
                    )
                else:
                    metrics = calculator.calculate_basic_metrics(current_data)

                # Store metrics (ensure no None values for template compatibility)
                company_performance[trading_date] = {
                    'openClosePercent': metrics.open_close_percent or 0,
                    'highLowPercent': metrics.high_low_percent or 0,
                    'prevClosePercent': metrics.prev_close_percent or 0,
                    'volPercent': metrics.vol_percent or 0,
                    'gapUp': metrics.gap_up if metrics.gap_up and metrics.gap_up > 0 else 0,
                    'gapDown': metrics.gap_down if metrics.gap_down and metrics.gap_down < 0 else 0
                }

                previous_data = current_data

        if company_performance:
            performance_results[company_name] = company_performance

    return performance_results


def calculate_watchlist_performance(stocks: List[Dict]) -> List[Dict]:
    """Calculate performance metrics for watchlist stocks."""
    logger.info(f"Calculating performance for {len(stocks)} stocks")

    # Get date intervals for performance calculation
    date_intervals = get_date_intervals()
    logger.info(f"Date intervals: {date_intervals}")

    stocks_with_returns = []
    stocks_without_returns = []

    for i, stock in enumerate(stocks):
        try:
            performance_data = get_stock_performance(stock, date_intervals)

            if performance_data.get('1D') != "-":
                stocks_with_returns.append(performance_data)
                logger.debug(f"Stock {stock['symbol']}: 1D = {performance_data.get('1D')}")
            else:
                stocks_without_returns.append(performance_data)
                logger.debug(f"Stock {stock['symbol']}: No performance data")

        except Exception as e:
            logger.error(f"Error calculating performance for {stock.get('symbol', 'Unknown')}: {e}")
            stocks_without_returns.append(stock)

    # Sort by subsector and combine
    stocks_with_returns.sort(key=lambda x: x.get('subsector', ''))
    stocks_with_returns.extend(stocks_without_returns)

    logger.info(f"Performance calculation complete: {len(stocks_with_returns)} with returns, {len(stocks_without_returns)} without")

    return stocks_with_returns


def get_date_intervals() -> Dict[str, Optional[date]]:
    """Get adjusted date intervals for performance calculations."""
    # Get all available trading dates (more recent data first)
    query = "SELECT DISTINCT(date) as date FROM eod ORDER BY date DESC LIMIT 500"

    with db_manager.get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            available_dates = [row['date'] for row in cursor.fetchall()]

    logger.info(f"Found {len(available_dates)} trading dates")
    if available_dates:
        logger.info(f"Date range: {available_dates[-1]} to {available_dates[0]}")

    if not available_dates:
        logger.warning("No EOD data found in database!")
        return {}

    # Calculate target intervals from the latest available date
    latest_date = available_dates[0]  # Most recent date

    # Calculate intervals more conservatively
    intervals = {
        'today': latest_date,
        '1D': latest_date - timedelta(days=1),
        '1W': latest_date - timedelta(days=7),
        '1M': latest_date - timedelta(days=30),
        '3M': latest_date - timedelta(days=90),
        '6M': latest_date - timedelta(days=180),
        '1Y': latest_date - timedelta(days=365)
    }

    # Adjust to available trading dates
    adjusted_intervals = {}
    for interval_name, target_date in intervals.items():
        found_date = find_nearest_trading_date(target_date, available_dates)
        adjusted_intervals[interval_name] = found_date

        if found_date:
            days_diff = (latest_date - found_date).days
            logger.info(f"{interval_name}: target {target_date} -> found {found_date} ({days_diff} days ago)")
        else:
            logger.warning(f"{interval_name}: No data found for target {target_date}")

    return adjusted_intervals


def find_nearest_trading_date(target_date: date, available_dates: List[date]) -> Optional[date]:
    """Find the nearest available trading date."""
    # Convert to set for faster lookup
    date_set = set(available_dates)

    # First try exact match
    if target_date in date_set:
        return target_date

    # Look back up to 30 days for shorter intervals, 60 days for longer intervals
    max_days = 60 if target_date < (datetime.today().date() - timedelta(days=90)) else 30

    for i in range(max_days):
        check_date = target_date - timedelta(days=i)
        if check_date in date_set:
            return check_date

    # If still not found, try the closest date from available dates
    available_dates_sorted = sorted(available_dates, reverse=True)  # Most recent first

    for available_date in available_dates_sorted:
        if available_date <= target_date:
            return available_date

    # Return the oldest available date as last resort
    return available_dates_sorted[-1] if available_dates_sorted else None


def get_stock_performance(stock: Dict, date_intervals: Dict) -> Dict:
    """Calculate performance for a single stock."""
    stock_copy = stock.copy()

    # Get closing prices for different intervals
    close_prices = get_close_prices(stock['id'], date_intervals)

    if 'today' in close_prices and close_prices['today']:
        stock_copy['LTP'] = close_prices['today']

    # Calculate percentage changes
    time_intervals = ['1D', '1W', '1M', '3M', '6M', '1Y']

    for interval in time_intervals:
        if ('today' in close_prices and
            interval in close_prices and
            close_prices[interval] is not None and
            close_prices['today'] is not None):
            try:
                diff = close_prices['today'] - close_prices[interval]
                percent_change = int((diff * 100) / close_prices[interval])
                stock_copy[interval] = percent_change
            except (ZeroDivisionError, TypeError):
                stock_copy[interval] = "-"
        else:
            stock_copy[interval] = "-"

    return stock_copy


def get_close_prices(stock_id: int, date_intervals: Dict) -> Dict:
    """Get closing prices for different time intervals."""
    close_prices = {}

    query = "SELECT close FROM eod WHERE date = %s AND instruments_id = %s"

    with db_manager.get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            for interval, interval_date in date_intervals.items():
                if interval_date:
                    cursor.execute(query, [interval_date, stock_id])
                    result = cursor.fetchone()
                    close_prices[interval] = result['close'] if result else None

    return close_prices

def get_search_text() -> Optional[str]:
    """Get and format search text from request."""
    search_input = request.form.get('search-bar')
    if search_input and search_input.strip():
        return f"%{search_input.strip()}%"
    return None#!/usr/bin/env python3


# Routes
@app.route('/')
@app.route('/watchlist', methods=["POST", "GET"])
def home():
    """Main watchlist page."""
    try:
        # Get filter parameters
        sector_filter = request.form.get('sector-dropdown')
        subsector_filter = request.form.get('sub-category-dropdown')
        search_text = get_search_text()

        # Get data
        stocks = stock_service.get_stocks(sector_filter, subsector_filter, search_text)
        stocks_with_performance = calculate_watchlist_performance(stocks)

        sectors = stock_service.get_sectors()
        subsectors = stock_service.get_subsectors(sector_filter) if sector_filter else []

        return render_template(
            'watchlist.html',
            listOfStocks=stocks_with_performance,
            listOfSectors=sectors,
            listOfSubSectors=subsectors,
            selectedSector=sector_filter,
            selectedSubSector=subsector_filter
        )

    except Exception as e:
        logger.error(f"Error handling watchlist request: {e}")
        return f"<h1>Error</h1><p>Unable to load watchlist: {str(e)}</p>", 500


@app.route('/daily-performance')
def daily_performance():
    """Daily performance analysis page."""
    try:
        # Get parameters from request or use defaults
        start_date = request.args.get('start_date', '2023-10-01')
        end_date = request.args.get('end_date', '2023-10-30')
        sector = request.args.get('sector')
        subsector = request.args.get('subsector')

        # Get EOD data and analyze performance
        eod_data = get_eod_data(start_date, end_date, sector, subsector)
        unique_dates = get_unique_dates(start_date, end_date)

        if not eod_data:
            performance_results = {}
        else:
            company_data = group_by_company(eod_data)
            performance_results = calculate_daily_performance(company_data, unique_dates)

        # Add filter information for display
        filter_info = {
            'start_date': start_date,
            'end_date': end_date,
            'sector': sector,
            'subsector': subsector
        }

        return render_template(
            'daily.html',
            columns=unique_dates,
            performance=performance_results,
            filter_info=filter_info
        )

    except Exception as e:
        logger.error(f"Error handling daily performance request: {e}")
        return f"<h1>Error</h1><p>Unable to load performance data: {str(e)}</p>", 500


@app.route('/fetchSubSector', methods=["POST", "GET"])
def fetch_sub_sector():
    """AJAX endpoint for fetching sub-sectors."""
    try:
        if request.method == 'POST':
            sector_name = request.form['sectorName']
            subsectors = stock_service.get_subsectors(sector_name)

            return jsonify({
                'subsector': [sub['subsector'] for sub in subsectors]
            })
    except Exception as e:
        logger.error(f"Error fetching sub-sectors: {e}")
        return jsonify({'error': 'Failed to fetch sub-sectors'}), 500


@app.route("/insert", methods=["POST", "GET"])
def insert():
    """AJAX endpoint for updating favourite status."""
    try:
        if request.method == 'POST':
            stock_id = int(request.form['data'])
            is_favourite = request.form['event'] == 'true'

            success = stock_service.update_favourite_status(stock_id, is_favourite)

            if success:
                message = ('Favourite Stocks Updated Successfully!' if is_favourite
                         else 'Stocks removed from favourite Successfully!')
                return jsonify(message)
            else:
                return jsonify('Failed to update favourite status'), 500

    except Exception as e:
        logger.error(f"Error updating favourite: {e}")
        return jsonify('Favourite Stocks Not Updated'), 500


@app.route('/api/performance')
def api_performance():
    """API endpoint for performance data."""
    try:
        start_date = request.args.get('start_date', '2023-10-01')
        end_date = request.args.get('end_date', '2023-10-30')
        sector = request.args.get('sector')
        subsector = request.args.get('subsector')

        eod_data = get_eod_data(start_date, end_date, sector, subsector)
        unique_dates = get_unique_dates(start_date, end_date)

        if not eod_data:
            performance_results = {}
        else:
            company_data = group_by_company(eod_data)
            performance_results = calculate_daily_performance(company_data, unique_dates)

        context = {
            'columns': [d.isoformat() for d in unique_dates],
            'performance': performance_results,
            'total_companies': len(performance_results),
            'date_range': {'start': start_date, 'end': end_date},
            'sector': sector,
            'subsector': subsector
        }

        return jsonify(context)

    except Exception as e:
        logger.error(f"Error handling API performance request: {e}")
        return jsonify({'error': 'Unable to fetch performance data'}), 500


@app.route('/debug/data-status')
def debug_data_status():
    """Debug endpoint to check data availability."""
    try:
        # Get database status
        db_status = check_database_status()

        # Get date intervals
        date_intervals = get_date_intervals()

        # Test with first few stocks
        stocks = stock_service.get_stocks()[:5]  # Get first 5 stocks

        debug_info = {
            'database_status': db_status,
            'date_intervals': {k: v.isoformat() if v else None for k, v in date_intervals.items()},
            'sample_stocks': []
        }

        for stock in stocks:
            close_prices = get_close_prices(stock['id'], date_intervals)
            debug_info['sample_stocks'].append({
                'symbol': stock['symbol'],
                'id': stock['id'],
                'close_prices': {k: v for k, v in close_prices.items() if v is not None}
            })

        return jsonify(debug_info)

    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        return jsonify({'error': str(e)}), 500


def check_database_status():
    """Check database status and data availability."""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Check instruments table
                cursor.execute("SELECT COUNT(*) FROM instruments WHERE active = TRUE")
                instrument_count = cursor.fetchone()[0]

                # Check EOD table
                cursor.execute("SELECT COUNT(*) FROM eod")
                eod_count = cursor.fetchone()[0]

                # Check latest EOD date
                cursor.execute("SELECT MAX(date) FROM eod")
                latest_eod = cursor.fetchone()[0]

                # Check earliest EOD date
                cursor.execute("SELECT MIN(date) FROM eod")
                earliest_eod = cursor.fetchone()[0]

                # Check data coverage for different periods
                if latest_eod and earliest_eod:
                    data_span_days = (latest_eod - earliest_eod).days

                    # Check specific time periods
                    six_months_ago = latest_eod - timedelta(days=180)
                    one_year_ago = latest_eod - timedelta(days=365)

                    cursor.execute("SELECT COUNT(DISTINCT date) FROM eod WHERE date >= %s", [six_months_ago])
                    six_month_dates = cursor.fetchone()[0]

                    cursor.execute("SELECT COUNT(DISTINCT date) FROM eod WHERE date >= %s", [one_year_ago])
                    one_year_dates = cursor.fetchone()[0]

                    logger.info(f"Database status: {instrument_count} active instruments, {eod_count} EOD records")
                    logger.info(f"Data span: {earliest_eod} to {latest_eod} ({data_span_days} days)")
                    logger.info(f"6-month data: {six_month_dates} trading days available")
                    logger.info(f"1-year data: {one_year_dates} trading days available")

                    return {
                        'instruments': instrument_count,
                        'eod_records': eod_count,
                        'latest_eod': latest_eod,
                        'earliest_eod': earliest_eod,
                        'data_span_days': data_span_days,
                        'six_month_dates': six_month_dates,
                        'one_year_dates': one_year_dates
                    }
                else:
                    logger.warning("No EOD date information available")
                    return None

    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return None


if __name__ == '__main__':
    logger.info("Starting Stock Screener application")

    # Check database status
    db_status = check_database_status()
    if db_status:
        logger.info(f"Database ready: {db_status}")
    else:
        logger.warning("Database check failed - performance calculations may not work")

    app.run(debug=True, host='127.0.0.1', port=5000)