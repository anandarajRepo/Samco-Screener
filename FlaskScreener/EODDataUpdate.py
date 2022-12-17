import json
import traceback
import psycopg2
import pandas as pd
import time

from snapi_py_client.snapi_bridge import StocknoteAPIPythonBridge
from pprint import pprint
from configparser import ConfigParser

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
samco.set_session_token(sessionToken="fa7537a21205f3c51f5bc8a80e6ae2e7")

#################
### File Path ###
#################
jsonFilePath = '../Output/EQUITY_L.json'

###################################
### Get inputs from config file ###
###################################
config = ConfigParser()
config.read('../config.ini')

#################
### DB config ###
#################
databaseName = config.get('Database', 'databaseName')
user = config.get('Database', 'user')
password = config.get('Database', 'password')
host = config.get('Database', 'host')
port = config.get('Database', 'port')

db = psycopg2.connect(database=databaseName, user=user, password=password, host=host, port=port)

###########################################
### Open json stock data to write in DB ###
###########################################
try:
    f = open(jsonFilePath)
    nse_companies = json.load(f)
    f.close()
except FileNotFoundError as error:
    print("Json file not found error: ", error)

##############################################
### Iterating retrieving historic EOD Data ###
##############################################

# for nse_company in nse_companies:
#     HistoricalCandleData = samco.get_historical_candle_data(symbol_name=nse_company["SYMBOL"], exchange=samco.EXCHANGE_NSE, from_date='2021-01-01', to_date='2021-05-21')
#     dictHistoricalData = json.loads(HistoricalCandleData)
#     df = pd.DataFrame(dictHistoricalData['historicalCandleData'])
#     print(nse_company["SYMBOL"])
#     print(df)

### Update EOD data to DB
try:
    conn = db.cursor()

    for nse_company in nse_companies:
        # if "SECTOR" in nse_company and "SUBSECTOR" in nse_company:
        conn.execute("""SELECT id FROM instruments WHERE active = TRUE AND symbol = '{0}'""".format(nse_company['SYMBOL']))
        instrument_id = conn.fetchone()
        print(nse_company["SYMBOL"])
        # time.sleep(1)
        HistoricalCandleData = samco.get_historical_candle_data(symbol_name=nse_company["SYMBOL"], exchange=samco.EXCHANGE_NSE, from_date='2021-12-08', to_date='2022-12-09')
        dictHistoricalData = json.loads(HistoricalCandleData)
        if dictHistoricalData["status"] == "Success" and instrument_id[0]:
            for eachDayEod in dictHistoricalData['historicalCandleData']:
                conn.execute("""INSERT INTO eod (instruments_id, date, open, high, low, close, ltp, volume) VALUES ( '{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}')""".format(instrument_id[0],
                                                                                                                         eachDayEod['date'],
                                                                                                                         eachDayEod['open'],
                                                                                                                         eachDayEod['high'],
                                                                                                                         eachDayEod['low'],
                                                                                                                         eachDayEod['close'],
                                                                                                                         eachDayEod['ltp'],
                                                                                                                         eachDayEod['volume']))
        else:
            print(f"No Records for instrument: {nse_company['NAMEOFCOMPANY']}")
    db.commit()
except Exception as e:
    db.rollback()
    print(e)
    print(traceback.print_exc())
