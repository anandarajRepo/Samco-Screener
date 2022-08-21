import json

from pprint import pprint

###########
# File Path
###########
jsonFilePath = 'Output/EQUITY_L.json'

# read the data from a json file
with open(jsonFilePath, 'r') as infile:
    nse_companies = json.load(infile)

try:
    for nse_company in nse_companies:
        if nse_company['SECTOR'] == None or nse_company['SUBSECTOR'] == None:
            pprint(f"{nse_company['SYMBOL']}, {nse_company['NAMEOFCOMPANY']}")
except Exception as e:
    print(e)