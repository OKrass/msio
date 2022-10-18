import dash_html_components as html
import dash_core_components as dcc
import dash
import dash_daq as daq
import plotly.graph_objs as go
import dash_table as dte
from dash.dependencies import Input, Output, State
from numpy import random
import pandas as pd
import base64
import io
import datetime
import numpy as np
from sklearn.preprocessing import StandardScaler
import scipy
import math
import plotly.figure_factory as ff
import copy
import urllib.parse
from statsmodels.tsa.stattools import adfuller

app = dash.Dash(__name__)
server = app.server

df = None
df_reset = None
tmp_df = None
df_before_changing = None
colors = {}
normalize_min_max = {}
is_normalized = False
was_changed = False
decreased_count = 0
dist_names = ['uniform','t','triang','weibull_min','weibull_max','rayleigh','pareto', 'norm',
              'logistic','laplace','gompertz','gamma','f',
              'expon','chi2','beta','cauchy']
theme =  {
    'dark': False,
    'dark_color': '#E0E0E0',
    'light_color': 'black',
    'graph_background':'#303030',
    'button_background':'#303030'
}

rootLayout = html.Div([
        #body
        html.Div(id='body',
    children=[
            # left body
            html.Div([
                # time series diagram
                # html.Div([
                    html.Div([
                        html.H4("SELECT DATA TO DRAW AND EXAMINE"),
                        html.Div(id='dropdown_column_div', children=[
                            dcc.Dropdown(
                                id="dropdown_columns",
                                multi=True,
                                style={'background-color': theme['dark_color']},
                            ),]),
                        html.Div([
                            html.Button('ADD', id='draw_btn', n_clicks=0, style={'margin-top': '10px', 'margin-bottom': '10px','background-color': theme['button_background'],
                                        'color': theme['dark_color']}),
                            html.Button('RESTORE TO THE FIRST VERSION OF THE DATA', id='reset_btn', n_clicks=0, style={'float': 'right', 'margin-left': '15px','margin-top': '10px', 'margin-bottom': '10px','background-color': theme['button_background'],
                                                                'color': theme['dark_color']}),
                        ]),
                        dcc.Graph(
                            id='output-graph',
                            figure={'layout': {'clickmode': 'event+select',
                                               'plot_bgcolor': theme['light_color'],
                                               'paper_bgcolor': theme['graph_background'],
                                                'font':{"color": "#E0E0E0"}}},
                        ),],
                        style={
                        'border': 'solid 1px #A2B1C6',
                        'border-radius': '5px',
                        'padding': '20px',
                        'margin-bottom': '15px',
                        'margin-top': '5px',
                        'margin-left': '5px',
                    }),
                    html.Div(
                    [
                        html.Div(
                        [
                            html.H4("CHANGE GRAPH COLOR"),
                            html.Div(id='change_color_div', children=[
                                dcc.Dropdown(
                                    id="dropdown_colors",
                                    style={
                                        'margin-bottom': '20px',
                                        'background-color': theme['dark_color']
                                    },
                                ),
                            ]),
                            daq.ColorPicker(
                                    id='graph-color-picker',
                                    label='Color Picker',
                                    value=dict(hex='#119DFF')
                                ),
                            html.Div(
                                [
                                    html.Button('CHANGE COLOR', id='change_color_btn', n_clicks=0, style={'background-color': theme['button_background'],
                                    'color': theme['dark_color']}),
                                ],
                                style={
                                    'margin-top': '20px',
                                    'text-align': 'center'
                                }
                            ),
                        ],
                            style = {
                            'width': '350px',
                            'height': '500px',
                            'float': 'left',
                            'border': 'solid 1px #A2B1C6',
                            'border-radius': '5px',
                            'text-align': 'center',
                            'padding': '20px',
                            'margin-top': '15px',
                            'margin-right': '15px',
                            'box-sizing':'border-box'
                            }
                        ),
                        html.Div(
                            [
                                html.H4("NORMALIZE DATA"),
                                dcc.Dropdown(
                                    id="dropdown_normalize",
                                    style={
                                        # 'margin-bottom': '20px',
                                        # 'margin-left': '20px',
                                        # 'margin-right': '20px',
                                        # 'width': '50%',
                                        # 'text-align': 'center'
                                        # 'float':'left',
                                        'width': '100%',
                                        # 'display': 'flex',
                                        'align-items': 'center',
                                        'justify-content': 'center',
                                        'margin': 'auto',
                                        'background-color': theme['dark_color'],
                                    },
                                ),
                                html.Div(
                                [
                                    html.Div(
                                    [
                                        html.Label('Min Value'),
                                        dcc.Input(id='normalize_min', type='number', value=0, style={'display': 'inline-block', 'margin-top': '10px','background-color': theme['button_background'], 'color': theme['dark_color']}),
                                    ],),

                                    html.Div(
                                    [
                                        html.Label('Max Value'),
                                        dcc.Input(id='normalize_max', type='number', value=1, style={'display': 'inline-block', 'margin-top': '10px','background-color': theme['button_background'], 'color': theme['dark_color']}),
                                    ],),

                                    html.Div(
                                    [
                                        html.Button('SAVE', id='save_normalize_btn', n_clicks=0, style={'margin-top': '10px','background-color': theme['button_background'],
                                    'color': theme['dark_color']})
                                    ],),

                                    html.Div(
                                    [
                                        html.Button('NORMALIZE', id='normalize_btn', n_clicks=0, style={'margin-top': '80px','background-color': theme['button_background'],
                                    'color': theme['dark_color']}),
                                    ],),

                                    html.Div(
                                    [
                                        html.Button('DENORMALIZE', id='denormalize_btn', n_clicks=0, style={'margin-top': '10px','background-color': theme['button_background'],
                                    'color': theme['dark_color']})
                                    ],),

                                ],
                                style={
                                    'margin': 'auto'
                                }),


                            ],
                            style={
                                'width': '350px',
                                'height': '500px',
                                'float':'left',
                                'text-align': 'center',
                                'border': 'solid 1px #A2B1C6',
                                'border-radius': '5px',
                                'padding': '20px',
                                'margin-top': '15px',
                                'margin-right': '15px',
                                'box-sizing':'border-box'
                            }

                        ),

                        html.Div([
                            html.H4("MODIFY DATA"),
                            html.Div(
                            [
                                html.Button('CLEAN UP DATA (IQR METHOD)', id='IQR_btn', n_clicks=0, style={'box-sizing':'border-box', 'display': 'inline-block','background-color': theme['button_background'],
                                    'color': theme['dark_color']}),
                            ],),

                            html.Div(
                                [
                                    html.Button('SMOOTH TIME SERIES', id='SMOOTH_btn', n_clicks=0,
                                                style={'box-sizing': 'border-box', 'margin-top': '10px',
                                                       'margin-bottom': '20px', 'display': 'inline-block',
                                                       'background-color': theme['button_background'],
                                                       'color': theme['dark_color']}),
                                ], ),

                            html.Div(
                            [
                                html.Div(id='set-delete-leap',
                                         children='set delete leap:'),
                                dcc.Input(
                                            id="decrease_leap", type="number", value=2,
                                            min=2, max=20, step=1,style={'background-color': theme['button_background'], 'color': theme['dark_color']}
                                        ),
                                html.Button('DECREASE NUMBER OF SAMPLES', id='DECREASE_btn', n_clicks=0, style={'box-sizing':'border-box','margin-top': '5px', 'display': 'inline-block','background-color': theme['button_background'],
                                    'color': theme['dark_color']}),
                                html.Div(id='decreasing-information',
                                         children='the number of time series samples has not been reduced', style={'padding': '5px'})

                            ],style={
                                'border': 'solid 1px #A2B1C6',
                                'border-radius': '5px',
                            } ),


                            html.Div(
                                [
                                    html.Button('NORMALIZE 0-1', id='normalize_2_btn', n_clicks=0,
                                                style={'box-sizing': 'border-box', 'margin-top': '10px',
                                                       'display': 'inline-block',
                                                       'background-color': theme['button_background'],
                                                       'color': theme['dark_color']}),
                                ], ),
                            html.Div(
                                [
                                    html.Button('UNDO ABOVE OPERATIONS', id='UNDO_btn', n_clicks=0,
                                                style={'box-sizing': 'border-box', 'margin-top': '10px',
                                                       'display': 'inline-block',
                                                       'background-color': theme['button_background'],
                                                       'color': theme['dark_color']}),
                                ], ),
                        ],
                        style={
                                # 'display': 'inline-block',
                                # 'margin': '0 auto',
                                #'position': 'absolute',
                                #'left': '50%',
                                'width': '350px',
                                'height': '500px',
                                'float':'left',
                                'text-align': 'center',
                                'border': 'solid 1px #A2B1C6',
                                'border-radius': '5px',
                                'padding': '20px',
                                'margin-top': '15px',
                                'box-sizing': 'border-box',
                        }
                        ),
                    ],
                    style={

                        # 'display': 'flex',
                        'overflow': 'hidden',
                        'border': 'solid 1px #A2B1C6',
                        'border-radius': '5px',
                        'padding': '20px',
                        'margin-left': '5px'
                    }),
                    html.Div([
                        html.H4("SELECT TIME SERIES AND FILTER DATE TO MEASURE STATISTICAL PROPERTIES"),
                        dcc.Dropdown(
                            id="dropdown_statistics",
                            style={
                                    'margin-bottom': '20px',
                                    'background-color': theme['dark_color'],
                                    'color': theme['light_color'],
                                },
                        ),
                        dcc.RangeSlider(
                            id="date_slider",
                        ),
                        html.Div(
                            [
                                html.Div([
                                    html.H6("SELECT YEARS"),
                                    dcc.Dropdown(
                                        id="dropdown_years",
                                        multi=True,
                                        placeholder="all years",
                                        style={
                                        'background-color': theme['dark_color'],}
                                    ),
                                ],
                                    style={
                                        'width': '100%',
                                        'margin-right': '5px',
                                    },
                                ),

                                html.Div([
                                    html.H6("SELECT MONTHS"),
                                    dcc.Dropdown(
                                        id="dropdown_months",
                                        multi=True,
                                        placeholder="all months",
                                        options=[({'label': x[0], 'value': x[1]}) for x in [['Jan.',1],['Feb.',2],['Mar.',3],['Apr.',4],['May',5],['Jun.',6],
                                                                                      ['Jul.',7],['Aug.',8],['Sep.',9],['Oct.',10],['Nov.',11],['Dec.',12]]],
                                        style={
                                            'background-color': theme['dark_color'],}
                                    ),
                                ],
                                    style={
                                        'width': '100%',
                                        'margin-right': '5px',
                                    },
                                ),

                                html.Div([
                                    html.H6("SELECT DAYS"),
                                    dcc.Dropdown(
                                        id="dropdown_days",
                                        multi=True,
                                        placeholder="all days",
                                        options=[({'label': x, 'value': x}) for x in range(1,32)],
                                        style={
                                            'background-color': theme['dark_color'],
                                            'color': theme['light_color'],}
                                    ),
                                ],
                                    style={
                                        'width': '100%',
                                        'margin-right': '5px',
                                    },
                                ),

                                html.Div([
                                    html.H6("SELECT DAYS OF WEEK"),
                                    dcc.Dropdown(
                                        id="dropdown_days_of_week",
                                        multi=True,
                                        placeholder="all days",
                                        options=[({'label': x[0], 'value': x[1]}) for x in [['Monday',0],['Tuesday',1],['Wednesday',2],['Thursday',3]
                                        ,['Friday',4],['Saturday',5],['Sunday',6]]],
                                        style={
                                            'background-color': theme['dark_color'],
                                            'color': theme['light_color'], }
                                    ),
                                ],
                                    style={
                                        'width': '100%',
                                    },
                                ),
                            ],
                        style={
                            'display': 'flex',
                        }),
                        html.Button('FILTER DATE AND CHECK STATISTICAL PROPERTIES', id='statistics_btn', n_clicks=0, style={'margin-top': '10px','background-color': theme['button_background'],
                                    'color': theme['dark_color']}),
                    ],style={
                        'clear': 'both',
                        'margin-top': '15px',
                        'border': 'solid 1px #A2B1C6',
                        'border-radius': '5px',
                        'padding': '20px',
                        'margin-left': '5px',
                    }),
                # ]),
                # properties of time series
                html.Div([
                    html.H4("TIME SERIES PROPERTIES"),
                    html.H5("SELECTED DATA"),
                    html.Div([
                        dte.DataTable(
                            id='time_series_data',
                            columns=[{"name": "time", "id": "1"},
                                    {"name": "value", "id": "2"}],
                            style_header={'backgroundColor': 'black'},
                            style_cell={
                                'backgroundColor': theme['graph_background'],
                                'color': '#E0E0E0'
                            },
                        ),
                    ], style={'height': '100px', 'overflowY':'scroll'}),

                    html.H5("TIME SERIES BASIC INFORMATION"),
                    dte.DataTable(
                        id='time_series_properties1',
                        columns=[{"name": "starting time", "id": "1"},
                                 {"name": "end time", "id": "2"},
                                 {"name": "time interval [months]", "id": "3"},
                                 {"name": "samples number", "id": "4"}],
                        style_header={'backgroundColor': 'black'},
                        style_cell={
                            'backgroundColor': theme['graph_background'],
                            'color': '#E0E0E0'
                        },
                    ),

                    html.H5("LOCATION MEASURES"),
                    dte.DataTable(
                        id='time_series_properties2_1',
                        columns=[{"name": "max value", "id": "1"},
                                 {"name": "min value", "id": "2"},
                                 {"name": "arithmetic mean", "id": "3"},
                                 {"name": "geometric mean", "id": "4"},
                                 {"name": "harmonic mean", "id": "5"},
                                 {"name": "mode", "id": "6"}],
                        style_header={'backgroundColor': 'black'},
                        style_cell={
                            'backgroundColor': theme['graph_background'],
                            'color': '#E0E0E0'
                        },
                    ),
                    dte.DataTable(
                            id='time_series_properties2_2',
                            columns = [{"name": "percentile 10", "id": "1"},
                                       {"name": "percentile 20", "id": "2"},
                                       {"name": "percentile 30", "id": "3"},
                                       {"name": "percentile 40", "id": "4"},
                                       {"name": "percentile 50", "id": "5"},
                                       ],
                        style_header={'backgroundColor': 'black'},
                        style_cell={
                            'backgroundColor': theme['graph_background'],
                            'color': '#E0E0E0'
                        },
                    ),
                    dte.DataTable(
                            id='time_series_properties2_3',
                            columns=[{"name": "percentile 60", "id": "1"},
                                     {"name": "percentile 70", "id": "2"},
                                     {"name": "percentile 80", "id": "3"},
                                     {"name": "percentile 90", "id": "4"},
                                     {"name": "percentile 100", "id": "5"},
                                     ],
                        style_header={'backgroundColor': 'black'},
                        style_cell={
                            'backgroundColor': theme['graph_background'],
                            'color': '#E0E0E0'
                        },
                    ),
                    html.H5("VARIABILITY MEASURES"),
                    dte.DataTable(
                        id='time_series_properties3_1',
                        columns=[{"name": "min-max distance", "id": "1"},
                                 {"name": "quartile deviation", "id": "2"},
                                 {"name": "average absolute deviation", "id": "3"}],
                        style_header={'backgroundColor': 'black'},
                        style_cell={
                            'backgroundColor': theme['graph_background'],
                            'color': '#E0E0E0'
                        },
                    ),
                    dte.DataTable(
                        id='time_series_properties3_2',
                        columns=[{"name": "standard deviation", "id": "1"},
                                 {"name": "variance", "id": "2"},
                                 {"name": "coefficient of variation [0-1]", "id": "3"}],
                        style_header={'backgroundColor': 'black'},
                        style_cell={
                            'backgroundColor': theme['graph_background'],
                            'color': '#E0E0E0'
                        },
                    ),
                    html.H5("ASYMMETRY, FLATTENING AND CONCENTRATION MEASURES"),
                    dte.DataTable(
                        id='time_series_properties4_1',
                        columns=[{"name": "asymmetry coefficient", "id": "1"},
                                 {"name": "third order central moment", "id": "2"}],
                        style_header={'backgroundColor': 'black'},
                        style_cell={
                            'backgroundColor': theme['graph_background'],
                            'color': '#E0E0E0'
                        },
                    ),
                    dte.DataTable(
                        id='time_series_properties4_2',
                        columns=[{"name": "kurtosis", "id": "1"},
                                 {"name": "excess coefficient", "id": "2"},
                                 {"name": "Gini coefficient", "id": "3"}],
                        style_header={'backgroundColor': 'black'},
                        style_cell={
                            'backgroundColor': theme['graph_background'],
                            'color': '#E0E0E0'
                        },
                    ),
                ],style={
                    'margin-top': '15px',
                    'border': 'solid 1px #A2B1C6',
                    'border-radius': '5px',
                    'padding': '20px',
                    'margin-left': '5px',
                }),
                html.Div([
                    html.H5("CORRELATION MATRIX"),
                    dcc.Graph(id='correlation_matrix', figure={'layout': {
                        'clickmode': 'event+select',
                        'plot_bgcolor': theme['light_color'],
                        'paper_bgcolor': theme['graph_background'],
                        'font':{"color": "#E0E0E0"}
                }})],style={
                    'margin-top': '15px',
                    'border': 'solid 1px #A2B1C6',
                    'border-radius': '5px',
                    'padding': '20px',
                    'margin-left': '5px',
                }),
                html.Div([
                    html.H5("SELECT TYPE OF DIAGRAM"),
                    dcc.Dropdown(
                        id="box_violin_dropdown",
                        placeholder="select type of diagram",
                        options=[
                                {'label': 'boxplot', 'value': 'boxplot'},
                                {'label': 'violinplot', 'value': 'violinplot'},
                            ],
                        style={
                            'background-color': theme['dark_color'],
                            'color': theme['light_color'],
                        },
                        value='boxplot'
                    ),
                    html.Br(),
                    dcc.Graph(id='violin_box_graph', figure={'layout': {
                        'clickmode': 'event+select',
                        'plot_bgcolor': theme['light_color'],
                        'paper_bgcolor': theme['graph_background'],
                        'font':{"color": "#E0E0E0"}
                    }}),
                ],style={
                    'margin-top': '15px',
                    'border': 'solid 1px #A2B1C6',
                    'border-radius': '5px',
                    'padding': '20px',
                    'margin-left': '5px',
                }),
                html.Div([
                    html.H4("GENERATE REPORT"),
                    html.Div(
                        [
                            html.Div([
                                html.H6("SELECT COLUMNS"),
                                dcc.Dropdown(
                                    id="dropdown_columns_statistics",
                                    multi=True,
                                    style={
                                        'background-color': theme['dark_color'],
                                        'color': theme['light_color'],
                                    }
                                ),
                            ],
                                style={
                                    'width': '20%',
                                    'margin-right': '5px'
                                },
                            ),

                            html.Div([
                                html.H6("SELECT PROPERTIES"),
                                dcc.Dropdown(
                                    id="dropdown_property",
                                    multi=True,
                                    options=[({'label': x[0], 'value': x[1]}) for x in
                                             [['starting time', 1],['end time', 2],['time interval [months]', 3], ['samples_number', 4],
                                              ['max value', 5],['min value', 6],
                                              ['arithmetic mean', 7], ['geometric mean', 8], ['harmonic mean', 9], ['mode', 10],
                                              ['percentile 10', 11],['percentile 20', 12],['percentile 30', 13],['percentile 40', 14],
                                              ['percentile 50', 15],['percentile 60', 16],['percentile 70', 17],['percentile 80', 18],
                                              ['percentile 90', 19],['percentile 100', 20],['min-max distance', 21],
                                              ['quartile deviation', 22], ['average absolute deviation', 23], ['standard deviation', 24],
                                              ['variance', 25], ['coefficient of variation', 26],['asymmetry coefficient', 27],
                                              ['third order central moment', 28], ['kurtosis', 29], ['excess coefficient', 30], ['Gini coefficient', 31]]],
                                    value=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31],
                                    style={
                                        'background-color': theme['dark_color'],
                                        'color': theme['light_color'],
                                    }
                                ),
                            ],
                                style={
                                    'width': '100%',
                                    'margin-right': '5px'
                                },
                            ),
                        ],
                        style={
                            'display': 'flex',
                        }),

                    html.Div(
                        [
                            html.Button('Save columns and properties, generate report', id='report_btn', n_clicks=0, style={'margin-top': '10px','background-color': theme['button_background'],
                                    'color': theme['dark_color']}),
                            html.Div(id = "download_div", children=[html.A(
                                'Download Report',
                                id='download-link',
                                download="statistical_properties.csv",
                                href="",
                                target="_blank"
                                )], style={'display': 'none', 'margin-top': '10px', 'margin-left': '10px'})
                        ],
                    style={
                        'display': 'flex',
                    })
                ],
                    style={
                    'margin-top': '15px',
                    'border': 'solid 1px #A2B1C6',
                    'border-radius': '5px',
                    'padding': '20px',
                    'margin-left': '5px',
                    'margin-bottom': '5px',
                })

            ],
            style = {
                'width': '65%',
            }),
            # right body
            html.Div([
                html.Div([
                # example data
                    html.Div([
                        html.H4('CHOOSE EXAMPLE TIME SERIES DATA'),
                        dcc.Dropdown(
                            id='dropdown_example',
                            options=[
                                {'label': 'forestry', 'value': '_forestry.csv'},
                                {'label': 'sea_ice', 'value': 'sea_ice.csv'},
                                {'label': 'births', 'value': '_births.csv'},
                                {'label': 'white_noise', 'value': 'example_white_noise.csv'},
                                {'label': 'many_columns', 'value': 'multiple_columns.csv'}
                            ],
                            value='_forestry.csv',
                            style={
                                'background-color': theme['dark_color'],
                                'color': theme['light_color'],
                            }
                        ),
                    ]),
                    # load data
                    html.Div([
                        # upload place
                        html.Div([
                            html.H4("UPLOAD YOUR TIME SERIES DATA IN CSV FILE"),
                                dcc.Upload(
                                id='upload-data',
                                children=html.Div([
                                    'UPLOAD'
                                ]),
                                style={
                                    'width': '60%',
                                    'height': '200px',
                                    'lineHeight': '60px',
                                    'borderWidth': '1px',
                                    'borderStyle': 'dashed',
                                    'borderRadius': '5px',
                                    'textAlign': 'center',
                                    'margin': '10px'
                                },
                                multiple=False),
                        ]),
                        # example
                        html.Div([
                            html.H4('EXAMPLE CSV FILE TO GET FAMILIAR WITH THE FORMAT'),
                            html.Div(id="example_csv", children=[html.A(
                                'DOWNLOAD EXAMPLE FILE WITH PROPER DATA FORMAT',
                                id='download-example',
                                download="example.csv",
                                href="",
                                target="_blank"
                            )], style={'margin-top': '10px'})
                        ],style={'margin-left':'15px'}),
                    ],
                    style = {
                        'display':'flex',
                    }),
                    ],
                style={
                    'border': 'solid 1px #A2B1C6',
                    'border-radius': '5px',
                    'padding': '20px',
                    'margin-right': '5px',
                    'margin-top': '5px',
                }),
                # wrong samples
                html.Div([
                    html.H4("CLICK ON THE TIME SERIES GRAPH TO MARK WRONG SAMPLES AND EDIT DATA (COLUMN 'VALUE' IS EDITABLE)"),
                    dte.DataTable(
                        id='wrong_samples_table',
                        row_deletable=True,
                        columns=[{"name": "name", "id": "1",},
                                 {"name": "time", "id": "2",},
                                 {"name": "value", "id": "3"}],
                        style_header={'backgroundColor': 'black'},
                        style_cell={
                            'backgroundColor': theme['graph_background'],
                            'color': '#E0E0E0'
                        },
                    ),
                    html.Button('COMMIT CHANGES', id='correct_data_btn', n_clicks=0, style={'margin-top': '10px','background-color': theme['button_background'],
                                    'color': theme['dark_color']}),
                ],
                style={
                    'margin-top':'15px',
                    'border': 'solid 1px #A2B1C6',
                    'border-radius': '5px',
                    'padding': '20px',
                    'margin-right': '5px',
                }),
                # is_stationary
                html.Div([
                    html.H4("CHOOSE TIME SERIES AND PRESS THE BUTTON BELLOW TO CHECK STATIONARITY"),
                    dcc.Dropdown(
                        id="dropdown_stationary",
                        style={
                            'margin-bottom': '20px',
                            'background-color': theme['dark_color'],
                            'color': theme['light_color'],
                        },
                    ),
                    html.Button('CHECK STATIONARITY', id='is_stationary_btn', n_clicks=0, style={'background-color': theme['button_background'],
                                    'color': theme['dark_color']}),
                    # dcc.Loading(id="loading-1", fullscreen=True, children=[html.H4(id='is_stationary_text_area', style={'whiteSpace': 'pre-line'},)]),
                    html.H4(id='is_stationary_text_area', style={'whiteSpace': 'pre-line'}),
                    html.Br()
                ],
                style={
                    'margin-top':'15px',
                    'border': 'solid 1px #A2B1C6',
                    'border-radius': '5px',
                    'padding': '20px',
                    'margin-right': '5px',
                }),
                # distribution determination
                html.Div([
                    html.H4("CHOOSE TIME SERIES AND PRESS THE BUTTON BELLOW TO FIT DISTRIBUTION AND PARAMETERS\n (COMPUTATION MAY TAKE SOME TIME)"),
                    dcc.Dropdown(
                        id="dropdown_distribution",
                        style={
                            'margin-bottom': '20px',
                            'background-color': theme['dark_color'],
                            'color': theme['light_color'],
                        },
                    ),
                    html.Button('CHECK DISTRIBUTION', id='distribution_btn', n_clicks=0, style={'background-color': theme['button_background'],
                                    'color': theme['dark_color']}),
                    # dcc.Loading(id="loading-2", fullscreen=True, children=[html.H4(id='distribution_text_area', style={'whiteSpace': 'pre-line'},)]),
                    html.H4(id='distribution_text_area', style={'whiteSpace': 'pre-line'}),
                    dcc.Link('MORE INFORMATION ABOUT DISTRIBUTION TYPE', href='https://docs.scipy.org/doc/scipy/reference/stats.html'),

                ],
                style={
                    'margin-top':'15px',
                    'border': 'solid 1px #A2B1C6',
                    'border-radius': '5px',
                    'padding': '20px',
                    'margin-right': '5px',
                }),
            ],
            style = {
                'width': '35%',
                'margin-left': '10px'
            })
        ],
        style = {
            'display':'flex',
        }),
        html.Div(id='filtered_df_value', style={'display': 'none'}),

])

