#!/usr/bin/env python3

import argparse
import collections
import os.path
from os import listdir
import sys
import xml.etree.ElementTree as ET
from decimal import *


profession_abbreviations = {}
profession_abbreviations["Guardian"] = "Guard"
profession_abbreviations["Dragonhunter"] = "DH"
profession_abbreviations["Firebrand"] = "FB"
profession_abbreviations["Willbender"] = "WB"

profession_abbreviations["Revenant"] = "Rev"
profession_abbreviations["Herald"] = "Herald"
profession_abbreviations["Renegade"] = "Ren"
profession_abbreviations["Vindicator"] = "Vin"    

profession_abbreviations["Warrior"] = "Warrior"
profession_abbreviations["Berserker"] = "Berserker"
profession_abbreviations["Spellbreaker"] = "SpB"
profession_abbreviations["Bladesworn"] = "Bl"

profession_abbreviations["Engineer"] = "Engy"
profession_abbreviations["Scrapper"] = "Scrap"
profession_abbreviations["Holosmith"] = "Holo"
profession_abbreviations["Mechanist"] = "Mec"    

profession_abbreviations["Ranger"] = "Ranger"
profession_abbreviations["Druid"] = "Druid"
profession_abbreviations["Soulbeast"] = "Soulbeast"
profession_abbreviations["Untamed"] = "UT"    

profession_abbreviations["Thief"] = "Th"
profession_abbreviations["Daredevil"] = "DD"
profession_abbreviations["Deadeye"] = "Deadeye"
profession_abbreviations["Specter"] = "Spe"

profession_abbreviations["Elementalist"] = "Ele"
profession_abbreviations["Tempest"] = "Tempest"
profession_abbreviations["Weaver"] = "Weaver"
profession_abbreviations["Catalyst"] = "Cata"

profession_abbreviations["Mesmer"] = "Mes"
profession_abbreviations["Chronomancer"] = "Chrono"
profession_abbreviations["Mirage"] = "Mir"
profession_abbreviations["Virtuoso"] = "Vir"
    
profession_abbreviations["Necromancer"] = "Necro"
profession_abbreviations["Reaper"] = "Reaper"
profession_abbreviations["Scourge"] = "Scourge"
profession_abbreviations["Harbinger"] = "Harbinger"



def myprint(output_file, output_string):
    print(output_string)
    output_file.write(output_string+"\n")

    
def get_name_and_professions(name, professions):
    name_and_professions = name+" ("
    for p in range(len(professions[name])-1):
        name_and_professions += profession_abbreviations[professions[name][p]]+" / "
    name_and_professions += profession_abbreviations[professions[name][-1]]+")"
    return name_and_professions


def get_professions(name, profession_dict):
    professions = ""
    for p in range(len(profession_dict[name])-1):
        professions += profession_abbreviations[profession_dict[name][p]]+" / "
    professions += profession_abbreviations[profession_dict[name][-1]]
    return professions


def get_topx_consistent_players(sorted_topx, total_values, stat, num_top_stats):
    i = 0
    top = total_values[sorted_topx[i][0]]
    top_consistent_players = list()
    name_length = 0

    # 1) index must be lower than length of the list
    # 2) index must be lower than number of output desired OR list entry has same value as previous entry, i.e. double place
    # 3) value must be greater than 0    
    while i < len(sorted_topx) and (i < num_top_stats or sorted_topx[i][1] == sorted_topx[i-1][1]) and sorted_topx[i][1] > 0:
        name = sorted_topx[i][0]
        if stat == "distance":
            top_consistent_players.append(name)
            if len(name) > name_length:
                name_length = len(name)
        elif total_values[name] > top * Decimal(0.5):
            # 4) value must be at least 50% of top value for everything except distance
            top_consistent_players.append(name)
            if len(name) > name_length:
                name_length = len(name)
        i += 1
    return top_consistent_players, name_length


