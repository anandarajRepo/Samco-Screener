import json
from snapi_py_client.snapi_bridge import StocknoteAPIPythonBridge
from pprint import pprint
import pandas as pd

################################################################
### Options to display complete set of data frame in console ###
################################################################

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
# pd.set_option('display.max_colwidth', -1)

#####################
### Session Token ###
#####################

samco = StocknoteAPIPythonBridge()
samco.set_session_token(sessionToken="759a8f43d26d830772456cc9cd3b5519")

################
### Analysis ###
################

# pprint(samco.search_equity_derivative(search_symbol_name="BANKNIFTY",exchange=samco.EXCHANGE_NFO))

HistoricalCandleData = samco.get_historical_candle_data(symbol_name='ZYDUSWELL', exchange=samco.EXCHANGE_NSE, from_date='2022-08-12', to_date='2022-08-30')

dictHistoricalData = json.loads(HistoricalCandleData)
df_hist = pd.DataFrame(dictHistoricalData['historicalCandleData'])
print(df_hist)
pprint(dictHistoricalData)

# IntradayCandleData = samco.get_intraday_candle_data(symbol_name='AAVAS', exchange=samco.EXCHANGE_NSE, from_date='2021-05-21 09:00:00')
# IntradayCandleData = samco.get_intraday_candle_data(symbol_name='INFY21APRFUT', exchange=samco.EXCHANGE_NFO, from_date='2021-04-17 09:15:00', to_date='2021-04-17 15:30:00')
# IntradayCandleData = samco.get_intraday_candle_data(symbol_name='WIPRO21APR450CE', exchange=samco.EXCHANGE_NFO, from_date='2021-04-16 09:15:00', to_date='2021-04-16 15:30:00')
# IntradayCandleData = samco.get_intraday_candle_data(symbol_name='BANKNIFTY22APR2132000PE', exchange=samco.EXCHANGE_NFO, from_date='2021-04-16 09:15:00', to_date='2021-04-16 15:30:00')

# dictIntradayData = json.loads(IntradayCandleData)
# df_intra = pd.DataFrame(dictIntradayData['intradayCandleData'])
# print(df_intra)

# import psycopg2
# from configparser import ConfigParser

# ###################################
# ### Get inputs from config file ###
# ###################################
# config = ConfigParser()
# config.read('config.ini')

# #################
# ### DB config ###
# #################
# databaseName = config.get('Database', 'databaseName')
# user = config.get('Database', 'user')
# password = config.get('Database', 'password')
# host = config.get('Database', 'host')
# port = config.get('Database', 'port')
# db = psycopg2.connect(database=databaseName, user=user, password=password, host=host, port=port)

# conn = db.cursor()
# conn.execute("""SELECT id FROM instruments WHERE active = TRUE AND symbol = '{0}'""".format('ZYDUSWELL'))
# instrument_id = conn.fetchone()
# print(instrument_id)

