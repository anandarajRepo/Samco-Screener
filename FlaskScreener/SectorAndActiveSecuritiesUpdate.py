import psycopg2
import json
import traceback

from configparser import ConfigParser
from psycopg2.extras import RealDictCursor

### File Path
jsonFilePath = 'Output/EQUITY_L.json'

### Get inputs from config file
config = ConfigParser()
config.read('config.ini')

### DB config
databaseName = config.get('Database', 'databaseName')
user = config.get('Database', 'user')
password = config.get('Database', 'password')
host = config.get('Database', 'host')
port = config.get('Database', 'port')

db = psycopg2.connect(database=databaseName, user=user, password=password, host=host, port=port)

### Open json stock data to write in DB
try:
    f = open(jsonFilePath)
    nse_companies = json.load(f)
    f.close()
except FileNotFoundError as error:
    print("Json file not found error: ", error)

### Insert new instrument to DB and update the sector & sub-sector details
try:
    conn = db.cursor()

    for nse_company in nse_companies:
        conn.execute("""SELECT COUNT(*) FROM instruments WHERE symbol = '{0}'""".format(nse_company['SYMBOL']))
        print("""SELECT COUNT(*) FROM instruments WHERE symbol = '{0}'""".format(nse_company['SYMBOL']))
        record = conn.fetchone()
        for row in record:
            print(row)
        if row > 0:
            if "SECTOR" in nse_company or "SUBSECTOR" in nse_company:
                conn.execute("""UPDATE instruments SET sector = '{0}', subsector = '{1}', active = TRUE WHERE symbol = '{2}'""".format(nse_company['SECTOR'], nse_company['SUBSECTOR'], nse_company['SYMBOL']))
                print("""UPDATE instruments SET sector = '{0}', subsector = '{1}', active = TRUE  WHERE symbol = '{2}'""".format(nse_company['SECTOR'], nse_company['SUBSECTOR'], nse_company['SYMBOL']))
        else:
            # if "SECTOR" in nse_company and "SUBSECTOR" in nse_company:
            conn.execute("""INSERT INTO instruments (symbol, nameofcompany, series, dateoflistings, paidvalue, marketlot, isinnumber, facevalue, sector, subsector, active) VALUES ( '{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}', NULLIF('{8}', ''), NULLIF('{9}', ''), TRUE)""".format(
                    nse_company['SYMBOL'],
                    nse_company['NAMEOFCOMPANY'].replace("'", ""),
                    nse_company['SERIES'],
                    nse_company['DATEOFLISTING'],
                    nse_company['PAIDUPVALUE'].replace(".", ""),
                    nse_company['MARKETLOT'],
                    nse_company['ISINNUMBER'],
                    nse_company['FACEVALUE'],
                    nse_company['SECTOR'],
                    nse_company['SUBSECTOR']))
            print("""INSERT INTO instruments (symbol, nameofcompany, series, dateoflistings, paidvalue, marketlot, isinnumber, facevalue, sector, subsector, active) VALUES ( '{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}', NULLIF('{8}', ''), NULLIF('{9}', ''), TRUE)""".format(
                    nse_company['SYMBOL'],
                    nse_company['NAMEOFCOMPANY'].replace("'", ""),
                    nse_company['SERIES'],
                    nse_company['DATEOFLISTING'],
                    nse_company['PAIDUPVALUE'].replace(".", ""),
                    nse_company['MARKETLOT'],
                    nse_company['ISINNUMBER'],
                    nse_company['FACEVALUE'],
                    nse_company['SECTOR'],
                    nse_company['SUBSECTOR']))
    db.commit()
except Exception as e:
    db.rollback()
    print(e)
    print(traceback.print_exc())


### Update active column in instrument table to False when instrument is not available in EQUITY_L.json
try:
    conn = db.cursor()
    conn.execute("""SELECT symbol FROM instruments""")
    records = conn.fetchall()

    # Converting the nse_companies json object to list of symbol
    symbol_list = [i['SYMBOL'] for i in nse_companies]

    # for row in records:
    for record in records:
        if not (record[0] in symbol_list):
            print(record[0])
            conn.execute("""UPDATE instruments SET active = FALSE WHERE symbol = '{0}'""".format(record[0]))
    db.commit()
except Exception as e:
    db.rollback()
    print(e)
    print(traceback.print_exc())