def get_topx_total_players(sorted_total_values, num_top_stats):
    i = 0
    top = sorted_total_values[i][1]
    top_total_players = list()
    name_length = 0
    
    # 1) index must be lower than length of the list and desired number of players listed
    # 2) value must be greater than 0
    # 3) value must be at least 50% of top value        
    while i < min(len(sorted_total_values), num_top_stats) and sorted_total_values[i][1] > 0 and sorted_total_values[i][1] > top * Decimal(0.5):
        name = sorted_total_values[i][0]
        top_total_players.append(name)
        if len(name) > name_length:
            name_length = len(name)
        i += 1
    return top_total_players, name_length


def get_topx_percentage_players(sorted_percentages, comparison_percentage, top_player, num_total_fights):
    i = 0
    top = sorted_percentages[i][1]
    top_percentage_players = list()
    name_length = 0
    
    # 1) index must be lower than length of the list
    # 2) percentage value must be at least top percentage value
    while i < len(sorted_percentages) and sorted_percentages[i][1] >= comparison_percentage: #*0.5:
        if sorted_percentages[i][0] == top_player:
            i += 1
            continue
        name = sorted_percentages[i][0]
        if num_fights_present[name] < num_total_fights and num_fights_present[name] > 0.5*num_total_fights:
            top_percentage_players.append(name)
            if len(name) > name_length:
                name_length = len(name)
        i += 1
    return top_percentage_players, name_length


def get_profession_and_length(names, professions):
    profession_strings = {}
    profession_length = 0
    for name in names:
        professions_str = get_professions(name, professions)
        profession_strings[name] = professions_str
        if len(professions_str) > profession_length:
            profession_length = len(professions_str)
    return profession_strings, profession_length


# Write the top x people who achieved top x in stat most often.
# Input:
# topx_x_times = how often did each player achieve a top x spot in this stat
# total_values = what's the summed up value over all fights for this stat for each player
# stat = which stat are we looking at (dmg, cleanses, ...)
# num_top_stats = number of players to print
def write_sorted_top_x(output_file, topx_x_times, total_values, professions, attendance_percentage, stat, num_top_stats):
    if len(topx_x_times) == 0:
        return

    # sort players according to number of times top x was achieved for stat
    sorted_topx = sorted(topx_x_times.items(), key=lambda x:x[1], reverse=True)

    if stat == "distance":
        print_string = "Top "+str(num_top_stats)+" "+stat+" consistency awards"
    else:
        print_string = "Top "+stat+" consistency awards (Max. "+str(num_top_stats)+" people, min. 50% of most consistent)"
    myprint(output_file, print_string)
    print_string = "Most times placed in the top "+str(num_top_stats)
    myprint(output_file, print_string)
    print_string = "------------------------------------------------------------------------"
    myprint(output_file, print_string)

    top = total_values[sorted_topx[0][0]] 

    # get names that get on the list and their professions
    top_consistent_players, name_length = get_topx_consistent_players(sorted_topx, total_values, stat, num_top_stats)
    profession_strings, profession_length = get_profession_and_length(top_consistent_players, professions)

    print_string = f"    {'Name':<{name_length}}" + f"  {'Class':<{profession_length}} "+f" Attendance " + " Times"
    if stat != "distance":
        print_string += f" {'Total':>8}"
    myprint(output_file, print_string)    

    
    place = 0
    last_val = 0
    
    for name in top_consistent_players:
        if topx_x_times[name] != last_val:
            place += 1
        print_string = f"{place:>2}"+f". {name:<{name_length}} "+f" {profession_strings[name]:<{profession_length}} "+f" {attendance_percentage[name]:>9}% "+f" {topx_x_times[name]:>5}"
        if stat != "distance":
            print_string += f" {total_values[name]:>8}"
            #print_string += " | total "+str(total_values[name])
        myprint(output_file, print_string)
        last_val = topx_x_times[name]
        
                
