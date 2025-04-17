#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 17 23:39:01 2025

@author: willket
"""

from dash import Dash, html, dcc, Input, Output, State, callback_context
from pymongo import MongoClient
import plotly.graph_objs as go  # Für die Ticker-Plots

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
    dcc.Tabs([
        dcc.Tab(label="Settings", children=[
            html.Div([
                html.H1("Zeitauswahl"),
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
            ]),
            
            html.H2("Ticker-Auswahl"),
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
        ]),

        dcc.Tab(label="Plots", children=[
            html.H1("Ticker-Plots"),
            html.Div([
                dcc.Dropdown(
                    id="plot-ticker-dropdown",
                    options=[{"label": f"{ticker['name']} ({ticker['symbol']})", "value": ticker["symbol"]} for ticker in tickers],
                    placeholder="Wählen Sie einen Ticker aus",
                ),
                dcc.Graph(id="ticker-plot")
            ])
        ])
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
    """
    Verwalte die Auswahl der Checkboxen und beschränke die maximale Auswahl auf 5 Ticker.

    Args:
        n_clicks (int): Anzahl der Klicks auf den "Alle auswählen"-Button.
        selected_symbols (list): Liste der aktuell ausgewählten Ticker-Symbole.
        options (list): Liste der verfügbaren Ticker-Optionen.

    Returns:
        tuple: Aktualisierte Liste der ausgewählten Ticker und eine Ausgabemeldung.
    """
    ctx = callback_context
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    max_ticker_limit = 5  # Maximale Anzahl an auswählbaren Tickern

    if triggered_id == "select-all-button" and n_clicks > 0:
        # Wenn der "Alle auswählen"-Button geklickt wurde
        all_symbols = [option["value"] for option in options]
        if len(all_symbols) > max_ticker_limit:
            return [], f"Fehler: Es können maximal {max_ticker_limit} Ticker ausgewählt werden. Bitte Key Updaten"
        # Datenbank aktualisieren
        selected_tickers_collection.delete_many({})
        selected_tickers_collection.insert_many(
            [{"symbol": ticker["symbol"], "name": ticker["name"]} for ticker in tickers]
        )
        return all_symbols, f"Alle Ticker ausgewählt: {', '.join(all_symbols)}"

    elif triggered_id == "ticker-checkboxes":
        # Wenn die Checkboxen geändert wurden
        if len(selected_symbols) > max_ticker_limit:
            return [], f"Fehler: Es können maximal {max_ticker_limit} Ticker ausgewählt werden. Bitte Key Updaten"
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


# Callback für den Plot der Ticker
@app.callback(
    Output("ticker-plot", "figure"),
    Input("plot-ticker-dropdown", "value")
)
def update_ticker_plot(selected_ticker):
    """
    Callback zum Aktualisieren des Ticker-Plots basierend auf der Auswahl.

    Args:
        selected_ticker (str): Das ausgewählte Ticker-Symbol.

    Returns:
        plotly.graph_objs.Figure: Der aktualisierte Plot.
    """
    if not selected_ticker:
        return go.Figure()  # Leerer Plot, wenn kein Ticker ausgewählt ist

    # Beispiel-Daten (hier: Dummy-Daten)
    # In der Praxis sollten die Daten aus der Datenbank abgerufen werden

# App ausführen
if __name__ == "__main__":
    app.run(debug=True)