#!/usr/bin/env python3

import argparse
import collections
import os.path
from os import listdir
import sys
import xml.etree.ElementTree as ET
from decimal import *

def myprint(output_file, output_string):
    print(output_string)
    output_file.write(output_string+"\n")

# Write the top x people who achieved top x in stat most often.
# Input:
# topx_x_times = how often did each player achieve a top x spot in this stat
# total_values = what's the summed up value over all fights for this stat for each player
# stat = which stat are we looking at (dmg, cleanses, ...)
# num_top_stats = number of players to print
# omit = omit the first n players in the list. Mostly used for dist to tag since closest is always the com. Add corresponding number of players at the end, i.e., if omit = 1, print players that had top x stat 2nd to x+1th most often.
def write_sorted_top_x(output_file, topx_x_times, total_values, stat, num_top_stats, omit = 0):
    if len(topx_x_times) <= omit:
        return

    # sort players according to number of times top x was achieved for stat
    sorted_topx = sorted(topx_x_times.items(), key=lambda x:x[1], reverse=True)

    if stat == "dist":
        print_string = "Top "+str(num_top_stats)+" "+stat+" consistency"
    else:
        print_string = "Top "+stat+" Consistency (Max. "+str(num_top_stats)+" people, min 50% of most consistent)"
    myprint(output_file, print_string)
    print_string = "Reached top "+str(num_top_stats)+" in x fights"
    myprint(output_file, print_string)

    i = omit
    top = total_values[sorted_topx[i][0]] #sorted_topx[i][1]

    # 1) index must be lower than length of the list
    # 2) index must be lower than number of output desired + number of omitted entries (don't output more than desired number of players) OR list entry has same value as previous entry, i.e. double place
    # 3) value must be greater than 0
    while i < len(sorted_topx) and (i < num_top_stats+omit or sorted_topx[i][1] == sorted_topx[i-1][1]) and sorted_topx[i][1] > 0:
        if stat == "dist":
            print_string = sorted_topx[i][0]+": "+str(sorted_topx[i][1])
        # 4) value must be at least 50% of top value for everything except dist
        elif total_values[sorted_topx[i][0]] > top * Decimal(0.5):
            print_string = sorted_topx[i][0]+": "+str(sorted_topx[i][1])+" (total "+str(total_values[sorted_topx[i][0]])+")"
        else:
            break
        myprint(output_file, print_string)
        i += 1
    myprint(output_file, "\n")

# Write the top x people who achieved top x in stat with the highest percentage. This only considers fights where each player was present, i.e., a player who was in 4 fights and achieved a top x spot in 2 of them gets 50%, as does a player who was only in 2 fights and achieved a top x spot in 1 of them.
# Input:
# topx_x_times = how often did each player achieve a topx spot in this stat
# num_fights_present = in how many fights was the player present
# stat = which stat are we looking at (dmg, cleanses, ...)
# num_top_stats = number of players to print
# omit = omit the first x player in the list. Mostly used for dist to tag since closest is always the com. Add corresponding number of players at the end, i.e., if omit = 1, print players that had top x stat 2nd to 4th most often.    
def write_sorted_top_x_percentage(output_file, topx_x_times, num_fights_present, stat, num_top_stats, omit = 0):
    if len(topx_x_times) == 0:
        return

    percentages = {}
    for name in topx_x_times.keys():
        percentages[name] = topx_x_times[name] / num_fights_present[name]
    sorted_percentages = sorted(percentages.items(), key=lambda x:x[1], reverse=True)

    print_string = "Top "+stat+" percentage (Max. " +str(num_top_stats)+" people, min 50% of top percentage)"
    myprint(output_file, print_string)
    print_string = "Achieved top "+str(num_top_stats)+" in x% of the fights they were in"
    myprint(output_file, print_string)    

    i = omit
    top = sorted_percentages[i][1]

    # 1) index must be lower than length of the list
    # 2) index must be lower than number of output desired + number of omitted entries (don't output more than desired number of players) OR list entry has same value as previous entry, i.e. double place
    # x) value must be greater than 0
    # 4) percentage value must be at least 50% of top percentage value
    while i < len(sorted_percentages) and (i < num_top_stats+omit or sorted_percentages[i][1] == sorted_percentages[i-1][1]) and sorted_percentages[i][1] > 0 and sorted_percentages[i][1] > top * 0.5:
        name = sorted_percentages[i][0]
        print_string = name+f": {sorted_percentages[i][1]*100:.0f}% ("+str(topx_x_times[name])+" / " + str(num_fights_present[name]) +")"
        myprint(output_file, print_string)
        i += 1
    myprint(output_file, "\n")
    
