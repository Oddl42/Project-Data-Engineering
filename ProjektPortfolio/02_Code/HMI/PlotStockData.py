#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  8 12:04:34 2025

@author: willket
"""

from pymongo import MongoClient
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

# Verbindung zur MongoDB herstellen
client = MongoClient("mongodb://localhost:27017/")  # Passe die URL an, falls nötig
db = client["stockDB"]
collection = db["tickers_data"]

# Daten aus der Collection abrufen
data = list(collection.find())

# Daten in ein Pandas DataFrame umwandeln
df = pd.DataFrame(data)
#df_AMZN = df.loc[df['ticker'] == 'AMZN']
df_AMZN = df[df['ticker'] == 'AMZN']

# Sicherstellen, dass die Daten korrekt sortiert sind (nach Timestamp)
df_AMZN = df_AMZN.sort_values(by="timestamp")

# Candlestick-Plot erstellen
fig = go.Figure()

9# Candlestick-Daten hinzufügen
fig.add_trace(go.Candlestick(
    x=df_AMZN['timestamp'],
    open=df_AMZN['open'],
    high=df_AMZN['high'],
    low=df_AMZN['low'],
    close=df_AMZN['close'],
    name='Candlestick'
))

# Volumendaten als Balkendiagramm hinzufügen
fig.add_trace(go.Bar(
    x=df_AMZN['timestamp'],
    y=df_AMZN['volume'],
    name='Volume',
    marker_color='blue',
    opacity=0.5,
    yaxis='y2'  # Zweite Y-Achse für das Volumen
))

# Layout anpassen
fig.update_layout(
    title="Candlestick Chart mit Volumendaten",
    xaxis_title="Zeit",
    yaxis_title="Preis",
    yaxis2=dict(
        title="Volumen",
        overlaying='y',
        side='right'
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)

# Plot als HTML-Datei speichern
pio.write_html(fig, file='candlestick_plot.html', auto_open=True)