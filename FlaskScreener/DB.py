import psycopg2
import json

from configparser import ConfigParser

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

### Insert instrument to DB
try:
    conn = db.cursor()

    for nse_company in nse_companies:
        if "SECTOR" in nse_company and "SUBSECTOR" in nse_company:
            conn.execute("""INSERT INTO instruments (symbol, nameofcompany, series, dateoflistings, paidvalue, marketlot, isinnumber, facevalue, sector, subsector) VALUES ( '{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}', '{8}', '{9}')""".format(nse_company['SYMBOL'],
                                                                                                                     nse_company['NAMEOFCOMPANY'].replace("'", ""),
                                                                                                                     nse_company['ISINNUMBER'],
                                                                                                                     nse_company['DATEOFLISTING'],
                                                                                                                     nse_company['PAIDUPVALUE'],
                                                                                                                     nse_company['MARKETLOT'],
                                                                                                                     nse_company['ISINNUMBER'],
                                                                                                                     nse_company['FACEVALUE'],
                                                                                                                     nse_company['SECTOR'],
                                                                                                                     nse_company['SUBSECTOR']))
    db.commit()
except Exception as e:
    db.rollback()
    print(e)