app.layout = html.Div(id='dark-theme-provider-demo', children=[
    html.Div([
        html.Div(
            [
                html.Div(
                    [
                        html.H2("THE STATISTICAL ANALYSIS OF TIME SERIES"),
                        html.H6(
                            "This application allows you to load time series and measure it's statistical properties.",
                        ),
                    ]),

                html.Div(
                    [
                        daq.ToggleSwitch(
                            id='toggle-theme',
                            label=['Light', 'Dark'],
                            value=False
                        )],
                    style={
                        'margin-left': 'auto',
                        'margin-top': '5px',
                    }),

            ],
            style={
                'display': 'flex',
            }
        ),
        html.Div(
            id='dark-theme-component-demo',
            children=[
                daq.DarkThemeProvider(theme=theme, children=
                                      rootLayout)
            ],style={'background-color': '#E0E0E0', 'color': 'black'},
        )
    ], style={'margin-left':'5px','margin-right':'5px'})
],style={'background-color': '#303030', 'color': '#C0C0C0'})

@app.callback(
    Output('dark-theme-component-demo', 'children'),
    [Input('toggle-theme', 'value')]
)
def turn_dark(dark_theme):
    if(dark_theme):
        theme.update(
            dark=True,
            dark_color='C0C0C0',
        )
    else:
        theme.update(
            dark=False,
            dark_color='FFFFFF',
        )
    return daq.DarkThemeProvider(theme=theme, children=
                                 rootLayout)

