#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 14 22:59:12 2025

@author: willket
"""
import os
import json
from datetime import datetime, timedelta
from polygon import RESTClient
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, FloatType, IntegerType, TimestampType
import pymongo
import time


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


def fetch_stock_data():
    """
    Fetch stock data from the Polygon.io API.

    Returns:
        list: A list of dictionaries containing stock data for all selected tickers.
    """
    try:
        # MongoDB connection to retrieve selected tickers
        with pymongo.MongoClient("mongodb://localhost:27017/") as clientDB:
            db = clientDB["stockDB"]
            selected_tickers_collection = db["selected_tickers"]
            tickers = selected_tickers_collection.find()

            # Retrieve time settings
            time_factor, time_frame = get_time_setting()
            if not time_factor or not time_frame:
                print("Invalid time setting. Aborting.")
                return []

            timestamps = get_current_and_past_timestamps()
            if not timestamps:
                print("Error retrieving timestamps. Aborting.")
                return []

            current_unix_timestamp = timestamps["current_unix_timestamp"]
            past_unix_timestamp = timestamps["past_unix_timestamp"]

            # Polygon.io API client
            api_key = os.getenv("POLYGON_API_KEY")
            if not api_key:
                print("Polygon.io API key is not set. Aborting.")
                return []

            client = RESTClient(api_key)

            # Fetch data for each ticker
            stock_data = []
            for ticker in tickers:
                symbol = ticker.get("symbol")
                if not symbol:
                    continue

                print(f"Fetching data for {symbol}...")
                try:
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
                        stock_data.append({
                            "symbol": symbol,
                            "timestamp": datetime.utcfromtimestamp(agg.timestamp / 1000),  # Convert to datetime
                            "open": float(agg.open),  # Convert to float
                            "high": float(agg.high),  # Convert to float
                            "low": float(agg.low),    # Convert to float
                            "close": float(agg.close),  # Convert to float
                            "volume": float(agg.volume),  # Convert to float
                            "vwap": float(agg.vwap),  # Convert to float
                            "transactions": int(agg.transactions),  # Keep as int
                            "retrieved_at": datetime.utcnow()
                        })

                except Exception as e:
                    print(f"Error fetching data for {symbol}: {e}")
            return stock_data
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return []


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


def process_with_spark(stock_data):
    """
    Process stock data using Spark and write it to MongoDB.

    Args:
        stock_data (list): A list of dictionaries containing stock data.
    """
    # Create Spark session
    spark = SparkSession.builder \
        .appName("Stock Data Streaming") \
        .config("spark.mongodb.write.connection.uri", "mongodb://localhost:27017/stockDB.tickers_data") \
        .getOrCreate()

    # Define schema for the incoming data
    schema = StructType([
        StructField("symbol", StringType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("open", FloatType(), True),
        StructField("high", FloatType(), True),
        StructField("low", FloatType(), True),
        StructField("close", FloatType(), True),
        StructField("volume", FloatType(), True),
        StructField("vwap", FloatType(), True),
        StructField("transactions", IntegerType(), True),
        StructField("retrieved_at", TimestampType(), True)
    ])

    # Check if stock data is not empty
    if stock_data:
        # Create a Spark DataFrame
        df = spark.createDataFrame(stock_data, schema=schema)

        # Write the DataFrame to MongoDB
        df.write \
            .format("mongo") \
            .mode("append") \
            .save()

        print("Data successfully written to MongoDB.")
    else:
        print("No stock data to process.")

    # Stop the Spark session
    spark.stop()


if __name__ == "__main__":
    while True:
        # Fetch stock data
        stock_data = fetch_stock_data()

        # Process with Spark
        process_with_spark(stock_data)

        # Wait for the next micro-batch
        time.sleep(60)