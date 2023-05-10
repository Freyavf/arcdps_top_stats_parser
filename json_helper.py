#!/usr/bin/env python3
import math

from stat_classes import Fight, Config

debug = False # enable / disable debug output

# get ids of buffs in the log from the buff map
# Input:
# player_json: json data with the player info. In a json file as parsed by Elite Insights, one entry of the 'players' list.
# config: config to use in top stats computation
# changes config.buffs_stacking_intensity and config.buffs_stacking_duration inplace
def get_buff_ids_from_json(json_data, config):
    buffs = json_data['buffMap']
    for buff_id, buff in buffs.items():
        if buff['name'] in config.squad_buff_abbrev:
            abbrev_name = config.squad_buff_abbrev[buff['name']]
            config.squad_buff_ids[abbrev_name] = buff_id[1:]
            if buff['stacking']:
                config.buffs_stacking_intensity.append(abbrev_name)
            else:
                config.buffs_stacking_duration.append(abbrev_name)
        if buff['name'] in config.self_buff_abbrev:
            abbrev_name = config.self_buff_abbrev[buff['name']]
            config.self_buff_ids[abbrev_name] = buff_id[1:]
    # check that all buff ids were found
    found_all_ids = True
    for buff, abbrev in config.self_buff_abbrev.items():
        if abbrev not in config.self_buff_ids:
            print("id for buff", buff, "could not be found. This is not necessarily an error, the buff might just not be present in this log.")
            found_all_ids = False
    return found_all_ids


# get stats for this fight from fight_json
# Input:
# fight_json = json object including one fight
# config = the config to use for top stat computation
# log = log file to write to
def get_stats_from_fight_json(fight_json, config, log):
    # get fight duration in min and sec
    fight_duration_json = fight_json['duration']
    split_duration = fight_duration_json.split('h ', 1)
    hours = 0
    mins = 0
    secs = 0
    if len(split_duration) > 1:
        hours = int(split_duration[0])
    split_duration = fight_duration_json.split('m ', 1)
    if len(split_duration) > 1:
        mins = int(split_duration[0])
    split_duration = split_duration[1].split('s', 1)
    if len(split_duration) > 1:
        secs = int(split_duration[0])
    if debug:
        print("duration: ", hours, "h ", mins, "m ", secs, "s")
    duration = hours*3600 + mins*60 + secs

    num_allies = len(fight_json['players'])
    num_enemies = 0
    num_kills = 0
    for enemy in fight_json['targets']:
        if 'enemyPlayer' in enemy and enemy['enemyPlayer'] == True:
            num_enemies += 1
            # if combat replay data is there, add number of times this player died to total num kills
            if 'combatReplayData' in enemy:
                num_kills += len(enemy['combatReplayData']['dead'])
                
    # initialize fight         
    fight = Fight()
    fight.duration = duration
    fight.enemies = num_enemies
    fight.allies = num_allies
    fight.kills = num_kills
    fight.start_time = fight_json['timeStartStd']
    fight.end_time = fight_json['timeEndStd']        
    fight.total_stats = {key: 0 for key in config.stats_to_compute}
    fight.avg_stats = {key: 0 for key in config.stats_to_compute}    
        
    # skip fights that last less than min_fight_duration seconds
    if(duration < config.min_fight_duration):
        fight.skipped = True
        print_string = "\nFight only took "+str(hours)+"h "+str(mins)+"m "+str(secs)+"s. Skipping fight."
        myprint(log, print_string)
        
    # skip fights with less than min_allied_players allies
    if num_allies < config.min_allied_players:
        fight.skipped = True
        print_string = "\nOnly "+str(num_allies)+" allied players involved. Skipping fight."
        myprint(log, print_string)

    # skip fights with less than min_enemy_players enemies
    if num_enemies < config.min_enemy_players:
        fight.skipped = True
        print_string = "\nOnly "+str(num_enemies)+" enemies involved. Skipping fight."
        myprint(log, print_string)

    # get players using healing addon, if the addon was used
    if 'usedExtensions' not in fight_json:
        fight.players_running_healing_addon = []
    else:
        extensions = fight_json['usedExtensions']
        for extension in extensions:
            if extension['name'] == "Healing Stats":
                fight.players_running_healing_addon = extension['runningExtension']
        
    # TODO don't write polling rate, inch_to_pixel, tag_positions_until_death
    fight.polling_rate = fight_json['combatReplayMetaData']['pollingRate']
    fight.inch_to_pixel = fight_json['combatReplayMetaData']['inchToPixel']

    # get commander positions
    tag_positions = {}
    commander_found = False
    i = 0
    for player in fight_json['players']:
        if player['hasCommanderTag']:
            if commander_found:
                # found a second player with commander tag -> distance to tag ambiguous, don't use it
                tag_positions = {}
                break
            commander_found = True
            tag_positions = player['combatReplayData']['positions']
            if player['combatReplayData']['dead']:
                death_time = int(player['combatReplayData']['dead'][0][0] / fight.polling_rate)
                tag_positions = tag_positions[:death_time]
                commander_found = True
    fight.tag_positions_until_death = tag_positions

    return fight



