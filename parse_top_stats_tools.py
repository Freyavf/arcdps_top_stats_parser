#!/usr/bin/env python3

#    parse_top_stats_tools.py contains tools for computing top stats in arcdps logs as parsed by Elite Insights.
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


from dataclasses import dataclass,field
import os.path
from os import listdir
import sys
import xml.etree.ElementTree as ET
from enum import Enum
import importlib
import xlrd
from xlutils.copy import copy
import json
import jsons

debug = False # enable / disable debug output

class StatType(Enum):
    TOTAL = 1
    CONSISTENT = 2
    LATE_PERCENTAGE = 3
    SWAPPED_PERCENTAGE = 4
    PERCENTAGE = 5
    

# This class stores information about a player. Note that a different profession will be treated as a new player / character.
@dataclass
class Player:
    account: str                        # account name
    name: str                           # character name
    profession: str                     # profession name
    num_fights_present: int = 0         # the number of fight the player was involved in 
    attendance_percentage: float = 0.   # the percentage of fights the player was involved in out of all fights
    duration_fights_present: int = 0    # the total duration of all fights the player was involved in
    swapped_build: bool = False         # a different player character or specialization with this account name was in some of the fights

    # fields for all stats defined in config
    consistency_stats: dict = field(default_factory=dict)     # how many times did this player get into top for each stat?
    total_stats: dict = field(default_factory=dict)           # what's the total value for this player for each stat?
    average_stats: dict = field(default_factory=dict)         # what's the average stat per second for this player? (exception: kills and deaths are per minute)
    portion_top_stats: dict = field(default_factory=dict)     # what percentage of fights did this player get into top for each stat, in relation to the number of fights they were involved in?
    stats_per_fight: list = field(default_factory=list)       # what's the value of each stat for this player in each fight?

    def initialize(self, config):
        self.total_stats = {key: 0 for key in config.stats_to_compute}
        self.average_stats = {key: 0 for key in config.stats_to_compute}        
        self.consistency_stats = {key: 0 for key in config.stats_to_compute}
        self.portion_top_stats = {key: 0 for key in config.stats_to_compute}


# This class stores information about a fight
@dataclass
class Fight:
    skipped: bool = False
    duration: int = 0
    total_stats: dict = field(default_factory=dict) # what's the over total value for the whole squad for each stat in this fight?
    enemies: int = 0
    allies: int = 0
    start_time: str = ""
    
    
# This class stores the configuration for running the top stats.
@dataclass
class Config:
    # fields for all stats: dmg, rips, stab, cleanses, heal, dist, deaths, kills
    num_players_listed: dict = field(default_factory=dict)          # How many players will be listed who achieved top stats most often for each stat?
    num_players_considered_top: dict = field(default_factory=dict)  # How many players are considered to be "top" in each fight for each stat?
    
    min_attendance_portion_for_percentage: float = 0.  # For what portion of all fights does a player need to be there to be considered for "percentage" awards?
    min_attendance_portion_for_late: float = 0.        # For what portion of all fights does a player need to be there to be considered for "late but great" awards?     
    min_attendance_portion_for_buildswap: float = 0.   # For what portion of all fights does a player need to be there to be considered for "jack of all trades" awards? 

    portion_of_top_for_total: float = 0.         # What portion of the top total player stat does someone need to reach to be considered for total awards?
    portion_of_top_for_consistent: float = 0.    # What portion of the total stat of the top consistent player does someone need to reach to be considered for consistency awards?
    portion_of_top_for_percentage: float = 0.    # What portion of the consistency stat of the top consistent player does someone need to reach to be considered for percentage awards?    
    portion_of_top_for_late: float = 0.          # What portion of the percentage the top consistent player reached top does someone need to reach to be considered for late but great awards?
    portion_of_top_for_buildswap: float = 0.     # What portion of the percentage the top consistent player reached top does someone need to reach to be considered for jack of all trades awards?

    min_allied_players: int = 0   # minimum number of allied players to consider a fight in the stats
    min_fight_duration: int = 0   # minimum duration of a fight to be considered in the stats
    min_enemy_players: int = 0    # minimum number of enemies to consider a fight in the stats

    stat_names: dict = field(default_factory=dict)
    profession_abbreviations: dict = field(default_factory=dict)

    empty_stats: dict = field(default_factory=dict)
    stats_to_compute: list = field(default_factory=list)

    buff_ids: dict = field(default_factory=dict)
    buffs_stacking_duration: list = field(default_factory=list)
    buffs_stacking_intensity: list = field(default_factory=list)
    buff_abbrev: dict = field(default_factory=dict)
    

    
# prints output_string to the console and the output_file, with a linebreak at the end
def myprint(output_file, output_string):
    print(output_string)
    output_file.write(output_string+"\n")



# fills a Config with the given input    
def fill_config(config_input):
    config = Config()
    config.num_players_listed = config_input.num_players_listed
    config.num_players_considered_top = config_input.num_players_considered_top

    config.min_attendance_portion_for_percentage = config_input.attendance_percentage_for_percentage/100.
    config.min_attendance_portion_for_late = config_input.attendance_percentage_for_late/100.    
    config.min_attendance_portion_for_buildswap = config_input.attendance_percentage_for_buildswap/100.

    config.portion_of_top_for_consistent = config_input.percentage_of_top_for_consistent/100.
    config.portion_of_top_for_total = config_input.percentage_of_top_for_total/100.
    config.portion_of_top_for_percentage = config_input.percentage_of_top_for_percentage/100.
    config.portion_of_top_for_late = config_input.percentage_of_top_for_late/100.    
    config.portion_of_top_for_buildswap = config_input.percentage_of_top_for_buildswap/100.

    config.min_allied_players = config_input.min_allied_players
    config.min_fight_duration = config_input.min_fight_duration
    config.min_enemy_players = config_input.min_enemy_players

    config.stat_names = config_input.stat_names
    config.profession_abbreviations = config_input.profession_abbreviations

    config.stats_to_compute = config_input.stats_to_compute
    config.empty_stats = {stat: -1 for stat in config.stats_to_compute}

    config.buff_abbrev["Stability"] = 'stab'
    config.buff_abbrev["Protection"] = 'prot'
    config.buff_abbrev["Aegis"] = 'aegis'
    config.buff_abbrev["Might"] = 'might'
    config.buff_abbrev["Fury"] = 'fury'
    
    return config
    
        
# For all players considered to be top in stat in this fight, increase
# the number of fights they reached top by 1 (i.e. increase
# consistency_stats[stat]).
# Input:
# players = list of all players
# sortedList = list of player names+profession, stat_value sorted by stat value in this fight
# config = configuration to use
# stat = stat that is considered
def increase_top_x_reached(players, sortedList, config, stat):
    # if stat isn't dist, increase top stats reached for the first num_players_considered_top players
    valid_values = 0
    if stat != 'dist':
        i = 0
        last_val = 0
        while i < len(sortedList) and (valid_values < config.num_players_considered_top[stat] or sortedList[i][1] == last_val) and players[sortedList[i][0]].total_stats[stat] > 0:
            if sortedList[i][1] < 0:
                i += 1
                continue
            players[sortedList[i][0]].consistency_stats[stat] += 1
            last_val = sortedList[i][1]
            i += 1
            valid_values += 1
        return

    # different for dist
    first_valid = True
    i = 0
    last_val = 0
    while i < len(sortedList) and (valid_values < config.num_players_considered_top[stat]+1 or sortedList[i][1] == last_val):
        # sometimes dist is -1, filter these out
        if sortedList[i][1] >= 0:
            # first valid dist is the comm, don't consider
            if first_valid:
                first_valid  = False
            else:
                players[sortedList[i][0]].consistency_stats[stat] += 1
                valid_values += 1
        last_val = sortedList[i][1]
        i += 1


        
