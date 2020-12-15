import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import dash_bootstrap_components as dbc
from   dash.exceptions import PreventUpdate
from   dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from   plotly.subplots import make_subplots
from   datacontroller_production import DatabaseController
import numpy as np
import pandas as pd
import time


# function to render target egm and 5 nearest neighbour egm
def render_egm3(current_id: int, df_all):
    fig2 = make_subplots(
        rows=7, cols=1, shared_xaxes=True, vertical_spacing=0.05
    )
    current_row = df_all.loc[current_id]
    current_egm = np.fromstring(current_row['egm'], sep=' ', dtype=np.float)
    x = np.arange(1, 2035)
    fig2.add_trace(go.Scatter(x=x, y=current_egm, name=f'id {current_id}'), row=1, col=1)
    fig2.add_trace(go.Scatter(x=x, y=abs(current_egm), name=f'abs id {current_id}'), row=2, col=1)

    # plot nn5
    nn5_ids = [int(i) for i in current_row['nn5'].split(',')]
    nn5_egm = []

    for i, row in df_all.iterrows():
        if row['id'] in nn5_ids:
            egm = row['egm']
            egm = np.fromstring(egm, sep=' ', dtype=np.float)
            nn5_egm.append(egm)
            if len(nn5_egm) == 5:
                break

    for i, (nn_id, nn_egm) in enumerate(zip(nn5_ids, nn5_egm)):
        name = "NN-{} (ID {})".format(i, nn_id)
        fig2.add_trace(go.Scatter(x=x, y=nn_egm, name=name), row=i + 3, col=1) # start from row 3

    fig2.update_yaxes(nticks=3)
    return fig2


"""  Connect to db   """
# db = DatabaseController('root', '4854197saw', 'tachy', 'localhost')  # local DB
db = DatabaseController.get_heroku_db()  #cloud dB
caseids = db.fetch_all_case_ids()
CASE_ID = '19_50_48'


""" Building app """
app = dash.Dash(
    __name__,
    # use dbc style layout
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[{"name": "viewport", "content": "width=device-width"}],
)
server = app.server
app.title = "Tachy Web App"  # name that appears on safari tab


""" Create app layout """
app.layout = html.Div(
    [
        # Variables
        dcc.Store(id='table_data'),
        dcc.Store(id="LAT3d_data"),
        dcc.Store(id='egm_nn5_data'),

        # col-lg-3 - Navbar
        html.Div(
            [
                # Col sticky-top
                html.Div(
                    [
                        # Dropdown to select case
                        dbc.Card(
                            [
                                html.H5("Load Case", className="my-color font-weight-bold"),
                                dcc.Dropdown(
                                    id="dropdown_case",
                                    className="dcc_control",
                                    placeholder="Select or search case...",
                                    options=[{'value': x, 'label': x} for x in caseids],
                                    value=CASE_ID,
                                ),
                            ], body=True, className="shadow my-navbar-well my-margin-top--1rem",
                        ),
                        # -end-

                        # DataTable
                        dbc.Card(
                            [
                                html.H5("Data", className="my-color font-weight-bold"),
                                dash_table.DataTable(
                                    id='datatable',
                                    columns=[{"name": i, "id": i} for i in ['id', 'new_gt', 'label', 'label_temp',
                                                                            'pattern_temp']],
                                    style_header={
                                        'backgroundColor': 'white',
                                        'fontWeight': 'bold'
                                    },
                                    style_table={
                                        'overflowY': 'auto',
                                        'maxHeight': '430px',
                                        # 'maxHeight': '100%',
                                    },
                                    page_size=12,
                                    sort_action='native',
                                    filter_action='custom',
                                    filter_query='',
                                    editable=True,
                                    export_format='csv',
                                ),
                            ], body=True, className="shadow my-navbar-well"
                        ),
                        # -end-

                        # Review radio buttons and save button
                        dbc.Card(
                            [
                                # Export button
                                dbc.Button("Upload to db", outline=True, color="primary", id='upload_button'),
                            ], body=True, className="shadow my-navbar-well",
                        ),
                        # -end-
                    ], className="sticky-top"
                )
                # -end-
            ], className='col-lg-3 padding-r-0 my-bg-color'
        ),
        # -end-

        # Content
        html.Div(
            [
                # Row
                dbc.Row(
                    [
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    # LAT/Timings model
                                    html.H5("Models", className="my-color font-weight-bold"),
                                    html.Div(
                                        [
                                            html.Div([
                                                dcc.Graph(id="graph_timings",
                                                          style={'height': '600px'}),
                                            ], className="col-md-12")
                                        ], className="row"
                                    ),
                                ],
                            ),
                            className="container-fluid my-navbar-well row-marin-top-0"
                        ),
                    ]
                ),
                # -- end graph

                # Row
                dbc.Row(
                    [
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    # Electrogram of selected id and 5nn
                                    html.H5('Electrogram', className="my-color font-weight-bold"),
                                    html.Div(
                                        [
                                            html.Div([
                                                dcc.Graph(id="graph_egm", style={'height': '850px'}),
                                            ], className="col-md-12"),

                                        ], className="row"
                                    ),
                                ],
                            ),
                            className="container-fluid my-navbar-well row-marin-top-0"
                        ),
                    ]
                ),
                # -- end graph

            ], className='col-lg-9 myContent'
        ),

    ], className="row", style={'background': 'black !important'},
)

