#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  8 22:51:19 2025

@author: willket
"""

from polygon import RESTClient
from datetime import datetime, timedelta
import pymongo


def get_time_setting():
    """
    Ruft die Zeiteinstellung aus der MongoDB ab und gibt diese als Intervall und Zeiteinheit zurück.

    Returns:
        tuple: (Zeitfaktor, Zeiteinheit) oder (None, None), falls keine gültige Einstellung gefunden wird.
    """
    try:
        # Verbindung zur MongoDB
        client = pymongo.MongoClient('mongodb://localhost:27017/')
        db = client["stockDB"]
        collection = db["settings"]

        # Einstellung für das Zeitintervall abrufen
        document = collection.find_one({"setting": "time_interval"})
        if document:
            interval = document.get("value")
            time_mapping = {
                "1m": (1, "minute"),
                "5m": (5, "minute"),
                "10m": (10, "minute"),
                "15m": (15, "minute"),
                "30m": (30, "minute"),
                "1h": (1, "hour"),
                "4h": (4, "hour"),
                "T": (1, "day"),
                "W": (1, "week"),
                "M": (1, "month"),
            }
            return time_mapping.get(interval, (None, None))
        return None, None
    except Exception as e:
        print(f"Fehler beim Abrufen der Zeiteinstellung: {e}")
        return None, None
    finally:
        client.close()


def get_current_and_past_timestamps():
    """
    Berechnet die aktuellen und vergangenen Zeitstempel basierend auf der Zeiteinstellung.

    Returns:
        dict: Ein Dictionary mit den aktuellen und vergangenen Zeitstempeln.
    """
    try:
        time_factor, time_frame = get_time_setting()
        if not time_factor or not time_frame:
            raise ValueError("Ungültige Zeiteinstellung")

        # Aktuelles Datum und Uhrzeit (UTC)
        current_datetime = datetime.utcnow() - timedelta(days=1)
        start_time = current_datetime.replace(hour=15, minute=30, second=0)

        # Berechnung des Zeitraums basierend auf der Zeiteinheit
        if time_frame == "minute":
            past_datetime = start_time - timedelta(minutes=50000 * 2.9)
        elif time_frame == "hour":
            past_datetime = start_time - timedelta(hours=50000 * 2.9)
        else:
            past_datetime = start_time - timedelta(days=730)  # ca. 2 Jahre

        # Formatierung und Unix-Timestamps
        current_datetime_str = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
        past_datetime_str = past_datetime.strftime('%Y-%m-%d %H:%M:%S')

        return {
            "current_datetime_str": current_datetime_str,
            "current_unix_timestamp": int(current_datetime.timestamp()),
            "past_datetime_str": past_datetime_str,
            "past_unix_timestamp": int(past_datetime.timestamp())
        }
    except Exception as e:
        print(f"Fehler bei der Berechnung der Zeitstempel: {e}")
        return None


def fetch_and_store_stock_data():
    """
    Ruft Börsendaten von Polygon.io ab und speichert sie in der MongoDB.
    """
    try:
        # MongoDB-Verbindung
        clientDB = pymongo.MongoClient("mongodb://localhost:27017/")
        db = clientDB["stockDB"]
        selected_tickers_collection = db["selected_tickers"]
        tickers_data_collection = db["tickers_data"]

        # Zeiteinstellungen und Zeitstempel abrufen
        time_factor, time_frame = get_time_setting()
        if not time_factor or not time_frame:
            print("Ungültige Zeiteinstellung. Abbruch.")
            return

        timestamps = get_current_and_past_timestamps()
        if not timestamps:
            print("Fehler beim Abrufen der Zeitstempel. Abbruch.")
            return

        current_unix_timestamp = timestamps["current_unix_timestamp"]
        past_unix_timestamp = timestamps["past_unix_timestamp"]

        # Polygon.io-Client
        client = RESTClient("TODO")

        # Ticker-Daten abrufen
        tickers = selected_tickers_collection.find()
        for ticker in tickers:
            symbol = ticker.get("symbol")
            if not symbol:
                continue  # Überspringe Ticker ohne Symbol

            print(f"Rufe Daten für {symbol} ab...")
            try:
                aggs = []
                for agg in client.list_aggs(
                    ticker=symbol,
                    multiplier=time_factor,
                    timespan=time_frame,
                    from_=past_unix_timestamp,
                    to=current_unix_timestamp,
                    adjusted=True,
                    sort="desc",
                    limit=50000,
                ):
                    aggs.append(agg)

                # Gesammelte Daten in die MongoDB speichern
                if aggs:
                    tickers_data_collection.insert_one({
                        "symbol": symbol,
                        "data": aggs,
                        "retrieved_at": datetime.utcnow()
                    })
                    print(f"Daten für {symbol} erfolgreich gespeichert.")
            except Exception as e:
                print(f"Fehler beim Abrufen der Daten für {symbol}: {e}")
    except Exception as e:
        print(f"Fehler beim Abrufen und Speichern von Börsendaten: {e}")
    finally:
        clientDB.close()


if __name__ == "__main__":
    print("Starte Datenabruf...")
    fetch_and_store_stock_data()
    print("Prozess abgeschlossen.")
    