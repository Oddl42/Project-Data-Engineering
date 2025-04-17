#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  8 15:04:12 2025

@author: willket
"""

from polygon import RESTClient
import datetime

client = RESTClient(api_key="TODO")

aggs = client.get_aggs(
    "AAPL",
    1,
    "day",
    "2024-12-01",
    "2025-04-07",
)
print(aggs)

startime = aggs[0].timestamp / 1000
startdatum = datetime.datetime.utcfromtimestamp(startime)
print(startdatum.strftime('%Y-%m-%d %H:%M:%S'))