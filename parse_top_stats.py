#!/usr/bin/env python3
from dataclasses import dataclass,field

import argparse
from collections import namedtuple,defaultdict
import os.path
from os import listdir
import sys
import xml.etree.ElementTree as ET
from decimal import *
from enum import Enum

import parser_config

#@dataclass
#class Stats:
Stats = namedtuple('Stats', 'dmg rips stab cleanses heal dist')
#    dmg: float
#    rips: float
#    stab: float
#    cleanses: float
#    heal: float
#    dist: float

class StatType(Enum):
    TOTAL = 1
    CONSISTENT = 2
    LATE_PERCENTAGE = 3
    SWAPPED_PERCENTAGE = 4
    

@dataclass
class Player:
    account: str
    name: str
    profession: str
    num_fights_present: int
    duration_fights_present: int
    num_other_professions: int
    
    total_stats: Stats
    #total_dmg: int = 0
    #total_rips: int = 0
    #total_stab: float = 0.
    #total_cleanses: int = 0
    #total_heal: int = 0

    num_top_x_stats: Stats
    #num_top_x_dmg: int = 0
    #num_top_x_rips: int = 0
    #num_top_x_stab: int = 0
    #num_top_x_cleanses: int = 0
    #num_top_x_heal: int = 0
    #num_top_x_dist: int = 0

    percentage_top_x_stats: Stats
    #percentage_top_x_dmg: int = 0
    #percentage_top_x_rips: int = 0
    #percentage_top_x_stab: int = 0
    #percentage_top_x_cleanses: int = 0
    #percentage_top_x_heal: int = 0
    #percentage_top_x_dist: int = 0

@dataclass
class Config:
    num_players_listed:  Stats
    num_players_considered_top: Stats
    
    min_attendance_portion_for_late: float
    min_attendance_portion_for_buildswap: float

    portion_of_top_for_total: float
    portion_of_top_for_consistent: float
    portion_of_top_for_late: float
    portion_of_top_for_buildswap: float

    min_allied_players: int
    min_fight_duration: int
    min_enemy_players: int

    output_file: str
    input_dir: str

    
def myprint(output_file, output_string):
    print(output_string)
    output_file.write(output_string+"\n")


# players = list of Players
# sorting = list of indices corresponding to players in players list
# config = the configuration being used to determine topx consistent players
# stat = which stat are we considering
def get_topx_players(players, sorting, config, stat, total_or_consistent):
    percentage = 0.
    if total_or_consistent == StatType.TOTAL:
        percentage = Decimal(config.percentage_of_top_for_consistent)
    elif total_or_consistent == StatType.CONSISTENT:
        percentage = Decimal(config.percentage_of_top_for_total)
    else:
        print("ERROR: Called get_topx_players for stats that are not total or consistent")
        return

    top = players[sorting[0]].total_stats(stat) # using total value for both top consistent and top total 
    top_players = list()
    name_length = 0

    # 1) index must be lower than length of the list
    # 2) index must be lower than number of output desired OR list entry has same value as previous entry, i.e. double place
    # 3) value must be greater than 0    
    i = 0
    while i < len(sorting) and (i < config.num_players_listed(stat) or players[sorting[i]].total_stats(stat) == players[sorting[i-1]].total_stats(stat)) and players[sorting[i]].total_stats(stat) > 0:
        is_top = false
        if stat != "dist":
            # 4) value must be at least percentage% of top value for everything except distance
            if players[sorting[i]].total_stats(stat) > top * percentage:
                is_top = True
        else: # dist stats
            is_top = True

        if append:
            top_players.append(sorting[i])
            name = players[sorting[i]].name
            if len(name) > name_length:
                name_length = len(name)
        i += 1
        
    return top_players, name_length

        
