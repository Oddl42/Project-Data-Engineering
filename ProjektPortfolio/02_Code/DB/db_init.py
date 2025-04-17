#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  4 23:03:08 2025

@author: willket
"""

from pymongo import MongoClient

# MongoD-Connection-URI (local instance)
uri = "mongodb://127.0.0.1:27017"
        
        
# initialize DB
def initialize_database():
    client = MongoClient(uri)
    print("Verbindung zur MongoDB hergestellt!")

    # Datenbank und Sammlung auswählen
    database = client["stockDB"]
    
    if "tickers" in database.list_collection_names():
        database["tickers"].drop()
        print(f"Collection tickers wurde gelöscht.")
    
    collection = database["tickers"]

    # Beispiel-Daten für Börsenticker
    tickers = [
        {"symbol": "AAPL", "name": "Apple Inc.", "market": "NASDAQ"},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "market": "NASDAQ"},
        {"symbol": "AMZN", "name": "Amazon.com Inc.", "market": "NASDAQ"},
        {"symbol": "TSLA", "name": "Tesla Inc.", "market": "NASDAQ"},
        {"symbol": "MSFT", "name": "Microsoft Corporation", "market": "NASDAQ"},
        {"symbol": "KLAC", "name": "KLA Corporation", "market": "NASDAQ"},
        {"symbol": "AMD", "name": "Advanced Micro Devices Inc", "market": "NASDAQ"},
        {"symbol": "OKTA", "name": "Okta Inc", "market": "NASDAQ"},
        {"symbol": "CTHR", "name": "Charter Communications, Inc.", "market": "NASDAQ"},
        {"symbol": "NEM", "name": "Newmont Corporations, Inc.", "market": "NASDAQ"}
    ]

    # Daten in die Sammlung einfügen
    result = collection.insert_many(tickers)
    print(f"{len(result.inserted_ids)} Börsenticker wurden erfolgreich eingefügt!")

    # Verbindung schließen
    client.close()
    print("Verbindung zur MongoDB geschlossen.")

# Skript ausführen
if __name__ == "__main__":
    initialize_database()