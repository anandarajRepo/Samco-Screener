#!/usr/bin/env python
# coding: utf-8

import psycopg2
import pandas as pd

from pprint import pprint
from configparser import ConfigParser
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, timedelta, time
from jinjasql import JinjaSql

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
startDate = '2022-01-01'
endDate = '2022-12-06'
sector = 'Technology Services'
nameOfCompany = 'Peninsula Land Limited'


######################
### List of Stocks ###
######################
def getTheListOfStocks(sectorFilter, subSectorFilter):
    instrument_query_template = """
        SELECT id, symbol, nameofcompany, sector, subsector, favourite
        FROM instruments
        {% if sectorFilter %}
        WHERE sector = {{ sectorFilter }} AND active = TRUE
        {% else %}
        WHERE favourite = true AND active = TRUE
        {% endif %}
        {% if subSectorFilter %}
        AND subsector = {{ subSectorFilter }}
        {% endif %}
        ORDER BY subsector, nameofcompany ASC
    """

    instrument_query_template_data = {
        "sectorFilter": sectorFilter,
        "subSectorFilter": subSectorFilter
    }

    query, bind_params = jinjaSql.prepare_query(instrument_query_template, instrument_query_template_data)
    conn.execute(query, bind_params)
    listOfStocks = conn.fetchall()

    # for listOfStock in listOfStocks:
    #     pprint(listOfStock['id'])

    context = {'listOfStocks': listOfStocks}
    return listOfStocks


def getDateIntervals():
    conn.execute("""SELECT DISTINCT(date) as date FROM eod ORDER BY date ASC""")
    dictDate = conn.fetchall()

    listOfDictDate = []
    for date in dictDate:
        listOfDictDate.append(date['date'])

    # Get date intervals
    today = datetime.today().date()
    one_day = today - timedelta(days=1)
    one_week = today - timedelta(days=5)
    one_month = today - timedelta(days=30)
    three_month = today - timedelta(days=90)
    six_month = today - timedelta(days=180)
    one_year = today - timedelta(days=360)

    # print(today)
    # print(one_week)
    # print(one_month)
    # print(three_month)
    # print(six_month)
    # print(one_year)
    # print('----------')

    dictOfDateIntervals = {'today': today, 'one_day': one_day, 'one_week': one_week, 'one_month': one_month, 'three_month': three_month, 'six_month': six_month,
                           'one_year': one_year}
    # print('Before Adjustment')
    # pprint(dictOfDateIntervals)

    dictOfDateIntervalsAdj = {}
    for dateInterval in dictOfDateIntervals:
        dateToVerify = dictOfDateIntervals[dateInterval]
        for i in range(10):
            if dateToVerify in listOfDictDate:
                dictOfDateIntervalsAdj[dateInterval] = dateToVerify
                break
            dateToVerify = dateToVerify - timedelta(days=1)
            if i == 9:
                dictOfDateIntervalsAdj[dateInterval] = None

    # print('After Adjustment')
    # pprint(dictOfDateIntervalsAdj)

    return dictOfDateIntervalsAdj


