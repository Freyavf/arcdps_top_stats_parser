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


import os.path
from os import listdir
import importlib
import json

from io_helper import myprint
from stat_classes import *
from json_helper import *

# For all players considered to be top in stat in this fight, increase
# the number of fights they reached top by 1 (i.e. increase
# consistency_stats[stat]).
# Input:
# players = list of all players
# sortedList = list of (player names+profession, stat_value) sorted by stat value in this fight
# config = configuration to use
# stat = stat that is considered
def increase_top_x_reached(players, sortedList, config, stat, fight_number):
    valid_values = 0
    # filter out com for dist to tag
    if stat == 'dist':
        # different for dist, filter out com since his distance is always 0
        first_valid = True
        i = 0
        last_val = 0
        while i < len(sortedList) and (valid_values < config.num_players_considered_top[stat]+1 or sortedList[i][1] == last_val):
            if not players[sortedList[i][0]].stats_per_fight[fight_number]['present_in_fight']:
                i += 1
                continue
            # sometimes dist is -1, filter these out
            if sortedList[i][1] >= 0:
                # first valid dist is the comm, don't consider
                if first_valid:
                    first_valid  = False
                else:
                    # player was top in this fight
                    players[sortedList[i][0]].consistency_stats[stat] += 1
                    valid_values += 1
            last_val = sortedList[i][1]
            i += 1
        return

    # total value doesn't need to be > 0 for deaths or stripped
    elif stat == 'deaths' or stat == 'stripped':
        i = 0
        last_val = 0
        # check the whole list or until the number of players considered to be "top" were found (including double places)
        while i < len(sortedList) and (valid_values < config.num_players_considered_top[stat] or sortedList[i][1] == last_val):
            # player wasn't in this fight, ignore
            if not players[sortedList[i][0]].stats_per_fight[fight_number]['present_in_fight']:
                i += 1
                continue
            # only 0 deaths counts as top for deaths
            if sortedList[i][1] == 0:
                players[sortedList[i][0]].consistency_stats[stat] += 1
                last_val = sortedList[i][1]
            i += 1
            valid_values += 1
        return
    
    
    # increase top stats reached for the first num_players_considered_top players (including double places)
    i = 0
    last_val = 0
    while i < len(sortedList) and (valid_values < config.num_players_considered_top[stat] or sortedList[i][1] == last_val) and players[sortedList[i][0]].total_stats[stat] > 0:
        # for dmg_taken or stripped, it's ok to have 0, for all other stats, you can only be in top if you contributed
        if not players[sortedList[i][0]].stats_per_fight[fight_number]['present_in_fight'] or (sortedList[i][1] == 0 and ('dmg_taken' not in stat and stat != 'stripped')):
            i += 1
            continue
        # player was top in this fight
        players[sortedList[i][0]].consistency_stats[stat] += 1
        last_val = sortedList[i][1]
        i += 1
        valid_values += 1
    return



# sort the list of players by value in stat in fight fight_num
# Input:
# players = list of all Players
# stat = stat that is considered
# fight_num = number of the fight that is considered
# Output:
# list of (player index, stat value in fight fight_num), sorted by total stat value in fight fight_num
def sort_players_by_value_in_fight(players, stat, fight_num):
    # get list of (stat value, index)
    decorated = [(player.stats_per_fight[fight_num][stat], i) for i, player in enumerate(players)]
    if stat == 'dist' or 'dmg_taken' in stat or stat == 'deaths' or stat == 'stripped':
        # for tag distance, dmg taken, deaths, and stripped, low numbers are good
        decorated.sort()
    else:
        # for all other stats, high numbers are good
        decorated.sort(reverse=True)
    # extract list of (index, stat value)
    sorted_by_value = [(i, value) for value, i in decorated]
    return sorted_by_value



