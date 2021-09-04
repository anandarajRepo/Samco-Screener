import json
from pprint import pprint
from pandas import ExcelWriter
import pandas as pd

###########
# File Path
###########

equity_l_csv = "Output/EQUITY_L.json"
xlsxFileClassified = 'Output/EQUITY_L_TICKERTAPE_CLASSIFIED.xlsx'
jsonIndicies = "Output/JSON_INDICIES_TICKERTAPE.json"

######################################
# populating the json values to xlsx #
######################################

with open(equity_l_csv) as f:
    equity_l_json = json.load(f)

# Fetch the distinct sectors from EQUITY_L.json
sector_unique_list = []

for equity_l_item in equity_l_json:
    for key, value in equity_l_item.items():
        if key == "SECTOR":
            if not sector_unique_list:
                sector_unique_list.append(value)
            elif value not in sector_unique_list:
                sector_unique_list.append(value)

with open(jsonIndicies, "r") as infile:
    json_indices = json.load(infile)

list_dfs = {}
for sector in sector_unique_list:
    df = pd.DataFrame(json_indices[sector])

    # Removing/Changing column order
    # df = df[['SYMBOL', 'NAMEOFCOMPANY', 'SUBSECTOR']]
    df = df.drop(["SERIES", "DATEOFLISTING", "PAIDUPVALUE", "MARKETLOT", "ISINNUMBER", "FACEVALUE"], axis=1)

    list_dfs[sector] = df

print("Excel generated successfully")

def save_xls(list_dfs, xls_path):
    with ExcelWriter(xls_path) as writer:
        for sheetname, df in list_dfs.items():
            df.to_excel(writer, sheetname, index=False)
            worksheet = writer.sheets[sheetname]  # pull worksheet object
            for idx, col in enumerate(df):  # loop through all columns
                series = df[col]
                max_len = max((
                    series.astype(str).map(str_len).max(),  # len of largest item
                    str_len(str(series.name))  # len of column name/header
                )) + 2  # adding a little extra space
                worksheet.set_column(idx, idx, max_len)  # set column width and this method is deprecated and not working

        writer.save()


def str_len(str):
    try:
        row_l = len(str)
        utf8_l = len(str.encode('utf-8'))
        return (utf8_l - row_l) / 2 + row_l
    except:
        return None


save_xls(list_dfs, xlsxFileClassified)