#!/usr/bin/env python3

#    parse_top_stats_sneak_peek.py outputs a sneak peek of top stats in arcdps logs as parsed by Elite Insights.
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
    parser.add_argument('-c', '--config_file', dest="config_file", help="Config file with all the settings", default="parser_config_sneak_peek")    
    args = parser.parse_args()

    if not os.path.isdir(args.xml_directory):
        print("Directory ",args.xml_directory," is not a directory or does not exist!")
        sys.exit()
    if args.output_filename is None:
        args.output_filename = args.xml_directory+"/top_stats_sneak_peek.txt"
    if args.xls_output_filename is None:
        args.xls_output_filename = args.xml_directory+"/top_stats_sneak_peek.xls"        
    if args.log_file is None:
        args.log_file = args.xml_directory+"/log_sneak_peek.txt"

    output = open(args.output_filename, "w")
    log = open(args.log_file, "w")

    parser_config = importlib.import_module("parser_configs."+args.config_file , package=None) 
    config = fill_config(parser_config)

    print_string = "Using xml directory "+args.xml_directory+", writing output to "+args.output_filename+" and log to "+args.log_file
    print(print_string)
    print_string = "Considering fights with at least "+str(config.min_allied_players)+" allied players and at least "+str(config.min_enemy_players)+" enemies that took longer than "+str(config.min_fight_duration)+" s."
    myprint(log, print_string)

    players, fights, found_healing = collect_stat_data(args, config, log)

    used_fights_duration = sum([f.duration for f in fights if not f.skipped])
    total_fight_duration = {}
    total_fight_duration["h"] = int(used_fights_duration/3600)
    total_fight_duration["m"] = int((used_fights_duration - total_fight_duration["h"]*3600) / 60)
    total_fight_duration["s"] = int(used_fights_duration - total_fight_duration["h"]*3600 -  total_fight_duration["m"]*60)

    # create xls file if it doesn't exist
    book = xlwt.Workbook(encoding="utf-8")
    book.add_sheet("fights overview")
    book.save(args.xls_output_filename)
    
    print_string = "Welcome to the raid sneak peek!"
    myprint(output, print_string)

    # print top x players for dmg, strips and condi cleanse.
    # If less then x
    # players, print all. If x-th place doubled, print all with the
    # same amount of top x achieved.

    top_total_damagers = write_sorted_total(players, config, total_fight_duration, 'dmg', output)
    write_stats_xls(players, top_total_damagers, 'dmg', args.xls_output_filename)    
    top_total_strippers = write_sorted_total(players, config, total_fight_duration, 'rips', output)
    write_stats_xls(players, top_total_strippers, 'rips', args.xls_output_filename)    
    top_total_cleansers = write_sorted_total(players, config, total_fight_duration, 'cleanses', output)
    write_stats_xls(players, top_total_cleansers, 'cleanses', args.xls_output_filename)        
