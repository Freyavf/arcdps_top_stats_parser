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
#import xlwt
import xlrd
from xlutils.copy import copy

debug = False # enable / disable debug output

class StatType(Enum):
    TOTAL = 1
    CONSISTENT = 2
    LATE_PERCENTAGE = 3
    SWAPPED_PERCENTAGE = 4

    

# This class stores information about a player. Note that a different profession will be treated as a new player / character.
@dataclass
class Player:
    account: str = ""                   # account name
    name: str = ""                      # character name
    profession: str = ""                # profession name
    num_fights_present: int = 0         # the number of fight the player was involved in 
    attendance_percentage: float = 0.   # the percentage of fights the player was involved in out of all fights
    duration_fights_present: int = 0    # the total duration of all fights the player was involved in
    swapped_build: bool = False         # a different player character or specialization with this account name was in some of the fights

    # fields for all stats: dmg, rips, stab, cleanses, heal, dist, deaths, kills
    consistency_stats: dict = field(default_factory=dict)     # how many times did this player get into top for each stat?
    total_stats: dict = field(default_factory=dict)           # what's the total value for this player for each stat?
    percentage_top_stats: dict = field(default_factory=dict)  # what percentage of fights did this player get into top for each stat, in relation to the number of fights they were involved in?


    
# This class stores the configuration for running the top stats.
@dataclass
class Config:
    # fields for all stats: dmg, rips, stab, cleanses, heal, dist, deaths, kills
    num_players_listed: dict = field(default_factory=dict)          # How many players will be listed who achieved top stats most often for each stat?
    num_players_considered_top: dict = field(default_factory=dict)  # How many players are considered to be "top" in each fight for each stat?
    
    min_attendance_portion_for_late: float = 0.        # For what portion of all fights does a player need to be there to be considered for "late but great" awards? 
    min_attendance_portion_for_buildswap: float = 0.   # For what portion of all fights does a player need to be there to be considered for "jack of all trades" awards? 

    portion_of_top_for_total: float = 0.         # What portion of the top total player stat does someone need to reach to be considered for total awards?
    portion_of_top_for_consistent: float = 0.    # What portion of the total stat of the top consistent player does someone need to reach to be considered for consistency awards?
    portion_of_top_for_late: float = 0.          # What portion of the percentage the top consistent player reached top does someone need to reach to be considered for late but great awards?
    portion_of_top_for_buildswap: float = 0.     # What portion of the percentage the top consistent player reached top does someone need to reach to be considered for jack of all trades awards?

    min_allied_players: int = 0   # minimum number of allied players to consider a fight in the stats
    min_fight_duration: int = 0   # minimum duration of a fight to be considered in the stats
    min_enemy_players: int = 0    # minimum number of enemies to consider a fight in the stats

    stat_names: dict = field(default_factory=dict)
    profession_abbreviations: dict = field(default_factory=dict)
    
    output_file: str = ""
    input_dir: str = ""


    
# prints output_string to the console and the output_file, with a linebreak at the end
def myprint(output_file, output_string):
    print(output_string)
    output_file.write(output_string+"\n")

    
    
# For all players considered to be top in stat in this fight, increase
# the number of fights they reached top by 1 (i.e. increase
# consistency_stats[stat]).
# Input:
# players = list of all players
# sortedList = list of player names+profession, sorted by stat value in this fight. for dist: list of (names+profession, dist_value)
# player_index = dict mapping player + profession to corresponding index in the players list
# config = configuration to use
# stat = stat that is considered
def increase_top_x_reached(players, sortedList, player_index, config, stat):
    # if stat isn't dist, increase top stats reached for the first num_players_considered_top players
    if stat != 'dist':
        i = 0
        last_val = 0
        while i < len(sortedList) and (i < config.num_players_considered_top[stat] or sortedList[i][1] == last_val):
            players[player_index[sortedList[i][0]]].consistency_stats[stat] += 1
            last_val = sortedList[i][1]
            i += 1
        return

    # different for dist
    valid_distances = 0
    first_valid = True
    i = 0
    last_val = 0
    while i < len(sortedList) and (valid_distances < config.num_players_considered_top[stat]+1 or sortedList[i][1] == last_val):
        # sometimes dist is -1, filter these out
        if sortedList[i][1] >= 0:
            # first valid dist is the comm, don't consider
            if first_valid:
                first_valid  = False
            else:
                players[player_index[sortedList[i][0]]].consistency_stats[stat] += 1
                valid_distances += 1
        last_val = sortedList[i][1]
        i += 1


        