# sort the list of players by total value in stat
# Input:
# players = list of all Players
# stat = stat that is considered
# fight_num = number of the fight that is considered
# Output:
# list of player index and total stat value, sorted by total stat value
def sort_players_by_value_in_fight(players, stat, fight_num):
    decorated = [(player.stats_per_fight[fight_num][stat], i, player) for i, player in enumerate(players)]
    if stat == 'dist' or stat == 'dmg_taken':
        decorated.sort()
    else:
        decorated.sort(reverse=True)
    sorted_by_value = [(i, value) for value, i, player in decorated]
    return sorted_by_value



# sort the list of players by total value in stat
# Input:
# players = list of all Players
# stat = stat that is considered
# Output:
# list of player index and total stat value, sorted by total stat value
def sort_players_by_total(players, stat):
    decorated = [(player.total_stats[stat], i, player) for i, player in enumerate(players)]
    if stat == 'dist' or stat == 'dmg_taken':
        decorated.sort()
    else:
        decorated.sort(reverse=True)
    sorted_by_total = [(i, total) for total, i, player in decorated]
    return sorted_by_total



# sort the list of players by consistency value in stat
# Input:
# players = list of all Players
# stat = stat that is considered
# Output:
# list of player index and consistency stat value, sorted by consistency stat value (how often was top x reached)
def sort_players_by_consistency(players, stat):
    decorated = [(player.consistency_stats[stat], player.total_stats[stat], i, player) for i, player in enumerate(players)]
    decorated.sort(reverse=True)    
    sorted_by_consistency = [(i, consistency) for consistency, total, i, player in decorated]
    return sorted_by_consistency


# sort the list of players by percentage value in stat
# Input:
# players = list of all Players
# stat = stat that is considered
# Output:
# list of player index and percentage stat value, sorted by percentage stat value (how often was top x reached / number of fights attended)
def sort_players_by_percentage(players, stat):
    decorated = [(player.portion_top_stats[stat], player.consistency_stats[stat], player.total_stats[stat], i, player) for i, player in enumerate(players)]                
    decorated.sort(reverse=True)    
    sorted_by_percentage = [(i, percentage) for percentage, consistency, total, i, player in decorated]
    return sorted_by_percentage



# Input:
# players = list of Players
# config = the configuration being used to determine top players
# stat = which stat are we considering
# total_or_consistent = enum StatType, either StatType.TOTAL or StatType.CONSISTENT, we are getting the players with top total values or top consistency values.
# Output:
# list of player indices getting a consistency / total award
def get_top_players(players, config, stat, total_or_consistent):
    percentage = 0.
    sorted_index = []
    if total_or_consistent == StatType.TOTAL:
        percentage = float(config.portion_of_top_for_total)
        sorted_index = sort_players_by_total(players, stat)
    elif total_or_consistent == StatType.CONSISTENT:
        percentage = float(config.portion_of_top_for_consistent)
        sorted_index = sort_players_by_consistency(players, stat)
    else:
        print("ERROR: Called get_top_players for stats that are not total or consistent")
        return        
        
    top_value = players[sorted_index[0][0]].total_stats[stat] # using total value for both top consistent and top total 
    top_players = list()

    i = 0
    last_value = 0
    while i < len(sorted_index):
        new_value = sorted_index[i][1] # value by which was sorted, i.e. total or consistency
        # index must be lower than number of output desired OR list entry has same value as previous entry, i.e. double place
        if i >= config.num_players_listed[stat] and new_value != last_value:
            break
        last_value = new_value

        if stat == "dist" or players[sorted_index[i][0]].total_stats[stat] >= top_value*percentage:
            # if stat isn't distance, total value must be at least percentage % of top value
            top_players.append(sorted_index[i][0])

        i += 1

    return top_players
            


# Input:
# players = list of Players
# config = the configuration being used to determine top players
# stat = which stat are we considering
# late_or_swapping = which type of stat. can be StatType.PERCENTAGE, StatType.LATE_PERCENTAGE or StatType.SWAPPED_PERCENTAGE
# num_used_fights = number of fights considered for computing top stats
# top_consistent_players = list of top consistent player indices
# top_total_players = list of top total player indices
# top_percentage_players = list of top percentage player indices
# top_late_players = list of player indices with late but great awards
# Output:
# list of player indices getting a percentage award, value with which the percentage stat was compared
def get_top_percentage_players(players, config, stat, late_or_swapping, num_used_fights, top_consistent_players, top_total_players, top_percentage_players, top_late_players):    
    sorted_index = sort_players_by_percentage(players, stat)
    top_percentage = players[sorted_index[0][0]].portion_top_stats[stat]
    
    comparison_value = 0
    min_attendance = 0
    if late_or_swapping == StatType.LATE_PERCENTAGE:
        comparison_value = top_percentage * config.portion_of_top_for_late
        min_attendance = config.min_attendance_portion_for_late * num_used_fights
    elif late_or_swapping == StatType.SWAPPED_PERCENTAGE:
        comparison_value = top_percentage * config.portion_of_top_for_buildswap
        min_attendance = config.min_attendance_portion_for_buildswap * num_used_fights
    elif late_or_swapping == StatType.PERCENTAGE:
        comparison_value = top_percentage * config.portion_of_top_for_percentage
        min_attendance = config.min_attendance_portion_for_percentage * num_used_fights
    else:
        print("ERROR: Called get_top_percentage_players for stats that are not percentage, late_percentage or swapped_percentage")
        return

    top_players = list()

    last_value = 0
    for (ind, percent) in sorted_index:
        # player wasn't there for enough fights
        if players[ind].num_fights_present < min_attendance:
            continue
        # player was there for all fights -> not late or swapping
        if late_or_swapping != StatType.PERCENTAGE and players[ind].num_fights_present == num_used_fights:
            continue
        # player got a different award already -> not late or swapping
        if late_or_swapping != StatType.PERCENTAGE and (ind in top_consistent_players or ind in top_total_players or ind in top_percentage_players or ind in top_late_players):
            continue
        # stat type swapping, but player didn't swap build
        if late_or_swapping == StatType.SWAPPED_PERCENTAGE and not players[ind].swapped_build:
            continue
        # index must be lower than number of output desired OR list entry has same value as previous entry, i.e. double place
        if len(top_players) >= config.num_players_listed[stat] and percent != last_value:
            break
        last_value = percent

        if percent >= comparison_value:
            top_players.append(ind)

    return top_players, comparison_value
 


