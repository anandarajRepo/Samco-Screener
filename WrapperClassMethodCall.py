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
samco.set_session_token(sessionToken="d1c5f3f1534ef9ec92be4f99c10a1c79")

################
### Analysis ###
################

# pprint(samco.search_equity_derivative(search_symbol_name="BANKNIFTY",exchange=samco.EXCHANGE_NFO))

HistoricalCandleData = samco.get_historical_candle_data(symbol_name='ADANIGAS', exchange=samco.EXCHANGE_NSE, from_date='2021-01-01', to_date='2021-05-21')

dictHistoricalData = json.loads(HistoricalCandleData)
df_hist = pd.DataFrame(dictHistoricalData['historicalCandleData'])
print(df_hist)

# IntradayCandleData = samco.get_intraday_candle_data(symbol_name='AAVAS', exchange=samco.EXCHANGE_NSE, from_date='2021-05-21 09:00:00')
# IntradayCandleData = samco.get_intraday_candle_data(symbol_name='INFY21APRFUT', exchange=samco.EXCHANGE_NFO, from_date='2021-04-17 09:15:00', to_date='2021-04-17 15:30:00')
# IntradayCandleData = samco.get_intraday_candle_data(symbol_name='WIPRO21APR450CE', exchange=samco.EXCHANGE_NFO, from_date='2021-04-16 09:15:00', to_date='2021-04-16 15:30:00')
# IntradayCandleData = samco.get_intraday_candle_data(symbol_name='BANKNIFTY22APR2132000PE', exchange=samco.EXCHANGE_NFO, from_date='2021-04-16 09:15:00', to_date='2021-04-16 15:30:00')

# dictIntradayData = json.loads(IntradayCandleData)
# df_intra = pd.DataFrame(dictIntradayData['intradayCandleData'])
# print(df_intra)

