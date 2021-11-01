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
startDate = '2021-04-01'
endDate = '2021-09-17'
sector = 'Financials'
nameOfCompany = 'Peninsula Land Limited'


######################
### List of Stocks ###
######################
def getTheListOfStocks(sectorFilter, subSectorFilter):
    instrument_query_template = """
        SELECT id, nameofcompany, sector, subsector, favourite
        FROM instruments
        {% if sectorFilter %}
        WHERE sector = {{ sectorFilter }}
        {% else %}
        WHERE favourite = true
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

    # Get date intervals
    today = datetime.today().date() - timedelta(days=3)
    one_week = today - timedelta(days=5)
    one_month = today - timedelta(days=30)
    three_month = today - timedelta(days=90)
    six_month = today - timedelta(days=180)
    one_year = today - timedelta(days=360)

    print(today)
    print(one_week)
    print(one_month)
    print(three_month)
    print(six_month)
    print(one_year)

    conn.execute("""SELECT DISTINCT(date) as date FROM eod ORDER BY date ASC""")
    dictDate = conn.fetchall()

    for date in dictDate:
        if today == date['date']:
            pprint(date['date'])

    if today.weekday() == 5:
        today = today - timedelta(days=1)

    if today.weekday() == 6:
        today = today - timedelta(days=2)

    if one_month.weekday() == 5:
        one_month = one_month - timedelta(days=1)

    if one_month.weekday() == 6:
        one_month = one_month - timedelta(days=1)

    today = datetime(2021, 10, 14)
    one_month = datetime(2021, 9, 14)
    listOfStocksWithReturns = []
    listOfStocksWithoutReturns = []

    # for listOfStock in listOfStocks:
    #     conn.execute("""SELECT
    #                       close
    #                     FROM
    #                       eod
    #                     WHERE date = '{0}' and instruments_id = '{1}'""".format(today, listOfStock['id']))
    #     todayClose = conn.fetchone()
    #
    #     conn.execute("""SELECT
    #                       close
    #                     FROM
    #                       eod
    #                     WHERE date = '{0}' and instruments_id = '{1}'""".format(one_month, listOfStock['id']))
    #     threeMonthClose = conn.fetchone()
    #
    #     # print(listOfStock[1])
    #     # print(todayClose['close'])
    #     # print(threeMonthClose['close'])
    #
    #     if todayClose and threeMonthClose:
    #         diff = todayClose['close'] - threeMonthClose['close']
    #         percentChange = (diff * 100) / todayClose['close']
    #         listOfStock['returns'] = int(percentChange)
    #         listOfStocksWithReturns.append(listOfStock)
    #     else:
    #         listOfStock['returns'] = "-"
    #         listOfStocksWithoutReturns.append(listOfStock)
    #
    # # pprint(listOfStocksWithReturns)
    # listOfStocksWithReturns.sort(key=lambda x: x['returns'], reverse=True)
    # listOfStocksWithReturns.sort(key=lambda x: x['subsector'])
    # listOfStocksWithReturns.extend(listOfStocksWithoutReturns)
    #
    # context = {'listOfStocks': listOfStocksWithReturns}
    context = {'listOfStocks': listOfStocks}
    return context


def getSectors():
    conn.execute("""SELECT DISTINCT(sector) as sector FROM instruments""")
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

    contextStocks = getTheListOfStocks(sectorFilter, subSectorFilter)
    listOfSectors = getSectors()
    listOfSubSectors = getSubSectors(sectorFilter)

    return render_template('watchlist.html', listOfStocks=contextStocks['listOfStocks'],
                           listOfSectors=listOfSectors,
                           listOfSubSectors=listOfSubSectors,
                           selectedSector=sectorFilter,
                           selectedSubSector=subSectorFilter)


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
        conn = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    except Exception as e:
        print(e)

    ################
    ### JinjaSql ###
    ################
    jinjaSql = JinjaSql()

    app.run(debug=True)
