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
# sortedList = list of (player_index, stat_value) sorted by stat value in this fight
# config = configuration to use
# stat = stat that is considered
# fight_number = index of the fight being considered
def increase_top_x_reached(players, sortedList, config, stat, fight_number):
    valid_values = 0
    # for distance to tag: consider only players with values > 0 (distance 0 should only be com; distance < 0 is invalid)
    i = 0
    last_val = 0
    # check the whole list or until the number of players considered to be "top" were found (including double places)
    while i < len(sortedList) and (valid_values < config.num_players_considered_top[stat] or sortedList[i][1] == last_val):
        # player wasn't present in this fight, ignore
        if not players[sortedList[i][0]].stats_per_fight[fight_number]['present_in_fight']:
            i += 1
            continue

        # only 0 deaths counts as top for a fight
        if stat == 'deaths' and sortedList[i][1] == 0:
            players[sortedList[i][0]].consistency_stats[stat] += 1
            valid_values += 1
            last_val = sortedList[i][1]
        # for incoming strips, dmg taken, or downstate, anything >= 0 can be top
        elif (stat == 'stripped' or 'dmg_taken' in stat or stat == 'downstate') and sortedList[i][1] >= 0:
            players[sortedList[i][0]].consistency_stats[stat] += 1
            valid_values += 1
            last_val = sortedList[i][1]
        # for all other stats, only values > 0 can be top
        elif sortedList[i][1] > 0:
            players[sortedList[i][0]].consistency_stats[stat] += 1
            valid_values += 1
            last_val = sortedList[i][1]
        i += 1
    return



# sort the list of players by value in stat in fight fight_num
# Input:
# players = list of all Players
# stat = stat that is considered
# fight_num = number of the fight that is considered
# is_squad_buff = stat is a squad buff
# Output:
# list of (player index, stat value in fight fight_num), sorted by total stat value in fight fight_num
def sort_players_by_value_in_fight(players, stat, fight_num, is_squad_buff):
    # get list of (stat value, index)
    decorated = []
    if is_squad_buff:
        decorated = [(player.stats_per_fight[fight_num][stat]['gen'], i) for i, player in enumerate(players)]
    else:
        decorated = [(player.stats_per_fight[fight_num][stat], i) for i, player in enumerate(players)]
    if stat == 'dist' or 'dmg_taken' in stat or stat == 'deaths' or stat == 'stripped' or stat == 'downstate':
        # for tag distance, dmg taken, deaths, stripped, and downstate, low numbers are good
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
# is_squad_buff = stat is a squad buff
# Output:
# list of (player index, total stat value), sorted by total stat value
def sort_players_by_total(players, stat, is_squad_buff):
    # get list of (total stat, index)
    decorated = []
    if is_squad_buff:
        decorated = [(player.total_stats[stat]['gen'], i) for i, player in enumerate(players)]
    else:
        decorated = [(player.total_stats[stat], i) for i, player in enumerate(players)]
    if stat == 'dist' or 'dmg_taken' in stat or stat == 'deaths' or stat == 'stripped' or stat == 'downstate':
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
# is_squad_buff = stat is a squad buff
# Output:
# list of (player index, consistency stat value), sorted by consistency stat value (how often was top x reached)
def sort_players_by_consistency(players, stat, is_squad_buff):
    # get list of (times top, total stat, index), sort first by times top (high value = good) and then by total
    decorated = []
    if is_squad_buff:
        decorated = [(player.consistency_stats[stat], player.total_stats[stat]['gen'], i) for i, player in enumerate(players)]
    else:
        decorated = [(player.consistency_stats[stat], player.total_stats[stat], i) for i, player in enumerate(players)]
    decorated.sort(reverse=True)
    # extract list of (index, times top)
    sorted_by_consistency = [(i, consistency) for consistency, total, i in decorated]
    return sorted_by_consistency



# sort the list of players by percentage value in stat
# Input:
# players = list of all Players
# stat = stat that is considered
# is_squad_buff = stat is a squad buff
# Output:
# list of (player index, percentage stat value), sorted by percentage stat value (how often was top x reached / number of fights attended)
def sort_players_by_percentage(players, stat, is_squad_buff):
    # get list of (percentage times top, times top, total stat, index), sort first by percentage times top (high value = good), then by times top, and then by total
    decorated = []
    if is_squad_buff:
        decorated = [(player.portion_top_stats[stat], player.consistency_stats[stat], player.total_stats[stat]['gen'], i) for i, player in enumerate(players)]
    else:
        decorated = [(player.portion_top_stats[stat], player.consistency_stats[stat], player.total_stats[stat], i) for i, player in enumerate(players)]
    decorated.sort(reverse=True)
    # extract list of (index, percentage times top)
    sorted_by_percentage = [(i, percentage) for percentage, consistency, total, i in decorated]
    return sorted_by_percentage



