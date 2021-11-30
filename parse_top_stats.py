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
import operator


import parser_config

#@dataclass
#class Stats(dict)
#Stats = namedtuple('Stats', 'dmg rips stab cleanses heal dist deaths kills')


class StatType(Enum):
    TOTAL = 1
    CONSISTENT = 2
    LATE_PERCENTAGE = 3
    SWAPPED_PERCENTAGE = 4
    

@dataclass
class Player:
    account: str = ""
    name: str = ""
    profession: str = ""
    num_fights_present: int = 0
    attendance_percentage: float = 0.
    duration_fights_present: int = 0
    swapped_build: bool = False
    
    total_stats: dict = field(default_factory=dict)# Stats #= Stats(0,0,0,0,0,0,0,0)
    consistency_stats: dict = field(default_factory=dict) # Stats #= Stats(0,0,0,0,0,0,0,0)
    percentage_top_stats: dict = field(default_factory=dict)#Stats# = Stats(0,0,0,0,0,0,0,0)

#def compareByName(player1, player2):
#    if player1.name == player2.name:
#        return 0
#    if player1.name < player2.name:
#        return -1
#    if player1.name < player2.name:
#        return 1
#
#def compareByNameAndClass(player1, player2):
#    if player1.name == player2.name:
#        if player1.profession == player2.profession:
#            return 0
#        if player1.profession < player2.profession:
#            return -1
#        if player1.profession > player2.profession:
#            return 1
#    if player1.name < player2.name:
#        return -1
#    if player1.name < player2.name:
#        return 1    
    
@dataclass
class Config:
    num_players_listed: dict = field(default_factory=dict)# Stats = Stats(0, 0, 0, 0, 0, 0, 0, 0)
    num_players_considered_top: dict = field(default_factory=dict)# Stats = Stats(0, 0, 0, 0, 0, 0, 0, 0)
    
    min_attendance_portion_for_late: float = 0.
    min_attendance_portion_for_buildswap: float = 0.

    portion_of_top_for_total: float = 0.
    portion_of_top_for_consistent: float = 0.
    portion_of_top_for_late: float = 0.
    portion_of_top_for_buildswap: float = 0.

    min_allied_players: int = 0
    min_fight_duration: int = 0
    min_enemy_players: int = 0

    output_file: str = ""
    input_dir: str = ""

    
def myprint(output_file, output_string):
    print(output_string)
    output_file.write(output_string+"\n")


def increase_top_x_reached(players, sortedList, player_index, config, stat):
    if stat != 'dist':
        for i in range(min(len(sortedList), config.num_players_considered_top[stat])):
            players[player_index[sortedList[i]]].consistency_stats[stat] += 1# = players[player_index[sortedList[i]]].percentage_top_stats._replace(stat=num_top_stat)
            players[player_index[sortedList[i]]].percentage_top_stats[stat] += 1 #TODO divide by num fights attended at the end
        return

    # different for dist
    valid_distance = 0
    first_valid = True
    i = 0
    while i < len(sortedDistance) and valid_distance < config.num_players_considered_top[stat]+1:
        if sortedList[i][1] >= 0:
            if first_valid:
                first_valid  = False
            else:
                players[player_index[sortedList[i][0]]].consistency_stats[stat] += 1
                players[player_index[sortedList[i][0]]].percentage_top_stats[stat] += 1 #TODO divide by num fights attended at the end         
                valid_distance += 1
        i += 1



