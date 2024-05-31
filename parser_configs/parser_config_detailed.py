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
                    'condi_dmg_total', 'condi_dmg_players', 'condi_dmg_other',
                    'power_dmg_total', 'power_dmg_players', 'power_dmg_other',
                    'spike_dmg', 'kills', 'downs', 'down_contrib',
                    'strips', 'interrupts', 'might', 'fury',
                    'heal_total', 'heal_players', 'heal_other',
                    'barrier', 'cleanses', 'stab', 'prot', 'aegis',
                    'resist', 'resolution', 'vigor', 'regen',
                    'heal_from_regen', 'hits_from_regen',
                    'dist', 'quick', 'alac', 'swift', 'speed',
                    'dmg_taken_total', 'dmg_taken_hp_lost',
                    'dmg_taken_absorbed', 'condi_dmg_taken_total', 'power_dmg_taken_total',
                    'deaths', 'downstate', 'stripped',
                    'dodges', 'blocks', 'stealth',
                    'chaos_aura', 'fire_aura', 'dark_aura', 'frost_aura',
                    'light_aura', 'magnetic_aura', 'shocking_aura',
                    'big_boomer', 'explosive_temper', 'explosive_entrance',
                    'med_kit']

# How many players will be listed who achieved top stats most often for each stat?
num_players_listed_default = 1000
#num_players_listed = {}

# How many players are considered to be "top" in each fight for each stat?
num_players_considered_top_default = 5
num_players_considered_top = {'strips': 3, 'stab': 3, 'prot': 3, 'aegis': 3, 'resist': 3, 'regen': 3, 'heal_from_regen': 3,
                              'hits_from_regen': 3, 'might': 3, 'fury': 3, 'quick': 3, 'alac': 3, 'speed': 3, 'cleanses': 3,
                              'heal': 3, 'barrier': 3, 'deaths': 1}

