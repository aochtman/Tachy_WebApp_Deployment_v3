# Import required libraries
import copy
# import pathlib
import dash
from dash.dependencies import Input, Output, State, ClientsideFunction
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import dash_bootstrap_components as dbc

# -- Added --
import json # can be removed later
import math
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import numpy as np


# -- Authentication --
import dash_auth
from flask import request


# Database controller
import sys
# sys.path.append('.') # go up one folder
from datacontroller_production import *


app = dash.Dash(
    __name__, 
    external_stylesheets = [dbc.themes.BOOTSTRAP], 
    meta_tags=[{"name": "viewport", "content": "width=device-width"}], 
    # show_undo_redo=True # undo redo left bottom corner button
)
server = app.server
app.title = "Tachy Web App"
# auth = dash_auth.BasicAuth(
#     app,
#     LOGINS
# )


# Create app layout
app.layout = html.Div(
    [
        

    ],id="mainContainer",style={"display": "flex", "flex-direction": "column",'bgcolor':'purple'},
)



# Main
if __name__ == "__main__":
    app.run_server(debug=True)