def calculatePerformance(listOfStocks, dictOfDateIntervalsAdj):
    listOfStocksWithReturns = []
    listOfStocksWithoutReturns = []

    for listOfStock in listOfStocks:

        # conn.execute("""SELECT
        #                     (SELECT close FROM eod WHERE date = '{1}' and instruments_id = '{0}') as todayClose,
        #                     (SELECT close FROM eod WHERE date = '{2}' and instruments_id = '{0}') as oneWeekClose,
        #                     (SELECT close FROM eod WHERE date = '{3}' and instruments_id = '{0}') as oneMonthClose,
        #                     (SELECT close FROM eod WHERE date = '{4}' and instruments_id = '{0}') as threeMonthClose,
        #                     (SELECT close FROM eod WHERE date = '{5}' and instruments_id = '{0}') as sixMonthClose
        #                 FROM
        #                     eod""".format(listOfStock['id'],
        #                                 dictOfDateIntervalsAdj['today'],
        #                                 dictOfDateIntervalsAdj['one_week'],
        #                                 dictOfDateIntervalsAdj['one_month'],
        #                                 dictOfDateIntervalsAdj['three_month'],
        #                                 dictOfDateIntervalsAdj['six_month']))
        #
        # closePrice = conn.fetchone()

        if dictOfDateIntervalsAdj['today']:
            conn.execute("""SELECT close FROM eod WHERE date = '{0}' and instruments_id = '{1}'""".format(dictOfDateIntervalsAdj['today'], listOfStock['id']))
            todayClose = conn.fetchone()
        else:
            todayClose = None

        if dictOfDateIntervalsAdj['one_day']:
            conn.execute("""SELECT close FROM eod WHERE date = '{0}' and instruments_id = '{1}'""".format(dictOfDateIntervalsAdj['one_day'], listOfStock['id']))
            prevDayClose = conn.fetchone()
        else:
            prevDayClose = None

        if dictOfDateIntervalsAdj['one_week']:
            conn.execute("""SELECT close FROM eod WHERE date = '{0}' and instruments_id = '{1}'""".format(dictOfDateIntervalsAdj['one_week'], listOfStock['id']))
            oneWeekClose = conn.fetchone()
        else:
            oneWeekClose = None

        if dictOfDateIntervalsAdj['one_month']:
            conn.execute("""SELECT close FROM eod WHERE date = '{0}' and instruments_id = '{1}'""".format(dictOfDateIntervalsAdj['one_month'], listOfStock['id']))
            oneMonthClose = conn.fetchone()
        else:
            oneMonthClose = None

        if dictOfDateIntervalsAdj['three_month']:
            conn.execute("""SELECT close FROM eod WHERE date = '{0}' and instruments_id = '{1}'""".format(dictOfDateIntervalsAdj['three_month'], listOfStock['id']))
            threeMonthClose = conn.fetchone()
        else:
            threeMonthClose = None

        if dictOfDateIntervalsAdj['six_month']:
            conn.execute("""SELECT close FROM eod WHERE date = '{0}' and instruments_id = '{1}'""".format(dictOfDateIntervalsAdj['six_month'], listOfStock['id']))
            sixMonthClose = conn.fetchone()
        else:
            sixMonthClose = None

        if dictOfDateIntervalsAdj['one_year']:
            conn.execute("""SELECT close FROM eod WHERE date = '{0}' and instruments_id = '{1}'""".format(dictOfDateIntervalsAdj['one_year'], listOfStock['id']))
            oneYearClose = conn.fetchone()
        else:
            oneYearClose = None

        if todayClose:
            listOfStock['LTP'] = todayClose['close']

        if todayClose and prevDayClose:
            diff = todayClose['close'] - prevDayClose['close']
            if diff >= 0:
                percentChange = ((diff * 100) / todayClose['close'])
            else:
                percentChange = ((diff * 100) / prevDayClose['close'])
            listOfStock['1D'] = percentChange
            listOfStocksWithReturns.append(listOfStock)
        else:
            listOfStock['1D'] = "-"
            listOfStocksWithoutReturns.append(listOfStock)

        if todayClose and oneWeekClose:
            diff = todayClose['close'] - oneWeekClose['close']
            if diff >= 0:
                percentChange = ((diff * 100) / todayClose['close'])
            else:
                percentChange = ((diff * 100) / oneWeekClose['close'])
            listOfStock['1W'] = int(percentChange)
            # listOfStocksWithReturns.append(listOfStock)
        else:
            listOfStock['1W'] = "-"
            # listOfStocksWithoutReturns.append(listOfStock)

        if todayClose and oneMonthClose:
            diff = todayClose['close'] - oneMonthClose['close']
            if diff >= 0:
                percentChange = ((diff * 100) / todayClose['close'])
            else:
                percentChange = ((diff * 100) / oneMonthClose['close'])
            listOfStock['1M'] = int(percentChange)
            # listOfStocksWithReturns.append(listOfStock))
        else:
            listOfStock['1M'] = "-"
            # listOfStocksWithoutReturns.append(listOfStock)

        if todayClose and threeMonthClose:
            diff = todayClose['close'] - threeMonthClose['close']
            if diff >= 0:
                percentChange = ((diff * 100) / todayClose['close'])
            else:
                percentChange = ((diff * 100) / threeMonthClose['close'])
            listOfStock['3M'] = int(percentChange)
            # listOfStocksWithReturns.append(listOfStock)
        else:
            listOfStock['3M'] = "-"
            # listOfStocksWithoutReturns.append(listOfStock)

        if todayClose and sixMonthClose:
            diff = todayClose['close'] - sixMonthClose['close']
            if diff >= 0:
                percentChange = ((diff * 100) / todayClose['close'])
            else:
                percentChange = ((diff * 100) / sixMonthClose['close'])
            listOfStock['6M'] = int(percentChange)
            # listOfStocksWithReturns.append(listOfStock)
        else:
            listOfStock['6M'] = "-"
            # listOfStocksWithoutReturns.append(listOfStock)

        if todayClose and oneYearClose:
            diff = todayClose['close'] - oneYearClose['close']
            if diff >= 0:
                percentChange = ((diff * 100) / todayClose['close'])
            else:
                percentChange = ((diff * 100) / oneYearClose['close'])
            listOfStock['1Y'] = int(percentChange)
            # listOfStocksWithReturns.append(listOfStock)
        else:
            listOfStock['1Y'] = "-"
            # listOfStocksWithoutReturns.append(listOfStock)

    listOfStocksWithReturns.sort(key=lambda x: x['1W'], reverse=True)
    listOfStocksWithReturns.sort(key=lambda x: x['subsector'])
    listOfStocksWithReturns.extend(listOfStocksWithoutReturns)

    # context = {'listOfStocks': listOfStocksWithReturns}
    return listOfStocksWithReturns


