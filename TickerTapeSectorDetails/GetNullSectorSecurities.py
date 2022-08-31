import json

from pprint import pprint

###########
# File Path
###########
jsonFilePath = 'Output/EQUITY_L.json'
jsonFilePathOfNullSectorStocks = 'Output/StockNeedSectorDetails.json'

stockWithNullSectorArr = []
stockWithNullSectorJson = {}

# read the data from a json file
with open(jsonFilePath, 'r') as infile:
    nse_companies = json.load(infile)

try:
    for nse_company in nse_companies:
        if nse_company["SECTOR"] == None or nse_company["SUBSECTOR"] == None:
            stockWithNullSectorJson["SYMBOL"] = nse_company["SYMBOL"]
            stockWithNullSectorJson["NAMEOFCOMPANY"] = nse_company["NAMEOFCOMPANY"]
            stockWithNullSectorJson["SECTOR"] = nse_company["SECTOR"]
            stockWithNullSectorJson["SUBSECTOR"] = nse_company["SUBSECTOR"]
            stockWithNullSectorArr.append(stockWithNullSectorJson)
except Exception as e:
    print(e)

pprint(stockWithNullSectorArr)

# Writing to json file
with open(jsonFilePathOfNullSectorStocks, "w") as outfile:
    outfile.write(json.dumps(stockWithNullSectorArr, indent=4))