# Input:
# players = list of Players
# sorting = list of indices in players list, sorted by stat value (total or consistency)
# config = the configuration being used to determine top players
# stat = which stat are we considering
# total_or_consistent = enum StatType, either StatType.TOTAL or StatType.CONSISTENT, we are getting the players with top total values or top consistency values.
# Output:
# list of player indices getting a consistency / total award, maximum character name length
def get_topx_players(players, sorting, config, stat, total_or_consistent):
    # get percentage of top to use according to config
    percentage = 0.
    if total_or_consistent == StatType.TOTAL:
        percentage = float(config.portion_of_top_for_consistent)
    elif total_or_consistent == StatType.CONSISTENT:
        percentage = float(config.portion_of_top_for_total)
    else:
        print("ERROR: Called get_topx_players for stats that are not total or consistent")
        return

    top = players[sorting[0]].total_stats[stat] # using total value for both top consistent and top total 
    top_players = list()
    name_length = 0

    # To be considered as top player:
    # 1) index must be lower than length of the list
    # 2) value must be greater than 0    
    i = 0
    last_val = 0
    
    while i < len(sorting):# and players[sorting[i]].total_stats[stat] > 0:
        if total_or_consistent == StatType.TOTAL:
            new_val = players[sorting[i]].total_stats[stat]
        else:
            new_val = players[sorting[i]].consistency_stats[stat]
        # 3) index must be lower than number of output desired OR list entry has same value as previous entry, i.e. double place
        if i >= config.num_players_listed[stat] and new_val != last_val:
            break
        last_val = new_val
        
        is_top = False
        if stat != "dist":
            # 4) value must be at least percentage% of top value for everything except distance
            if players[sorting[i]].total_stats[stat] >= top * percentage:
                is_top = True
        else: # dist stats
            is_top = True

        # append player index to top_players, get maximum name length for printing purposes
        if is_top:
            top_players.append(sorting[i])
            name = players[sorting[i]].name
            if len(name) > name_length:
                name_length = len(name)
        i += 1
        
    return top_players, name_length



# Input:
# players = list of Players
# sorting = list of indices in players list, sorted by top stat percentage
# config = the configuration being used to determine top players
# stat = which stat are we considering
# comparison_percentage = portion of top that has to be reached to be considered for an award
# late_or_swapping = enum StatType, either StatType.LATE_PERCENTAGE or StatType.SWAPPED_PERCENTAGE.
# num_total_fights = number of fights that go into stat computation
# top_consistent_players = list of indices of players that got a top consistency award
# top_total_players = list of indices of players that got a top total award
# top_late_players = list of indices of players that got a late but great award
# Output:
# list of player indices getting a late but great / jack of all trades awards, maximum character name length
def get_topx_percentage_players(players, sorting, config, stat, comparison_percentage, late_or_swapping, num_total_fights, top_consistent_players, top_total_players, top_late_players):
    i = 0
    top_percentage_players = list()
    name_length = 0
    
    # compute minimum attendance based on config
    min_attendance = 0
    if late_or_swapping == StatType.LATE_PERCENTAGE:
        min_attendance = config.min_attendance_portion_for_late * num_total_fights
    elif late_or_swapping == StatType.SWAPPED_PERCENTAGE:
        min_attendance = config.min_attendance_portion_for_buildswap * num_total_fights
    else:
        print("ERROR: Called get_topx_percentag_players for stats that are not late_percentage or swapped_percentage")
        return 

    # 1) index must be lower than length of the list
    # 2) percentage value must be at least comparison percentage value
    while i < len(sorting) and players[sorting[i]].percentage_top_stats[stat] >= comparison_percentage:
        # no double awards
        if sorting[i] in top_consistent_players or sorting[i] in top_total_players or sorting[i] in top_late_players:
            i += 1
            continue
        player = players[sorting[i]]
        # player can't be there for all fights, but has to be there for at least min_attendance fights
        if player.num_fights_present < num_total_fights and player.num_fights_present >= min_attendance:
            # Jack of all trades awards only when build / character was swapped at least once
            if late_or_swapping == StatType.SWAPPED_PERCENTAGE and player.swapped_build == False:
                i += 1
                continue                
            top_percentage_players.append(sorting[i])
            if len(player.name) > name_length:
                name_length = len(player.name)

        i += 1
    return top_percentage_players, name_length



