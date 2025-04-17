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
    html.Div(id="output")
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

# App ausführen
if __name__ == "__main__":
    app.run(debug=True)