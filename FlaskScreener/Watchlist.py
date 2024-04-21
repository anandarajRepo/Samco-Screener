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
startDate = '2023-01-01'
endDate = '2023-12-06'
sector = 'Technology Services'
nameOfCompany = 'Peninsula Land Limited'


######################
### List of Stocks ###
######################
def getTheListOfStocks(sectorFilter, subSectorFilter, searchText):
    instrument_query_template = """
        SELECT id, symbol, nameofcompany, sector, subsector, favourite, dateoflistings, marketcap
        FROM instruments
        {% if searchText %}
        WHERE nameofcompany ILIKE {{ searchText }}
        {% else %}
        WHERE favourite = true AND active = TRUE
        {% endif %}
        {% if sectorFilter %}
        WHERE sector = {{ sectorFilter }} AND active = TRUE
        {% endif %}
        {% if subSectorFilter %}
        AND subsector = {{ subSectorFilter }}
        {% endif %}
        ORDER BY subsector, nameofcompany ASC
    """

    instrument_query_template_data = {
        "searchText": searchText,
        "sectorFilter": sectorFilter,
        "subSectorFilter": subSectorFilter,
    }

    query, bind_params = jinjaSql.prepare_query(instrument_query_template, instrument_query_template_data)
    conn.execute(query, bind_params)
    listOfStocks = conn.fetchall()

    for index, listOfStock in enumerate(listOfStocks):
        if listOfStock['marketcap'] is not None and 'T' in listOfStock['marketcap']:
            listOfStocks[index]['marketcapincrs'] = int((float(listOfStock['marketcap'].replace('T', '')) * 100000))
        elif listOfStock['marketcap'] is not None and 'B' in listOfStock['marketcap']:
            listOfStocks[index]['marketcapincrs'] = int((float(listOfStock['marketcap'].replace('B', '')) * 100))
        elif listOfStock['marketcap'] is not None and 'M' in listOfStock['marketcap']:
            listOfStocks[index]['marketcapincrs'] = int((float(listOfStock['marketcap'].replace('M', '')) / 10))
        elif listOfStock['marketcap'] is not None and 'k' in listOfStock['marketcap']:
            listOfStocks[index]['marketcapincrs'] = int((float(listOfStock['marketcap'].replace('k', ''))))

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

    dictOfDateIntervals = {'today': today, '1D': one_day, '1W': one_week, '1M': one_month, '3M': three_month,
                           '6M': six_month, '1Y': one_year}
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

        # Define the list of time intervals and their corresponding keys
        time_intervals = ['today', '1D', '1W', '1M', '3M', '6M', '1Y']

        # Initialize a dictionary to store the fetched close prices
        close_prices = {}

        # Loop over the time intervals and fetch the close prices
        for interval in time_intervals:
            if interval in dictOfDateIntervalsAdj:
                if dictOfDateIntervalsAdj[interval]:
                    query = """SELECT close FROM eod WHERE date = '{0}' AND instruments_id = '{1}'""".format(dictOfDateIntervalsAdj[interval], listOfStock['id'])
                    # print(query)
                    conn.execute(query)
                    close_price = conn.fetchone()
                    if close_price:
                        close_prices[interval] = close_price['close']
                    else:
                        close_prices[interval] = None

        if 'today' in close_prices:
            listOfStock['LTP'] = close_prices['today']

        for interval in time_intervals:
            if 'today' in close_prices and interval in close_prices and close_prices[interval] and close_prices['today'] not in [None, '']:
                diff = close_prices['today'] - close_prices[interval]
                percentChange = ((diff * 100) / close_prices[interval])
                listOfStock[interval] = int(percentChange)
                if interval == '1D':
                    listOfStocksWithReturns.append(listOfStock)
            else:
                listOfStock[interval] = "-"
                if interval == '1D':
                    listOfStocksWithoutReturns.append(listOfStock)

    # listOfStocksWithReturns.sort(key=lambda x: x['1M'], reverse=True)
    listOfStocksWithReturns.sort(key=lambda x: x['subsector'])
    listOfStocksWithReturns.extend(listOfStocksWithoutReturns)

    # context = {'listOfStocks': listOfStocksWithReturns}
    return listOfStocksWithReturns


def getSectors():
    conn.execute("""SELECT DISTINCT(sector) as sector FROM instruments WHERE sector NOT IN (SELECT DISTINCT(sector) as sector FROM instruments WHERE sector IN ('', 'None', 
    'N/A')) ORDER BY sector ASC""")
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
    if request.form.get('search-bar') is not None:
        searchText = "%{}%".format(request.form.get('search-bar'))
    else:
        searchText = None

    listOfStocks = getTheListOfStocks(sectorFilter, subSectorFilter, searchText)
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