# get account, character name and profession from json object
# Input:
# player_json: json data with the player info. In a json file as parsed by Elite Insights, one entry of the 'players' list.
# Output: account, character name, profession
def get_basic_player_data_from_json(player_json):
    account = player_json['account']
    name = player_json['name']
    profession = player_json['profession']
    return account, name, profession



# get value of stat from player_json
# Input:
# player_json: json data with the player info. In a json file as parsed by Elite Insights, one entry of the 'players' list.
# fight: information about the fight
# stat: the stat being considered
# config: the config used for top stats computation
def get_stat_from_player_json(player_json, fight, stat, config):
    if stat == 'time_in_combat':
        return round(sum_breakpoints(get_combat_time_breakpoints(player_json)) / 1000)

    if stat == 'group':
        if 'group' not in player_json:
            return 0
        return int(player_json['group'])
    
    if stat == 'time_active':
        if 'activeTimes' not in player_json:
            return 0
        return round(int(player_json['activeTimes'][0])/1000)

    # includes dmg absorbed by barrier
    if stat == 'dmg_taken' or stat == 'dmg_taken_total':
        if 'defenses' not in player_json or len(player_json['defenses']) != 1 or 'damageTaken' not in player_json['defenses'][0]:
            return 0
        return int(player_json['defenses'][0]['damageTaken'])

    if stat == 'dmg_taken_absorbed':
        if 'defenses' not in player_json or len(player_json['defenses']) != 1 or 'damageBarrier' not in player_json['defenses'][0]:
            return 0
        return int(player_json['defenses'][0]['damageBarrier'])

    if stat == 'dmg_taken_hp_lost':
        total_dmg_taken = get_stat_from_player_json(player_json, fight, 'dmg_taken_total', config)
        dmg_absorbed = get_stat_from_player_json(player_json, fight, 'dmg_taken_absorbed', config)
        return total_dmg_taken - dmg_absorbed

    if stat == 'deaths':
        if 'defenses' not in player_json or len(player_json['defenses']) != 1 or 'deadCount' not in player_json['defenses'][0]:
            return 0
        return int(player_json['defenses'][0]['deadCount'])

    #if stat == 'kills':
    #    if 'statsAll' not in player_json or len(player_json['statsAll']) != 1 or 'killed' not in player_json['statsAll'][0]:
    #        return 0        
    #    return int(player_json['statsAll'][0]['killed'])

    if stat == 'dmg_total' or stat == 'dmg':
        if 'dpsAll' not in player_json or len(player_json['dpsAll']) != 1 or 'damage' not in player_json['dpsAll'][0]:
            return 0
        return int(player_json['dpsAll'][0]['damage'])  

    if stat == 'dmg_players':
        if 'targetDamage1S' not in player_json:
            return 0
        return sum(target[0][-1] for target in player_json['targetDamage1S'])

    if stat == 'dmg_other':
        total_dmg = get_stat_from_player_json(player_json, fight, 'dmg_total', config)
        players_dmg = get_stat_from_player_json(player_json, fight, 'dmg_players', config)
        return total_dmg - players_dmg

    if stat == 'rips':
        if 'support' not in player_json or len(player_json['support']) != 1 or 'boonStrips' not in player_json['support'][0]:
            return 0
        return int(player_json['support'][0]['boonStrips'])
    
    if stat == 'cleanses':
        if 'support' not in player_json or len(player_json['support']) != 1 or 'condiCleanse' not in player_json['support'][0]:
            return 0
        return int(player_json['support'][0]['condiCleanse'])            

    if stat == 'dist':
        if fight.tag_positions_until_death == list():
            return -1
        if 'combatReplayData' not in player_json or 'dead' not in player_json['combatReplayData'] or 'down' not in player_json['combatReplayData'] or 'statsAll' not in player_json or len(player_json['statsAll']) != 1 or 'distToCom' not in player_json['statsAll'][0]:
            return -1
        player_dist_to_tag = player_json['statsAll'][0]['distToCom']
        player_deaths = dict(player_json['combatReplayData']['dead'])
        player_downs = dict(player_json['combatReplayData']['down'])
        first_death_time = len(fight.tag_positions_until_death)
        player_positions = player_json['combatReplayData']['positions']
        player_distances = list()
        for death_begin, death_end in player_deaths.items():
            for down_begin, down_end in player_downs.items():
                if death_begin == down_end:
                    first_death_time = min(int(down_begin / fight.polling_rate), first_death_time)

        if first_death_time < len(player_positions):
            for position,tag_position in zip(player_positions[:first_death_time], fight.tag_positions_until_death[:first_death_time]):
                deltaX = position[0] - tag_position[0]
                deltaY = position[1] - tag_position[1]
                player_distances.append(math.sqrt(deltaX * deltaX + deltaY * deltaY))
            player_dist_to_tag = (sum(player_distances) / len(player_distances)) / fight.inch_to_pixel

        if player_dist_to_tag > 2000:
            player_dist_to_tag = -1
            first_death_time = 0
        return float(player_dist_to_tag), float(first_death_time)

    if stat == 'stripped':
        if 'defenses' not in player_json or len(player_json['defenses']) != 1 or 'boonStrips' not in player_json['defenses'][0]:
            return 0
        return int(player_json['defenses'][0]['boonStrips'])

    if stat == 'heal' or stat == 'heal_total':
        # check if healing was logged, save it
        if player_json['name'] not in fight.players_running_healing_addon or 'extHealingStats' not in player_json or 'outgoingHealing' not in player_json['extHealingStats']:
            return -1
        return player_json['extHealingStats']['outgoingHealing'][0]['healing']

    if stat == 'heal_players':
        # check if healing was logged, save it
        if player_json['name'] not in fight.players_running_healing_addon or 'extHealingStats' not in player_json or 'alliedHealing1S' not in player_json['extHealingStats']:
            return -1
        return sum([healing[0][-1] for healing in player_json['extHealingStats']['alliedHealing1S']])
    
    if stat == 'heal_other':
        # check if healing was logged, save it
        total_heal = get_stat_from_player_json(player_json, fight, 'heal_total', config)
        player_heal = get_stat_from_player_json(player_json, fight, 'heal_players', config)
        if total_heal == -1 or player_heal == -1:
            return -1
        return total_heal - player_heal

    if stat == 'barrier':
        # check if barrier was logged, save it
        if player_json['name'] in fight.players_running_healing_addon and 'extBarrierStats' in player_json and 'outgoingBarrier' in player_json['extBarrierStats']:
            return player_json['extBarrierStats']['outgoingBarrier'][1]['barrier']
        return -1

    if stat == 'heal_from_regen':
        # check if healing was logged, look for regen
        if player_json['name'] in fight.players_running_healing_addon and 'extHealingStats' in player_json and 'totalHealingDist' in player_json['extHealingStats']:
            healing_json = player_json['extHealingStats']['totalHealingDist'][0]
            for healing_json2 in healing_json:
                if 'id' in healing_json2 and healing_json2['id'] == int(config.squad_buff_ids['regen']):
                    return healing_json2['totalHealing']
        return -1    

    if stat == 'hits_from_regen':
        # check if healing was logged, look for regen
        if player_json['name'] in fight.players_running_healing_addon and 'extHealingStats' in player_json and 'totalHealingDist' in player_json['extHealingStats']:
            healing_json = player_json['extHealingStats']['totalHealingDist'][0]
            for healing_json2 in healing_json:
                if 'id' in healing_json2 and healing_json2['id'] == int(config.squad_buff_ids['regen']):
                    return int(healing_json2['hits'])
        return -1

    ### Buffs ###
    if stat in config.squad_buff_ids:
        if 'squadBuffs' not in player_json:
            return 0.
        # get buffs in squad generation -> need to loop over all buffs
        for buff in player_json['squadBuffs']:
            if 'id' not in buff:
                continue 
            # find right buff
            buffId = buff['id']
            if buffId == int(config.squad_buff_ids[stat]):
                if 'buffData' not in buff or len(buff['buffData']) == 0 or 'generation' not in buff['buffData'][0]:
                    return 0.
                return float(buff['buffData'][0]['generation'])
        return 0.

    if stat in config.self_buff_ids:
        if 'selfBuffs' not in player_json:
            return 0
        for buff in player_json['selfBuffs']:
            if 'id' not in buff:
                continue 
            # find right buff
            buffId = buff['id']
            if buffId == int(config.self_buff_ids[stat]):
                if 'buffData' not in buff or len(buff['buffData']) == 0 or 'generation' not in buff['buffData'][0]:
                    return 0
                return 1
        return 0


    if stat not in config.self_buff_abbrev.values() and stat not in config.squad_buff_abbrev.values():
        print("stat ", stat, " ist currently not supported! Treating it as 0.")
    return 0


