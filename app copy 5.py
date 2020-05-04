# Import required libraries
import copy
import pathlib
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
sys.path.append('.') # go up one folder
from DataController_2 import *

# Database Connection
# db = DatabaseController('root','','tachy','localhost')
# db = DatabaseController('b59b25a8f483fb','df9f008b','heroku_59f0bb8d5ef8c3d','us-cdbr-iron-east-05.cleardb.net') # Heroku DB

def render_egm3(targetID, df):
    targetID = int(targetID)
    fig2 = make_subplots(
            rows=7, cols=1, shared_xaxes=True, vertical_spacing=0.05
        )
    target = df[df['id'] == targetID]
    # name = "{} ({})".format(targetID, target['label'].values[0])
    name = "Target (ID {})".format(targetID)
    name2 = "Target Absolute (ID {})".format(targetID)
    x = np.arange(1,2035)
    y = copy.deepcopy(target['egm'].values)
    y = pd.DataFrame(list(map(float, y[0].split())))[0].values
    fig2.add_trace(go.Scatter(x=x, y=y, name=name),row=1, col=1)
    fig2.add_trace(go.Scatter(x=x, y=abs(y), name=name),row=2, col=1)
    a = target['nn5'].values[0].split()
    a = a[0]
    b = a.split(',')
    c = list(map(int, b))

    count = 3
    for id_ in c:
        df_nn = df[df['id'] == id_]
        y = df_nn['egm'].values
        y = pd.DataFrame(list(map(float, y[0].split())))[0].values
        # name = "NN-{} (ID {})".format(count-2,id_, df_nn['label'].values[0])
        name = "NN-{} (ID {})".format(count-2,id_)
        fig2.add_trace(go.Scatter(x=x, y=y, name=name),row=count, col=1)
        count +=1

    # myRange = 1
    # fig2.update_yaxes(range=[-myRange,myRange])
    fig2.update_yaxes(nticks=3)
    fig2.update_layout(title_text = "EGM Graphs")
    return fig2

# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()

LOGINS = [
        ('andrie', 'tachyplatform1234'),
        ('shiernee', 'tachyplatform1234'),
        ('eric', 'tachyplatform1234'),
        ('murphy', 'tachyplatform1234'),
        ('intern', 'intern1234'),
    ]

app = dash.Dash(
    __name__, 
    external_stylesheets = [dbc.themes.BOOTSTRAP], 
    meta_tags=[{"name": "viewport", "content": "width=device-width"}], 
    # show_undo_redo=True # undo redo left bottom corner button
)
server = app.server
app.title = "Tachy"
auth = dash_auth.BasicAuth(
    app,
    LOGINS
)



