import os
import csv
import shutil
import pandas as pd

from pprint import pprint

###########
# File Path
###########
pathForTickerTapeSector = "TickerTapeSectorDetails/TickerTape/"
symbolChangeFilePath = 'Resources/symbolchange.csv'
stockNameChangeFilePath = 'Resources/namechange.csv'

### Read all files from directory
files = os.listdir(pathForTickerTapeSector)

#####################
### Symbol Change ###
#####################

print("***Stock Symbol Change***")

### Open changed stock symbol CSV file and save in dict obj
try:
    symbolChange_dict = {}
    with open(symbolChangeFilePath, newline='') as f:
        ereader = csv.DictReader(f)
        for row in ereader:
            symbolChange_dict[row['SM_KEY_SYMBOL'].strip()] = row['SM_NEW_SYMBOL'].strip()
except FileNotFoundError as error:
    print("CSV file not found error: ", error)


### Creating new temp CSV file with new symbol change and replacing the existing CSV file
for csvFile in files:
    csvFile = pathForTickerTapeSector + csvFile
    with open(csvFile, 'r', encoding='cp1252') as fread, open('tempcsv.csv', 'w') as ftemp:
        csvReader = csv.DictReader(fread)
        csvWriter = csv.DictWriter(ftemp,
                        delimiter=",",
                        lineterminator="\n",
                        fieldnames=['Name', 'Ticker', 'Sub-Sector'])
        csvWriter.writeheader()
        for csvRow in csvReader:
            if csvRow['Ticker'] in symbolChange_dict \
                and csvRow['Ticker'].strip() != symbolChange_dict[csvRow['Ticker'].strip()]:
                    print(csvFile, csvRow['Ticker'].strip(), symbolChange_dict[csvRow['Ticker'].strip()], sep="---")
                    row = {'Name': csvRow['Name'],
                            'Ticker': symbolChange_dict[csvRow['Ticker'].strip()],
                            'Sub-Sector': csvRow['Sub-Sector']}
                    csvWriter.writerow(row)
            else:
                row = {'Name': csvRow['Name'],
                        'Ticker': csvRow['Ticker'],
                        'Sub-Sector': csvRow['Sub-Sector']}
                csvWriter.writerow(row)
    shutil.move('tempcsv.csv', csvFile)

###################
### Name Change ###
###################

print("***Stock Name Change***")

### Open changed stock name CSV file and save in dict obj
try:
    nameChange_dict = {}
    with open(stockNameChangeFilePath, newline='') as f:
        ereader = csv.DictReader(f)
        for row in ereader:
            nameChange_dict[row['NCH_SYMBOL'].strip()] = row['NCH_NEW_NAME'].strip()
except FileNotFoundError as error:
    print("CSV file not found error: ", error)


### Creating new temp CSV file with new stock name change and replacing the existing CSV file
for csvFile in files:
    csvFile = pathForTickerTapeSector + csvFile
    with open(csvFile, 'r', encoding='cp1252') as fread, open('tempcsv.csv', 'w') as ftemp:
        csvReader = csv.DictReader(fread)
        csvWriter = csv.DictWriter(ftemp,
                        delimiter=",",
                        lineterminator="\n",
                        fieldnames=['Name', 'Ticker', 'Sub-Sector'])
        csvWriter.writeheader()
        for csvRow in csvReader:
            if csvRow['Ticker'] in nameChange_dict \
                and csvRow['Name'].strip().lower() != nameChange_dict[csvRow['Ticker'].strip()].lower():
                    print(csvFile, csvRow['Ticker'], csvRow['Name'].strip(), nameChange_dict[csvRow['Ticker'].strip()], sep="---")
                    row = {'Name': nameChange_dict[csvRow['Ticker'].strip()],
                            'Ticker': csvRow['Ticker'],
                            'Sub-Sector': csvRow['Sub-Sector']}
                    csvWriter.writerow(row)
            else:
                row = {'Name': csvRow['Name'],
                        'Ticker': csvRow['Ticker'],
                        'Sub-Sector': csvRow['Sub-Sector']}
                csvWriter.writerow(row)
    shutil.move('tempcsv.csv', csvFile)