# players = list of Players
# sorting = list of indices corresponding to players in players list
# config = the configuration being used to determine topx consistent players
# stat = which stat are we considering
def get_topx_players(players, sorting, config, stat, total_or_consistent):
    percentage = 0.
    if total_or_consistent == StatType.TOTAL:
        percentage = float(config.portion_of_top_for_consistent)#Decimal
    elif total_or_consistent == StatType.CONSISTENT:
        percentage = float(config.portion_of_top_for_total)#Decimal
    else:
        print("ERROR: Called get_topx_players for stats that are not total or consistent")
        return

    top = players[sorting[0]].total_stats[stat] # using total value for both top consistent and top total 
    top_players = list()
    name_length = 0

    # 1) index must be lower than length of the list
    # 2) index must be lower than number of output desired OR list entry has same value as previous entry, i.e. double place
    # 3) value must be greater than 0    
    i = 0
    while i < len(sorting) and (i < config.num_players_listed[stat] or players[sorting[i]].total_stats[stat] == players[sorting[i-1]].total_stats[stat]) and players[sorting[i]].total_stats[stat] > 0:
        is_top = False
        if stat != "dist":
            # 4) value must be at least percentage% of top value for everything except distance
            if players[sorting[i]].total_stats[stat] > top * percentage:
                is_top = True
        else: # dist stats
            is_top = True

        if is_top:
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
        comparison_value = comparison_percentage * config.portion_of_top_for_late
        min_attendance = config.min_attendance_portion_for_late/100 * num_total_fights
    elif late_or_swapping == StatType.SWAPPED_PERCENTAGE:
        comparison_value = comparison_percentage * config.portion_of_top_for_buildswap
        min_attendance = config.min_attendance_portion_for_buildswap/100 * num_total_fights
    else:
        print("ERROR: Called get_topx_percentag_players for stats that are not late_percentage or swapped_percentage")
        return 

        
    # 1) index must be lower than length of the list
    # 2) percentage value must be at least comparison percentage value
    while i < len(sorting) and players[sorting[i]].percentage_top_stats(stat) >= comparison_value:
        if sorting[i] in top_consistent_players or sorting[i] in top_total_players:
            i += 1
            continue
        player = players[sorting[i]]
        if player.num_fights_present < num_total_fights and player.num_fights_present > min_attendance:
            if late_or_swapping == StatType.SWAPPED_PERCENTAGE and player.swapped_build == False:
                i += 1
                continue                
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
    print([player.name for player in players])
    print(indices)
    for i in indices:
        player = players[i]
        professions_str = parser_config.profession_abbreviations[player.profession]
        profession_strings.append(professions_str)
        if len(professions_str) > profession_length:
            profession_length = len(professions_str)
    return profession_strings, profession_length


# Write the top x people who achieved top x in stat most often.
# Input:
# players = list of Players
# config = the configuration being used to determine topx consistent players
# num_used_fights = the number of fights that are being used in stat computation
# stat = which stat are we considering
def write_sorted_top_x(players, config, num_used_fights, stat, output_file):

    # sort players according to number of times top x was achieved for stat
    #sorted_topx = sorted(topx_x_times.items(), key=lambda x:x[1], reverse=True)
    #sorted_topx = sorted(players, key=operator.attrgetter('consistency_stats')[stat]) # key = itemgetter('consistency_stats[stat]'))
    #sorted_topx = sorted(players, key = lambda p: p.consistency_stats[stat])
    decorated = [(player.consistency_stats[stat], i, player) for i, player in enumerate(players)]
    decorated.sort(reverse=True)
    sorted_topx = [i for consistency, i, player in decorated] 
    print("top stats for consistency",stat,":", sorted_topx)

    if stat == "distance":
        print_string = "Top "+str(config.num_players_considered_top[stat])+" "+stat+" consistency awards"
    else:
        print_string = "Top "+stat+" consistency awards (Max. "+str(config.num_players_considered_top[stat])+" people, min. "+str(round(config.portion_of_top_for_consistent*100.))+"% of most consistent)"
    myprint(output_file, print_string)
    #print_string = "Most times placed in the top "+str(num_top_stats)+". Attendance = number of fights a player was present out of "+str(used_fights)+" total fights."
    print_string = "Most times placed in the top "+str(config.num_players_considered_top[stat])+". \nAttendance = number of fights a player was present out of "+str(num_used_fights)+" total fights."    
    myprint(output_file, print_string)
    #print_string = "-----------------------------------------------------------------------------------------------------------"
    print_string = "-------------------------------------------------------------------------------"    
    myprint(output_file, print_string)

    # get names that get on the list and their professions
    top_consistent_players, name_length = get_topx_players(players, sorted_topx, config, stat, StatType.CONSISTENT)
    profession_strings, profession_length = get_professions_and_length(players, top_consistent_players)

    print_string = f"    {'Name':<{name_length}}" + f"  {'Class':<{profession_length}} "+f" Attendance " + " Times Top"
    if stat != "dist":
        print_string += f" {'Total':>9}"
    if stat == "stab":
        print_string += f"  {'Average':>7}"
        
    myprint(output_file, print_string)    

    
    place = 0
    last_val = 0
    
    for i in range(len(top_consistent_players)):
        player = players[top_consistent_players[i]]
        if player.consistency_stats[stat] != last_val:
            place += 1
        print_string = f"{place:>2}"+f". {player.name:<{name_length}} "+f" {profession_strings[i]:<{profession_length}} "+f" {player.num_fights_present:>10} "+f" {round(player.consistency_stats[stat]):>9}"
        if stat != "dist" and stat != "stab":
            print_string += f" {round(player.total_stats[stat], 2):>8}"
            #print_string += " | total "+str(total_values[name])
        if stat == "stab":
            average = round(player.total_stats[stat]/player.duration_fights_present, 2)
            total = round(player.total_stats[stat], 2)
            print_string += f" {total:>8}s"+f" {average:>8}"

        myprint(output_file, print_string)
        last_val = player.consistency_stats[stat]

    return top_consistent_players
        
                