# Write the top x people who achieved top x in stat with the highest percentage. This only considers fights where each player was present, i.e., a player who was in 4 fights and achieved a top x spot in 2 of them gets 50%, as does a player who was only in 2 fights and achieved a top x spot in 1 of them.
# Input:
# topx_x_times = how often did each player achieve a topx spot in this stat
# num_fights_present = in how many fights was the player present
# stat = which stat are we looking at (dmg, cleanses, ...)
def write_sorted_top_x_percentage(output_file, topx_x_times, num_fights_present, num_total_fights, professions, stat):
    if len(topx_x_times) == 0:
        return
    
    percentages = {}
    for name in topx_x_times.keys():
        percentages[name] = topx_x_times[name] / num_fights_present[name]
    sorted_percentages = sorted(percentages.items(), key=lambda x:x[1], reverse=True)

    # get names that get on the list and their professions
    sorted_topx = sorted(topx_x_times.items(), key=lambda x:x[1], reverse=True)    
    comparison_percentage = sorted_topx[0][1]/num_fights_present[sorted_topx[0][0]]
    top_player = sorted_topx[0][0]
    top_percentage_players, name_length = get_topx_percentage_players(sorted_percentages, comparison_percentage, top_player, num_total_fights)
    profession_strings, profession_length = get_profession_and_length(top_percentage_players, professions)

    place = 0
    last_val = 0

    if len(top_percentage_players) > 0:
        print_string = "\nTop "+stat+" percentage (Min. top consistent player percentage = "+f"{comparison_percentage*100:.0f}%)"
        myprint(output_file, print_string)
        print_string = "------------------------------------------------------------------------"                
        myprint(output_file, print_string)                
        print_string = f"    {'Name':<{name_length}}" + f"  {'Class':<{profession_length}} "+f"  Percentage "+f" {'Times':>5} " + f"{'out of':>6}"
        myprint(output_file, print_string)    
    
    for name in top_percentage_players:
        if percentages[name] != last_val:
            place += 1
        percentage = int(percentages[name]*100)
        print_string = f"{place:>2}"+f". {name:<{name_length}} "+f" {profession_strings[name]:<{profession_length}} " +f" {percentage:>10}% " +f"{topx_x_times[name]:>5}" +f"{num_fights_present[name]:>6}"
        myprint(output_file, print_string)
        last_val = percentages[name]
    

