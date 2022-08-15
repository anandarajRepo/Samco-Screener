from pprint import pprint

oldCSVFilePath = "Resources\OldEquityList\EQUITY_L.csv"
newCSVFilePath = "Resources\EQUITY_L.csv"

with open(oldCSVFilePath, 'r') as oldcsv, open(newCSVFilePath, 'r') as newcsv:  # Import CSV files
    oldcsvimport = oldcsv.readlines()
    newcsvimport = newcsv.readlines()

with open('Output\EQUITY_L_DIFF_OLDVSNEW.csv', 'w') as outFile:
    for row in newcsvimport:
        if row not in oldcsvimport:
            outFile.write(row)