def getSectors():
    conn.execute("""SELECT DISTINCT(sector) as sector FROM instruments WHERE sector NOT IN (SELECT DISTINCT(sector) as sector FROM instruments WHERE sector IN ('', 
    'None')) ORDER BY sector ASC""")
    listOfSectors = conn.fetchall()
    return listOfSectors


def getSubSectors(sectorName):
    conn.execute("""SELECT DISTINCT(subsector) as subsector FROM instruments WHERE sector = '{0}' ORDER BY subsector ASC""".format(sectorName))
    listOfSubSectors = conn.fetchall()
    return listOfSubSectors


@app.route('/fetchSubSector', methods=["POST", "GET"])
def fetchSubSector():
    if request.method == 'POST':
        dictOfSubSectors = {'subsector': []}
        sectorName = request.form['sectorName']
        listOfSubSectors = getSubSectors(sectorName)
        for listOfSubSector in listOfSubSectors:
            dictOfSubSectors['subsector'].append(listOfSubSector['subsector'])
        return dictOfSubSectors


@app.route("/insert", methods=["POST", "GET"])
def insert():
    global msg
    if request.method == 'POST':
        checkedStockId = request.form['data']
        event = request.form['event']
        print(checkedStockId)
        print(event)

        try:
            conn.execute("""UPDATE instruments SET favourite = '{1}' WHERE id = '{0}'""".format(int(checkedStockId), event))
            db.commit()
        except Exception as e:
            print(e)

        if event == 'true':
            msg = 'Favourite Stocks Updated Successfully!'
        elif event == 'false':
            msg = 'Stocks removed from favourite Successfully!'
        return jsonify(msg)
    else:
        msg = 'Favourite Stocks Not Updated'
        return jsonify(msg)


@app.route('/', methods=["POST", "GET"])
def home():
    sectorFilter = request.form.get('sector-dropdown')
    subSectorFilter = request.form.get('sub-category-dropdown')

    listOfStocks = getTheListOfStocks(sectorFilter, subSectorFilter)
    dictOfDateIntervalsAdj = getDateIntervals()
    listOfStocksWithReturns = calculatePerformance(listOfStocks, dictOfDateIntervalsAdj)
    listOfSectors = getSectors()
    listOfSubSectors = getSubSectors(sectorFilter)

    return render_template('watchlist.html', listOfStocks=listOfStocksWithReturns,
                           listOfSectors=listOfSectors,
                           listOfSubSectors=listOfSubSectors,
                           selectedSector=sectorFilter,
                           selectedSubSector=subSectorFilter)


if __name__ == '__main__':
    ###################################
    ### Get inputs from config file ###
    ###################################
    config = ConfigParser()
    config.read("../config.ini")

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
        conn = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    except Exception as e:
        print(e)

    ################
    ### JinjaSql ###
    ################
    jinjaSql = JinjaSql()

    app.run(debug=True)