# Create app layout
app.layout = html.Div(
    [
        dcc.Store(id="aggregate_data"),
        # empty Div to trigger javascript file for graph resizing
        html.Div(id="output-clientside"),

        # Row 1 - Upper bar
        html.Div(
            [
                html.Div(
                    [
                        html.Img(
                            src=app.get_asset_url("dash-logo.png"),
                            id="plotly-image",
                            style={
                                "height": "60px",
                                "width": "auto",
                                "margin-bottom": "25px",
                            },
                        )
                    ],
                    className="col",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H3(
                                    "Tachycardia Dashboard",
                                    style={"margin-bottom": "0px"},
                                ),
                                # html.H5(
                                #     "Loading message...", style={"margin-top": "0px"},id='text_user'
                                # ),
                            ]
                        )
                    ],
                    className="col",
                    id="title",
                ),
                html.Div(
                    [
                        html.Div([
                            # dbc.Button("Log Out", outline=True, color="danger", className="ml-4 pull-right font-weight-bold invisible"),
                            html.H5("Loading message...", style={"margin-top": "0px"},id='text_user'),
                        ],className="text-right"),
                    ],
                    className="col",
                    id="button",
                ),
            ],
            id="header",
            className="row flex-display",
            style={"margin-bottom": "25px"},
        ),

        # Row 1
        html.Div(
            [
                html.Div(
                    [
                        html.H6("Load Case", className="well"),
                        dcc.Dropdown(
                            id="dropdown_case",
                            className="dcc_control",
                            placeholder="Select or search case..."
                        ),
                    ],
                    className="col pretty_container load case",
                    id="cross-filter-options",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                # html.Div([
                                #     # dcc.Markdown("""
                                #     #     **Zoom and Relayout Data**

                                #     #     Click and drag on the graph to zoom or click on the zoom
                                #     #     buttons in the graph's menu bar.
                                #     #     Clicking on legend items will also fire
                                #     #     this event.
                                #     # """),
                                #     # html.Pre(id='relayout-data'),
                                #     html.P("RelayoutData here", id="relayout-data")
                                # ], className='mini_container'),
                                html.Div(
                                    [
                                        html.H6("Ground Truth / Signals", className="well"), 
                                        html.P("Loading...", className="test", id="text_gt"),
                                        dbc.Progress("",id='progress_gt',value=0,striped=True,animated=True,color="progress",style={"height": "20px", "margin":"-8px 4px 0px 4px", 'font-size':'14px'})
                                    ],id="gt",
                                    className="col mini_container",
                                ),
                                html.Div(
                                    [
                                        html.H6("Predictions / Ground Truth", className="well"), 
                                        html.P("Loading...", className="test", id="text_pred"),
                                        dbc.Progress("",id='progress_pred',value=0,striped=True,animated=True,color="warning",style={"height": "20px", "margin":"-8px 4px 0px 4px", 'font-size':'14px'})
                                    ],id="pred",
                                    className="col mini_container",
                                ),
                                html.Div(
                                    [
                                        html.H6("No. of Error", className="well"), 
                                        html.P("233 / 234", className="test", id="text_error"),
                                        dbc.Progress("50%",value=50,striped=True,animated=True,color="danger",style={"height": "20px", "margin":"-8px 4px 0px 4px", 'font-size':'14px'})
                                    ],id="error",
                                    className="col mini_container",
                                ),
                                # html.Div(
                                #     [html.H6("Wrong Predictions", id="oilText", className="well"), html.P("30 / 233 (14%)", className="test")],
                                #     id="oil",
                                #     className="mini_container",
                                # ),
                                html.Div(
                                    [html.H6("No. of Manual Review",id="waterText", className="well"), html.P("3 / 30 (10%)", className="test")],
                                    id="water",
                                    className="col mini_container",
                                ),
                            ],
                            id="info-container",
                            className="row container-display",
                        ),
                    ],
                    id="right-column",
                    className="eight columns",
                ),
            ],
            className="row flex-display",
        ),
        # End row 1

        # Row 2
        html.Div(
            [
                # Col 1
                html.Div(
                    [   
                        # Row 1 - DataTable
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.H6("Data Table", className="well"),
                                        dash_table.DataTable(
                                            id='datatable',
                                            style_cell_conditional=[
                                                {'if': {'column_id': 'ID'},
                                                    'max-width': '40px',
                                                    'fontWeight': 'bold',
                                                    'textAlign': 'center'},
                                                {'if': {'column_id': 'GT'},
                                                    'max-width': '60px',
                                                    'fontWeight': 'bold',
                                                    'textAlign': 'center'},
                                                {'if': {'column_id': 'Predicted'},
                                                    'max-width': '60px',
                                                    'fontWeight': 'bold',
                                                    'textAlign': 'center'},
                                                {'if': {'column_id': 'Pattern'},
                                                    'max-width': '60px',
                                                    'fontWeight': 'bold',
                                                    'textAlign': 'center'},
                                                {'if': {'column_id': 'Review'},
                                                    'max-width': '60px',
                                                    'fontWeight': 'bold',
                                                    'textAlign': 'center'}
                                            ],
                                            style_data_conditional=[
                                                {
                                                    'if': {'row_index': 'odd'},
                                                    'backgroundColor': 'rgb(248, 248, 248)'
                                                }
                                            ],
                                            style_header={
                                                'backgroundColor': 'rgb(230, 230, 230)',
                                                'fontWeight': 'bold'
                                            },
                                            style_table={
                                                'overflowY': 'scroll',
                                                'maxHeight': '400px',
                                                # 'maxHeight': '100%',
                                                },
                                            page_size=10000,
                                            sort_action='native',
                                        )
                                    ], className='col pretty_container'
                                )
                            ], className='row'
                        ),
                        # Row 2 - Review
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.H6("Review", className="well"),
                                        # html.Br(),
                                        html.Label("Loading...", id="text_target", className="font-weight-bold"),
                                        dcc.RadioItems(
                                            options=[
                                                {'label': '   None', 'value': 0},
                                                {'label': '   Normal', 'value': 'normal'},
                                                {'label': '   Split', 'value': 'split'},
                                                {'label': '   Unclassified', 'value': 'unclassified'},
                                            ],
                                            value=0,
                                            id="radio_review",
                                        ),
                                        # html.Br(),
                                        dbc.Button("Save", color="primary", block=True, id="button_review"),
                                    ], className='col pretty_container'
                                )
                            ], className='row col-md-3 fixed-bottom'
                        )
                    ],
                    className="col-md-3",
                ),
                html.Div(
                    [
                        dcc.Tabs(id='tabs-example', value='tab-1', children=[
                            # dcc.Tab(label='EGM Graphs', value='tab-1', className="myTab", selected_className="myTab2", children=[dcc.Graph(
                            #         id="graph_egm",
                            #         figure=make_subplots(rows=6, cols=1, shared_xaxes=True, vertical_spacing=0.05),
                            #         animate=False)
                            #     ]),
                            dcc.Tab(label='Model Timings, Voltage & EGM Graph', value='tab-1', className="myTab", selected_className="myTab2", children=[
                                html.Div(
                                    [
                                        html.Div([
                                            dcc.Graph(id="graph_timings",style={'height': '600px'}),
                                        ], className="col-md-6"),
                                        html.Div([
                                            dcc.Graph(id="graph_voltage",style={'height': '600px'})
                                        ], className="col-md-6"),
                                    ], className="row"
                                ),
                                html.Div(
                                    [
                                        html.Div([
                                            dcc.Graph(id="graph_egm2",style={'height': '900px'}),
                                        ], className="col"),
                                    ], className="row"
                                ),
                            ]),
                            # dcc.Tab(label='Model Voltage', value='tab-3', className="myTab", selected_className="myTab2", children=[dcc.Graph(id="graph_voltage2",style={'height': '650px', 'width':'100%'})]),
                            dcc.Tab(label='Model Classes', value='tab-2', className="myTab", selected_className="myTab2", children=[dcc.Graph(id="graph_classes",style={'height': '650px', 'width':'100%'})]),
                        ]),
                        html.Div(id='tabs-example-content')
                    ],
                    className="col-md-8 pretty_container",
                ),
            ],
            className="row flex-display",
        ),
        # END

        # Row 1 - Upper bar
        html.Hr(style={'margin-top': '1rem;','margin-bottom': '1rem;','border': '0;','border-top': '1px solid rgba(0, 0, 0, 0.1);'}),
        html.Div(
            [
                html.Div(
                    [
                    ],
                    className="col",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H5(
                                    "Made by Andrie Ochtman",
                                    style={"margin-bottom": "0px",'color':'black'},
                                    className="text-center"
                                ),
                            ]
                        )
                    ],
                    className="col",
                    id="title1",
                ),
                html.Div(
                    [
                    ],
                    className="col",
                    id="button1",
                ),
            ],
            id="header1",
            className="row flex-display",
            style={"margin-bottom": "25px"},
        ),
    

    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)

