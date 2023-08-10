#    This file contains the configuration for computing the detailed top stats in arcdps logs as parsed by Elite Insights.
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

# Note that if you want to know heal_from_regen, you also have to compute hits_from_regen

# possible log levels: "info", "warning", "debug"
# "info" gives information about the current status of the program
# "warning" gives additional information about things that could have gone wrong, but don't necessarily mean the program can't deal with the data (e.g., some players might not be running the healing addon)
# "debug" gives more detailed information about the state of the program and is usually only needed for debugging
log_level = "info" 

stats_to_compute = ['dmg_total', 'dmg_players', 'dmg_other',
                    'strips', 'cleanses', 'heal_total',
                    'heal_players', 'heal_other', 'dist', 'stab',
                    'prot', 'aegis', 'resist', 'regen', 'heal_from_regen',
                    'hits_from_regen', 'might', 'fury', 'quick',
                    'alac', 'speed', 'barrier',
                    'dmg_taken_total', 'dmg_taken_hp_lost',
                    'dmg_taken_absorbed', 'deaths', 'stripped',
                    'big_boomer', 'explosive_temper', 'explosive_entrance',
                    'med_kit']

# How many players will be listed who achieved top stats most often for each stat?
num_players_listed_default = 1000
#num_players_listed = {}

# How many players are considered to be "top" in each fight for each stat?
num_players_considered_top_default = 5
num_players_considered_top = {'strips': 3, 'stab': 3, 'prot': 3, 'aegis': 3, 'resist': 3, 'regen': 3, 'heal_from_regen': 3,
                              'hits_from_regen': 3, 'might': 3, 'fury': 3, 'quick': 3, 'alac': 3, 'speed': 3, 'cleanses': 3,
                              'heal': 3, 'barrier': 3, 'deaths': 1, 'big_boomer': 3, 'explosive_temper': 3, 'explosive_entrance': 3,
                              'med_kit': 3}


# duration_for_averages_default = 'in_combat'
duration_for_averages_default = 'total'
duration_for_averages = {'dist': 'not_running_back', 'dmg_total': 'total'}

# For what portion of all fights does a player need to be there to be considered for "consistency percentage" awards?
attendance_percentage_for_percentage = 50
# For what portion of all fights does a player need to be there to be considered for "top average" awards? 
attendance_percentage_for_average = 33

# What portion of the top total player stat does someone need to reach to be considered for total awards?
percentage_of_top_for_consistent = 0
# What portion of the total stat of the top consistent player does someone need to reach to be considered for consistency awards?
percentage_of_top_for_total = 0
# What portion of the percentage the top consistent player reached top does someone need to reach to be considered for percentage awards?
percentage_of_top_for_percentage = 0

# minimum number of allied players to consider a fight in the stats
min_allied_players = 10
# minimum duration of a fight to be considered in the stats
min_fight_duration = 30
# minimum number of enemies to consider a fight in the stats
min_enemy_players = 10

# choose which files to write as results and whether to write results to console. Options are 'console', 'txt', 'xls' and 'json'.
files_to_write = ['console', 'txt', 'xls', 'json']
#files_to_write = ['txt', 'xls', 'json']

# names as which each specialization will show up in the stats
profession_abbreviations = {}
profession_abbreviations["Guardian"] = "Guardian"
profession_abbreviations["Dragonhunter"] = "Dragonhunter"
profession_abbreviations["Firebrand"] = "Firebrand"
profession_abbreviations["Willbender"] = "Willbender"

profession_abbreviations["Revenant"] = "Revenant"
profession_abbreviations["Herald"] = "Herald"
profession_abbreviations["Renegade"] = "Renegade"
profession_abbreviations["Vindicator"] = "Vindicator"    

profession_abbreviations["Warrior"] = "Warrior"
profession_abbreviations["Berserker"] = "Berserker"
profession_abbreviations["Spellbreaker"] = "Spellbreaker"
profession_abbreviations["Bladesworn"] = "Bladesworn"

profession_abbreviations["Engineer"] = "Engineer"
profession_abbreviations["Scrapper"] = "Scrapper"
profession_abbreviations["Holosmith"] = "Holosmith"
profession_abbreviations["Mechanist"] = "Mechanist"    

profession_abbreviations["Ranger"] = "Ranger"
profession_abbreviations["Druid"] = "Druid"
profession_abbreviations["Soulbeast"] = "Soulbeast"
profession_abbreviations["Untamed"] = "Untamed"    

profession_abbreviations["Thief"] = "Thief"
profession_abbreviations["Daredevil"] = "Daredevil"
profession_abbreviations["Deadeye"] = "Deadeye"
profession_abbreviations["Specter"] = "Specter"

profession_abbreviations["Elementalist"] = "Elementalist"
profession_abbreviations["Tempest"] = "Tempest"
profession_abbreviations["Weaver"] = "Weaver"
profession_abbreviations["Catalyst"] = "Catalyst"

profession_abbreviations["Mesmer"] = "Mesmer"
profession_abbreviations["Chronomancer"] = "Chronomancer"
profession_abbreviations["Mirage"] = "Mirage"
profession_abbreviations["Virtuoso"] = "Virtuoso"
    
profession_abbreviations["Necromancer"] = "Necromancer"
profession_abbreviations["Reaper"] = "Reaper"
profession_abbreviations["Scourge"] = "Scourge"
profession_abbreviations["Harbinger"] = "Harbinger"

# name each stat will be written as
stat_names = {}
stat_names["dmg_total"] = "Total Damage"
stat_names["dmg_players"] = "Player Damage"
stat_names["dmg_other"] = "Other Damage"
stat_names["strips"] = "Boon Strips"
stat_names["stab"] = "Stability Output"
stat_names["prot"] = "Protection Output"
stat_names["aegis"] = "Aegis Output"
stat_names["resist"] = "Resistance Output"
stat_names["regen"] = "Regeneration Output"
stat_names["heal_from_regen"] = "Healing from Regeneration"
stat_names["hits_from_regen"] = "Hits with Regeneration"
stat_names["might"] = "Might Output"
stat_names["fury"] = "Fury Output"
stat_names["alac"] = "Alacrity Output"
stat_names["quick"] = "Quickness Output"
stat_names["speed"] = "Superspeed Output"
stat_names["cleanses"] = "Condition Cleanses"
stat_names["heal_total"] = "Total Healing"
stat_names["heal_players"] = "Player Healing"
stat_names["heal_other"] = "Other Healing"
stat_names["barrier"] = "Barrier"
stat_names["dist"] = "Distance to Tag"
stat_names["dmg_taken_total"] = "Total Damage Taken"
stat_names["dmg_taken_hp_lost"] = "HP lost"
stat_names["dmg_taken_absorbed"] = "Damage absorbed"
stat_names["deaths"] = "Deaths"
stat_names["stripped"] = "Incoming Strips"
stat_names["big_boomer"] = "Big Boomer"
stat_names["explosive_temper"] = "Explosive Temper"
stat_names["explosive_entrance"] = "Explosive Entrance"
stat_names["med_kit"] = "Med Kit"