# players = list of Players
# sorting = list of indices corresponding to players in players list
# config = the configuration being used to determine topx consistent players
# stat = which stat are we considering
def get_topx_percentage_players(players, sorting, config, stat, comparison_percentage, late_or_swapping, num_total_fights, top_consistent_players, top_total_players):
    #sorted_percentages, comparison_percentage, num_total_fights, top_consistent_players, top_total_players):
    i = 0
    top_percentage_players = list()
    name_length = 0
    
    comparison_value = 0
    min_attendance = 0
    if late_or_swapping == StatType.LATE_PERCENTAGE:
        comparison_value = comparison_percentage * config.percentage_of_top_for_total/100
        min_attendance = config.min_attendance_portion_for_late/100 * num_total_fights
    elif late_or_swapping == StatType.SWAPPED_PERCENTAGE:
        comparison_value = comparison_percentage * config.percentage_of_top_for_buildswap/100
        min_attendance = config.min_attendance_portion_for_buildswap/100 * num_total_fights
    else:
        print("ERROR: Called get_topx_percentag_players for stats that are not late_percentage or swapped_percentage")
        return 

        
    # 1) index must be lower than length of the list
    # 2) percentage value must be at least comparison percentage value
    while i < len(sorting) and players[sorting[i]].percentage_stats(stat) >= comparison_value:
        if sorting[i] in top_consistent_players or sorting[i] in top_total_players:
            i += 1
            continue
        player = players[sorting[i]]
        if player.num_fights_present < num_total_fights and player.num_fights_present > min_attendance
            top_percentage_players.append(sorting[i])
            if len(player.name) > name_length:
                name_length = len(name)
        i += 1
    return top_percentage_players, name_length


# get the professions of all players indicated by the indices. Additionally, get the length of the longest profession name.
# players = list of all players
# indices = list of relevant indices
def get_professions_and_length(players, indices):
    profession_strings = list()
    profession_length = 0
    for i in indices:
        player = players[indices[i]]
        professions_str = profession_abbreviations[player.profession]
        profession_strings.append(professions_str)
        if len(professions_str) > profession_length:
            profession_length = len(professions_str)
    return profession_strings, profession_length


# Write the top x people who achieved top x in stat most often.
# Input:
# topx_x_times = how often did each player achieve a top x spot in this stat
# total_values = what's the summed up value over all fights for this stat for each player
# stat = which stat are we looking at (dmg, cleanses, ...)
# num_top_stats = number of players to print
def write_sorted_top_x(output_file, topx_x_times, total_values, professions, num_fights_present, used_fights, stat, num_top_stats, percentage_of_top):
    
    if len(topx_x_times) == 0:
        return

    # sort players according to number of times top x was achieved for stat
    sorted_topx = sorted(topx_x_times.items(), key=lambda x:x[1], reverse=True)

    if stat == "distance":
        print_string = "Top "+str(num_top_stats)+" "+stat+" consistency awards"
    else:
        print_string = "Top "+stat+" consistency awards (Max. "+str(num_top_stats)+" people, min. "+str(round(percentage_of_top*100.))+"% of most consistent)"
    myprint(output_file, print_string)
    #print_string = "Most times placed in the top "+str(num_top_stats)+". Attendance = number of fights a player was present out of "+str(used_fights)+" total fights."
    print_string = "Most times placed in the top "+str(num_top_stats)+". \nAttendance = number of fights a player was present out of "+str(used_fights)+" total fights."    
    myprint(output_file, print_string)
    #print_string = "-----------------------------------------------------------------------------------------------------------"
    print_string = "-------------------------------------------------------------------------------"    
    myprint(output_file, print_string)

    top = total_values[sorted_topx[0][0]] 

    # get names that get on the list and their professions
    top_consistent_players, name_length = get_topx_consistent_players(sorted_topx, total_values, stat, num_top_stats, percentage_of_top)
    profession_strings, profession_length = get_profession_and_length(top_consistent_players, professions)

    print_string = f"    {'Name':<{name_length}}" + f"  {'Class':<{profession_length}} "+f" Attendance " + " Times Top"
    if stat != "distance":
        print_string += f" {'Total':>9}"
    if stat == "stab output":
        print_string += f"  {'Average':>7}"
        
    myprint(output_file, print_string)    

    
    place = 0
    last_val = 0
    
    for name in top_consistent_players:
        if topx_x_times[name] != last_val:
            place += 1
        print_string = f"{place:>2}"+f". {name:<{name_length}} "+f" {profession_strings[name]:<{profession_length}} "+f" {num_fights_present[name]:>10} "+f" {topx_x_times[name]:>9}"
        if stat != "distance" and stat != "stab output":
            print_string += f" {round(total_values[name], 2):>8}"
            #print_string += " | total "+str(total_values[name])
        if stat == "stab output":
            average = round(total_values[name]/duration_fights_present[name], 2)
            total = round(total_values[name], 2)
            print_string += f" {total:>8}s"+f" {average:>8}"

        myprint(output_file, print_string)
        last_val = topx_x_times[name]

    return top_consistent_players
        
                