########################################################################################################################################################
# CALLBACKS
########################################################################################################################################################

############
# Workflow 1 - Populate Dropdown
############
@app.callback(
    [
        Output("dropdown_case", "options"), Output("dropdown_case", "value"), # Dropdown
        Output("text_user", "children"), # Dropdown
        Output("button_review", "disabled"), Output("button_review", "children"),
        
    ], 
    [
        Input("aggregate_data", "data"), # Invisible Div (on page load)
    ] 
)
def populate_dropdown(data):
    db = DatabaseController('root','','tachy','localhost')
    # db = DatabaseController('b59b25a8f483fb','df9f008b','heroku_59f0bb8d5ef8c3d','us-cdbr-iron-east-05.cleardb.net') # Heroku DB
    caseids = db.pd_read_sql("SELECT caseid FROM data GROUP BY caseid;")
    case_options = []
    for case in caseids["caseid"]:
        case_options.append({"label": f"Case {case} progress: 99%", "value": case})
    value = "21_34_08" # Initial Case

    text_user = "Welcome {}".format(request.authorization['username'].title())
    username = request.authorization['username']
    if username == "andrie" or username == "eric" or username == "murphy":
        text_button = "Save"
        state_button = False
    else:
        text_button = "No Review Authority"
        state_button = True
    return case_options, value, text_user, state_button, text_button

