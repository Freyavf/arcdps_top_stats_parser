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
from enum import Enum
import importlib
import xlrd
from xlutils.copy import copy
import json
import jsons
import math

debug = False # enable / disable debug output

class StatType(Enum):
    TOTAL = 1                       # top total stat value over all fights
    CONSISTENT = 2                  # top consistency value over all fights = achieved top in most fights
    AVERAGE = 3                     # top average value over all fights
    LATE_PERCENTAGE = 4             # not there for all fights, but great consistency in the fights present. late but great awards
    SWAPPED_PERCENTAGE = 5          # not there for all fights, swapped build at least once. Jack of all trades awards
    PERCENTAGE = 6                  # top consistency percentage = times top / fights present


    
# This class stores information about a player. Note that a different profession will be treated as a new player / character.
@dataclass
class Player:
    account: str                        # account name
    name: str                           # character name
    profession: str                     # profession name
    num_fights_present: int = 0         # the number of fight the player was involved in 
    attendance_percentage: float = 0.   # the percentage of fights the player was involved in out of all fights
    duration_fights_present: int = 0    # the total duration of all fights the player was involved in, in s
    duration_active: int = 0            # the total duration a player was active (alive or down)
    duration_in_combat: int = 0         # the total duration a player was in combat (taking/dealing dmg)
    normalization_time_allies: int = 0  # the sum of fight duration * (squad members -1) of all fights the player was involved in
    swapped_build: bool = False         # a different player character or specialization with this account name was in some of the fights

    # fields for all stats defined in config
    consistency_stats: dict = field(default_factory=dict)     # how many times did this player get into top for each stat?
    total_stats: dict = field(default_factory=dict)           # what's the total value for this player for each stat?
    average_stats: dict = field(default_factory=dict)         # what's the average stat per second for this player? (exception: deaths are per minute)
    portion_top_stats: dict = field(default_factory=dict)     # what percentage of fights did this player get into top for each stat, in relation to the number of fights they were involved in?
                                                              # = consistency_stats/num_fights_present
    stats_per_fight: list = field(default_factory=list)       # what's the value of each stat for this player in each fight?

    def initialize(self, config):
        self.total_stats = {key: 0 for key in config.stats_to_compute}
        self.average_stats = {key: 0 for key in config.stats_to_compute}        
        self.consistency_stats = {key: 0 for key in config.stats_to_compute}
        self.portion_top_stats = {key: 0 for key in config.stats_to_compute}


        
# This class stores information about a fight
@dataclass
class Fight:
    skipped: bool = False                                 # a fight is skipped in the top stats computation if number of enemies or allies is too small, or if it is too short
    duration: int = 0                                     # duration of the fight in seconds
    total_stats: dict = field(default_factory=dict)       # what's the overall total value for the whole squad for each stat in this fight?
    avg_stats: dict = field(default_factory=dict)         # what's the overall average value for the whole squad for each stat in this fight?
    enemies: int = 0                                      # number of enemy players involved
    allies: int = 0                                       # number of squad players involved
    kills: int = 0                                        # number of kills
    start_time: str = ""                                  # start time of the fight
    squad_composition: dict = field(default_factory=dict) # squad composition of the fight (how many of which class)
    

    
# This class stores the configuration for running the top stats.
@dataclass
class Config:
    num_players_listed: dict = field(default_factory=dict)          # How many players will be listed who achieved top stats most often for each stat?
    num_players_considered_top: dict = field(default_factory=dict)  # How many players are considered to be "top" in each fight for each stat?
    
    min_attendance_portion_for_percentage: float = 0.  # For what portion of all fights does a player need to be there to be considered for "percentage" awards?
    min_attendance_portion_for_late: float = 0.        # For what portion of all fights does a player need to be there to be considered for "late but great" awards?     
    min_attendance_portion_for_buildswap: float = 0.   # For what portion of all fights does a player need to be there to be considered for "jack of all trades" awards?
    min_attendance_percentage_for_average: float = 0.  # For what percentage of all fights does a player need to be there to be considered for "jack of all trades" awards?     

    portion_of_top_for_total: float = 0.         # What portion of the top total player stat does someone need to reach to be considered for total awards?
    portion_of_top_for_consistent: float = 0.    # What portion of the total stat of the top consistent player does someone need to reach to be considered for consistency awards?
    portion_of_top_for_percentage: float = 0.    # What portion of the consistency stat of the top consistent player does someone need to reach to be considered for percentage awards?    
    portion_of_top_for_late: float = 0.          # What portion of the percentage the top consistent player reached top does someone need to reach to be considered for late but great awards?
    portion_of_top_for_buildswap: float = 0.     # What portion of the percentage the top consistent player reached top does someone need to reach to be considered for jack of all trades awards?

    min_allied_players: int = 0   # minimum number of allied players to consider a fight in the stats
    min_fight_duration: int = 0   # minimum duration of a fight to be considered in the stats
    min_enemy_players: int = 0    # minimum number of enemies to consider a fight in the stats

    stat_names: dict = field(default_factory=dict)                  # the names under which the stats appear in the output
    profession_abbreviations: dict = field(default_factory=dict)    # the names under which each profession appears in the output

    empty_stats: dict = field(default_factory=dict)                 # all stat values = -1 for initialization
    stats_to_compute: list = field(default_factory=list)            # all stats that should be computed

    squad_buff_ids: dict = field(default_factory=dict)              # dict of squad buff name to buff id as read from buffMap
    self_buff_ids: dict = field(default_factory=dict)               # dict of self buff name to buff id as read from buffMap
    buffs_stacking_duration: list = field(default_factory=list)     # list of squad_buff names stacking duration
    buffs_stacking_intensity: list = field(default_factory=list)    # list of squad_buff names stacking intensity
    squad_buff_abbrev: dict = field(default_factory=dict)           # abbreviations of squad buff names
    self_buff_abbrev: dict = field(default_factory=dict)            # abbreviations of self buff names
    

    
