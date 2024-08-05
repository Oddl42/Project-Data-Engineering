# -*- coding: utf-8 -*-
"""
Created on Tue Jul 30 16:59:52 2024

@author: timwi
"""

import pandas as pd
import json as js
import requests



# Funktion zum Abrufen der Aktiendaten
def get_stock_data(symbol, time_frame):
    # API-Schlüssel für Alpha Vantage
    api_key = "2SU00J0HO2G4RLHA"
    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol='+ symbol + '&interval=' + time_frame + '&apikey=' + api_key
    return requests.get(url)

# Eingaben für Time-Frame und Stocks:1min, 5min, 15min, 30min, 60min
time_frame =  '5min'
#stocks = input('Geben Sie die Aktien ein, getrennt durch Kommas: ').split(',')
stocks = ['BORR', 'NKE', 'SMLR', 'ZIP', 'LC', 'POWL', 'AMD']

# Daten für jede Aktie abrufen und in CSV-Datei speichern
for stock in stocks:
    data = get_stock_data(stock, time_frame)
    #data.to_csv(f'{stock}_data.csv', index=False)
    
    datajson = data.json()
    
    with open(stock + '.json', 'w') as fp:
        js.dump(datajson, fp)