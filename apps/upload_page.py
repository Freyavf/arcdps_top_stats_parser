import base64
import io
from pydoc import classname
from dash import dash_table
from dash.dependencies import Input, Output, State
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
#from dash.long_callback import DiskcacheLongCallbackManager
#from sqlalchemy.sql.elements import Null
#from helpers import db_writer, graphs

## Diskcache
#import diskcache
#cache = diskcache.Cache("./cache")
#long_callback_manager = DiskcacheLongCallbackManager(cache)


import pandas as pd
from app import app #, db

import os.path
from os import listdir
import sys
from enum import Enum
import importlib
import xlwt
import json
import jsons

from parse_top_stats_tools import *
import parser_configs.parser_config_detailed as parser_config
config = fill_config(parser_config)
log = open("log_detailed.txt","w")
output = open("top_stats_detailed.txt", "w")
xls_output_filename = "top_stats_detailed.xls"
json_output_filename = "top_stats_detailed.json"

#from models import FightSummary, Raid, RaidType

#dropdown_options = [{'label':s.name, 'value':s.id} for s in db.session.query(RaidType).all()]
#raids_dict = [s.to_dict() for s in db.session.query(FightSummary).all()]
#raids_df = pd.DataFrame(raids_dict)


layout = [
    dcc.Store(id='temp-data'),
    dcc.Store(id='temp-raid'),
    dcc.ConfirmDialog(
        id='confirm-raid-exists',
        message='This raid already exists. Want to overwrite?',
    ),
    dcc.ConfirmDialog(
        id='confirm-raid-delete',
        message='Are you sure you want to delete this raid?',
    ),
    dbc.Row([dcc.Loading(dbc.Col(id='raid-summary'))]),
    dbc.Row([
        dbc.Col(dcc.Upload(id='upload-file', children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files')
                ]), multiple=True),md=12)               
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Row(id='input-row', class_name='input-row', children=[
                dbc.Col(dcc.Loading(html.Div(id='save-msg'))),
                #dbc.Col(dbc.Input(id='raid-name-input',placeholder='Raid title (optional)', value='')),
                #dbc.Col(dcc.Dropdown(id='raid-type-dropdown',
                #                    placeholder='Select raid type',
                #                    options=dropdown_options,
                #                    value=dropdown_options[1]['value'])),
                #dbc.Col(dbc.Button("Save", id='save-button')),
                dbc.Col(html.Div([html.Button("Save Log", id = "btn_save_log"), dcc.Download(id='save-log')])),
                dbc.Col(html.Div([html.Button("Save xls", id = "btn_save_xls"), dcc.Download(id='save-xls')])),
                dbc.Col(html.Div([html.Button("Save json", id = "btn_save_json"), dcc.Download(id='save-json')])),                
            ]),
        ])
    ]),
    #dbc.Row([
    #    dbc.Col(id='raids-update-output'),
    #    dbc.Col(dbc.Button("Delete Raid(s)", id='delete-raid-btn'), width={}, style={'text-align':'end'})
    #], justify='end'),
    #dbc.Row([
    #    dcc.Loading(html.Div(
    #        dash_table.DataTable(
    #            id='fights-table',
    #            data={"testing": "working"},
    #            editable=False,
    #            row_selectable=False,
    #            cell_selectable=False,
    #            style_as_list_view=True,
    #            style_cell={
    #                'border': '1px solid #444',
    #                'padding': '0.5rem',
    #                'textAlign': 'center',
    #                'font-family': 'var(--bs-body-font-family)',
    #                'line-height': 'var(--bs-body-line-height)'
    #            },
    #            style_data={
    #                'backgroundColor': '#424242',
    #            },
    #            style_header={
    #                'backgroundColor': '#212121',
    #                'textAlign': 'center',
    #                'fontWeight': 'bold',
    #                'border-top': '0px',
    #                'border-bottom': '1px solid white'
    #            },
    #        ),
    #    ))
    #]),
]

#@app.long_callback(#Output('fights-table', 'data'),
@app.callback(#Output('fights-table', 'data'),
              Output('raid-summary', 'children'),
              #Output('temp-data', 'data'),
              Input('upload-file', 'contents'),
              State('upload-file', 'filename'),)
