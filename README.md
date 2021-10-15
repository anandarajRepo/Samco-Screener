# Steps to execute Flask Screener
1. Run TokenGenerator.py to get the new Samco token
2. Run FlaskScreener/DB.py to update all the instruments and their respective details to DB. Data will be pushed to instruments table in DB.
(Run this python file if required, which means run this file if their is new instrument needs to be added in DB)
3. Run FlaskScreener/EODDataUpdate.py to update the EOD data of instrument
4. Finally, run FlaskScreener/DailyPerformance.py in terminal ex: path to file>python app.py. localhost server will be generated and click on the link to see the screener.

