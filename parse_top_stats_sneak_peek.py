#!/usr/bin/env python3
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
    
    config = Config()
    config.num_players_listed = parser_config.num_players_listed
    config.num_players_considered_top = parser_config.num_players_considered_top

    config.portion_of_top_for_total = parser_config.percentage_of_top_for_total/100.

    config.min_allied_players = parser_config.min_allied_players
    config.min_fight_duration = parser_config.min_fight_duration
    config.min_enemy_players = parser_config.min_enemy_players

    config.stat_names = parser_config.stat_names
    config.profession_abbreviations = parser_config.profession_abbreviations

    print_string = "Using xml directory "+args.xml_directory+", writing output to "+args.output_filename+" and log to "+args.log_file
    print(print_string)
    print_string = "Considering fights with at least "+str(config.min_allied_players)+" allied players and at least "+str(config.min_enemy_players)+" enemies that took longer than "+str(config.min_fight_duration)+" s."
    myprint(log, print_string)

    players, overall_squad_stats, used_fights_duration, used_fights, total_fights, num_players_per_fight, found_healing = collect_stat_data(args, config, log)

    total_fight_duration = {}
    total_fight_duration["h"] = int(used_fights_duration/3600)
    total_fight_duration["m"] = int((used_fights_duration - total_fight_duration["h"]*3600) / 60)
    total_fight_duration["s"] = int(used_fights_duration - total_fight_duration["h"]*3600 -  total_fight_duration["m"]*60)

    # create xls file if it doesn't exist
    book = xlwt.Workbook(encoding="utf-8")
    book.add_sheet("dummy")
    book.save(args.xls_output_filename)
    
    print_string = "Welcome to the raid sneak peek!"
    myprint(output, print_string)

    # print top x players for dmg, strips and condi cleanse.
    # If less then x
    # players, print all. If x-th place doubled, print all with the
    # same amount of top x achieved.

    top_total_damagers = write_sorted_total(players, config, total_fight_duration, 'dmg', output, args.xls_output_filename)    
    #myprint(output, "\n")    
        
    top_total_strippers = write_sorted_total(players, config, total_fight_duration, 'rips', output, args.xls_output_filename)    
    #myprint(output, "\n")            

    top_total_cleansers = write_sorted_total(players, config, total_fight_duration, 'cleanses', output, args.xls_output_filename)
    #myprint(output, "\n")    
