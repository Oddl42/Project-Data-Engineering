#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 14 22:59:12 2025

@author: willket
"""
import os
import schedule
import time
from polygon import RESTClient
from datetime import datetime, timedelta
import pymongo


def get_time_setting():
    """
    Retrieve the time setting from MongoDB and return it as an interval and time unit.

    Returns:
        tuple: (time_factor, time_frame) or (None, None) if no valid setting is found.
    """
    try:
        with pymongo.MongoClient('mongodb://localhost:27017/') as client:
            db = client["stockDB"]
            collection = db["settings"]

            # Retrieve time interval setting
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
        print(f"Error retrieving time setting: {e}")
        return None, None


def get_current_and_past_timestamps():
    """
    Calculate current and past timestamps based on the time setting.

    Returns:
        dict: A dictionary with current and past timestamps.
    """
    try:
        time_factor, time_frame = get_time_setting()
        if not time_factor or not time_frame:
            raise ValueError("Invalid time setting")

        # Current date and time (UTC)
        current_datetime = datetime.utcnow() - timedelta(days=1)
        start_time = current_datetime.replace(hour=15, minute=30, second=0)

        # Calculate time range based on the time unit
        if time_frame == "minute":
            past_datetime = start_time - timedelta(minutes=50000 * 2.0)
        elif time_frame == "hour":
            past_datetime = start_time - timedelta(hours=50000 * 2.0)
        else:
            past_datetime = start_time - timedelta(days=730)  # approx. 2 years

        return {
            "current_datetime_str": current_datetime.strftime('%Y-%m-%d %H:%M:%S'),
            "current_unix_timestamp": int(current_datetime.timestamp()),
            "past_datetime_str": past_datetime.strftime('%Y-%m-%d %H:%M:%S'),
            "past_unix_timestamp": int(past_datetime.timestamp())
        }
    except Exception as e:
        print(f"Error calculating timestamps: {e}")
        return None


def fetch_and_store_stock_data():
    """
    Fetch stock data from Polygon.io and store it in MongoDB.
    Clears the `tickers_data` collection at the start and pauses for 1 minute after every 5 ticker calls.
    """
    try:
        with pymongo.MongoClient("mongodb://localhost:27017/") as clientDB:
            db = clientDB["stockDB"]
            selected_tickers_collection = db["selected_tickers"]
            tickers_data_collection = db["tickers_data"]

            # Clear the tickers_data collection
            tickers_data_collection.delete_many({})
            print("The 'tickers_data' collection has been cleared.")

            # Retrieve time settings and timestamps
            time_factor, time_frame = get_time_setting()
            if not time_factor or not time_frame:
                print("Invalid time setting. Aborting.")
                return

            timestamps = get_current_and_past_timestamps()
            if not timestamps:
                print("Error retrieving timestamps. Aborting.")
                return

            current_unix_timestamp = timestamps["current_unix_timestamp"]
            past_unix_timestamp = timestamps["past_unix_timestamp"]

            # Polygon.io Client
            api_key = os.getenv("POLYGON_API_KEY")
            if not api_key:
                print("Polygon.io API key is not set. Aborting.")
                return

            client = RESTClient(api_key)

            # Fetch data for each ticker
            tickers = selected_tickers_collection.find()
            ticker_count = 0  # Counter for ticker calls

            for ticker in tickers:
                symbol = ticker.get("symbol")
                if not symbol:
                    continue  # Skip tickers without a symbol

                print(f"Fetching data for {symbol}...")
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
                        # Convert the Agg object into a dictionary
                        agg_dict = {
                            "open": agg.open,
                            "high": agg.high,
                            "low": agg.low,
                            "close": agg.close,
                            "volume": agg.volume,
                            "vwap": agg.vwap,
                            "timestamp": agg.timestamp,
                            "transactions": agg.transactions,
                            "otc": agg.otc,
                        }
                        aggs.append(agg_dict)

                    # Store collected data in MongoDB
                    if aggs:
                        tickers_data_collection.insert_one({
                            "symbol": symbol,
                            "data": aggs,
                            "retrieved_at": datetime.utcnow()
                        })
                        print(f"Data for {symbol} successfully saved.")

                    # Increase ticker call counter
                    ticker_count += 1

                    # Pause for 1 minute after every 5 ticker calls
                    if ticker_count % 5 == 0:
                        print(f"Pausing for 1 minute after {ticker_count} ticker calls...")
                        time.sleep(60)

                except Exception as e:
                    print(f"Error fetching data for {symbol}: {e}")
    except Exception as e:
        print(f"Error fetching and storing stock data: {e}")


if __name__ == "__main__":
    # Scheduler einrichten
    print("Scheduler läuft. Drücke STRG+C, um das Programm zu beenden.")
    print("Starte Datenabruf...")
    schedule.every(1).minutes.do(fetch_and_store_stock_data)
    print("Prozess abgeschlossen.")
    while True:
        schedule.run_pending()
        time.sleep(1)