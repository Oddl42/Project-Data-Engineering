#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  7 11:13:30 2025

@author: willket
"""
import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")  # Passe die URL an, falls nötig
db = client["stockDB"]
selected_tickers_collection = db["selected_tickers"]

all_tickers = selected_tickers_collection.find()

if db["selected_tickers"].count_documents({}) == 0:
    print("Keine Dokumente in der Sammlung gefunden.")
else:    
    for ticker in all_tickers:
        print(ticker['symbol'])