# get the professions of all players indicated by the indices. Additionally, get the length of the longest profession name.
# Input:
# players = list of all players
# indices = list of relevant indices
# config = config to use for top stats computation/printing
# Output:
# list of profession strings, maximum profession length
def get_professions_and_length(players, indices, config):
    profession_strings = list()
    profession_length = 0
    for i in indices:
        player = players[i]
        professions_str = config.profession_abbreviations[player.profession]
        profession_strings.append(professions_str)
        if len(professions_str) > profession_length:
            profession_length = len(professions_str)
    return profession_strings, profession_length



# Get and write the top x people who achieved top y in stat most often.
# Input:
# players = list of Players
# config = the configuration being used to determine the top consistent players
# num_used_fights = the number of fights that are being used in stat computation
# stat = which stat are we considering
# output_file = the file to write the output to
# Output:
# list of player indices that got a top consistency award
def get_and_write_sorted_top_consistent(players, config, num_used_fights, stat, output_file):
    top_consistent_players = get_top_players(players, config, stat, StatType.CONSISTENT)
    write_sorted_top_consistent(players, top_consistent_players, config, num_used_fights, stat, output_file)
    return top_consistent_players



# Write the top x people who achieved top y in stat most often.
# Input:
# players = list of Players
# top_consistent_players = list of Player indices considered top consistent players
# config = the configuration being used to determine the top consistent players
# num_used_fights = the number of fights that are being used in stat computation
# stat = which stat are we considering
# output_file = the file to write the output to
# Output:
# list of player indices that got a top consistency award
def write_sorted_top_consistent(players, top_consistent_players, config, num_used_fights, stat, output_file):
    max_name_length = max([len(players[i].name) for i in top_consistent_players])
    profession_strings, profession_length = get_professions_and_length(players, top_consistent_players, config)
    
    if stat == "dist":
        print_string = "Top "+str(config.num_players_considered_top[stat])+" "+config.stat_names[stat]+" consistency awards"
    else:
        print_string = "Top "+config.stat_names[stat]+" consistency awards (Max. "+str(config.num_players_considered_top[stat])+" people, min. "+str(round(config.portion_of_top_for_consistent*100.))+"% of most consistent)"
    myprint(output_file, print_string)
    print_string = "Most times placed in the top "+str(config.num_players_considered_top[stat])+". \nAttendance = number of fights a player was present out of "+str(num_used_fights)+" total fights."    
    myprint(output_file, print_string)
    print_string = "-------------------------------------------------------------------------------"    
    myprint(output_file, print_string)


    # print table header
    print_string = f"    {'Name':<{max_name_length}}" + f"  {'Class':<{profession_length}} "+" Attendance " + " Times Top"
    if stat != "dist":
        print_string += f" {'Total':>9}"
    if stat in config.buff_ids:
        print_string += f"  {'Average':>7}"
        
    myprint(output_file, print_string)    

    
    place = 0
    last_val = 0
    # print table
    for i in range(len(top_consistent_players)):
        player = players[top_consistent_players[i]]
        if player.consistency_stats[stat] != last_val:
            place += 1
        print_string = f"{place:>2}"+f". {player.name:<{max_name_length}} "+f" {profession_strings[i]:<{profession_length}} "+f" {player.num_fights_present:>10} "+f" {round(player.consistency_stats[stat]):>9}"
        if stat != "dist" and stat not in config.buff_ids:
            print_string += f" {round(player.total_stats[stat]):>9}"
        if stat in config.buffs_stacking_intensity:
            print_string += f" {player.total_stats[stat]:>8}s"+f" {player.average_stats[stat]:>8}"
        elif stat in config.buffs_stacking_duration:
            print_string += f" {player.total_stats[stat]:>8}s"+f" {player.average_stats[stat]:>7}%"            

        myprint(output_file, print_string)
        last_val = player.consistency_stats[stat]
    myprint(output_file, "\n")
        
                

# Write the top x people who achieved top total stat.
# Input:
# players = list of Players
# top_players = list of indices in players that are considered as top
# stat = which stat are we considering
# xls_output_filename = where to write to
def write_stats_xls(players, top_players, stat, xls_output_filename):
    book = xlrd.open_workbook(xls_output_filename)
    wb = copy(book)
    sheet1 = wb.add_sheet(stat)

    sheet1.write(0, 0, "Name")
    sheet1.write(0, 1, "Profession")
    sheet1.write(0, 2, "Attendance (number of fights)")
    sheet1.write(0, 3, "Attendance (duration fights)")
    sheet1.write(0, 4, "Times Top")
    sheet1.write(0, 5, "Percentage Top")
    sheet1.write(0, 6, "Total "+stat)
    if stat == 'deaths' or stat == 'kills':
        sheet1.write(0, 7, "Average "+stat+" per min")
    else:
        sheet1.write(0, 7, "Average "+stat+" per s")        

    for i in range(len(top_players)):
        player = players[top_players[i]]
        sheet1.write(i+1, 0, player.name)
        sheet1.write(i+1, 1, player.profession)
        sheet1.write(i+1, 2, player.num_fights_present)
        sheet1.write(i+1, 3, player.duration_fights_present)
        sheet1.write(i+1, 4, player.consistency_stats[stat])        
        sheet1.write(i+1, 5, round(player.portion_top_stats[stat]*100))
        sheet1.write(i+1, 6, round(player.total_stats[stat]))
        sheet1.write(i+1, 7, player.average_stats[stat])

    wb.save(xls_output_filename)


# Get and write the top x people who achieved top total stat.
# Input:
# players = list of Players
# config = the configuration being used to determine topx consistent players
# total_fight_duration = the total duration of all fights
# stat = which stat are we considering
# output_file = where to write to
# Output:
# list of top total player indices
def get_and_write_sorted_total(players, config, total_fight_duration, stat, output_file):
    # get players that get an award and their professions
    top_total_players = get_top_players(players, config, stat, StatType.TOTAL)
    write_sorted_total(players, top_total_players, config, total_fight_duration, stat, output_file)
    return top_total_players



# Write the top x people who achieved top total stat.
# Input:
# players = list of Players
# top_total_players = list of Player indices considered top total players
# config = the configuration being used to determine topx consistent players
# total_fight_duration = the total duration of all fights
# stat = which stat are we considering
# output_file = where to write to
# Output:
# list of top total player indices
def write_sorted_total(players, top_total_players, config, total_fight_duration, stat, output_file):
    max_name_length = max([len(players[i].name) for i in top_total_players])    
    profession_strings, profession_length = get_professions_and_length(players, top_total_players, config)
    profession_length = max(profession_length, 5)
    
    print_string = "Top overall "+config.stat_names[stat]+" awards (Max. "+str(config.num_players_listed[stat])+" people, min. "+str(round(config.portion_of_top_for_total*100.))+"% of 1st place)"
    myprint(output_file, print_string)
    print_string = "Attendance = total duration of fights attended out of "
    if total_fight_duration["h"] > 0:
        print_string += str(total_fight_duration["h"])+"h "
    print_string += str(total_fight_duration["m"])+"m "+str(total_fight_duration["s"])+"s."    
    myprint(output_file, print_string)
    print_string = "------------------------------------------------------------------------"
    myprint(output_file, print_string)


    # print table header
    print_string = f"    {'Name':<{max_name_length}}" + f"  {'Class':<{profession_length}} "+f" {'Attendance':>11}"+f" {'Total':>9}"
    if stat in config.buff_ids:
        print_string += f"  {'Average':>7}"
    myprint(output_file, print_string)    

    place = 0
    last_val = 0
    # print table
    for i in range(len(top_total_players)):
        player = players[top_total_players[i]]
        if player.total_stats[stat] != last_val:
            place += 1

        fight_time_h = int(player.duration_fights_present/3600)
        fight_time_m = int((player.duration_fights_present - fight_time_h*3600)/60)
        fight_time_s = int(player.duration_fights_present - fight_time_h*3600 - fight_time_m*60)

        print_string = f"{place:>2}"+f". {player.name:<{max_name_length}} "+f" {profession_strings[i]:<{profession_length}} "

        if fight_time_h > 0:
            print_string += f" {fight_time_h:>2}h {fight_time_m:>2}m {fight_time_s:>2}s"
        else:
            print_string += f" {fight_time_m:>6}m {fight_time_s:>2}s"

        if stat in config.buffs_stacking_duration:
            print_string += f" {round(player.total_stats[stat]):>8}s"
            print_string += f" {player.average_stats[stat]:>7}%"
        elif stat in config.buffs_stacking_intensity:
            print_string += f" {round(player.total_stats[stat]):>8}s"
            print_string += f" {player.average_stats[stat]:>8}"
        else:
            print_string += f" {round(player.total_stats[stat]):>9}"
        myprint(output_file, print_string)
        last_val = player.total_stats[stat]
    myprint(output_file, "\n")

   

