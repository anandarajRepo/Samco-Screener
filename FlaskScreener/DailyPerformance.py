#!/usr/bin/env python
# coding: utf-8

import psycopg2
import pandas as pd

from pprint import pprint
from configparser import ConfigParser
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template

################################################################
### Options to display complete set of data frame in console ###
################################################################
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
# pd.set_option('display.max_colwidth', -1)

####################
### Flask Object ###
####################
app = Flask(__name__)

#######################
### Global Variable ###
#######################
startDate = '2021-04-01'
endDate = '2021-09-17'
sector = 'Real Estate'
nameOfCompany = 'Peninsula Land Limited'


###############################
### Performance Calculation ###
###############################
def getTheDailyPerform():
    conn.execute("""SELECT 
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
                      eod INNER JOIN instruments ON instruments.id = eod.instruments_id
                    WHERE
                        eod.date >= '{0}' AND eod.date <= '{1}'
                        AND instruments.sector = '{2}'
                    ORDER BY eod.date ASC""".format(startDate, endDate, sector))

    records = conn.fetchall()

    conn.execute("""SELECT 
                        DISTINCT(date) 
                    FROM
                        eod 
                    WHERE
                        eod.date >= '{0}' AND eod.date <= '{1}'
                    ORDER BY eod.date ASC""".format(startDate, endDate))

    columns = conn.fetchall()

    performance = {}
    uniqueColumns = []

    for column in columns:
        uniqueColumns.append(column['date'])
        for record in records:
            if column['date'] == record['date']:
                try:
                    performance[record['nameofcompany']][column['date']] = {}

                    performance[record['nameofcompany']][column['date']]["openClosePercent"] = round((((record['close'] - record['open']) * 100) / record['open']), 2)
                    performance[record['nameofcompany']][column['date']]["highLowPercent"] = round((((record['high'] - record['low']) * 100) / record['high']), 2)
                    performance[record['nameofcompany']][column['date']]["prevClosePercent"] = round((((record['close'] - performance[record['nameofcompany']]["prevClose"]) * 100) / performance[record['nameofcompany']]["prevClose"]), 2)
                    performance[record['nameofcompany']][column['date']]["volPercent"] = round((((record['volume'] - performance[record['nameofcompany']]["prevVol"]) * 100) / performance[record['nameofcompany']]["prevVol"]))
                    performance[record['nameofcompany']][column['date']]["gapUp"] = round((((record['open'] - performance[record['nameofcompany']]["prevHigh"]) * 100) / performance[record['nameofcompany']]["prevHigh"]), 2)
                    performance[record['nameofcompany']][column['date']]["gapDown"] = round((((record['open'] - performance[record['nameofcompany']]["prevLow"]) * 100) / performance[record['nameofcompany']]["prevLow"]), 2)

                    performance[record['nameofcompany']]["prevOpen"] = record['open']
                    performance[record['nameofcompany']]["prevClose"] = record['close']
                    performance[record['nameofcompany']]["prevHigh"] = record['high']
                    performance[record['nameofcompany']]["prevLow"] = record['low']
                    performance[record['nameofcompany']]["prevVol"] = int(record['volume'])
                except KeyError:
                    if record['nameofcompany'] not in performance:
                        performance[record['nameofcompany']] = {}
                    if column['date'] not in performance[record['nameofcompany']]:
                        performance[record['nameofcompany']][column['date']] = {}
                        performance[record['nameofcompany']]["prevOpen"] = {}
                        performance[record['nameofcompany']]["prevClose"] = {}
                        performance[record['nameofcompany']]["prevHigh"] = {}
                        performance[record['nameofcompany']]["prevVol"] = {}
                        performance[record['nameofcompany']]["prevClose"] = {}

                        performance[record['nameofcompany']][column['date']]["openClosePercent"] = round((((record['close'] - record['open']) * 100) / record['open']), 2)
                        performance[record['nameofcompany']][column['date']]["highLowPercent"] = round((((record['high'] - record['low']) * 100) / record['high']), 2)

                        performance[record['nameofcompany']]["prevOpen"] = record['open']
                        performance[record['nameofcompany']]["prevClose"] = record['close']
                        performance[record['nameofcompany']]["prevHigh"] = record['high']
                        performance[record['nameofcompany']]["prevLow"] = record['low']
                        performance[record['nameofcompany']]["prevVol"] = int(record['volume'])

    context = {'columns': uniqueColumns, 'performance': performance}
    return context


@app.route('/')
def dailyPerformance():
    context = getTheDailyPerform()
    return render_template('daily.html', columns=context['columns'], performance=context['performance'])


if __name__ == '__main__':
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

    ###########################
    ### Database Connection ###
    ###########################
    try:
        db = psycopg2.connect(database=databaseName, user=user, password=password, host=host, port=port)
        conn = db.cursor(cursor_factory=RealDictCursor)
    except Exception as e:
        print(e)

    app.run(debug=True)