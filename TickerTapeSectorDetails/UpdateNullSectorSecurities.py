import json

###########
# File Path
###########
sectorDetailsForNullStocksFilePath = "Resources/StockNeedsSectorDetailsAfterSelenium.json"
equityFilePath = "Output/EQUITY_L.json"

# read the data from a json file
with open(sectorDetailsForNullStocksFilePath, 'r') as infile:
    sectorDetailsForNullStocks = json.load(infile)

# read the data from a json file
with open(equityFilePath, 'r') as infile:
    nse_companies = json.load(infile)

for sectorDetailsForNullStock in sectorDetailsForNullStocks:
    for nse_Company in nse_companies:
        if (sectorDetailsForNullStock["SYMBOL"] == nse_Company["SYMBOL"]):
        # and (nse_Company["SECTOR"] == None or nse_Company["SUBSECTOR"] == None):
            nse_Company["SECTOR"] = sectorDetailsForNullStock["SECTOR"]
            nse_Company["SUBSECTOR"] = sectorDetailsForNullStock["SUBSECTOR"]

# Dumping updated TickerTape sector to json file
with open(equityFilePath, "w") as jsonFile:
    jsonFile.write(json.dumps(nse_companies, indent=4))