# sort the list of players by total value in stat
# Input:
# players = list of all Players
# stat = stat that is considered
# Output:
# list of (player index, total stat value), sorted by total stat value
def sort_players_by_total(players, stat):
    # get list of (total stat, index)
    decorated = [(player.total_stats[stat], i) for i, player in enumerate(players)]
    if stat == 'dist' or 'dmg_taken' in stat or stat == 'deaths' or stat == 'stripped':
        # for tag distance, dmg taken, deaths, and stripped, low numbers are good
        decorated.sort()
    else:
        # for all other stats, high numbers are good
        decorated.sort(reverse=True)
    # extract list of (index, total stat)
    sorted_by_total = [(i, total) for total, i in decorated]
    return sorted_by_total



# sort the list of players by consistency value in stat
# Input:
# players = list of all Players
# stat = stat that is considered
# Output:
# list of (player index, consistency stat value), sorted by consistency stat value (how often was top x reached)
def sort_players_by_consistency(players, stat):
    # get list of (times top, total stat, index), sort first by times top (high value = good) and then by total
    decorated = [(player.consistency_stats[stat], player.total_stats[stat], i) for i, player in enumerate(players)]
    decorated.sort(reverse=True)
    # extract list of (index, times top)
    sorted_by_consistency = [(i, consistency) for consistency, total, i in decorated]
    return sorted_by_consistency



# sort the list of players by percentage value in stat
# Input:
# players = list of all Players
# stat = stat that is considered
# Output:
# list of (player index, percentage stat value), sorted by percentage stat value (how often was top x reached / number of fights attended)
def sort_players_by_percentage(players, stat):
    # get list of (percentage times top, times top, total stat, index), sort first by percentage times top (high value = good), then by times top, and then by total
    decorated = [(player.portion_top_stats[stat], player.consistency_stats[stat], player.total_stats[stat], i) for i, player in enumerate(players)]                
    decorated.sort(reverse=True)
    # extract list of (index, percentage times top)
    sorted_by_percentage = [(i, percentage) for percentage, consistency, total, i in decorated]
    return sorted_by_percentage



# sort the list of players by average value in stat
# Input:
# players = list of all Players
# stat = stat that is considered
# Output:
# list of (player index, average stat value), sorted by average stat value ( total stat value / duration of fights attended)
def sort_players_by_average(players, stat):
    # get list of (average stat, times top, total stat, index), sort first by average stat, then by times top, and then by total
    decorated = [(player.average_stats[stat], player.consistency_stats[stat], player.total_stats[stat], i) for i, player in enumerate(players)]
    if stat == 'dist' or 'dmg_taken' in stat or stat == 'deaths' or stat == 'stripped':
        # for dist, dmg taken, deaths, and stripped: low values good
        decorated.sort()
    else:
        # for all other stats: high values good
        decorated.sort(reverse=True)
    # extract list of (index, average stat)
    sorted_by_average = [(i, average) for average, consistency, total, i in decorated]
    return sorted_by_average



# replace all acount names with "account <number>" and all player names with "anon <number>"
def anonymize_players(players, account_index):
    for account in account_index:
        for i in account_index[account]:
            players[i].account = "Account "+str(i)
    for i,player in enumerate(players):
        player.name = "Anon "+str(i)


        
