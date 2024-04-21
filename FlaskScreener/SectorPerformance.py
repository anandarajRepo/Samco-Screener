import pandas as pd
import psycopg2
import json

from configparser import ConfigParser
from flask import Flask, render_template, request, jsonify, redirect, url_for
from pprint import pprint

################################################################
### Options to display complete set of data frame in console ###
################################################################
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

###################################
### Get inputs from config file ###
###################################
config = ConfigParser()
config.read("../config.ini")

#################
### DB config ###
#################
db_params = {
    'database': config.get('Database', 'databaseName'),
    'user': config.get('Database', 'user'),
    'password': config.get('Database', 'password'),
    'host': config.get('Database', 'host'),
    'port': config.get('Database', 'port')
}

####################
### Flask Object ###
####################
app = Flask(__name__)


def calculateSectorPerformance(dictOfSectorPerformance=None):
    global connection, cursor
    try:
        # Connect to the PostgresSQL database
        connection = psycopg2.connect(**db_params)

        # Create a cursor object to execute SQL queries
        cursor = connection.cursor()

        # Example SQL query to fetch stock symbols and subsector
        # sql_query = "SELECT symbol, subsector FROM instruments ORDER BY subsector, symbol"
        sql_query = "SELECT symbol, subsector, sector FROM instruments WHERE sector = 'Healthcare' ORDER BY subsector, symbol"
        cursor.execute(sql_query)

        # Fetch all rows from the query result
        rows = cursor.fetchall()

        # Format the result into a dictionary with subsector as keys and lists of stock symbols as values
        subsector_json = {}
        sectorName = None
        for row in rows:
            symbol, subsector, sector = row
            sectorName = sector
            if subsector not in ['N/A', 'None', '']:
                if subsector not in subsector_json:
                    subsector_json[subsector] = []
                subsector_json[subsector].append(symbol)

        for subsector in subsector_json:

            # Initialize an empty DataFrame to store the adjusted closing prices
            last_traded_closing_prices = None

            # Loop through each stock
            for symbol in subsector_json[subsector]:

                sql_query_eod = f"SELECT date, open, high, low, close, ltp, volume FROM eod WHERE instrument_symbol = '{symbol}'"
                stock_data = pd.read_sql_query(sql_query_eod, connection)

                # Convert the 'date' column to a datetime object
                stock_data['date'] = pd.to_datetime(stock_data['date'])

                # Set the 'date' column as the index
                stock_data.set_index('date', inplace=True)

                if last_traded_closing_prices is None:
                    last_traded_closing_prices = stock_data['ltp'].to_frame()
                    last_traded_closing_prices = last_traded_closing_prices.rename(columns={'ltp': f'SYMBOL-{symbol}'})
                else:
                    last_traded_closing_prices = last_traded_closing_prices.join(stock_data['ltp'].to_frame())
                    last_traded_closing_prices = last_traded_closing_prices.rename(columns={'ltp': f'SYMBOL-{symbol}'})

                last_traded_closing_prices = last_traded_closing_prices.dropna(axis=1)

            # Resample the data to monthly frequency and calculate quarterly returns
            avg_returns_stocks = round(last_traded_closing_prices.resample('Q').last().pct_change().dropna() * 100, 2)

            # Calculate the average quarterly return for the sector in percentage
            average_sector_return_percentage = round(avg_returns_stocks.mean(axis=1), 2)

            # Create a new dictionary with date-only keys
            average_sector_return_percentage = {key.date(): value for key, value in average_sector_return_percentage.to_dict().items()}

            # print(f"SECTOR: {subsector}")
            # print(average_monthly_return_percentage)

            # dictOfSectorPerformance.update({subsector: average_sector_return_percentage})
            # dictOfSectorPerformance.update(avg_returns_stocks)

            dictOfSectorPerformance.update({"sectorName": sectorName, "subSectorName": subsector, "subSectorPerformance": average_sector_return_percentage, "stocksPerformacne": avg_returns_stocks})

        return dictOfSectorPerformance

    except (Exception, psycopg2.Error) as error:
        print(f"Error: {error}")

    finally:
        # Close the database connection
        if connection:
            cursor.close()
            connection.close()
            print("Database connection closed.")


# dictOfSectorPerformance = {}
# dictOfSectorPerformance = calculateSectorPerformance(dictOfSectorPerformance)
# columnTitle = set(next(iter(dictOfSectorPerformance.items()))[1].keys())
# pprint(dictOfSectorPerformance)
# pprint(columnTitle)

@app.route('/')
def home():
    dictOfSectorPerformance = {}
    dictOfSectorPerformance = calculateSectorPerformance(dictOfSectorPerformance)
    # columnTitle = sorted(set(next(iter(dictOfSectorPerformance['subSectorPerformance'].keys()))))
    columnTitle = sorted(set(dictOfSectorPerformance['subSectorPerformance'].keys()))
    pprint(dictOfSectorPerformance)
    pprint(columnTitle)
    return render_template('sector_performance.html', columnTitle=columnTitle, sectorPerformance=dictOfSectorPerformance)


if __name__ == '__main__':
    app.run(debug=True)