# sort the list of players by average value in stat
# Input:
# players = list of all Players
# stat = stat that is considered
# is_squad_buff = stat is a squad buff
# Output:
# list of (player index, average stat value), sorted by average stat value ( total stat value / duration of fights attended)
def sort_players_by_average(players, stat, is_squad_buff):
    # get list of (average stat, times top, total stat, index), sort first by average stat, then by times top, and then by total
    decorated = []
    if is_squad_buff:
        decorated = [(player.average_stats[stat], player.consistency_stats[stat], player.total_stats[stat]['gen'], i) for i, player in enumerate(players)]
    else:
        decorated = [(player.average_stats[stat], player.consistency_stats[stat], player.total_stats[stat], i) for i, player in enumerate(players)]
    if stat == 'dist' or 'dmg_taken' in stat or stat == 'deaths' or stat == 'stripped' or stat == 'downstate':
        # for dist, dmg taken, deaths, downstate, and stripped: low values good
        decorated.sort()
    else:
        # for all other stats: high values good
        decorated.sort(reverse=True)
    # extract list of (index, average stat)
    sorted_by_average = [(i, average) for average, consistency, total, i in decorated]
    return sorted_by_average



# replace all acount names with "Account <number>" and all player names with "Anon <number>"
# Input:
# players = list of all Players
# account_index = dictionary of account name -> list of player indices; one account can map to several players since one player = <character name>_<profession>
def anonymize_players(players, account_index):
    for account in account_index:
        for i in account_index[account]:
            players[i].account = "Account "+str(i)
    for i,player in enumerate(players):
        player.name = "Anon "+str(i)



# Get the top players wrt total value, average value, or consistency.
# Only if a given percentage of the total value of the overall top total player was reached, a player will be considered for the top n.
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
        sorted_index = sort_players_by_total(players, stat, (stat in config.squad_buff_abbrev.values()))
    elif total_or_consistent_or_average == StatType.CONSISTENT:
        percentage = float(config.portion_of_top_for_consistent)
        sorted_index = sort_players_by_consistency(players, stat, (stat in config.squad_buff_abbrev.values()))
    elif total_or_consistent_or_average == StatType.AVERAGE:
        percentage = 0.
        sorted_index = sort_players_by_average(players, stat, (stat in config.squad_buff_abbrev.values()))
    else:
        print("ERROR: Called get_top_players for stats that are not total or consistent or average")
        return        

    # using total value for overall top player to compare with
    top_value = 0
    if stat in config.squad_buff_abbrev.values():
        top_value = players[sorted_index[0][0]].total_stats[stat]['gen']
    else:
        top_value = players[sorted_index[0][0]].total_stats[stat]
    top_players = list()

    i = 0
    last_value = 0
    while i < len(sorted_index):
        new_value = sorted_index[i][1] # value by which was sorted, i.e. total, consistency, or average
        # index must be lower than number of output desired OR list entry has same value as previous entry, i.e. double place
        if i >= config.num_players_listed[stat] and new_value != last_value:
            break
        last_value = new_value
        total_value = 0
        if stat in config.squad_buff_abbrev.values():
            total_value = players[sorted_index[i][0]].total_stats[stat]['gen']
        else:
            total_value = players[sorted_index[i][0]].total_stats[stat]

        # if stat isn't distance, dmg taken, deaths, stripped, or downstate, total value must be at least percentage % of top value
        if stat == "dist" or "dmg_taken" in stat or stat == "deaths" or stat == 'stripped' or stat == 'downstate' or stat in config.squad_buff_abbrev.values() or total_value >= top_value*percentage:
            # consider minimum attendance percentage for average stats
            if total_or_consistent_or_average != StatType.AVERAGE or (players[sorted_index[i][0]].attendance_percentage > config.min_attendance_percentage_for_average):
                top_players.append(sorted_index[i][0])

        i += 1

    return top_players
            