# Write the top x people who achieved top x in stat with the highest percentage. This only considers fights where each player was present, i.e., a player who was in 4 fights and achieved a top x spot in 2 of them gets 50%, as does a player who was only in 2 fights and achieved a top x spot in 1 of them.
# Input:
# topx_x_times = how often did each player achieve a topx spot in this stat
# num_fights_present = in how many fights was the player present
# stat = which stat are we looking at (dmg, cleanses, ...)
def write_sorted_top_x_percentage(output_file, topx_x_times, total_values, num_fights_present, num_total_fights, professions, stat, top_consistent_players, top_total_players = list()):
    if len(topx_x_times) == 0:
        return
    
    percentages = {}
    for name in topx_x_times.keys():
        percentages[name] = topx_x_times[name] / num_fights_present[name]
    sorted_percentages = sorted(percentages.items(), key=lambda x:x[1], reverse=True)

    # get names that get on the list and their professions
    sorted_topx = sorted(topx_x_times.items(), key=lambda x:x[1], reverse=True)    
    comparison_percentage = sorted_topx[0][1]/num_fights_present[sorted_topx[0][0]]

    top_percentage_players, name_length = get_topx_percentage_players(sorted_percentages, comparison_percentage, num_total_fights, top_consistent_players, top_total_players)
    profession_strings, profession_length = get_profession_and_length(top_percentage_players, professions)

    if len(top_percentage_players) > 0:
        print_string = "\nTop "+stat+" percentage (Min. top consistent player percentage = "+f"{comparison_percentage*100:.0f}%)"
        myprint(output_file, print_string)
        print_string = "------------------------------------------------------------------------"                
        myprint(output_file, print_string)                
        print_string = f"    {'Name':<{name_length}}" + f"  {'Class':<{profession_length}} "+f"  Percentage "+f" {'Times Top':>9} " + f" {'Out of':>6}"
        if stat != "distance":
            print_string += f" {'Total':>8}"
        myprint(output_file, print_string)    

    place = 0
    last_val = 0
    
    for name in top_percentage_players:
        if percentages[name] != last_val:
            place += 1

        percentage = int(percentages[name]*100)
        print_string = f"{place:>2}"+f". {name:<{name_length}} "+f" {profession_strings[name]:<{profession_length}} " +f" {percentage:>10}% " +f" {topx_x_times[name]:>9} "+f" {num_fights_present[name]:>6} "
        if stat != "distance":
            print_string += f" {total_values[name]:>7}"
        myprint(output_file, print_string)
        last_val = percentages[name]
    