# Write the top x people who achieved top total stat.
# Input:
# total_values = stat summed up over all fights
# stat = which stat are we looking at (dmg, cleanses, ...)
# num_top_stats = number of players to print
def write_sorted_total(output_file, total_values, professions, attendance_percentage, stat, num_top_stats = 3):
    if len(total_values) == 0:
        return

    sorted_total_values = sorted(total_values.items(), key=lambda x:x[1], reverse=True)    

    print_string = "\nTop overall "+stat+" awards (Max. "+str(num_top_stats)+" people, min. 50% of 1st place)"
    myprint(output_file, print_string)
    print_string = "------------------------------------------------------------------------"                
    myprint(output_file, print_string)

    top_total_players, name_length = get_topx_total_players(sorted_total_values, num_top_stats)
    profession_strings, profession_length = get_profession_and_length(top_total_players, professions)

    print_string = f"    {'Name':<{name_length}}" + f"  {'Class':<{profession_length}} "+f" Attendance"+f" {'Total':>8}"
    myprint(output_file, print_string)    
    
    place = 0
    last_val = 0
    
    for name in top_total_players:
        if total_values[name] != last_val:
            place += 1
        print_string = f"{place:>2}"+f". {name:<{name_length}} "+f" {profession_strings[name]:<{profession_length}} "+f" {attendance_percentage[name]:>9}% "+f"{total_values[name]:>8}"
        myprint(output_file, print_string)
        last_val = total_values[name]
    
    
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
    parser.add_argument('-p', '--print_percentage', dest="print_percentage", action='store_false', help="Disable printing players with the top percentage of reaching top x stats.")    
    
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

    num_fights_present = collections.defaultdict(int)
    professions = collections.defaultdict(list)
    
    stab_id = "1122"
    used_fights = 0
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

        # dictionaries for stats for each player in this fight
        damage = {}
        cleanses = {}
        strips = {}
        stab = {}
        healing = {}
        distance = {}

        # healing only in xml if addon was installed
        found_healing = False
        
        # get stats for each player
        for xml_player in xml_root.iter('players'):
            # get player name -> was present in this fight
            name_xml = xml_player.find('name')
            name = name_xml.text
            num_fights_present[name] += 1
            profession = xml_player.find('profession').text
            if not profession in professions[name]:
                professions[name].append(profession)
            #print(professions[name])

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
            total_stab[name] += stab[name]
            if found_healing:
                total_healing[name] += healing[name]
            # distance sometimes -1 for some reason
            if distance[name] >= 0:
                total_distance[name] += distance[name]
            
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

    # print top x players for all stats. If less then x
    # players, print all. If x-th place doubled, print all with the
    # same amount of top x achieved.

    myprint(log, "\n")

    print_string = "Welcome to the CARROT AWARDS!\n"
    myprint(output, print_string)
    
    print_string = "The following stats are computed over "+str(used_fights)+" out of "+str(total_fights)+" fights.\n"
    myprint(output, print_string)

    myprint(output, "DAMAGE AWARDS\n")
    write_sorted_top_x(output, top_damage_x_times, total_damage, professions, attendance_percentage, "damage", args.num_top_stats_dmg)
    write_sorted_total(output, total_damage, professions, attendance_percentage, "damage", args.num_top_stats_dmg)
    myprint(output, "\n")    
        
    myprint(output, "BOON STRIPS AWARDS\n")        
    write_sorted_top_x(output, top_strips_x_times, total_strips, professions, attendance_percentage, "strips", args.num_top_stats)
    write_sorted_total(output, total_strips, professions, attendance_percentage, "strips", args.num_top_stats)
    myprint(output, "\n")            

    myprint(output, "CONDITION CLEANSES AWARDS\n")        
    write_sorted_top_x(output, top_cleanses_x_times, total_cleanses, professions, attendance_percentage, "cleanses", args.num_top_stats)
    write_sorted_total(output, total_cleanses, professions, attendance_percentage, "cleanses", args.num_top_stats)
    myprint(output, "\n")    
        
    myprint(output, "STABILITY OUTPUT AWARDS \n")        
    write_sorted_top_x(output, top_stab_x_times, total_stab, professions, attendance_percentage, "stab output", args.num_top_stats)        
    write_sorted_total(output, total_stab, professions, attendance_percentage, "stab output", args.num_top_stats)
    myprint(output, "\n")    
        
    myprint(output, "HEALING AWARDS\n")        
    write_sorted_top_x(output, top_healing_x_times, total_healing, professions, attendance_percentage, "healing", args.num_top_stats)
    write_sorted_total(output, total_healing, professions, attendance_percentage, "healing", args.num_top_stats)
    myprint(output, "\n")    

    myprint(output, "SHORTEST DISTANCE TO TAG AWARDS\n")        
    write_sorted_top_x(output, top_distance_x_times, total_distance, professions, attendance_percentage, "distance", args.num_top_stats)
    # distance to tag total doesn't make much sense
    myprint(output, "\n")
    
    if args.print_percentage:
        myprint(output, 'SPECIAL "LATE BUT GREAT" MENTIONS\n')        
        write_sorted_top_x_percentage(output, top_damage_x_times, num_fights_present, used_fights, professions, "damage")
        write_sorted_top_x_percentage(output, top_strips_x_times, num_fights_present, used_fights, professions, "strips")
        write_sorted_top_x_percentage(output, top_cleanses_x_times, num_fights_present, used_fights, professions, "cleanses")
        write_sorted_top_x_percentage(output, top_stab_x_times, num_fights_present, used_fights, professions, "stab")
        write_sorted_top_x_percentage(output, top_healing_x_times, num_fights_present, used_fights, professions, "healing")        
        write_sorted_top_x_percentage(output, top_distance_x_times, num_fights_present, used_fights, professions, "distance")        