# Input:
# players = list of Players
# config = the configuration being used to determine top players
# stat = which stat are we considering
# num_used_fights = number of fights considered for computing top stats
# top_consistent_players (optional) = list of top consistent player indices
# top_total_players (optional) = list of top total player indices
# top_percentage_players (optional) = list of top percentage player indices
# top_late_players (optional) = list of player indices with late but great awards
# Output:
# list of player indices getting a percentage award, value with which the percentage stat was compared
def get_top_percentage_players(players, config, stat, num_used_fights, top_consistent_players = list(), top_total_players = list()):
    sorted_index = sort_players_by_percentage(players, stat, (stat in config.squad_buff_abbrev.values()))
    top_percentage = players[sorted_index[0][0]].portion_top_stats[stat]

    # get correct comparison value for top percentage and minimum attendance
    comparison_value = top_percentage * config.portion_of_top_for_percentage
    min_attendance = config.min_attendance_portion_for_percentage * num_used_fights

    top_players = list()

    last_value = 0
    for (ind, percent) in sorted_index:
        # player wasn't there for enough fights
        if players[ind].num_fights_present < min_attendance:
            continue
        # index must be lower than number of output desired OR list entry has same value as previous entry, i.e. double place
        if len(top_players) >= config.num_players_listed[stat] and percent != last_value:
            break
        last_value = percent

        if percent >= comparison_value:
            top_players.append(ind)

    return top_players, comparison_value
 


# Given the values per fight and player, compute the total values for each player over all fights and for each fight over all players
# Stores result directly in players / fights
# Input:
# players = list of Players
# fights = light of Fights
# config = the config being used to compute top stats
def compute_total_values(players, fights, config):
    for player in players:
        for fight_number in range(len(fights)):
            fight = fights[fight_number]
            player_stats = player.stats_per_fight[fight_number]
            if player_stats['present_in_fight']:
                # increase number of fights the player was present
                player.num_fights_present += 1
                # compute overall duration present (for all types) and the normalization factor of duration * allies
                for duration_type in player.duration_present:
                    player.duration_present[duration_type] += player_stats['duration_present'][duration_type]
                    player.normalization_time_allies[duration_type] += (fight.allies - 1) * player.stats_per_fight[fight_number]['duration_present'][duration_type]

                # compute total values per player and per fight
                for stat in config.stats_to_compute:
                    duration_type = config.duration_for_averages[stat]
                    # add stats of this fight and player to total stats of this fight and player, if value is valid ( >=0 )
                    if player_stats['present_in_fight'] and (player_stats['duration_present'][duration_type] > 0) and ((stat not in config.squad_buff_abbrev.values() and player_stats[stat] >= 0) or stat in config.squad_buff_abbrev.values()):
                        # buff are generation squad values, using total over time
                        if stat in config.buffs_stacking_duration:
                            if player_stats[stat]['gen'] >= 0:
                                # value from json is generated boon time on all squad players / fight duration / (players-1)" in percent, we want generated boon time on all squad players
                                fight.total_stats[stat] += player_stats[stat]['gen'] / 100. * player_stats['duration_present'][duration_type] * (fight.allies-1)
                                player.total_stats[stat]['gen'] += player_stats[stat]['gen'] / 100. * player_stats['duration_present'][duration_type] * (fight.allies-1)
                            if player_stats[stat]['uptime'] >= 0:
                                player.total_stats[stat]['uptime'] += player_stats[stat]['uptime'] / 100. * player_stats['duration_present'][duration_type]
                        elif stat in config.buffs_not_stacking:
                            if player_stats[stat]['gen'] >= 0:
                                # value from json is boon uptime / fight duration" in percent, we want overall boon uptime
                                fight.total_stats[stat] += player_stats[stat]['gen'] / 100. * player_stats['duration_present'][duration_type]
                                player.total_stats[stat]['gen'] += player_stats[stat]['gen'] / 100. * player_stats['duration_present'][duration_type]
                            if player_stats[stat]['uptime'] >= 0:
                                player.total_stats[stat]['uptime'] += player_stats[stat]['uptime'] / 100. * player_stats['duration_present'][duration_type]
                        elif stat in config.buffs_stacking_intensity:
                            if player_stats[stat]['gen'] >= 0:
                                # value from json is generated boon time on all squad players / fight duration / (players-1)", we want generated boon time on all squad players
                                fight.total_stats[stat] += player_stats[stat]['gen'] * player_stats['duration_present'][duration_type] * (fight.allies-1)
                                player.total_stats[stat]['gen'] += player_stats[stat]['gen'] * player_stats['duration_present'][duration_type] * (fight.allies-1)
                            if player_stats[stat]['uptime'] >= 0:
                                player.total_stats[stat]['uptime'] += player_stats[stat]['uptime'] / 100. * player_stats['duration_present'][duration_type]
                        elif stat == 'dist':
                            if player_stats[stat] >= 0:
                                fight.total_stats[stat] += player_stats[stat] * player_stats['duration_present'][duration_type]
                                player.total_stats[stat] += player_stats[stat] * player_stats['duration_present'][duration_type]
                        elif 'dmg_taken' in stat:
                            fight.total_stats[stat] += player_stats[stat] * player_stats['duration_present'][duration_type]
                            player.total_stats[stat] += player_stats[stat] * player_stats['duration_present'][duration_type]
                        elif stat in config.self_buff_ids:
                            # only count whether or not buff was present
                            fight.total_stats[stat] += player_stats[stat]
                            player.total_stats[stat] += player_stats[stat]
                        elif stat == 'spike_dmg':
                            fight.total_stats[stat] = max(fight.total_stats[stat], player_stats[stat])
                            player.total_stats[stat] = max(player.total_stats[stat], player_stats[stat])
                        elif stat in config.squad_buff_abbrev.values():
                            if player_stats[stat]['gen'] >= 0:
                                fight.total_stats[stat] += player.stats_per_fight[fight_number][stat]['gen']
                                player.total_stats[stat]['gen'] += player.stats_per_fight[fight_number][stat]['gen']
                            if player_stats[stat]['uptime'] >= 0:
                                player.total_stats[stat]['uptime'] += player.stats_per_fight[fight_number][stat]['uptime']
                        else:
                            # all other stats
                            fight.total_stats[stat] += player.stats_per_fight[fight_number][stat]
                            player.total_stats[stat] += player.stats_per_fight[fight_number][stat]