@app.callback(
    [Output('dark-theme-component-demo', 'style'),
     Output('body','style')],
    [Input('toggle-theme', 'value')],
    [State('dark-theme-component-demo', 'style'),
     State('body','style'),
     State('dropdown_columns','style')],
)
def change_bg(value,style1,style2,style3):
    ctx = dash.callback_context
    if ctx.triggered[0]['prop_id'] == 'toggle-theme.value':
        if value:
            return {'background-color': '#303030', 'color': '#C0C0C0'},{'color': '#C0C0C0','display':'flex'}
        else:
            return {'background-color': '#E0E0E0', 'color': 'black'},{'color': 'black','display':'flex'}
    else:
        return style1,style2

@app.callback(
    [Output('date_slider', 'min'),
    Output('date_slider', 'max'),
    Output('date_slider', 'marks'),
    Output('date_slider', 'value')],
    [Input('draw_btn', 'n_clicks')])
def update_dropdown(n_clicks):
    global df
    ctx = dash.callback_context
    try:
        if ctx.triggered[0]['prop_id'] == 'draw_btn.n_clicks' and df is not None:
            date = pd.DataFrame()
            date['dt'] = [pd.to_datetime(x,format='%Y-%m-%d %H:%M:%S')for x in df.time]
            date['y'] = [x.year for x in date['dt']]

            min = date['y'].tolist()[0]
            max = date['y'].tolist()[-1]

            quarter = date['y'].tolist()[int(len(date['y'].tolist())/4)]
            mid = date['y'].tolist()[int(len(date['y'].tolist())/2)]
            three_fourth = date['y'].tolist()[int(3*len(date['y'].tolist())/4)]

            marks = {
                min: {'label': str(min)},
                max: {'label': str(max)},
                quarter: {'label': str(quarter)},
                mid: {'label': str(mid)},
                three_fourth: {'label': str(three_fourth)},
            }

            value = [min, max]

            return min,max,marks,value
        else:
            return None,None,{},[]
    except:
        return None, None, {}, []