# find the first time a player took or dealt damage after initial_time
# Input:
# initial_time = check for first time this player was in combat after this time in the fight
# player_json = the json data for this player in this fight
# Output:
# First time the player took or dealt damage after initial_time
def get_combat_start_from_player_json(initial_time, player_json):
    start_combat = -1
    # if healthPercents is not available, assume the player was in combat right away
    if 'healthPercents' not in player_json:
        return initial_time
    last_health_percent = 100
    for change in player_json['healthPercents']:
        # look for last timestamp before initial time
        if change[0] < initial_time:
            last_health_percent = change[1]
            continue
        if change[1] - last_health_percent < 0:
            # got dmg
            start_combat = change[0]
            break
        last_health_percent = change[1]
        
    # from initial time until end of the fight, check when player dealt (power) dmg the first time
    # not using condi, because condis can still tick after a player died
    for i in range(math.ceil(initial_time/1000), len(player_json['powerDamage1S'][0])):
        if i == 0:
            continue
        if player_json['powerDamage1S'][0][i] != player_json['powerDamage1S'][0][i-1]:
            if start_combat == -1:
                start_combat = i*1000
            else:
                start_combat = min(start_combat, i*1000)
            break
    return start_combat


    
# find the combat breakpoints, i.e., start and end points of this player being in combat (interrupted by death)
# Input:
# player_json = the json data for this player in this fight
# Output:
# List of start and end timestamps of the player being in combat
def get_combat_time_breakpoints(player_json):
    start_combat = get_combat_start_from_player_json(0, player_json)
    if 'combatReplayData' not in player_json:
        print("WARNING: combatReplayData not in json, using activeTimes as time in combat")
        # activeTimes = duration the player was not dead
        return [start_combat, get_stat_from_player_json(player_json, None, 'time_active', None) * 1000]
    replay = player_json['combatReplayData']
    if 'dead' not in replay:
        return [start_combat, get_stat_from_player_json(player_json, None, 'time_active', None) * 1000]

    breakpoints = []
    playerDeaths = dict(replay['dead'])
    playerDowns = dict(replay['down'])
    # need corresponding down event for each death event. down end = death start
    for deathStart, deathEnd in playerDeaths.items():
        for downStart, downEnd in playerDowns.items():
            if deathStart == downEnd:
                if start_combat != -1:
                    breakpoints.append([start_combat, deathStart])
                start_combat = get_combat_start_from_player_json(deathEnd + 1000, player_json)
                break
    end_combat = (len(player_json['damage1S'][0]))*1000
    if start_combat != -1:
        breakpoints.append([start_combat, end_combat])

    return breakpoints



# compute the time in combat from the breakpoints as determined in get_combat_time_breakpoints
# Input:
# breakpoints = list of [start combat, end combat] items
# Output:
# total time in combat
def sum_breakpoints(breakpoints):
    combat_time = 0
    for [start, end] in breakpoints:
        combat_time += end - start
    return combat_time

