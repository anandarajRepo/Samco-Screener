from datetime import datetime, timedelta, time
from snapi_py_client.snapi_bridge import StocknoteAPIPythonBridge
import pandas as pd
import json

## this function will help to reduce to pass session token for other apis. This will automate the session token for other apis
samco = StocknoteAPIPythonBridge()
samco.set_session_token(sessionToken="53a02e707b6f45892cb514975a5b0591")

################################################################
### Options to display complete set of data frame in console ###
################################################################
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)


###########
# File Path
###########
equity_l_csv = "Output/EQUITY_L.json"
jsonIndicies = "Output/JSON_INDICIES_TICKERTAPE.json"

with open(equity_l_csv) as f:
    equity_l_json = json.load(f)

# Fetch the distinct sectors from EQUITY_L.json
sector_unique_list = []

for equity_l_item in equity_l_json:
    for key, value in equity_l_item.items():
        if key == "SECTOR":
            if not sector_unique_list:
                sector_unique_list.append(value)
            elif value not in sector_unique_list:
                sector_unique_list.append(value)

# Creating a empty list with sector as index name
json_indices = {}

for sector in sector_unique_list:
    json_indices[sector] = []

# Adding stocks based on sector to above created empty list
for sector in sector_unique_list:
    for equity_l_item in equity_l_json:
        for key, value in equity_l_item.items():
            if key == "SECTOR" and value == sector:

                json_indices[sector].append(equity_l_item)

with open(jsonIndicies, "w") as outputfile:
    json.dump(json_indices, outputfile)

### Get date intervals
today = datetime.today().date()
start_date = today - timedelta(days=360)

if today.weekday() == 5:
    today = today - timedelta(days=1)

if today.weekday() == 6:
    today = today - timedelta(days=2)

if start_date.weekday() == 5:
    start_date = start_date - timedelta(days=1)

if start_date.weekday() == 6:
    start_date = start_date - timedelta(days=2)

# read the data from a json file
with open(jsonIndicies, 'r') as infile:
    json_indices = json.load(infile)

# Iterate json stock list
for sector in sector_unique_list:
    print("Started: " + sector)
    for nse_company in json_indices[sector]:

        HistoricalCandleData = samco.get_historical_candle_data(symbol_name=nse_company['SYMBOL'], exchange=samco.EXCHANGE_NSE, from_date=str(start_date), to_date=str(today))
        dictHistoricalData = json.loads(HistoricalCandleData)
        if dictHistoricalData['status'] != 'Failure':
            df = pd.DataFrame(dictHistoricalData['historicalCandleData'])

            # convert column of a DataFrame to type numeric
            df["date"] = pd.to_datetime(df["date"])
            df["close"] = pd.to_numeric(df["open"])
            df["high"] = pd.to_numeric(df["high"])
            df["low"] = pd.to_numeric(df["low"])
            df["close"] = pd.to_numeric(df["close"])
            df["ltp"] = pd.to_numeric(df["ltp"])
            df["volume"] = pd.to_numeric(df["volume"])

            start_price = df['close'].min()
            stop_price = df['close'].max()

            low = start_price
            high = 0
            delta = (stop_price - start_price) / 100  # here we are splitting whole price range into blocks

            ### Volume Profile Calculation
            idx_array = []
            vol_array = []
            low_array = []

            while high < stop_price:
                volume = 0
                high = low + delta

                sub_df = df.loc[df['close'].between(low, high, inclusive=False)]
                low_array.append(low)

                for i in sub_df.index.values:
                    volume = volume + df.iloc[i]['volume']

                vol_array.append(volume)
                low = high

            # using naive method
            # to convert lists to dictionary
            hashmap_vol = {}
            for key in low_array:
                for value in vol_array:
                    hashmap_vol[key] = value
                    vol_array.remove(value)
                    break

            # Printing resultant dictionary
            # print("Resultant dictionary is : " + str(hashmap_vol))

            hashmap_vol = {k: v for k, v in sorted(hashmap_vol.items(), key=lambda item: item[1])}
            # print(hashmap_vol)

            maxVol = []
            for x in list(hashmap_vol)[-5:]:
                maxVol.append(x)

            for i in range(1, len(df)):
                if i >= 0:
                    df.loc[i, "maxVol1"] = maxVol[4]
                    df.loc[i, "maxVol2"] = maxVol[3]
                    df.loc[i, "maxVol3"] = maxVol[2]
                    df.loc[i, "maxVol4"] = maxVol[1]
                    df.loc[i, "maxVol5"] = maxVol[0]
                    # Get ltp of stock
                    nse_company['currentPrice'] = df.loc[i, "ltp"]
                    # save max volume in nse_company list
                    nse_company['maxVol1'] = df.loc[i, "maxVol1"]
                    nse_company['maxVol2'] = df.loc[i, "maxVol2"]
                    nse_company['maxVol3'] = df.loc[i, "maxVol3"]
                    nse_company['maxVol4'] = df.loc[i, "maxVol4"]
                    nse_company['maxVol5'] = df.loc[i, "maxVol5"]


            # # Get the max volume of volume profile
            # nse_company['maxVol1'] = maxVol[0]
            # nse_company['maxVol2'] = maxVol[1]
            # nse_company['maxVol3'] = maxVol[2]
            # nse_company['maxVol4'] = maxVol[3]
            # nse_company['maxVol5'] = maxVol[4]
            #
            # # Get ltp of stock
            # nse_company['ltp'] = df[-1:]['ltp']

            # print(df)
        else:
            print(f"No Historical data for {nse_company['SYMBOL']}")

    print("Finished: " + sector)

with open(jsonIndicies, "w") as outputfile:
    json.dump(json_indices, outputfile)


