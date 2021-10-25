#!/usr/bin/env python3

import argparse
import collections
import os.path
from os import listdir
import sys
import xml.etree.ElementTree as ET
from decimal import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='This reads a set of arcdps reports in xml format and generates top stats.')
    parser.add_argument('xml_directory', help='directory containing .xml files from arcdps reports')

    args = parser.parse_args()

    if os.path.isdir(args.xml_directory):
        print("Using xml directory ",args.xml_directory)
    else:
        print("Directory ",xml_directory," is not a directory or does not exist!")
        sys.exit()

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
            print(".",end='',flush=True)
            name_xml = xml_player.find('name')
            #print(name_xml.text)

            dmg_xml = xml_player.find('dpsAll').find('damage')#.find('damage')
            #print("dmg:",dmg_xml.text)
            damage[name_xml.text] = int(dmg_xml.text)

            support_stats = xml_player.find('support')
            strips_xml = support_stats.find('boonStrips')
            #print "strips:",strips.text
            strips[name_xml.text] = int(strips_xml.text)
            cleanses_xml = support_stats.find('condiCleanse')
            #print("cleanses:",cleanses_xml.text)
            cleanses[name_xml.text] = int(cleanses_xml.text)

            stab_generated = 0
            for buff in xml_player.iter('squadBuffs'):
                # find stab buff
                if buff.find('id').text != stab_id:
                    continue
                stab_xml = buff.find('buffData').find('generation')
                stab_generated = Decimal(stab_xml.text)
                break
            #print("stab:",stab_generated)
            stab[name_xml.text] = stab_generated

            # check if healing was logged
            ext_healing_xml = xml_player.find('extHealingStats')
            if(ext_healing_xml != None):
                found_healing = True
                healing_xml = ext_healing_xml.find('outgoingHealingAllies').find('outgoingHealingAllies').find('healing')
                #print("healing:",healing_xml.text)
                healing[name_xml.text] = int(healing_xml.text)
            
            dist_xml = xml_player.find('statsAll').find('distToCom')
            #print("dist:",dist_xml.text)
            dist[name_xml.text] = Decimal(dist_xml.text)

            # add new data from this fight to total stats
            total_damage[name_xml.text] += damage[name_xml.text]
            total_strips[name_xml.text] += strips[name_xml.text]
            total_cleanses[name_xml.text] += cleanses[name_xml.text]
            total_stab[name_xml.text] += stab[name_xml.text]
            if found_healing:
                total_healing[name_xml.text] += healing[name_xml.text]
            # dist sometimes -1 for some reason
            if dist[name_xml.text] >= 0:
                total_dist[name_xml.text] += dist[name_xml.text]
            
        print("\n")

        # create dictionaries sorted according to stats
        sortedDamage = sorted(damage, key=damage.get, reverse=True)
        #print("top dmg:", sortedDamage)
        sortedStrips = sorted(strips, key=strips.get, reverse=True)
        #print("top strips:",sortedStrips)
        sortedCleanses = sorted(cleanses, key=cleanses.get, reverse=True)
        #print("top cleanses:",sortedCleanses)
        sortedStab = sorted(stab, key=stab.get, reverse=True)
        #print("top stab:",sortedStab)
        sortedHealing = sorted(healing, key=healing.get, reverse=True)
        #print("top healing:", sortedHealing)
        # small dist = good -> don't reverse sorting. Need to check for -1 -> keep values
        sortedDist = sorted(dist.items(), key=lambda x:x[1])
        #print("top dist:",sortedDist)

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
    
    print("top 3 damage top x times")
    i = 0
    while i < len(sorted_top_damage) and (i < 3 or sorted_top_damage[i][1] == sorted_top_damage[i-1][1]):
        print(sorted_top_damage[i][0],":",sorted_top_damage[i][1],"(total",total_damage[sorted_top_damage[i][0]],")")
        i += 1
    print("\n")

    print("top 3 strips top x times")
    i = 0
    while i < len(sorted_top_strips) and (i < 3 or sorted_top_strips[i][1] == sorted_top_strips[i-1][1]):
        print(sorted_top_strips[i][0],":",sorted_top_strips[i][1],"(total",total_strips[sorted_top_strips[i][0]],")")
        i += 1
    print("\n")
    
    print("top 3 cleanses top x times")
    i = 0
    while i < len(sorted_top_cleanses) and (i < 3 or sorted_top_cleanses[i][1] == sorted_top_cleanses[i-1][1]):
        print(sorted_top_cleanses[i][0],":",sorted_top_cleanses[i][1],"(total",total_cleanses[sorted_top_cleanses[i][0]],")")
        i += 1
    print("\n")
    
    print("top 3 stab output top x times")
    i = 0
    while i < len(sorted_top_stab) and (i < 3 or sorted_top_stab[i][1] == sorted_top_stab[i-1][1]):
        print(sorted_top_stab[i][0],":",sorted_top_stab[i][1],"(total",total_stab[sorted_top_stab[i][0]],")")
        i += 1
    print("\n")    

    if(len(sorted_top_healing) > 0):
        print("top 3 healing top x times")
        i = 0
        while i < len(sorted_top_healing) and (i < 3 or sorted_top_healing[i][1] == sorted_top_healing[i-1][1]):
            print(sorted_top_healing[i][0],":",sorted_top_healing[i][1],"(total",total_healing[sorted_top_healing[i][0]],")")
            i += 1
        print("\n")    

    print("top 3 dist top x times")
    # top dist = com -> start at 1
    i = 1
    while i < len(sorted_top_dist) and (i < 4 or sorted_top_dist[i][1] == sorted_top_dist[i-1][1]):
        print(sorted_top_dist[i][0],":",sorted_top_dist[i][1],"(total",total_dist[sorted_top_dist[i][0]],")")
        i += 1
    print("\n")

    # sort total stats
    sorted_total_damage = sorted(total_damage.items(), key=lambda x:x[1], reverse=True)
    sorted_total_strips = sorted(total_strips.items(), key=lambda x:x[1], reverse=True)
    sorted_total_cleanses = sorted(total_cleanses.items(), key=lambda x:x[1], reverse=True)
    sorted_total_stab = sorted(total_stab.items(), key=lambda x:x[1], reverse=True)
    sorted_total_healing = sorted(total_healing.items(), key=lambda x:x[1], reverse=True)    
    sorted_total_dist = sorted(total_dist.items(), key=lambda x:x[1]) # small dist = good -> don't reverse

    print("top 3 total damage")
    i = 0
    while i < min(len(sorted_total_damage),3):
        print(sorted_total_damage[i][0],":",sorted_total_damage[i][1])
        i += 1
    print("\n")

    print("top 3 total strips")
    i = 0
    while i < min(len(sorted_total_strips), 3):
        print(sorted_total_strips[i][0],":",sorted_total_strips[i][1])
        i += 1
    print("\n")
    
    print("top 3 total cleanses")
    i = 0
    while i < min(len(sorted_total_cleanses), 3):
        print(sorted_total_cleanses[i][0],":",sorted_total_cleanses[i][1])
        i += 1
    print("\n")
    
    print("top 3 total stab output")
    i = 0
    while i < min(len(sorted_total_stab), 3):
        print(sorted_total_stab[i][0],":",sorted_total_stab[i][1])
        i += 1
    print("\n")

    if len(sorted_total_healing) > 0:
        print("top 3 total healing")
        i = 0
        while i < min(len(sorted_total_healing), 3):
            print(sorted_total_healing[i][0],":",sorted_total_healing[i][1])
            i += 1
        print("\n")        

    print("top 3 total dist")
    # top dist = com -> start at 1
    i = 1
    while i < min(len(sorted_total_dist), 4):
        print(sorted_total_dist[i][0],":",sorted_total_dist[i][1])
        i += 1
    print("\n")
    