relevant_classes_for_stat = {
    'dmg_total': ["Dragonhunter", "Willbender", "Herald", "Vindicator", "Berserker", "Holosmith", "Weaver", "Catalyst", "Virtuoso", "Reaper"],
    'dmg_players': ["Dragonhunter", "Willbender", "Herald", "Vindicator", "Berserker", "Holosmith", "Weaver", "Catalyst", "Virtuoso", "Reaper"],
    'dmg_other': ["Dragonhunter", "Willbender", "Herald", "Vindicator", "Berserker", "Holosmith", "Weaver", "Catalyst", "Virtuoso", "Reaper"],
    'condi_dmg_total': [],
    'condi_dmg_players': [],
    'condi_dmg_other': [],
    'power_dmg_total': [],
    'power_dmg_players': [],
    'power_dmg_other': [],
    'spike_dmg': ["Dragonhunter", "Willbender", "Herald", "Vindicator", "Berserker", "Holosmith", "Weaver", "Catalyst", "Virtuoso", "Reaper"],
    'kills': ["Dragonhunter", "Willbender", "Herald", "Vindicator", "Berserker", "Holosmith", "Weaver", "Catalyst", "Virtuoso", "Reaper"],
    'downs': ["Dragonhunter", "Willbender", "Herald", "Vindicator", "Berserker", "Holosmith", "Weaver", "Catalyst", "Virtuoso", "Reaper"],
    'down_contrib': ["Dragonhunter", "Willbender", "Herald", "Vindicator", "Berserker", "Holosmith", "Weaver", "Catalyst", "Virtuoso", "Reaper"],
    'strips': ["Chronomancer", "Virtuoso", "Reaper", "Scourge"],
    'interrupts': ["Firebrand", "Chronomancer"],
    'cleanses': ["Vindicator", "Scrapper", "Druid", "Tempest"],
    'heal_total': ["Vindicator", "Scrapper", "Druid", "Tempest"],
    'heal_players': ["Vindicator", "Scrapper", "Druid", "Tempest"],
    'heal_other': ["Vindicator", "Scrapper", "Druid", "Tempest"],
    'dist': ["Guardian", "Dragonhunter", "Firebrand", "Willbender", "Revenant", "Renegade", "Herald", "Vindicator", "Warrior", "Berserker", "Spellbreaker", "Bladesworn",  "Engineer", "Scrapper", "Holosmith", "Mechanist",  "Ranger", "Druid", "Soulbeast", "Untamed",  "Thief", "Daredevil", "Deadeye", "Specter",  "Elementalist", "Tempest",  "Weaver", "Catalyst",  "Mesmer", "Chronomancer", "Mirage", "Virtuoso",  "Necromancer", "Reaper", "Scourge", "Harbinger"],
    'stab': ["Firebrand", "Vindicator"],
    'prot': ["Firebrand", "Scrapper", "Druid", "Tempest"],
    'aegis': ["Firebrand"],
    'resist': ["Firebrand"],
    'regen': ["Vindicator", "Scrapper", "Druid", "Tempest"],
    'heal_from_regen': ["Vindicator", "Scrapper", "Druid", "Tempest"],
    'hits_from_regen': ["Vindicator", "Scrapper", "Druid", "Tempest"],
    'might': ["Firebrand", "Scrapper", "Tempest",  "Weaver", "Catalyst"],
    'fury': [],
    'quick': ["Firebrand", "Chronomancer", "Virtuoso"],
    'alac': ["Chronomancer", "Virtuoso", "Scourge"],
    'resolution': [],
    'swift': [],
    'vigor': [],
    'speed': ["Scrapper", "Druid", "Tempest",  "Weaver", "Catalyst"],
    'barrier': ["Scourge"],
    'dmg_taken_total': ["Guardian", "Dragonhunter", "Firebrand", "Willbender", "Revenant", "Renegade", "Herald", "Vindicator", "Warrior", "Berserker", "Spellbreaker", "Bladesworn",  "Engineer", "Scrapper", "Holosmith", "Mechanist",  "Ranger", "Druid", "Soulbeast", "Untamed",  "Thief", "Daredevil", "Deadeye", "Specter",  "Elementalist", "Tempest",  "Weaver", "Catalyst",  "Mesmer", "Chronomancer", "Mirage", "Virtuoso",  "Necromancer", "Reaper", "Scourge", "Harbinger"],
    'dmg_taken_hp_lost': ["Guardian", "Dragonhunter", "Firebrand", "Willbender", "Revenant", "Renegade", "Herald", "Vindicator", "Warrior", "Berserker", "Spellbreaker", "Bladesworn",  "Engineer", "Scrapper", "Holosmith", "Mechanist",  "Ranger", "Druid", "Soulbeast", "Untamed",  "Thief", "Daredevil", "Deadeye", "Specter",  "Elementalist", "Tempest",  "Weaver", "Catalyst",  "Mesmer", "Chronomancer", "Mirage", "Virtuoso",  "Necromancer", "Reaper", "Scourge", "Harbinger"],
    'dmg_taken_absorbed': ["Guardian", "Dragonhunter", "Firebrand", "Willbender", "Revenant", "Renegade", "Herald", "Vindicator", "Warrior", "Berserker", "Spellbreaker", "Bladesworn",  "Engineer", "Scrapper", "Holosmith", "Mechanist",  "Ranger", "Druid", "Soulbeast", "Untamed",  "Thief", "Daredevil", "Deadeye", "Specter",  "Elementalist", "Tempest",  "Weaver", "Catalyst",  "Mesmer", "Chronomancer", "Mirage", "Virtuoso",  "Necromancer", "Reaper", "Scourge", "Harbinger"],
    'condi_dmg_taken_total': ["Guardian", "Dragonhunter", "Firebrand", "Willbender", "Revenant", "Renegade", "Herald", "Vindicator", "Warrior", "Berserker", "Spellbreaker", "Bladesworn",  "Engineer", "Scrapper", "Holosmith", "Mechanist",  "Ranger", "Druid", "Soulbeast", "Untamed",  "Thief", "Daredevil", "Deadeye", "Specter",  "Elementalist", "Tempest",  "Weaver", "Catalyst",  "Mesmer", "Chronomancer", "Mirage", "Virtuoso",  "Necromancer", "Reaper", "Scourge", "Harbinger"],
    'power_dmg_taken_total': ["Guardian", "Dragonhunter", "Firebrand", "Willbender", "Revenant", "Renegade", "Herald", "Vindicator", "Warrior", "Berserker", "Spellbreaker", "Bladesworn",  "Engineer", "Scrapper", "Holosmith", "Mechanist",  "Ranger", "Druid", "Soulbeast", "Untamed",  "Thief", "Daredevil", "Deadeye", "Specter",  "Elementalist", "Tempest",  "Weaver", "Catalyst",  "Mesmer", "Chronomancer", "Mirage", "Virtuoso",  "Necromancer", "Reaper", "Scourge", "Harbinger"],
    'deaths': ["Guardian", "Dragonhunter", "Firebrand", "Willbender", "Revenant", "Renegade", "Herald", "Vindicator", "Warrior", "Berserker", "Spellbreaker", "Bladesworn",  "Engineer", "Scrapper", "Holosmith", "Mechanist",  "Ranger", "Druid", "Soulbeast", "Untamed",  "Thief", "Daredevil", "Deadeye", "Specter",  "Elementalist", "Tempest",  "Weaver", "Catalyst",  "Mesmer", "Chronomancer", "Mirage", "Virtuoso",  "Necromancer", "Reaper", "Scourge", "Harbinger"],
    'downstate': [],
    'stripped': ["Guardian", "Dragonhunter", "Firebrand", "Willbender", "Revenant", "Renegade", "Herald", "Vindicator", "Warrior", "Berserker", "Spellbreaker", "Bladesworn",  "Engineer", "Scrapper", "Holosmith", "Mechanist",  "Ranger", "Druid", "Soulbeast", "Untamed",  "Thief", "Daredevil", "Deadeye", "Specter",  "Elementalist", "Tempest",  "Weaver", "Catalyst",  "Mesmer", "Chronomancer", "Mirage", "Virtuoso",  "Necromancer", "Reaper", "Scourge", "Harbinger"],
    'dodges': [],
    'blocks': [],
    'stealth': [],
    'big_boomer': ["Engineer", "Scrapper", "Holosmith", "Mechanist"],
    'explosive_temper': ["Engineer", "Scrapper", "Holosmith", "Mechanist"],
    'explosive_entrance': ["Engineer", "Scrapper", "Holosmith", "Mechanist"],
    'med_kit': ["Engineer", "Scrapper", "Holosmith", "Mechanist"],
    'chaos_aura': [],
    'fire_aura': [],
    'frost_aura': [],
    'light_aura': [],
    'magnetic_aura': [],
    'shocking_aura': [],
    'dark_aura': []
}