# Input:
# players = list of Players
# config = the configuration being used to determine top players
# stat = which stat are we considering
# total_or_consistent_or_average = enum StatType, either StatType.TOTAL, StatType.CONSISTENT or StatType.AVERAGE, we are getting the players with top total values, top consistency values, or top average values.
# Output:
# list of player indices getting a consistency / total / average award
def get_top_players(players, config, stat, total_or_consistent_or_average):
    percentage = 0.
    sorted_index = []
    # get correct portion of total value and get sorted list of (player index, total/consistency/average stat) 
    if total_or_consistent_or_average == StatType.TOTAL:
        percentage = float(config.portion_of_top_for_total)
        sorted_index = sort_players_by_total(players, stat)
    elif total_or_consistent_or_average == StatType.CONSISTENT:
        percentage = float(config.portion_of_top_for_consistent)
        sorted_index = sort_players_by_consistency(players, stat)
    elif total_or_consistent_or_average == StatType.AVERAGE:
        percentage = 0.
        sorted_index = sort_players_by_average(players, stat)        
    else:
        print("ERROR: Called get_top_players for stats that are not total or consistent or average")
        return        
        
    top_value = players[sorted_index[0][0]].total_stats[stat] # using total value for top to compare with
    top_players = list()

    i = 0
    last_value = 0
    while i < len(sorted_index):
        new_value = sorted_index[i][1] # value by which was sorted, i.e. total, consistency, or average
        # index must be lower than number of output desired OR list entry has same value as previous entry, i.e. double place
        if i >= config.num_players_listed[stat] and new_value != last_value:
            break
        last_value = new_value

        # if stat isn't distance, dmg taken, deaths, or stripped, total value must be at least percentage % of top value
        if stat == "dist" or "dmg_taken" in stat or stat == "deaths" or stat == 'stripped' or players[sorted_index[i][0]].total_stats[stat] >= top_value*percentage:
            # consider minimum attendance percentage for average stats
            if total_or_consistent_or_average != StatType.AVERAGE or (players[sorted_index[i][0]].attendance_percentage > config.min_attendance_percentage_for_average):
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
def get_top_percentage_players(players, config, stat, late_or_swapping, num_used_fights, top_consistent_players = list(), top_total_players = list(), top_percentage_players = list(), top_late_players = list()):    
    sorted_index = sort_players_by_percentage(players, stat)
    top_percentage = players[sorted_index[0][0]].portion_top_stats[stat]

    # get correct comparison value for top percentage and minimum attendance
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
 