# prints output_string to the console and the output_file, with a linebreak at the end
def myprint(output_file, output_string, config = None):
    if config == None or "console" in config.files_to_write:
        print(output_string)
    if config == None or "txt" in config.files_to_write:
        output_file.write(output_string+"\n")



# fills a Config with the given input    
def fill_config(config_input):
    config = Config()
    config.num_players_listed = config_input.num_players_listed
    for stat in config_input.stats_to_compute:
        if stat not in config.num_players_listed:
            config.num_players_listed[stat] = config_input.num_players_listed_default
            
    config.num_players_considered_top = config_input.num_players_considered_top
    for stat in config_input.stats_to_compute:
        if stat not in config.num_players_considered_top:
            config.num_players_considered_top[stat] = config_input.num_players_considered_top_default

    config.min_attendance_portion_for_percentage = config_input.attendance_percentage_for_percentage/100.
    config.min_attendance_portion_for_late = config_input.attendance_percentage_for_late/100.    
    config.min_attendance_portion_for_buildswap = config_input.attendance_percentage_for_buildswap/100.
    config.min_attendance_percentage_for_average = config_input.attendance_percentage_for_average

    config.portion_of_top_for_consistent = config_input.percentage_of_top_for_consistent/100.
    config.portion_of_top_for_total = config_input.percentage_of_top_for_total/100.
    config.portion_of_top_for_percentage = config_input.percentage_of_top_for_percentage/100.
    config.portion_of_top_for_late = config_input.percentage_of_top_for_late/100.    
    config.portion_of_top_for_buildswap = config_input.percentage_of_top_for_buildswap/100.

    config.min_allied_players = config_input.min_allied_players
    config.min_fight_duration = config_input.min_fight_duration
    config.min_enemy_players = config_input.min_enemy_players

    config.files_to_write = config_input.files_to_write
    
    config.stat_names = config_input.stat_names
    config.profession_abbreviations = config_input.profession_abbreviations

    config.stats_to_compute = config_input.stats_to_compute
    config.empty_stats = {stat: -1 for stat in config.stats_to_compute}
    config.empty_stats['time_active'] = -1
    config.empty_stats['time_in_combat'] = -1
    config.empty_stats['present_in_fight'] = False

    # TODO move to config?
    config.squad_buff_abbrev["Stability"] = 'stab'
    config.squad_buff_abbrev["Protection"] = 'prot'
    config.squad_buff_abbrev["Aegis"] = 'aegis'
    config.squad_buff_abbrev["Regeneration"] = 'regen'
    config.squad_buff_abbrev["Might"] = 'might'
    config.squad_buff_abbrev["Fury"] = 'fury'
    config.squad_buff_abbrev["Quickness"] = 'quick'
    config.squad_buff_abbrev["Alacrity"] = 'alac'
    config.squad_buff_abbrev["Superspeed"] = 'speed'
    config.self_buff_abbrev["Explosive Entrance"] = 'explosive_entrance'
    config.self_buff_abbrev["Explosive Temper"] = 'explosive_temper'
    config.self_buff_abbrev["Big Boomer"] = 'big_boomer'
    config.self_buff_abbrev["Med Kit"] = 'med_kit'
    
    return config
    


# get ids of buffs in the log from the buff map
# Input:
# player_json: json data with the player info. In a json file as parsed by Elite Insights, one entry of the 'players' list.
# config: config to use in top stats computation
# changes config.buffs_stacking_intensity and config.buffs_stacking_duration inplace
def get_buff_ids_from_json(json_data, config):
    buffs = json_data['buffMap']
    for buff_id, buff in buffs.items():
        if buff['name'] in config.squad_buff_abbrev:
            abbrev_name = config.squad_buff_abbrev[buff['name']]
            config.squad_buff_ids[abbrev_name] = buff_id[1:]
            if buff['stacking']:
                config.buffs_stacking_intensity.append(abbrev_name)
            else:
                config.buffs_stacking_duration.append(abbrev_name)
        if buff['name'] in config.self_buff_abbrev:
            abbrev_name = config.self_buff_abbrev[buff['name']]
            config.self_buff_ids[abbrev_name] = buff_id[1:]


# get stats for this fight from fight_json
# Input:
# fight_json = json object including one fight
# config = the config to use for top stat computation
# log = log file to write to
def get_stats_from_fight_json(fight_json, config, log):
    # get fight duration in min and sec
    fight_duration_json = fight_json['duration']
    split_duration = fight_duration_json.split('h ', 1)
    hours = 0
    mins = 0
    secs = 0
    if len(split_duration) > 1:
        hours = int(split_duration[0])
    split_duration = fight_duration_json.split('m ', 1)
    if len(split_duration) > 1:
        mins = int(split_duration[0])
    split_duration = split_duration[1].split('s', 1)
    if len(split_duration) > 1:
        secs = int(split_duration[0])
    if debug:
        print("duration: ", hours, "h ", mins, "m ", secs, "s")
    duration = hours*3600 + mins*60 + secs

    num_allies = len(fight_json['players'])
    num_enemies = 0
    num_kills = 0
    for enemy in fight_json['targets']:
        if 'enemyPlayer' in enemy and enemy['enemyPlayer'] == True:
            num_enemies += 1
            # if combat replay data is there, add number of times this player died to total num kills
            if 'combatReplayData' in enemy:
                num_kills += len(enemy['combatReplayData']['dead'])
                
    # initialize fight         
    fight = Fight()
    fight.duration = duration
    fight.enemies = num_enemies
    fight.allies = num_allies
    fight.kills = num_kills
    fight.start_time = fight_json['timeStartStd']
    fight.end_time = fight_json['timeEndStd']        
    fight.total_stats = {key: 0 for key in config.stats_to_compute}
    fight.avg_stats = {key: 0 for key in config.stats_to_compute}    
        
    # skip fights that last less than min_fight_duration seconds
    if(duration < config.min_fight_duration):
        fight.skipped = True
        print_string = "\nFight only took "+str(hours)+"h "+str(mins)+"m "+str(secs)+"s. Skipping fight."
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

    # get players using healing addon, if the addon was used
    if 'usedExtensions' not in fight_json:
        players_running_healing_addon = []
    else:
        extensions = fight_json['usedExtensions']
        for extension in extensions:
            if extension['name'] == "Healing Stats":
                players_running_healing_addon = extension['runningExtension']
        
    return fight, players_running_healing_addon



