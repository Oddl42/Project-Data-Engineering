# dashboard.py
import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd

# Test-Datenset
df = px.data.iris()

# Create Plotly-Grafic
fig = px.scatter(
    df, 
    x="sepal_width", 
    y="sepal_length", 
    color="species", 
    title="Iris-Datensatz"
)

# Create Dash-App
app = dash.Dash(__name__)

# define Layout
app.layout = html.Div([
    html.H1("Beispiel-Dashboard"),
    dcc.Graph(figure=fig)
])

# Start: localhost => 127.0.0.1
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8050)