# get the professions of all players indicated by the indices. Additionally, get the length of the longest profession name.
# Input:
# players = list of all players
# indices = list of relevant indices
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



# Write the top x people who achieved top y in stat most often.
# Input:
# players = list of Players
# config = the configuration being used to determine the top consistent players
# num_used_fights = the number of fights that are being used in stat computation
# stat = which stat are we considering
# output_file = the file to write the output to
# Output:
# list of player indices that got a top consistency award
def write_sorted_top_x(players, config, num_used_fights, stat, output_file):
    # sort players according to number of times top was achieved for stat
    decorated = [(player.consistency_stats[stat], player.total_stats[stat], i, player) for i, player in enumerate(players)]
    decorated.sort(reverse=True)
    sorted_topx = [i for consistency, total, i, player in decorated] 

    if stat == "dist":
        print_string = "Top "+str(config.num_players_considered_top[stat])+" "+config.stat_names[stat]+" consistency awards"
    else:
        print_string = "Top "+config.stat_names[stat]+" consistency awards (Max. "+str(config.num_players_considered_top[stat])+" people, min. "+str(round(config.portion_of_top_for_consistent*100.))+"% of most consistent)"
    myprint(output_file, print_string)
    print_string = "Most times placed in the top "+str(config.num_players_considered_top[stat])+". \nAttendance = number of fights a player was present out of "+str(num_used_fights)+" total fights."    
    myprint(output_file, print_string)
    print_string = "-------------------------------------------------------------------------------"    
    myprint(output_file, print_string)

    # get names that get on the list and their professions
    top_consistent_players, name_length = get_topx_players(players, sorted_topx, config, stat, StatType.CONSISTENT)
    profession_strings, profession_length = get_professions_and_length(players, top_consistent_players, config)
    profession_length = max(profession_length, 5)

    # print table header
    print_string = f"    {'Name':<{name_length}}" + f"  {'Class':<{profession_length}} "+f" Attendance " + " Times Top"
    if stat != "dist":
        print_string += f" {'Total':>9}"
    if stat == "stab":
        print_string += f"  {'Average':>7}"
        
    myprint(output_file, print_string)    

    
    place = 0
    last_val = 0
    # print table
    for i in range(len(top_consistent_players)):
        player = players[top_consistent_players[i]]
        if player.consistency_stats[stat] != last_val:
            place += 1
        print_string = f"{place:>2}"+f". {player.name:<{name_length}} "+f" {profession_strings[i]:<{profession_length}} "+f" {player.num_fights_present:>10} "+f" {round(player.consistency_stats[stat]):>9}"
        if stat != "dist" and stat != "stab":
            print_string += f" {round(player.total_stats[stat]):>9}"
        if stat == "stab":
            average = round(player.total_stats[stat]/player.duration_fights_present, 2)
            total = round(player.total_stats[stat])
            print_string += f" {total:>8}s"+f" {average:>8}"

        myprint(output_file, print_string)
        last_val = player.consistency_stats[stat]

    return top_consistent_players
        
                

