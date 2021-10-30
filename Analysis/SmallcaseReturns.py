import csv
import calendar
import datetime
import pandas as pd

from datetime import timedelta
from pprint import pprint

###### Options to display complete set of data frame in console
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)


###### Open the CSV file
file = open("..\Resources\SCET_0005_Historical.csv")


###### Use the csv.reader object to read the CSV file
csvreader = csv.reader(file)


###### Extract the field names
header = []
header = next(csvreader)
# pprint(header)


###### Extract CSV data and append in rowRef list
smallcaseCSV = list(csvreader)
firstDate = smallcaseCSV[0][0]
prevMonthOrYear = datetime.datetime.strptime(firstDate, '%d-%m-%Y').month

rowRef = []
for row in smallcaseCSV:
    date_time_obj = datetime.datetime.strptime(row[0], '%d-%m-%Y')
    monthOrYear = date_time_obj.month
    if prevMonthOrYear != monthOrYear:
        rowRef.append(row)
        prevMonthOrYear = monthOrYear


###### Create a empty dataframe
data = {'From Date': [],
        'To Date': [],
        'Returns': []
        }
df_smallcase = pd.DataFrame(data)


###### Use the rowRef list to calculate the returns
prevRow = []
for row in rowRef:
    prevRow.append(row)
    if len(prevRow) > 1:
        fromDate = prevRow[len(prevRow) - 2][0]
        toDate = row[0]
        monthlyReturns = round((((float(row[1]) - float(prevRow[len(prevRow) - 2][1])) * 100) / float(prevRow[len(prevRow) - 2][1])), 2)
        new_row = {'From Date': fromDate, 'To Date': toDate, 'Returns': monthlyReturns}
        df_smallcase = df_smallcase.append(new_row, ignore_index=True)

print(df_smallcase)


### Get the date of fist & last of the month for the given year
# allWeatherDates = []
#
# year = 2007
# month = 1
# for x in range(15):
#     for y in range(12):
#         dateRange = calendar.monthrange(year + x, month + y)
#         # print(dateRange)
#         # print(f"Year==%s, Month==%s, Day==%s" % (year + x, month + y, 1))
#         # print(f"Year==%s, Month==%s, Day==%s" % (year + x, month + y, dateRange[1]))
#
#         startDate = datetime.date(year + x, month + y, 1)
#         endDate = datetime.date(year + x, month + y, dateRange[1])
#
#         if startDate.weekday() == 5:
#             startDate = startDate - timedelta(days=1)
#
#         if startDate.weekday() == 6:
#             startDate = startDate - timedelta(days=2)
#
#         if endDate.weekday() == 5:
#             endDate = endDate - timedelta(days=1)
#
#         if endDate.weekday() == 6:
#             endDate = endDate - timedelta(days=2)
#
#         # print(startDate)
#         # print(endDate)
#
#         allWeatherDates.append(startDate)
#         allWeatherDates.append(endDate)
#         if month == 12:
#             month = 1

# pprint(allWeatherDates)

### Extract the rows/records
# startNav = None
# endNav = None
# loopCount = 1
# prevRow = None
# dateFoundFlag = None
#
# for row in csvreader:
#     for allWeatherDate in allWeatherDates:
#         date_time_obj = datetime.datetime.strptime(row[0], '%d-%m-%Y')
#         if allWeatherDate == date_time_obj.date():
#             print(row)
#             dateFoundFlag = True
#             prevRow = row
#             if loopCount == 1:
#                 startNav = float(row[1])
#             if loopCount == 2:
#                 endNav = float(row[1])
#                 loopCount = 0
#                 print(endNav - startNav)
#             loopCount += 1


