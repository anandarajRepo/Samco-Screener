import time
from asyncio.windows_events import NULL
import os
import csv
import json
import yfinance as yf
import requests
from bs4 import BeautifulSoup

from pprint import pprint
from collections import OrderedDict

###########
# File Path
###########
csvFilePath = '../Resources/EQUITY_L.csv'
jsonFilePath = '../Output/EQUITY_L.json'


##########################################################################
# Getting all Sector and Sub-Sector Name's and saving it in a dictionary #
##########################################################################
### Sector details from Yahoo ###
def get_sector_and_industry(stock_symbol):
    stock = yf.Ticker(stock_symbol)
    info = stock.info

    sector = info.get('sector', 'N/A')
    industry = info.get('industry', 'N/A')

    return sector, industry


# Function to get sector details from screener.in
def get_sector_screener_in(symbol):
    url = f"https://www.screener.in/company/{symbol}/consolidated/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    time.sleep(1)
    response = requests.get(url, headers=headers)
    sector = []

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        html_content = response.content
        soup = BeautifulSoup(html_content, 'html.parser')
        section = soup.find('section', {'id': 'peers'})
        paragraph = section.find('p')
        anchors = paragraph.find_all('a')
        for anchor in anchors:
            sector.append(anchor.text.strip())
        return sector
    else:
        print(f"Failed to retrieve the webpage. Status code: {response.status_code}")


# Function to get sector details from FMP
def get_sector_financial_modeling_prep(symbol):
    url = f"https://site.financialmodelingprep.com/financial-summary/{symbol}.NS"
    headers = {'User-Agent': 'Mozilla/5.0'}
    time.sleep(1)
    response = requests.get(url, headers=headers)
    summary = []

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        html_content = response.content
        soup = BeautifulSoup(html_content, 'html.parser')

        div = soup.find('div', {'class': 'global_fccs__H36ba'})
        # wrapper = div.find('div', {'class': 'wrapper'})
        listOfAboutSectionItems = div.find_all('div', {'class': 'global_fcss__ZrDvn'})

        for item in listOfAboutSectionItems:
            h4 = item.find('h4', {'class': 'text_h4__Fs_dF'})
            p = item.find('p', {'class': 'text_p__pUIto'})
            if h4 is not None and h4.text.strip().casefold() == "sector":
                summary.append(p.text.strip())
            elif h4 is not None and h4.text.strip().casefold() == "industry":
                summary.append(p.text.strip())

        div = soup.find('div', {'class': 'SummaryTable_root__kQuSO'})
        listOfSummarySectionItems = div.find_all('div', {'class': 'SummaryTable_col__ZtZNE'})

        for item in listOfSummarySectionItems:
            h4 = item.find('h4', {'class': 'text_h4__Fs_dF'})
            p = item.find('p', {'class': 'text_p__pUIto'})
            if h4 is not None and h4.text.strip().casefold() == "market cap":
                summary.append(p.text.strip())
        return summary[0], summary[1], summary[2]
    else:
        print(f"Failed to retrieve the webpage. Status code: {response.status_code}")


############################################################
# Open List of securities (CSV file) and adding TickerTape #
# Sector & Sub-Sector to EQUITY_L.json file ################
############################################################
stockList = []

# read the instruments from CSV and convert it to List
with open(csvFilePath) as csvFile:
    csvReader = csv.DictReader(csvFile, skipinitialspace=True)
    for csvRow in csvReader:
        od = OrderedDict()
        for k, v in csvRow.items():
            od[k.strip().replace(" ", "")] = v
        stockList.append(od)

# write the data to a json file
with open(jsonFilePath, "w") as jsonFile:
    jsonFile.write(json.dumps(stockList, indent=4))

# read the data from a json file
with open(jsonFilePath, 'r') as infile:
    nse_companies = json.load(infile)

# Making all sector & subsector null before mapping sector details
for nse_company in nse_companies:
    nse_company['SECTOR'] = None
    nse_company['SUBSECTOR'] = None
    nse_company['MARKETCAP'] = None

# Iterate json stock list
# New Code
for nse_company in nse_companies:
    try:
        if nse_company['SYMBOL'].strip() is not None:
            # sector, industry = get_sector_and_industry(nse_company['SYMBOL'].strip() + ".NS")
            # sector, industry = get_sector_screener_in(nse_company['SYMBOL'].strip())
            sector, industry, marketcap = get_sector_financial_modeling_prep(nse_company['SYMBOL'].strip())
            nse_company['SECTOR'] = sector
            nse_company['SUBSECTOR'] = industry
            nse_company['MARKETCAP'] = marketcap
            print(f"SYMBOL : {nse_company['SYMBOL'].strip()}, SECTOR: {sector}, SUBSECTOR: {industry}, MARKETCAP: {marketcap}")
    except Exception as e:
        print(e)

# Dumping updated TickerTape sector to json file
with open(jsonFilePath, "w") as jsonFile:
    jsonFile.write(json.dumps(nse_companies, indent=4))

pprint(nse_companies)