# get account, character name and profession from json object
# Input:
# player_json: json data with the player info. In a json file as parsed by Elite Insights, one entry of the 'players' list.
# Output: account, character name, profession
def get_basic_player_data_from_json(player_json):
    account = player_json['account']
    name = player_json['name']
    profession = player_json['profession']
    return account, name, profession



# get value of stat from player_json
# Input:
# player_json: json data with the player info. In a json file as parsed by Elite Insights, one entry of the 'players' list.
# players_running_healing_addon: names of all characters running the healing addon
# stat: the stat being considered
# config: the config used for top stats computation
def get_stat_from_player_json(player_json, players_running_healing_addon, stat, config):
    if stat == 'time_in_combat':
        return round(sum_breakpoints(get_combat_time_breakpoints(player_json)) / 1000)

    if stat == 'group':
        if 'group' not in player_json:
            return 0
        return int(player_json['group'])
    
    if stat == 'time_active':
        if 'activeTimes' not in player_json:
            return 0
        return round(int(player_json['activeTimes'][0])/1000)

    # includes dmg absorbed by barrier
    if stat == 'dmg_taken' or stat == 'dmg_taken_total':
        if 'defenses' not in player_json or len(player_json['defenses']) != 1 or 'damageTaken' not in player_json['defenses'][0]:
            return 0
        return int(player_json['defenses'][0]['damageTaken'])

    if stat == 'dmg_taken_absorbed':
        if 'defenses' not in player_json or len(player_json['defenses']) != 1 or 'damageBarrier' not in player_json['defenses'][0]:
            return 0
        return int(player_json['defenses'][0]['damageBarrier'])

    if stat == 'dmg_taken_hp_lost':
        total_dmg_taken = get_stat_from_player_json(player_json, players_running_healing_addon, 'dmg_taken_total', config)
        dmg_absorbed = get_stat_from_player_json(player_json, players_running_healing_addon, 'dmg_taken_absorbed', config)
        return total_dmg_taken - dmg_absorbed

    if stat == 'deaths':
        if 'defenses' not in player_json or len(player_json['defenses']) != 1 or 'deadCount' not in player_json['defenses'][0]:
            return 0
        return int(player_json['defenses'][0]['deadCount'])

    #if stat == 'kills':
    #    if 'statsAll' not in player_json or len(player_json['statsAll']) != 1 or 'killed' not in player_json['statsAll'][0]:
    #        return 0        
    #    return int(player_json['statsAll'][0]['killed'])

    if stat == 'dmg_total' or stat == 'dmg':
        if 'dpsAll' not in player_json or len(player_json['dpsAll']) != 1 or 'damage' not in player_json['dpsAll'][0]:
            return 0
        return int(player_json['dpsAll'][0]['damage'])  

    if stat == 'dmg_players':
        if 'targetDamage1S' not in player_json:
            return 0
        return sum(target[0][-1] for target in player_json['targetDamage1S'])

    if stat == 'dmg_other':
        total_dmg = get_stat_from_player_json(player_json, players_running_healing_addon, 'dmg_total', config)
        players_dmg = get_stat_from_player_json(player_json, players_running_healing_addon, 'dmg_players', config)
        return total_dmg - players_dmg

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
            return 0
        return float(player_json['statsAll'][0]['distToCom'])

    if stat == 'stripped':
        if 'defenses' not in player_json or len(player_json['defenses']) != 1 or 'boonStrips' not in player_json['defenses'][0]:
            return 0
        return int(player_json['defenses'][0]['boonStrips'])

    if stat == 'heal' or stat == 'heal_total':
        # check if healing was logged, save it
        if player_json['name'] not in players_running_healing_addon or 'extHealingStats' not in player_json or 'outgoingHealing' not in player_json['extHealingStats']:
            return -1
        return player_json['extHealingStats']['outgoingHealing'][0]['healing']

    if stat == 'heal_players':
        # check if healing was logged, save it
        if player_json['name'] not in players_running_healing_addon or 'extHealingStats' not in player_json or 'alliedHealing1S' not in player_json['extHealingStats']:
            return -1
        return sum([healing[0][-1] for healing in player_json['extHealingStats']['alliedHealing1S']])
    
    if stat == 'heal_other':
        # check if healing was logged, save it
        total_heal = get_stat_from_player_json(player_json, players_running_healing_addon, 'heal_total', config)
        player_heal = get_stat_from_player_json(player_json, players_running_healing_addon, 'heal_players', config)
        if total_heal == -1 or player_heal == -1:
            return -1
        return total_heal - player_heal

    if stat == 'barrier':
        # check if barrier was logged, save it
        if player_json['name'] in players_running_healing_addon and 'extBarrierStats' in player_json and 'outgoingBarrier' in player_json['extBarrierStats']:
            return player_json['extBarrierStats']['outgoingBarrier'][1]['barrier']
        return -1

    if stat == 'heal_from_regen':
        # check if healing was logged, look for regen
        if player_json['name'] in players_running_healing_addon and 'extHealingStats' in player_json and 'totalHealingDist' in player_json['extHealingStats']:
            healing_json = player_json['extHealingStats']['totalHealingDist'][0]
            for healing_json2 in healing_json:
                if 'id' in healing_json2 and healing_json2['id'] == int(config.squad_buff_ids['regen']):
                    return healing_json2['totalHealing']
        return -1    

    if stat == 'hits_from_regen':
        # check if healing was logged, look for regen
        if player_json['name'] in players_running_healing_addon and 'extHealingStats' in player_json and 'totalHealingDist' in player_json['extHealingStats']:
            healing_json = player_json['extHealingStats']['totalHealingDist'][0]
            for healing_json2 in healing_json:
                if 'id' in healing_json2 and healing_json2['id'] == int(config.squad_buff_ids['regen']):
                    return int(healing_json2['hits'])
        return -1

    ### Buffs ###
    if stat in config.squad_buff_ids:
        if 'squadBuffs' not in player_json:
            return 0.
        # get buffs in squad generation -> need to loop over all buffs
        for buff in player_json['squadBuffs']:
            if 'id' not in buff:
                continue 
            # find right buff
            buffId = buff['id']
            if buffId == int(config.squad_buff_ids[stat]):
                if 'buffData' not in buff or len(buff['buffData']) == 0 or 'generation' not in buff['buffData'][0]:
                    return 0.
                return float(buff['buffData'][0]['generation'])
        return 0.

    if stat in config.self_buff_ids:
        if 'selfBuffs' not in player_json:
            return 0
        for buff in player_json['selfBuffs']:
            if 'id' not in buff:
                continue 
            # find right buff
            buffId = buff['id']
            if buffId == int(config.self_buff_ids[stat]):
                if 'buffData' not in buff or len(buff['buffData']) == 0 or 'generation' not in buff['buffData'][0]:
                    return 0
                return 1
        return 0




