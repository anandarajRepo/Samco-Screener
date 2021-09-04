# Steps to execute
1. Run TokenGenerator.py to get the new Samco token
2. Run Screener/DB.py to update all the instruments and their respective details to DB. Data will be pushed to instruments table in DB.
(Run this python file if required, which means run this file if their is new instrument needs to be added in DB)
3. Run Screener/EODDataUpdate.py to update the EOD data of instrument
4. Finally, run Screener/app.py in terminal ex: path to file>python app.py. localhost server will be generated and click on the link to see the screener.
5. Use the filer option in app.py code to customize the screener.