# Get and write the top x people who achieved top in stat with the highest percentage. This only considers fights where each player was present, i.e., a player who was in 4 fights and achieved a top spot in 2 of them gets 50%, as does a player who was only in 2 fights and achieved a top spot in 1 of them.
# Input:
# players = list of Players
# config = the configuration being used to determine topx consistent players
# num_used_fights = the number of fights that are being used in stat computation
# stat = which stat are we considering
# output_file = file to write to
# late_or_swapping = which type of stat. can be StatType.PERCENTAGE, StatType.LATE_PERCENTAGE or StatType.SWAPPED_PERCENTAGE
# top_consistent_players = list with indices of top consistent players
# top_total_players = list with indices of top total players
# top_percentage_players = list with indices of players with top percentage award
# top_late_players = list with indices of players who got a late but great award
# Output:
# list of players that got a top percentage award (or late but great or jack of all trades)
def get_and_write_sorted_top_percentage(players, config, num_used_fights, stat, output_file, late_or_swapping, top_consistent_players, top_total_players = list(), top_percentage_players = list(), top_late_players = list()):
    # get names that get on the list and their professions
    top_percentage_players, comparison_percentage = get_top_percentage_players(players, config, stat, late_or_swapping, num_used_fights, top_consistent_players, top_total_players, top_percentage_players, top_late_players)
    write_sorted_top_percentage(players, top_percentage_players, comparison_percentage, config, num_used_fights, stat, output_file, late_or_swapping, top_consistent_players, top_total_players, top_percentage_players, top_late_players)
    return top_percentage_players, comparison_percentage


# Write the top x people who achieved top in stat with the highest percentage. This only considers fights where each player was present, i.e., a player who was in 4 fights and achieved a top spot in 2 of them gets 50%, as does a player who was only in 2 fights and achieved a top spot in 1 of them.
# Input:
# players = list of Players
# top_players = list of Player indices considered top percentage players
# config = the configuration being used to determine topx consistent players
# num_used_fights = the number of fights that are being used in stat computation
# stat = which stat are we considering
# output_file = file to write to
# late_or_swapping = which type of stat. can be StatType.PERCENTAGE, StatType.LATE_PERCENTAGE or StatType.SWAPPED_PERCENTAGE
# top_consistent_players = list with indices of top consistent players
# top_total_players = list with indices of top total players
# top_percentage_players = list with indices of players with top percentage award
# top_late_players = list with indices of players who got a late but great award
# Output:
# list of players that got a top percentage award (or late but great or jack of all trades)
def write_sorted_top_percentage(players, top_players, comparison_percentage, config, num_used_fights, stat, output_file, late_or_swapping, top_consistent_players, top_total_players = list(), top_percentage_players = list(), top_late_players = list()):
    # get names that get on the list and their professions
    if len(top_players) <= 0:
        return top_players

    profession_strings, profession_length = get_professions_and_length(players, top_players, config)
    max_name_length = max([len(players[i].name) for i in top_players])
    profession_length = max(profession_length, 5)

    # print table header
    print_string = "Top "+config.stat_names[stat]+" percentage (Minimum percentage = "+f"{comparison_percentage*100:.0f}%)"
    myprint(output_file, print_string)
    print_string = "------------------------------------------------------------------------"     
    myprint(output_file, print_string)                

    # print table header
    print_string = f"    {'Name':<{max_name_length}}" + f"  {'Class':<{profession_length}} "+f"  Percentage "+f" {'Times Top':>9} " + f" {'Out of':>6}"
    if stat != "dist":
        print_string += f" {'Total':>8}"
    myprint(output_file, print_string)    

    # print stats for top players
    place = 0
    last_val = 0
    # print table
    for i in range(len(top_players)):
        player = players[top_players[i]]
        if player.portion_top_stats[stat] != last_val:
            place += 1

        percentage = int(player.portion_top_stats[stat]*100)
        print_string = f"{place:>2}"+f". {player.name:<{max_name_length}} "+f" {profession_strings[i]:<{profession_length}} " +f" {percentage:>10}% " +f" {round(player.consistency_stats[stat]):>9} "+f" {player.num_fights_present:>6} "

        if stat != "dist":
            print_string += f" {round(player.total_stats[stat]):>7}"
        myprint(output_file, print_string)
        last_val = player.portion_top_stats[stat]
    myprint(output_file, "\n")



# get value of stat from player_xml
def get_stat_from_player_xml(player_xml, players_running_healing_addon, stat, config):
    if stat == 'dmg_taken':
        return int(player_xml.find('defenses').find('damageTaken').text)

    if stat == 'deaths':
        return int(player_xml.find('defenses').find('deadCount').text)

    if stat == 'kills':
        return int(player_xml.find('statsAll').find('killed').text)

    if stat == 'dmg':
        return int(player_xml.find('dpsAll').find('damage').text)            

    if stat == 'rips':
        return int(player_xml.find('support').find('boonStrips').text)
    
    if stat == 'cleanses':
        return int(player_xml.find('support').find('condiCleanse').text)            

    if stat == 'dist':
        return float(player_xml.find('statsAll').find('distToCom').text)

    ### Buffs ###
    if stat in config.buff_ids:
        # get buffs in squad generation -> need to loop over all buffs
        for buff in player_xml.iter('squadBuffs'):
            # find right buff
            buffId = buff.find('id').text
            if buffId == config.buff_ids[stat]:
                return float(buff.find('buffData').find('generation').text) 
        return 0.

    if stat == 'heal':
        # check if healing was logged, save it
        heal = -1
        if player_xml.find('name').text not in players_running_healing_addon:
            return heal
        ext_healing_xml = player_xml.find('extHealingStats')
        if(ext_healing_xml != None):
            heal = 0
            for outgoing_healing_xml in ext_healing_xml.iter('outgoingHealingAllies'):
                outgoing_healing_xml2 = outgoing_healing_xml.find('outgoingHealingAllies')
                # TODO why is this in the xml twice?
                if not outgoing_healing_xml2 is None:
                    heal += int(outgoing_healing_xml2.find('healing').text)
        return heal

    if stat == 'barrier':
        # check if barrier was logged, save it
        barrier = -1
        if player_xml.find('name').text not in players_running_healing_addon:
            return barrier        
        ext_barrier_xml = player_xml.find('extBarrierStats')
        if(ext_barrier_xml != None):
            barrier = 0
            for outgoing_barrier_xml in ext_barrier_xml.iter('outgoingBarrierAllies'):
                outgoing_barrier_xml2 = outgoing_barrier_xml.find('outgoingBarrierAllies')
                # TODO why is this in the xml twice?                
                if not outgoing_barrier_xml2 is None:
                    barrier += int(outgoing_barrier_xml2.find('barrier').text)
        return barrier