# find the first time a player took or dealt damage after initial_time
# Input:
# initial_time = check for first time this player was in combat after this time in the fight
# player_json = the json data for this player in this fight
# Output:
# First time the player took or dealt damage after initial_time
def get_combat_start_from_player_json(initial_time, player_json):
    start_combat = -1
    # if healthPercents is not available, assume the player was in combat right away
    if 'healthPercents' not in player_json:
        return initial_time
    last_health_percent = 100
    for change in player_json['healthPercents']:
        # look for last timestamp before initial time
        if change[0] < initial_time:
            last_health_percent = change[1]
            continue
        if change[1] - last_health_percent < 0:
            # got dmg
            start_combat = change[0]
            break
        last_health_percent = change[1]
        
    # from initial time until end of the fight, check when player dealt (power) dmg the first time
    # not using condi, because condis can still tick after a player died
    for i in range(math.ceil(initial_time/1000), len(player_json['powerDamage1S'][0])):
        if i == 0:
            continue
        if player_json['powerDamage1S'][0][i] != player_json['powerDamage1S'][0][i-1]:
            if start_combat == -1:
                start_combat = i*1000
            else:
                start_combat = min(start_combat, i*1000)
            break
    return start_combat


    
# find the combat breakpoints, i.e., start and end points of this player being in combat (interrupted by death)
# Input:
# player_json = the json data for this player in this fight
# Output:
# List of start and end timestamps of the player being in combat
def get_combat_time_breakpoints(player_json):
    start_combat = get_combat_start_from_player_json(0, player_json)
    if 'combatReplayData' not in player_json:
        print("WARNING: combatReplayData not in json, using activeTimes as time in combat")
        # activeTimes = duration the player was not dead
        return [start_combat, get_stat_from_player_json(player_json, None, 'time_active', None) * 1000]
    replay = player_json['combatReplayData']
    if 'dead' not in replay:
        return [start_combat, get_stat_from_player_json(player_json, None, 'time_active', None) * 1000]

    breakpoints = []
    playerDeaths = dict(replay['dead'])
    playerDowns = dict(replay['down'])
    # need corresponding down event for each death event. down end = death start
    for deathStart, deathEnd in playerDeaths.items():
        for downStart, downEnd in playerDowns.items():
            if deathStart == downEnd:
                if start_combat != -1:
                    breakpoints.append([start_combat, deathStart])
                start_combat = get_combat_start_from_player_json(deathEnd + 1000, player_json)
                break
    end_combat = (len(player_json['damage1S'][0]))*1000
    if start_combat != -1:
        breakpoints.append([start_combat, end_combat])

    return breakpoints



# compute the time in combat from the breakpoints as determined in get_combat_time_breakpoints
# Input:
# breakpoints = list of [start combat, end combat] items
# Output:
# total time in combat
def sum_breakpoints(breakpoints):
    combat_time = 0
    for [start, end] in breakpoints:
        combat_time += end - start
    return combat_time



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
            # TODO might be outdated, time to remove?
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
 