# Write the top x people who achieved top total stat.
# Input:
# players = list of Players
# top_total_players = list of indeces in players that are considered as top
# stat = which stat are we considering
# xls_output_filename = where to write to
def write_total_stats_xls(players, top_total_players, stat, xls_output_filename):
    book = xlrd.open_workbook(xls_output_filename)
    wb = copy(book)
    sheet1 = wb.add_sheet(stat)

    sheet1.write(0, 0, "Name")
    sheet1.write(0, 1, "Profession")
    sheet1.write(0, 2, "Attendance (number of fights)")
    sheet1.write(0, 3, "Attendance (duration fights)")
    sheet1.write(0, 4, "Times Top")
    sheet1.write(0, 5, "Total "+stat)
    sheet1.write(0, 6, "Average "+stat+" per s")

    for i in range(len(top_total_players)):
        player = players[top_total_players[i]]
        sheet1.write(i+1, 0, player.name)
        sheet1.write(i+1, 1, player.profession)
        sheet1.write(i+1, 2, player.num_fights_present)
        sheet1.write(i+1, 3, player.duration_fights_present)
        sheet1.write(i+1, 4, player.consistency_stats[stat])
        sheet1.write(i+1, 5, player.total_stats[stat])
        sheet1.write(i+1, 6, player.total_stats[stat]/player.duration_fights_present)        

    wb.save(xls_output_filename)


# Write the top x people who achieved top total stat.
# Input:
# players = list of Players
# config = the configuration being used to determine topx consistent players
# total_fight_duration = the total duration of all fights
# stat = which stat are we considering
# output_file = where to write to
def write_sorted_total(players, config, total_fight_duration, stat, output_file, xls_output_filename):
    # sort players according to number of times top x was achieved for stat
    decorated = [(player.total_stats[stat], i, player) for i, player in enumerate(players)]
    decorated.sort(reverse=True)
    sorted_topx = [i for total, i, player in decorated] 
    #print("top stats for total",stat,":", sorted_topx)

    print_string = "\nTop overall "+config.stat_names[stat]+" awards (Max. "+str(config.num_players_listed[stat])+" people, min. "+str(round(config.portion_of_top_for_total*100.))+"% of 1st place)"
    myprint(output_file, print_string)
    print_string = "Attendance = total duration of fights attended out of "
    if total_fight_duration["h"] > 0:
        print_string += str(total_fight_duration["h"])+"h "
    print_string += str(total_fight_duration["m"])+"m "+str(total_fight_duration["s"])+"s."    
    myprint(output_file, print_string)
    print_string = "------------------------------------------------------------------------"
    myprint(output_file, print_string)

    # get players that get on the list and their professions
    top_total_players, name_length = get_topx_players(players, sorted_topx, config, stat, StatType.TOTAL)
    profession_strings, profession_length = get_professions_and_length(players, top_total_players, config)
    profession_length = max(profession_length, 5)

    # print table header
    print_string = f"    {'Name':<{name_length}}" + f"  {'Class':<{profession_length}} "+f" {'Attendance':>11}"+f" {'Total':>9}"
    if stat == "stab":
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

        print_string = f"{place:>2}"+f". {player.name:<{name_length}} "+f" {profession_strings[i]:<{profession_length}} "

        if fight_time_h > 0:
            print_string += f" {fight_time_h:>2}h {fight_time_m:>2}m {fight_time_s:>2}s"
        else:
            print_string += f" {fight_time_m:>6}m {fight_time_s:>2}s"

        if stat == "stab":
            print_string += f" {round(player.total_stats[stat]):>8}s"
            average = round(player.total_stats[stat]/player.duration_fights_present, 2)
            print_string += f" {average:>8}"
        else:
            print_string += f" {round(player.total_stats[stat]):>9}"
        myprint(output_file, print_string)
        last_val = player.total_stats[stat]

    write_total_stats_xls(players, top_total_players, stat, xls_output_filename)
        
    return top_total_players

   

