#!/usr/bin/env python3

import argparse
import collections
import os.path
from os import listdir
import sys
import xml.etree.ElementTree as ET
from decimal import *

# Write the top x people who achieved top 3 in stat most often.
# Input:
# top3_x_times = how often did each player achieve a top3 spot in this stat
# total_values = what's the summed up value over all fights for this stat for each player
# stat = which stat are we looking at (dmg, cleanses, ...)
# omit = omit the first x player in the list. Mostly used for dist to tag since closest is always the com. Add corresponding number of players at the end, i.e., if omit = 1, print players that had top 3 stat 2nd to 4th most often.
def write_sorted_top_3(output_file, top3_x_times, total_values, stat, omit = 0):
    if len(top3_x_times) == 0:
        return

    # sort players according to number of times top 3 was achieved for stat
    sorted_top3 = sorted(top3_x_times.items(), key=lambda x:x[1], reverse=True)

    print("top 3", stat, "top x times")
    output_file.write("top 3 "+stat+" top x times\n")
    i = omit
    while i < len(sorted_top3) and (i < 3+omit or sorted_top3[i][1] == sorted_top3[i-1][1]) and sorted_top3[i][1] > 0:
        print(sorted_top3[i][0]+": "+str(sorted_top3[i][1])+f" (total {total_values[sorted_top3[i][0]]:.0f})")
        output_file.write(sorted_top3[i][0]+": "+str(sorted_top3[i][1])+f" (total {total_values[sorted_top3[i][0]]:.0f})\n")
        i += 1
    print("\n")
    output_file.write("\n")


# Write the top x people who achieved top 3 in stat with the highest percentage. This only considers fights where each player was present, i.e., a player who was in 4 fights and achieved a top 3 spot in 2 of them gets 50%, as does a player who was only in 2 fights and achieved a top 3 spot in 1 of them.
# Input:
# top3_x_times = how often did each player achieve a top3 spot in this stat
# num_fights_present = in how many fights was the player present
# stat = which stat are we looking at (dmg, cleanses, ...)
# omit = omit the first x player in the list. Mostly used for dist to tag since closest is always the com. Add corresponding number of players at the end, i.e., if omit = 1, print players that had top 3 stat 2nd to 4th most often.    
def write_sorted_top_3_percentage(output_file, top3_x_times, num_fights_present, stat, omit = 0):
    if len(top3_x_times) == 0:
        return

    percentages = {}
    for name in top3_x_times.keys():
        percentages[name] = top3_x_times[name] / num_fights_present[name]
    sorted_percentages = sorted(percentages.items(), key=lambda x:x[1], reverse=True)
    print("top 3", stat, "top 3 percentage")
    output_file.write("top 3 "+stat+" top 3 percentage\n")
    i = omit
    while i < len(sorted_percentages) and (i < 3+omit or sorted_percentages[i][1] == sorted_percentages[i-1][1]) and sorted_percentages[i][1] > 0:
        name = sorted_percentages[i][0]
        print(name+f": {sorted_percentages[i][1]*100:.0f}% ("+str(top3_x_times[name])+" / " + str(num_fights_present[name]) +")")
        output_file.write(name+": "+str(sorted_percentages[i][1])+" ("+str(top3_x_times[name])+" / " + str(num_fights_present[name]) +")\n")
        i += 1
    print("\n")
    output_file.write("\n")

def write_sorted_total(output_file, total_values, stat):
    if len(total_values) == 0:
        return

    sorted_total_values = sorted(total_values.items(), key=lambda x:x[1], reverse=True)    
    
    print("top 3 total", stat)
    output_file.write("top 3 total "+stat+"\n")
    i = 0
    while i < min(len(sorted_total_values), 3) and sorted_total_values[i][1] > 0:
        print(sorted_total_values[i][0]+":",sorted_total_values[i][1])
        output_file.write(sorted_total_values[i][0]+": "+str(sorted_total_values[i][1])+"\n")
        i += 1
    print("\n")
    output_file.write("\n")
    
    
