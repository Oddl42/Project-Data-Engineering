# -*- coding: utf-8 -*-
"""
Created on Thu Apr  3 12:24:52 2025

@author: timwi
"""

import os
import time
import json
import requests
import findspark
from pyspark import SparkConf, SparkContext
from pyspark.streaming import StreamingContext

# =============================================================================
# Konfigurationen
# =============================================================================

# Alpha Vantage API Key (bitte anpassen)
ALPHA_VANTAGE_API_KEY = "2SU00J0HO2G4RLHA"

# Symbol (Aktie oder Kryptowährung) für die Abfrage, z.B. Microsoft (MSFT)
SYMBOL = "MSFT"

# Abfrageintervall in Sekunden
FETCH_INTERVAL = 120  # z.B. alle 15 Sekunden Alpha Vantage abfragen

# Find Spark
findspark.init()

# =============================================================================
# Funktionen zur Datenabfrage und Vorbereitung
# =============================================================================

def fetch_stock_data(symbol):
    """
    Ruft Echtzeit-Daten (Intraday) von Alpha Vantage ab und gibt das Ergebnis
    als Dictionary zurück.
    Quelle: Alpha Vantage stellt kostenlose API-Endpunkte zur Verfügung [[1]].
    """
    base_url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol,
        "interval": "1min",
        "apikey": ALPHA_VANTAGE_API_KEY,
        "datatype": "json"
    }

    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        # Extrahieren der zuletzt verfügbaren Daten (falls vorhanden)
        time_series = data.get("Time Series (1min)", {})
        if not time_series:
            return None

        # Neuesten Time-Stamp holen
        last_timestamp = sorted(time_series.keys())[-1]
        latest_data = time_series[last_timestamp]

        # Rückgabe eines vereinfachten Datensatzes
        return {
            "symbol": symbol,
            "timestamp": last_timestamp,
            "open": latest_data.get("1. open"),
            "high": latest_data.get("2. high"),
            "low": latest_data.get("3. low"),
            "close": latest_data.get("4. close"),
            "volume": latest_data.get("5. volume")
        }
    except Exception as e:
        print(f"Fehler beim Abfragen der Alpha Vantage API: {e}")
        return None

def rdd_handler(time, rdd):
    """
    Nimmt das RDD des aktuellen Micro-Batch entgegen, transformiert
    und speichert/behandelt die Daten gegebenenfalls weiter.
    """
    records = rdd.collect()
    if records:
        print(f"=== Batch-Zeitstempel: {time} ===")
        for record in records:
            print(record)
            # Hier könnte man Daten in eine Datenbank schreiben,
            # z.B. mit JDBC oder anderen Bibliotheken
            # db_write_function(record)
    else:
        print(f"Keine neuen Daten im Batch um {time}")

# =============================================================================
# Hauptprogramm: Streaming-Kontext erstellen und Daten verarbeiten
# =============================================================================

if __name__ == "__main__":
    # Spark-Konfiguration
    conf = SparkConf().setAppName("AlphaVantageSparkStreaming").setMaster("local[2]")
    sc = SparkContext(conf=conf)
    ssc = StreamingContext(sc, 60)  # Micro-Batch alle 5 Sekunden

    # Erstellen eines DStreams aus einer Queue (simulierte Live-Daten),
    # da Alpha Vantage nicht von sich aus ununterbrochen "pushed" [[4]].
    rdd_queue = [sc.parallelize([])]

    # Initialisiere QueueStream
    input_stream = ssc.queueStream(rdd_queue)
    input_stream.foreachRDD(rdd_handler)

    # Starte einen separaten Thread oder Loop, um kontinuierlich (in Intervallen)
    # neue Daten abzurufen und in die RDD-Queue einzuspeisen
    def fetch_data_loop():
        while True:
            stock_data = fetch_stock_data(SYMBOL)
            if stock_data:
                rdd = sc.parallelize([stock_data])
                rdd_queue.append(rdd)
            # Warte bis zur nächsten Abfrage
            time.sleep(FETCH_INTERVAL)

    # Starte Streaming-Kontext
    try:
        ssc.start()
        # fetch_data_loop() läuft so lange, bis es einen KeyboardInterrupt gibt
        fetch_data_loop()
        ssc.awaitTermination()
    except KeyboardInterrupt:
        print("Beende Streaming...")
        ssc.stop(stopSparkContext=True, stopGraceFully=True)

   