#              manager=long_callback_manager,)
def get_temp_data(list_of_contents, list_of_names):
    if list_of_contents is None:
        return

    log = open("log_detailed.txt","w")

    print_string = "Considering fights with at least "+str(config.min_allied_players)+" allied players and at least "+str(config.min_enemy_players)+" enemies that took longer than "+str(config.min_fight_duration)+" s."
    print(print_string)

    # healing only in logs if addon was installed
    found_healing = False # Todo what if some logs have healing and some don't
    found_barrier = False    

    players = []        # list of all player/profession combinations
    player_index = {}   # dictionary that matches each player/profession combo to its index in players list
    account_index = {}  # dictionary that matches each account name to a list of its indices in players list

    used_fights = 0
    fights = []
    first = True
            
    for content, filename in zip(list_of_contents, list_of_names):
        # skip files of incorrect filetype
        file_start, file_extension = os.path.splitext(filename)
        if 'json' not in file_extension or "top_stats" in file_start:
            continue

        print_string = "parsing "+filename
        print(print_string)

        content_type, content_string = content.split(',')
        decoded = base64.b64decode(content_string)
        json_data = json.loads(decoded)
        used_fights, first, found_healing, found_barrier = get_stats_from_json_data(json_data, players, player_index, account_index, used_fights, fights, config, first, found_healing, found_barrier, log, filename)

    get_overall_stats(players, used_fights, False, config)
    print("\n")

    print_string = "Welcome to the Records of Valhalla!\n"
    myprint(output, print_string)

    # print overall stats
    overall_squad_stats = get_overall_squad_stats(fights, config)
    total_fight_duration = print_total_squad_stats(fights, overall_squad_stats, found_healing, found_barrier, config, log)

    print_fights_overview(fights, overall_squad_stats, config, log)

    # create xls file if it doesn't exist
    book = xlwt.Workbook(encoding="utf-8")
    book.add_sheet("fights overview")
    book.save(xls_output_filename)
    
    #myprint(output, print_string)

    # print overall stats
    overall_squad_stats = get_overall_squad_stats(fights, config)
    total_fight_duration = print_total_squad_stats(fights, overall_squad_stats, found_healing, found_barrier, config, output)

    print_fights_overview(fights, overall_squad_stats, config, output)
    write_fights_overview_xls(fights, overall_squad_stats, config, xls_output_filename)
    
    # print top x players for all stats. If less then x
    # players, print all. If x-th place doubled, print all with the
    # same amount of top x achieved.
    num_used_fights = len([f for f in fights if not f.skipped])

    top_total_stat_players = {key: list() for key in config.stats_to_compute}
    top_consistent_stat_players = {key: list() for key in config.stats_to_compute}
    top_average_stat_players = {key: list() for key in config.stats_to_compute}
    top_percentage_stat_players = {key: list() for key in config.stats_to_compute}
    top_late_players = {key: list() for key in config.stats_to_compute}
    top_jack_of_all_trades_players = {key: list() for key in config.stats_to_compute}    
    
    for stat in config.stats_to_compute:
        if (stat == 'heal' and not found_healing) or (stat == 'barrier' and not found_barrier):
            continue

        myprint(output, config.stat_names[stat].upper()+" AWARDS\n")
        
        if stat == 'dist':
            top_consistent_stat_players[stat] = get_top_players(players, config, stat, StatType.CONSISTENT)
            top_total_stat_players[stat] = get_top_players(players, config, stat, StatType.TOTAL)
            top_average_stat_players[stat] = get_top_players(players, config, stat, StatType.AVERAGE)            
            top_percentage_stat_players[stat],comparison_val = get_and_write_sorted_top_percentage(players, config, num_used_fights, stat, output, StatType.PERCENTAGE, top_consistent_stat_players[stat])
        elif stat == 'dmg_taken':
            top_consistent_stat_players[stat] = get_top_players(players, config, stat, StatType.CONSISTENT)
            top_total_stat_players[stat] = get_top_players(players, config, stat, StatType.TOTAL)
            top_percentage_stat_players[stat],comparison_val = get_top_percentage_players(players, config, stat, StatType.PERCENTAGE, num_used_fights, top_consistent_stat_players[stat], top_total_stat_players[stat], list(), list())
            top_average_stat_players[stat] = get_and_write_sorted_average(players, config, num_used_fights, stat, output)
        else:
            top_consistent_stat_players[stat] = get_and_write_sorted_top_consistent(players, config, num_used_fights, stat, output)
            top_total_stat_players[stat] = get_and_write_sorted_total(players, config, total_fight_duration, stat, output)
            top_average_stat_players[stat] = get_top_players(players, config, stat, StatType.AVERAGE)
            top_percentage_stat_players[stat],comparison_val = get_top_percentage_players(players, config, stat, StatType.PERCENTAGE, num_used_fights, top_consistent_stat_players[stat], top_total_stat_players[stat], list(), list())

    write_to_json(overall_squad_stats, fights, players, top_total_stat_players, top_average_stat_players, top_consistent_stat_players, top_percentage_stat_players, top_late_players, top_jack_of_all_trades_players, json_output_filename)

    for stat in config.stats_to_compute:
        if stat == 'dist':
            write_stats_xls(players, top_percentage_stat_players[stat], stat, xls_output_filename)
        elif stat == 'dmg_taken':
            write_stats_xls(players, top_average_stat_players[stat], stat, xls_output_filename)
        elif stat == 'heal' and found_healing:
            write_stats_xls(players, top_total_stat_players[stat], stat, xls_output_filename)            
        elif stat == 'barrier' and found_barrier:
            write_stats_xls(players, top_total_stat_players[stat], stat, xls_output_filename)
        elif stat == 'deaths':
            write_stats_xls(players, top_consistent_stat_players[stat], stat, xls_output_filename)
        else:
            write_stats_xls(players, top_total_stat_players[stat], stat, xls_output_filename)

    log.close()    
    
    print_string = get_fights_overview_string(fights, overall_squad_stats, config)
    return print_string

    #return {"players":[player.__dict__ for player in players], "fights":[fight.__dict__ for fight in fights], "overall_stats": overall_squad_stats, "found_healing":found_healing, "found_barrier":found_barrier}
        
    #return content_string