# Given the total values per fight and player, compute the average values for each player over all fights and for each fight over all players
# Stores result directly in players / fights
# Input:
# players = list of Players
# fights = light of Fights
# config = the config being used to compute top stats
# TODO use only duration of fight where stat >= 0
def compute_avg_values(players, fights, config): 
    total_normalization_time_per_fight = list()
    for fight_number in range(len(fights)):
        total_normalization_time_per_fight.append({})
        for duration_type in config.empty_stats['duration_present']:
            # sum_players (player_duration_present)
            total_normalization_time_per_fight[fight_number][duration_type] = sum([player.stats_per_fight[fight_number]['duration_present'][duration_type] for player in players])

    total_normalization_time_allies_per_fight = list()
    for fight_number in range(len(fights)):
        total_normalization_time_allies_per_fight.append({})
        for duration_type in config.empty_stats['duration_present']:
            # sum_players (player_duration_present * (allies - 1))
            total_normalization_time_allies_per_fight[fight_number][duration_type] = total_normalization_time_per_fight[fight_number][duration_type] * (fights[fight_number].allies - 1)

    for stat in config.stats_to_compute:
        for fight_number in range(len(fights)):
            if fights[fight_number].skipped:
                continue
            fight = fights[fight_number]
            # round total_stats for this fight
            fight.total_stats[stat] = round(fight.total_stats[stat])
            fight.avg_stats[stat] = fight.total_stats[stat]

            # TODO double check fight avg stats
            if stat == 'spike_dmg':
                fight.avg_stats[stat] = sum(player.stats_per_fight[fight_number][stat] for player in players)/len(players)
            elif stat in config.squad_buff_abbrev.values() and stat in config.buffs_not_stacking:
                # all not stacking buff averages are per time, and the % values are always relative to the total fight duration
                fight.avg_stats[stat] /= total_normalization_time_per_fight[fight_number]['total']
            elif stat in config.squad_buff_abbrev.values() and stat not in config.buffs_not_stacking:
                # all buff averages are per time and allied player
                fight.avg_stats[stat] /= total_normalization_time_allies_per_fight[fight_number][config.duration_for_averages[stat]]
            else:
                # all other averages are per time
                fight.avg_stats[stat] /= total_normalization_time_per_fight[fight_number][config.duration_for_averages[stat]]

            if stat in config.buffs_stacking_duration or stat in config.buffs_not_stacking:
                # averages for buffs stacking duration are given in % -> * 100
                fight.avg_stats[stat] *= 100

    for player in players:
        # compute percentage top stats and attendance percentage for each player
        used_fights = len([fight for fight in fights if fight.skipped == False])
        player.attendance_percentage = round(sum(fight.duration for i,fight in enumerate(fights) if player.stats_per_fight[i]['present_in_fight']) / sum(fight.duration for fight in fights if fight.skipped == False) * 100)
        # round total and portion top stats
        for stat in config.stats_to_compute:
            player.portion_top_stats[stat] = round(player.consistency_stats[stat]/player.num_fights_present, 4)
            if stat in config.squad_buff_abbrev.values():
                player.total_stats[stat]['gen'] = round(player.total_stats[stat]['gen'], 2)