# get stats for this fight from fight_xml
# Input:
# fight_xml = xml object including one fight
# config = the config to use
# log = log file to write to
def get_stats_from_fight_xml(fight_xml, config, log):
    # get fight duration
    fight_duration_xml = fight_xml.find('duration')
    split_duration = fight_duration_xml.text.split('m ', 1)
    mins = int(split_duration[0])
    split_duration = split_duration[1].split('s', 1)
    secs = int(split_duration[0])
    if debug:
        print("duration: ", mins, "m", secs, "s")
    duration = mins*60 + secs

    num_allies = len(fight_xml.findall('players'))
    num_enemies = 0
    for enemy in fight_xml.iter('targets'):
        is_enemy_player_xml = enemy.find('enemyPlayer')
        if is_enemy_player_xml != None and is_enemy_player_xml.text == "true":
            num_enemies += 1
                
    # initialize fight         
    fight = Fight()
    fight.duration = duration
    fight.enemies = num_enemies
    fight.allies = num_allies
    fight.start_time = fight_xml.find('timeStartStd').text
    fight.end_time = fight_xml.find('timeEndStd').text        
    fight.total_stats = {key: 0 for key in config.stats_to_compute}
        
    # skip fights that last less than min_fight_duration seconds
    if(duration < config.min_fight_duration):
        fight.skipped = True
        print_string = "\nFight only took "+str(mins)+"m "+str(secs)+"s. Skipping fight."
        myprint(log, print_string)
        
    # skip fights with less than min_allied_players allies
    if num_allies < config.min_allied_players:
        fight.skipped = True
        print_string = "\nOnly "+str(num_allies)+" allied players involved. Skipping fight."
        myprint(log, print_string)

    # skip fights with less than min_enemy_players enemies
    if num_enemies < config.min_enemy_players:
        fight.skipped = True
        print_string = "\nOnly "+str(num_enemies)+" enemies involved. Skipping fight."
        myprint(log, print_string)

    for extension in fight_xml.iter('usedExtensions'):
        if extension.find('name').text == "Healing Stats":
            players_running_healing_addon = [player.text for player in extension.iter('runningExtension')]

    return fight, players_running_healing_addon


# get account, character name and profession from xml object
def get_basic_player_data_from_xml(player_xml):
    account = player_xml.find('account').text
    name = player_xml.find('name').text
    profession = player_xml.find('profession').text
    return account, name, profession



# get account, character name and profession from json object
def get_basic_player_data_from_json(player_json):
    account = player_json['account']
    name = player_json['name']
    profession = player_json['profession']
    return account, name, profession


def get_buff_ids_from_json(json_data, config):
    buffs = json_data['buffMap']
    for buff_id, buff in buffs.items():
        if buff['name'] in config.buff_abbrev:
            abbrev_name = config.buff_abbrev[buff['name']]
            config.buff_ids[abbrev_name] = buff_id[1:]
            if buff['stacking']:
                config.buffs_stacking_intensity.append(abbrev_name)
            else:
                config.buffs_stacking_duration.append(abbrev_name)

            

def get_buff_ids_from_xml(xml_data, config):
    buffs = xml_data.find('buffMap')
    for buff in buffs:
        buff_xml = buffs.find(buff.tag)
        buffname = buff_xml.find('name').text
        if buffname in config.buff_abbrev:
            abbrev_name = config.buff_abbrev[buffname]
            config.buff_ids[abbrev_name] = buff.tag[1:]

            if buff_xml.find('stacking').text == "true":
                config.buffs_stacking_intensity.append(abbrev_name)
            else:
                config.buffs_stacking_duration.append(abbrev_name)
            
    