def get_stats_from_json_data(json_data, players, player_index, account_index, used_fights, fights, config, found_all_buff_ids, found_healing, found_barrier, log, filename):
    # get fight stats
    fight = get_stats_from_fight_json(json_data, config, log)
            
    if not found_all_buff_ids:
        found_all_buff_ids = get_buff_ids_from_json(json_data, config)
                    
    # add new entry for this fight in all players
    for player in players:
        player.stats_per_fight.append({key: value for key, value in config.empty_stats.items()})   

    fight_number = int(len(fights))
        
    # don't compute anything for skipped fights
    if fight.skipped:
        fights.append(fight)
        log.write("skipped "+filename)            
        return used_fights, found_all_buff_ids, found_healing, found_barrier
        
    used_fights += 1

    # get stats for each player
    for player_data in json_data['players']:
        create_new_player = False
        build_swapped = False

        account, name, profession = get_basic_player_data_from_json(player_data)                

        if profession in fight.squad_composition:
            fight.squad_composition[profession] += 1
        else:
            fight.squad_composition[profession] = 1

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
            while len(player.stats_per_fight) <= fight_number:
                player.stats_per_fight.append({key: value for key, value in config.empty_stats.items()})                
            players.append(player)

        player = players[player_index[name_and_prof]]

        player.stats_per_fight[fight_number]['time_active'] = get_stat_from_player_json(player_data, fight, 'time_active', config)
        #player.stats_per_fight[fight_number]['time_to_first_death'] = get_stat_from_player_json(player_data, fight, 'time_to_first_death', config)
        player.stats_per_fight[fight_number]['time_in_combat'] = get_stat_from_player_json(player_data, fight, 'time_in_combat', config)
        player.stats_per_fight[fight_number]['group'] = get_stat_from_player_json(player_data, fight, 'group', config)
        player.stats_per_fight[fight_number]['present_in_fight'] = True
            
        # get all stats that are supposed to be computed from the player data
        for stat in config.stats_to_compute:
            if stat == 'dist':
                player.stats_per_fight[fight_number][stat], player.stats_per_fight[fight_number]['time_to_first_death'] = get_stat_from_player_json(player_data, fight, stat, config)
                player.duration_on_tag += player.stats_per_fight[fight_number]['time_to_first_death']
            else:
                player.stats_per_fight[fight_number][stat] = get_stat_from_player_json(player_data, fight, stat, config)
                    
            if 'heal' in stat and player.stats_per_fight[fight_number][stat] >= 0:
                found_healing = True
            elif stat == 'barrier' and player.stats_per_fight[fight_number][stat] >= 0:
                found_barrier = True                    
            elif stat == 'dist':
                player.stats_per_fight[fight_number][stat] = round(player.stats_per_fight[fight_number][stat])
            elif 'dmg_taken' in stat:
                if player.stats_per_fight[fight_number]['time_in_combat'] == 0:
                    player.stats_per_fight[fight_number]['time_in_combat'] = 1
                player.stats_per_fight[fight_number][stat] = player.stats_per_fight[fight_number][stat]/player.stats_per_fight[fight_number]['time_in_combat']

            # add stats of this fight and player to total stats of this fight and player
            if player.stats_per_fight[fight_number][stat] > 0:
                # buff are generation squad values, using total over time
                if stat in config.buffs_stacking_duration:
                    #value is generated boon time on all squad players / fight duration / (players-1)" in percent, we want generated boon time on all squad players
                    fight.total_stats[stat] += round(player.stats_per_fight[fight_number][stat]/100.*fight.duration*(fight.allies-1), 2)
                    player.total_stats[stat] += round(player.stats_per_fight[fight_number][stat]/100.*fight.duration*(fight.allies-1), 2)
                elif stat in config.buffs_stacking_intensity:
                    #value is generated boon time on all squad players / fight duration / (players-1)", we want generated boon time on all squad players
                    fight.total_stats[stat] += round(player.stats_per_fight[fight_number][stat]*fight.duration*(fight.allies-1), 2)
                    player.total_stats[stat] += round(player.stats_per_fight[fight_number][stat]*fight.duration*(fight.allies-1), 2)
                elif stat == 'dist':
                    if player.stats_per_fight[fight_number][stat] >= 0:
                        fight.total_stats[stat] += round(player.stats_per_fight[fight_number][stat]*player.stats_per_fight[fight_number]['time_to_first_death'])
                        player.total_stats[stat] += round(player.stats_per_fight[fight_number][stat]*player.stats_per_fight[fight_number]['time_to_first_death'])
                elif 'dmg_taken' in stat:
                    fight.total_stats[stat] += round(player.stats_per_fight[fight_number][stat]*player.stats_per_fight[fight_number]['time_in_combat'])
                    player.total_stats[stat] += round(player.stats_per_fight[fight_number][stat]*player.stats_per_fight[fight_number]['time_in_combat'])
                elif stat in config.self_buff_ids:
                    fight.total_stats[stat] += 1
                    player.total_stats[stat] += 1
                else:
                    # all other stats
                    fight.total_stats[stat] += player.stats_per_fight[fight_number][stat]
                    player.total_stats[stat] += player.stats_per_fight[fight_number][stat]
                    
        if debug:
            print(name)
            for stat in player.stats_per_fight[fight_number].keys():
                print(stat+": "+player.stats_per_fight[fight_number][stat])
            print("\n")

        player.num_fights_present += 1
        player.duration_fights_present += fight.duration
        player.duration_active += player.stats_per_fight[fight_number]['time_active']
        player.duration_in_combat += player.stats_per_fight[fight_number]['time_in_combat']
        player.normalization_time_allies += (fight.allies - 1) * fight.duration
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
        increase_top_x_reached(players, sortedStats[stat], config, stat, fight_number)
        # round total_stats for this fight
        fight.total_stats[stat] = round(fight.total_stats[stat])
        fight.avg_stats[stat] = fight.total_stats[stat]
        if fight.avg_stats[stat] > 0 and stat != 'dist':
            fight.avg_stats[stat] = fight.avg_stats[stat] / len([p for p in players if p.stats_per_fight[fight_number][stat] >= 0])

        # avg for buffs stacking duration:
        # total / (allies - 1) / fight duration in % (i.e. * 100)
        # avg for buffs stacking intensity:
        # total / (allies - 1) / fight duration
        if stat in config.buffs_stacking_duration:
            fight.avg_stats[stat] *= 100
        if stat in config.squad_buff_ids:
            fight.avg_stats[stat] /= (fight.allies - 1)
        if stat in config.squad_buff_ids or "dmg_taken" in stat: # not strictly correct for dmg taken, since we use time in combat there, but... eh
            fight.avg_stats[stat] = round(fight.avg_stats[stat]/fight.duration, 2)
            
        if stat == "dist":
            fight.avg_stats[stat] = round(fight.avg_stats[stat]/(sum(p.stats_per_fight[fight_number]['time_to_first_death'] for p in players)), 2)
            

    fights.append(fight)

    return used_fights, found_all_buff_ids, found_healing, found_barrier


    
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
    # healing only in logs if addon was installed
    found_healing = False # Todo what if some logs have healing and some don't
    found_barrier = False    

    players = []        # list of all player/profession combinations
    player_index = {}   # dictionary that matches each player/profession combo to its index in players list
    account_index = {}  # dictionary that matches each account name to a list of its indices in players list

    used_fights = 0
    fights = []
    found_all_buff_ids = False
    
    # iterating over all fights in directory
    files = listdir(args.input_directory)
    sorted_files = sorted(files)
    for filename in sorted_files:
        # skip files of incorrect filetype
        file_start, file_extension = os.path.splitext(filename)
        if file_extension not in ['.json', '.gz'] or "top_stats" in file_start:
            continue

        print_string = "parsing "+filename
        print(print_string)
        file_path = "".join((args.input_directory,"/",filename))

        # load file
        if file_extension == '.gz':
            with gzip.open(file_path, mode="r") as f:
                json_data = json.loads(f.read().decode('utf-8'))
        else:
            json_datafile = open(file_path, encoding='utf-8')
            json_data = json.load(json_datafile)

        used_fights, found_all_buff_ids, found_healing, found_barrier = get_stats_from_json_data(json_data, players, player_index, account_index, used_fights, fights, config, found_all_buff_ids, found_healing, found_barrier, log, filename)

    get_overall_stats(players, used_fights, config)
                
    myprint(log, "\n")

    if anonymize:
        anonymize_players(players, account_index)
    
    return players, fights, found_healing, found_barrier



