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
import xml.etree.ElementTree as ET
from enum import Enum
import importlib
import xlwt

from parse_top_stats_tools import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='This reads a set of arcdps reports in xml format and generates top stats.')
    parser.add_argument('xml_directory', help='Directory containing .xml files from arcdps reports')
    parser.add_argument('-o', '--output', dest="output_filename", help="Text file to write the computed top stats")
    parser.add_argument('-x', '--xls_output', dest="xls_output_filename", help="Text file to write the computed top stats")
    parser.add_argument('-l', '--log_file', dest="log_file", help="Logging file with all the output")
    parser.add_argument('-c', '--config_file', dest="config_file", help="Config file with all the settings", default="parser_config_detailed")    
    args = parser.parse_args()

    if not os.path.isdir(args.xml_directory):
        print("Directory ",args.xml_directory," is not a directory or does not exist!")
        sys.exit()
    if args.output_filename is None:
        args.output_filename = args.xml_directory+"/top_stats_detailed.txt"
    if args.xls_output_filename is None:
        args.xls_output_filename = args.xml_directory+"/top_stats_detailed.xls"        
    if args.log_file is None:
        args.log_file = args.xml_directory+"/log_detailed.txt"

    output = open(args.output_filename, "w")
    log = open(args.log_file, "w")

    parser_config = importlib.import_module("parser_configs."+args.config_file , package=None) 
    
    config = Config()
    config.num_players_listed = parser_config.num_players_listed
    config.num_players_considered_top = parser_config.num_players_considered_top

    config.min_attendance_portion_for_late = parser_config.attendance_percentage_for_late/100.
    config.min_attendance_portion_for_buildswap = parser_config.attendance_percentage_for_buildswap/100.

    config.portion_of_top_for_consistent = parser_config.percentage_of_top_for_consistent/100.
    config.portion_of_top_for_total = parser_config.percentage_of_top_for_total/100.
    config.portion_of_top_for_late = parser_config.percentage_of_top_for_late/100.
    config.portion_of_top_for_buildswap = parser_config.percentage_of_top_for_buildswap/100.

    config.min_allied_players = parser_config.min_allied_players
    config.min_fight_duration = parser_config.min_fight_duration
    config.min_enemy_players = parser_config.min_enemy_players

    config.stat_names = parser_config.stat_names
    config.profession_abbreviations = parser_config.profession_abbreviations

    print_string = "Using xml directory "+args.xml_directory+", writing output to "+args.output_filename+" and log to "+args.log_file
    print(print_string)
    print_string = "Considering fights with at least "+str(config.min_allied_players)+" allied players and at least "+str(config.min_enemy_players)+" enemies that took longer than "+str(config.min_fight_duration)+" s."
    myprint(log, print_string)

    players, fights, found_healing = collect_stat_data(args, config, log)

    # create xls file if it doesn't exist
    book = xlwt.Workbook(encoding="utf-8")
    book.add_sheet("fights overview")
    book.save(args.xls_output_filename)
    
    print_string = "Welcome to the CARROT AWARDS!\n"
    myprint(output, print_string)

    # print overall stats
    overall_squad_stats = get_overall_squad_stats(fights)
    total_fight_duration = print_total_squad_stats(fights, overall_squad_stats, found_healing, output)

    print_fights_overview(fights, overall_squad_stats, output)
    write_fights_overview_xls(fights, overall_squad_stats, args.xls_output_filename)
    
    # print top x players for all stats. If less then x
    # players, print all. If x-th place doubled, print all with the
    # same amount of top x achieved.
    num_used_fights = len([f for f in fights if not f.skipped])
    myprint(output, "DAMAGE AWARDS\n")
    top_consistent_damagers = write_sorted_top_x(players, config, num_used_fights, 'dmg', output)
    top_total_damagers = write_sorted_total(players, config, total_fight_duration, 'dmg', output, args.xls_output_filename)    
    #myprint(output, "\n")    
        
    myprint(output, "BOON STRIPS AWARDS\n")        
    top_consistent_strippers = write_sorted_top_x(players, config, num_used_fights, 'rips', output)
    top_total_strippers = write_sorted_total(players, config, total_fight_duration, 'rips', output, args.xls_output_filename)    
    #myprint(output, "\n")            
    
    myprint(output, "CONDITION CLEANSES AWARDS\n")        
    top_consistent_cleansers = write_sorted_top_x(players, config, num_used_fights, 'cleanses', output)
    top_total_cleansers = write_sorted_total(players, config, total_fight_duration, 'cleanses', output, args.xls_output_filename)
    #myprint(output, "\n")    
        
    myprint(output, "STABILITY OUTPUT AWARDS \n")        
    top_consistent_stabbers = write_sorted_top_x(players, config, num_used_fights, 'stab', output)
    top_total_stabbers = write_sorted_total(players, config, total_fight_duration, 'stab', output, args.xls_output_filename)    
    #myprint(output, "\n")    
    
    top_consistent_healers = list()
    if found_healing:
        myprint(output, "HEALING AWARDS\n")        
        top_consistent_healers = write_sorted_top_x(players, config, num_used_fights, 'heal', output)
        top_total_healers = write_sorted_total(players, config, total_fight_duration, 'heal', output, args.xls_output_filename)   
        #myprint(output, "\n")    
    
    myprint(output, "SHORTEST DISTANCE TO TAG AWARDS\n")
    top_consistent_distancers = write_sorted_top_x(players, config, num_used_fights, 'dist', output)
    write_total_stats_xls(players, top_consistent_distancers, 'dist', args.xls_output_filename)
    #myprint(output, "\n")