## Write the top x people who achieved top x in stat with the highest percentage. This only considers fights where each player was present, i.e., a player who was in 4 fights and achieved a top x spot in 2 of them gets 50%, as does a player who was only in 2 fights and achieved a top x spot in 1 of them.
## Input:
## topx_x_times = how often did each player achieve a topx spot in this stat
## num_fights_present = in how many fights was the player present
## stat = which stat are we looking at (dmg, cleanses, ...)
#def write_sorted_top_x_percentage(output_file, topx_x_times, total_values, num_fights_present, num_total_fights, professions, stat, top_consistent_players, top_total_players = list()):
#    if len(topx_x_times) == 0:
#        return
#    
#    percentages = {}
#    for name in topx_x_times.keys():
#        percentages[name] = topx_x_times[name] / num_fights_present[name]
#    sorted_percentages = sorted(percentages.items(), key=lambda x:x[1], reverse=True)
#
#    # get names that get on the list and their professions
#    sorted_topx = sorted(topx_x_times.items(), key=lambda x:x[1], reverse=True)    
#    comparison_percentage = sorted_topx[0][1]/num_fights_present[sorted_topx[0][0]]
#
#    top_percentage_players, name_length = get_topx_percentage_players(sorted_percentages, comparison_percentage, num_total_fights, top_consistent_players, top_total_players)
#    profession_strings, profession_length = get_profession_and_length(top_percentage_players, professions)
#
#    if len(top_percentage_players) > 0:
#        print_string = "\nTop "+stat+" percentage (Min. top consistent player percentage = "+f"{comparison_percentage*100:.0f}%)"
#        myprint(output_file, print_string)
#        print_string = "------------------------------------------------------------------------"                
#        myprint(output_file, print_string)                
#        print_string = f"    {'Name':<{name_length}}" + f"  {'Class':<{profession_length}} "+f"  Percentage "+f" {'Times Top':>9} " + f" {'Out of':>6}"
#        if stat != "distance":
#            print_string += f" {'Total':>8}"
#        myprint(output_file, print_string)    
#
#    place = 0
#    last_val = 0
#    
#    for name in top_percentage_players:
#        if percentages[name] != last_val:
#            place += 1
#
#        percentage = int(percentages[name]*100)
#        print_string = f"{place:>2}"+f". {name:<{name_length}} "+f" {profession_strings[name]:<{profession_length}} " +f" {percentage:>10}% " +f" {topx_x_times[name]:>9} "+f" {num_fights_present[name]:>6} "
#        if stat != "distance":
#            print_string += f" {total_values[name]:>7}"
#        myprint(output_file, print_string)
#        last_val = percentages[name]
#    
#
## Write the top x people who achieved top total stat.
## Input:
## total_values = stat summed up over all fights
## stat = which stat are we looking at (dmg, cleanses, ...)
## num_top_stats = number of players to print
#def write_sorted_total(output_file, total_values, professions, duration_fights_present, total_fight_duration, stat, num_top_stats, percentage_of_top):
#    if len(total_values) == 0:
#        return
#
#    sorted_total_values = sorted(total_values.items(), key=lambda x:x[1], reverse=True)    
#
#    print_string = "\nTop overall "+stat+" awards (Max. "+str(num_top_stats)+" people, min. "+str(round(percentage_of_top*100.))+"% of 1st place)"
#    myprint(output_file, print_string)
#    print_string = "Attendance = total duration of fights attended out of "
#    if total_fight_duration["h"] > 0:
#        print_string += str(total_fight_duration["h"])+"h "
#    print_string += str(total_fight_duration["m"])+"m "+str(total_fight_duration["s"])+"s."    
#    myprint(output_file, print_string)
#    print_string = "------------------------------------------------------------------------"                
#    myprint(output_file, print_string)
#
#    top_total_players, name_length = get_topx_total_players(sorted_total_values, num_top_stats, percentage_of_top)
#    profession_strings, profession_length = get_profession_and_length(top_total_players, professions)
#    profession_length = max(profession_length, 5)
#    
#    print_string = f"    {'Name':<{name_length}}" + f"  {'Class':<{profession_length}} "+f" {'Attendance':>11}"+f" {'Total':>9}"
#    if stat == "stab output":
#        print_string += f"  {'Average':>7}"
#    myprint(output_file, print_string)    
#    
#    place = 0
#    last_val = 0
#    
#    for name in top_total_players:
#        if total_values[name] != last_val:
#            place += 1
#
#        fight_time_h = int(duration_fights_present[name]/3600)
#        fight_time_m = int((duration_fights_present[name] - fight_time_h*3600)/60)
#        fight_time_s = int(duration_fights_present[name] - fight_time_h*3600 - fight_time_m*60)
#        print_string = f"{place:>2}"+f". {name:<{name_length}} "+f" {profession_strings[name]:<{profession_length}} "
#        if fight_time_h > 0:
#            print_string += f" {fight_time_h:>2}h {fight_time_m:>2}m {fight_time_s:>2}s"
#        else:
#            print_string += f" {fight_time_m:>6}m {fight_time_s:>2}s"
#
#        if stat == "stab output":
#            print_string += f" {round(total_values[name], 2):>8}s"
#            average = round(total_values[name]/duration_fights_present[name], 2)
#            print_string += f" {average:>8}"
#        else:
#            print_string += f" {total_values[name]:>8}"
#        myprint(output_file, print_string)
#        last_val = total_values[name]
#
#    return top_total_players
    
