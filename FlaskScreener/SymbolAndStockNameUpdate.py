### Uncomment the udpate query to make changes in DB

import csv
import traceback
import psycopg2

from configparser import ConfigParser
from psycopg2.extras import RealDictCursor
from pprint import pprint

### File Path
symbolChangeFilePath = 'Resources/symbolchange.csv'
nameChangeFilePath = 'Resources/namechange.csv'

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

#####################
### Symbol Change ###
#####################

### Open changed symbol CSV file and save in dict obj
try:
    symbolChange_dict = {}
    with open(symbolChangeFilePath, newline='') as f:
        ereader = csv.DictReader(f)
        for row in ereader:
            symbolChange_dict[row['SM_KEY_SYMBOL'].strip()] = row['SM_NEW_SYMBOL'].strip()
except FileNotFoundError as error:
    print("CSV file not found error: ", error)

# pprint(symbolChange_dict)

### Insert new instrument to DB and update the sector & sub-sector details
try:
    conn = db.cursor(cursor_factory=RealDictCursor)
    conn.execute("""SELECT symbol FROM instruments""")
    records = conn.fetchall()

    for record in records:
        if record['symbol'].strip() in symbolChange_dict:
            if record['symbol'].strip() != symbolChange_dict[record['symbol']]:
                print(record['symbol'], symbolChange_dict[record['symbol']])
                # conn.execute("""UPDATE instruments SET symbol = '{0}' WHERE symbol = '{1}'""".format(symbolChange_dict[record['symbol']], record['symbol']))

    db.commit()
except Exception as e:
    db.rollback()
    print(e)
    print(traceback.print_exc())

###################
### Name Change ###
###################

### Open changed stock name CSV file and save in dict obj
try:
    stockNameChange_dict = {}
    with open(nameChangeFilePath, newline='') as f:
        ereader = csv.DictReader(f)
        for row in ereader:
            stockNameChange_dict[row['NCH_PREV_NAME'].strip()] = row['NCH_NEW_NAME'].strip()
except FileNotFoundError as error:
    print("CSV file not found error: ", error)

# pprint(stockNameChange_dict)

### Insert new instrument to DB and update the sector & sub-sector details
try:
    conn = db.cursor(cursor_factory=RealDictCursor)
    conn.execute("""SELECT nameofcompany FROM instruments""")
    records = conn.fetchall()

    for record in records:
        if record['nameofcompany'].strip() in stockNameChange_dict:
            if record['nameofcompany'].strip() != stockNameChange_dict[record['nameofcompany']]:
                print(record['nameofcompany'], stockNameChange_dict[record['nameofcompany']])
                # conn.execute("""UPDATE instruments SET nameofcompany = '{0}' WHERE nameofcompany = '{1}'""".format(stockNameChange_dict[record['nameofcompany']], record['nameofcompany']))

    db.commit()
except Exception as e:
    db.rollback()
    print(e)
    print(traceback.print_exc())




