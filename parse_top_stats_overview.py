#!/usr/bin/env python3

#    parse_top_stats_overview.py outputs a rough overview of top stats in arcdps logs as parsed by Elite Insights.
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
import xml.etree.ElementTree as ET
from enum import Enum
import importlib
import xlwt

from parse_top_stats_tools import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='This reads a set of arcdps reports in xml format and generates top stats.')
    parser.add_argument('input_directory', help='Directory containing .xml or .json files from arcdps reports')
    parser.add_argument('-o', '--output', dest="output_filename", help="Text file to write the computed top stats")
    parser.add_argument('-f', '--input_filetype', dest="filetype", help="filetype of input files. Currently supports json and xml, defaults to json.", default="json")
    parser.add_argument('-x', '--xls_output', dest="xls_output_filename", help="xls file to write the computed top stats")    
    parser.add_argument('-j', '--json_output', dest="json_output_filename", help="json file to write the computed top stats to")    
    parser.add_argument('-l', '--log_file', dest="log_file", help="Logging file with all the output")
    parser.add_argument('-c', '--config_file', dest="config_file", help="Config file with all the settings", default="parser_config_overview")    
    args = parser.parse_args()

    if not os.path.isdir(args.input_directory):
        print("Directory ",args.input_directory," is not a directory or does not exist!")
        sys.exit()
    if args.output_filename is None:
        args.output_filename = args.input_directory+"/top_stats_overview.txt"
    if args.xls_output_filename is None:
        args.xls_output_filename = args.input_directory+"/top_stats_overview.xls"
    if args.json_output_filename is None:
        args.json_output_filename = args.input_directory+"/top_stats_overview.json"                
    if args.log_file is None:
        args.log_file = args.input_directory+"/log_overview.txt"

    output = open(args.output_filename, "w")
    log = open(args.log_file, "w")

    parser_config = importlib.import_module("parser_configs."+args.config_file , package=None) 
    
    config = fill_config(parser_config)

    print_string = "Using input directory "+args.input_directory+", writing output to "+args.output_filename+" and log to "+args.log_file
    print(print_string)
    print_string = "Considering fights with at least "+str(config.min_allied_players)+" allied players and at least "+str(config.min_enemy_players)+" enemies that took longer than "+str(config.min_fight_duration)+" s."
    myprint(log, print_string)

    players, fights, found_healing, found_barrier = collect_stat_data(args, config, log)    

    # create xls file if it doesn't exist
    book = xlwt.Workbook(encoding="utf-8")
    book.add_sheet("fights overview")
    book.save(args.xls_output_filename)
    
    print_string = "Welcome to the CARROT AWARDS!\n"
    myprint(output, print_string)

    # print overall stats
    overall_squad_stats = get_overall_squad_stats(fights, config)
    total_fight_duration = print_total_squad_stats(fights, overall_squad_stats, found_healing, output)
    write_fights_overview_xls(fights, overall_squad_stats, args.xls_output_filename)    
    num_used_fights = len([f for f in fights if not f.skipped])
    
    # print top x players for all stats. If less then x
    # players, print all. If x-th place doubled, print all with the
    # same amount of top x achieved.

    top_total_stat_players = {key: list() for key in config.stats_to_compute}
    top_consistent_stat_players = {key: list() for key in config.stats_to_compute}
    top_percentage_stat_players = {key: list() for key in config.stats_to_compute}
    top_late_players = {key: list() for key in config.stats_to_compute}
    top_jack_of_all_trades_players = {key: list() for key in config.stats_to_compute}
    
    for stat in config.stats_to_compute:
        if (stat == 'heal' and not found_healing) or (stat == 'barrier' and not found_barrier):
            continue

        if stat == 'barrier' or stat == 'deaths' or stat == 'kills':
            top_consistent_stat_players[stat] = get_top_players(players, config, stat, StatType.CONSISTENT)
            top_total_stat_players[stat] = get_top_players(players, config, stat, StatType.TOTAL)
            top_percentage_stat_players[stat],comparison_val = get_top_percentage_players(players, config, stat, StatType.PERCENTAGE, num_used_fights, top_consistent_stat_players[stat], top_total_stat_players[stat], list(), list())
        else:
            myprint(output, config.stat_names[stat].upper()+" AWARDS\n")
            if stat == 'dist':
                top_consistent_stat_players[stat] = get_top_players(players, config, stat, StatType.CONSISTENT)
                top_total_stat_players[stat] = get_top_players(players, config, stat, StatType.TOTAL)
                top_percentage_stat_players[stat] = write_sorted_top_percentage(players, config, num_used_fights, stat, output, StatType.PERCENTAGE, top_consistent_stat_players[stat])
            else:
                top_consistent_stat_players[stat] = write_sorted_top_consistent(players, config, num_used_fights, stat, output)
                top_total_stat_players[stat] = write_sorted_total(players, config, total_fight_duration, stat, output)
                top_percentage_stat_players[stat],comparison_val = get_top_percentage_players(players, config, stat, StatType.PERCENTAGE, num_used_fights, top_consistent_stat_players[stat], top_total_stat_players[stat], list(), list())
        top_late_players[stat],comparison_percentage = get_top_percentage_players(players, config, stat, StatType.LATE_PERCENTAGE, num_used_fights, top_consistent_stat_players[stat], top_total_stat_players[stat], top_percentage_stat_players[stat], list())            
        top_jack_of_all_trades_players[stat],comparison_percentage = get_top_percentage_players(players, config, stat, StatType.SWAPPED_PERCENTAGE, num_used_fights, top_consistent_stat_players[stat], top_total_stat_players[stat], top_percentage_stat_players[stat], top_late_players[stat])

    write_to_json(overall_squad_stats, fights, players, top_total_stat_players, top_consistent_stat_players, top_percentage_stat_players, top_late_players, top_jack_of_all_trades_players, args.json_output_filename)

    for stat in config.stats_to_compute:
        if stat == 'dist':
            write_stats_xls(players, top_percentage_stat_players[stat], stat, args.xls_output_filename)
        elif stat == 'heal' and found_healing:
            write_stats_xls(players, top_total_stat_players[stat], stat, args.xls_output_filename)            
        elif stat == 'barrier' and found_barrier:
            write_stats_xls(players, top_total_stat_players[stat], stat, args.xls_output_filename)
        else:
            write_stats_xls(players, top_total_stat_players[stat], stat, args.xls_output_filename)

    if any(len(top_late_players[stat]) > 0 for stat in config.stats_to_compute):
        myprint(output, 'SPECIAL "LATE BUT GREAT" MENTIONS\n')
        for stat in config.stats_to_compute:
            write_sorted_top_percentage(players, config, num_used_fights, stat, output, StatType.LATE_PERCENTAGE, top_consistent_stat_players[stat], top_total_stat_players[stat])

    if any(len(top_jack_of_all_trades_players[stat]) > 0 for stat in config.stats_to_compute):
        myprint(output, 'JACK OF ALL TRADES (swapped build at least once)\n')
        for stat in config.stats_to_compute:
            write_sorted_top_percentage(players, config, num_used_fights, stat, output, StatType.SWAPPED_PERCENTAGE, top_consistent_stat_players[stat], top_total_stat_players[stat], top_late_players[stat])
    