if __name__ == '__main__':
    debug = False # enable / disable debug output

    parser = argparse.ArgumentParser(description='This reads a set of arcdps reports in xml format and generates top stats.')
    parser.add_argument('xml_directory', help='Directory containing .xml files from arcdps reports')
    parser.add_argument('-o', '--output', dest="output_filename", help="Text file to write the computed top stats")
    parser.add_argument('-l', '--log_file', dest="log_file", help="Logging file with all the output")
#    parser.add_argument('-d', '--duration', dest="minimum_duration", type=int, help="Minimum duration of a fight in s. Shorter fights will be ignored. Defaults to 30s.", default=30)
#    parser.add_argument('-a', '--ally_numbers', dest="minimum_ally_numbers", type=int, help="Minimum of allied players in a fight. Fights with less players will be ignored. Defaults to 10.", default=10)
#    parser.add_argument('-n', '--num_top_stats', dest="num_top_stats", type=int, help="Number of players that will be printed for achieving top <num_top_stats> for most stats. Special cases: Distance to tag and damage. Defaults to 5.", default=5)
#    parser.add_argument('-m', '--num_top_stats_dmg', dest="num_top_stats_dmg", type=int, help="Number of players that will be printed for achieving top <num_top_stats_dmg> damage. Defaults to 10.", default=10)    
#    parser.add_argument('-p', '--percentage_of_top', dest="percentage_of_top", type=int, help="Minimum percentage of the top player that has to be reached to get an award. Defaults to 50%.", default=50)    
    
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
        
    config = Config()
    config.num_players_listed = parser_config.num_players_listed # = Stats(parser_config.num_players_listed['dmg'], parser_config.num_players_listed['rips'], parser_config.num_players_listed['stab'], parser_config.num_players_listed['cleanses'], parser_config.num_players_listed['heal'], parser_config.num_players_listed['dist'], parser_config.num_players_listed['deaths'], parser_config.num_players_listed['kills'])
    config.num_players_considered_top = parser_config.num_players_considered_top #Stats(parser_config.num_players_considered_top['dmg'], parser_config.num_players_considered_top['rips'], parser_config.num_players_considered_top['stab'], parser_config.num_players_considered_top['cleanses'], parser_config.num_players_considered_top['heal'], parser_config.num_players_considered_top['dist'], parser_config.num_players_considered_top['deaths'], parser_config.num_players_considered_top['kills'])

    config.min_attendance_portion_for_late = parser_config.attendance_percentage_for_late/100.
    config.min_attendance_portion_for_buildswap = parser_config.attendance_percentage_for_buildswap/100.

    config.portion_of_top_for_consistent = parser_config.percentage_of_top_for_consistent/100.
    config.portion_of_top_for_total = parser_config.percentage_of_top_for_total/100.
    config.portion_of_top_for_late = parser_config.percentage_of_top_for_late/100.
    config.portion_of_top_for_buildswap = parser_config.percentage_of_top_for_buildswap/100.

    config.min_allied_players = parser_config.min_allied_players
    config.min_fight_duration = parser_config.min_fight_duration
    config.min_enemy_players = parser_config.min_enemy_players

    #output_file: str
    #input_dir: str

    print_string = "Using xml directory "+args.xml_directory+", writing output to "+args.output_filename+" and log to "+args.log_file
    print(print_string)
    print_string = "Considering fights with at least "+str(config.min_allied_players)+" allied players and at least "+str(config.min_enemy_players)+" that took longer than "+str(config.min_fight_duration)+" s."
    myprint(log, print_string)
    
    num_players_per_fight = list()

    # healing only in xml if addon was installed
    found_healing = False

    # overall stats over whole squad
    overall_squad_stats = {'dmg': 0., 'rips': 0., 'stab': 0., 'cleanses': 0., 'heal': 0., 'dist': 0., 'deaths': 0., 'kills': 0.}  # defaultdict(int)# #Stats(0,0,0,0,0,0,0,0)
    players = [] # list of all player/profession combinations
    player_index = {} # dictionary that matches each player/profession combo to its index in players list
    account_index = {} # dictionary that matches each account name to a list of its indices in players list
    
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

        # skip fights that last less than min_fight_duration seconds
        if(duration < config.min_fight_duration):
            log.write(print_string)
            print_string = "\nFight only took "+str(mins)+"m "+str(secs)+"s. Skipping fight."
            myprint(log, print_string)
            continue
        
        # skip fights with less than min_allied_players allies
        num_allies = len(xml_root.findall('players'))
        if num_allies < config.min_allied_players:
            log.write(print_string)
            print_string = "\nOnly "+str(num_allies)+" allied players involved. Skipping fight."
            myprint(log, print_string)
            continue

        # skip fights with less than min_enemy_players enemies
        num_enemies = len(xml_root.findall('targets')) # technically would need to check whether enemyPlayer == True
        #if num_enemies < config.min_enemy_players:
        #    log.write(print_string)
        #    print_string = "\nOnly "+str(num_enemies)+" enemies involved. Skipping fight."
        #    myprint(log, print_string)
        #    continue

        used_fights += 1
        used_fights_duration += duration
        num_players_per_fight.append(num_allies)

        # dictionaries for stats for each player in this fight
        damage_per_player = {}
        cleanses_per_player = {}
        strips_per_player = {}
        stab_per_player = {}
        healing_per_player = {}
        distance_per_player = {}
        deaths_per_player = {}
        kills_per_player = {}

        # get stats for each player
        for xml_player in xml_root.iter('players'):
            create_new_player = False
            build_swapped = False
            
            # get player name -> was present in this fight
            account = xml_player.find('account').text
            name = xml_player.find('name').text
            profession = xml_player.find('profession').text
            #if not profession in professions[name]:
            #    professions[name].append(profession)

            deaths = int(xml_player.find('defenses').find('deadCount').text)
            kills = int(xml_player.find('statsAll').find('killed').text)

            # get damage
            damage = int(xml_player.find('dpsAll').find('damage').text)

            # get strips and cleanses
            support_stats = xml_player.find('support')
            strips = int(support_stats.find('boonStrips').text)
            cleanses = int(support_stats.find('condiCleanse').text)

            # get stab in squad generation -> need to loop over all buff
            stab_generated = 0
            for buff in xml_player.iter('squadBuffs'):
                # find stab buff
                if buff.find('id').text != stab_id:
                    continue
                stab_generated = float(buff.find('buffData').find('generation').text)#Decimal
                break

            # check if healing was logged
            ext_healing_xml = xml_player.find('extHealingStats')
            healing = 0
            if(ext_healing_xml != None):
                found_healing = True
                for outgoing_healing_xml in ext_healing_xml.iter('outgoingHealingAllies'):
                    outgoing_healing_xml2 = outgoing_healing_xml.find('outgoingHealingAllies')
                    if not outgoing_healing_xml2 is None:
                        healing += int(outgoing_healing_xml2.find('healing').text)

            # get distance to tag
            distance = float(xml_player.find('statsAll').find('distToCom').text)#Decimal

            if debug:
                print(name)
                print("damage:",damage)
                print("strips:",strips)
                print("cleanses:",cleanses)
                print("stab:",stab_generated)
                print("healing:",healing)
                print(f"distance: {distance:.2f}")
                print("\n")
            
            name_and_prof = name+" "+profession
            if name_and_prof not in player_index.keys():
                print("creating new player")
                create_new_player = True
                
            if account not in account_index.keys():
                account_index[account] = [len(players)]
            else:
                for ind in range(len(account_index[account])):
                    print(ind)
                    print(account_index[account])
                    print(account_index[account][ind])
                    print(len(players))
                    print(players[account_index[account][ind]])
                    players[account_index[account][ind]].swapped_build = True
                if create_new_player:
                    account_index[account].append(len(players))
                build_swapped = True

            if create_new_player:
                player = Player()
                player.account = account
                player.name = name
                player.profession = profession
                player.total_stats = {'dmg': 0., 'rips': 0., 'stab': 0., 'cleanses': 0., 'heal': 0., 'dist': 0., 'deaths': 0., 'kills': 0.}
                player.consistency_stats = {'dmg': 0., 'rips': 0., 'stab': 0., 'cleanses': 0., 'heal': 0., 'dist': 0., 'deaths': 0., 'kills': 0.}
                player.percentage_top_stats = {'dmg': 0., 'rips': 0., 'stab': 0., 'cleanses': 0., 'heal': 0., 'dist': 0., 'deaths': 0., 'kills': 0.}                 
                player_index[name_and_prof] = len(players)
                players.append(player)
                

            damage_per_player[name_and_prof] = damage
            strips_per_player[name_and_prof] = strips
            stab_per_player[name_and_prof] = stab_generated
            cleanses_per_player[name_and_prof] = cleanses
            if found_healing:
                healing_per_player[name_and_prof] = healing
            if distance >= 0: # distance sometimes -1 for some reason
                distance_per_player[name_and_prof] = distance
            else:
                distance_per_player[name_and_prof] = -1
            deaths_per_player[name_and_prof] = deaths
            kills_per_player[name_and_prof] = kills                 

            #player = players[-1]
            print("present:", players[player_index[name_and_prof]].num_fights_present)
            players[player_index[name_and_prof]].num_fights_present += 1
            players[player_index[name_and_prof]].duration_fights_present += duration
            players[player_index[name_and_prof]].swapped_build |= build_swapped
            players[player_index[name_and_prof]].total_stats['dmg'] += damage
            players[player_index[name_and_prof]].total_stats['rips'] += strips
            players[player_index[name_and_prof]].total_stats['stab'] += stab_generated*duration
            players[player_index[name_and_prof]].total_stats['cleanses'] += cleanses
            if found_healing:
                players[player_index[name_and_prof]].total_stats['heal'] += healing
            if distance > 0: # distance sometimes player_index[name_and_prof] for some reason
                players[player_index[name_and_prof]].total_stats['dist'] += distance
            players[player_index[name_and_prof]].total_stats['deaths'] += deaths
            players[player_index[name_and_prof]].total_stats['kills'] += kills
            #players[player_index[name_and_prof]] = player
                        
            #players[-1].num_fights_present += 1
            #players[-1].duration_fights_present += duration
            #players[-1].swapped_build |= build_swapped
            #players[-1].total_stats.dmg += damage
            #players[-1].total_stats['rips'] += strips
            #players[-1].total_stats['stab'] += stab_generated*duration
            #players[-1].total_stats['cleanses'] += cleanses
            #if found_healing:
            #    players[-1].total_stats['heal'] += heal
            #if distance > 0: # distance sometimes -1 for some reason
            #    players[-1].total_stats['dist'] += distance
            #players[-1].total_stats['deaths'] += deaths
            #players[-1].total_stats['kills'] += kills                 


            # deaths and kills
            #overall_squad_stats = Stats(overall_squad_stats.dmg + damage, overall_squad_stats.rips + strips, overall_squad_stats.stab + stab_generated*duration,
            #                            overall_squad_stats.cleanses + cleanses, overall_squad_stats.heal + healing, overall_squad_stats.dist + distance,
            #                            overall_squad_stats.deaths + deaths, overall_squad_stats.kills + kills)
            overall_squad_stats['dmg'] += damage
            overall_squad_stats['rips'] += strips
            overall_squad_stats['stab'] += stab_generated*duration
            overall_squad_stats['cleanses'] += cleanses
            overall_squad_stats['heal'] += healing
            overall_squad_stats['dist'] += distance
            overall_squad_stats['deaths'] += deaths
            overall_squad_stats['kills'] += kills

            
        # create dictionaries sorted according to stats
        sortedDamage = sorted(damage_per_player, key=damage_per_player.get, reverse=True)
        sortedStrips = sorted(strips_per_player, key=strips_per_player.get, reverse=True)
        sortedCleanses = sorted(cleanses_per_player, key=cleanses_per_player.get, reverse=True)
        sortedStab = sorted(stab_per_player, key=stab_per_player.get, reverse=True)
        sortedHealing = sorted(healing_per_player, key=healing_per_player.get, reverse=True)
        # small distance = good -> don't reverse sorting. Need to check for -1 -> keep values
        sortedDistance = sorted(distance_per_player.items(), key=lambda x:x[1])
        sortedDeaths = sorted(deaths_per_player, key=deaths_per_player.get, reverse=True)
        sortedKills = sorted(kills_per_player, key=kills_per_player.get, reverse=True)        

        if debug:
            print("sorted dmg:", sortedDamage,"\n")
            print("sorted strips:", sortedStrips,"\n")
            print("sorted cleanses:",sortedCleanses,"\n")
            print("sorted stab:", sortedStab,"\n")
            print("sorted healing:", sortedHealing,"\n")
            print("sorted distance:", sortedDistance, "\n")
        
        # increase number of times top x was achieved for top x players in each stat
        increase_top_x_reached(players, sortedDamage, player_index, config, 'dmg')
        increase_top_x_reached(players, sortedStrips, player_index, config, 'rips')
        increase_top_x_reached(players, sortedStab, player_index, config, 'stab')
        increase_top_x_reached(players, sortedCleanses, player_index, config, 'cleanses')
        increase_top_x_reached(players, sortedHealing, player_index, config, 'heal')
        increase_top_x_reached(players, sortedDistance, player_index, config, 'dist')
        increase_top_x_reached(players, sortedDeaths, player_index, config, 'deaths')
        increase_top_x_reached(players, sortedKills, player_index, config, 'kills')        
    
        # get top x+1 for distance bc first is always the com. Also throw out negative distance.


    attendance_percentage = {}
    for player in players:
        player.attendance_percentage = player.num_fights_present / used_fights*100
        #attendance_percentage[name] = int(num_fights_present[name]/used_fights*100)

    #get total duration in h, m, s
    total_fight_duration = {}
    total_fight_duration["h"] = int(used_fights_duration/3600)
    total_fight_duration["m"] = int((used_fights_duration - total_fight_duration["h"]*3600) / 60)
    total_fight_duration["s"] = int(used_fights_duration - total_fight_duration["h"]*3600 -  total_fight_duration["m"]*60)

    total_stab_duration = {}
    total_stab_duration["h"] = int(overall_squad_stats['stab']/3600)
    total_stab_duration["m"] = int((overall_squad_stats['stab'] - total_stab_duration["h"]*3600)/60)
    total_stab_duration["s"] = int(overall_squad_stats['stab'] - total_stab_duration["h"]*3600 - total_stab_duration["m"]*60)    
    
    # print top x players for all stats. If less then x
    # players, print all. If x-th place doubled, print all with the
    # same amount of top x achieved.

    myprint(log, "\n")

    print_string = "Welcome to the CARROT AWARDS!\n"
    myprint(output, print_string)
    
    print_string = "The following stats are computed over "+str(used_fights)+" out of "+str(total_fights)+" fights.\n"# fights with a total duration of "+used_fights_duration+".\n"
    myprint(output, print_string)

    # print total squad stats
    print_string = "Squad overall did "+str(overall_squad_stats['dmg'])+" damage, ripped "+str(overall_squad_stats['rips'])+" boons, cleansed "+str(overall_squad_stats['cleanses'])+" conditions, \ngenerated "
    if total_stab_duration["h"] > 0:
        print_string += str(total_stab_duration["h"])+"h "
    print_string += str(total_stab_duration["m"])+"m "+str(total_stab_duration["s"])+"s of stability"        
    if found_healing:
        print_string += ", healed for "+str(overall_squad_stats['heal'])
    print_string += ", \nkilled "+str(overall_squad_stats['kills'])+" enemies and had "+str(overall_squad_stats['deaths'])+" deaths \nover a total time of "
    if total_fight_duration["h"] > 0:
        print_string += str(total_fight_duration["h"])+"h "
    print_string += str(total_fight_duration["m"])+"m "+str(total_fight_duration["s"])+"s in "+str(used_fights)+" fights.\n"
    print_string += "There were between "+str(min(num_players_per_fight))+" and "+str(max(num_players_per_fight))+" allied players involved.\n"    
        
    myprint(output, print_string)

    
    myprint(output, "DAMAGE AWARDS\n")
    #top_consistent_damagers = write_sorted_top_x(output, top_damage_x_times, total_damage, professions, num_fights_present, used_fights, "damage", args.num_top_stats_dmg, top_percentage_frac)
    top_consistent_damagers = write_sorted_top_x(players, config, used_fights, 'dmg', output)