# Write the top x people who achieved top in stat with the highest percentage. This only considers fights where each player was present, i.e., a player who was in 4 fights and achieved a top spot in 2 of them gets 50%, as does a player who was only in 2 fights and achieved a top spot in 1 of them.
# Input:
# players = list of Players
# config = the configuration being used to determine topx consistent players
# num_used_fights = the number of fights that are being used in stat computation
# stat = which stat are we considering
# output_file = file to write to
# top_consistent_players = list with indices of top consistent players
# top_total_players = list with indices of top total players
# top_late_players = list with indices of players who got a late but great award
# Output:
# list of players that got a top percentage award (late but great or jack of all trades)
def write_sorted_top_x_percentage(players, config, num_used_fights, stat, output_file, late_or_swapping, top_consistent_players, top_total_players = list(), top_late_players = list()):
    # TODO check this gives the first
    comparison_percentage = 0
    if late_or_swapping == StatType.LATE_PERCENTAGE:
        comparison_percentage = players[top_consistent_players[0]].percentage_top_stats[stat] * config.portion_of_top_for_late
    elif late_or_swapping == StatType.SWAPPED_PERCENTAGE:
        comparison_percentage = players[top_consistent_players[0]].percentage_top_stats[stat] * config.portion_of_top_for_buildswap
    else:
        print("ERROR: Called write_sorted_top_x_percentage with stats that are neither for late players nor for players who swapped build")
    
    # sort players according to percentage of top achieved for stat
    decorated = [(player.percentage_top_stats[stat], player.consistency_stats[stat], i, player) for i, player in enumerate(players)]
    decorated.sort(reverse=True)
    sorted_top_percentage = [i for percentage, consistency, i, player in decorated] 

    # get names that get on the list and their professions
    top_percentage_players, name_length = get_topx_percentage_players(players, sorted_top_percentage, config, stat, comparison_percentage, late_or_swapping, num_used_fights, top_consistent_players, top_total_players, top_late_players)
    profession_strings, profession_length = get_professions_and_length(players, top_percentage_players, config)
    profession_length = max(profession_length, 5)
    
    if len(top_percentage_players) <= 0:
        return top_percentage_players

    print_string = "Top "+config.stat_names[stat]+" percentage (Minimum percentage = "+f"{comparison_percentage*100:.0f}%)"
    myprint(output_file, print_string)
    print_string = "------------------------------------------------------------------------"     
    myprint(output_file, print_string)                

    # print table header
    print_string = f"    {'Name':<{name_length}}" + f"  {'Class':<{profession_length}} "+f"  Percentage "+f" {'Times Top':>9} " + f" {'Out of':>6}"
    if stat != "distance":
        print_string += f" {'Total':>8}"
    myprint(output_file, print_string)    

    place = 0
    last_val = 0
    # print table
    for i in range(len(top_percentage_players)):
        player = players[top_percentage_players[i]]
        if player.percentage_top_stats[stat] != last_val:
            place += 1

        percentage = int(player.percentage_top_stats[stat]*100)
        print_string = f"{place:>2}"+f". {player.name:<{name_length}} "+f" {profession_strings[i]:<{profession_length}} " +f" {percentage:>10}% " +f" {round(player.consistency_stats[stat]):>9} "+f" {player.num_fights_present:>6} "

        if stat != "dist":
            print_string += f" {round(player.total_stats[stat]):>7}"
        myprint(output_file, print_string)
        last_val = player.percentage_top_stats[stat]

    return top_percentage_players



