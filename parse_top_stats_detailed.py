#!/usr/bin/env python3

#    parse_top_stats_detailed.py outputs detailed top stats in arcdps logs as parsed by Elite Insights.
#    Copyright (C) 2021 Freya Fleckenstein
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.


import argparse
import os.path
from os import listdir
import sys
from enum import Enum
import importlib
import xlwt

from parse_top_stats_tools import *
from io_helper import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='This reads a set of arcdps reports in json format and generates top stats.')
    parser.add_argument('input_directory', help='Directory containing .json files from arcdps reports')
    parser.add_argument('-o', '--output', dest="output_filename", help="Text file to write the computed top stats")
    parser.add_argument('-x', '--xls_output', dest="xls_output_filename", help="xls file to write the computed top stats")    
    parser.add_argument('-j', '--json_output', dest="json_output_filename", help="json file to write the computed top stats to")    
    parser.add_argument('-l', '--log_file', dest="log_file", help="Logging file with all the output")
    parser.add_argument('-c', '--config_file', dest="config_file", help="Config file with all the settings", default="parser_config_detailed")
    parser.add_argument('-a', '--anonymized', dest="anonymize", help="Create an anonymized version of the top stats. All account and character names will be replaced.", default=False, action='store_true')
    args = parser.parse_args()

    if not os.path.isdir(args.input_directory):
        print("Directory ",args.input_directory," is not a directory or does not exist!")
        sys.exit()
    if args.output_filename is None:
        args.output_filename = args.input_directory+"/top_stats_detailed.txt"
    if args.xls_output_filename is None:
        args.xls_output_filename = args.input_directory+"/top_stats_detailed.xls"
    if args.json_output_filename is None:
        args.json_output_filename = args.input_directory+"/top_stats_detailed.json"                
    if args.log_file is None:
        args.log_file = args.input_directory+"/log_detailed.txt"

    log = open(args.log_file, "w")

    parser_config = importlib.import_module("parser_configs."+args.config_file , package=None) 
    config = fill_config(parser_config, log)

    output = None
    if 'txt' in config.files_to_write:
        output = open(args.output_filename, "w")

    print_string = "Using input directory "+args.input_directory+", writing output to "+args.output_filename+" and log to "+args.log_file
    print(print_string)
    print_string = "Considering fights with at least "+str(config.min_allied_players)+" allied players and at least "+str(config.min_enemy_players)+" enemies that took longer than "+str(config.min_fight_duration)+" s."
    myprint(log, print_string, "info")

    players, fights, found_healing, found_barrier = collect_stat_data(args, config, log, args.anonymize)
    if (not fights) or all(fight.skipped for fight in fights):
        myprint(log, "Aborting!", "info")
        exit(1)

    if "xls" in config.files_to_write:
        # create xls file if it doesn't exist
        book = xlwt.Workbook(encoding="utf-8")
        book.add_sheet("fights overview")
        book.save(args.xls_output_filename)
    
    print_string = "Welcome to the CARROT AWARDS!\n"
    myprint(output, print_string, "info", config)

    # print overall stats
    overall_squad_stats = get_overall_squad_stats(fights, config)
    overall_raid_stats = get_overall_raid_stats(fights)
    total_fight_duration = get_total_fight_duration_in_hms(overall_raid_stats['used_fights_duration'])
    if 'console' in config.files_to_write or 'txt' in config.files_to_write:
        print_total_squad_stats(fights, overall_squad_stats, overall_raid_stats, total_fight_duration, found_healing, found_barrier, config, output)

    if 'console' in config.files_to_write or 'txt' in config.files_to_write:
        print_fights_overview(fights, overall_squad_stats, overall_raid_stats, config, output)
    if 'xls' in config.files_to_write:
        write_fights_overview_xls(fights, overall_squad_stats, overall_raid_stats, config, args.xls_output_filename)
    
    # print top x players for all stats. If less then x
    # players, print all. If x-th place doubled, print all with the
    # same amount of top x achieved.
    num_used_fights = overall_raid_stats['num_used_fights']

    top_total_stat_players = {key: list() for key in config.stats_to_compute}
    top_consistent_stat_players = {key: list() for key in config.stats_to_compute}
    top_average_stat_players = {key: list() for key in config.stats_to_compute}
    top_percentage_stat_players = {key: list() for key in config.stats_to_compute}
    percentage_comparison_val = {key: 0 for key in config.stats_to_compute}
    top_late_players = {key: list() for key in config.stats_to_compute}
    top_jack_of_all_trades_players = {key: list() for key in config.stats_to_compute}    
    
    for stat in config.stats_to_compute:
        if (stat == 'heal' and not found_healing) or (stat == 'barrier' and not found_barrier):
            continue

        top_consistent_stat_players[stat] = get_top_players(players, config, stat, StatType.CONSISTENT)
        top_total_stat_players[stat] = get_top_players(players, config, stat, StatType.TOTAL)
        top_average_stat_players[stat] = get_top_players(players, config, stat, StatType.AVERAGE)            
        top_percentage_stat_players[stat],percentage_comparison_val[stat] = get_top_percentage_players(players, config, stat, StatType.PERCENTAGE, num_used_fights, top_consistent_stat_players[stat])

    if 'console' in config.files_to_write or 'txt' in config.files_to_write:
        for stat in config.stats_to_compute:
            myprint(output, config.stat_names[stat].upper()+" AWARDS\n", "info", config)
            
            if stat == 'dist':
                #write_sorted_top_percentage(players, top_percentage_stat_players[stat], percentage_comparison_val[stat], config, num_used_fights, stat, output)
                write_sorted_top_consistent_or_avg(players, top_average_stat_players[stat], config, num_used_fights, stat, StatType.AVERAGE, output)
            elif stat == 'dmg_taken':
                write_sorted_top_consistent_or_avg(players, top_average_stat_players[stat], config, num_used_fights, stat, StatType.AVERAGE, output)
            else:
                write_sorted_top_consistent_or_avg(players, top_consistent_stat_players[stat], config, num_used_fights, stat, StatType.CONSISTENT, output)                
                write_sorted_total(players, top_total_stat_players[stat], config, total_fight_duration, stat, output)
                write_sorted_top_consistent_or_avg(players, top_average_stat_players[stat], config, num_used_fights, stat, StatType.AVERAGE, output)
                write_sorted_top_percentage(players, top_percentage_stat_players[stat], percentage_comparison_val[stat], config, num_used_fights, stat, output)

    if 'json' in config.files_to_write:
        write_to_json(overall_raid_stats, overall_squad_stats, fights, players, top_total_stat_players, top_average_stat_players, top_consistent_stat_players, top_percentage_stat_players, top_late_players, top_jack_of_all_trades_players, args.json_output_filename)

    if 'xls' in config.files_to_write:
        for stat in config.stats_to_compute:
            if stat == 'dist':
                write_stats_xls(players, top_average_stat_players[stat], stat, args.xls_output_filename, config)
            elif 'dmg_taken' in stat:
                write_stats_xls(players, top_average_stat_players[stat], stat, args.xls_output_filename, config)
            elif 'heal' in stat and stat != 'heal_from_regen' and found_healing:
                write_stats_xls(players, top_total_stat_players[stat], stat, args.xls_output_filename, config)            
            elif stat == 'barrier' and found_barrier:
                write_stats_xls(players, top_total_stat_players[stat], stat, args.xls_output_filename, config)
            elif stat == 'deaths':
                write_stats_xls(players, top_consistent_stat_players[stat], stat, args.xls_output_filename, config)
            else:
                write_stats_xls(players, top_total_stat_players[stat], stat, args.xls_output_filename, config)
