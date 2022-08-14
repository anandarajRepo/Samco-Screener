import os
from pprint import pprint
import csv
import json

###########
# File Path
###########
pathForTickerTapeSector = "TickerTape/"
csvFilePath = 'Resources/EQUITY_L.csv'
jsonFilePath = 'Output/EQUITY_L.json'

# Read all files from directory
files = os.listdir(pathForTickerTapeSector)

##########################################################################
# Getting all Sector and Sub-Sector Name's and saving it in a dictionary #
##########################################################################
sector = {}

for csvFile in files:
    csvFile = pathForTickerTapeSector + csvFile
    index_name = csvFile.replace(".csv", "").replace("TickerTape/", "")
    sector[index_name] = []
    with open(csvFile) as csvFile:
        csvReader = csv.DictReader(csvFile)
        for csvRow in csvReader:
            # subSector = {}
            listTemp = []
            for key, value in csvRow.items():
                if key == "Ticker":
                    listTemp.append(value)
                elif key == "Sub-Sector":
                    listTemp.append(value)
            sector[index_name].append({listTemp[0]:listTemp[1]})

# pprint(sector)

############################################################
# Open List of securities (CSV file) and adding TickerTape #
# Sector & Sub-Sector to EQUITY_L.json file ################
############################################################
stockList = []

# read the from CSV and convert it to List
with open(csvFilePath) as csvFile:
    csvReader = csv.DictReader(csvFile)
    for csvRow in csvReader:
        stockList.append(csvRow)

# write the data to a json file
with open(jsonFilePath, "w") as jsonFile:
    jsonFile.write(json.dumps(stockList, indent=4))

# read the data from a json file
with open(jsonFilePath, 'r') as infile:
    nse_companies = json.load(infile)

# Iterate json stock list
for nse_company in nse_companies:
    try:
        for parentSector, subSectorList in sector.items():
            for subSectorDict in subSectorList:
                for symbol, subSectorName in subSectorDict.items():
                    if nse_company['SYMBOL'].strip() == symbol.strip():
                        nse_company['SECTOR'] = parentSector
                        nse_company['SUBSECTOR'] = subSectorName
    except Exception as e:
        print(e)

# Dumping updated TickerTape sector to json file
with open(jsonFilePath, "w") as jsonFile:
    jsonFile.write(json.dumps(nse_companies, indent=4))

pprint(nse_companies)