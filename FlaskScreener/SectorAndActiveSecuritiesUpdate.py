import psycopg2
import json
import traceback

from configparser import ConfigParser
from psycopg2.extras import RealDictCursor

### File Path
jsonFilePath = '../Output/EQUITY_L.json'

### Get inputs from config file
config = ConfigParser()
config.read('../config.ini')

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
                    updateQuery = """UPDATE instruments SET sector = '{0}', subsector = '{1}', active = TRUE WHERE symbol = '{2}'""".format(nse_company['SECTOR'], nse_company['SUBSECTOR'], nse_company['SYMBOL'])
                    conn.execute(updateQuery)
                    print(updateQuery)
            else:
                # if "SECTOR" in nse_company and "SUBSECTOR" in nse_company:
                insertQuery = """INSERT INTO instruments (symbol, nameofcompany, series, dateoflistings, paidvalue, marketlot, isinnumber, facevalue, sector, subsector, active) VALUES ( '{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}', NULLIF('{8}', 'None'), NULLIF('{9}', 'None'), TRUE)""".format(
                        nse_company['SYMBOL'],
                        nse_company['NAMEOFCOMPANY'].replace("'", ""),
                        nse_company['SERIES'],
                        nse_company['DATEOFLISTING'],
                        nse_company['PAIDUPVALUE'].replace(".", ""),
                        nse_company['MARKETLOT'],
                        nse_company['ISINNUMBER'],
                        nse_company['FACEVALUE'],
                        nse_company['SECTOR'],
                        nse_company['SUBSECTOR'])
                conn.execute(insertQuery)
                print(insertQuery)
    db.commit()
except Exception as e:
    db.rollback()
    print(e)
    print(traceback.print_exc())



