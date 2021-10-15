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


######################
### List of Stocks ###
######################
def getTheListOfStocks():
    conn.execute("""SELECT 
                      nameofcompany, 
                      sector, 
                      subsector
                    FROM 
                      instruments""")

    listOfStocks = conn.fetchall()

    context = {'listOfStocks': listOfStocks}
    return context


@app.route('/')
def home():
    context = getTheListOfStocks()
    pprint(type(context['listOfStocks']))
    pprint(context['listOfStocks'])
    return render_template('watchlist.html', listOfStocks=context['listOfStocks'])


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
        conn = db.cursor()
    except Exception as e:
        print(e)

    app.run(debug=True)