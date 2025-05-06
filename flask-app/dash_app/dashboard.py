# dash_app/dashboard.py
import dash
from dash import html, dcc
import plotly.express as px
import pandas as pd

def init_dashboard(server):
    app = dash.Dash(
        __name__,
        server=server,
        routes_pathname_prefix='/dash/',
    )

    # Example data
    df = pd.DataFrame({
        "Category": ["A", "B", "C"],
        "Value": [10, 20, 30]
    })

    fig = px.bar(df, x="Category", y="Value", title="Sample Bar Chart")

    app.layout = html.Div([
        html.H1("Dashboard Content"),
        dcc.Graph(figure=fig),
    ])

    return app