def get_stats_from_json_data(json_data, players, player_index, account_index, used_fights, fights, config, first, found_healing, found_barrier, log, filename):
    # get fight stats
    fight, players_running_healing_addon = get_stats_from_fight_json(json_data, config, log)
            
    if first:
        first = False
        get_buff_ids_from_json(json_data, config)
                    
    # add new entry for this fight in all players
    for player in players:
        player.stats_per_fight.append({key: value for key, value in config.empty_stats.items()})   

    fight_number = int(len(fights))
        
    # don't compute anything for skipped fights
    if fight.skipped:
        fights.append(fight)
        log.write("skipped "+filename)            
        return used_fights, first, found_healing, found_barrier
        
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

        player.stats_per_fight[fight_number]['time_active'] = get_stat_from_player_json(player_data, players_running_healing_addon, 'time_active', config)
        player.stats_per_fight[fight_number]['time_in_combat'] = get_stat_from_player_json(player_data, players_running_healing_addon, 'time_in_combat', config)
        player.stats_per_fight[fight_number]['group'] = get_stat_from_player_json(player_data, players_running_healing_addon, 'group', config)
        player.stats_per_fight[fight_number]['present_in_fight'] = True
            
        # get all stats that are supposed to be computed from the player data
        for stat in config.stats_to_compute:
            player.stats_per_fight[fight_number][stat] = get_stat_from_player_json(player_data, players_running_healing_addon, stat, config)
            #print(stat, player.stats_per_fight[fight_number][stat])
                    
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
            #elif stat == 'heal_from_regen':
            #    player.stats_per_fight[fight_number]['hits_from_regen'] = get_stat_from_player_json(player_data, players_running_healing_addon, 'hits_from_regen', config)
                    
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
                    fight.total_stats[stat] += round(player.stats_per_fight[fight_number][stat]*fight.duration)
                    player.total_stats[stat] += round(player.stats_per_fight[fight_number][stat]*fight.duration)
                elif 'dmg_taken' in stat:
                    fight.total_stats[stat] += round(player.stats_per_fight[fight_number][stat]*player.stats_per_fight[fight_number]['time_in_combat'])
                    player.total_stats[stat] += round(player.stats_per_fight[fight_number][stat]*player.stats_per_fight[fight_number]['time_in_combat'])
                #elif stat == 'heal_from_regen':
                #    fight.total_stats[stat] += player.stats_per_fight[fight_number][stat]
                #    player.total_stats[stat] += player.stats_per_fight[fight_number][stat]
                #    fight.total_stats['hits_from_regen'] += player.stats_per_fight[fight_number]['hits_from_regen']
                #    player.total_stats['hits_from_regen'] += player.stats_per_fight[fight_number]['hits_from_regen']
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
        if fight.avg_stats[stat] > 0:
            fight.avg_stats[stat] = fight.avg_stats[stat] / len([p for p in players if p.stats_per_fight[fight_number][stat] >= 0])

        # avg for buffs stacking duration:
        # total / (allies - 1) / fight duration in % (i.e. * 100)
        # avg for buffs stacking intensity:
        # total / (allies - 1) / fight duration
        if stat in config.buffs_stacking_duration:
            fight.avg_stats[stat] *= 100
        if stat in config.squad_buff_ids:
            fight.avg_stats[stat] /= (fight.allies - 1)
        if stat in config.squad_buff_ids or stat == "dist" or "dmg_taken" in stat: # not strictly correct for dmg taken, since we use time in combat there, but... eh
            fight.avg_stats[stat] = round(fight.avg_stats[stat]/fight.duration, 2)

    fights.append(fight)

    return used_fights, first, found_healing, found_barrier


    
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
    first = True
    
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

        used_fights, first, found_healing, found_barrier = get_stats_from_json_data(json_data, players, player_index, account_index, used_fights, fights, config, first, found_healing, found_barrier, log, filename)

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
            if 'dmg_taken' in stat:
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



# get total duration in h, m, s
def get_total_fight_duration_in_hms(fight_duration_in_s):
    total_fight_duration = {}
    total_fight_duration['h'] = int(fight_duration_in_s/3600)
    total_fight_duration['m'] = int((fight_duration_in_s - total_fight_duration['h']*3600) / 60)
    total_fight_duration['s'] = int(fight_duration_in_s - total_fight_duration['h']*3600 -  total_fight_duration['m']*60)
    return total_fight_duration



# print the overall squad stats and some overall raid stats
# Input:
# fights = list of Fights
# overall_squad_stats = overall stats of the whole squad; output of get_overall_squad_stats
# overall_raid_stats = raid stats like start time, end time, total kills, etc.; output of get_overall_raid_stats
# found_healing = was healing logged
# found_barrier = was barrier logged
# config = the config used for stats computation
# output = file to write to
def print_total_squad_stats(fights, overall_squad_stats, overall_raid_stats, total_fight_duration, found_healing, found_barrier, config, output):
    print_string = "The following stats are computed over "+str(overall_raid_stats['num_used_fights'])+" out of "+str(len(fights))+" fights.\n"
    myprint(output, print_string, config)
    
    # print total squad stats
    print_string = "Squad overall"
    i = 0
    printed_kills = False
    for stat in config.stats_to_compute:
        if stat == 'dist':
            continue

        # TODO fix commas, fix showing avg boons
        if i == 0:
            print_string += " "
        elif i == len(config.stats_to_compute)-1 and printed_kills:
            print_string += ", and "
        else:
            print_string += ", "
        i += 1
            
        if stat == 'dmg_total':
            print_string += "did "+str(round(overall_squad_stats['dmg_total']))+" total damage"
        elif stat == 'rips':
            print_string += "ripped "+str(round(overall_squad_stats['rips']))+" boons"
        elif stat == 'cleanses':
            print_string += "cleansed "+str(round(overall_squad_stats['cleanses']))+" conditions"
        elif stat in config.squad_buff_ids:
            total_buff_duration = {}
            total_buff_duration["h"] = int(overall_squad_stats[stat]/3600)
            total_buff_duration["m"] = int((overall_squad_stats[stat] - total_buff_duration["h"]*3600)/60)
            total_buff_duration["s"] = int(overall_squad_stats[stat] - total_buff_duration["h"]*3600 - total_buff_duration["m"]*60)    
            
            print_string += "generated "
            if total_buff_duration["h"] > 0:
                print_string += str(total_buff_duration["h"])+"h "
            print_string += str(total_buff_duration["m"])+"m "+str(total_buff_duration["s"])+"s of "+stat
        elif stat == 'heal_total' and found_healing:
            print_string += "healed for "+str(round(overall_squad_stats['heal_total']))
        elif stat == 'barrier' and found_barrier:
            print_string += "generated "+str(round(overall_squad_stats['barrier']))+" barrier"
        elif stat == 'dmg_taken_total':
            print_string += "took "+str(round(overall_squad_stats['dmg_taken_total']))+" damage"
        elif stat == 'deaths':
            print_string += "killed "+str(overall_raid_stats['total_kills'])+" enemies and had "+str(round(overall_squad_stats['deaths']))+" deaths"
            printed_kills = True

    if not printed_kills:
        print_string += ", and killed "+str(overall_raid_stats['total_kills'])+" enemies"
    print_string += " over a total time of "
    if total_fight_duration["h"] > 0:
        print_string += str(total_fight_duration["h"])+"h "
    print_string += str(total_fight_duration["m"])+"m "+str(total_fight_duration["s"])+"s in "+str(overall_raid_stats['num_used_fights'])+" fights.\n"
    print_string += "There were between "+str(overall_raid_stats['min_allies'])+" and "+str(overall_raid_stats['max_allies'])+" allied players involved (average "+str(round(overall_raid_stats['mean_allies'], 1))+" players).\n"
    print_string += "The squad faced between "+str(overall_raid_stats['min_enemies'])+" and "+str(overall_raid_stats['max_enemies'])+" enemy players (average "+str(round(overall_raid_stats['mean_enemies'], 1))+" players).\n"    
        
    myprint(output, print_string, config)
    return total_fight_duration



