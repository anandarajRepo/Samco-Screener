# Steps to execute Flask Screener
1. Run TokenGenerator.py to get the new Samco token
2. Run FlaskScreener/DB.py to update all the instruments and their respective details to DB. Data will be pushed to instruments table in DB.
(Run this python file if required, which means run this file if their is new instrument needs to be added in DB)
3. Run FlaskScreener/EODDataUpdate.py to update the EOD data of instrument
4. Finally, run FlaskScreener/DailyPerformance.py in terminal ex: path to file>python app.py. localhost server will be generated and click on the link to see the screener.

# Steps for updating new securities sector details 
1. Move the existing Equity_L.csv to Resources/OldEquityList folder.
2. Download the Equity_L.csv file from https://www.nseindia.com/market-data/securities-available-for-trading and choose Securites available for Equity segment (.csv) file to download.
3. After downloaded place it in Resources folder.
4. Next run the CompareCSVFiles.py which will compare the old list of securities with new one and generate the difference in EQUITY_L_DIFF_OLDVSNEW.csv file.
5. If new securities/stocks gets listed then run the GetNullSectorSecurities.py file. This will generate the StockNeedSectorDetails.json file in the Output folder.
6. Copy the StockNeedSectorDetails.json file to TradingviewTickertapeScrapper\src\main\resources folder and run the TradingviewTickertapeScrapper\src\main\java\tickertape\IndustryScrapper.java file which will generate the StockNeedsSectorDetailsAfterSelenium.json file with sector details filled if available.
7. Now, Copy that StockNeedsSectorDetailsAfterSelenium.json file to Resources folder of this project. Finally, run the UpdateNullSectorSecurities.py file under TickerTapeSectorDetails folder which will upadate the securities sector detials in Equity_L.json file in Output folder.

Pending work --> After StockNeedsSectorDetailsAfterSelenium.json generated I need to update the files under TickerTapeSectorDetails/TickerTape folder. Instead, I directly udpated the Equity_L.json file by running the UpdateNullSectorSecurities.py file for now

# Steps for updating changed stock name and symbol by SEBI
