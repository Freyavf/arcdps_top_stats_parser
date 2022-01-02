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
    parser.add_argument('xml_directory', help='Directory containing .xml files from arcdps reports')
    parser.add_argument('-o', '--output', dest="output_filename", help="Text file to write the computed top stats")
    parser.add_argument('-x', '--xls_output', dest="xls_output_filename", help="Text file to write the computed top stats")
    parser.add_argument('-l', '--log_file', dest="log_file", help="Logging file with all the output")
    parser.add_argument('-c', '--config_file', dest="config_file", help="Config file with all the settings", default="parser_config_overview")    
    args = parser.parse_args()

    if not os.path.isdir(args.xml_directory):
        print("Directory ",args.xml_directory," is not a directory or does not exist!")
        sys.exit()
    if args.output_filename is None:
        args.output_filename = args.xml_directory+"/top_stats_overview.txt"
    if args.xls_output_filename is None:
        args.xls_output_filename = args.xml_directory+"/top_stats_overview.xls"        
    if args.log_file is None:
        args.log_file = args.xml_directory+"/log_overview.txt"

    output = open(args.output_filename, "w")
    log = open(args.log_file, "w")

    parser_config = importlib.import_module("parser_configs."+args.config_file , package=None) 
    
    config = fill_config(parser_config)

    print_string = "Using xml directory "+args.xml_directory+", writing output to "+args.output_filename+" and log to "+args.log_file
    print(print_string)
    print_string = "Considering fights with at least "+str(config.min_allied_players)+" allied players and at least "+str(config.min_enemy_players)+" enemies that took longer than "+str(config.min_fight_duration)+" s."
    myprint(log, print_string)

    players, fights, found_healing, found_barrier = collect_stat_data_from_xml(args, config, log)

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
    
    # print top x players for all stats. If less then x
    # players, print all. If x-th place doubled, print all with the
    # same amount of top x achieved.
    num_used_fights = len([f for f in fights if not f.skipped])
    myprint(output, "DAMAGE AWARDS\n")
    top_consistent_damagers = write_sorted_top_consistent(players, config, num_used_fights, 'dmg', output)
    top_total_damagers = write_sorted_total(players, config, total_fight_duration, 'dmg', output)
    write_stats_xls(players, top_total_damagers, 'dmg', args.xls_output_filename)
    
    myprint(output, "BOON STRIPS AWARDS\n")        
    top_consistent_strippers = write_sorted_top_consistent(players, config, num_used_fights, 'rips', output)
    top_total_strippers = write_sorted_total(players, config, total_fight_duration, 'rips', output)
    write_stats_xls(players, top_total_strippers, 'rips', args.xls_output_filename)    
    
    myprint(output, "CONDITION CLEANSES AWARDS\n")        
    top_consistent_cleansers = write_sorted_top_consistent(players, config, num_used_fights, 'cleanses', output)
    top_total_cleansers = write_sorted_total(players, config, total_fight_duration, 'cleanses', output)
    write_stats_xls(players, top_total_cleansers, 'cleanses', args.xls_output_filename)        
        
    myprint(output, "STABILITY OUTPUT AWARDS \n")        
    top_consistent_stabbers = write_sorted_top_consistent(players, config, num_used_fights, 'stab', output)
    top_total_stabbers = write_sorted_total(players, config, total_fight_duration, 'stab', output)
    write_stats_xls(players, top_total_stabbers, 'stab', args.xls_output_filename)            
    
    top_consistent_healers = list()
    if found_healing:
        myprint(output, "HEALING AWARDS\n")        
        top_consistent_healers = write_sorted_top_consistent(players, config, num_used_fights, 'heal', output)
        top_total_healers = write_sorted_total(players, config, total_fight_duration, 'heal', output)
        write_stats_xls(players, top_total_healers, 'heal', args.xls_output_filename)                    

    top_consistent_barriers = list()
    if found_barrier:
        myprint(output, "BARRIER AWARDS\n")        
        top_consistent_barriers = write_sorted_top_consistent(players, config, num_used_fights, 'barrier', output)
        top_total_barriers = write_sorted_total(players, config, total_fight_duration, 'barrier', output)
        write_stats_xls(players, top_total_barriers, 'barrier', args.xls_output_filename)                    

        
    myprint(output, "SHORTEST DISTANCE TO TAG AWARDS\n")
    top_consistent_distancers = get_top_players(players, config, 'dist', StatType.CONSISTENT)
    top_percentage_distancers = write_sorted_top_percentage(players, config, num_used_fights, 'dist', output, StatType.PERCENTAGE, top_consistent_distancers)
    write_stats_xls(players, top_percentage_distancers, 'dist', args.xls_output_filename)    
    
    myprint(output, 'SPECIAL "LATE BUT GREAT" MENTIONS\n')        
    top_late_damagers = write_sorted_top_percentage(players, config, num_used_fights, 'dmg', output, StatType.LATE_PERCENTAGE, top_consistent_damagers, top_total_damagers)
    top_late_strippers = write_sorted_top_percentage(players, config, num_used_fights, 'rips', output, StatType.LATE_PERCENTAGE, top_consistent_strippers, top_total_strippers)
    top_late_cleansers = write_sorted_top_percentage(players, config, num_used_fights, 'cleanses', output, StatType.LATE_PERCENTAGE, top_consistent_cleansers, top_total_cleansers)
    top_late_stabbers = write_sorted_top_percentage(players, config, num_used_fights, 'stab', output, StatType.LATE_PERCENTAGE, top_consistent_stabbers, top_total_stabbers)
    top_late_healers = write_sorted_top_percentage(players, config, num_used_fights, 'heal', output, StatType.LATE_PERCENTAGE, top_consistent_healers, top_total_healers)
    top_late_distancers = write_sorted_top_percentage(players, config, num_used_fights, 'dist', output, StatType.LATE_PERCENTAGE, top_consistent_distancers)    
    
    myprint(output, 'JACK OF ALL TRADES (swapped build at least once)\n')        
    write_sorted_top_percentage(players, config, num_used_fights, 'dmg', output, StatType.SWAPPED_PERCENTAGE, top_consistent_damagers, top_total_damagers, top_late_damagers)
    write_sorted_top_percentage(players, config, num_used_fights, 'rips', output, StatType.SWAPPED_PERCENTAGE, top_consistent_strippers, top_total_strippers, top_late_strippers)
    write_sorted_top_percentage(players, config, num_used_fights, 'cleanses', output, StatType.SWAPPED_PERCENTAGE, top_consistent_cleansers, top_total_cleansers, top_late_cleansers)
    write_sorted_top_percentage(players, config, num_used_fights, 'stab', output, StatType.SWAPPED_PERCENTAGE, top_consistent_stabbers, top_total_stabbers, top_late_stabbers)
    write_sorted_top_percentage(players, config, num_used_fights, 'heal', output, StatType.SWAPPED_PERCENTAGE, top_consistent_healers, top_total_healers, top_late_healers)
    write_sorted_top_percentage(players, config, num_used_fights, 'dist', output, StatType.SWAPPED_PERCENTAGE, top_consistent_distancers, top_late_distancers)    
    