# print an overview of the fights
# Input:
# fights = list of Fights
# overall_squad_stats = overall stats of the whole squad; output of get_overall_squad_stats
# overall_raid_stats = raid stats like start time, end time, total kills, etc.; output of get_overall_raid_stats
# config = the config used for stats computation
# output = file to write to
def print_fights_overview(fights, overall_squad_stats, overall_raid_stats, config, output):
    stat_len = {}
    print_string = "  #  "+f"{'Date':<10}"+"  "+f"{'Start Time':>10}"+"  "+f"{'End Time':>8}"+"  Duration in s  Skipped  Num. Allies  Num. Enemies  Kills"
    for stat in overall_squad_stats:
        stat_len[stat] = max(len(config.stat_names[stat]), len(str(overall_squad_stats[stat])))
        print_string += "  "+f"{config.stat_names[stat]:>{stat_len[stat]}}"
    myprint(output, print_string, config)
    for i in range(len(fights)):
        fight = fights[i]
        skipped_str = "yes" if fight.skipped else "no"
        date = fight.start_time.split()[0]
        start_time = fight.start_time.split()[1]
        end_time = fight.end_time.split()[1]        
        print_string = f"{i+1:>3}"+"  "+f"{date:<10}"+"  "+f"{start_time:>10}"+"  "+f"{end_time:>8}"+"  "+f"{fight.duration:>13}"+"  "+f"{skipped_str:>7}"+"  "+f"{fight.allies:>11}"+"  "+f"{fight.enemies:>12}"+"  "+f"{fight.kills:>5}"
        for stat in overall_squad_stats:
            print_string += "  "+f"{round(fight.total_stats[stat]):>{stat_len[stat]}}"
        myprint(output, print_string, config)

    print_string = "-" * (3+2+10+2+10+2+8+2+13+2+7+2+11+2+12+sum([stat_len[stat] for stat in overall_squad_stats])+2*len(stat_len)+7)
    myprint(output, print_string, config)
    print_string = f"{overall_raid_stats['num_used_fights']:>3}"+"  "+f"{overall_raid_stats['date']:>7}"+"  "+f"{overall_raid_stats['start_time']:>10}"+"  "+f"{overall_raid_stats['end_time']:>8}"+"  "+f"{overall_raid_stats['used_fights_duration']:>13}"+"  "+f"{overall_raid_stats['num_skipped_fights']:>7}" +"  "+f"{overall_raid_stats['mean_allies']:>11}"+"  "+f"{overall_raid_stats['mean_enemies']:>12}"+"  "+f"{overall_raid_stats['total_kills']:>5}"
    for stat in overall_squad_stats:
        print_string += "  "+f"{round(overall_squad_stats[stat]):>{stat_len[stat]}}"
    print_string += "\n\n"
    myprint(output, print_string, config)


        
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
    write_sorted_top_consistent_or_avg(players, top_consistent_players, config, num_used_fights, stat, StatType.CONSISTENT, output_file)
    return top_consistent_players



