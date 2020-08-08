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
# import json # can be removed later
import math
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import numpy as np
from plotly.validators.scatter.marker import SymbolValidator


# -- Authentication --
import dash_auth
from flask import request


# Database controller
import sys
# sys.path.append('.') # go up one folder
from datacontroller_production import *


def render_egm3(targetID, df):
    targetID = int(targetID)
    fig2 = make_subplots(
            rows=7, cols=1, shared_xaxes=True, vertical_spacing=0.05
        )
    target = df[df['id'] == targetID]
    # name = "{} ({})".format(targetID, target['label'].values[0])
    name = "Target (ID {})".format(targetID)
    name2 = "Target Abs (ID {})".format(targetID)
    x = np.arange(1,2035)
    y = copy.deepcopy(target['egm'].values)
    y = pd.DataFrame(list(map(float, y[0].split())))[0].values
    fig2.add_trace(go.Scatter(x=x, y=y, name=name),row=1, col=1)
    fig2.add_trace(go.Scatter(x=x, y=abs(y), name=name2),row=2, col=1)
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
    # fig2.update_layout(title_text = "EGM Graphs")
    return fig2

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
app.title = "Tachy Web App"

auth = dash_auth.BasicAuth(
    app,
    LOGINS
)

w1 = [
    dbc.CardBody(
        [
            html.Div(
                [
                    html.H5("Loading...", className="col card-title font-weight-bold", style={'color':'black !important;'},id="w1_header"),
                    html.H5("n/a", className="col card-title font-weight-bold text-right", style={'color':'black !important;'},id="w1_header_perc"),
                ], className='row'
            ),
            dbc.Progress(style={"height": "5px"},value=1, striped=True, animated=True, color='info',id="w1_progress"),
            html.P("Normal",className="card-text font-weight-bold text-center",style={'margin-top':'6px'}),
        ]
    ),
]
w2 = [
    dbc.CardBody(
        [
            html.Div(
                [
                    html.H5("Loading...", className="card-title font-weight-bold", style={'color':'black !important;'},id="w2_header"),
                    html.H5("n/a", className="col card-title font-weight-bold text-right", style={'color':'black !important;'},id="w2_header_perc"),
                ], className='row'
            ),
            dbc.Progress(style={"height": "5px"},value=1, striped=True, animated=True, color='warning',id="w2_progress"),
            html.P("Split",className="card-text font-weight-bold text-center",style={'margin-top':'6px'}),
        ]
    ),
]
w3 = [
    dbc.CardBody(
        [
            html.Div(
                [
                    html.H5("Loading...", className="card-title font-weight-bold", style={'color':'black !important;'},id="w3_header"),
                    html.H5("n/a", className="col card-title font-weight-bold text-right", style={'color':'black !important;'},id="w3_header_perc"),
                ], className='row'
            ),
            dbc.Progress(style={"height": "5px"},value=1, striped=True, animated=True, color='danger',id="w3_progress"),
            html.P("Unclassified",className="card-text font-weight-bold text-center",style={'margin-top':'6px'}),
        ]
    ),
]
w4 = [
    dbc.CardBody(
        [
            html.Div(
                [
                    html.H5("Loading...", className="card-title font-weight-bold", style={'color':'black !important;'},id="w4_header"),
                    html.H5("n/a", className="col card-title font-weight-bold text-right", style={'color':'black !important;'},id="w4_header_perc"),
                ], className='row'
            ),
            dbc.Progress(style={"height": "5px"},value=1, striped=True, animated=True, color='progress',id="w4_progress"),
            html.P("None",className="card-text font-weight-bold text-center",style={'margin-top':'6px'}),
        ]
    ),
]