#                player.total_stats[stat]['uptime'] = round(player.total_stats[stat]['uptime'], 2)
                player.total_stats[stat]['uptime'] = round(player.total_stats[stat]['uptime']/player.duration_present['total'] * 100, 2)
                if player.total_stats[stat]['gen'] <= 0:
                    player.average_stats[stat] = player.total_stats[stat]['gen']
                    continue
            else:
                player.total_stats[stat] = round(player.total_stats[stat], 2)
                if player.total_stats[stat] == 0:
                    player.average_stats[stat] = 0
                    continue
            
            # DON'T SWITCH DMG_TAKEN AND DMG OR HEAL_FROM_REGEN AND HEAL
            if stat == 'spike_dmg':
                # find the fights that weren't skipped in which the player was present
                fights_used_for_player = [fight for fight_number,fight in enumerate(fights) if fight.skipped == False and player.stats_per_fight[fight_number]['present_in_fight']]
                if not fights_used_for_player:
                    player.average_stats[stat] = 0
                else:
                    player.average_stats[stat] = 0
                    # sum over all fights that weren't skipped and in which the player was present
                    for fight_number,fight in enumerate(fights):
                        if fight.skipped == False and player.stats_per_fight[fight_number]['present_in_fight']:
                            player.average_stats[stat] += player.stats_per_fight[fight_number][stat]
                    # average over all fights in which he was present
                    player.average_stats[stat] /= len(fights_used_for_player)

            elif stat == 'heal_from_regen':
                if player.total_stats['hits_from_regen'] == 0:
                    player.average_stats[stat] = 0
                else:
                    player.average_stats[stat] = round(player.total_stats[stat]/player.total_stats['hits_from_regen'], 2)
            elif stat == 'deaths' or stat == 'kills' or stat == 'downs' or stat == 'downstate':
                player.average_stats[stat] = round(player.total_stats[stat]/(player.duration_present[config.duration_for_averages[stat]] / 60), 2)
            elif stat in config.self_buff_ids:
                # self buffs are only mentioned as "present" or "not present"
                player.average_stats[stat] = round(player.total_stats[stat]/player.num_fights_present, 2)
            elif stat in config.buffs_stacking_duration:
                player.average_stats[stat] = round(player.total_stats[stat]['gen']/player.normalization_time_allies[config.duration_for_averages[stat]] * 100, 2)
            elif stat in config.buffs_stacking_intensity:
                player.average_stats[stat] = round(player.total_stats[stat]['gen']/player.normalization_time_allies[config.duration_for_averages[stat]], 2)
            elif stat in config.buffs_not_stacking:
                player.average_stats[stat] = round(player.total_stats[stat]['gen']/player.duration_present['total'] * 100, 2)
            else:
                player.average_stats[stat] = round(player.total_stats[stat]/player.duration_present[config.duration_for_averages[stat]], 2)