# Write the top x people who achieved top total stat.
# Input:
# total_values = stat summed up over all fights
# stat = which stat are we looking at (dmg, cleanses, ...)
# num_top_stats = number of players to print
def write_sorted_total(output_file, total_values, stat, num_top_stats = 3):
    if len(total_values) == 0:
        return

    sorted_total_values = sorted(total_values.items(), key=lambda x:x[1], reverse=True)    

    print_string = "Top overall "+stat+" (Max. "+str(num_top_stats)+" people, min 50% of 1st place)"
    myprint(output_file, print_string)
    i = 0
    top = sorted_total_values[i][1]

    # 1) index must be lower than length of the list and desired number of players listed
    # 2) value must be greater than 0
    # 3) value must be at least 50% of top value        
    while i < min(len(sorted_total_values), num_top_stats) and sorted_total_values[i][1] > 0 and sorted_total_values[i][1] > top * Decimal(0.5):
        print_string = sorted_total_values[i][0]+": "+str(sorted_total_values[i][1])
        myprint(output_file, print_string)
        i += 1
    myprint(output_file, "\n")
    
if __name__ == '__main__':
    debug = False # enable / disable debug output

    parser = argparse.ArgumentParser(description='This reads a set of arcdps reports in xml format and generates top stats.')
    parser.add_argument('xml_directory', help='Directory containing .xml files from arcdps reports')
    parser.add_argument('-o', '--output', dest="output_filename", help="Text file to write the computed top stats")
    parser.add_argument('-l', '--log_file', dest="log_file", help="Logging file with all the output")
    parser.add_argument('-d', '--duration', dest="minimum_duration", type=int, help="Minimum duration of a fight in s. Shorter fights will be ignored. Defaults to 30s.", default=30)
    parser.add_argument('-a', '--ally_numbers', dest="minimum_ally_numbers", type=int, help="Minimum of allied players in a fight. Fights with less players will be ignored. Defaults to 10.", default=10)
    parser.add_argument('-n', '--num_top_stats', dest="num_top_stats", type=int, help="Number of players that will be printed for achieving top <num_top_stats> for most stats. Special cases: Distance to tag and damage. Defaults to 5.", default=5)
    parser.add_argument('-m', '--num_top_stats_dmg_dist', dest="num_top_stats_dmg_dist", type=int, help="Number of players that will be printed for achieving top <num_top_stats_dmg_dist> damage and distance to tag. Defaults to 10.", default=10)    
    parser.add_argument('-p', '--print_percentage', dest="print_percentage", action='store_true', help="Print players with the top percentage of reaching top x stats. Defaults to False.")    
    
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
    myprint(log, print_string)
    print_string = "Considering fights with more than "+str(args.minimum_ally_numbers)+" allied players that took longer than "+str(args.minimum_duration)+" s."
    myprint(log, print_string)
        
    top_damage_x_times = collections.defaultdict(int)
    top_strips_x_times = collections.defaultdict(int)
    top_cleanses_x_times = collections.defaultdict(int)
    top_stab_x_times = collections.defaultdict(int)
    top_healing_x_times = collections.defaultdict(int)
    top_dist_x_times = collections.defaultdict(int)

    total_damage = collections.defaultdict(int)
    total_strips = collections.defaultdict(int)
    total_cleanses = collections.defaultdict(int)
    total_stab = collections.defaultdict(int)
    total_healing = collections.defaultdict(int)    
    total_dist = collections.defaultdict(int)

    num_fights_present = collections.defaultdict(int)
    
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
        dist = {}

        # healing only in xml if addon was installed
        found_healing = False
        
        # get stats for each player
        for xml_player in xml_root.iter('players'):
            # get player name -> was present in this fight
            name_xml = xml_player.find('name')
            name = name_xml.text
            num_fights_present[name] += 1

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

            # get dist to tag
            dist_xml = xml_player.find('statsAll').find('distToCom')
            dist[name] = Decimal(dist_xml.text)

            if debug:
                print(name)
                print("damage:",damage[name])
                print("strips:",strips[name])
                print("cleanses:",cleanses[name])
                print("stab:",stab_generated)
                print("healing:",healing[name])
                print(f"dist: {dist[name]:.2f}")
                print("\n")
                
            # add new data from this fight to total stats
            total_damage[name] += damage[name]
            total_strips[name] += strips[name]
            total_cleanses[name] += cleanses[name]
            total_stab[name] += stab[name]
            if found_healing:
                total_healing[name] += healing[name]
            # dist sometimes -1 for some reason
            if dist[name] >= 0:
                total_dist[name] += dist[name]
            
        #print("\n")

        # create dictionaries sorted according to stats
        sortedDamage = sorted(damage, key=damage.get, reverse=True)
        sortedStrips = sorted(strips, key=strips.get, reverse=True)
        sortedCleanses = sorted(cleanses, key=cleanses.get, reverse=True)
        sortedStab = sorted(stab, key=stab.get, reverse=True)
        sortedHealing = sorted(healing, key=healing.get, reverse=True)
        # small dist = good -> don't reverse sorting. Need to check for -1 -> keep values
        sortedDist = sorted(dist.items(), key=lambda x:x[1])

        if debug:
            print("sorted dmg:", sortedDamage,"\n")
            print("sorted strips:", sortedStrips,"\n")
            print("sorted cleanses:",sortedCleanses,"\n")
            print("sorted stab:", sortedStab,"\n")
            print("sorted healing:", sortedHealing,"\n")
            print("sorted dist:", sortedDist, "\n")
        
        # increase number of times top x was achieved for top x players in each stat
        for i in range(min(len(sortedDamage), args.num_top_stats_dmg_dist)):
            top_damage_x_times[sortedDamage[i]] += 1
            
        for i in range(min(len(sortedStrips), args.num_top_stats)):
            top_strips_x_times[sortedStrips[i]] += 1
            top_cleanses_x_times[sortedCleanses[i]] += 1
            top_stab_x_times[sortedStab[i]] += 1

        # might not have entries for healing -> separate loop
        for i in range(min(len(sortedHealing), args.num_top_stats)):
            top_healing_x_times[sortedHealing[i]] += 1

        # get top x+1 for dist bc first is always the com. Also throw out negative dist.
        valid_dist = 0
        i = 0
        while i < len(sortedDist) and valid_dist < args.num_top_stats_dmg_dist+1:
            if sortedDist[i][1] >= 0:
                top_dist_x_times[sortedDist[i][0]] += 1
                valid_dist += 1
            i += 1

    # print top x players for all stats. If less then x
    # players, print all. If x-th place doubled, print all with the
    # same amount of top x achieved.

    myprint(log, "\n")
    #print("The following stats are computed over",used_fights,"out of",total_fights,"fights.\n")
    #print("For damage and distance to tag, the best", args.num_top_stats_dmg_dist, "players are shown. For all other stats, the best", args.num_top_stats, "players are shown. For total values, only the best three players are shown. Everything is cut at 50% of the highest value.\n")

    print_string = "The following stats are computed over "+str(used_fights)+" out of "+str(total_fights)+" fights."
    myprint(output, print_string)
    print_string = "For damage and distance to tag, the best "+str(args.num_top_stats_dmg_dist)+" players are shown. For all other stats, the best "+str(args.num_top_stats)+" players are shown. For total values, only the best three players are shown. Everything is cut at 50% of the highest value."
    myprint(output, print_string)

    write_sorted_top_x(output, top_damage_x_times, total_damage, "damage", args.num_top_stats_dmg_dist)
    write_sorted_top_x(output, top_strips_x_times, total_strips, "strips", args.num_top_stats)
    write_sorted_top_x(output, top_cleanses_x_times, total_cleanses, "cleanses", args.num_top_stats)
    write_sorted_top_x(output, top_stab_x_times, total_stab, "stab output", args.num_top_stats)        
    write_sorted_top_x(output, top_healing_x_times, total_healing, "healing", args.num_top_stats)
    write_sorted_top_x(output, top_dist_x_times, total_dist, "dist", args.num_top_stats_dmg_dist, 1)
    
    write_sorted_total(output, total_damage, "damage", args.num_top_stats_dmg_dist)
    write_sorted_total(output, total_strips, "strips", args.num_top_stats)
    write_sorted_total(output, total_cleanses, "cleanses", args.num_top_stats)
    write_sorted_total(output, total_stab, "stab output", args.num_top_stats)
    write_sorted_total(output, total_healing, "healing", args.num_top_stats)
    # dist to tag total doesn't make much sense

    if args.print_percentage:
        write_sorted_top_x_percentage(output, top_damage_x_times, num_fights_present, "damage", args.num_top_stats_dmg_dist)
        write_sorted_top_x_percentage(output, top_strips_x_times, num_fights_present, "strips", args.num_top_stats)
        write_sorted_top_x_percentage(output, top_cleanses_x_times, num_fights_present, "cleanses", args.num_top_stats)
        write_sorted_top_x_percentage(output, top_stab_x_times, num_fights_present, "stab", args.num_top_stats)
        write_sorted_top_x_percentage(output, top_healing_x_times, num_fights_present, "healing", args.num_top_stats)
        write_sorted_top_x_percentage(output, top_dist_x_times, num_fights_present, "dist", args.num_top_stats_dmg_dist, 1)        
    