# Collect the top stats data.
# Input:
# args = cmd line arguments
# config = configuration to use for top stats computation
# log = log file to write to
# Output:
# list of Players with their stats
# list of all fights (also the skipped ones)
# was healing found in the logs?
def collect_stat_data(args, config, log, anonymize=False):
    if args.filetype != "json" and args.filetype != "xml":
        print("unsupported filetype "+args.filetype+". Please choose json or xml.")

    # healing only in xml if addon was installed
    found_healing = False # Todo what if some logs have healing and some don't
    found_barrier = False    

    players = []        # list of all player/profession combinations
    player_index = {}   # dictionary that matches each player/profession combo to its index in players list
    account_index = {}  # dictionary that matches each account name to a list of its indices in players list

    used_fights = 0
    fights = []
    first = True
    
    # iterating over all fights in directory
    files = listdir(args.input_directory)
    sorted_files = sorted(files)
    for filename in sorted_files:
        # skip files of incorrect filetype
        file_start, file_extension = os.path.splitext(filename)
        if args.filetype not in file_extension or "top_stats" in file_start:
            continue

        print_string = "parsing "+filename
        print(print_string)
        file_path = "".join((args.input_directory,"/",filename))

        # load file
        if args.filetype == "xml":
            # create xml tree
            xml_tree = ET.parse(file_path)
            xml_root = xml_tree.getroot()
            # get fight stats
            fight, players_running_healing_addon = get_stats_from_fight_xml(xml_root, config, log)
        else: # filetype == "json"
            json_datafile = open(file_path, encoding='utf-8')
            json_data = json.load(json_datafile)
            # get fight stats
            fight, players_running_healing_addon = get_stats_from_fight_json(json_data, config, log)
            
        if first:
            first = False
            if args.filetype == "json":
                get_buff_ids_from_json(json_data, config)
            else:
                get_buff_ids_from_xml(xml_root, config)
                    
        # add new entry for this fight in all players
        for player in players:
            player.stats_per_fight.append({key: value for key, value in config.empty_stats.items()})   

        # don't compute anything for skipped fights
        if fight.skipped:
            fights.append(fight)
            log.write("skipped "+filename)            
            continue
        
        used_fights += 1
        fight_number = used_fights-1

        # get stats for each player
        for player_data in (xml_root.iter('players') if args.filetype == "xml" else json_data['players']):
            create_new_player = False
            build_swapped = False

            if args.filetype == "xml":
                account, name, profession = get_basic_player_data_from_xml(player_data)
            else:
                account, name, profession = get_basic_player_data_from_json(player_data)                

            # if this combination of charname + profession is not in the player index yet, create a new entry
            name_and_prof = name+" "+profession
            if name_and_prof not in player_index.keys():
                print("creating new player",name_and_prof)
                create_new_player = True

            # if this account is not in the account index yet, create a new entry
            if account not in account_index.keys():
                account_index[account] = [len(players)]
            elif name_and_prof not in player_index.keys():
                # if account does already exist, but name/prof combo does not, this player swapped build or character
                # -> note for all Player instances of this account
                for ind in range(len(account_index[account])):
                    players[account_index[account][ind]].swapped_build = True
                account_index[account].append(len(players))
                build_swapped = True

            if create_new_player:
                player = Player(account, name, profession)
                player.initialize(config)
                player_index[name_and_prof] = len(players)
                # fill up fights where the player wasn't there yet with empty stats
                while len(player.stats_per_fight) < used_fights:
                    player.stats_per_fight.append({key: value for key, value in config.empty_stats.items()})                
                players.append(player)

            player = players[player_index[name_and_prof]]

            # get all stats that are supposed to be computed from the player data
            for stat in config.stats_to_compute:
                if args.filetype == "xml":
                    player.stats_per_fight[fight_number][stat] = get_stat_from_player_xml(player_data, players_running_healing_addon, stat, config)
                else:
                    player.stats_per_fight[fight_number][stat] = get_stat_from_player_json(player_data, players_running_healing_addon, stat, config)
                    
                if stat == 'heal' and player.stats_per_fight[fight_number][stat] >= 0:
                    found_healing = True
                if stat == 'barrier' and player.stats_per_fight[fight_number][stat] >= 0:
                    found_barrier = True                    
                if stat == 'dist':
                    player.stats_per_fight[fight_number][stat] = round(player.stats_per_fight[fight_number][stat])
                    
                # add stats of this fight and player to total stats of this fight and player
                if player.stats_per_fight[fight_number][stat] > 0:
                    # buff are generation squad values, using total over time
                    if stat in config.buffs_stacking_duration:
                        #value is generated boon time on all squad players / fight duration / (players-1)" in percent, we want generated boon time on all squad players / (players-1)
                        fight.total_stats[stat] += round(player.stats_per_fight[fight_number][stat]/100.*fight.duration, 2)
                        player.total_stats[stat] += round(player.stats_per_fight[fight_number][stat]/100.*fight.duration, 2)
                    elif stat in config.buffs_stacking_intensity:
                        #value is generated boon time on all squad players / fight duration / (players-1)", we want generated boon time on all squad players / (players-1)
                        fight.total_stats[stat] += round(player.stats_per_fight[fight_number][stat]*fight.duration, 2)
                        player.total_stats[stat] += round(player.stats_per_fight[fight_number][stat]*fight.duration, 2)                        
                    else:
                        # all non-buff stats
                        fight.total_stats[stat] += player.stats_per_fight[fight_number][stat]
                        player.total_stats[stat] += player.stats_per_fight[fight_number][stat]
                    
            if debug:
                print(name)
                for stat in player.stats_per_fight[fight_number].keys():
                    print(stat+": "+player.stats_per_fight[fight_number][stat])
                print("\n")

            player.num_fights_present += 1
            player.duration_fights_present += fight.duration
            player.swapped_build |= build_swapped

        # create lists sorted according to stats
        sortedStats = {key: list() for key in config.stats_to_compute}
        for stat in config.stats_to_compute:
            sortedStats[stat] = sort_players_by_value_in_fight(players, stat, fight_number)

        if debug:
            for stat in config.stats_to_compute:
                print("sorted "+stat+": "+sortedStats[stat])
        
        # increase number of times top x was achieved for top x players in each stat
        for stat in config.stats_to_compute:
            increase_top_x_reached(players, sortedStats[stat], config, stat)
            # round total_stats for this fight
            fight.total_stats[stat] = round(fight.total_stats[stat])

        fights.append(fight)

    if used_fights == 0:
        print("ERROR: no valid fights with filetype "+args.filetype+" found in "+args.input_directory)
        exit(1)

    # compute percentage top stats and attendance percentage for each player    
    for player in players:
        player.attendance_percentage = round(player.num_fights_present / used_fights*100)
        # round total and portion top stats
        for stat in config.stats_to_compute:
            player.portion_top_stats[stat] = round(player.consistency_stats[stat]/player.num_fights_present, 4)
            player.total_stats[stat] = round(player.total_stats[stat], 2)
            if stat == 'dmg' or stat == 'heal' or stat == 'dmg_taken' or stat == 'barrier':
                player.average_stats[stat] = round(player.total_stats[stat]/player.duration_fights_present)
            elif stat == 'deaths' or stat == 'kills':
                player.average_stats[stat] = round(player.total_stats[stat]/(player.duration_fights_present/60), 2)
            elif stat in config.buffs_stacking_duration:
                player.average_stats[stat] = round(player.total_stats[stat]/player.duration_fights_present*100, 2)
            else:
                player.average_stats[stat] = round(player.total_stats[stat]/player.duration_fights_present, 2)

                
    myprint(log, "\n")

    if anonymize:
        anonymize_players(players, account_index)
    
    return players, fights, found_healing, found_barrier
            


# replace all acount names with "account <number>" and all player names with "anon <number>"
def anonymize_players(players, account_index):
    for account in account_index:
        for i in account_index[account]:
            players[i].account = "Account "+str(i)
    for i,player in enumerate(players):
        player.name = "Anon "+str(i)


        
# get value of stat from player_json
def get_stat_from_player_json(player_json, players_running_healing_addon, stat, config):
    if stat == 'dmg_taken':
        if 'defenses' not in player_json or len(player_json['defenses']) != 1 or 'damageTaken' not in player_json['defenses'][0]:
            return 0
        return int(player_json['defenses'][0]['damageTaken'])

    if stat == 'deaths':
        if 'defenses' not in player_json or len(player_json['defenses']) != 1 or 'deadCount' not in player_json['defenses'][0]:
            return 0        
        return int(player_json['defenses'][0]['deadCount'])

    if stat == 'kills':
        if 'statsAll' not in player_json or len(player_json['statsAll']) != 1 or 'killed' not in player_json['statsAll'][0]:
            return 0        
        return int(player_json['statsAll'][0]['killed'])

    if stat == 'dmg':
        if 'dpsAll' not in player_json or len(player_json['dpsAll']) != 1 or 'damage' not in player_json['dpsAll'][0]:
            return 0
        return int(player_json['dpsAll'][0]['damage'])            

    if stat == 'rips':
        if 'support' not in player_json or len(player_json['support']) != 1 or 'boonStrips' not in player_json['support'][0]:
            return 0
        return int(player_json['support'][0]['boonStrips'])
    
    if stat == 'cleanses':
        if 'support' not in player_json or len(player_json['support']) != 1 or 'condiCleanse' not in player_json['support'][0]:
            return 0
        return int(player_json['support'][0]['condiCleanse'])            

    if stat == 'dist':
        if 'statsAll' not in player_json or len(player_json['statsAll']) != 1 or 'distToCom' not in player_json['statsAll'][0]:
            return -1
        return float(player_json['statsAll'][0]['distToCom'])

    ### Buffs ###
    if stat in config.buff_ids:
        if 'squadBuffs' not in player_json:
            return 0
        # get buffs in squad generation -> need to loop over all buffs
        for buff in player_json['squadBuffs']:
            if 'id' not in buff:
                continue 
            # find right buff
            buffId = buff['id']
            if buffId == int(config.buff_ids[stat]):
                if 'generation' not in buff['buffData'][0]:
                    return 0.
                return float(buff['buffData'][0]['generation'])
        return 0.

    if stat == 'heal':
        # check if healing was logged, save it
        heal = -1
        if player_json['name'] not in players_running_healing_addon:
            return heal
        if 'extHealingStats' in player_json:
            heal = 0
            if 'outgoingHealingAllies' not in player_json['extHealingStats']:
                return 0
            for outgoing_healing_json in player_json['extHealingStats']['outgoingHealingAllies']:
                # TODO why is this in the json twice?                
                for outgoing_healing_json2 in outgoing_healing_json:
                    if 'healing' in outgoing_healing_json2:
                        heal += int(outgoing_healing_json2['healing'])
                        break
        return heal

    if stat == 'barrier':
        # check if barrier was logged, save it
        barrier = -1
        if player_json['name'] not in players_running_healing_addon:
            return barrier
        if 'extBarrierStats' in player_json:
            barrier = 0
            if 'outgoingBarrierAllies' not in player_json['extBarrierStats']:
                return 0
            for outgoing_barrier_json in player_json['extBarrierStats']['outgoingBarrierAllies']:
                # TODO why is this in the json twice?                
                for outgoing_barrier_json2 in outgoing_barrier_json:
                    barrier += outgoing_barrier_json2['barrier']
                    break
        return barrier