# Get and write the people who achieved top x average in stat
# Input:
# players = list of Players
# config = the configuration being used to determine the top consistent players
# num_used_fights = the number of fights that are being used in stat computation
# stat = which stat are we considering
# output_file = the file to write the output to
# Output:
# list of player indices that got a top consistency award
def get_and_write_sorted_average(players, config, num_used_fights, stat, output_file):
    top_average_players = get_top_players(players, config, stat, StatType.AVERAGE)
    write_sorted_top_consistent_or_avg(players, top_average_players, config, num_used_fights, stat, StatType.AVERAGE, output_file)
    return top_average_players



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
    write_sorted_top_percentage(players, top_percentage_players, comparison_percentage, config, num_used_fights, stat, output_file)
    return top_percentage_players, comparison_percentage



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
def write_sorted_top_consistent_or_avg(players, top_consistent_players, config, num_used_fights, stat, consistent_or_avg, output_file):
    max_name_length = max([len(players[i].name) for i in top_consistent_players])
    profession_strings, profession_length = get_professions_and_length(players, top_consistent_players, config)

    if consistent_or_avg == StatType.CONSISTENT:
        if stat == "dist":
            print_string = "Top "+str(config.num_players_considered_top[stat])+" "+config.stat_names[stat]+" consistency awards"
        else:
            print_string = "Top "+config.stat_names[stat]+" consistency awards (Max. "+str(config.num_players_listed[stat])+" places, min. "+str(round(config.portion_of_top_for_consistent*100.))+"% of most consistent)"
            myprint(output_file, print_string, config)
            print_string = "Most times placed in the top "+str(config.num_players_considered_top[stat])+". \nAttendance = number of fights a player was present out of "+str(num_used_fights)+" total fights."
            myprint(output_file, print_string, config)
    elif consistent_or_avg == StatType.AVERAGE:
        if stat == "dist":
            print_string = "Top average "+str(config.num_players_considered_top[stat])+" "+config.stat_names[stat]+" awards"
        else:
            print_string = "Top average "+config.stat_names[stat]+" awards (Max. "+str(config.num_players_listed[stat])+" places)"
            myprint(output_file, print_string, config)
            print_string = "Attendance = number of fights a player was present out of "+str(num_used_fights)+" total fights."
            myprint(output_file, print_string, config)
    print_string = "-------------------------------------------------------------------------------"    
    myprint(output_file, print_string, config)


    # print table header
    print_string = f"    {'Name':<{max_name_length}}" + f"  {'Class':<{profession_length}} "+" Attendance " + " Times Top"
    if stat != "dist":
        print_string += f" {'Total':>9}"
    if stat in config.squad_buff_ids or 'dmg_taken' in stat:
        print_string += f"  {'Average':>7}"
        
    myprint(output_file, print_string, config)    

    
    place = 0
    last_val = 0
    # print table
    for i in range(len(top_consistent_players)):
        player = players[top_consistent_players[i]]
        if player.consistency_stats[stat] != last_val:
            place += 1
        print_string = f"{place:>2}"+f". {player.name:<{max_name_length}} "+f" {profession_strings[i]:<{profession_length}} "+f" {player.num_fights_present:>10} "+f" {round(player.consistency_stats[stat]):>9}"
        if stat != "dist" and stat not in config.squad_buff_ids and 'dmg_taken' not in stat:
            print_string += f" {round(player.total_stats[stat]):>9}"
        if 'dmg_taken' in stat:
            print_string += f" {player.total_stats[stat]:>9}"+f" {player.average_stats[stat]:>8}"
        elif stat in config.buffs_stacking_intensity:
            print_string += f" {player.total_stats[stat]:>8}s"+f" {player.average_stats[stat]:>8}"
        elif stat in config.buffs_stacking_duration:
            print_string += f" {player.total_stats[stat]:>8}s"+f" {player.average_stats[stat]:>7}%"            

        myprint(output_file, print_string, config)
        last_val = player.consistency_stats[stat]
    myprint(output_file, "\n", config)
        
                


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
    
    print_string = "Top overall "+config.stat_names[stat]+" awards (Max. "+str(config.num_players_listed[stat])+" places, min. "+str(round(config.portion_of_top_for_total*100.))+"% of 1st place)"
    myprint(output_file, print_string, config)
    print_string = "Attendance = total duration of fights attended out of "
    if total_fight_duration["h"] > 0:
        print_string += str(total_fight_duration["h"])+"h "
    print_string += str(total_fight_duration["m"])+"m "+str(total_fight_duration["s"])+"s."    
    myprint(output_file, print_string, config)
    print_string = "------------------------------------------------------------------------"
    myprint(output_file, print_string, config)


    # print table header
    print_string = f"    {'Name':<{max_name_length}}" + f"  {'Class':<{profession_length}} "+f" {'Attendance':>11}"+f" {'Total':>9}"
    if stat in config.squad_buff_ids:
        print_string += f"  {'Average':>7}"
    myprint(output_file, print_string, config)    

    place = 0
    last_val = -1
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
        myprint(output_file, print_string, config)
        last_val = player.total_stats[stat]
    myprint(output_file, "\n", config)
    
   

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
def write_sorted_top_percentage(players, top_players, comparison_percentage, config, num_used_fights, stat, output_file):
    # get names that get on the list and their professions
    if len(top_players) <= 0:
        return top_players

    profession_strings, profession_length = get_professions_and_length(players, top_players, config)
    max_name_length = max([len(players[i].name) for i in top_players])
    profession_length = max(profession_length, 5)

    # print table header
    print_string = "Top "+config.stat_names[stat]+" percentage (Minimum percentage = "+f"{comparison_percentage*100:.0f}%)"
    myprint(output_file, print_string, config)
    print_string = "------------------------------------------------------------------------"     
    myprint(output_file, print_string, config)                

    # print table header
    print_string = f"    {'Name':<{max_name_length}}" + f"  {'Class':<{profession_length}} "+f"  Percentage "+f" {'Times Top':>9} " + f" {'Out of':>6}"
    if stat != "dist":
        print_string += f" {'Total':>8}"
    myprint(output_file, print_string, config)    

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
        myprint(output_file, print_string, config)
        last_val = player.portion_top_stats[stat]
    myprint(output_file, "\n", config)



