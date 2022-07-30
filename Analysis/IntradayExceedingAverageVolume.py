import json
import traceback
import psycopg2
import pandas as pd
import time

from psycopg2.extras import RealDictCursor
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
samco.set_session_token(sessionToken="d84793349ed56861a7529594d2d342b7")

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
conn = db.cursor(cursor_factory=RealDictCursor)

from_date = '2022-05-01'
to_date = '2022-07-01'
symbol = '63MOONS'

try:
    conn.execute("""SELECT
                        instruments.symbol, CAST(AVG(eod.volume) AS INTEGER) as AvgVol
                    FROM 
                        eod INNER JOIN instruments ON instruments.id = eod.instruments_id
                    WHERE
                        eod.date >= '{0}' AND eod.date <= '{1}'
                    GROUP BY
                        instruments.symbol
                    ORDER BY
                        symbol ASC;""".format(from_date, to_date))
    monthlyAvgVols = conn.fetchall()

    conn.execute("""SELECT
                        instruments.symbol, eod.date, eod.ltp, eod.volume
                    FROM 
                        eod INNER JOIN instruments ON instruments.id = eod.instruments_id
                    WHERE
                        eod.date >= '{0}' AND eod.date <= '{1}'
                    ORDER BY
                        eod.date ASC;""".format(from_date, to_date, symbol))
    dailyVolumes = conn.fetchall()

except Exception as e:
    db.rollback()
    print(e)
    print(traceback.print_exc())

for monthlyAvgVol in monthlyAvgVols:
    for dailyVolume in dailyVolumes:
        if (monthlyAvgVol['symbol'] == dailyVolume['symbol']) and (dailyVolume['volume'] > monthlyAvgVol['avgvol']):
            print(monthlyAvgVol['symbol'], dailyVolume['date'], monthlyAvgVol['avgvol'], dailyVolume['volume'], dailyVolume['ltp'])