@app.callback(
    [Output('dropdown_years', 'options'),
     Output('dropdown_years', 'value')],
    [Input('date_slider', 'value')],
    [State('dropdown_years', 'options')])
def update_dropdown(value, current_options):
    try:
        ctx = dash.callback_context

        if ctx.triggered[0]['prop_id'] == 'date_slider.value' and len(value) == 2:
            options = []
            options += ({'label': x, 'value': x} for x in range(value[0], value[1]+1))
            return options, None
        return [], None
    except:
        return [], None

@app.callback([Output('wrong_samples_table', 'data'),
              Output('wrong_samples_table', 'columns')],
              [Input('output-graph', 'clickData'),
               Input('upload-data', 'contents'),
               Input('dropdown_example', 'value'),
               Input('normalize_btn', 'n_clicks'),
               Input('denormalize_btn', 'n_clicks')],
              [State('wrong_samples_table', 'data'),
               State('output-graph', 'figure'),
               State('wrong_samples_table', 'columns'),
               State('dropdown_columns', 'value')])
def display_click_data(clickData, contents, value, n_clicks1, n_clicks2, rows, figure, current_columns, _value):
    try:
        ctx = dash.callback_context
        x = '1'
        y = '2'
        z = '3'
        if ctx.triggered[0]['prop_id'] == 'normalize_btn.n_clicks':
            return [], [{"name": "name", "id": "1"}, {"name": "time", "id": "2"},
                        {"name": "value", "id": "3", 'editable': True}]
        if ctx.triggered[0]['prop_id'] == 'denormalize_btn.n_clicks':
            return [], [{"name": "name", "id": "1"}, {"name": "time", "id": "2"},
                        {"name": "value", "id": "3", 'editable': True}]
        if ctx.triggered[0]['prop_id'] == 'upload-data.contents' or (ctx.triggered[0]['prop_id'] == 'dropdown_example.value' and value is not None):
            return [], [{"name": "name", "id": "1"},{"name": "time", "id": "2"},{"name": "value", "id": "3", 'editable': True}]
        if ctx.triggered[0]['prop_id'] == 'output-graph.clickData':
            if rows is None:
                rows = {}
            for i in range (len(clickData['points'])):
                if not rows.__contains__({x:figure['data'][i]['name'], y:clickData['points'][i]['x'], z:clickData['points'][i]['y']}):
                    rows.append({x:figure['data'][i]['name'], y:clickData['points'][i]['x'], z:clickData['points'][i]['y']})
            return rows, [{"name": "name", "id": "1"},{"name": "time", "id": "2"},{"name": "value", "id": "3", 'editable': True}]
        else:
            return [], [{"name": "name", "id": "1"},{"name": "time", "id": "2"},{"name": "value", "id": "3", 'editable': True}]
    except:
        return [], [{"name": "name", "id": "1"}, {"name": "time", "id": "2"},
                    {"name": "value", "id": "3", 'editable': True}]

@app.callback(
    [Output('correlation_matrix', 'figure'),
     Output('time_series_properties1','data'),
     Output('time_series_properties2_1','data'),
     Output('time_series_properties2_2','data'),
     Output('time_series_properties2_3','data'),
     Output('time_series_properties3_1','data'),
     Output('time_series_properties3_2','data'),
     Output('time_series_properties4_1','data'),
     Output('time_series_properties4_2','data'),
     Output('time_series_data','data'),
     Output('filtered_df_value', 'children')],
    [Input('statistics_btn', 'n_clicks'),
     Input('upload-data', 'contents'),
     Input('upload-data', 'filename'),
     Input('dropdown_example', 'value')],
    [State('dropdown_statistics', 'value'),
     State('dropdown_years', 'value'),
     State('dropdown_months', 'value'),
     State('dropdown_days', 'value'),
     State('dropdown_days_of_week', 'value'),
     State('dropdown_years', 'options'),
     State('dropdown_months', 'options'),
     State('dropdown_days', 'options'),
     State('dropdown_days_of_week', 'options'),
     State('dropdown_columns', 'value')
     ]
)
def update_value(n_clicks, content, filename, _value, time_series, v_years, v_months, v_days, v_days_of_week, o_years, o_months, o_days, o_days_of_week, dropdown_columns):
    global df
    ctx = dash.callback_context

    if ctx.triggered[0]['prop_id'] == 'statistics_btn.n_clicks' and time_series is not None:
        return get_statistical_properties(v_years, v_months, v_days, v_days_of_week, o_years, o_months, o_days, o_days_of_week, time_series, dropdown_columns)

    else:
        return get_figure([], [], "", "", ""), [], [], [], [], [], [], [], [], [], ""


def change_values_when_empty(v_years, v_months, v_days, v_days_of_week, o_years, o_months, o_days, o_days_of_week):
    try:
        if v_years is None:
            v_years = []
            for year in o_years:
                v_years.append(year['value'])
        elif isinstance(v_years, list):
            if len(v_years) == 0:
                for year in o_years:
                    v_years.append(year['value'])

        if v_months is None:
            v_months = []
            for month in o_months:
                v_months.append(month['value'])
        elif isinstance(v_months, list):
            if len(v_months) == 0:
                for month in o_months:
                    v_months.append(month['value'])

        if v_days is None:
            v_days = []
            for day in o_days:
                v_days.append(day['value'])
        elif isinstance(v_days, list):
            if len(v_days) == 0:
                for day in o_days:
                    v_days.append(day['value'])

        if v_days_of_week is None:
            v_days_of_week = []
            for day in o_days_of_week:
                v_days_of_week.append(day['value'])
        elif isinstance(v_days_of_week, list):
            if len(v_days_of_week) == 0:
                for day in o_days_of_week:
                    v_days_of_week.append(day['value'])

        return v_years, v_months, v_days, v_days_of_week
    except:
        return [],[],[],[]