# Write the top x people who achieved top total stat.
# Input:
# players = list of Players
# top_players = list of indices in players that are considered as top
# stat = which stat are we considering
# xls_output_filename = where to write to
def write_stats_xls(players, top_players, stat, xls_output_filename, config):
    book = xlrd.open_workbook(xls_output_filename)
    wb = copy(book)
    sheet1 = wb.add_sheet(stat)
    sheet1.write(0, 0, "Account")
    sheet1.write(0, 1, "Name")
    sheet1.write(0, 2, "Profession")
    sheet1.write(0, 3, "Attendance (number of fights)")
    sheet1.write(0, 4, "Attendance (duration fights)")
    sheet1.write(0, 5, "Times Top")
    sheet1.write(0, 6, "Percentage Top")
    sheet1.write(0, 7, "Total "+stat)
    if stat == 'deaths':
        sheet1.write(0, 8, "Average "+stat+" per min")
    elif stat not in config.self_buff_ids:
        sheet1.write(0, 8, "Average "+stat+" per s")        

    for i in range(len(top_players)):
        player = players[top_players[i]]
        sheet1.write(i+1, 0, player.account)
        sheet1.write(i+1, 1, player.name)
        sheet1.write(i+1, 2, player.profession)
        sheet1.write(i+1, 3, player.num_fights_present)
        sheet1.write(i+1, 4, player.duration_fights_present)
        sheet1.write(i+1, 5, player.consistency_stats[stat])        
        sheet1.write(i+1, 6, round(player.portion_top_stats[stat]*100))
        sheet1.write(i+1, 7, round(player.total_stats[stat]))
        if stat not in config.self_buff_ids:
            sheet1.write(i+1, 8, player.average_stats[stat])

    wb.save(xls_output_filename)


    
# Write xls fight overview
# Input:
# fights = list of Fights as returned by collect_stat_data
# overall_squad_stats = overall stats of the whole squad; output of get_overall_squad_stats
# overall_raid_stats = raid stats like start time, end time, total kills, etc.; output of get_overall_raid_stats
# config = the config to use for stats computation
# xls_output_filename = where to write to
def write_fights_overview_xls(fights, overall_squad_stats, overall_raid_stats, config, xls_output_filename):
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
    sheet1.write(0, 9, "Kills")
    
    for i,stat in enumerate(config.stats_to_compute):
        sheet1.write(0, 10+i, config.stat_names[stat])

    for i,fight in enumerate(fights):
        skipped_str = "yes" if fight.skipped else "no"
        sheet1.write(i+1, 1, i+1)
        sheet1.write(i+1, 2, fight.start_time.split()[0])
        sheet1.write(i+1, 3, fight.start_time.split()[1])
        sheet1.write(i+1, 4, fight.end_time.split()[1])
        sheet1.write(i+1, 5, fight.duration)
        sheet1.write(i+1, 6, skipped_str)
        sheet1.write(i+1, 7, fight.allies)
        sheet1.write(i+1, 8, fight.enemies)
        sheet1.write(i+1, 9, fight.kills)
        for j,stat in enumerate(config.stats_to_compute):
            if stat not in config.squad_buff_ids and stat != "dist":
                sheet1.write(i+1, 10+j, fight.total_stats[stat])
            else:
                sheet1.write(i+1, 10+j, fight.avg_stats[stat])                

    sheet1.write(len(fights)+1, 0, "Sum/Avg. in used fights")
    sheet1.write(len(fights)+1, 1, overall_raid_stats['num_used_fights'])
    sheet1.write(len(fights)+1, 2, overall_raid_stats['date'])
    sheet1.write(len(fights)+1, 3, overall_raid_stats['start_time'])
    sheet1.write(len(fights)+1, 4, overall_raid_stats['end_time'])    
    sheet1.write(len(fights)+1, 5, overall_raid_stats['used_fights_duration'])
    sheet1.write(len(fights)+1, 6, overall_raid_stats['num_skipped_fights'])
    sheet1.write(len(fights)+1, 7, overall_raid_stats['mean_allies'])    
    sheet1.write(len(fights)+1, 8, overall_raid_stats['mean_enemies'])
    sheet1.write(len(fights)+1, 9, overall_raid_stats['total_kills'])
    for i,stat in enumerate(config.stats_to_compute):
        sheet1.write(len(fights)+1, 10+i, overall_squad_stats[stat])

    wb.save(xls_output_filename)



    

# write all stats to a json file
# Input:
# overall_raid_stats = raid stats like start time, end time, total kills, etc.; output of get_overall_raid_stats
# overall_squad_stats = overall stats of the whole squad; output of get_overall_squad_stats
# fights = list of Fights
# config = the config used for stats computation
# output = file to write to

def write_to_json(overall_raid_stats, overall_squad_stats, fights, players, top_total_stat_players, top_average_stat_players, top_consistent_stat_players, top_percentage_stat_players, top_late_players, top_jack_of_all_trades_players, output_file):
    json_dict = {}
    json_dict["overall_raid_stats"] = {key: value for key, value in overall_raid_stats.items()}
    json_dict["overall_squad_stats"] = {key: value for key, value in overall_squad_stats.items()}
    json_dict["fights"] = [jsons.dump(fight) for fight in fights]
    json_dict["players"] = [jsons.dump(player) for player in players]
    json_dict["top_total_players"] =  {key: value for key, value in top_total_stat_players.items()}
    json_dict["top_average_players"] =  {key: value for key, value in top_average_stat_players.items()}
    json_dict["top_consistent_players"] =  {key: value for key, value in top_consistent_stat_players.items()}
    json_dict["top_percentage_players"] =  {key: value for key, value in top_percentage_stat_players.items()}
    json_dict["top_late_players"] =  {key: value for key, value in top_late_players.items()}
    json_dict["top_jack_of_all_trades_players"] =  {key: value for key, value in top_jack_of_all_trades_players.items()}        

    with open(output_file, 'w') as json_file:
        json.dump(json_dict, json_file, indent=4)