def get_stats_from_json_data(json_data, players, player_index, account_index, fights, config, found_all_buff_ids, found_healing, found_barrier, log, filename):
    # get fight stats
    fight = get_stats_from_fight_json(json_data, config, log)
            
    if not found_all_buff_ids:
        found_all_buff_ids = get_buff_ids_from_json(json_data, config, log)
                    
    # add new entry for this fight in all players
    for player in players:
        player.stats_per_fight.append({key: value for key, value in config.empty_stats.items()})
        player.stats_per_fight[-1]['duration_present'] = {key: value for key, value in config.empty_stats['duration_present'].items()}

    fight_number = int(len(fights))
        
    # don't compute anything for skipped fights
    if fight.skipped:
        fights.append(fight)
        log.write("skipped "+filename)            
        return found_all_buff_ids, found_healing, found_barrier

    # get stats for each player
    for player_data in json_data['players']:
        build_swapped = False
        new_player_created = False

        account, name, profession, not_in_squad = get_basic_player_data_from_json(player_data)
        if not_in_squad:
            continue

        if profession in fight.squad_composition:
            fight.squad_composition[profession] += 1
        else:
            fight.squad_composition[profession] = 1

        # if this combination of charname + profession is not in the player index yet, create a new entry
        name_and_prof = name+" "+profession
        if name_and_prof not in player_index.keys():
            print("creating new player",name_and_prof)
            new_player = Player(account, name, profession)
            new_player.initialize(config)
            player_index[name_and_prof] = len(players)
            # fill up fights where the player wasn't there yet with empty stats
            while len(new_player.stats_per_fight) <= fight_number:
                new_player.stats_per_fight.append({key: value for key, value in config.empty_stats.items()})
                new_player.stats_per_fight[-1]['duration_present'] = {key: value for key, value in config.empty_stats['duration_present'].items()}
            players.append(new_player)
            new_player_created = True

        # if this account is not in the account index yet, create a new entry
        if account not in account_index.keys():
            account_index[account] = [len(players)-1]
        elif new_player_created:
            # if account does already exist, but name/prof combo does not, this player swapped build or character
            # -> note for all Player instances of this account
            for ind in range(len(account_index[account])):
                players[account_index[account][ind]].swapped_build = True
            account_index[account].append(len(players)-1)
            build_swapped = True

        player = players[player_index[name_and_prof]]

        player.stats_per_fight[fight_number]['duration_present']['total'] = fight.duration
        player.stats_per_fight[fight_number]['duration_present']['active'] = get_stat_from_player_json(player_data, 'time_active', None, None, config)
        player.stats_per_fight[fight_number]['duration_present']['in_combat'] = get_stat_from_player_json(player_data, 'time_in_combat', None, None, config)
        player.stats_per_fight[fight_number]['duration_present']['not_running_back'] = get_stat_from_player_json(player_data, 'time_not_running_back', fight, None, config)
        player.stats_per_fight[fight_number]['group'] = get_stat_from_player_json(player_data, 'group', fight, player.stats_per_fight[fight_number]['duration_present'], config)
        player.stats_per_fight[fight_number]['present_in_fight'] = True

        error_index = len(config.errors)
        # get all stats that are supposed to be computed from the player data
        for stat in config.stats_to_compute:
            # TODO add total stats per fight and avg stats per fight; add option to decide whether "top" should be determined by total or avg ?
            player.stats_per_fight[fight_number][stat] = get_stat_from_player_json(player_data, stat, fight, player.stats_per_fight[fight_number]['duration_present'], config)
            if 'heal' in stat and player.stats_per_fight[fight_number][stat] >= 0:
                found_healing = True
            elif stat == 'barrier' and player.stats_per_fight[fight_number][stat] >= 0:
                found_barrier = True                    
            elif 'dmg_taken' in stat:
                # TODO fix with using proper duration for avg; check the rest of the comp is right
                # if player wasn't present, dmg taken doesn't count
                #TODO for anything where total-players or total-absorbed is something else, use same duration type?
                if player.stats_per_fight[fight_number]['duration_present'][config.duration_for_averages[stat]] == 0:
                    player.stats_per_fight[fight_number][stat] = -1
                else:
                    # dmg taken per fight should be sorted by avg, what else?
                    player.stats_per_fight[fight_number][stat] = player.stats_per_fight[fight_number][stat]/player.stats_per_fight[fight_number]['duration_present'][config.duration_for_averages[stat]]

        player.swapped_build |= build_swapped

        ################################
        ### print warning/debug logs ###
        ################################
        if len(config.errors) > error_index:
            myprint(log, "In fight "+str(fight_number)+", "+player.name+" ("+player.profession+"):", "warning", config)
            for error in config.errors:
                myprint(log, error, "warning", config)
            config.errors = list()
        
        myprint(log, name, "debug", config)
        for stat in player.stats_per_fight[fight_number].keys():
            myprint(log, stat+": "+str(player.stats_per_fight[fight_number][stat]), "debug", config)
        myprint(log, "\n", "debug", config)

    # create lists sorted according to stats
    sortedStats = {key: list() for key in config.stats_to_compute}
    for stat in config.stats_to_compute:
        sortedStats[stat] = sort_players_by_value_in_fight(players, stat, fight_number, (stat in config.squad_buff_abbrev.values()))

    #######################
    ### print debug log ###
    #######################
    for stat in config.stats_to_compute:
        myprint(log, "sorted "+stat+": ", "debug", config)
        for entry in sortedStats[stat]:
            print_string = "("+str(entry[0])+", "+str(entry[1])+")"
            myprint(log, print_string, "debug", config)
        
    # increase number of times top x was achieved for top x players in each stat
    for stat in config.stats_to_compute:
        increase_top_x_reached(players, sortedStats[stat], config, stat, fight_number)
        
    fights.append(fight)

    return found_all_buff_ids, found_healing, found_barrier


    
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

        found_all_buff_ids, found_healing, found_barrier = get_stats_from_json_data(json_data, players, player_index, account_index, fights, config, found_all_buff_ids, found_healing, found_barrier, log, filename)

    if (not fights) or all(fight.skipped for fight in fights):
        # list of fights is empty or all were skipped -> no valid fights were found
        myprint(log, "\n No valid fights were found in "+args.input_directory, "info")
        return None, None, None, None

    get_overall_stats(players, fights, config)
                
    myprint(log, "\n", "info", config)

    if anonymize:
        anonymize_players(players, account_index)
    
    return players, fights, found_healing, found_barrier



