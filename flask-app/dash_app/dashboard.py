# dash_app/dashboard.py
import dash
from dash import html, dcc
import plotly.express as px
import pandas as pd
import plotly.graph_objs as go

import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp

def ode_system(t, y):
    # Example: simple harmonic oscillator
    dydt = [y[1], -0.1 * y[1] - y[0]]
    return dydt

# Solve ODE
sol = solve_ivp(
    ode_system,
    t_span=[0, 100],
    y0=[1, 0],
    dense_output=True
)

# Generate 10,000 time points
t_vals = np.linspace(0, 100, 10000)
y_vals = sol.sol(t_vals)

# Create DataFrame
df = pd.DataFrame({
    "time": t_vals,
    "y0": y_vals[0],
    "y1": y_vals[1]
})

def create_dashboard(server):
    dash_app = dash.Dash(server=server, url_base_pathname='/dash/', external_stylesheets=['/static/css/style.css'],)

    print("BUILT DASH")

    # Build layout
    dash_app.layout = html.Div([
        html.H2("ODE Solution Dashboard"),
        dcc.Graph(
            id="ode-plot",
            figure={
                "data": [
                    go.Scatter(x=df["time"], y=df["y0"], mode="lines", name="y0"),
                    go.Scatter(x=df["time"], y=df["y1"], mode="lines", name="y1")
                ],
                "layout": go.Layout(title="ODE Solution", xaxis={"title": "Time"}, yaxis={"title": "State"})
            }
        ),
        html.Div([
            html.H4("Time Series Snapshot"),
            dcc.Slider(
                id="time-slider",
                min=0,
                max=100,
                step=0.1,
                value=0,
                marks={0: '0', 50: '50', 100: '100'}
            ),
            html.Div(id="time-series-output")
        ])
    ])
    

    # Callback for time series info
    @dash_app.callback(
        dash.dependencies.Output("time-series-output", "children"),
        [dash.dependencies.Input("time-slider", "value")]
    )
    def update_output(selected_time):
        idx = (np.abs(df["time"] - selected_time)).argmin()
        return f"At t = {df.iloc[idx]['time']:.2f}, y0 = {df.iloc[idx]['y0']:.4f}, y1 = {df.iloc[idx]['y1']:.4f}"

    return dash_app.server