def get_statistical_properties(v_years, v_months, v_days, v_days_of_week, o_years, o_months, o_days, o_days_of_week, time_series, dropdown_columns):
    global df
    filtered_df = None
    rows1 = []
    rows2_1 = []
    rows2_2 = []
    rows2_3 = []
    rows3_1 = []
    rows3_2 = []
    rows4_1 = []
    rows4_2 = []
    try:
        v_years, v_months, v_days, v_days_of_week = change_values_when_empty(v_years, v_months, v_days, v_days_of_week, o_years, o_months, o_days, o_days_of_week)

        local_df = df
        local_df['date'] = [pd.to_datetime(x, format='%Y-%m-%d %H:%M:%S') for x in df.time]
        local_df['years'] = [x.year for x in local_df['date']]
        local_df['months'] = [x.month for x in local_df['date']]
        local_df['days'] = [x.day for x in local_df['date']]
        local_df['days_of_week'] = [x.weekday() for x in local_df['date']]
        filtered_df = local_df[local_df['years'].isin(v_years) & local_df['months'].isin(v_months)\
                        & local_df['days'].isin(v_days) & local_df['days_of_week'].isin(v_days_of_week)]
        t = filtered_df
        k = local_df
        selected_data = []
        for v in filtered_df.iterrows():
            selected_data.append({"1": v[1]['time'], "2": v[1][time_series]})

        data = []
        for v in filtered_df.iterrows():
            if not math.isnan(v[1][time_series]):
                data.append(v[1][time_series])

        interval = get_interval()
        horizon = get_horizon(filtered_df)
        samples_number = get_samples_number(filtered_df)
        kurtosis = get_kurtosis(data)
        skewness = get_skewness(data)
        min_max_distance = get_min_max_distance(data)
        quartile_deviation = get_quartile_deviation(data)
        gmean = get_gmean(data)
        hmean = get_hmean(data)
        max = get_max(data)
        min = get_min(data)
        percentiles = get_percentiles(data)
        std = get_std(data)
        mean = get_mean(data)
        mode = get_mode(data)
        median_absolute_deviation = get_median_absolute_deviation(data)
        variance = get_variance(data)
        coefficient_of_variation = get_coeficient_of_variation(data)
        third_order_central_moment = get_third_order_central_moment(data)
        excess_coef = get_excess_coefficient(data)

        rows1.append({"1": horizon.get("start"), "2": horizon.get("end"), "3": interval, "4": samples_number})
        rows2_1.append({"1": max, "2": min, "3": mean, "4": gmean, "5": hmean, "6": mode})
        rows2_2.append({"1": percentiles['10'], "2": percentiles['20'], "3": percentiles['30'],
                      "4": percentiles['40'], "5": percentiles['50']})
        rows2_3.append({"1": percentiles['60'], "2": percentiles['70'], "3": percentiles['80'],
                      "4": percentiles['90'], "5": percentiles['100']})
        rows3_1.append({"1": min_max_distance, "2": quartile_deviation, "3": median_absolute_deviation})
        rows3_2.append({"1": std, "2": variance, "3": coefficient_of_variation})
        rows4_1.append({"1": skewness, "2": third_order_central_moment})
        rows4_2.append({"1": kurtosis, "2": excess_coef, "3": gini_coefficient(data)})

        filtered_df.drop(columns=['date', 'years', 'months', 'days', 'days_of_week'], axis=1, inplace=True)
        columns = [e for e in filtered_df.columns if e not in dropdown_columns]
        filtered_df.drop(columns=columns, axis=1, inplace=True)

        corrs = filtered_df.corr(method ='pearson')
        values = corrs.values
        values = [["" for i in range(np.size(values,0))] for j in range(np.size(values,1))]


        figure = ff.create_annotated_heatmap(
            z=corrs.values,
            x=list(corrs.columns),
            y=list(corrs.index),
            annotation_text=values,
            showscale=True,

        )
        figure.update_layout(plot_bgcolor=theme['light_color'],
            paper_bgcolor=theme['graph_background'],
            font={"color": "#E0E0E0"})

        return figure, rows1, rows2_1, rows2_2, rows2_3, rows3_1, rows3_2, rows4_1, rows4_2, selected_data, filtered_df.to_json(date_format='iso', orient='split'),
    except:
        return get_figure([], [], "", "", ""),[],[],[],[],[],[],[],[],[],df.to_json(date_format='iso', orient='split')

def get_kurtosis(data):
    try:
        if len(data) == 0:
            return "impossible to measure"
        return scipy.stats.kurtosis(data)+3
    except:
        return "impossible to measure"

def get_skewness(data):
    try:
        if len(data) == 0:
            return "impossible to measure"
        return scipy.stats.skew(data)
    except:
        return "impossible to measure"


def get_mean(data):
    try:
        if len(data) == 0:
            return "impossible to measure"
        return np.mean(data)
    except:
        return "impossible to measure"


def get_mode(data):
    try:
        if len(data) == 0:
            return "impossible to measure"
        return scipy.stats.mode(data, axis=None).mode
    except:
        return "impossible to measure"


def get_median_absolute_deviation(data):
    try:
        if len(data) == 0:
            return "impossible to measure"
        _df = pd.DataFrame(data)
        return _df.mad()
    except:
        return "impossible to measure"


def get_variance(data):
    try:
        if len(data) == 0:
            return "impossible to measure"
        return np.var(data)
    except:
        return "impossible to measure"


def get_coeficient_of_variation(data):
    try:
        if len(data) == 0:
            return "impossible to measure"
        return scipy.stats.variation(data)
    except:
        return "impossible to measure"


def get_third_order_central_moment(data):
    try:
        if len(data) == 0:
            return "impossible to measure"
        return scipy.stats.moment(data, moment=3)
    except:
        return "impossible to measure"


def get_excess_coefficient(data):
    try:
        if len(data) == 0:
            return "impossible to measure"
        return scipy.stats.kurtosis(data)
    except:
        return "impossible to measure"


def gini_coefficient(data):
    try:
        if len(data) == 0:
            return "impossible to measure"
        sorted_data = sorted(data)
        height = 0
        area = 0
        for val in sorted_data:
            height += val
            area += height - val / 2.
        triangle_area = height * len(data) / 2.
        return (triangle_area - area) / triangle_area
    except:
        return "impossible to measure"

def get_std(data):
    try:
        if len(data) == 0:
            return "impossible to measure"
        return np.std(data)
    except:
        return "impossible to measure"


def get_percentiles(data):
    percentiles = {}
    try:
        for x in range(10,110,10):
            percentiles[str(x)] = np.percentile(data, x)
    except:
        for x in range(10,110,10):
            percentiles[str(x)] = "impossible to measure"
    return percentiles



def get_quartile_deviation(data):
    try:
        if len(data) == 0:
            return "impossible to measure"
        return scipy.stats.iqr(data, interpolation = 'midpoint')
    except:
        return "impossible to measure"


def get_max(data):
    try:
        if len(data) == 0:
            return "impossible to measure"
        return max(data)
    except:
        return "impossible to measure"


def get_min(data):
    try:
        if len(data) == 0:
            return "impossible to measure"
        return min(data)
    except:
        return "impossible to measure"


def get_gmean(data):
    try:
        if all(i > 0 for i in data):
            gmean = scipy.stats.gmean(data)
        else:
            gmean = "impossible to measure"
        if math.isnan(gmean):
            return "impossible to measure"
        return gmean

    except:
        return "impossible to measure"


def get_hmean(data):
    try:
        if all(i > 0 for i in data):
            hmean = scipy.stats.hmean(data)
        else:
            hmean = "impossible to measure"
        if math.isnan(hmean):
            return "impossible to measure"
        return hmean

    except:
        return "impossible to measure"


def get_min_max_distance(data):
    try:
        if len(data) == 0:
            return "impossible to measure"
        return max(data) - min(data)
    except:
        return "impossible to measure"


def get_samples_number(filtered_df):
    try:
        return len(filtered_df.values.tolist())
    except:
        return "impossible to measure"


def get_horizon(filtered_df):
    try:
        if len(filtered_df) == 0:
            return ({"start":"impossible to measure","end":"impossible to measure"})
        date_time_str1 = filtered_df.values.tolist()[0][0]
        date_time_str2 = filtered_df.values.tolist()[-1][0]
        return {"start":date_time_str1,"end":date_time_str2}
    except:
        return {"start": "impossible to measure", "end": "impossible to measure"}

def get_interval():
    try:
        date_time_str1 = df.values.tolist()[0][0]
        date_time_str2 = df.values.tolist()[1][0]
        date_time_obj1 = datetime.datetime.strptime(date_time_str1, '%Y-%m-%d %H:%M:%S.%f')
        date_time_obj2 = datetime.datetime.strptime(date_time_str2, '%Y-%m-%d %H:%M:%S.%f')
        num_months = (date_time_obj2.year - date_time_obj1.year) * 12 + (date_time_obj2.month - date_time_obj1.month)
        return num_months
    except:
        return "impossible to measure"


def parse_contents(contents, filename):
    try:
        global df
        content_type, content_string = contents.split(',')

        decoded = base64.b64decode(content_string)
        try:
            if 'csv' in filename:
                # Assume that the user uploaded a CSV file
                df = pd.read_csv(
                    io.StringIO(decoded.decode('utf-8')))
        except Exception as e:
            return None

        return df
    except:
        return pd.DataFrame()


@app.callback(
    Output('dropdown_columns', 'options'),
    [Input('upload-data', 'contents'),
     Input('upload-data', 'filename'),
     Input('dropdown_example', 'value')])
def update_dropdown(contents, filename, value):
    global df
    global df_reset

    ctx = dash.callback_context
    try:
        if ctx.triggered[0]['prop_id'] == 'upload-data.contents':
            df = parse_contents(contents, filename)
            df_reset = copy.deepcopy(df)
            output = []
            i = 0
            for column in df.columns.values.tolist():
                if i > 0:
                    output.append({'label': column, 'value': column})
                i += 1

            return output

        elif (ctx.triggered[0]['prop_id'] == 'dropdown_example.value' or not ctx.triggered) and value is not None:
            df = pd.read_csv(value)
            df_reset = copy.deepcopy(df)
            output = []
            i = 0
            for column in df.columns.values.tolist():
                if i > 0:
                    output.append({'label': column, 'value': column})
                i += 1

            return output

        else:
            return []
    except:
        return []