# Write the top x people who achieved top total stat.
# Input:
# total_values = stat summed up over all fights
# stat = which stat are we looking at (dmg, cleanses, ...)
# num_top_stats = number of players to print
def write_sorted_total(output_file, total_values, professions, duration_fights_present, total_fight_duration, stat, num_top_stats, percentage_of_top):
    if len(total_values) == 0:
        return

    sorted_total_values = sorted(total_values.items(), key=lambda x:x[1], reverse=True)    

    print_string = "\nTop overall "+stat+" awards (Max. "+str(num_top_stats)+" people, min. "+str(round(percentage_of_top*100.))+"% of 1st place)"
    myprint(output_file, print_string)
    print_string = "Attendance = total duration of fights attended out of "
    if total_fight_duration["h"] > 0:
        print_string += str(total_fight_duration["h"])+"h "
    print_string += str(total_fight_duration["m"])+"m "+str(total_fight_duration["s"])+"s."    
    myprint(output_file, print_string)
    print_string = "------------------------------------------------------------------------"                
    myprint(output_file, print_string)

    top_total_players, name_length = get_topx_total_players(sorted_total_values, num_top_stats, percentage_of_top)
    profession_strings, profession_length = get_profession_and_length(top_total_players, professions)
    profession_length = max(profession_length, 5)
    
    print_string = f"    {'Name':<{name_length}}" + f"  {'Class':<{profession_length}} "+f" {'Attendance':>11}"+f" {'Total':>9}"
    if stat == "stab output":
        print_string += f"  {'Average':>7}"
    myprint(output_file, print_string)    
    
    place = 0
    last_val = 0
    
    for name in top_total_players:
        if total_values[name] != last_val:
            place += 1

        fight_time_h = int(duration_fights_present[name]/3600)
        fight_time_m = int((duration_fights_present[name] - fight_time_h*3600)/60)
        fight_time_s = int(duration_fights_present[name] - fight_time_h*3600 - fight_time_m*60)
        print_string = f"{place:>2}"+f". {name:<{name_length}} "+f" {profession_strings[name]:<{profession_length}} "
        if fight_time_h > 0:
            print_string += f" {fight_time_h:>2}h {fight_time_m:>2}m {fight_time_s:>2}s"
        else:
            print_string += f" {fight_time_m:>6}m {fight_time_s:>2}s"

        if stat == "stab output":
            print_string += f" {round(total_values[name], 2):>8}s"
            average = round(total_values[name]/duration_fights_present[name], 2)
            print_string += f" {average:>8}"
        else:
            print_string += f" {total_values[name]:>8}"
        myprint(output_file, print_string)
        last_val = total_values[name]

    return top_total_players
    