@app.callback(
#    [Output("temp-raid", "data"),
    Output('save-msg', 'data'), 
    Input("save-button", "n_clicks")
)
def on_save_click(n):
    if n:
        return "viewing log"
    return False

    
@app.callback(
    Output('save-log', 'data'), 
    Input("btn_save_log", "n_clicks")
)
def on_save_log_click(n):
    if n:
        return dcc.send_file(
        "./log_detailed.txt"
        )
    return False

@app.callback(
    Output('save-xls', 'data'), 
    Input("btn_save_xls", "n_clicks")
)
def on_save_xls_click(n):
    if n:
        return dcc.send_file(
            xls_output_filename
        )
    return False

@app.callback(
    Output('save-json', 'data'), 
    Input("btn_save_json", "n_clicks")
)
def on_save_json_click(n):
    if n:
        return dcc.send_file(
            json_output_filename
        )
    return False

#@app.callback(Output('raid-summary', 'children'),
#            Input('temp-data', 'data'))
#def show_fights_summary_table(collected_data):
#    if collected_data:

#        print(print_string)
#        log = open(os.devnull,"w")
#        decoded = base64.b64decode(content)
#        #json_datafile = open(file_path, encoding='utf-8')
#        json_data = json.loads(decoded)
#        fight, players_running_healing_addon = get_stats_from_fight_json(json_data, config, log)        
#
#        #players, fights, found_healing, found_barrier = collect_stat_data(args, config, log, args.anonymize)
#
#        return ["duration ", fight.duration]


#@app.callback(
#    Output('confirm-raid-delete', 'displayed'), 
#    Input("delete-raid-btn", "n_clicks")
#)
#def on_delete_click(n):
#    if n:
#        return True

#@app.callback(
#    Output('raids-table', 'data'),
#    Input('raids-update-output', 'children'),
#    Input('save-msg', 'children'),
#    Input("temp-raid", "data")
#)
#def update_raids_table(msg, save_msg, data):
#    raids_dict = [s.to_dict() for s in db.session.query(FightSummary).join(Raid).order_by(Raid.raid_date.desc(), FightSummary.start_time.desc()).all()]
#    return raids_dict


#@app.callback(Output('raids-update-output', 'children'),
#              Input('confirm-raid-delete', 'submit_n_clicks'),
#              State('raids-table', 'selected_rows'),
#              State('raids-table', 'data'))
#def confirm_delete_row(submit_n_clicks, rows, data):
#    if submit_n_clicks:
#        row_list = []
#        for row in rows:
#            raid = db_writer.get_raid_by_summary(data[row]['Date'], data[row]['Kills'], data[row]['Deaths'])
#            db_writer.delete_raid(raid.id)
#            row_list.append(raid)
#            data[row] = {}
#        data = [s for s in data if s != {}]
#        return [f'Just removed {row}:{row.raid_date}' for row in row_list]
#
#
#
#@app.callback(
#    [Output("temp-raid", "data"),
#    Output('confirm-raid-exists', 'displayed')], 
#    [Input("save-button", "n_clicks")],
#    [State('temp-data', 'data'),
#    State('raid-name-input', 'value'),
#    State('raid-type-dropdown', 'value'),
#    ]
#)
#def on_save_click(n, content, name, t):
#    db_msg = ''
#    if n and content:
#        decoded = base64.b64decode(content)
#        df_fights = pd.read_excel(io.BytesIO(decoded), sheet_name='fights overview').tail(1).iloc[:,1:]
#        raid = db_writer.check_if_raid_exists(df_fights['Date'].values[0], df_fights['Start Time'].values[0])
#        if raid:
#            return raid.id, True
#        db_msg = db_writer.write_xls_to_db(decoded, name, t)
#        return db_msg, False
#    return content, False
#
#
#@app.callback(Output('save-msg', 'children'),
#              Input('confirm-raid-exists', 'submit_n_clicks'),
#              State('temp-raid', 'data'),
#              State('temp-data', 'data'),
#              State('raid-name-input', 'value'),
#              State('raid-type-dropdown', 'value'),)
#def update_output(submit_n_clicks, raid, xls, name, t):
#    if submit_n_clicks:
#        db_writer.delete_raid(raid)
#        decoded = base64.b64decode(xls)
#        db_writer.write_xls_to_db(decoded, name, t)
#        return f'Overwriting raid {raid}'