@app.callback(
    [Output('dropdown_statistics', 'options'),
     Output('dropdown_statistics', 'value'),
     Output('dropdown_stationary', 'options'),
     Output('dropdown_stationary', 'value'),
     Output('dropdown_distribution', 'options'),
     Output('dropdown_distribution', 'value'),
     Output('dropdown_columns_statistics', 'options'),
     Output('dropdown_columns_statistics', 'value')],
    [Input('draw_btn', 'n_clicks'),
     Input('upload-data', 'contents'),
     Input('upload-data', 'filename'),
     Input('dropdown_example', 'value')],
     [State('dropdown_columns', 'value')])
def update_dropdown(n_clicks, content, filename, _value, value):
    ctx = dash.callback_context
    try:
        if ctx.triggered[0]['prop_id'] == 'upload-data.contents' or ctx.triggered[0]['prop_id'] == 'dropdown_example.value':
            return [],"",[],"",[],"",[],""
        options = []
        values = []
        if value is None:
            return [],"",[],"",[],"",[],""
        else:
            for val in value:
                options.append({'label': val, 'value': val})
                values.append(val)
            return options, options[0]['value'], options, options[0]['value'], options, options[0]['value'], options, values
    except:
        return [],"",[],"",[],"",[],""


@app.callback(
    [Output('dropdown_normalize', 'options'),
    Output('dropdown_normalize', 'value')],
    [Input('draw_btn', 'n_clicks'),
     Input('upload-data', 'contents'),
     Input('upload-data', 'filename'),
     Input('dropdown_example', 'value'),
     Input('save_normalize_btn', 'n_clicks')],
     [State('dropdown_columns', 'value'),
      State('normalize_min', 'value'),
      State('normalize_max', 'value'),
      State('dropdown_normalize', 'options'),
      State('dropdown_normalize', 'value')])
def update_dropdown(n_clicks_1, content, filename, _value, n_clicks_2, value, min, max, dn_options, dn_value):
    global normalize_min_max
    global is_normalized

    ctx = dash.callback_context
    try:
        if ctx.triggered[0]['prop_id'] == 'save_normalize_btn.n_clicks' and dn_value is not None:
            _min = float(min)
            _max = float(max)

            if _min == _max or _min > _max:
                normalize_min_max[dn_value] = {}
                normalize_min_max[dn_value]['min'] = 0
                normalize_min_max[dn_value]['max'] = 1
                assigned_min = 0
                assigned_max = 1
            else:
                normalize_min_max[dn_value] = {}
                normalize_min_max[dn_value]['min'] = _min
                normalize_min_max[dn_value]['max'] = _max
                assigned_min = _min
                assigned_max = _max

            for i in range(len(dn_options)):
                if dn_options[i]['value'] == dn_value:
                    dn_options[i]['label'] = dn_value + " min=" + str(assigned_min) + ", max=" + str(assigned_max)
            return dn_options, dn_value

        if ctx.triggered[0]['prop_id'] == 'upload-data.contents' or ctx.triggered[0]['prop_id'] == 'dropdown_example.value':
            return [], ""
        output = []
        if value is None:
            return [], ""
        else:
            for val in value:
                output.append({'label': val+" min=0, max=1", 'value': val})
            return output, output[0]['value']
    except:
        if dn_value is not None:
            normalize_min_max[dn_value] = {}
            normalize_min_max[dn_value]['min'] = 0
            normalize_min_max[dn_value]['max'] = 1
        return [], ""


@app.callback(
    [Output('dropdown_colors', 'options'),
    Output('dropdown_colors', 'value')],
    [Input('draw_btn', 'n_clicks'),
     Input('upload-data', 'contents'),
     Input('upload-data', 'filename'),
     Input('dropdown_example', 'value')],
     [State('dropdown_columns', 'value')])
def update_dropdown(n_clicks, content, filename, _value, value):
    ctx = dash.callback_context
    try:
        if ctx.triggered[0]['prop_id'] == 'upload-data.contents' or ctx.triggered[0]['prop_id'] == 'dropdown_example.value':
            return [],""
        output = []
        if value is None:
            return [],""
        else:
            for val in value:
                output.append({'label': val, 'value': val})
            return output,output[0]['value']
    except:
        return [], ""


@app.callback(
    Output('violin_box_graph', 'figure'),
    [Input('filtered_df_value', 'children'),
     Input('box_violin_dropdown', 'value'),
     Input('draw_btn', 'n_clicks'),
     Input('statistics_btn', 'n_clicks')],
     [State('dropdown_columns', 'value')])
def update_value(jsonified_cleaned_data, value, n_clicks_1, n_clicks_2, dropdown_column):
    ctx = dash.callback_context
    try:
        if ctx.triggered[0]['prop_id'] == 'draw_btn.n_clicks':
            return get_figure([], [], "", "", "")

        if (ctx.triggered[0]['prop_id'] == 'box_violin_dropdown.value' or ctx.triggered[0]['prop_id'] == 'statistics_btn.n_clicks') and jsonified_cleaned_data != "" and dropdown_column is not None:
            filtered_df = pd.read_json(jsonified_cleaned_data, orient='split')

            if value is None:
                value = "boxplot"

            if value == "boxplot":
                fig = go.Figure(layout=go.Layout(
                    plot_bgcolor=theme['light_color'],
                    paper_bgcolor=theme['graph_background'],
                    font={"color": "#E0E0E0"}
                ))
                for col in dropdown_column:
                    if col != 'time':
                        fig.add_trace(go.Box(y=filtered_df[col].tolist(),
                                                name=col,
                                                boxpoints='all'))
                return fig
            elif value == "violinplot":
                fig = go.Figure(layout = go.Layout(
                            plot_bgcolor=theme['light_color'],
                            paper_bgcolor=theme['graph_background'],
                            font={"color": "#E0E0E0"}
                        ))
                for col in dropdown_column:
                    if col != 'time':

                        fig.add_trace(go.Violin(y=filtered_df[col].tolist(),
                                                name=col,
                                                box_visible=True))
                return fig
        return get_figure([], [], "", "", "")
    except:
        return get_figure([], [], "", "", "")


@app.callback(
    Output('download-example','href'),
    [Input('dropdown_example','value')])
