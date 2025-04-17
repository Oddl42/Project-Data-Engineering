#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr  9 19:42:46 2025

@author: willket
"""

from dash import Dash, html, dcc, Input, Output, State, callback_context
from pymongo import MongoClient

# Verbindung zur MongoDB herstellen
uri = "mongodb://127.0.0.1:27017"
client = MongoClient(uri)
db = client["stockDB"]
tickers_collection = db["tickers"]
selected_tickers_collection = db["selected_tickers"]
settings_db = db["settings"]

# Dash-App initialisieren
app = Dash(__name__)

# Alle Ticker aus der tickers-Datenbank abrufen
tickers = list(tickers_collection.find({}, {"_id": 0, "symbol": 1, "name": 1}))

# Layout der Dash-App
app.layout = html.Div([
    html.H1("Ticker-Auswahl"),
    html.Div(id="checkbox-container", children=[
        dcc.Checklist(
            id="ticker-checkboxes",
            options=[{"label": f"{ticker['name']} ({ticker['symbol']})", "value": ticker["symbol"]} for ticker in tickers],
            value=[],  # Initial leer, wird durch Callback gefüllt
            inline=False  # Checkboxen untereinander
        )
    ]),
    html.Button("Alle auswählen", id="select-all-button", n_clicks=0),
    html.Div(id="output"),
    html.Div([
        html.H2("Zeitauswahl"),
        html.Div(
            id="time-selection-bar",
            children=[
                html.Button("1m", id="1m", n_clicks=0, className="time-button"),
                html.Button("5m", id="5m", n_clicks=0, className="time-button"),
                html.Button("10m", id="10m", n_clicks=0, className="time-button"),
                html.Button("15m", id="15m", n_clicks=0, className="time-button"),
                html.Button("30m", id="30m", n_clicks=0, className="time-button"),
                html.Button("1h", id="1h", n_clicks=0, className="time-button"),
                html.Button("4h", id="4h", n_clicks=0, className="time-button"),
                html.Button("T", id="T", n_clicks=0, className="time-button"),
                html.Button("W", id="W", n_clicks=0, className="time-button"),
                html.Button("M", id="M", n_clicks=0, className="time-button"),
            ],
            style={"display": "flex", "gap": "10px"}
        ),
        html.Div(id="time-selection-output", style={"marginTop": "20px"}),
    ])
])

# Kombinierter Callback zur Initialisierung und Aktualisierung der Checkboxen
@app.callback(
    Output("ticker-checkboxes", "value"),
    Output("output", "children"),
    Input("select-all-button", "n_clicks"),
    Input("ticker-checkboxes", "value"),
    State("ticker-checkboxes", "options")
)
def manage_checkboxes(n_clicks, selected_symbols, options):
    ctx = callback_context
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if triggered_id == "select-all-button" and n_clicks > 0:
        # Wenn der "Alle auswählen"-Button geklickt wurde
        all_symbols = [option["value"] for option in options]
        # Datenbank aktualisieren
        selected_tickers_collection.delete_many({})
        selected_tickers_collection.insert_many(
            [{"symbol": ticker["symbol"], "name": ticker["name"]} for ticker in tickers]
        )
        return all_symbols, f"Alle Ticker ausgewählt: {', '.join(all_symbols)}"

    elif triggered_id == "ticker-checkboxes":
        # Wenn die Checkboxen geändert wurden
        selected_tickers_collection.delete_many({})
        selected_tickers_collection.insert_many(
            [{"symbol": ticker["symbol"], "name": ticker["name"]} for ticker in tickers if ticker["symbol"] in selected_symbols]
        )
        return selected_symbols, f"Ausgewählte Ticker: {', '.join(selected_symbols)}"

    else:
        # Initialisierung beim Laden der Seite
        selected_tickers = list(selected_tickers_collection.find({}, {"_id": 0, "symbol": 1}))
        initial_symbols = [ticker["symbol"] for ticker in selected_tickers]
        return initial_symbols, f"Ausgewählte Ticker: {', '.join(initial_symbols)}"

# Callback für die Zeitauswahl
@app.callback(
    [Output(button_id, "style") for button_id in ["1m", "5m", "10m", "15m", "30m", "1h", "4h", "T", "W", "M"]] +
    [Output("time-selection-output", "children")],
    [Input(button_id, "n_clicks") for button_id in ["1m", "5m", "10m", "15m", "30m", "1h", "4h", "T", "W", "M"]]
)
def update_time_selection(*n_clicks):
    time_buttons = ["1m", "5m", "10m", "15m", "30m", "1h", "4h", "T", "W", "M"]
    ctx = callback_context
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Standard-Stil für alle Buttons
    default_style = {"backgroundColor": "white", "color": "black", "padding": "10px", "border": "1px solid black"}
    selected_style = {"backgroundColor": "blue", "color": "white", "padding": "10px", "border": "1px solid black"}

    # Initialisierung
    styles = [default_style for _ in time_buttons]

    # Wenn ein Button geklickt wurde
    if triggered_id in time_buttons:
        selected_time = triggered_id
        # Markiere den ausgewählten Button
        styles[time_buttons.index(triggered_id)] = selected_style
        # Speichere die Auswahl in der settings_db
        settings_db.update_one(
            {"setting": "time_interval"},
            {"$set": {"value": selected_time}},
            upsert=True
        )
        output_text = f"Ausgewählte Zeiteinstellung: {selected_time}"
    else:
        # Standardausgabe
        selected_time = settings_db.find_one({"setting": "time_interval"}) or {"value": "Keine Auswahl"}
        output_text = f"Ausgewählte Zeiteinstellung: {selected_time['value']}"

    return styles + [output_text]

# App ausführen
if __name__ == "__main__":
    app.run(debug=True)