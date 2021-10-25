#!/usr/bin/env python3

import argparse
import collections
import os.path
from os import listdir
import sys
import xml.etree.ElementTree as ET
from decimal import *

def write_sorted_top_3(output_file, sorted_values, total_values, stat):
    if len(sorted_values) == 0:
        return
    print("top 3", stat, "top x times")
    output_file.write("top 3 "+stat+" top x times\n")
    i = 0
    while i < len(sorted_values) and (i < 3 or sorted_values[i][1] == sorted_values[i-1][1]):
        print(sorted_values[i][0]+": "+str(sorted_values[i][1])+" (total "+str(total_values[sorted_values[i][0]])+")")
        output_file.write(sorted_values[i][0]+": "+str(sorted_values[i][1])+" (total "+str(total_values[sorted_values[i][0]])+")\n")
        i += 1
    print("\n")
    output_file.write("\n")

def write_sorted_top_3_dist(output_file, sorted_top_dist, total_dist):
    print("top 3 dist top x times")
    output_file.write("top 3 dist top x times\n")
    # top dist = com -> start at 1
    i = 1
    while i < len(sorted_top_dist) and (i < 4 or sorted_top_dist[i][1] == sorted_top_dist[i-1][1]):
        print(sorted_top_dist[i][0],":",sorted_top_dist[i][1], f"(total {total_dist[sorted_top_dist[i][0]]:.2f})")
        output_file.write(sorted_top_dist[i][0]+": "+str(sorted_top_dist[i][1])+f"(total {total_dist[sorted_top_dist[i][0]]:.2f})\n")
        i += 1
    print("\n")
    output_file.write("\n")

def write_sorted_total(output_file, sorted_total_values, stat):
    if len(sorted_total_values) == 0:
        return
    print("top 3 total", stat)
    output_file.write("top 3 total "+stat+"\n")
    i = 0
    while i < min(len(sorted_total_values), 3):
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
        output = open(args.output_filename, "x")
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
            #print(".",end='',flush=True)
            name_xml = xml_player.find('name')
            name = name_xml.text
            dmg_xml = xml_player.find('dpsAll').find('damage')#.find('damage')
            damage[name] = int(dmg_xml.text)

            support_stats = xml_player.find('support')
            strips_xml = support_stats.find('boonStrips')
            strips[name] = int(strips_xml.text)
            cleanses_xml = support_stats.find('condiCleanse')
            cleanses[name] = int(cleanses_xml.text)

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
                healing_xml = ext_healing_xml.find('outgoingHealingAllies').find('outgoingHealingAllies').find('healing')
                healing[name] = int(healing_xml.text)
            
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

    # sort players according to number of times top 3 was achieved for each stat
    sorted_top_damage = sorted(top_damage_x_times.items(), key=lambda x:x[1], reverse=True)
    sorted_top_strips = sorted(top_strips_x_times.items(), key=lambda x:x[1], reverse=True)
    sorted_top_cleanses = sorted(top_cleanses_x_times.items(), key=lambda x:x[1], reverse=True)
    sorted_top_stab = sorted(top_stab_x_times.items(), key=lambda x:x[1], reverse=True)
    sorted_top_healing = sorted(top_healing_x_times.items(), key=lambda x:x[1], reverse=True)
    sorted_top_dist = sorted(top_dist_x_times.items(), key=lambda x:x[1], reverse=True)

    # print top 3 players top x times for all stats. If less then 3
    # players, print all. If 3rd place doubled, print all with the
    # same amount of top 3 achieved.

    print("\n")
    print("The following stats are computed over",used_fights,"fights.\n")

    write_sorted_top_3(output, sorted_top_damage, total_damage, "damage")
    write_sorted_top_3(output, sorted_top_strips, total_strips, "strips")
    write_sorted_top_3(output, sorted_top_cleanses, total_cleanses, "cleanses")
    write_sorted_top_3(output, sorted_top_stab, total_stab, "stab output")        
    write_sorted_top_3(output, sorted_top_healing, total_healing, "healing")
    write_sorted_top_3_dist(output, sorted_top_dist, total_dist) # dist handled slightly differently.

    # sort total stats
    sorted_total_damage = sorted(total_damage.items(), key=lambda x:x[1], reverse=True)
    sorted_total_strips = sorted(total_strips.items(), key=lambda x:x[1], reverse=True)
    sorted_total_cleanses = sorted(total_cleanses.items(), key=lambda x:x[1], reverse=True)
    sorted_total_stab = sorted(total_stab.items(), key=lambda x:x[1], reverse=True)
    sorted_total_healing = sorted(total_healing.items(), key=lambda x:x[1], reverse=True)    
    sorted_total_dist = sorted(total_dist.items(), key=lambda x:x[1]) # small dist = good -> don't reverse

    write_sorted_total(output, sorted_total_damage, "damage")
    write_sorted_total(output, sorted_total_strips, "strips")
    write_sorted_total(output, sorted_total_cleanses, "cleanses")
    write_sorted_total(output, sorted_total_stab, "stab output")
    write_sorted_total(output, sorted_total_healing, "healing")
    
    #print("top 3 total dist")
    ## top dist = com -> start at 1
    #i = 1
    #while i < min(len(sorted_total_dist), 4):
    #    print(sorted_total_dist[i][0],f": {sorted_total_dist[i][1]:.2f}")
    #    i += 1
    #print("\n")
    