def upload_data(value):
    dff = pd.read_csv('multiple_columns.csv')
    csv_string = dff.to_csv(index=False, encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

@app.callback(
    [Output('download-link', 'href'),
    Output(component_id='download_div', component_property='style')],
    [Input('report_btn','n_clicks'),
     Input('draw_btn','n_clicks'),
     Input('statistics_btn','n_clicks'),
     Input('dropdown_property', 'value'),
     Input('dropdown_columns_statistics', 'value')],
     [State('dropdown_property', 'options'),
     State('dropdown_years', 'value'),
     State('dropdown_months', 'value'),
     State('dropdown_days', 'value'),
     State('dropdown_days_of_week', 'value'),
     State('dropdown_years', 'options'),
     State('dropdown_months', 'options'),
     State('dropdown_days', 'options'),
     State('dropdown_days_of_week', 'options'),
     State('download-link', 'href')],
)
def update_download_link(n_clicks0, n_clicks1, n_clicks_2, properties_indexes, columns, property_options, years, months, days, days_of_week, o_years, o_months, o_days, o_days_of_week, csv_string):
    data = {}
    properties_column = []
    ctx = dash.callback_context
    try:
        if ctx.triggered[0]['prop_id'] == 'statistics_btn.n_clicks' or ctx.triggered[0]['prop_id'] == 'draw_btn.n_clicks'\
                or ctx.triggered[0]['prop_id'] == 'dropdown_property.value'or ctx.triggered[0]['prop_id'] == 'dropdown_columns_statistics.value':
            return "", {'display': 'none', 'margin-top': '16px', 'margin-left': '10px'}

        if ctx.triggered[0]['prop_id'] == 'report_btn.n_clicks':
            # return csv_string, {'display': 'block'}

            properties = []
            for x in property_options:
                if x['value'] in properties_indexes:
                    properties.append(x['label'])
            data["properties"] = properties

            for col in columns:
                properties_column = get_statistical_properties(years, months, days, days_of_week, o_years, o_months, o_days, o_days_of_week, col, columns)
                data[col] = parse_statistical_properties(properties_column, properties_indexes)
            dff = pd.DataFrame(data)
            csv_string = dff.to_csv(index=False, encoding='utf-8')
            csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
            return csv_string, {'display': 'block', 'margin-top': '16px', 'margin-left': '10px'}

        elif n_clicks0 is None:
            return "", {'display': 'none', 'margin-top': '16px', 'margin-left': '10px'}
        elif n_clicks0 > 1:
            return "", {'display': 'block', 'margin-top': '16px', 'margin-left': '10px'}
        else:
            return "", {'display': 'none', 'margin-top': '16px', 'margin-left': '10px'}
    except:
        return "", {'display': 'none', 'margin-top': '16px', 'margin-left': '10px'}


def parse_statistical_properties(properties_column, properties):
    data = []
    returned_data = []
    try:
        if type(properties_column[5][0]["3"]) is str and properties_column[5][0]["3"] == "impossible to measure":
            mad = "impossible to measure"
        else:
            mad = properties_column[5][0]["3"][0]

        if type(properties_column[2][0]["6"]) is str and properties_column[5][0]["3"] == "impossible to measure":
            mode = "impossible to measure"
        else:
            mode = properties_column[2][0]["6"][0]

        data.extend([properties_column[1][0]["1"], properties_column[1][0]["2"], properties_column[1][0]["3"], properties_column[1][0]["4"]])
        data.extend(
            (properties_column[2][0]["1"], properties_column[2][0]["2"], properties_column[2][0]["3"], properties_column[2][0]["4"],
             properties_column[2][0]["5"], mode))
        data.extend(
            (properties_column[3][0]["1"], properties_column[3][0]["2"], properties_column[3][0]["3"], properties_column[3][0]["4"],
             properties_column[3][0]["5"]))
        data.extend(
            (properties_column[4][0]["1"], properties_column[4][0]["2"], properties_column[4][0]["3"], properties_column[4][0]["4"],
             properties_column[4][0]["5"]))
        data.extend(
            (properties_column[5][0]["1"], properties_column[5][0]["2"], mad))
        data.extend(
            (properties_column[6][0]["1"], properties_column[6][0]["2"], properties_column[6][0]["3"]))
        data.extend(
            (properties_column[7][0]["1"], properties_column[7][0]["2"]))
        data.extend(
            (properties_column[8][0]["1"], properties_column[8][0]["2"], properties_column[8][0]["3"]))

        properties.sort()
        for prop in properties:
            returned_data.append(data[prop-1])

        return returned_data

    except:
        return []


@app.callback(
    [Output('output-graph', 'figure'),
    Output('decreasing-information','children')],
    [Input('correct_data_btn', 'n_clicks'),
     Input('draw_btn', 'n_clicks'),
     Input('dropdown_example', 'value'),
     Input('normalize_btn', 'n_clicks'),
     Input('denormalize_btn', 'n_clicks'),
     Input('change_color_btn', 'n_clicks'),
     Input('SMOOTH_btn', 'n_clicks'),
     Input('UNDO_btn', 'n_clicks'),
     Input('IQR_btn', 'n_clicks'),
     Input('DECREASE_btn', 'n_clicks'),
     Input('reset_btn', 'n_clicks'),
     Input('normalize_2_btn','n_clicks')],
     [State('output-graph', 'figure'),
      State('wrong_samples_table', 'data'),
      State('graph-color-picker', 'value'),
      State('dropdown_colors', 'value'),
      State('dropdown_columns', 'value'),
      State('decreasing-information', 'children'),
      State('decrease_leap', 'value')])
def update_value(n_click_1, n_click_2, value, n_click_3, n_click_4, n_click_5, n_click_6, n_click_7, n_click_8, n_click_9, n_cick_10, n_click_11, figure, rows, color, dropdown_color, dropdown_value, info, decrease_leap):
    global df
    global tmp_df

    global df_before_changing

    global colors

    global normalize_min_max
    global is_normalized

    global was_changed
    global df_reset

    global decreased_count

    info = 'the number of time series samples has not been reduced'
    ctx = dash.callback_context

    if ctx.triggered[0]['prop_id'] == 'reset_btn.n_clicks':
        try:
            if df_reset is not None:
                df = copy.deepcopy(df_reset)
                df_before_changing = copy.deepcopy(df_reset)
                tmp_df = copy.deepcopy(df_reset)
                is_normalized = False
                was_changed = False
                return get_graph(dropdown_value,df),info
        except:
            return get_graph(dropdown_value)
    elif ctx.triggered[0]['prop_id'] == 'IQR_btn.n_clicks' and dropdown_value is not None:
        try:
            if was_changed == False:
                df_before_changing = copy.deepcopy(df)

            was_changed = True

            new_df = copy.deepcopy(df)

            for v in dropdown_value:
                # df
                if new_df is not None:
                    current_values = new_df[v].tolist()

                    Q1 = np.percentile(current_values, 25)
                    Q3 = np.percentile(current_values, 75)

                    IQR = Q3 - Q1

                    min_of_the_range = Q1 - 1.5 * IQR
                    max_of_the_range = Q3 + 1.5 * IQR

                    for k in range(len(current_values)):
                        if current_values[k] < min_of_the_range or current_values[k] > max_of_the_range:
                            current_values[k] = None

                    df[v] = current_values
            if decreased_count > 0:
                info = 'the number of time series samples has been reduced ' + str(decreased_count) + ' times'

            return get_graph(dropdown_value,df),info
        except:
            return get_graph(dropdown_value)
    elif ctx.triggered[0]['prop_id'] == 'DECREASE_btn.n_clicks' and dropdown_value is not None:
        try:
            was_decreased = False
            if decrease_leap not in [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]:
                if decreased_count > 0:
                    info = 'the number of time series samples has been reduced ' + str(decreased_count) + ' times'
                return get_graph(dropdown_value, df), info

            if was_changed == False:
                df_before_changing = copy.deepcopy(df)

            was_changed = True
            new_df = copy.deepcopy(df)
            # new_tmp_df = copy.deepcopy(tmp_df)
            if df is not None:
                current_values = df['time'].tolist()
                count = 0
                if len(current_values) > decrease_leap:
                    for k in range(len(current_values)):
                        if k % decrease_leap == 0:
                            count += 1
                    was_decreased = True
                    new_df.drop(new_df.tail(count).index, inplace=True)

            for v in df.columns:
                # df
                if df is not None:
                    decreased_samples = []
                    current_values = df[v].tolist()
                    if len(current_values) > decrease_leap:
                        for k in range(len(current_values)):
                            if k % decrease_leap != 0:
                                decreased_samples.append(current_values[k])

                        new_df[v] = decreased_samples

            if new_df is not None:
                df = copy.deepcopy(new_df)

            if was_decreased:
                decreased_count += 1
                info = 'the number of time series samples has been reduced '+ str(decreased_count) +' times'
            else:
                info = 'the number of time series samples has been reduced ' + str(decreased_count) + ' times'
            return get_graph(dropdown_value, df), info
        except:
            return get_graph(dropdown_value)
    elif ctx.triggered[0]['prop_id'] == 'UNDO_btn.n_clicks' and dropdown_value is not None:
        try:
            if was_changed == False:
                return get_graph(dropdown_value,df),info
            else:
                was_changed = False
                decreased_count = 0
                df = copy.deepcopy(df_before_changing)
                return get_graph(dropdown_value,df), info
        except:
            return get_graph(dropdown_value)
    elif ctx.triggered[0]['prop_id'] == 'normalize_2_btn.n_clicks' and dropdown_value is not None:
        try:
            if was_changed == False:
                df_before_changing = copy.deepcopy(df)

            was_changed = True

            for v in df.columns.values.tolist():
                if v != 'time':
                    df[v] = df[v].sub(df[v].min())
                    if df[v].max() != df[v].min():
                        df[v] = df[v].div(df[v].max()-df[v].min())

            if decreased_count > 0:
                info = 'the number of time series samples has been reduced ' + str(decreased_count) + ' times'
            return get_graph(dropdown_value,df),info
        except:
            return get_graph(dropdown_value)

    elif ctx.triggered[0]['prop_id'] == 'SMOOTH_btn.n_clicks' and dropdown_value is not None:
        try:
            if was_changed == False:
                df_before_changing = copy.deepcopy(df)

            was_changed = True

            new_df = copy.deepcopy(df)

            if decreased_count > 0:
                info = 'the number of time series samples has been reduced ' + str(decreased_count) + ' times'

            if df is not None:
                if len(df.index) < 3:
                    return get_graph(dropdown_value,df),info
                df.drop(df.tail(1).index, inplace=True)
                df.drop(df.head(1).index, inplace=True)

            for v in dropdown_value:
                # df
                if new_df is not None:
                    smooth_values = []
                    current_values = new_df[v].tolist()
                    if len(current_values) > 2:
                        for k in range(len(current_values)-2):
                            smooth_values.append((current_values[k]+current_values[k+1]+current_values[k+2])/3)

                        df[v] = smooth_values

            return get_graph(dropdown_value,df),info
        except:
            return get_graph(dropdown_value)
    elif ctx.triggered[0]['prop_id'] == 'change_color_btn.n_clicks' and dropdown_value is not None:
        try:
            colors['r'] = int(color['hex'][1:3],16)
            colors['g'] = int(color['hex'][3:5],16)
            colors['b'] = int(color['hex'][5:7],16)
            colors[dropdown_color] = ('rgb(' + str(colors['r']) + ', ' + str(colors['g']) + ', ' + str(
                colors['b']) + ')')
            if decreased_count > 0:
                info = 'the number of time series samples has been reduced ' + str(decreased_count) + ' times'
            return get_graph(dropdown_value,df),info
        except:
            return get_graph(dropdown_value)
    elif ctx.triggered[0]['prop_id'] == 'normalize_btn.n_clicks' and dropdown_value is not None and is_normalized == False:
        try:
            if was_changed == True:
                was_changed = False
                decreased_count = 0
                df = copy.deepcopy(df_before_changing)

            tmp_df = copy.deepcopy(df)
            for v in df.columns.values.tolist():
                if v != 'time':
                    if v not in normalize_min_max:
                        normalize_min_max[v] = {}
                        normalize_min_max[v]['min'] = 0
                        normalize_min_max[v]['max'] = 1
                    df[v] = df[v].sub(df[v].min())
                    if df[v].max() != df[v].min():
                        df[v] = df[v].div(df[v].max()-df[v].min())
                    df[v] = df[v].mul(normalize_min_max[v]['max']-normalize_min_max[v]['min'])
                    df[v] = df[v].add(normalize_min_max[v]['min'])
                    is_normalized = True
            return get_graph(dropdown_value,df), info
        except:
            return get_graph(dropdown_value)
    elif ctx.triggered[0]['prop_id'] == 'denormalize_btn.n_clicks' and dropdown_value is not None and is_normalized:
        try:
            if was_changed == True:
                was_changed = False
                decreased_count = 0
                df = copy.deepcopy(df_before_changing)

            if tmp_df is not None:
                df = copy.deepcopy(tmp_df)

            is_normalized = False
            return get_graph(dropdown_value,df),info
        except:
            return get_graph(dropdown_value)
    elif ctx.triggered[0]['prop_id'] == 'denormalize_btn.n_clicks' and dropdown_value is not None:
        return get_graph(dropdown_value,df),info
    elif ctx.triggered[0]['prop_id'] == 'correct_data_btn.n_clicks' and dropdown_value is not None:
        try:
            for row in rows:
                try:
                    name = str(row['1'])
                    row_data = str(row['2'])+":00.000000"
                    new_data = float(row['3'])

                    for i in range(len(df.values)):
                        index, _column = None, None
                        for j in range(len(df.columns.values)):
                            t = df.values[i][0]
                            k = df.columns.values[j]
                            if df.values[i][0] == row_data and df.columns.values[j] == name:
                                index = i
                                _column = df.columns.values[j]
                                break
                        if index is not None and _column is not None:
                            break
                    df.set_value(index,_column,new_data)
                except:
                    continue
        except:
            return get_graph(dropdown_value)
        if decreased_count > 0:
            info = 'the number of time series samples has been reduced ' + str(decreased_count) + ' times'
        return get_graph(dropdown_value,df),info

    elif ctx.triggered[0]['prop_id'] == 'draw_btn.n_clicks':

        is_normalized = False
        if dropdown_value is not None and df is not None:
            if decreased_count > 0:
                info = 'the number of time series samples has been reduced ' + str(decreased_count) + ' times'
            return get_graph(dropdown_value,df),info
        else:
            return get_graph(None, None),info

    elif is_normalized:
        return get_graph(dropdown_value,df),info
    elif df is not None:
        return get_graph(dropdown_value,df),info
    else:
        return get_graph(None,None),info

def get_graph(dropdown_value, _df):
    global colors
    figure = {
        'data': [],
        'layout': {
            'showlegend': True,
            'xaxis': {
                'title': 'time'
            },
            'yaxis': {
                'title': 'value'
            },
            'plot_bgcolor': theme['light_color'],
            'paper_bgcolor': theme['graph_background'],
            'font': {"color": "#E0E0E0"}
        }
    }
    example_colors = [[0,0,255],[0,255,0],[255,0,0],[0,255,255],[255,0,255],[255,255,0]]

    try:
        if _df is not None and dropdown_value is not None:
            for column in _df.columns.values:
                if column not in colors:
                    if example_colors:
                        example_color = example_colors.pop(0)
                        colors[column] = ('rgb(' + str(example_color[0]) + ', ' + str(
                            example_color[1]) + ', ' + str(example_color[2]) + ')')
                    else:
                        colors[column] = ('rgb(' + str(random.randint(190,255)) + ', ' + str(random.randint(190,255)) + ', ' + str(random.randint(190,255)) + ')')
                if column != _df.columns.values[0] and column in dropdown_value:
                    figure['data'].append({'x': _df[_df.columns.values[0]], 'y': _df[column], 'type': 'line', 'name': str(column),
                                           'marker': {'color': colors[column]}})
        return figure
    except:
        return figure

def get_figure(time, data, value, x_axis_name, y_axis_name):
    if value == "":
        return {
            'data': [
                {'x': time, 'y': data, 'type': 'line', 'name': 'SF'},
            ],
            'layout': {
                'xaxis': {
                    'title': x_axis_name
                },
                'yaxis': {
                    'title': y_axis_name
                },
                'plot_bgcolor': theme['light_color'],
                'paper_bgcolor': theme['graph_background'],
                'font': {"color": "#E0E0E0"}
            }
        }
    else:
        return {
            'data': [
                {'x': time, 'y': data, 'type': 'line', 'name': 'SF'},
            ],
            'layout': {
                'title': 'filename: ' + str(value),
                'xaxis': {
                    'title': x_axis_name
                },
                'yaxis': {
                    'title': y_axis_name
                },
                'plot_bgcolor': theme['light_color'],
                'paper_bgcolor': theme['graph_background'],
                'font': {"color": "#E0E0E0"}
            }
        }


def best_distribution(time_series):
    #names of tested distributions
    global dist_names

    #getting time series data from global DataFrame
    values = df[time_series].tolist()
    data = []
    for v in values:
        if not math.isnan(v):
            data.append(v)
    x = np.arange(len(data))
    size = len(data)

    # standarize data
    standardScaler = StandardScaler()
    y = np.array(data).reshape(-1, 1)
    standardScaler.fit(y)
    y_transformed = standardScaler.transform(y)
    y_transformed = y_transformed.flatten()
    del y

    # lists for results
    chi_sqr = []
    p_val = []

    # setting 50 probes for chi-square test
    percentile_probes = np.linspace(0, 100, 51)
    percentile_cutoffs = np.percentile(y_transformed, percentile_probes)
    observed_freq, bins = (np.histogram(y_transformed, bins=percentile_cutoffs))
    cum_obsrv_freq = np.cumsum(observed_freq)

    # Loop through all distributions

    for distribution in dist_names:
        #get fitted distribution parameters
        distrib = getattr(scipy.stats, distribution)
        param = distrib.fit(y_transformed)

        # get KS test P statistic and round it
        p = scipy.stats.kstest(y_transformed, distribution, args=param)[1]
        p = np.around(p, 5)
        p_val.append(p)

        # cdf fit
        cdf_fit = distrib.cdf(percentile_cutoffs, *param[:-2], loc=param[-2],
                              scale=param[-1])
        expected_freq = []
        for bin in range(len(percentile_probes) - 1):
            expected_cdf_area = cdf_fit[bin + 1] - cdf_fit[bin]
            expected_freq.append(expected_cdf_area)

        #  chi-squared
        expected_freq = np.array(expected_freq) * size
        cum_expected_freq = np.cumsum(expected_freq)
        ss = sum(((cum_expected_freq - cum_obsrv_freq) ** 2) / cum_obsrv_freq)
        chi_sqr.append(ss)

    # sort by goodness of fit
    results = pd.DataFrame()
    results['dist'] = dist_names
    results['chi_sqr'] = chi_sqr
    results['p_val'] = p_val
    results.sort_values(['chi_sqr'], inplace=True)

    number_distribution = 1
    chosen_dists = results['dist'].iloc[0:number_distribution]

    parameters_of_best_dist = []

    for name in chosen_dists:
        dist = getattr(scipy.stats, name)
        param = dist.fit(data)

        if dist.shapes:
            shapes = [name.strip() for name in dist.shapes.split(',')]
        else:
            shapes = []
        if dist.name in scipy.stats._discrete_distns._distn_names:
            shapes += ['loc']
        elif dist.name in scipy.stats._continuous_distns._distn_names:
            shapes += ['loc', 'scale']

        parameters_of_best_dist.append(param)


    # Store distribution parameters
    dist_parameters = pd.DataFrame()
    dist_parameters['dist'] = (
        results['dist'].iloc[0:number_distribution])
    dist_parameters['dist params'] = parameters_of_best_dist

    returned_value = ''

    for index, row in dist_parameters.iterrows():
        returned_value += 'DISTRIBUTION TYPE: {},'.format(row[0])
        returned_value += ' PARAMETERS: '
    for i in range(len(shapes)):
        tmp = str(shapes[i]) + " = " + str(parameters_of_best_dist[0][i])
        returned_value += tmp
        if i < (len(shapes)-1):
            returned_value += ", "

    return returned_value


@app.callback(
    Output('distribution_text_area','children'),
    [Input('distribution_btn', 'n_clicks'),
     Input('draw_btn', 'n_clicks'),
     Input('dropdown_distribution', 'value')],
    [State('dropdown_distribution', 'value')]
)
def update_value(n_clicks_1,n_clicks_2,value,time_series):
    ctx = dash.callback_context

    if ctx.triggered[0]['prop_id'] == 'dropdown_distribution.value':
        return ""
    if ctx.triggered[0]['prop_id'] == 'distribution_btn.n_clicks':
        try:
            x = best_distribution(time_series)
        except:
            x = "unable to find proper distribution"
        return x
    else:
        return ""

def is_stationary(time_series):
    try:
        values = df[time_series].tolist()
        data = []
        for v in values:
            if not math.isnan(v):
                data.append(v)
        result = adfuller(data)
        if result[1] < 0.05:
            return "TIME SERIES IS STATIONARY"
        else:
            return "TIME SERIES IS NOT STATIONARY"
    except:
        return "unable to check stationarity"

@app.callback(
    Output('is_stationary_text_area','children'),
    [Input('is_stationary_btn', 'n_clicks'),
     Input('draw_btn', 'n_clicks'),
     Input('dropdown_stationary', 'value')],
    [State('dropdown_stationary', 'value')]
)
def update_value(n_clicks_1, n_clicks_2, value, time_series):
    ctx = dash.callback_context
    try:
        if ctx.triggered[0]['prop_id'] == 'dropdown_stationary.value':
            return ""
        if ctx.triggered[0]['prop_id'] == 'is_stationary_btn.n_clicks':
            x = is_stationary(time_series)
            return x
        else:
            return ""
    except:
        return ""


if __name__ == '__main__':
    app.run_server(debug=True, threaded=False, processes=1)

