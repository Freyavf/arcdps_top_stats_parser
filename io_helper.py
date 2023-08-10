#!/usr/bin/env python3

from stat_classes import *
import xlrd
from xlutils.copy import copy
import jsons
import json

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



# prints output_string to the console and the output_file, with a linebreak at the end
def myprint(output_file, output_string, log_level, config = None):
    if config != None:
        if log_level == "warning" and config.log_level == "info":
            return
        if log_level == "debug" and config.log_level != "debug":
            return
        
    if config == None:
        print(output_string)
        output_file.write(output_string+"\n")


# Write the top x people who achieved top total stat.
# Input:
# players = list of Players
# top_players = list of indices in players that are considered as top
# stat = which stat are we considering
# xls_output_filename = where to write to
def write_stats_xls(players, top_players, stat, xls_output_filename, config):
    book = xlrd.open_workbook(xls_output_filename)
    wb = copy(book)
    sheet1 = wb.add_sheet(config.stat_names[stat])
    sheet1.write(0, 0, "Account")
    sheet1.write(0, 1, "Name")
    sheet1.write(0, 2, "Profession")
    sheet1.write(0, 3, "Attendance (number of fights)")
    sheet1.write(0, 4, "Attendance (duration present)")
    sheet1.write(0, 5, "Times Top "+str(config.num_players_considered_top[stat]))
    sheet1.write(0, 6, "Percentage Top"+str(config.num_players_considered_top[stat]))
    sheet1.write(0, 7, "Total "+stat)
    if stat == 'deaths':
        sheet1.write(0, 8, "Average "+stat+" per min"+config.duration_for_averages[stat])
    elif stat not in config.self_buff_ids:
        sheet1.write(0, 8, "Average "+stat+" per s "+config.duration_for_averages[stat])

    for i in range(len(top_players)):
        player = players[top_players[i]]
        sheet1.write(i+1, 0, player.account)
        sheet1.write(i+1, 1, player.name)
        sheet1.write(i+1, 2, player.profession)
        sheet1.write(i+1, 3, player.num_fights_present)
        sheet1.write(i+1, 4, player.duration_present[config.duration_for_averages[stat]])
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
        sheet1.write(len(fights)+1, 10+i, overall_squad_stats['total'][stat])

    wb.save(xls_output_filename)



# write all stats to a json file
# Input:
# overall_raid_stats = raid stats like start time, end time, total kills, etc.; output of get_overall_raid_stats
# overall_squad_stats = overall stats of the whole squad; output of get_overall_squad_stats
# fights = list of Fights
# config = the config used for stats computation
# output = file to write to

def write_to_json(overall_raid_stats, overall_squad_stats, fights, players, top_total_stat_players, top_average_stat_players, top_consistent_stat_players, top_percentage_stat_players, output_file):
    json_dict = {}
    json_dict["overall_raid_stats"] = {key: value for key, value in overall_raid_stats.items()}
    json_dict["overall_squad_stats"] = {key: value for key, value in overall_squad_stats.items()}
    json_dict["fights"] = [jsons.dump(fight) for fight in fights]
    json_dict["players"] = [jsons.dump(player) for player in players]
    json_dict["top_total_players"] =  {key: value for key, value in top_total_stat_players.items()}
    json_dict["top_average_players"] =  {key: value for key, value in top_average_stat_players.items()}
    json_dict["top_consistent_players"] =  {key: value for key, value in top_consistent_stat_players.items()}
    json_dict["top_percentage_players"] =  {key: value for key, value in top_percentage_stat_players.items()}

    with open(output_file, 'w') as json_file:
        json.dump(json_dict, json_file, indent=4)