"""====================================      CALLBACKS    ===================================================="""


# Update all dcc.Store variable with respect to seleceted caseid
@app.callback(
    [
        Output("LAT3d_data", "data"),
        Output("egm_nn5_data", "data"),
        Output("table_data", "data"),
    ],
    [
        Input("dropdown_case", "value"),
    ]
)
def store_data_in_dcc(value):
    print('-------------------------------------')
    print(f'Updating {value} data in dcc.Store...')
    sql = f"SELECT id, new_gt, x, y, z, t, egm, nn5, label, label_temp, pattern_temp FROM data WHERE caseid='{value}';"
    start_time = time.time()
    df = db.fetch_as_df(sql)
    print(f'fetch as df time elapse: {(time.time()-start_time)/60:.2f}min')

    df_table_data = df[['id', 'new_gt', 'label', 'label_temp', 'pattern_temp']]
    df_table_data = df_table_data.dropna(subset=['label'])

    LAT3d_data = df[['id', 'x', 'y', 'z', 't']].to_dict('records')
    egm_nn5_data = df[['id', 'egm', 'nn5']].to_dict('records')
    df_table_data = df_table_data.to_dict('records')

    return LAT3d_data, egm_nn5_data, df_table_data


# Update datatable for display
@app.callback(
    Output("datatable", "data"),
    [
        Input("table_data",   "data"),        # dcc.Store variable
    ]
)
def populate_datatable(data):
    return data


# Update LAT graph for display
@app.callback(
    Output('graph_timings', 'figure'),  # Graph Timings
    [
      Input("LAT3d_data", "data"),
    ]
)
def update_graph_lat(data):
    print('-------------------------------------')
    print('Updating graph timing...')
    df = pd.DataFrame.from_dict(data)
    x, y, z = df['x'].values, df['y'].values, df['z'].values
    t = df['t'].values

    LAT_data = dict(
        mode="markers",
        name="All Points",
        type="scatter3d",
        opacity=1,
        x=x,
        y=y,
        z=z,
        # ids=df['id'].values,
        # text=df['id'].values,
        hoverinfo='text',
        marker=dict(size=8, color=t, colorscale='Jet', colorbar=dict(title="Time Scale"),
                    line=dict(width=2, color='DarkSlateGrey', opacity=1, ))
    )

    # 2. Populate Graph Timings with selected case
    layout1 = dict(
        scene=dict(
            xaxis=dict(zeroline=False),
            yaxis=dict(zeroline=False),
            zaxis=dict(zeroline=False),
        ),
        layout={'clickmode': 'event+select'},
        legend_title='Timings Model',
        legend=dict(
            x=0,
            y=900,
            bordercolor="white",
            borderwidth=1,
        ),
        plot_bgcolor='black',
        paper_bgcolor='black',
        font={'color': 'white'},
        title={
            'text': "Timing Model",
            'y': 0.9,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'color': 'white'
        }
    )

    fig_timings = dict(data=[LAT_data], layout=layout1)
    return fig_timings


# Update egm plots for display
@app.callback(
    Output('graph_egm', 'figure'),
    [
      Input("egm_nn5_data", "data"),
      Input('datatable', 'active_cell'),
    ]
)
def update_egm_plot(data, active_cell=None):
    print('-------------------------------------')
    print('Updating egm plot...')
    df = pd.DataFrame.from_dict(data)

    active_row_id = active_cell['row_id'] if active_cell else 0
    start_time = time.time()
    graph_egm = render_egm3(current_id=active_row_id, df_all=df)
    print(f'egm plotting time elapsed: {(time.time() - start_time):.2f}sec')
    return graph_egm



# Main
if __name__ == "__main__":
    app.run_server(debug=True)
