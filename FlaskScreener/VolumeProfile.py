import pandas as pd
import yfinance as yf
import psycopg2

from psycopg2 import extras
from configparser import ConfigParser

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

nifty_50_symbols = [
    "ADANIPORTS.NS",
    "ASIANPAINT.NS",
    "AXISBANK.NS",
    "BAJAJ-AUTO.NS",
    "BAJFINANCE.NS",
    "BAJAJFINSV.NS",
    "BPCL.NS",
    "BHARTIARTL.NS",
    "INFRATEL.NS",
    "CIPLA.NS",
    "COALINDIA.NS",
    "DRREDDY.NS",
    "EICHERMOT.NS",
    "GAIL.NS",
    "GRASIM.NS",
    "HCLTECH.NS",
    "HDFCBANK.NS",
    "HEROMOTOCO.NS",
    "HINDALCO.NS",
    "HINDPETRO.NS",
    "HINDUNILVR.NS",
    "HDFC.NS",
    "ITC.NS",
    "ICICIBANK.NS",
    "IBULHSGFIN.NS",
    "IOC.NS",
    "INDUSINDBK.NS",
    "INFY.NS",
    "JSWSTEEL.NS",
    "KOTAKBANK.NS",
    "LT.NS",
    "M&M.NS",
    "MARUTI.NS",
    "NTPC.NS",
    "ONGC.NS",
    "POWERGRID.NS",
    "RELIANCE.NS",
    "SBIN.NS",
    "SUNPHARMA.NS",
    "TCS.NS",
    "TECHM.NS",
    "TITAN.NS",
    "ULTRACEMCO.NS",
    "UPL.NS",
    "VEDL.NS",
    "WIPRO.NS",
    "ZEEL.NS"
]

# Connect to the PostgresSQL database
connection = psycopg2.connect(**db_params)

# Create a cursor object to execute SQL queries
cursor = connection.cursor(cursor_factory=extras.DictCursor)

# Example SQL query to fetch stocks
sql_query = "SELECT * FROM instruments"
cursor.execute(sql_query)

# Fetch all rows from the query result
nse_stocks = cursor.fetchall()

for nse_stock in nse_stocks:
    try:
        # Example SQL query to fetch stocks
        sql_query = f"SELECT * FROM eod WHERE instruments_id={nse_stock['id']}"
        historical_data = pd.read_sql_query(sql_query, connection)

        # Print or manipulate the DataFrame as needed
        # print(historical_data)

        # Group data by price level and calculate total volume at each level
        volume_profile = historical_data.groupby('close')['volume'].sum()

        # Display the volume profile
        # print(volume_profile)

        # Sort the volume profile by volume
        volume_profile_sorted = volume_profile.sort_values(ascending=False)

        # Display the ticker symbol
        print(f"Ticker  : {nse_stock['symbol']}")
        print(f"Organization  : {nse_stock['nameofcompany']}")
        print(f"Sector  : {nse_stock['sector']}")
        print(f"Sub-Sector  : {nse_stock['subsector']}")

        # Identify the two highest volume price levels
        support_level = volume_profile_sorted.index[1]
        resistance_level = volume_profile_sorted.index[0]

        print(f"Support level: {support_level}")
        print(f"Resistance level: {resistance_level}")

        # Identify the price level with the highest volume
        highest_volume_price = volume_profile.idxmax()

        # Display the ltp
        print(f"LTP: {historical_data['close'].iloc[-1]}")

        # Look for a breakout above or below the highest volume price level
        if historical_data['close'].iloc[-1] > resistance_level:
            print("Potential long entry")
            # Calculate the percentage of price above the volume zone
            percentage_above_volume_zone = (historical_data['close'].iloc[-1] - resistance_level) / resistance_level
            print(f"Percentage of price above the volume zone: {percentage_above_volume_zone:.2%}")
        elif historical_data['close'].iloc[-1] < support_level:
            print("Potential short entry")
            # Calculate the percentage of price below the volume zone
            percentage_below_volume_zone = (support_level - historical_data['close'].iloc[-1]) / support_level
            print(f"Percentage of price below the volume zone: {percentage_below_volume_zone:.2%}")
        else:
            print("No potential entry - ltp is within the volume zone")

        print("*****======================================*****")

    except Exception as e:
        print(e)