if __name__ == '__main__':
    debug = False # enable / disable debug output

    parser = argparse.ArgumentParser(description='This reads a set of arcdps reports in xml format and generates top stats.')
    parser.add_argument('xml_directory', help='Directory containing .xml files from arcdps reports')
    parser.add_argument('-o', '--output', dest="output_filename", help="Text file to write the computed top stats")
    parser.add_argument('-l', '--log_file', dest="log_file", help="Logging file with all the output")
    parser.add_argument('-d', '--duration', dest="minimum_duration", type=int, help="Minimum duration of a fight in s. Shorter fights will be ignored. Defaults to 30s.", default=30)
    parser.add_argument('-a', '--ally_numbers', dest="minimum_ally_numbers", type=int, help="Minimum of allied players in a fight. Fights with less players will be ignored. Defaults to 10.", default=10)
    parser.add_argument('-n', '--num_top_stats', dest="num_top_stats", type=int, help="Number of players that will be printed for achieving top <num_top_stats> for most stats. Special cases: Distance to tag and damage. Defaults to 5.", default=5)
    parser.add_argument('-m', '--num_top_stats_dmg', dest="num_top_stats_dmg", type=int, help="Number of players that will be printed for achieving top <num_top_stats_dmg> damage. Defaults to 10.", default=10)    
    parser.add_argument('-p', '--percentage_of_top', dest="percentage_of_top", type=int, help="Minimum percentage of the top player that has to be reached to get an award. Defaults to 50%.", default=50)    
    
    args = parser.parse_args()

    if not os.path.isdir(args.xml_directory):
        print("Directory ",args.xml_directory," is not a directory or does not exist!")
        sys.exit()
    if args.output_filename is None:
        args.output_filename = args.xml_directory+"/top_stats.txt"
    if args.log_file is None:
        args.log_file = args.xml_directory+"/log.txt"

    output = open(args.output_filename, "w")
    log = open(args.log_file, "w")
    top_percentage_frac = args.percentage_of_top/100.
        
    print_string = "Using xml directory "+args.xml_directory+", writing output to "+args.output_filename+" and log to "+args.log_file
    print(print_string)
    print_string = "Considering fights with more than "+str(args.minimum_ally_numbers)+" allied players that took longer than "+str(args.minimum_duration)+" s."
    myprint(log, print_string)
        
    top_damage_x_times = collections.defaultdict(int)
    top_strips_x_times = collections.defaultdict(int)
    top_cleanses_x_times = collections.defaultdict(int)
    top_stab_x_times = collections.defaultdict(int)
    top_healing_x_times = collections.defaultdict(int)
    top_distance_x_times = collections.defaultdict(int)

    total_damage = collections.defaultdict(int)
    total_strips = collections.defaultdict(int)
    total_cleanses = collections.defaultdict(int)
    total_stab = collections.defaultdict(int)
    total_healing = collections.defaultdict(int)    
    total_distance = collections.defaultdict(int)

    num_players_per_fight = list()
    
    num_fights_present = collections.defaultdict(int)
    duration_fights_present = collections.defaultdict(int)
    professions = collections.defaultdict(list)

    # healing only in xml if addon was installed
    found_healing = False

    # overall stats over whole squad
    all_damage = 0
    all_strips = 0
    all_cleanses = 0
    all_stab = 0
    all_healing = 0
    all_deaths = 0
    all_kills = 0
    
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

        # skip fights that last less than minimum_duration seconds
        if(duration < args.minimum_duration):
            log.write(print_string)
            print_string = "\nFight only took "+str(mins)+"m "+str(secs)+"s. Skipping fight."
            myprint(log, print_string)
            continue
        
        # skip fights with less than minimum_ally_numbers allies
        num_allies = len(xml_root.findall('players'))
        if num_allies < args.minimum_ally_numbers:
            log.write(print_string)
            print_string = "\nOnly "+str(num_allies)+" allied players involved. Skipping fight."
            myprint(log, print_string)
            continue

        used_fights += 1
        used_fights_duration += duration
        num_players_per_fight.append(num_allies)

        # dictionaries for stats for each player in this fight
        damage = {}
        cleanses = {}
        strips = {}
        stab = {}
        healing = {}
        distance = {}

        # get stats for each player
        for xml_player in xml_root.iter('players'):
            # get player name -> was present in this fight
            name_xml = xml_player.find('name')
            name = name_xml.text
            num_fights_present[name] += 1
            duration_fights_present[name] += duration
            profession = xml_player.find('profession').text
            if not profession in professions[name]:
                professions[name].append(profession)
            #print(professions[name])

            # deaths and kills
            deaths = xml_player.find('defenses').find('deadCount')
            all_deaths += int(deaths.text)
            kills = xml_player.find('statsAll').find('killed')
            all_kills += int(kills.text)
            
            # get damage
            dmg_xml = xml_player.find('dpsAll').find('damage')
            damage[name] = int(dmg_xml.text)

            # get strips and cleanses
            support_stats = xml_player.find('support')
            strips_xml = support_stats.find('boonStrips')
            strips[name] = int(strips_xml.text)
            cleanses_xml = support_stats.find('condiCleanse')
            cleanses[name] = int(cleanses_xml.text)

            # get stab in squad generation -> need to loop over all buff
            stab_generated = 0
            for buff in xml_player.iter('squadBuffs'):
                # find stab buff
                if buff.find('id').text != stab_id:
                    continue
                stab_xml = buff.find('buffData').find('generation')
                stab_generated = Decimal(stab_xml.text)
                break
            stab[name] = stab_generated

            # check if healing was logged
            ext_healing_xml = xml_player.find('extHealingStats')
            if(ext_healing_xml != None):
                found_healing = True
                healing[name] = 0
                for outgoing_healing_xml in ext_healing_xml.iter('outgoingHealingAllies'):
                    outgoing_healing_xml2 = outgoing_healing_xml.find('outgoingHealingAllies')
                    if not outgoing_healing_xml2 is None:
                        healing_xml = outgoing_healing_xml2.find('healing')
                        healing[name] += int(healing_xml.text)

            # get distance to tag
            distance_xml = xml_player.find('statsAll').find('distToCom')
            distance[name] = Decimal(distance_xml.text)

            if debug:
                print(name)
                print("damage:",damage[name])
                print("strips:",strips[name])
                print("cleanses:",cleanses[name])
                print("stab:",stab_generated)
                print("healing:",healing[name])
                print(f"distance: {distance[name]:.2f}")
                print("\n")
                
            # add new data from this fight to total stats
            total_damage[name] += damage[name]
            total_strips[name] += strips[name]
            total_cleanses[name] += cleanses[name]
            total_stab[name] += stab[name]*duration
            if found_healing:
                total_healing[name] += healing[name]
            # distance sometimes -1 for some reason
            if distance[name] >= 0:
                total_distance[name] += distance[name]

            all_damage += damage[name]
            all_strips += strips[name]
            all_cleanses += cleanses[name]
            all_stab += stab[name]*duration
            if found_healing:
                all_healing += healing[name]
            
        #print("\n")

        # create dictionaries sorted according to stats
        sortedDamage = sorted(damage, key=damage.get, reverse=True)
        sortedStrips = sorted(strips, key=strips.get, reverse=True)
        sortedCleanses = sorted(cleanses, key=cleanses.get, reverse=True)
        sortedStab = sorted(stab, key=stab.get, reverse=True)
        sortedHealing = sorted(healing, key=healing.get, reverse=True)
        # small distance = good -> don't reverse sorting. Need to check for -1 -> keep values
        sortedDistance = sorted(distance.items(), key=lambda x:x[1])

        if debug:
            print("sorted dmg:", sortedDamage,"\n")
            print("sorted strips:", sortedStrips,"\n")
            print("sorted cleanses:",sortedCleanses,"\n")
            print("sorted stab:", sortedStab,"\n")
            print("sorted healing:", sortedHealing,"\n")
            print("sorted distance:", sortedDistance, "\n")
        
        # increase number of times top x was achieved for top x players in each stat
        for i in range(min(len(sortedDamage), args.num_top_stats_dmg)):
            top_damage_x_times[sortedDamage[i]] += 1
            
        for i in range(min(len(sortedStrips), args.num_top_stats)):
            top_strips_x_times[sortedStrips[i]] += 1
            top_cleanses_x_times[sortedCleanses[i]] += 1
            top_stab_x_times[sortedStab[i]] += 1

        # might not have entries for healing -> separate loop
        for i in range(min(len(sortedHealing), args.num_top_stats)):
            top_healing_x_times[sortedHealing[i]] += 1

        # get top x+1 for distance bc first is always the com. Also throw out negative distance.
        valid_distance = 0
        first_valid = True
        i = 0
        while i < len(sortedDistance) and valid_distance < args.num_top_stats+1:
            if sortedDistance[i][1] >= 0:
                if first_valid:
                    first_valid  = False
                else:
                    top_distance_x_times[sortedDistance[i][0]] += 1
                valid_distance += 1
            i += 1


    attendance_percentage = {}
    for name in num_fights_present.keys():
        attendance_percentage[name] = int(num_fights_present[name]/used_fights*100)


    #get total duration in h, m, s
    total_fight_duration = {}
    total_fight_duration["h"] = int(used_fights_duration/3600)
    total_fight_duration["m"] = int((used_fights_duration - total_fight_duration["h"]*3600) / 60)
    total_fight_duration["s"] = int(used_fights_duration - total_fight_duration["h"]*3600 -  total_fight_duration["m"]*60)

    total_stab_duration = {}
    total_stab_duration["h"] = int(all_stab/3600)
    total_stab_duration["m"] = int((all_stab - total_stab_duration["h"]*3600)/60)
    total_stab_duration["s"] = int(all_stab - total_stab_duration["h"]*3600 - total_stab_duration["m"]*60)    
    
    # print top x players for all stats. If less then x
    # players, print all. If x-th place doubled, print all with the
    # same amount of top x achieved.

    myprint(log, "\n")

    print_string = "Welcome to the CARROT AWARDS!\n"
    myprint(output, print_string)
    
    print_string = "The following stats are computed over "+str(used_fights)+" out of "+str(total_fights)+" fights.\n"# fights with a total duration of "+used_fights_duration+".\n"
    myprint(output, print_string)

    # print total squad stats
    print_string = "Squad overall did "+str(all_damage)+" damage, ripped "+str(all_strips)+" boons, cleansed "+str(all_cleanses)+" conditions, \ngenerated "
    if total_stab_duration["h"] > 0:
        print_string += str(total_stab_duration["h"])+"h "
    print_string += str(total_stab_duration["m"])+"m "+str(total_stab_duration["s"])+"s of stability"        
    if found_healing:
        print_string += ", healed for "+str(all_healing)
    print_string += ", \nkilled "+str(all_kills)+" enemies and had "+str(all_deaths)+" deaths \nover a total time of "
    if total_fight_duration["h"] > 0:
        print_string += str(total_fight_duration["h"])+"h "
    print_string += str(total_fight_duration["m"])+"m "+str(total_fight_duration["s"])+"s in "+str(used_fights)+" fights.\n"
    print_string += "There were between "+str(min(num_players_per_fight))+" and "+str(max(num_players_per_fight))+" allied players involved.\n"    
        
    myprint(output, print_string)

    
    myprint(output, "DAMAGE AWARDS\n")
    top_consistent_damagers = write_sorted_top_x(output, top_damage_x_times, total_damage, professions, num_fights_present, used_fights, "damage", args.num_top_stats_dmg, top_percentage_frac)
    top_total_damagers = write_sorted_total(output, total_damage, professions, duration_fights_present, total_fight_duration, "damage", args.num_top_stats_dmg, top_percentage_frac)
    myprint(output, "\n")    
        
    myprint(output, "BOON STRIPS AWARDS\n")        
    top_consistent_strippers = write_sorted_top_x(output, top_strips_x_times, total_strips, professions, num_fights_present, used_fights, "strips", args.num_top_stats, top_percentage_frac)
    top_total_strippers = write_sorted_total(output, total_strips, professions, duration_fights_present, total_fight_duration, "strips", args.num_top_stats, top_percentage_frac)
    myprint(output, "\n")            

    myprint(output, "CONDITION CLEANSES AWARDS\n")        
    top_consistens_cleaners = write_sorted_top_x(output, top_cleanses_x_times, total_cleanses, professions, num_fights_present, used_fights, "cleanses", args.num_top_stats, top_percentage_frac)
    top_total_cleaners = write_sorted_total(output, total_cleanses, professions, duration_fights_present, total_fight_duration, "cleanses", args.num_top_stats, top_percentage_frac)
    myprint(output, "\n")    
        
    myprint(output, "STABILITY OUTPUT AWARDS \n")        
    top_consistent_stabbers = write_sorted_top_x(output, top_stab_x_times, total_stab, professions, num_fights_present, used_fights, "stab output", args.num_top_stats, top_percentage_frac)        
    top_total_stabbers = write_sorted_total(output, total_stab, professions, duration_fights_present, total_fight_duration, "stab output", args.num_top_stats, top_percentage_frac)
    myprint(output, "\n")    

    top_consistent_healers = list()
    top_total_healers = list()    
    if found_healing:
        myprint(output, "HEALING AWARDS\n")        
        top_consistent_healers = write_sorted_top_x(output, top_healing_x_times, total_healing, professions, num_fights_present, used_fights, "healing", args.num_top_stats, top_percentage_frac)
        top_total_healers = write_sorted_total(output, total_healing, professions, duration_fights_present, total_fight_duration, "healing", args.num_top_stats, top_percentage_frac)
        myprint(output, "\n")    

    myprint(output, "SHORTEST DISTANCE TO TAG AWARDS\n")        
    top_consistent_distancers = write_sorted_top_x(output, top_distance_x_times, total_distance, professions, num_fights_present, used_fights, "distance", args.num_top_stats, top_percentage_frac)
    # distance to tag total doesn't make much sense
    myprint(output, "\n")
    
    myprint(output, 'SPECIAL "LATE BUT GREAT" MENTIONS\n')        
    write_sorted_top_x_percentage(output, top_damage_x_times, total_damage, num_fights_present, used_fights, professions, "damage", top_consistent_damagers, top_total_damagers)
    write_sorted_top_x_percentage(output, top_strips_x_times, total_strips, num_fights_present, used_fights, professions, "strips", top_consistent_strippers, top_total_strippers)
    write_sorted_top_x_percentage(output, top_cleanses_x_times, total_cleanses, num_fights_present, used_fights, professions, "cleanses", top_consistens_cleaners, top_total_cleaners)
    write_sorted_top_x_percentage(output, top_stab_x_times, total_stab, num_fights_present, used_fights, professions, "stab", top_consistent_stabbers, top_total_stabbers)
    write_sorted_top_x_percentage(output, top_healing_x_times, total_healing, num_fights_present, used_fights, professions, "healing", top_consistent_healers, top_total_healers)        
    write_sorted_top_x_percentage(output, top_distance_x_times, total_distance, num_fights_present, used_fights, professions, "distance", top_consistent_distancers)        