# get stats for this fight from fight_json
# Input:
# fight_json = json object including one fight
# config = the config to use
# log = log file to write to
def get_stats_from_fight_json(fight_json, config, log):
    # get fight duration
    fight_duration_json = fight_json['duration']
    split_duration = fight_duration_json.split('m ', 1)
    mins = int(split_duration[0])
    split_duration = split_duration[1].split('s', 1)
    secs = int(split_duration[0])
    if debug:
        print("duration: ", mins, "m", secs, "s")
    duration = mins*60 + secs

    num_allies = len(fight_json['players'])
    num_enemies = 0
    for enemy in fight_json['targets']:
        if 'enemyPlayer' in enemy and enemy['enemyPlayer'] == True:
            num_enemies += 1
                
    # initialize fight         
    fight = Fight()
    fight.duration = duration
    fight.enemies = num_enemies
    fight.allies = num_allies
    fight.start_time = fight_json['timeStartStd']
    fight.end_time = fight_json['timeEndStd']        
    fight.total_stats = {key: 0 for key in config.stats_to_compute}
        
    # skip fights that last less than min_fight_duration seconds
    if(duration < config.min_fight_duration):
        fight.skipped = True
        print_string = "\nFight only took "+str(mins)+"m "+str(secs)+"s. Skipping fight."
        myprint(log, print_string)
        
    # skip fights with less than min_allied_players allies
    if num_allies < config.min_allied_players:
        fight.skipped = True
        print_string = "\nOnly "+str(num_allies)+" allied players involved. Skipping fight."
        myprint(log, print_string)

    # skip fights with less than min_enemy_players enemies
    if num_enemies < config.min_enemy_players:
        fight.skipped = True
        print_string = "\nOnly "+str(num_enemies)+" enemies involved. Skipping fight."
        myprint(log, print_string)

    extensions = fight_json['usedExtensions']
    for extension in extensions:
        if extension['name'] == "Healing Stats":
            players_running_healing_addon = extension['runningExtension']
        
    return fight, players_running_healing_addon



# add up total stats over all fights
def get_overall_squad_stats(fights, config):
    # overall stats over whole squad
    overall_squad_stats = {key: 0 for key in config.stats_to_compute}
    for fight in fights:
        if not fight.skipped:
            for stat in config.stats_to_compute:
                overall_squad_stats[stat] += fight.total_stats[stat]
    return overall_squad_stats



# print the overall squad stats
def print_total_squad_stats(fights, overall_squad_stats, found_healing, output): #, used_fights, used_fights_duration
    used_fights = [f for f in fights if not f.skipped]
    used_fights_duration = sum([f.duration for f in used_fights])
    
    #get total duration in h, m, s
    total_fight_duration = {}
    total_fight_duration["h"] = int(used_fights_duration/3600)
    total_fight_duration["m"] = int((used_fights_duration - total_fight_duration["h"]*3600) / 60)
    total_fight_duration["s"] = int(used_fights_duration - total_fight_duration["h"]*3600 -  total_fight_duration["m"]*60)

    total_stab_duration = {}
    total_stab_duration["h"] = int(overall_squad_stats['stab']/3600)
    total_stab_duration["m"] = int((overall_squad_stats['stab'] - total_stab_duration["h"]*3600)/60)
    total_stab_duration["s"] = int(overall_squad_stats['stab'] - total_stab_duration["h"]*3600 - total_stab_duration["m"]*60)    

    
    min_players = min([f.allies for f in used_fights])
    max_players = max([f.allies for f in used_fights])    
    mean_players = sum([f.allies for f in used_fights])/len(used_fights)
    min_enemies = min([f.enemies for f in used_fights])
    max_enemies = max([f.enemies for f in used_fights])        
    mean_enemies = sum([f.enemies for f in used_fights])/len(used_fights)
    
    print_string = "The following stats are computed over "+str(len(used_fights))+" out of "+str(len(fights))+" fights.\n"
    myprint(output, print_string)

    # print total squad stats
    print_string = "Squad overall did "+str(round(overall_squad_stats['dmg']))+" damage, ripped "+str(round(overall_squad_stats['rips']))+" boons, cleansed "+str(round(overall_squad_stats['cleanses']))+" conditions, \ngenerated "
    if total_stab_duration["h"] > 0:
        print_string += str(total_stab_duration["h"])+"h "
    print_string += str(total_stab_duration["m"])+"m "+str(total_stab_duration["s"])+"s of stability"        
    if found_healing:
        print_string += ", healed for "+str(round(overall_squad_stats['heal']))
    print_string += ", \nkilled "+str(round(overall_squad_stats['kills']))+" enemies and had "+str(round(overall_squad_stats['deaths']))+" deaths \nover a total time of "
    if total_fight_duration["h"] > 0:
        print_string += str(total_fight_duration["h"])+"h "
    print_string += str(total_fight_duration["m"])+"m "+str(total_fight_duration["s"])+"s in "+str(len(used_fights))+" fights.\n"
    print_string += "There were between "+str(min_players)+" and "+str(max_players)+" allied players involved (average "+str(round(mean_players, 1))+" players).\n"
    print_string += "The squad faced between "+str(min_enemies)+" and "+str(max_enemies)+" enemy players (average "+str(round(mean_enemies, 1))+" players).\n"    
        
    myprint(output, print_string)
    return total_fight_duration


