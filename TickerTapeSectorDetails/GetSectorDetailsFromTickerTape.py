# import requests
# import pandas as pd
# from pprint import pprint

# other_data = {}
# results = []
# stock_list = ['ION Exchange']

# with requests.Session() as s:
#     for ticker in stock_list:
#         try:
#             r = s.get(f'https://api.tickertape.in/search?text={ticker.lower}&types=stock,brands,index,etf,mutualfund').json()
#             pprint(r)
#             stock_id = r['data']['stocks'][0]['sid']
#             name = r['data']['stocks'][0]['name']
#             other_data[stock_id] = r

#             r = s.get(f'https://api.tickertape.in/stocks/investmentChecklists/{stock_id}?type=basic').json()
#             d = {i['title']: i['description'] for i in r['data']}
#             d = {**{'Security': name}, **other_data[stock_id]['data']['stocks'][0]['quote'], **{'marketCap': other_data[stock_id]['data']['stocks'][0]['marketCap']},  **d}
#             results.append(d)
#         except Exception as e:
#             print(ticker, e)

# df = pd.DataFrame(results)
# print(df)