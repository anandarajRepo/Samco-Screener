#!/usr/bin/env python
# coding: utf-8

import psycopg2
import pandas as pd

from pprint import pprint
from configparser import ConfigParser


################################################################
### Options to display complete set of data frame in console ###
################################################################
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
# pd.set_option('display.max_colwidth', -1)

###################################
### Get inputs from config file ###
###################################
config = ConfigParser()
config.read('../DataframeScreener/config.ini')

#################
### DB config ###
#################
databaseName = config.get('Database', 'databaseName')
user = config.get('Database', 'user')
password = config.get('Database', 'password')
host = config.get('Database', 'host')
port = config.get('Database', 'port')

### Database Connection
try:
    db = psycopg2.connect(database=databaseName, user=user, password=password, host=host, port=port)
    conn = db.cursor()
except Exception as e:
    print(e)


def getTheDailyPerform():
    conn.execute("""SELECT 
                          instruments.nameofcompany, 
                          instruments.sector, 
                          instruments.subsector, 
                          eod.date,
                          eod.open,
                          eod.close,
                          eod.volume
                        FROM 
                          eod 
                          INNER JOIN instruments ON instruments.id = eod.instruments_id""")

    records = conn.fetchall()

    conn.execute("""SELECT DISTINCT(date) FROM eod ORDER BY date ASC""")
    columns = conn.fetchall()

    candles_1 = {}

    for column in columns:
        for record in records:
            if column[0] == record[3]:
                try:
                    if column[0] in candles_1[record[0]]:
                        candles_1[record[0]][column[0]] = round((((record[5] - record[4]) * 100) / record[4]), 2)
                    else:
                        candles_1[record[0]][column[0]] = {}
                        candles_1[record[0]][column[0]] = round((((record[5] - record[4]) * 100) / record[4]), 2)
                except KeyError:
                    if record[0] not in candles_1:
                        candles_1[record[0]] = {}
                    if column[0] not in candles_1[record[0]]:
                        candles_1[record[0]][column[0]] = {}
                        candles_1[record[0]][column[0]] = round((((record[5] - record[4]) * 100) / record[4]), 2)

    ### List to pandas conversion
    df = pd.DataFrame(candles_1).T

    ### Filter percentage across all columns
    for column in columns:
        df = df[df[column[0]] > -3]

    ### Filter percentage in one column
    # df = df[df[datetime.date(2021, 4, 5)] > 10]

    return df


def getTheDailyVolume():
    conn.execute("""SELECT 
                          instruments.nameofcompany, 
                          instruments.sector, 
                          instruments.subsector, 
                          eod.date,
                          eod.open,
                          eod.close,
                          eod.volume
                        FROM 
                          eod 
                          INNER JOIN instruments ON instruments.id = eod.instruments_id""")

    records = conn.fetchall()

    conn.execute("""SELECT DISTINCT(date) FROM eod ORDER BY date ASC""")
    columns = conn.fetchall()

    candles_1 = {}

    for column in columns:
        for record in records:
            if column[0] == record[3]:
                try:
                    if column[0] in candles_1[record[0]]:
                        candles_1[record[0]][column[0]] = record[6]
                    else:
                        candles_1[record[0]][column[0]] = {}
                        candles_1[record[0]][column[0]] = record[6]
                except KeyError:
                    if record[0] not in candles_1:
                        candles_1[record[0]] = {}
                    if column[0] not in candles_1[record[0]]:
                        candles_1[record[0]][column[0]] = {}
                        candles_1[record[0]][column[0]] = record[6]

    ### List to pandas conversion
    df = pd.DataFrame(candles_1).T

    return df


def getTheDailyVolumePercentage():
    conn.execute("""SELECT 
                          instruments.nameofcompany, 
                          instruments.sector, 
                          instruments.subsector, 
                          eod.date,
                          eod.open,
                          eod.close,
                          eod.volume
                        FROM 
                          eod 
                          INNER JOIN instruments ON instruments.id = eod.instruments_id""")

    records = conn.fetchall()

    conn.execute("""SELECT DISTINCT(date) FROM eod ORDER BY date ASC""")
    columns = conn.fetchall()

    candles_1 = {}

    for column in columns:
        for record in records:
            if column[0] == record[3]:
                try:
                    if column[0] in candles_1[record[0]]:
                        candles_1[record[0]][column[0]] = round((((record[6] - candles_1[record[0]]["prevVol"]) * 100) / candles_1[record[0]]["prevVol"]))
                        candles_1[record[0]]["prevVol"] = int(record[6])
                    else:
                        candles_1[record[0]][column[0]] = {}
                        candles_1[record[0]][column[0]] = round((((record[6] - candles_1[record[0]]["prevVol"]) * 100) / candles_1[record[0]]["prevVol"]))
                        candles_1[record[0]]["prevVol"] = int(record[6])
                except KeyError:
                    if record[0] not in candles_1:
                        candles_1[record[0]] = {}
                    if column[0] not in candles_1[record[0]]:
                        candles_1[record[0]][column[0]] = {}
                        candles_1[record[0]]["prevVol"] = {}
                        if candles_1[record[0]]["prevVol"]:
                            candles_1[record[0]][column[0]] = round((((record[6] - candles_1[record[0]]["prevVol"]) * 100) / candles_1[record[0]]["prevVol"]))
                        else:
                            candles_1[record[0]]["prevVol"] = int(record[6])

    ### List to pandas conversion
    df = pd.DataFrame(candles_1).T

    return df


def color_negative_red(value):
    """
  Colors elements in a dateframe
  green if positive and red if
  negative. Does not color NaN
  values.
  """

    if value < 0:
        color = 'red'
    elif value > 0:
        color = 'green'
    else:
        color = 'black'

    return 'color: %s' % color


df = getTheDailyPerform()
df_vol = getTheDailyVolume()
df_vol_percent = getTheDailyVolumePercentage()

df.style.applymap(color_negative_red)
df_vol.style.applymap(color_negative_red)
df_vol_percent.style.applymap(color_negative_red)

df.index.name = 'Company'
df_vol.index.name = 'Company'
df_vol_percent.index.name = 'Company'

# print(df)
# print(df_vol)
# print(df_vol_percent)

merged_df = pd.concat([df, df_vol_percent], axis=1, join='inner')
merged_df = merged_df[df.columns]

# print(merged_df)


# merged_df.to_csv('merged_df.csv')