# Collect the top stats data.
# Input:
# args = cmd line arguments
# config = configuration to use for top stats computation
# log = log file to write to
# Output:
# list of Players with their stats
# overall stats for the whole squads
# duration of the fights that were used in the top stats computation
# number of used fights
# number of total fights
# number of players per fight
# was healing found in the logs?
def collect_stat_data(args, config, log):
    # healing only in xml if addon was installed
    found_healing = False

    # overall stats over whole squad
    overall_squad_stats = {'dmg': 0., 'rips': 0., 'stab': 0., 'cleanses': 0., 'heal': 0., 'dist': 0., 'deaths': 0., 'kills': 0.}

    players = []        # list of all player/profession combinations
    player_index = {}   # dictionary that matches each player/profession combo to its index in players list
    account_index = {}  # dictionary that matches each account name to a list of its indices in players list
    
    num_players_per_fight = list()
    num_enemies_per_fight = list()    
    stab_id = "1122"
    used_fights = 0
    used_fights_duration = 0
    total_fights = 0
    
    # iterating over all fights in directory
    for xml_filename in listdir(args.xml_directory):
        # skip non xml files
        if not ".xml" in xml_filename:
            continue
        total_fights += 1
        
        # create xml tree
        print_string = "parsing "+xml_filename
        print(print_string)
        xml_file_path = "".join((args.xml_directory,"/",xml_filename))
        xml_tree = ET.parse(xml_file_path)
        
        xml_root = xml_tree.getroot()

        # get fight duration
        fight_duration_xml = xml_root.find('duration')
        split_duration = fight_duration_xml.text.split('m ', 1)
        mins = int(split_duration[0])
        split_duration = split_duration[1].split('s', 1)
        secs = int(split_duration[0])
        if debug:
            print("duration: ", mins, "m", secs, "s")
        duration = mins*60 + secs

        # skip fights that last less than min_fight_duration seconds
        if(duration < config.min_fight_duration):
            log.write(print_string)
            print_string = "\nFight only took "+str(mins)+"m "+str(secs)+"s. Skipping fight."
            myprint(log, print_string)
            continue
        
        # skip fights with less than min_allied_players allies
        num_allies = len(xml_root.findall('players'))
        if num_allies < config.min_allied_players:
            log.write(print_string)
            print_string = "\nOnly "+str(num_allies)+" allied players involved. Skipping fight."
            myprint(log, print_string)
            continue

        # skip fights with less than min_enemy_players enemies
        num_enemies = 0
        for enemy in xml_root.iter('targets'):
            is_enemy_player_xml = enemy.find('enemyPlayer')
            if is_enemy_player_xml != None and is_enemy_player_xml.text == "true":
                num_enemies += 1

        #len(xml_root.findall('targets')) # technically would need to check whether enemyPlayer == True
        if num_enemies < config.min_enemy_players:
            log.write(print_string)
            print_string = "\nOnly "+str(num_enemies)+" enemies involved. Skipping fight."
            myprint(log, print_string)
            continue

        used_fights += 1
        used_fights_duration += duration
        num_players_per_fight.append(num_allies)
        num_enemies_per_fight.append(num_enemies)        

        # dictionaries for stats for each player in this fight
        damage_per_player = {}
        cleanses_per_player = {}
        strips_per_player = {}
        stab_per_player = {}
        healing_per_player = {}
        distance_per_player = {}
        deaths_per_player = {}
        kills_per_player = {}

        # get stats for each player
        for xml_player in xml_root.iter('players'):
            create_new_player = False
            build_swapped = False
            
            # get player account, name, profession
            account = xml_player.find('account').text
            name = xml_player.find('name').text
            profession = xml_player.find('profession').text

            # get deaths and kills
            deaths = int(xml_player.find('defenses').find('deadCount').text)
            kills = int(xml_player.find('statsAll').find('killed').text)

            # get damage
            damage = int(xml_player.find('dpsAll').find('damage').text)

            # get strips and cleanses
            support_stats = xml_player.find('support')
            strips = int(support_stats.find('boonStrips').text)
            cleanses = int(support_stats.find('condiCleanse').text)

            # get stab in squad generation -> need to loop over all buffs
            stab_generated = 0
            for buff in xml_player.iter('squadBuffs'):
                # find stab buff
                if buff.find('id').text != stab_id:
                    continue
                stab_generated = float(buff.find('buffData').find('generation').text)#Decimal
                break

            # check if healing was logged, save it
            ext_healing_xml = xml_player.find('extHealingStats')
            healing = 0
            if(ext_healing_xml != None):
                found_healing = True
                for outgoing_healing_xml in ext_healing_xml.iter('outgoingHealingAllies'):
                    outgoing_healing_xml2 = outgoing_healing_xml.find('outgoingHealingAllies')
                    if not outgoing_healing_xml2 is None:
                        healing += int(outgoing_healing_xml2.find('healing').text)

            # get distance to tag
            distance = float(xml_player.find('statsAll').find('distToCom').text)#Decimal

            if debug:
                print(name)
                print("damage:",damage)
                print("strips:",strips)
                print("cleanses:",cleanses)
                print("stab:",stab_generated)
                print("healing:",healing)
                print(f"distance: {distance:.2f}")
                print("\n")

            # if this combination of charname + profession is not in the player index yet, create a new entry
            name_and_prof = name+" "+profession
            if name_and_prof not in player_index.keys():
                print("creating new player",name_and_prof)
                create_new_player = True

            # if this account is not in the account index yet, create a new entry
            if account not in account_index.keys():
                account_index[account] = [len(players)]
            else:
                # if account does already exist, this player swapped build or character -> note for all Player instances of this account
                for ind in range(len(account_index[account])):
                    players[account_index[account][ind]].swapped_build = True
                if create_new_player:
                    account_index[account].append(len(players))
                build_swapped = True

            if create_new_player:
                player = Player()
                player.account = account
                player.name = name
                player.profession = profession
                player.total_stats = {'dmg': 0., 'rips': 0., 'stab': 0., 'cleanses': 0., 'heal': 0., 'dist': 0., 'deaths': 0., 'kills': 0.}
                player.consistency_stats = {'dmg': 0., 'rips': 0., 'stab': 0., 'cleanses': 0., 'heal': 0., 'dist': 0., 'deaths': 0., 'kills': 0.}
                player.percentage_top_stats = {'dmg': 0., 'rips': 0., 'stab': 0., 'cleanses': 0., 'heal': 0., 'dist': 0., 'deaths': 0., 'kills': 0.}                 
                player_index[name_and_prof] = len(players)
                players.append(player)

            # fill dictionary of stats for this fight
            damage_per_player[name_and_prof] = damage
            strips_per_player[name_and_prof] = strips
            stab_per_player[name_and_prof] = stab_generated
            cleanses_per_player[name_and_prof] = cleanses
            if found_healing:
                healing_per_player[name_and_prof] = healing
            if distance >= 0: # distance sometimes -1 for some reason
                distance_per_player[name_and_prof] = distance
            else:
                distance_per_player[name_and_prof] = -1
            deaths_per_player[name_and_prof] = deaths
            kills_per_player[name_and_prof] = kills                 

            # add stats of this fight to total player stats
            players[player_index[name_and_prof]].num_fights_present += 1
            players[player_index[name_and_prof]].duration_fights_present += duration
            players[player_index[name_and_prof]].swapped_build |= build_swapped
            players[player_index[name_and_prof]].total_stats['dmg'] += damage
            players[player_index[name_and_prof]].total_stats['rips'] += strips
            players[player_index[name_and_prof]].total_stats['stab'] += stab_generated*duration
            players[player_index[name_and_prof]].total_stats['cleanses'] += cleanses
            if found_healing:
                players[player_index[name_and_prof]].total_stats['heal'] += healing
            if distance > 0: # distance sometimes -1 for some reason
                players[player_index[name_and_prof]].total_stats['dist'] += distance*duration
            players[player_index[name_and_prof]].total_stats['deaths'] += deaths
            players[player_index[name_and_prof]].total_stats['kills'] += kills

            # add stats of this player for this fight to overall squad stats
            overall_squad_stats['dmg'] += damage
            overall_squad_stats['rips'] += strips
            overall_squad_stats['stab'] += stab_generated*duration
            overall_squad_stats['cleanses'] += cleanses
            overall_squad_stats['heal'] += healing
            overall_squad_stats['dist'] += distance*duration
            overall_squad_stats['deaths'] += deaths
            overall_squad_stats['kills'] += kills

            
        # create lists sorted according to stats
        sortedDamage = sorted(damage_per_player.items(), key=lambda x:x[1], reverse=True)
        sortedStrips = sorted(strips_per_player.items(), key=lambda x:x[1], reverse=True)
        sortedCleanses = sorted(cleanses_per_player.items(), key=lambda x:x[1], reverse=True)
        sortedStab = sorted(stab_per_player.items(), key=lambda x:x[1], reverse=True)
        sortedHealing = sorted(healing_per_player.items(), key=lambda x:x[1], reverse=True)
        # small distance = good -> don't reverse sorting. Need to check for -1 -> keep values
        sortedDistance = sorted(distance_per_player.items(), key=lambda x:x[1])
        sortedDeaths = sorted(deaths_per_player.items(), key=lambda x:x[1], reverse=True)
        sortedKills = sorted(kills_per_player.items(), key=lambda x:x[1], reverse=True)        

        if debug:
            print("sorted dmg:", sortedDamage,"\n")
            print("sorted strips:", sortedStrips,"\n")
            print("sorted cleanses:",sortedCleanses,"\n")
            print("sorted stab:", sortedStab,"\n")
            print("sorted healing:", sortedHealing,"\n")
            print("sorted distance:", sortedDistance, "\n")
        
        # increase number of times top x was achieved for top x players in each stat
        increase_top_x_reached(players, sortedDamage, player_index, config, 'dmg')
        increase_top_x_reached(players, sortedStrips, player_index, config, 'rips')
        increase_top_x_reached(players, sortedStab, player_index, config, 'stab')
        increase_top_x_reached(players, sortedCleanses, player_index, config, 'cleanses')
        increase_top_x_reached(players, sortedHealing, player_index, config, 'heal')
        increase_top_x_reached(players, sortedDistance, player_index, config, 'dist')
        increase_top_x_reached(players, sortedDeaths, player_index, config, 'deaths')
        increase_top_x_reached(players, sortedKills, player_index, config, 'kills')        
    
    for player in players:
        player.attendance_percentage = player.num_fights_present / used_fights*100
        for stat in player.consistency_stats.keys():
            player.percentage_top_stats[stat] = player.consistency_stats[stat]/player.num_fights_present


    myprint(log, "\n")
    
    return players, overall_squad_stats, used_fights_duration, used_fights, total_fights, num_players_per_fight, num_enemies_per_fight, found_healing