############
# Workflow 2 - Populate DataTable
############
@app.callback(
    [
        Output("datatable", "data"), Output("datatable", "columns"), Output("datatable", "active_cell"),Output("datatable", "selected_cells")# Output("datatable", "selected_cells")  # Dropdown
    ], 
    [
        Input("dropdown_case", "value"), # Invisible Div (on page load)
    ] 
)
def populate_datatable(value):
    db = DatabaseController('root','','tachy','localhost')
    sql = "SELECT * FROM data WHERE caseid='{}';".format(value)
    df = db.pd_read_sql(sql)

    # 1. Populate DataTable with selected case
    df.rename(columns={'id':'ID','label':'GT','label_temp':'Predicted','pattern_temp':'Pattern','review':'Review'}, inplace=True)
    data = df.to_dict('records')
    # print(df.columns)
    # columns = [{"name": i, "id": i} for i in df[['id','label', 'label_algorithm','pattern']]]

    columns = [{"name": i, "id": i} for i in df[['ID','GT', 'Predicted','Pattern','Review']]]
    active_cell = {'row': 0, 'column': 0, 'column_id': 'label', 'row_id': 1}
    selected_cells = [
            {'row': 0, 'column': 0, 'column_id': 'ID', 'row_id': 1}, 
            {'row': 0, 'column': 1, 'column_id': 'GT', 'row_id': 1}, 
            {'row': 0, 'column': 2, 'column_id': 'Predicted', 'row_id': 1}, 
            {'row': 0, 'column': 3, 'column_id': 'Pattern', 'row_id': 1},
            {'row': 0, 'column': 4, 'column_id': 'Review', 'row_id': 1},
        ]

    return data, columns, active_cell, selected_cells