#    top_total_damagers = write_sorted_total(output, total_damage, professions, duration_fights_present, total_fight_duration, "damage", args.num_top_stats_dmg, top_percentage_frac)
    myprint(output, "\n")    
        
    myprint(output, "BOON STRIPS AWARDS\n")        
    top_consistent_strippers = write_sorted_top_x(players, config, used_fights, 'rips', output)
#    top_consistent_strippers = write_sorted_top_x(output, top_strips_x_times, total_strips, professions, num_fights_present, used_fights, "strips", args.num_top_stats, top_percentage_frac)    
##    top_total_strippers = write_sorted_total(output, total_strips, professions, duration_fights_present, total_fight_duration, "strips", args.num_top_stats, top_percentage_frac)
    myprint(output, "\n")            

    myprint(output, "CONDITION CLEANSES AWARDS\n")        
    top_consistent_cleansers = write_sorted_top_x(players, config, used_fights, 'cleanses', output)
#    top_consistens_cleaners = write_sorted_top_x(output, top_cleanses_x_times, total_cleanses, professions, num_fights_present, used_fights, "cleanses", args.num_top_stats, top_percentage_frac)
##    top_total_cleaners = write_sorted_total(output, total_cleanses, professions, duration_fights_present, total_fight_duration, "cleanses", args.num_top_stats, top_percentage_frac)
    myprint(output, "\n")    
        
    myprint(output, "STABILITY OUTPUT AWARDS \n")        
    top_consistent_stabbers = write_sorted_top_x(players, config, used_fights, 'stab', output)