# compute average stats and some other overall stats for each player
# Input:
# players = list of Players
# used_fights = number of fights that weren't skipped in the stat computation
# config = config used in the stats computation
def get_overall_stats(players, used_fights, config):
    if used_fights == 0:
        print("ERROR: no valid fights found.")
        exit(1)

    # compute percentage top stats and attendance percentage for each player    
    for player in players:
        player.attendance_percentage = round(player.num_fights_present / used_fights*100)
        # round total and portion top stats
        for stat in config.stats_to_compute:
            player.portion_top_stats[stat] = round(player.consistency_stats[stat]/player.num_fights_present, 4)
            player.total_stats[stat] = round(player.total_stats[stat], 2)
            # DON'T SWITCH DMG_TAKEN AND DMG OR HEAL_FROM_REGEN AND HEAL
            if stat == 'dist':
                player.average_stats[stat] = round(player.total_stats[stat]/player.duration_on_tag)
            elif 'dmg_taken' in stat:
                #player.average_stats[stat] = round(player.total_stats[stat]/player.duration_active)
                player.average_stats[stat] = round(player.total_stats[stat]/player.duration_in_combat)
            elif stat == 'heal_from_regen':
                if player.total_stats['hits_from_regen'] == 0:
                    player.average_stats[stat] = 0
                else:
                    player.average_stats[stat] = round(player.total_stats[stat]/player.total_stats['hits_from_regen'], 2)
            elif 'dmg' in stat or 'heal' in stat or stat == 'barrier':
                player.average_stats[stat] = round(player.total_stats[stat]/player.duration_fights_present)
            elif stat == 'deaths':
                player.average_stats[stat] = round(player.total_stats[stat]/(player.duration_fights_present/60), 2)
            elif stat in config.buffs_stacking_duration:
                # TODO figure out self buffs
                player.average_stats[stat] = round(player.total_stats[stat]/player.normalization_time_allies *100, 2)
            elif stat in config.buffs_stacking_intensity:
                player.average_stats[stat] = round(player.total_stats[stat]/player.normalization_time_allies, 2)
            elif stat in config.self_buff_ids:
                player.average_stats[stat] = round(player.total_stats[stat]/player.num_fights_present, 2)
            else:
                player.average_stats[stat] = round(player.total_stats[stat]/player.duration_fights_present, 2)