############
# Workflow 3 - Initial Load Callbacks
############
@app.callback(
    [
        # Output("datatable", "data"), Output('datatable', 'columns'), # 1. Datatable
        Output('graph_timings', 'figure'), # 2. Graph Timings
        Output('graph_voltage', 'figure'), # 3. Graph Voltage
        Output('graph_classes', 'figure'), # 
        Output('text_gt', 'children'), Output('progress_gt', 'value'), Output('progress_gt', 'children'),# 
        Output('text_pred', 'children'), Output('progress_pred', 'value'), Output('progress_pred', 'children'),#
        Output('text_target', 'children'), # 
        Output('graph_egm2', 'figure'), # Graph EGM
    ],
    [
        Input("dropdown_case", "value"), # Dropdown Selection
        Input("datatable","active_cell"), # Selected cell from datatable
        Input("datatable","selected_cells"),
        Input("datatable","start_cell"),
        Input("datatable","end_cell"),
    ] 
)
def reload_data(value,active_cell,selected_cells,start_cell,end_cell):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    print('\n\n- CTX: ', trigger_id)


    caseid = value
    if value is None:
        caseid = "21_34_08"
    db = DatabaseController('root','','tachy','localhost')
    sql = "SELECT * FROM data WHERE caseid='{}';".format(caseid)
    df = db.pd_read_sql(sql)

    if trigger_id == "dropdown_case":
        target = df.loc[0:0]
        print(target)
    else:
        list_ids = []
        print('- selected_cells: ', selected_cells)
        for i in selected_cells:
            list_ids.append(i["row"])
        target = df.loc[list_ids]
        # for i in selected_cells:
        #     list_ids.append(i["row_id"])
        print('- selected_cells row ids: ', list_ids)

    # -- Target 5 Neareast Neighbors --
    # find row, values=get value from pandas core series, 
    # [0] = convert list to single item (['1029,1028,78,77,87'] becomes '1029,1028,78,77,87')
    # convert to list of integers
    list_target_5nn_ids = to_list_int(df[ df['id'] == active_cell['row']+1]['nn5'].values[0]) 
    target_5nn = df.loc[[i - 1 for i in list_target_5nn_ids]] # substract 1 as df.loc starts from 0 whereas signal IDS start from 1 
    print('- target_5nn: ', list_target_5nn_ids)

    text_target = "Selected Signal ID: {}".format(active_cell['row']+1) if active_cell is not None else "Loading..."

    # -- STATISTICS --
    no_signals = df['id'].count()
    count_per_col = df[(df['label'].notnull()) & (df['label'] != "collision") & (df['label'] != "slow")].count()

    no_gt = count_per_col['label']
    text_gt = "{} / {}".format(no_gt,no_signals)
    perc_gt = int(math.floor(no_gt / no_signals * 100))
    text_gt_progress = "{}%".format(perc_gt) if perc_gt > 9 else " "

    no_pred = count_per_col['label_temp']
    text_pred = "{} / {}".format(no_pred,no_gt)
    perc_pred = int(math.floor(no_pred / no_gt * 100))
    text_pred_progress = "{}%".format(perc_pred) if perc_pred > 9 else ""


    print('- no_signals: {}'.format(no_signals))
    # print('- no_gt: {}\n'.format(count_per_col))
    print('- no_gt: {}'.format(no_gt))
    print('- no_pred: {}'.format(no_pred))
    print("- USERNAME: ", request.authorization['username'])
    print('- Start Cell: ', start_cell)
    print('- End Cell: ', end_cell)
    # print('\nclickData: ', clickData)
    # print("\nclickData['row_id']: ", clickData['row_id'])

    # 2. Populate Graph Timings with selected case
    layout = dict(
        scene = dict(
            xaxis = dict( zeroline=False ),
            yaxis = dict( zeroline=False ),
            zaxis = dict( zeroline=False ),
        ),
        layout = {'clickmode': 'event+select'},
        legend = dict(
            x=0,
            y=900,
            bordercolor="white",
            borderwidth=1,
            # font = 'white',
        ),
        # plot_bgcolor = '#BEBEBE',
        # paper_bgcolor = '#BEBEBE'
        plot_bgcolor = 'black',
        paper_bgcolor = 'black',
        font = {'color': 'white'},
    )
    TARGET = dict(
        mode = "markers",
        name = "Target",
        type = "scatter3d",
        opacity = 1,
        x = target['x'], 
        y = target['y'], 
        z = target['z'],
        ids = target['id'],
        text = target['id'],
        hoverinfo = 'text',
        marker = dict( size=20, color="white", opacity=1 )
    )
    target_5nn = dict(
        mode = "markers",
        name = "Target's 5NN",
        type = "scatter3d",
        opacity = 1,
        x = target_5nn['x'], 
        y = target_5nn['y'], 
        z = target_5nn['z'],
        ids = target_5nn['id'],
        text = target_5nn['id'],
        hoverinfo = 'text',
        marker = dict( size=12, color="pink", opacity=1 )
    )

    allpoints_timings = dict(
        mode = "markers",
        name = "All Points",
        type = "scatter3d",
        opacity = 1,
        x = df['x'].values, 
        y = df['y'].values, 
        z = df['z'].values,
        ids = df['id'].values,
        text = df['id'].values,
        hoverinfo = 'text',
        marker = dict( size=8, color=df['t'].values, colorscale='Jet', colorbar=dict(title="Time Scale") )
    )
    fig_timings = dict( data=[TARGET,target_5nn,allpoints_timings], layout=layout)

    # target_5nn = dict(
    #     mode = "markers",
    #     name = "TARGET",
    #     type = "scatter3d",
    #     opacity = 1,
    #     x = target_5nn['x'], 
    #     y = target_5nn['y'], 
    #     z = target_5nn['z'],
    #     ids = target_5nn['id'],
    #     text = target_5nn['id'],
    #     hoverinfo = 'text',
    #     marker = dict( size=17, color="pink", opacity=1 )
    # )
    # fig_timings = dict( data=[TARGET,allpoints_timings], layout=layout)

    # 3. Populate Graph Voltage with selected case
    allpoints_voltage = dict(
        mode = "markers",
        name = "All Points",
        type = "scatter3d",
        opacity = 1,
        x = df['x'].values, 
        y = df['y'].values, 
        z = df['z'].values,
        ids = df['id'].values,
        text = df['id'].values,
        hoverinfo = 'text',
        marker = dict( size=8, color=df['peak2peak'].values, colorscale='Jet', colorbar=dict(title="Voltage Scale"))
    )
    fig_voltage = dict( data=[TARGET,target_5nn,allpoints_voltage], layout=layout)

    df_normal = df[df['label'] == "normal"]
    df_split = df[df['label'] == "split"]
    df_uncl = df[df['label'] == "unclassified"]
    df_rest = df[(df['label'] != "normal") & (df['label'] != "split") & (df['label'] != "unclassified")]

    normal = dict(mode = "markers",name = "Normal",type = "scatter3d",opacity = 1,
        x = df_normal['x'].values,y = df_normal['y'].values,z = df_normal['z'].values,ids = df_normal['id'].values,text = df_normal['id'].values,
        hoverinfo = 'text',
        marker = dict( size=8, color='#3AE314',)
    )
    split = dict(mode = "markers",name = "Split",type = "scatter3d",opacity = 1,
        x = df_split['x'].values,y = df_split['y'].values,z = df_split['z'].values,ids = df_split['id'].values,text = df_split['id'].values,
        hoverinfo = 'text',
        marker = dict( size=8, color='#F9A913',)
    )
    uncl = dict(mode = "markers",name = "Unclassified",type = "scatter3d",opacity = 1,
        x = df_uncl['x'].values,y = df_uncl['y'].values,z = df_uncl['z'].values,ids = df_uncl['id'].values,text = df_uncl['id'].values,
        hoverinfo = 'text',
        marker = dict( size=8, color='red',)
    )
    rest = dict(mode = "markers",name = "Unlabeled",type = "scatter3d",opacity = 1,
        x = df_rest['x'].values,y = df_rest['y'].values,z = df_rest['z'].values,ids = df_rest['id'].values,text = df_rest['id'].values,
        hoverinfo = 'text',
        marker = dict( size=8, color='blue',)
    )
    fig_classes = dict( data=[TARGET,target_5nn,normal,split,uncl,rest], layout=layout)


    graph_egm = render_egm3(active_cell['row']+1, df)

    # return data, columns, fig_timings, fig_voltage
    print('- active_cell: ', active_cell)

    return fig_timings, fig_voltage, fig_classes, text_gt, perc_gt, text_gt_progress, text_pred, perc_pred, text_pred_progress, text_target, graph_egm

########################################################################################################################################################
# END CALLBACKS
########################################################################################################################################################


# Main
if __name__ == "__main__":
    app.run_server(debug=True)

