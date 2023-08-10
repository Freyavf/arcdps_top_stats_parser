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
        
    if config == None or "console" in config.files_to_write:
        print(output_string)
    if config == None or "txt" in config.files_to_write:
        output_file.write(output_string+"\n")



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
    myprint(output, print_string, "info", config)
    
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
        elif stat == 'strips':
            print_string += "ripped "+str(round(overall_squad_stats['strips']))+" boons"
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
        
    myprint(output, print_string, "info", config)
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
    myprint(output, print_string, "info", config)
    for i in range(len(fights)):
        fight = fights[i]
        skipped_str = "yes" if fight.skipped else "no"
        date = fight.start_time.split()[0]
        start_time = fight.start_time.split()[1]
        end_time = fight.end_time.split()[1]        
        print_string = f"{i+1:>3}"+"  "+f"{date:<10}"+"  "+f"{start_time:>10}"+"  "+f"{end_time:>8}"+"  "+f"{fight.duration:>13}"+"  "+f"{skipped_str:>7}"+"  "+f"{fight.allies:>11}"+"  "+f"{fight.enemies:>12}"+"  "+f"{fight.kills:>5}"
        for stat in overall_squad_stats:
            print_string += "  "+f"{round(fight.total_stats[stat]):>{stat_len[stat]}}"
        myprint(output, print_string, "info", config)

    print_string = "-" * (3+2+10+2+10+2+8+2+13+2+7+2+11+2+12+sum([stat_len[stat] for stat in overall_squad_stats])+2*len(stat_len)+7)
    myprint(output, print_string, "info", config)
    print_string = f"{overall_raid_stats['num_used_fights']:>3}"+"  "+f"{overall_raid_stats['date']:>7}"+"  "+f"{overall_raid_stats['start_time']:>10}"+"  "+f"{overall_raid_stats['end_time']:>8}"+"  "+f"{overall_raid_stats['used_fights_duration']:>13}"+"  "+f"{overall_raid_stats['num_skipped_fights']:>7}" +"  "+f"{overall_raid_stats['mean_allies']:>11}"+"  "+f"{overall_raid_stats['mean_enemies']:>12}"+"  "+f"{overall_raid_stats['total_kills']:>5}"
    for stat in overall_squad_stats:
        print_string += "  "+f"{round(overall_squad_stats[stat]):>{stat_len[stat]}}"
    print_string += "\n\n"
    myprint(output, print_string, "info", config)


        
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
            myprint(output_file, print_string, "info", config)
            print_string = "Most times placed in the top "+str(config.num_players_considered_top[stat])+". \nAttendance = number of fights a player was present out of "+str(num_used_fights)+" total fights."
            myprint(output_file, print_string, "info", config)
    elif consistent_or_avg == StatType.AVERAGE:
        if stat == "dist":
            print_string = "Top average "+str(config.num_players_considered_top[stat])+" "+config.stat_names[stat]+" awards"
        else:
            print_string = "Top average "+config.stat_names[stat]+" awards (Max. "+str(config.num_players_listed[stat])+" places)"
            myprint(output_file, print_string, "info", config)
            print_string = "Attendance = number of fights a player was present out of "+str(num_used_fights)+" total fights."
            myprint(output_file, print_string, "info", config)
    print_string = "-------------------------------------------------------------------------------"    
    myprint(output_file, print_string, "info", config)


    # print table header
    print_string = f"    {'Name':<{max_name_length}}" + f"  {'Class':<{profession_length}} "+" Attendance " + " Times Top"
    if stat != "dist":
        print_string += f" {'Total':>9}"
    if stat in config.squad_buff_ids or 'dmg_taken' in stat:
        print_string += f"  {'Average':>7}"
        
    myprint(output_file, print_string, "info", config)    

    
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

        myprint(output_file, print_string, "info", config)
        last_val = player.consistency_stats[stat]
    myprint(output_file, "\n", "info", config)
        


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
    myprint(output_file, print_string, "info", config)
    print_string = "Attendance = total duration of fights attended out of "
    if total_fight_duration["h"] > 0:
        print_string += str(total_fight_duration["h"])+"h "
    print_string += str(total_fight_duration["m"])+"m "+str(total_fight_duration["s"])+"s."    
    myprint(output_file, print_string, "info", config)
    print_string = "------------------------------------------------------------------------"
    myprint(output_file, print_string, "info", config)


    # print table header
    print_string = f"    {'Name':<{max_name_length}}" + f"  {'Class':<{profession_length}} "+f" {'Attendance':>11}"+f" {'Total':>9}"
    if stat in config.squad_buff_ids:
        print_string += f"  {'Average':>7}"
    myprint(output_file, print_string, "info", config)    

    place = 0
    last_val = -1
    # print table
    for i in range(len(top_total_players)):
        player = players[top_total_players[i]]
        if player.total_stats[stat] != last_val:
            place += 1

        fight_time_h = int(player.duration_present['total']/3600)
        fight_time_m = int((player.duration_present['total'] - fight_time_h*3600)/60)
        fight_time_s = int(player.duration_present['total'] - fight_time_h*3600 - fight_time_m*60)

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
        myprint(output_file, print_string, "info", config)
        last_val = player.total_stats[stat]
    myprint(output_file, "\n", "info", config)
    
   

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
    myprint(output_file, print_string, "info", config)
    print_string = "------------------------------------------------------------------------"     
    myprint(output_file, print_string, "info", config)                

    # print table header
    print_string = f"    {'Name':<{max_name_length}}" + f"  {'Class':<{profession_length}} "+f"  Percentage "+f" {'Times Top':>9} " + f" {'Out of':>6}"
    if stat != "dist":
        print_string += f" {'Total':>8}"
    myprint(output_file, print_string, "info", config)    

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
        myprint(output_file, print_string, "info", config)
        last_val = player.portion_top_stats[stat]
    myprint(output_file, "\n", "info", config)


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

