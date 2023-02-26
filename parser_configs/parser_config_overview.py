#    This file contains the configuration for computing the overview of top stats in arcdps logs as parsed by Elite Insights.
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

stats_to_compute = ['dmg', 'rips', 'stab', 'cleanses', 'heal', 'barrier', 'dist', 'deaths']

# How many players will be listed who achieved top stats most often for each stat?
num_players_listed = {'dmg': 5, 'rips': 3, 'stab': 3, 'cleanses': 3, 'heal': 3, 'barrier': 3, 'dist': 5, 'deaths': 5}
# How many players are considered to be "top" in each fight for each stat?
num_players_considered_top = {'dmg': 5, 'rips': 3, 'stab': 3, 'cleanses': 3, 'heal': 3, 'barrier': 3, 'dist': 5, 'deaths': 1}


# For what portion of all fights does a player need to be there to be considered for "consistency percentage" awards?
attendance_percentage_for_percentage = 50
# For what portion of all fights does a player need to be there to be considered for "late but great" awards?
attendance_percentage_for_late = 50
# For what portion of all fights does a player need to be there to be considered for "jack of all trades" awards? 
attendance_percentage_for_buildswap = 30
# For what portion of all fights does a player need to be there to be considered for "top average" awards? 
attendance_percentage_for_average = 50

# What portion of the top total player stat does someone need to reach to be considered for total awards?
percentage_of_top_for_consistent = 50
# What portion of the total stat of the top consistent player does someone need to reach to be considered for consistency awards?
percentage_of_top_for_total = 50
# What portion of the percentage the top consistent player reached top does someone need to reach to be considered for percentage awards?
percentage_of_top_for_percentage = 50
# What portion of the percentage the top consistent player reached top does someone need to reach to be considered for late but great awards?
percentage_of_top_for_late = 100
# What portion of the percentage the top consistent player reached top does someone need to reach to be considered for jack of all trades awards?
percentage_of_top_for_buildswap = 100

# minimum number of allied players to consider a fight in the stats
min_allied_players = 10
# minimum duration of a fight to be considered in the stats
min_fight_duration = 30
# minimum number of enemies to consider a fight in the stats
min_enemy_players = 10

# choose which files to write as results and whether to write results to console. Options are 'console', 'txt', 'xls' and 'json'.
files_to_write = ['console', 'txt', 'json', 'xls']

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
stat_names["dmg"] = "Damage"
stat_names["rips"] = "Boon Strips"
stat_names["stab"] = "Stability Output"
stat_names["cleanses"] = "Condition Cleanses"
stat_names["heal"] = "Healing"
stat_names["barrier"] = "Barrier"
stat_names["dist"] = "Distance to Tag"
stat_names["deaths"] = "Deaths"