# duration_for_averages_default = 'in_combat'
# the time used for average uptime computation can not be configured here. It is hardcoded to the total duration of the fight.
duration_for_averages_default = 'total'
duration_for_averages = {'dist': 'not_running_back'}

# Default column(s) to sort the xls by. valid values are: "account", "name", "profession", "attendance_num", "attendance_duration", "times_top", "percentage_top", "total", and "avg".
default_sort_xls_by = ['total', 'avg']
# Individual column(s) per stat to sort the xls by
sort_xls_by = {'dist': ['avg'], 'big_boomer': ['total'], 'explosive_temper': ['total'], 'explosive_entrance': ['total'], 'med_kit': ['total'],}

# For what portion of all fights does a player need to be there to be considered for "consistency percentage" awards?
attendance_percentage_for_percentage = 50
# For what portion of all fights does a player need to be there to be considered for "top average" awards? 
attendance_percentage_for_average = 25

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
files_to_write = ['xls', 'json']

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

# name each stat will be written as in the .xls file
stat_names = {}
stat_names["dmg_total"] = "Total Damage"
stat_names["dmg_players"] = "Player Damage"
stat_names["dmg_other"] = "Other Damage"
stat_names["condi_dmg_total"] = "Total Condition Damage"
stat_names["condi_dmg_players"] = "Player Condition Damage"
stat_names["condi_dmg_other"] = "Other Condition Damage"
stat_names["power_dmg_total"] = "Total Power Damage"
stat_names["power_dmg_players"] = "Player Power Damage"
stat_names["power_dmg_other"] = "Other Power Damage"
stat_names["spike_dmg"] = "Spike Damage"
stat_names["kills"] = "Kills"
stat_names["downs"] = "Downs"
stat_names["down_contrib"] = "Down Contribution"
stat_names["strips"] = "Boon Strips"
stat_names["interrupts"] = "Interrupts"
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
stat_names["condi_dmg_taken_total"] = "Total Condition Damage Taken"
stat_names["power_dmg_taken_total"] = "Total Power Damage Taken"
stat_names["deaths"] = "Deaths"
stat_names["downstate"] = "Player Downstate"
stat_names["stripped"] = "Incoming Strips"
stat_names["dodges"] = "Dodges"
stat_names["blocks"] = "Blocks"
stat_names["stealth"] = "Stealth Output"
stat_names["big_boomer"] = "Big Boomer"
stat_names["explosive_temper"] = "Explosive Temper"
stat_names["explosive_entrance"] = "Explosive Entrance"
stat_names["med_kit"] = "Med Kit"
stat_names["resolution"] = "Resolution Output"
stat_names["swift"] = "Swiftness Output"
stat_names["vigor"] = "Vigor Output"
stat_names["chaos_aura"] = "Chaos Aura Uptime"
stat_names["fire_aura"] = "Fire Aura Uptime"
stat_names["frost_aura"] = "Frost Aura Uptime"
stat_names["light_aura"] = "Light Aura Uptime"
stat_names["magnetic_aura"] = "Magnetic Aura Uptime"
stat_names["shocking_aura"] = "Shocking Aura Uptime"
stat_names["dark_aura"] = "Dark Aura Uptime"