if __name__ == '__main__':
    debug = False # enable / disable debug output

    parser = argparse.ArgumentParser(description='This reads a set of arcdps reports in xml format and generates top stats.')
    parser.add_argument('xml_directory', help='directory containing .xml files from arcdps reports')
    parser.add_argument('-o', '--output', dest="output_filename", help="text file to write the computed top stats")
    parser.add_argument('-d', '--duration', dest="minimum_duration", type=int, help="minimum duration of a fight in s. Shorter fights will be ignored.", default=30)
    parser.add_argument('-a', '--ally_numbers', dest="minimum_ally_numbers", type=int, help="minimum of allied players in a fight. Fights with less players will be ignored.", default=10)        

    args = parser.parse_args()

    if not os.path.isdir(args.xml_directory):
        print("Directory ",args.xml_directory," is not a directory or does not exist!")
        sys.exit()
    if args.output_filename is None:
        args.output_filename = args.xml_directory+"/top_stats.txt"

    print("Using xml directory ",args.xml_directory+", writing output to", args.output_filename)
    try:
        output = open(args.output_filename, "w")
    except FileExistsError:
        print("The output file "+args.output_filename+" already exists. Please rename or delete it. For changing the output file, see the help message:")
        parser.print_help()
        sys.exit()

    print("considering fights with more than", args.minimum_ally_numbers, "allied players that took longer than", args.minimum_duration, "s.")
        
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
    
    # iterating over all fights in directory
    for xml_filename in listdir(args.xml_directory):

        # skip non xml files
        if not ".xml" in xml_filename:
            continue

        # create xml tree
        print("parsing",xml_filename)
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

        # skip fights that last less than 30s
        if(duration < args.minimum_duration):
            print("Fight only took", mins, "m", secs, "s. Skipping fight.")
            continue
        
        # skip fights with less than 10 allies
        num_allies = len(xml_root.findall('players'))
        if num_allies < args.minimum_ally_numbers:
            print("only",num_allies,"allied players involved. Skipping fight.")
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
            dmg_xml = xml_player.find('dpsAll').find('damage')#.find('damage')
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
            
        print("\n")

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
        
        # increase number of times top 3 was achieved for top 3 players in each stat
        for i in range(min(len(sortedDamage), 3)):
            top_damage_x_times[sortedDamage[i]] += 1
            top_strips_x_times[sortedStrips[i]] += 1
            top_cleanses_x_times[sortedCleanses[i]] += 1
            top_stab_x_times[sortedStab[i]] += 1

        # might not have entries for healing -> separate loop
        for i in range(min(len(sortedHealing), 3)):
            top_healing_x_times[sortedHealing[i]] += 1

        # get top 4 for dist bc first is always the com. Also throw out negative dist.
        valid_dist = 0
        i = 0
        while i < len(sortedDist) and valid_dist < 4:
            if sortedDist[i][1] >= 0:
                top_dist_x_times[sortedDist[i][0]] += 1
                valid_dist += 1
            i += 1

    # print top 3 players top x times for all stats. If less then 3
    # players, print all. If 3rd place doubled, print all with the
    # same amount of top 3 achieved.

    print("\n")
    print("The following stats are computed over",used_fights,"fights.\n")

    write_sorted_top_3(output, top_damage_x_times, total_damage, "damage")
    write_sorted_top_3(output, top_strips_x_times, total_strips, "strips")
    write_sorted_top_3(output, top_cleanses_x_times, total_cleanses, "cleanses")
    write_sorted_top_3(output, top_stab_x_times, total_stab, "stab output")        
    write_sorted_top_3(output, top_healing_x_times, total_healing, "healing")
    write_sorted_top_3(output, top_dist_x_times, total_dist, "dist", 1) # dist handled slightly differently.
    
    write_sorted_total(output, sorted_total_damage, "damage")
    write_sorted_total(output, sorted_total_strips, "strips")
    write_sorted_total(output, sorted_total_cleanses, "cleanses")
    write_sorted_total(output, sorted_total_stab, "stab output")
    write_sorted_total(output, sorted_total_healing, "healing")
    # dist to tag total doesn't make much sense
    
    write_sorted_top_3_percentage(output, top_damage_x_times, num_fights_present, "damage")
    write_sorted_top_3_percentage(output, top_strips_x_times, num_fights_present, "strips")
    write_sorted_top_3_percentage(output, top_cleanses_x_times, num_fights_present, "cleanses")
    write_sorted_top_3_percentage(output, top_stab_x_times, num_fights_present, "stab")
    write_sorted_top_3_percentage(output, top_healing_x_times, num_fights_present, "healing")
    write_sorted_top_3_percentage(output, top_dist_x_times, num_fights_present, "dist", 1)        
    