#    top_consistent_stabbers = write_sorted_top_x(output, top_stab_x_times, total_stab, professions, num_fights_present, used_fights, "stab output", args.num_top_stats, top_percentage_frac)        
##    top_total_stabbers = write_sorted_total(output, total_stab, professions, duration_fights_present, total_fight_duration, "stab output", args.num_top_stats, top_percentage_frac)
    myprint(output, "\n")    

    top_consistent_healers = list()
#    top_total_healers = list()    
    if found_healing:
        myprint(output, "HEALING AWARDS\n")        
        top_consistent_healers = write_sorted_top_x(players, config, used_fights, 'heal', output)        
#        top_consistent_healers = write_sorted_top_x(output, top_healing_x_times, total_healing, professions, num_fights_present, used_fights, "healing", args.num_top_stats, top_percentage_frac)
# #       top_total_healers = write_sorted_total(output, total_healing, professions, duration_fights_present, total_fight_duration, "healing", args.num_top_stats, top_percentage_frac)
        myprint(output, "\n")    

    myprint(output, "SHORTEST DISTANCE TO TAG AWARDS\n")
    top_consistent_distancers = write_sorted_top_x(players, config, used_fights, 'dist', output)            
#    top_consistent_distancers = write_sorted_top_x(output, top_distance_x_times, total_distance, professions, num_fights_present, used_fights, "distance", args.num_top_stats, top_percentage_frac)
#    # distance to tag total doesn't make much sense
#    myprint(output, "\n")
#    
##    myprint(output, 'SPECIAL "LATE BUT GREAT" MENTIONS\n')        
##    write_sorted_top_x_percentage(output, top_damage_x_times, total_damage, num_fights_present, used_fights, professions, "damage", top_consistent_damagers, top_total_damagers)
##    write_sorted_top_x_percentage(output, top_strips_x_times, total_strips, num_fights_present, used_fights, professions, "strips", top_consistent_strippers, top_total_strippers)
##    write_sorted_top_x_percentage(output, top_cleanses_x_times, total_cleanses, num_fights_present, used_fights, professions, "cleanses", top_consistens_cleaners, top_total_cleaners)
##    write_sorted_top_x_percentage(output, top_stab_x_times, total_stab, num_fights_present, used_fights, professions, "stab", top_consistent_stabbers, top_total_stabbers)
##    write_sorted_top_x_percentage(output, top_healing_x_times, total_healing, num_fights_present, used_fights, professions, "healing", top_consistent_healers, top_total_healers)        
##    write_sorted_top_x_percentage(output, top_distance_x_times, total_distance, num_fights_present, used_fights, professions, "distance", top_consistent_distancers)        

