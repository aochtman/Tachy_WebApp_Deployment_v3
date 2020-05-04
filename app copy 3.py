# Import required libraries
import copy
import pathlib
import dash
from dash.dependencies import Input, Output, State, ClientsideFunction
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import dash_bootstrap_components as dbc
import json # can be removed later

# Database controller
import sys
# # insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, 'E:/Data/Dropbox/BII Graduation Internship/2. Dash')
from DataController_2 import *

# Database Connection
# db = DatabaseController('root','','tachy','localhost')
# db = DatabaseController('b59b25a8f483fb','df9f008b','heroku_59f0bb8d5ef8c3d','us-cdbr-iron-east-05.cleardb.net') # Heroku DB

# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()

app = dash.Dash(
    __name__, 
    external_stylesheets = [dbc.themes.BOOTSTRAP], 
    meta_tags=[{"name": "viewport", "content": "width=device-width"}], 
    show_undo_redo=True # undo redo left bottom corner button
)
server = app.server
app.title = "Tachy"

# Create app layout
app.layout = html.Div(
    [
        dcc.Store(id="aggregate_data"),
        # empty Div to trigger javascript file for graph resizing
        html.Div(id="output-clientside"),

        # Upper bar
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
                                html.H5(
                                    "Welcome dr. Eric", style={"margin-top": "0px"}
                                ),
                            ]
                        )
                    ],
                    className="col",
                    id="title",
                ),
                html.Div(
                    [
                        dbc.Button("Log Out", outline=True, color="danger", className="ml-4"),
                        # html.A(
                        #     html.Button("Log Out", id="learn-more-button"),
                        #     href="#",
                        # )
                    ],
                    className="col-md-auto",
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
                    className="pretty_container load case",
                    id="cross-filter-options",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div([
                                    # dcc.Markdown("""
                                    #     **Zoom and Relayout Data**

                                    #     Click and drag on the graph to zoom or click on the zoom
                                    #     buttons in the graph's menu bar.
                                    #     Clicking on legend items will also fire
                                    #     this event.
                                    # """),
                                    # html.Pre(id='relayout-data'),
                                    html.P("RelayoutData here", id="relayout-data")
                                ], className='mini_container'),
                                html.Div(
                                    [
                                        html.H6("No. of Predicted Signals", id="gasText", className="well"), 
                                        html.P("233 / 234", className="test"),
                                        dbc.Progress("99%", value=99, style={"height": "20px", "margin":"-8px 4px 0px 4px", 'font-size':'14px'})
                                    ],id="gas",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6("Wrong Predictions", id="oilText", className="well"), html.P("30 / 233 (14%)", className="test")],
                                    id="oil",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6("No. of Manual Review",id="waterText", className="well"), html.P("3 / 30 (10%)", className="test")],
                                    id="water",
                                    className="mini_container",
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
                                    'max-width': '70px',
                                    'fontWeight': 'bold',
                                    'textAlign': 'center'},
                                {'if': {'column_id': 'Predicted'},
                                    'max-width': '70px',
                                    'fontWeight': 'bold',
                                    'textAlign': 'center'},
                                {'if': {'column_id': 'Pattern'},
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
                                'maxHeight': '700px'
                                },
                            page_size=10000,
                            sort_action='native',
                        )
                    ],
                    className="pretty_container table",
                ),
                html.Div(
                    [   
                        html.H6("Review", className="well"),
                        html.Br(),
                        html.Label("Targeted Signal ID: 1234", id="label_target"),
                        dcc.RadioItems(
                            options=[
                                {'label': '   None', 'value': 'none'},
                                {'label': '   Normal', 'value': 'normal'},
                                {'label': '   Split', 'value': 'split'},
                                {'label': '   Unclassified', 'value': 'unclassified'},
                            ],
                            value='none',
                            id="radio_review"
                        ),
                        html.Br(),
                        dbc.Button("Save", color="primary", block=True),
                    ],
                    className="pretty_container annotation",
                ),
                # Main Graph
                html.Div(
                    [
                        dcc.Tabs(id='tabs-example', value='tab-4', children=[
                            dcc.Tab(label='EGM Graphs', value='tab-1', className="myTab", selected_className="myTab2", children=[dcc.Graph(id="graph_egm",style={'height': '920px', 'width':'100%'})]),
                            dcc.Tab(label='Model Timings', value='tab-2', className="myTab", selected_className="myTab2", children=[dcc.Graph(id="graph_timings",style={'height': '920px', 'width':'100%'})]),
                            dcc.Tab(label='Model Voltage', value='tab-3', className="myTab", selected_className="myTab2", children=[dcc.Graph(id="graph_voltage",style={'height': '920px', 'width':'100%'})]),
                            dcc.Tab(label='Model Classes', value='tab-4', className="myTab", selected_className="myTab2", children=[dcc.Graph(id="graph_classes",style={'height': '920px', 'width':'100%'})]),
                        ]),
                        html.Div(id='tabs-example-content')
                    ],
                    className="pretty_container egm graph",
                ),
            ],
            className="row flex-display",
        ),
        # END

    

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
    return case_options, value

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
    df.rename(columns={'id':'ID','label':'GT','label_algorithm':'Predicted','pattern':'Pattern'}, inplace=True)
    data = df.to_dict('records')
    # print(df.columns)
    # columns = [{"name": i, "id": i} for i in df[['id','label', 'label_algorithm','pattern']]]

    columns = [{"name": i, "id": i} for i in df[['ID','GT', 'Predicted','Pattern']]]
    active_cell = {'row': 0, 'column': 0, 'column_id': 'label', 'row_id': 1}
    selected_cells = [
            {'row': 0, 'column': 0, 'column_id': 'ID', 'row_id': 1}, 
            {'row': 0, 'column': 1, 'column_id': 'GT', 'row_id': 1}, 
            {'row': 0, 'column': 2, 'column_id': 'Predicted', 'row_id': 1}, 
            {'row': 0, 'column': 3, 'column_id': 'Pattern', 'row_id': 1}
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
        Output('graph_classes', 'figure'), # 3. Graph Voltage
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
    print('\n\nCTX: ', trigger_id)


    caseid = value
    if value is None:
        caseid = "21_34_08"
    db = DatabaseController('root','','tachy','localhost')
    sql = "SELECT * FROM data WHERE caseid='{}';".format(caseid)
    df = db.pd_read_sql(sql)

    if trigger_id == "dropdown_case":
        target = df.loc[0:0]
    else:
        list_ids = []
        for i in selected_cells:
            list_ids.append(i["row_id"])
        target = df.loc[list_ids]

    # STATISTICS
    

    
    
    print('\nselected_cells: ', selected_cells)

    for i in selected_cells:
        list_ids.append(i["row_id"])
    print('\nselected_cells row ids: ', list_ids)
    print('\nStart Cell: ', start_cell)
    print('\nEnd Cell: ', end_cell)
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
    TARGET = dict(
        mode = "markers",
        name = "TARGET",
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
    fig_timings = dict( data=[TARGET,allpoints_timings], layout=layout)

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
    fig_voltage = dict( data=[TARGET,allpoints_voltage], layout=layout)

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
    fig_classes = dict( data=[normal,split,uncl,rest,TARGET], layout=layout)


    # return data, columns, fig_timings, fig_voltage
    return fig_timings, fig_voltage, fig_classes

########################################################################################################################################################
# END CALLBACKS
########################################################################################################################################################


# Main
if __name__ == "__main__":
    app.run_server(debug=True)