# Write xls fight overview
# Input:
# fights = list of Fights
# overall_squad_stats = overall stats of the whole squad
# xls_output_filename = where to write to
def write_fights_overview_xls(fights, overall_squad_stats, xls_output_filename):
    book = xlrd.open_workbook(xls_output_filename)
    wb = copy(book)
    if len(book.sheet_names()) == 0 or book.sheet_names()[0] != 'fights overview':
        print("Sheet 'fights overview' is not the first sheet in"+xls_output_filename+". Skippping fights overview.")
        return
    sheet1 = wb.get_sheet(0)

    sheet1.write(0, 1, "#")
    sheet1.write(0, 2, "Date")
    sheet1.write(0, 3, "Start Time")
    sheet1.write(0, 4, "End Time")
    sheet1.write(0, 5, "Duration in s")
    sheet1.write(0, 6, "Skipped")
    sheet1.write(0, 7, "Num. Allies")
    sheet1.write(0, 8, "Num. Enemies")
    sheet1.write(0, 9, "Damage")
    sheet1.write(0, 10, "Boonrips")
    sheet1.write(0, 11, "Cleanses")
    sheet1.write(0, 12, "Stability Output")
    sheet1.write(0, 13, "Healing")
    sheet1.write(0, 14, "Deaths")
    sheet1.write(0, 15, "Kills")        

    for i in range(len(fights)):
        fight = fights[i]
        skipped_str = "yes" if fight.skipped else "no"
        sheet1.write(i+1, 1, i+1)
        sheet1.write(i+1, 2, fight.start_time.split()[0])
        sheet1.write(i+1, 3, fight.start_time.split()[1])
        sheet1.write(i+1, 4, fight.end_time.split()[1])
        sheet1.write(i+1, 5, fight.duration)
        sheet1.write(i+1, 6, skipped_str)
        sheet1.write(i+1, 7, fight.allies)
        sheet1.write(i+1, 8, fight.enemies)
        sheet1.write(i+1, 9, fight.total_stats['dmg'])
        sheet1.write(i+1, 10, fight.total_stats['rips'])
        sheet1.write(i+1, 11, fight.total_stats['cleanses'])
        sheet1.write(i+1, 12, round(fight.total_stats['stab']))
        sheet1.write(i+1, 13, fight.total_stats['heal'])
        sheet1.write(i+1, 14, fight.total_stats['deaths'])
        sheet1.write(i+1, 15, fight.total_stats['kills'])                


    used_fights = [f for f in fights if not f.skipped]
    used_fights_duration = sum([f.duration for f in used_fights])
    num_used_fights = len(used_fights)
    mean_allies = round(sum([f.allies for f in used_fights])/num_used_fights, 1)
    mean_enemies = round(sum([f.enemies for f in used_fights])/num_used_fights, 1)
    sheet1.write(len(fights)+1, 0, "Sum/Avg. in used fights")
    sheet1.write(len(fights)+1, 1, num_used_fights)    
    sheet1.write(len(fights)+1, 5, used_fights_duration)
    sheet1.write(len(fights)+1, 7, mean_allies)
    sheet1.write(len(fights)+1, 8, mean_enemies)
    sheet1.write(len(fights)+1, 9, overall_squad_stats['dmg'])
    sheet1.write(len(fights)+1, 10, overall_squad_stats['rips'])
    sheet1.write(len(fights)+1, 11, overall_squad_stats['cleanses'])
    sheet1.write(len(fights)+1, 12, round(overall_squad_stats['stab']))
    sheet1.write(len(fights)+1, 13, overall_squad_stats['heal'])
    sheet1.write(len(fights)+1, 14, overall_squad_stats['deaths'])
    sheet1.write(len(fights)+1, 15, overall_squad_stats['kills'])                

    wb.save(xls_output_filename)


def print_fights_overview(fights, overall_squad_stats, output):
    print_string = "  #  "+f"{'Date':<10}"+"  "+f"{'Start Time':>10}"+"  "+f"{'End Time':>8}"+"  Duration in s  Skipped  Num. Allies  Num. Enemies  "    
    print_string += f"{'Damage':>9}"
    print_string += "  Strips  Cleanses  Stability Output  "
    print_string += f"{'Healing':>9}"
    #+"  "+f"{'Distance':>10}"
    print_string += "  Deaths  Kills"
    myprint(output, print_string)
    for i in range(len(fights)):
        fight = fights[i]
        skipped_str = "yes" if fight.skipped else "no"
        date = fight.start_time.split()[0]
        start_time = fight.start_time.split()[1]
        end_time = fight.end_time.split()[1]        
        print_string = f"{i+1:>3}"+"  "+f"{date:<10}"+"  "+f"{start_time:>10}"+"  "+f"{end_time:>8}"+"  "+f"{fight.duration:>13}"+"  "+f"{skipped_str:>7}"+"  "+f"{fight.allies:>11}"+"  "+f"{fight.enemies:>12}"+"  "
        print_string += f"{round(fight.total_stats['dmg']):>9}" +"  "+f"{round(fight.total_stats['rips']):>6}" +"  "+f"{round(fight.total_stats['cleanses']):>8}"  +"  "+f"{round(fight.total_stats['stab']):>16}"+"  "+f"{round(fight.total_stats['heal']):>9}" #+"  "+f"{round(fight.total_stats['dist']):>10}"
        print_string += "  "+f"{round(fight.total_stats['deaths']):>6}" +"  "+f"{round(fight.total_stats['kills']):>5}"
        myprint(output, print_string)

    used_fights = [f for f in fights if not f.skipped]
    used_fights_duration = sum([f.duration for f in used_fights])

    print_string = "-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------"
    myprint(output, print_string)
    print_string = f"{'Sum':>3}"+"  "+f"{' ':<10}"+"  "+f"{' ':>10}"+"  "+f"{' ':>8}"+"  "+f"{used_fights_duration:>13}"+"  "+f"{' ':>7}"+"  "+f"{' ':>11}"+"  "+f"{' ':>12}"+"  "
    print_string += f"{round(overall_squad_stats['dmg']):>9}" +"  "+f"{round(overall_squad_stats['rips']):>6}" +"  "+f"{round(overall_squad_stats['cleanses']):>8}"  +"  "+f"{round(overall_squad_stats['stab']):>16}"+"  "+f"{round(overall_squad_stats['heal']):>9}" +"  "#+f"{round(overall_squad_stats['dist']):>10}" +"  "
    print_string += f"{round(overall_squad_stats['deaths']):>6}" +"  "+f"{round(overall_squad_stats['kills']):>5}\n"
    myprint(output, print_string)


    
def write_to_json(overall_squad_stats, fights, players, top_total_stat_players, top_consistent_stat_players, top_percentage_stat_players, top_late_players, top_jack_of_all_trades_players, output_file):
    json_dict = {}
    json_dict["overall_squad_stats"] = {key: value for key, value in overall_squad_stats.items()}
    json_dict["fights"] = [jsons.dump(fight) for fight in fights]
    json_dict["players"] = [jsons.dump(player) for player in players]
    json_dict["top_total_players"] =  {key: value for key, value in top_total_stat_players.items()}
    json_dict["top_consistent_players"] =  {key: value for key, value in top_consistent_stat_players.items()}
    json_dict["top_percentage_players"] =  {key: value for key, value in top_percentage_stat_players.items()}
    json_dict["top_late_players"] =  {key: value for key, value in top_late_players.items()}
    json_dict["top_jack_of_all_trades_players"] =  {key: value for key, value in top_jack_of_all_trades_players.items()}        
    with open(output_file, 'w') as json_file:
        json.dump(json_dict, json_file, indent=4)