# compute total and average stats for each player
# Input:
# players = list of Players
# fights = list of Fights
# config = config used in the stats computation
def get_overall_stats(players, fights, config):
    compute_total_values(players, fights, config)
    compute_avg_values(players, fights, config)



# add up total squad stats over all fights
# Input:
# fights = list of Fights
# config = config used in the stat computation
# Output:
# Dictionary of total squad values over all fights for all stats to compute
def get_overall_squad_stats(fights, config):

    #total_normalization_time = {}
    #for duration_type in config.duration_for_averages:
    #    total_normalization_time[duration_type] = sum([total_normalization_time_per_fight[i][duration_type] for i in range(len(fights))])
    #total_normalization_time_allies = {}
    #for duration_type in config.duration_for_averages:
    #    total_normalization_time_allies[duration_type] = sum([total_normalization_time_allies_per_fight[i][duration_type] for i in range(len(fights))])

    # TODO check that sum([player.normalization_time_allies[duration_type] for player in players]) = total_normalization_time_allies


    # TODO fix averages to use duration_used_for_avgs
    used_fights = [f for f in fights if not f.skipped]
    # overall stats over whole squad
    overall_squad_stats = {'total': {key: 0 for key in config.stats_to_compute}, 'avg': {key: 0 for key in config.stats_to_compute}}
    
    for fight in used_fights:
        for stat in config.stats_to_compute:
            # using max for spike dmg
            if stat == 'spike_dmg':
                overall_squad_stats['total'][stat] = max(overall_squad_stats['total'][stat], fight.total_stats[stat])
            else:
                overall_squad_stats['total'][stat] += fight.total_stats[stat]

    # compute avg values
    normalizer_duration_allies = sum([f.duration * (f.allies - 1) * f.allies for f in used_fights])
    for stat in config.stats_to_compute:
        if stat == 'spike_dmg':
            # TODO fix
            spike_dmg = 0
            overall_allies = 0
            for fight in used_fights:
                spike_dmg += fight.avg_stats[stat] * fight.allies
                overall_allies += fight.allies
            spike_dmg = spike_dmg / (overall_allies * len(used_fights))
            overall_squad_stats['avg'][stat] = round(spike_dmg, 2)
        if stat not in config.squad_buff_abbrev.values():
            overall_squad_stats['avg'][stat] = round(overall_squad_stats['total'][stat] / (sum([f.duration * f.allies for f in fights])), 2)
        else:
            overall_squad_stats['avg'][stat] = overall_squad_stats['total'][stat]
            if stat in config.buffs_stacking_duration:
                overall_squad_stats['avg'][stat] *= 100
            overall_squad_stats['avg'][stat] = round(overall_squad_stats['avg'][stat] / normalizer_duration_allies, 2)
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
