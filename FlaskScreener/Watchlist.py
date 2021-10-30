#!/usr/bin/env python
# coding: utf-8

import psycopg2
import pandas as pd

from pprint import pprint
from configparser import ConfigParser
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, timedelta, time

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
    if sectorFilter:
        conn.execute("""SELECT 
                          id,
                          nameofcompany, 
                          sector, 
                          subsector,
                          favourite
                        FROM 
                          instruments
                        WHERE sector = '{0}' and subsector = '{1}'
                        ORDER BY subsector, nameofcompany ASC""".format(sectorFilter, subSectorFilter))
    else:
        conn.execute("""SELECT 
                          id,
                          nameofcompany, 
                          sector, 
                          subsector,
                          favourite
                        FROM 
                          instruments
                        WHERE sector = '{0}'
                        ORDER BY subsector, nameofcompany ASC""".format('Real Estate'))

    listOfStocks = conn.fetchall()

    # for listOfStock in listOfStocks:
    #     pprint(listOfStock['id'])

    # # Get date intervals
    # today = datetime.today().date()
    # today = today - timedelta(days=1)
    #
    # if today.weekday() == 5:
    #     today = today - timedelta(days=1)
    #
    # if today.weekday() == 6:
    #     today = today - timedelta(days=2)
    #
    # # Time Interval
    # one_month = today - timedelta(days=90)
    #
    # if one_month.weekday() == 5:
    #     one_month = one_month - timedelta(days=1)
    #
    # if one_month.weekday() == 6:
    #     one_month = one_month - timedelta(days=1)
    #
    # today = datetime(2021, 10, 14)
    # one_month = datetime(2021, 9, 14)
    # listOfStocksWithReturns = []
    # listOfStocksWithoutReturns = []
    #
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
    # listOfStocksWithReturns.extend(listOfStocksWithoutReturns)
    #
    # context = {'listOfStocks': listOfStocksWithReturns}
    context = {'listOfStocks': listOfStocks}
    return context


def getSectors():
    conn.execute("""SELECT DISTINCT(sector) as sector FROM instruments""")
    listOfSectors = conn.fetchall()
    context = {'listOfSectors': listOfSectors}
    return context


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
    if request.method == 'POST':
        # favId = request.args['checkboxvalue']
        # favIdList = favId.split(',')
        # print(favIdList)

        checkedStockId = request.form['data']
        event = request.form['event']
        print(checkedStockId)
        print(event)

        try:
            # for favStockId in checkedStockId:
            conn.execute("""UPDATE instruments SET favourite = '{1}' WHERE id = '{0}'""".format(int(checkedStockId), event))
            db.commit()
        except Exception as e:
            print(e)
        msg = 'Favourite Stocks Updated Successfully!'
    else:
        msg = 'Favourite Stocks Not Updated'
    return jsonify(msg)
    # return redirect(url_for('home'))


@app.route('/', methods=["POST", "GET"])
def home():
    sectorFilter = request.form.get('sector-dropdown')
    subSectorFilter = request.form.get('sub-category-dropdown')

    contextStocks = getTheListOfStocks(sectorFilter, subSectorFilter)
    contextSector = getSectors()

    return render_template('watchlist.html', listOfStocks=contextStocks['listOfStocks'], listOfSectors=contextSector['listOfSectors'])

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

    app.run(debug=True)
