import json
from snapi_py_client.snapi_bridge import StocknoteAPIPythonBridge
from pprint import pprint
import pandas as pd
import numpy as np

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
samco.set_session_token(sessionToken="b5675ab77a319643c810be5cfaa1265a")

################
### Analysis ###
################
# pprint(samco.search_equity_derivative(search_symbol_name="RELIANCE",exchange=samco.EXCHANGE_NFO))

spot_date = samco.get_intraday_candle_data(symbol_name='RELIANCE', exchange=samco.EXCHANGE_NSE, from_date='2021-04-01 09:00:00', to_date='2021-04-16 15:30:00')
fut_data = samco.get_intraday_candle_data(symbol_name='RELIANCE21APRFUT', exchange=samco.EXCHANGE_NFO, from_date='2021-04-01 09:00:00', to_date='2021-04-16 15:30:00')

### Spot Price
df_spot_json = json.loads(spot_date)
df_spot = pd.DataFrame(df_spot_json['intradayCandleData'])
# print(df_spot)

### Future Price
df_fut_json = json.loads(fut_data)
df_fut = pd.DataFrame(df_fut_json['intradayCandleData'])
# print(df_fut)

### Merging Spot and Future Price of same instrument
merged_df = pd.merge(df_spot, df_fut, on='dateTime')

### storing dtype before converting
before = merged_df.dtypes

### converting dtypes using astype
merged_df["close_x"] = merged_df["close_x"].astype(float)
merged_df["close_y"] = merged_df["close_y"].astype(float)

### storing dtype after converting
after = merged_df.dtypes

# printing to compare
# print("BEFORE CONVERSION\n", before, "\n")
# print("AFTER CONVERSION\n", after, "\n")

### Calculating price diff btw future and spot price
merged_df['Diff'] = merged_df['close_x'] - merged_df['close_y']
merged_df['Reverse'] = np.where(merged_df['Diff'] > 0, "Reverse", None)
print(merged_df)
