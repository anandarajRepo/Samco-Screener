#!/usr/bin/env python3
"""
Combined Flask Application

This application combines both watchlist and daily performance functionality
with seamless navigation and filter passing between pages.
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


class StockScreenerApp:
    """Combined Flask application for stock screening functionality."""

    def __init__(self, config_path: str = "../config.ini"):
        """Initialize the Flask application."""
        self.app = Flask(__name__)
        self.db_manager = DatabaseManager(config_path)
        self.stock_service = StockService(self.db_manager)
        self.calculator = PerformanceCalculator()
        self._setup_routes()

    def _setup_routes(self):
        """Setup Flask routes."""

        # Watchlist routes
        @self.app.route('/')
        @self.app.route('/watchlist', methods=["POST", "GET"])
        def watchlist():
            """Main watchlist page."""
            return self._handle_watchlist_request()

        @self.app.route('/fetchSubSector', methods=["POST", "GET"])
        def fetch_sub_sector():
            """AJAX endpoint for fetching sub-sectors."""
            return self._handle_subsector_request()

        @self.app.route("/insert", methods=["POST", "GET"])
        def insert():
            """AJAX endpoint for updating favourite status."""
            return self._handle_favourite_update()

        # Daily performance routes
        @self.app.route('/daily-performance')
        def daily_performance():
            """Daily performance analysis page."""
            return self._handle_daily_performance_request()

        @self.app.route('/api/performance')
        def api_performance():
            """API endpoint for performance data."""
            return self._handle_api_performance_request()

    def _handle_watchlist_request(self):
        """Handle the main watchlist page request."""
        try:
            # Get filter parameters
            sector_filter = request.form.get('sector-dropdown')
            subsector_filter = request.form.get('sub-category-dropdown')
            search_text = self._get_search_text()

            # Get data
            stocks = self.stock_service.get_stocks(sector_filter, subsector_filter, search_text)
            stocks_with_performance = self._calculate_watchlist_performance(stocks)
            sectors = self.stock_service.get_sectors()
            subsectors = self.stock_service.get_subsectors(sector_filter) if sector_filter else []

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

    def _handle_daily_performance_request(self):
        """Handle daily performance analysis request."""
        try:
            # Get parameters from request or use defaults
            start_date = request.args.get('start_date', '2023-10-01')
            end_date = request.args.get('end_date', '2023-10-30')
            sector = request.args.get('sector')
            subsector = request.args.get('subsector')

            # Get EOD data and analyze performance
            eod_data = self._get_eod_data(start_date, end_date, sector, subsector)
            unique_dates = self._get_unique_dates(start_date, end_date)

            if not eod_data:
                performance_results = {}
            else:
                company_data = self._group_by_company(eod_data)
                performance_results = self._calculate_daily_performance(company_data, unique_dates)

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

    def _get_eod_data(self, start_date: str, end_date: str,
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

        with self.db_manager.get_connection() as conn:
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

    def _get_unique_dates(self, start_date: str, end_date: str) -> List[date]:
        """Get unique trading dates in the specified range."""
        query = """
            SELECT DISTINCT(date) 
            FROM eod 
            WHERE date >= %s AND date <= %s
            ORDER BY date ASC
        """

        with self.db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, [start_date, end_date])
                records = cursor.fetchall()
                return [record['date'] for record in records]

    def _group_by_company(self, stock_data: List[StockData]) -> Dict[str, List[StockData]]:
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

    def _calculate_daily_performance(
            self,
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
                        metrics = self.calculator.calculate_advanced_metrics(
                            current_data, previous_data
                        )
                    else:
                        metrics = self.calculator.calculate_basic_metrics(current_data)

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

    def _calculate_watchlist_performance(self, stocks: List[Dict]) -> List[Dict]:
        """Calculate performance metrics for watchlist stocks."""
        # Get date intervals for performance calculation
        date_intervals = self._get_date_intervals()
        stocks_with_returns = []
        stocks_without_returns = []

        for stock in stocks:
            performance_data = self._get_stock_performance(stock, date_intervals)

            if performance_data.get('1D') != "-":
                stocks_with_returns.append(performance_data)
            else:
                stocks_without_returns.append(performance_data)

        # Sort by subsector and combine
        stocks_with_returns.sort(key=lambda x: x.get('subsector', ''))
        stocks_with_returns.extend(stocks_without_returns)

        return stocks_with_returns

    def _get_date_intervals(self) -> Dict[str, Optional[date]]:
        """Get adjusted date intervals for performance calculations."""
        # Get all available trading dates
        query = "SELECT DISTINCT(date) as date FROM eod ORDER BY date ASC"

        with self.db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query)
                available_dates = [row['date'] for row in cursor.fetchall()]

        # Calculate target intervals
        today = datetime.today().date()
        intervals = {
            'today': today,
            '1D': today - timedelta(days=1),
            '1W': today - timedelta(days=5),
            '1M': today - timedelta(days=30),
            '3M': today - timedelta(days=90),
            '6M': today - timedelta(days=180),
            '1Y': today - timedelta(days=360)
        }

        # Adjust to available trading dates
        adjusted_intervals = {}
        for interval_name, target_date in intervals.items():
            adjusted_intervals[interval_name] = self._find_nearest_trading_date(
                target_date, available_dates
            )

        return adjusted_intervals

    def _find_nearest_trading_date(self, target_date: date, available_dates: List[date]) -> Optional[date]:
        """Find the nearest available trading date."""
        for i in range(10):  # Look back up to 10 days
            check_date = target_date - timedelta(days=i)
            if check_date in available_dates:
                return check_date
        return None

    def _get_stock_performance(self, stock: Dict, date_intervals: Dict) -> Dict:
        """Calculate performance for a single stock."""
        stock_copy = stock.copy()

        # Get closing prices for different intervals
        close_prices = self._get_close_prices(stock['id'], date_intervals)

        if 'today' in close_prices:
            stock_copy['LTP'] = close_prices['today']

        # Calculate percentage changes
        time_intervals = ['1D', '1W', '1M', '3M', '6M', '1Y']

        for interval in time_intervals:
            if ('today' in close_prices and
                    interval in close_prices and
                    close_prices[interval] is not None and
                    close_prices['today'] is not None):

                diff = close_prices['today'] - close_prices[interval]
                percent_change = int((diff * 100) / close_prices[interval])
                stock_copy[interval] = percent_change
            else:
                stock_copy[interval] = "-"

        return stock_copy

    def _get_close_prices(self, stock_id: int, date_intervals: Dict) -> Dict:
        """Get closing prices for different time intervals."""
        close_prices = {}

        query = "SELECT close FROM eod WHERE date = %s AND instruments_id = %s"

        with self.db_manager.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                for interval, interval_date in date_intervals.items():
                    if interval_date:
                        cursor.execute(query, [interval_date, stock_id])
                        result = cursor.fetchone()
                        close_prices[interval] = result['close'] if result else None

        return close_prices

    def _handle_subsector_request(self):
        """Handle AJAX request for sub-sectors."""
        try:
            if request.method == 'POST':
                sector_name = request.form['sectorName']
                subsectors = self.stock_service.get_subsectors(sector_name)

                return jsonify({
                    'subsector': [sub['subsector'] for sub in subsectors]
                })
        except Exception as e:
            logger.error(f"Error fetching sub-sectors: {e}")
            return jsonify({'error': 'Failed to fetch sub-sectors'}), 500

    def _handle_favourite_update(self):
        """Handle favourite status update."""
        try:
            if request.method == 'POST':
                stock_id = int(request.form['data'])
                is_favourite = request.form['event'] == 'true'

                success = self.stock_service.update_favourite_status(stock_id, is_favourite)

                if success:
                    message = ('Favourite Stocks Updated Successfully!' if is_favourite
                               else 'Stocks removed from favourite Successfully!')
                    return jsonify(message)
                else:
                    return jsonify('Failed to update favourite status'), 500

        except Exception as e:
            logger.error(f"Error updating favourite: {e}")
            return jsonify('Favourite Stocks Not Updated'), 500

    def _handle_api_performance_request(self):
        """Handle API request for performance data."""
        try:
            start_date = request.args.get('start_date', '2023-10-01')
            end_date = request.args.get('end_date', '2023-10-30')
            sector = request.args.get('sector')
            subsector = request.args.get('subsector')

            eod_data = self._get_eod_data(start_date, end_date, sector, subsector)
            unique_dates = self._get_unique_dates(start_date, end_date)

            if not eod_data:
                performance_results = {}
            else:
                company_data = self._group_by_company(eod_data)
                performance_results = self._calculate_daily_performance(company_data, unique_dates)

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

    def _get_search_text(self) -> Optional[str]:
        """Get and format search text from request."""
        search_input = request.form.get('search-bar')
        if search_input and search_input.strip():
            return f"%{search_input.strip()}%"
        return None

    def run(self, debug: bool = True, host: str = '127.0.0.1', port: int = 5000):
        """Run the Flask application."""
        logger.info(f"Starting Stock Screener application on {host}:{port}")
        self.app.run(debug=debug, host=host, port=port)


def create_app(config_path: str = "../config.ini") -> Flask:
    """Factory function to create Flask app instance."""
    app_wrapper = StockScreenerApp(config_path)
    return app_wrapper.app


def main():
    """Main entry point for the application."""
    try:
        app_wrapper = StockScreenerApp()
        app_wrapper.run(debug=True)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())