# Create app layout
app.layout = html.Div(
    [
        # Variables
        dcc.Store(id="aggregate_data"),

        # col-lg-3 - Navbar
        html.Div(
            [
                # Col sticky-top
                html.Div(
                    [
                        html.H5("User", className="my-color font-weight-bold invisible", id='text_user'),
                        # Load Case
                        dbc.Card(
                            [
                                html.H5("Load Case", className="my-color font-weight-bold"),
                                dcc.Dropdown(
                                    id="dropdown_case",
                                    className="dcc_control",
                                    placeholder="Select or search case..."
                                ),
                            ], body=True, className="shadow my-navbar-well my-margin-top--1rem",
                        ),
                        # -end-

                        # DataTable
                        dbc.Card(
                            [
                                html.H5("Data", className="my-color font-weight-bold"),
                                # dbc.Spinner(color="primary"),
                                dash_table.DataTable(
                                    id='datatable',
                                    style_cell_conditional=[
                                        {'if': {'column_id': 'id'},
                                            # 'max-width': '60px',
                                            'min-width': '40px',
                                            'fontWeight': 'bold',
                                            'textAlign': 'right'},
                                        {'if': {'column_id': 'label'},
                                            'max-width': '60px',
                                            'min-width': '60px',
                                            # 'fontWeight': 'bold',
                                            'textAlign': 'right'},
                                        {'if': {'column_id': 'label_temp'},
                                            'max-width': '60px',
                                            'min-width': '60px',
                                            # 'fontWeight': 'bold',
                                            'textAlign': 'right'},
                                        {'if': {'column_id': 'pattern_temp'},
                                            'max-width': '40px',
                                            'min-width': '40px',
                                            # 'fontWeight': 'bold',
                                            'textAlign': 'right'},
                                        {'if': {'column_id': 'review'},
                                            'max-width': '60px',
                                            'min-width': '60px',
                                            # 'fontWeight': 'bold',
                                            'textAlign': 'right'},
                                        # Cell
                                        # {
                                        #     'if': {
                                        #         'column_id': 'label',
                                        #         'filter_query': '{label} eq normal'
                                        #     },
                                        #     'backgroundColor': '#3ab0c3',
                                        #     'color': 'white',
                                        # },
                                    ],
                                    # style_as_list_view=True,

                                    # style_header={'backgroundColor': 'rgb(30, 30, 30)'},
                                    # style_cell={
                                    #     'backgroundColor': 'rgb(50, 50, 50)',
                                    #     'color': 'white'
                                    # },

                                    # css=[{ # override default css for selected/focused table cells
                                    #     selector: 'td.cell--selected, td.focused',
                                    #     rule: 'background-color: #FF4136;'
                                    # }, {
                                    #     selector: 'td.cell--selected *, td.focused *',
                                    #     rule: 'color: #3C3C3C !important;'
                                    # }],

                                    # style_data_conditional=[
                                    #     {
                                    #         'if': {'row_index': 'odd'},
                                    #         'backgroundColor': 'rgb(248, 248, 248)'
                                    #     }
                                    # ],
                                    # style_header={
                                    #     'backgroundColor': 'rgb(230, 230, 230)',
                                    #     'fontWeight': 'bold'
                                    # },
                                    # fixed_rows={'headers': True, 'data': 0},
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
                                ),
                            ], body=True, className="shadow my-navbar-well"
                        ),
                        # -end-

                        # Review
                        dbc.Card(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.H5("Review Signal:", className="my-color font-weight-bold", id='text_review'),
                                            ],className='col'
                                        ),
                                        html.Div(
                                            [
                                                html.H5("1", className="my-color text-right font-weight-bold", id='value_review'),
                                            ],className='col'
                                        ),
                                    ], className='row'
                                ),
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                dbc.RadioItems(
                                                    options=[
                                                        {'label': '   None', 'value': 0},
                                                        {'label': '   Normal', 'value': 'normal'},
                                                        {'label': '   Split', 'value': 'split'},
                                                        {'label': '   Unclassified', 'value': 'unclassified'},
                                                    ],
                                                    value=0,
                                                    id="radio_review",
                                                ),
                                            ], className='col'
                                        ),
                                        html.Div(
                                            [
                                                html.Br(),
                                                # html.H3("ID: 1234",className='text-center')
                                            ], className='col'
                                        ),
                                    ],className='row'
                                ),
                                dbc.Button("Save", outline=True, color="primary", id='button_review'),
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
                        dbc.Col(dbc.Card(w1, color="dark", inverse=True, className='margin-top-1rem')),
                        dbc.Col(dbc.Card(w2, color="dark", inverse=True, className='margin-top-1rem')),
                        dbc.Col(dbc.Card(w3, color="dark", inverse=True, className='margin-top-1rem')),
                        dbc.Col(dbc.Card(w4, color="dark", inverse=True, className='margin-top-1rem')),                        
                    ],className="mb-3"
                ),

                # Row
                dbc.Row(
                    [
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    # -- MODELS --
                                    html.H5("Models", className="my-color font-weight-bold"),
                                    html.Div(
                                        [
                                            html.Div([
                                                dcc.Graph(id="graph_timings",style={'height': '600px', 'margin-right':'-15px'}),
                                            ], className="col-md-6"),
                                            html.Div([
                                                dcc.Graph(id="graph_voltage",style={'height': '600px', 'margin-left':'-15px'})
                                            ], className="col-md-6"),
                                            html.Div([
                                                dcc.Graph(id="graph_predictions",style={'height': '600px', 'margin-right':'-15px'}),
                                            ], className="col-md-6"),
                                            html.Div([
                                                dcc.Graph(id="graph_gt",style={'height': '600px', 'margin-left':'-15px',})
                                            ], className="col-md-6"),
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
                                    # -- MODELS --
                                    html.H5('Electogram', className="my-color font-weight-bold"),
                                    html.Div(
                                        [
                                            html.Div([
                                                dcc.Graph(id="graph_egm",style={'height': '850px'}),
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

                # # Row
                # dbc.Row(
                #     [
                #         dbc.Card(
                #             dbc.CardBody(
                #                 [
                #                     # -- Electrogram --
                #                     html.H5("Electrogram", className="my-color font-weight-bold"),
                #                     html.Div(
                #                         [
                #                             html.Div([
                #                                 dcc.Graph(id="graph_egm",style={'height': '900px', 'width':'2000px'}),
                #                             ], className="col-md-12"),
                #                         ], className="row"
                #                     ),
                #                 ], 
                #             ),
                #             className="row my-navbar-well row-marin-top-0"
                #         ),
                #     ]
                # ),
                # # -- end graph



            ], className='col-lg-9 myContent'#className='col-lg-9 offset-lg-3 myContent'
        ),

    ], className="row", style={'background':'black !important'},
)

########################################################################################################################################################
# CALLBACKS
########################################################################################################################################################
# db = DatabaseController('root','','tachy','localhost') # Heroku DB
db = DatabaseController('b59b25a8f483fb','df9f008b','heroku_59f0bb8d5ef8c3d','us-mm-dca-c6a1e480c80b.g5.cleardb.net') # Heroku DB
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
    # db = DatabaseController('root','','tachy','localhost') # Heroku DB
    db = DatabaseController('b59b25a8f483fb','df9f008b','heroku_59f0bb8d5ef8c3d','us-mm-dca-c6a1e480c80b.g5.cleardb.net') # Heroku DB
    caseids = db.pd_read_sql("SELECT caseid FROM data GROUP BY caseid;")
    case_options = []
    for case in caseids["caseid"]:
        case_options.append({"label": f"Case {case}", "value": case})
    value = "21_52_36" # Initial Case

    text_user = "Welcome {}".format(request.authorization['username'].title())
    username = request.authorization['username']
    if username == "andrie" or username == "eric" or username == "murphy":
        text_button = "Currently Disabled"
        state_button = True
    else:
        text_button = "No Review Authority"
        state_button = True
    return case_options, value, text_user, state_button, text_button

# ###########
# Workflow 2 - Populate DataTable
# ###########
@app.callback(
    [
        Output("datatable", "data"), Output("datatable", "columns"), Output("datatable", "active_cell"),Output("datatable", "selected_cells")# Output("datatable", "selected_cells")  # Dropdown
    ], 
    [
        Input("dropdown_case", "value"), # Invisible Div (on page load)
    ] 
)
def populate_datatable(value):
    # db = DatabaseController('root','','tachy','localhost')
    db = DatabaseController('b59b25a8f483fb','df9f008b','heroku_59f0bb8d5ef8c3d','us-mm-dca-c6a1e480c80b.g5.cleardb.net') # Heroku DB
    sql = "SELECT * FROM data WHERE caseid='{}';".format(value)
    df = db.pd_read_sql(sql)

    # 1. Populate DataTable with selected case
    # df.rename(columns={'id':'ID','label':'GT','label_temp':'Predicted','pattern_temp':'Pattern','review':'Review'}, inplace=True)
    data = df.to_dict('records')
    # print(df.columns)
    columns = [{"name": i, "id": i} for i in df[['id','label', 'label_temp','pattern_temp','review']]]

    # columns = [{"name": i, "id": i} for i in df[['ID','GT', 'Predicted','Pattern','Review']]]
    active_cell = {'row': 0, 'column': 0, 'column_id': 'label', 'row_id': 1}
    selected_cells = [
            {'row': 0, 'column': 0, 'column_id': 'id', 'row_id': 1}, 
            {'row': 0, 'column': 1, 'column_id': 'label', 'row_id': 1}, 
            {'row': 0, 'column': 2, 'column_id': 'label_temp', 'row_id': 1}, 
            {'row': 0, 'column': 3, 'column_id': 'pattern_temp', 'row_id': 1},
            {'row': 0, 'column': 4, 'column_id': 'review', 'row_id': 1},
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
        Output('graph_predictions', 'figure'), # Prediction Model
        Output('graph_gt', 'figure'), # Ground Truth Model
        Output('w1_header', 'children'), Output('w1_header_perc', 'children'), Output('w1_progress', 'value'), #Output('progress_widg_1', 'children'),# 
        Output('w2_header', 'children'), Output('w2_header_perc', 'children'), Output('w2_progress', 'value'), #Output('progress_widg_2', 'children'),#
        Output('w3_header', 'children'), Output('w3_header_perc', 'children'), Output('w3_progress', 'value'), #Output('progress_widg_3', 'children'),#
        Output('w4_header', 'children'), Output('w4_header_perc', 'children'), Output('w4_progress', 'value'), #Output('progress_widg_4', 'children'),#
        Output('graph_egm', 'figure'), # Graph EGM
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
    # db = DatabaseController('root','','tachy','localhost')
    db = DatabaseController('b59b25a8f483fb','df9f008b','heroku_59f0bb8d5ef8c3d','us-mm-dca-c6a1e480c80b.g5.cleardb.net') # Heroku DB
    sql = "SELECT * FROM data WHERE caseid='{}';".format(caseid)
    df = db.pd_read_sql(sql)

    if trigger_id == "dropdown_case":
        target = df.loc[0:0]
        # print(target)
    else:
        list_ids = []
        print('- selected_cells: ', selected_cells)
        for i in selected_cells:
            list_ids.append(i["row_id"]-1) # prepare to be sent to .loc (which starts from 0 instead of 1 so must substract 1)
        target = df.loc[list_ids]
        # for i in selected_cells:
        #     list_ids.append(i["row_id"])
        print('- selected_cells row ids: ', list_ids)

    # -- Target 5 Neareast Neighbors --
    # find row, values=get value from pandas core series, 
    # [0] = convert list to single item (['1029,1028,78,77,87'] becomes '1029,1028,78,77,87')
    # convert to list of integers
    print("- active cell: ", type(active_cell))
    list_target_5nn_ids = to_list_int(df[ df['id'] == active_cell['row_id']]['nn5'].values[0]) if active_cell is not None else to_list_int(df[ df['id'] == 1]['nn5'].values[0]) # check for NoneType on load
    target_5nn = df.loc[[i - 1 for i in list_target_5nn_ids]] # substract 1 as df.loc starts from 0 whereas signal IDS start from 1 
    print('- target_5nn: ', list_target_5nn_ids)

    text_target = "Selected Signal ID: {}".format(active_cell['row_id']) if active_cell is not None else "Loading..."

    # -- STATISTICS --
    no_signals = df['id'].count()

    # counts
    count_nor_pred = df[ (df['label_temp'] == "normal") ]['label_temp'].count()
    count_spl_pred = df[ (df['label_temp'] == "split") ]['label_temp'].count()
    count_unc_pred = df[ (df['label_temp'] == "unclassified") ]['label_temp'].count()
    count_non_pred = df[df['label_temp'].isnull()]['label_temp'].size
    print("- df: ", df[ df['label_temp'].isnull() ]['label_temp'] )
    print("- df count: ", count_non_pred)

    test = df[df['label_temp'].isnull()]['label_temp'].size
    print("- test count: ", test)

    # texts
    txt_count_nor = "{}".format(count_nor_pred)
    txt_count_spl = "{}".format(count_spl_pred)
    txt_count_unc = "{}".format(count_unc_pred)
    txt_count_non = "{}".format(count_non_pred)
    
    # value percentage
    value_perc_nor = count_nor_pred / no_signals * float(100)
    value_perc_spl = count_spl_pred / no_signals * float(100)
    value_perc_unc = count_unc_pred / no_signals * float(100)
    value_perc_non = count_non_pred / no_signals * float(100)
    print(value_perc_nor)

    # percentage
    txt_perc_nor = "{:.1f}%".format(value_perc_nor)
    txt_perc_spl = "{:.1f}%".format(value_perc_spl)
    txt_perc_unc = "{:.1f}%".format(value_perc_unc)
    txt_perc_non = "{:.1f}%".format(value_perc_non)
    print(txt_perc_nor)


    count_per_col = df[(df['label'].notnull()) & (df['label'] != "collision") & (df['label'] != "slow")].count()

    no_gt = count_per_col['label']
    text_gt = "{} / {}".format(no_gt,no_signals)
    perc_gt = int(math.floor(no_gt / no_signals * 100))
    text_gt_progress = "{}%".format(perc_gt) if perc_gt > 9 else " "

    no_pred = count_per_col['label_temp']
    count_normal = df[(df['label'].notnull()) & (df['label'] != "collision") & (df['label'] != "slow")].count()
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
    layout1 = dict(
        scene = dict(
            xaxis = dict( zeroline=False ),
            yaxis = dict( zeroline=False ),
            zaxis = dict( zeroline=False ),
        ),
        layout = {'clickmode': 'event+select'},
        legend_title='Timings Model',
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
        title={
                'text': "Timing Model",
                'y':0.9,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'color': 'white'
            }
    )
    layout2 = dict(
        scene = dict(
            xaxis = dict( zeroline=False ),
            yaxis = dict( zeroline=False ),
            zaxis = dict( zeroline=False ),
        ),
        layout = {'clickmode': 'event+select'},
        legend_title='Timings Model',
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
        title={
                'text': "Voltage Model",
                'y':0.9,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'color': 'white'
            }
    )
    layout3 = dict(
        scene = dict(
            xaxis = dict( zeroline=False ),
            yaxis = dict( zeroline=False ),
            zaxis = dict( zeroline=False ),
        ),
        layout = {'clickmode': 'event+select'},
        legend_title='Timings Model',
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
        title={
                'text': "Predicted Model",
                'y':0.9,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'color': 'white'
            }
    )
    layout4 = dict(
        scene = dict(
            xaxis = dict( zeroline=False ),
            yaxis = dict( zeroline=False ),
            zaxis = dict( zeroline=False ),
        ),
        layout = {'clickmode': 'event+select'},
        legend_title='Timings Model',
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
        title={
                'text': "Ground Truth Model",
                'y':0.9,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'color': 'white'
            }
    )

    # layout_title_1 = dict(legend_title='<b> Timings Model </b>')
    # print("- marker symbol: ", SymbolValidator().values[0])
    TARGET = dict(
        mode = "markers",
        name = "Target",
        type = "scatter3d",
        # opacity = .1,
        x = target['x'], 
        y = target['y'], 
        z = target['z'],
        ids = target['id'],
        text = target['id'],
        hoverinfo = 'text',
        marker = dict( size=20, color="purple", opacity=0.9, symbol="x",line=dict(width=1,color="black"))
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
        marker = dict( size=12, color="pink", opacity=1, symbol="asterisk",line=dict(width=2,color='DarkSlateGrey'))
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
        marker = dict( size=8, color=df['t'].values, colorscale='Jet', colorbar=dict(title="Time Scale"), line=dict(width=2,color='DarkSlateGrey',opacity = 1,))
    )
    # mesh = dict(
    #     alphahull = 6,
    #     name = "mesh",
    #     color = 'purple',
    #     opacity = 0.6,
    #     type = "mesh3d",
    #     x = df['x'].values, 
    #     y = df['y'].values, 
    #     z = df['z'].values,
    #     mode = 'markers',
    #     hoverinfo = 'skip',
    #     showlegend = False
    # )
    fig_timings = dict( data=[TARGET,allpoints_timings], layout=layout1)

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
        marker = dict( size=8, color=df['peak2peak'].values, colorscale='Jet', colorbar=dict(title="Voltage Scale"), line=dict(width=2,color='DarkSlateGrey'))
    )
    fig_voltage = dict( data=[TARGET,allpoints_voltage], layout=layout2)

    # -- Prediction Dataset --
    df_normal = df[df['label_temp'] == "normal"]
    df_split = df[df['label_temp'] == "split"]
    df_uncl = df[df['label_temp'] == "unclassified"]
    df_rest = df[(df['label_temp'] != "normal") & (df['label_temp'] != "split") & (df['label_temp'] != "unclassified")]

    normal = dict(mode = "markers",name = "Normal",type = "scatter3d",opacity = 1,
        x = df_normal['x'].values,y = df_normal['y'].values,z = df_normal['z'].values,ids = df_normal['id'].values,text = df_normal['id'].values,
        hoverinfo = 'text',
        marker = dict( size=8, color='cyan', line=dict(width=2,color='DarkSlateGrey'))
    )
    split = dict(mode = "markers",name = "Split",type = "scatter3d",opacity = 1,
        x = df_split['x'].values,y = df_split['y'].values,z = df_split['z'].values,ids = df_split['id'].values,text = df_split['id'].values,
        hoverinfo = 'text',
        marker = dict( size=8, color='#F9A913', line=dict(width=2,color='DarkSlateGrey'))
    )
    uncl = dict(mode = "markers",name = "Unclassified",type = "scatter3d",opacity = 1,
        x = df_uncl['x'].values,y = df_uncl['y'].values,z = df_uncl['z'].values,ids = df_uncl['id'].values,text = df_uncl['id'].values,
        hoverinfo = 'text',
        marker = dict( size=8, color='red', line=dict(width=2,color='DarkSlateGrey'))
    )
    rest = dict(mode = "markers",name = "Unlabeled",type = "scatter3d",opacity = 1,
        x = df_rest['x'].values,y = df_rest['y'].values,z = df_rest['z'].values,ids = df_rest['id'].values,text = df_rest['id'].values,
        hoverinfo = 'text',
        marker = dict( size=8, color='blue', line=dict(width=2,color='DarkSlateGrey'))
    )
    fig_predictions = dict( data=[TARGET,normal,split,uncl,rest], layout=layout3)

    # -- Ground Truth Dataset --
    df_normal_gt = df[df['label'] == "normal"]
    df_split_gt = df[df['label'] == "split"]
    df_uncl_gt = df[df['label'] == "unclassified"]
    df_rest_gt = df[(df['label'] != "normal") & (df['label'] != "split") & (df['label'] != "label")]

    normal_gt= dict(mode = "markers",name = "Normal",type = "scatter3d",opacity = 1,
        x = df_normal_gt['x'].values,y = df_normal_gt['y'].values,z = df_normal_gt['z'].values,ids = df_normal_gt['id'].values,text = df_normal_gt['id'].values,
        hoverinfo = 'text',
        marker = dict( size=8, color='cyan', line=dict(width=2,color='DarkSlateGrey'))
    )
    split_gt = dict(mode = "markers",name = "Split",type = "scatter3d",opacity = 1,
        x = df_split_gt['x'].values,y = df_split_gt['y'].values,z = df_split_gt['z'].values,ids = df_split_gt['id'].values,text = df_split_gt['id'].values,
        hoverinfo = 'text',
        marker = dict( size=8, color='#F9A913', line=dict(width=2,color='DarkSlateGrey'))
    )
    uncl_gt = dict(mode = "markers",name = "Unclassified",type = "scatter3d",opacity = 1,
        x = df_uncl_gt['x'].values,y = df_uncl_gt['y'].values,z = df_uncl_gt['z'].values,ids = df_uncl_gt['id'].values,text = df_uncl_gt['id'].values,
        hoverinfo = 'text',
        marker = dict( size=8, color='red', line=dict(width=2,color='DarkSlateGrey'))
    )
    rest_gt = dict(mode = "markers",name = "Unlabeled",type = "scatter3d",opacity = 1,
        x = df_rest_gt['x'].values,y = df_rest_gt['y'].values,z = df_rest_gt['z'].values,ids = df_rest_gt['id'].values,text = df_rest_gt['id'].values,
        hoverinfo = 'text',
        marker = dict( size=8, color='blue', line=dict(width=2,color='DarkSlateGrey'))
    )
    fig_ground_truth = dict( data=[TARGET,normal_gt,split_gt,uncl_gt,rest_gt], layout=layout4)
    # fig_ground_truth['layout'].update_layout(
    #     title={
    #             'text': "Ground Truth",
    #             'y':0.9,
    #             'x':0.5,
    #             'xanchor': 'center',
    #             'yanchor': 'top',
    #             'color': 'white'
    #         }
    # )

    graph_egm = render_egm3(active_cell['row_id'], df) if active_cell is not None else render_egm3(1, df)

    # return data, columns, fig_timings, fig_voltage
    print('- active_cell: ', active_cell)

    return (
            fig_timings, # Graph 1
            fig_voltage, # Graph 2
            fig_predictions, # Graph 3
            fig_ground_truth, # Graph 4
            count_nor_pred, txt_perc_nor, value_perc_nor, #txt_perc_nor, # Stats Widget 1
            txt_count_spl, txt_perc_spl, value_perc_spl, #txt_perc_spl, # Stats Widget 2
            txt_count_unc, txt_perc_unc, value_perc_unc, #txt_perc_unc, # Stats Widget 3
            txt_count_non, txt_perc_non, value_perc_non, #txt_perc_non, # Stats Widget 4
            graph_egm # # Graph 5
            ) 

############
# Workflow 4 - Shared relayoutData across 3d Graphs
############
@app.callback(
    [
        Output('datatable', 'style_data_conditional'),
        Output('value_review', 'children'),
    ],
    [
        Input('datatable', 'active_cell'),
    ]
)
def highlight_row(active_cell):
    if active_cell is not None:
        return [{
            "if": {"row_index": active_cell['row']},
            "backgroundColor": "teal",
            'color': 'white'
        }], str(active_cell['row_id'])
    else:
        return None, 1

# Main
if __name__ == "__main__":
    app.run_server(debug=True)

