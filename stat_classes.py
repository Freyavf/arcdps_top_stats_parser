#!/usr/bin/env python3

from dataclasses import dataclass,field
from enum import Enum

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
    attendance_percentage: float = 0.   # the percentage of fight duration the player was involved in out of all fights # TODO
    # the duration of all fights the player was involved in; including
    # - 'total' (total duration of the fights a player was involved in),
    # - 'active' (total duration a player was active (alive or down)),
    # - 'in_combat' (total duration a player was in combat (from each start of taking/dealing dmg until death, also multiple times in one fight))
    # - 'not_running_back' (time from beginning of each fight until down of either player or tag leading to death; 0 if player was running back at the beginning of the fight)
    duration_present: dict = field(default_factory=dict) 
    # the sum of duration present * (squad members -1) of all fights the player was involved in;
    # analogue to duration_present (see above)
    normalization_time_allies: dict = field(default_factory=dict)  
    swapped_build: bool = False         # a different player character or specialization with this account name was in some of the fights

    # fields for all stats defined in config
    consistency_stats: dict = field(default_factory=dict)     # how many times did this player get into top for each stat?
    total_stats: dict = field(default_factory=dict)           # what's the total value for this player for each stat?
    average_stats: dict = field(default_factory=dict)         # what's the average stat per second for this player? (exception: deaths are per minute)
    portion_top_stats: dict = field(default_factory=dict)     # what percentage of fights did this player get into top for each stat, in relation to the number of fights they were involved in?
                                                              # = consistency_stats/num_fights_present
    stats_per_fight: list = field(default_factory=list)       # what's the value of each stat for this player in each fight?

    def initialize(self, config):
        self.duration_present = {'total': 0, 'active': 0, 'in_combat': 0, 'not_running_back': 0}
        self.normalization_time_allies = {'total': 0, 'active': 0, 'in_combat': 0, 'not_running_back': 0}
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
    tag_positions_until_death: list = field(default_factory=list) # position of the commander until he died (empty if no com was found or more than one com was found)
    polling_rate: int = 150                                       # polling rate of position data as read from json (could get overwritten)
    inch_to_pixel: float = 0.009                                  # inch to pixel conversion value; different for some maps -> might get overwritten
    

    
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

    empty_stats: dict = field(default_factory=dict)                 # stat values to initialize player stats per fight
    stats_to_compute: list = field(default_factory=list)            # all stats that should be computed
    duration_for_averages: dict = field(default_factory=dict)       # which duration type should be used to compute the avg for each stat? (one of 'total', 'active', 'in_combat', 'not_running_back')

    squad_buff_ids: dict = field(default_factory=dict)              # dict of squad buff name to buff id as read from buffMap
    self_buff_ids: dict = field(default_factory=dict)               # dict of self buff name to buff id as read from buffMap
    buffs_stacking_duration: list = field(default_factory=list)     # list of squad_buff names stacking duration
    buffs_stacking_intensity: list = field(default_factory=list)    # list of squad_buff names stacking intensity
    squad_buff_abbrev: dict = field(default_factory=dict)           # abbreviations of squad buff names
    self_buff_abbrev: dict = field(default_factory=dict)            # abbreviations of self buff names

    errors: list = field(default_factory=list)
    log_level: str = "info"
    

    
# fills a Config with the given input    
def fill_config(config_input, log):
    config = Config()
    if hasattr(config_input, "num_players_listed"):
        config.num_players_listed = config_input.num_players_listed
    else:
        config.num_players_listed = dict()
    for stat in config_input.stats_to_compute:
        if stat not in config.num_players_listed:
            config.num_players_listed[stat] = config_input.num_players_listed_default

    if hasattr(config_input, "num_players_considered_top"):
        config.num_players_considered_top = config_input.num_players_considered_top
    else:
        config.num_players_considered_top = dict()
    for stat in config_input.stats_to_compute:
        if stat not in config.num_players_considered_top:
            config.num_players_considered_top[stat] = config_input.num_players_considered_top_default

    if hasattr(config_input, "duration_for_averages"):
        config.duration_for_averages = config_input.duration_for_averages
    else:
        config.duration_for_averages = dict()
    for stat in config_input.stats_to_compute:
        if stat not in config.duration_for_averages:
            config.duration_for_averages[stat] = config_input.duration_for_averages_default

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
    config.empty_stats['duration_present'] = {'total': 0, 'active': 0, 'in_combat': 0, 'not_running_back': 0}
    config.empty_stats['present_in_fight'] = False

    config.squad_buff_abbrev["Stability"] = 'stab'
    config.squad_buff_abbrev["Protection"] = 'prot'
    config.squad_buff_abbrev["Aegis"] = 'aegis'
    config.squad_buff_abbrev["Resistance"] = 'resist'
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

    if config_input.log_level == "debug" or config_input.log_level == "warning" or config_input.log_level == "info":
        config.log_level = config_input.log_level
    else:
        print("log level "+config_input.log_level+" is not available. Using \"info\" instead.")
        config.log_level = "info"
    
    return config
