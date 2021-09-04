import datetime
import psycopg2
import pandas as pd

from flask import Flask, render_template
from configparser import ConfigParser
from pprint import pprint

app = Flask(__name__)


# @app.route('/')
# def home():
#     return render_template('home.html')


@app.route('/')
def dailyPerformance():
    df = rearrangeDataForDisplay()

    # print(df)

    return render_template('daily_df.html', data=df.to_html(classes="table table-striped"))


def rearrangeDataForDisplay():
    conn.execute("""SELECT 
                          instruments.nameofcompany, 
                          instruments.sector, 
                          instruments.subsector, 
                          eod.date,
                          eod.open,
                          eod.close
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
        df = df[df[column[0]] > -5]

    ### Filter percentage in one column
    # df = df[df[datetime.date(2021, 4, 5)] > 10]

    return df


if __name__ == '__main__':
    ###################################
    ### Get inputs from config file ###
    ###################################
    config = ConfigParser()
    config.read('config.ini')

    #################
    ### DB config ###
    #################
    databaseName = config.get('Database', 'databaseName')
    user = config.get('Database', 'user')
    password = config.get('Database', 'password')
    host = config.get('Database', 'host')
    port = config.get('Database', 'port')

    try:
        db = psycopg2.connect(database=databaseName, user=user, password=password, host=host, port=port)
        conn = db.cursor()
    except Exception as e:
        print(e)

    app.run(debug=True)