# print the overall squad stats
def print_total_squad_stats(overall_squad_stats, used_fights, used_fights_duration, total_fights, num_players_per_fight, num_enemies_per_fight, found_healing, output):
    #get total duration in h, m, s
    total_fight_duration = {}
    total_fight_duration["h"] = int(used_fights_duration/3600)
    total_fight_duration["m"] = int((used_fights_duration - total_fight_duration["h"]*3600) / 60)
    total_fight_duration["s"] = int(used_fights_duration - total_fight_duration["h"]*3600 -  total_fight_duration["m"]*60)

    total_stab_duration = {}
    total_stab_duration["h"] = int(overall_squad_stats['stab']/3600)
    total_stab_duration["m"] = int((overall_squad_stats['stab'] - total_stab_duration["h"]*3600)/60)
    total_stab_duration["s"] = int(overall_squad_stats['stab'] - total_stab_duration["h"]*3600 - total_stab_duration["m"]*60)    

    mean_players = sum(num_players_per_fight)/len(num_players_per_fight)
    mean_enemies = sum(num_enemies_per_fight)/len(num_enemies_per_fight)
    
    print_string = "The following stats are computed over "+str(used_fights)+" out of "+str(total_fights)+" fights.\n"# fights with a total duration of "+used_fights_duration+".\n"
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
    print_string += str(total_fight_duration["m"])+"m "+str(total_fight_duration["s"])+"s in "+str(used_fights)+" fights.\n"
    print_string += "There were between "+str(min(num_players_per_fight))+" and "+str(max(num_players_per_fight))+" allied players involved (mean "+str(round(mean_players, 1))+" players).\n"
    print_string += "The squad faced between "+str(min(num_enemies_per_fight))+" and "+str(max(num_enemies_per_fight))+" enemy players (mean "+str(round(mean_enemies, 1))+" players).\n"    
        
    myprint(output, print_string)
    return total_fight_duration