# description for each stat to be written as in the .xls file
stat_descriptions = {}
stat_descriptions["dmg_total"] = "Total Damage dealt to everything"
stat_descriptions["dmg_players"] = "Damage dealt to enemy players"
stat_descriptions["dmg_other"] = "Damage dealt to siege, gates, npcs, pets,..."
stat_descriptions["condi_dmg_total"] = "Total Condition Damage dealt to everything"
stat_descriptions["condi_dmg_players"] = "Condition Damage dealt to players"
stat_descriptions["condi_dmg_other"] = "Condition Damage dealt to siege, gates, npcs, pets,..."
stat_descriptions["power_dmg_total"] = "Total Power Damage dealt to everything"
stat_descriptions["power_dmg_players"] = "Power Damage dealt to players"
stat_descriptions["power_dmg_other"] = "Power Damage dealt to siege, gates, npcs, pets,..."
stat_descriptions["spike_dmg"] = "Spike Damage (Maximum damage dealt to players within 1s)"
stat_descriptions["kills"] = "Number of killing hits"
stat_descriptions["downs"] = "Number of downing hits"
stat_descriptions["down_contrib"] = "Damage done to downstates"
stat_descriptions["strips"] = "Boon Strips"
stat_descriptions["interrupts"] = "Number of hits that interrupted an enemy"
stat_descriptions["stab"] = "Stability Output (Squad Generation, excluding self)"
stat_descriptions["prot"] = "Protection Output (Squad Generation, excluding self)"
stat_descriptions["aegis"] = "Aegis Output (Squad Generation, excluding self)"
stat_descriptions["resist"] = "Resistance Output (Squad Generation, excluding self)"
stat_descriptions["regen"] = "Regeneration Output"
stat_descriptions["heal_from_regen"] = "Healing from Regeneration"
stat_descriptions["hits_from_regen"] = "Regeneration ticks"
stat_descriptions["might"] = "Might Output (Squad Generation, excluding self)"
stat_descriptions["fury"] = "Fury Output (Squad Generation, excluding self)"
stat_descriptions["alac"] = "Alacrity Output (Squad Generation, excluding self)"
stat_descriptions["quick"] = "Quickness Output (Squad Generation, excluding self)"
stat_descriptions["speed"] = "Superspeed Output (Squad Generation, excluding self)"
stat_descriptions["cleanses"] = "Condition Cleanses"
stat_descriptions["heal_total"] = "Total Healing (only shown if player has the healing addon installed)"
stat_descriptions["heal_players"] = "Healing on players (only shown if player has the healing addon installed)"
stat_descriptions["heal_other"] = "Healing on pets, npcs, ... (only shown if player has the healing addon installed)"
stat_descriptions["barrier"] = "Barrier(only shown if player has the healing addon installed)"
stat_descriptions["dist"] = "Distance to Tag"
stat_descriptions["dmg_taken_total"] = "Total Damage Taken (includes damage absorbed by barrier)"
stat_descriptions["dmg_taken_hp_lost"] = "HP lost"
stat_descriptions["dmg_taken_absorbed"] = "Damage absorbed by barrier"
stat_descriptions["condi_dmg_taken_total"] = "Total Condition Damage Taken (includes damage absorbed by barrier)"
stat_descriptions["power_dmg_taken_total"] = "Total Power Damage Taken (includes damage absorbed by barrier)"
stat_descriptions["deaths"] = "Deaths"
stat_descriptions["downstate"] = "Number of times a player went downstate"
stat_descriptions["stripped"] = "Incoming Strips"
stat_descriptions["dodges"] = "Dodges"
stat_descriptions["blocks"] = "Number of Blocked Enemy Attacks"
stat_descriptions["stealth"] = "Stealth Output (Squad Generation, excluding self)"
stat_descriptions["big_boomer"] = "Big Boomer"
stat_descriptions["explosive_temper"] = "Explosive Temper"
stat_descriptions["explosive_entrance"] = "Explosive Entrance"
stat_descriptions["med_kit"] = "Med Kit"
stat_descriptions["resolution"] = "Resolution Output (Squad Generation, excluding self)"
stat_descriptions["swift"] = "Swiftness Output (Squad Generation, excluding self)"
stat_descriptions["vigor"] = "Vigor Output (Squad Generation, excluding self)"
stat_descriptions["chaos_aura"] = "Chaos Aura Uptime"
stat_descriptions["fire_aura"] = "Fire Aura Uptime"
stat_descriptions["frost_aura"] = "Frost Aura Uptime"
stat_descriptions["light_aura"] = "Light Aura Uptime"
stat_descriptions["magnetic_aura"] = "Magnetic Aura Uptime"
stat_descriptions["shocking_aura"] = "Shocking Aura Uptime"
stat_descriptions["dark_aura"] = "Dark Aura Uptime"

# TODO move this somewhere else as "fixed"?
xls_column_names = {}
xls_column_names['account'] = "Account"
xls_column_names['name'] = "Name"
xls_column_names['profession'] = "Profession"
xls_column_names['attendance_num'] = "Attendance (number of fights)"
xls_column_names['attendance_duration'] = "Attendance (duration present)"