# add up total squad stats over all fights
# Input:
# fights = list of Fights
# config = config used in the stat computation
# Output:
# Dictionary of total squad values over all fights for all stats to compute
def get_overall_squad_stats(fights, config):
    used_fights = [f for f in fights if not f.skipped]
    # overall stats over whole squad
    overall_squad_stats = {key: 0 for key in config.stats_to_compute}
    for fight in used_fights:
        for stat in config.stats_to_compute:
            overall_squad_stats[stat] += fight.total_stats[stat]

    # use avg instead of total for buffs
    normalizer_duration_allies = sum([f.duration * (f.allies - 1) * f.allies for f in used_fights])
    for stat in config.stats_to_compute:
        if stat not in config.squad_buff_ids:
            continue
        if stat in config.buffs_stacking_duration:
            overall_squad_stats[stat] = overall_squad_stats[stat] * 100
        overall_squad_stats[stat] = round(overall_squad_stats[stat] / normalizer_duration_allies, 2)
    if "dist" in config.stats_to_compute:
        overall_squad_stats['dist'] = round(overall_squad_stats['dist'] / (sum([f.duration * f.allies for f in fights])), 2)
    return overall_squad_stats



# get raid stats like date, start and end time, number of skipped fights, etc.
# Input:
# fights = list of Fights
# Output:
# Dictionary of raid stats
def get_overall_raid_stats(fights):
    overall_raid_stats = {}
    used_fights = [f for f in fights if not f.skipped]

    overall_raid_stats['num_used_fights'] = len([f for f in fights if not f.skipped])
    overall_raid_stats['used_fights_duration'] = sum([f.duration for f in used_fights])
    overall_raid_stats['date'] = min([f.start_time.split()[0] for f in used_fights])
    overall_raid_stats['start_time'] = min([f.start_time.split()[1] for f in used_fights])
    overall_raid_stats['end_time'] = max([f.end_time.split()[1] for f in used_fights])
    overall_raid_stats['num_skipped_fights'] = len([f for f in fights if f.skipped])
    overall_raid_stats['min_allies'] = min([f.allies for f in used_fights])
    overall_raid_stats['max_allies'] = max([f.allies for f in used_fights])    
    overall_raid_stats['mean_allies'] = round(sum([f.allies for f in used_fights])/len(used_fights), 1)
    overall_raid_stats['min_enemies'] = min([f.enemies for f in used_fights])
    overall_raid_stats['max_enemies'] = max([f.enemies for f in used_fights])        
    overall_raid_stats['mean_enemies'] = round(sum([f.enemies for f in used_fights])/len(used_fights), 1)
    overall_raid_stats['total_kills'] = sum([f.kills for f in used_fights])
    overall_raid_stats['avg_squad_composition'] = {}
    for f in used_fights:
        for prof in f.squad_composition:
            if prof in overall_raid_stats['avg_squad_composition']:
                overall_raid_stats['avg_squad_composition'][prof] += f.squad_composition[prof]
            else:
                overall_raid_stats['avg_squad_composition'][prof] = 1
    for prof in overall_raid_stats['avg_squad_composition']:
        overall_raid_stats['avg_squad_composition'][prof] /= len(used_fights) 
                
    return overall_raid_stats
