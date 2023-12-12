#!/usr/bin/env python3
import math

from stat_classes import Fight, Config
from io_helper import myprint

# get ids of buffs in the log from the buff map
# Input:
# player_json: json data with the player info. In a json file as parsed by Elite Insights, one entry of the 'players' list.
# config: config to use in top stats computation
# changes config.buffs_stacking_intensity and config.buffs_stacking_duration inplace
def get_buff_ids_from_json(json_data, config, log):
    buffs = json_data['buffMap']
    for buff_id, buff in buffs.items():
        if buff['name'] in config.squad_buff_abbrev:
            abbrev_name = config.squad_buff_abbrev[buff['name']]
            config.squad_buff_ids[abbrev_name] = buff_id[1:]
            if buff['stacking']:
                config.buffs_stacking_intensity.append(abbrev_name)
            elif 'aura' in abbrev_name:
                config.buffs_not_stacking.append(abbrev_name)
            else:
                config.buffs_stacking_duration.append(abbrev_name)
        if buff['name'] in config.self_buff_abbrev:
            abbrev_name = config.self_buff_abbrev[buff['name']]
            config.self_buff_ids[abbrev_name] = buff_id[1:]
    # check that all buff ids were found
    found_all_ids = True
    for buff, abbrev in config.self_buff_abbrev.items():
        if abbrev not in config.self_buff_ids:
            myprint(log, "id for buff "+buff+" could not be found. This is not necessarily an error, the buff might just not be present in this log.", "info", config)
            found_all_ids = False
    for buff, abbrev in config.squad_buff_abbrev.items():
        if abbrev not in config.squad_buff_ids:
            myprint(log, "id for buff "+buff+" could not be found. This is not necessarily an error, the buff might just not be present in this log.", "info", config)
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
    myprint(log, "duration: "+str(hours)+"h "+str(mins)+"m "+str(secs)+"s", "debug", config)
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
        myprint(log, print_string, "info")
        
    # skip fights with less than min_allied_players allies
    if num_allies < config.min_allied_players:
        fight.skipped = True
        print_string = "\nOnly "+str(num_allies)+" allied players involved. Skipping fight."
        myprint(log, print_string, "info")

    # skip fights with less than min_enemy_players enemies
    if num_enemies < config.min_enemy_players:
        fight.skipped = True
        print_string = "\nOnly "+str(num_enemies)+" enemies involved. Skipping fight."
        myprint(log, print_string, "info")

    # get players using healing addon, if the addon was used
    if 'usedExtensions' not in fight_json:
        fight.players_running_healing_addon = []
    else:
        extensions = fight_json['usedExtensions']
        for extension in extensions:
            if extension['name'] == "Healing Stats":
                fight.players_running_healing_addon = extension['runningExtension']
        
    # TODO don't write polling rate, inch_to_pixel, tag_positions_until_death?
    fight.polling_rate = fight_json['combatReplayMetaData']['pollingRate']
    fight.inch_to_pixel = fight_json['combatReplayMetaData']['inchToPixel']

    # get commander positions
    tag_positions = list()
    commander_found = False
    i = 0
    for player in fight_json['players']:
        if player['hasCommanderTag']:
            if commander_found:
                # found a second player with commander tag -> distance to tag ambiguous, don't use it
                tag_positions = list()
                break
            commander_found = True
            tag_positions = player['combatReplayData']['positions']
            tag_down_time, tag_death_time = get_first_down_and_death_time(player)
            if tag_death_time > 0:
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



# get the first time the player went down, leading to death and the corresponding time of death, or -1, -1 if they never died
# Input:
# player_json: json data with the player info. In a json file as parsed by Elite Insights, one entry of the 'players' list.
def get_first_down_and_death_time(player_json):
    first_down_time = -1
    first_death_time = -1
    
    player_deaths = dict(player_json['combatReplayData']['dead'])
    player_downs = dict(player_json['combatReplayData']['down'])

    # find the first player downstate event that lead to death
    for death_begin, death_end in player_deaths.items():
        for down_begin, down_end in player_downs.items():
            if death_begin == down_end:
                # down times are logged in ms -> divide by 1000
                first_down_time = down_begin / 1000
                first_death_time = death_begin / 1000
                return first_down_time, first_death_time
    return first_down_time, first_death_time



# get average distance to tag given the player and tag positions
def get_distance_to_tag(player_positions, tag_positions, inch_to_pixel):
    player_distances = list()
    for position,tag_position in zip(player_positions, tag_positions):
        deltaX = position[0] - tag_position[0]
        deltaY = position[1] - tag_position[1]
        player_distances.append(math.sqrt(deltaX * deltaX + deltaY * deltaY))
    if len(player_distances) > 0:
        return (sum(player_distances) / len(player_distances)) / inch_to_pixel
    else:
        return -1
    

# TODO treat -1
# get value of stat from player_json
# return -1 if stat is not available or cannot be computed; or player was not present in the fight according to the duration_present relevant for the respective stat
# Input:
# player_json: json data with the player info. In a json file as parsed by Elite Insights, one entry of the 'players' list.
# stat: the stat being considered
# fight: information about the fight
# player_duration_present: the player.duration_present dict for this player, needed for some stat computations
# config: the config used for top stats computation
def get_stat_from_player_json(player_json, stat, fight, player_duration_present, config):
    #######################
    ### Fight durations ###
    #######################
    if stat == 'time_active':
        if 'activeTimes' not in player_json:
            config.errors.append("Could not find activeTimes in json to determine time_active.")
            return -1
        return round(int(player_json['activeTimes'][0])/1000)

    if stat == 'time_in_combat':
        return round(sum_breakpoints(get_combat_time_breakpoints(player_json)) / 1000)
    
    if stat == 'time_not_running_back':
        if fight.tag_positions_until_death == list():
            config.errors.append("Could not find tag positions to determine time_not_running_back.")
            return -1
        if 'combatReplayData' not in player_json or 'dead' not in player_json['combatReplayData'] or 'down' not in player_json['combatReplayData'] or 'statsAll' not in player_json or len(player_json['statsAll']) != 1 or 'distToCom' not in player_json['statsAll'][0]:
            config.errors.append("json is missing combatReplayData or entries for dead, down, or distToCom to determine time_not_running_back.")
            return -1
        player_dist_to_tag = player_json['statsAll'][0]['distToCom']
        player_positions = player_json['combatReplayData']['positions']
        player_distances = list()
        first_down_time, first_death_time = get_first_down_and_death_time(player_json)
        first_tag_down_time = len(fight.tag_positions_until_death) * fight.polling_rate / 1000
        
        # if player didn't go down and die, use time when com died
        if first_down_time < 0 or first_down_time < first_tag_down_time:
            first_down_time = first_tag_down_time
        
        # check the avg distance to tag until a player died to see if they were running back
        # if nobody was running back, just use the avg distance as computed by arcdps / EI
        if first_down_time < len(player_positions) * fight.polling_rate / 1000:
            first_down_position_index = int(first_down_time * 1000 / fight.polling_rate)
            player_dist_to_tag = get_distance_to_tag(player_positions[:first_down_position_index], fight.tag_positions_until_death[:first_down_position_index], fight.inch_to_pixel)

        # an average distance of more than 2000 until player or tag died likely means that the player was running back from the beginning
        if player_dist_to_tag > 2000:
            #print(f"distance of {player_json['name']} is {player_dist_to_tag}")
            first_down_time = 0

        # positions are recorded with polling rate in ms -> to get the time, need to multiply by that and divide by 1000
        return first_down_time

    #############
    ### group ###
    #############
    if stat == 'group':
        if 'group' not in player_json:
            config.errors.append("Could not find group in json.")
            return -1
        return int(player_json['group'])

    ########################################################
    ### check that fight duration is valid for this stat ###
    ########################################################
    if config.duration_for_averages[stat] not in player_duration_present or player_duration_present[config.duration_for_averages[stat]] <= 0:
        config.errors.append("Player was not in this fight according to duration_present relevant for stat"+stat+", or duration_present was not computed yet.")
        return -1
    
    ################
    ### cleanses ###
    ################
    if stat == 'cleanses':
        if 'support' not in player_json or len(player_json['support']) != 1 or 'condiCleanse' not in player_json['support'][0]:
            config.errors.append("Could not find support or an entry for condiCleanse in json.")
            return -1
        return int(player_json['support'][0]['condiCleanse'])            

    ##############
    ### deaths ###
    ##############
    if stat == 'deaths':
        # TODO split by death on tag / off tag
        if 'defenses' not in player_json or len(player_json['defenses']) != 1 or 'deadCount' not in player_json['defenses'][0]:
            config.errors.append("Could not find defenses or an entry for deadCount in json.")
            return -1
        return int(player_json['defenses'][0]['deadCount'])


    ################
    ### distance ###
    ################          
    if stat == 'dist':
        if fight.tag_positions_until_death == list():
            config.errors.append("Could not find tag positions to determine distance to tag.")
            return -1
        if 'combatReplayData' not in player_json or 'dead' not in player_json['combatReplayData'] or 'down' not in player_json['combatReplayData'] or 'statsAll' not in player_json or len(player_json['statsAll']) != 1 or 'distToCom' not in player_json['statsAll'][0]:
            config.errors.append("json is missing  combat replay data or entries for dead, down, or distToCom to determine distance to tag.")
            return -1
        # TODO this is hardcoded to not_running_back. make it possible to use active, total or in_combat too?
        player_dist_to_tag = player_json['statsAll'][0]['distToCom']
        if config.duration_for_averages[stat] == 'not_running_back':
            first_down_time = player_duration_present['not_running_back']
            player_positions = player_json['combatReplayData']['positions']

            # if player or tag died before the fight ended, compute average distance until the first down time that lead to death
            num_valid_positions = int(first_down_time * 1000 / fight.polling_rate)
            player_dist_to_tag = get_distance_to_tag(player_positions[:num_valid_positions], fight.tag_positions_until_death[:num_valid_positions], fight.inch_to_pixel)
        elif config.duration_for_averages[stat] == 'in_combat':
            config.errors.append("average distance over time in combat is not implemented yet. Using overall average distance instead.")
        return float(player_dist_to_tag)

    #################
    ### Dmg Taken ###
    #################
    # includes dmg absorbed by barrier
    if stat == 'dmg_taken_total':
        if 'defenses' not in player_json or len(player_json['defenses']) != 1 or 'damageTaken' not in player_json['defenses'][0]:
            config.errors.append("Could not find defenses or an entry for damageTaken in json to determine dmg_taken(_total).")
            return -1
        return int(player_json['defenses'][0]['damageTaken'])

    if stat == 'dmg_taken_absorbed':
        if 'defenses' not in player_json or len(player_json['defenses']) != 1 or 'damageBarrier' not in player_json['defenses'][0]:
            config.errors.append("Could not find defenses or an entry for damageBarrier in json to determine dmg_taken_absorbed.")
            return -1
        return int(player_json['defenses'][0]['damageBarrier'])

    if stat == 'dmg_taken_hp_lost':
        total_dmg_taken = get_stat_from_player_json(player_json, 'dmg_taken_total', fight, player_duration_present, config)
        dmg_absorbed = get_stat_from_player_json(player_json, 'dmg_taken_absorbed', fight, player_duration_present, config)
        if total_dmg_taken < 0 or dmg_absorbed < 0:
            return -1
        return total_dmg_taken - dmg_absorbed

    #################
    ### Dmg Dealt ###
    #################
    if stat == 'dmg_total':
        if 'dpsAll' not in player_json or len(player_json['dpsAll']) != 1 or 'damage' not in player_json['dpsAll'][0]:
            config.errors.append("Could not find dpsAll or an entry for damage in json to determine dmg_total.")
            return -1
        return int(player_json['dpsAll'][0]['damage'])  

    if stat == 'dmg_players':
        if 'targetDamage1S' not in player_json:
            config.errors.append("Could not find targetDamage1S in json to determine dmg_players.")
            return -1
        return sum(target[0][-1] for target in player_json['targetDamage1S'])

    if stat == 'dmg_other':
        total_dmg = get_stat_from_player_json(player_json, 'dmg_total', fight, player_duration_present, config)
        players_dmg = get_stat_from_player_json(player_json, 'dmg_players', fight, player_duration_present, config)
        if total_dmg < 0 or players_dmg < 0:
            return -1
        return total_dmg - players_dmg

    if stat == 'spike_dmg':
        if 'targetDamage1S' not in player_json:
            config.errors.append("Could not find targetDamage1S in json to determine spike_dmg.")
            return -1
        spike_dmg = -1
        last_dmg = 0
        for t in range(len(player_json['targetDamage1S'][0][0])):
            new_dmg = sum(player_json['targetDamage1S'][enemy][0][t] for enemy in range(len(player_json['targetDamage1S'])))
            spike_dmg = max(spike_dmg, new_dmg - last_dmg)
            last_dmg = new_dmg
        return spike_dmg
    
    ##############################
    ### Kill/Down contribution ###
    ##############################

    if stat == 'kills':
        if 'statsAll' not in player_json or len(player_json['statsAll']) == 0 or 'killed' not in player_json['statsAll'][0]:
            config.errors.append("Could not find statsAll or killed in json to determine number of kills.")
            return -1
        return int(player_json['statsAll'][0]['killed'])

    if stat == 'downs':
        if 'statsAll' not in player_json or len(player_json['statsAll']) == 0 or 'downed' not in player_json['statsAll'][0]:
            config.errors.append("Could not find statsAll or downed in json to determine number of downed.")
            return -1
        return int(player_json['statsAll'][0]['downed'])

    if stat == 'down_contrib':
        if 'statsAll' not in player_json or len(player_json['statsAll']) == 0 or 'downContribution' not in player_json['statsAll'][0]:
            config.errors.append("Could not find statsAll or downed in json to determine down contribution.")
            return -1
        return int(player_json['statsAll'][0]['downContribution'])

    ##################################
    ### Incoming / Outgoing strips ###
    ##################################

    if stat == 'strips':
        if 'support' not in player_json or len(player_json['support']) != 1 or 'boonStrips' not in player_json['support'][0]:
            config.errors.append("Could not find support or an entry for boonStrips in json to determine strips.")
            return -1
        return int(player_json['support'][0]['boonStrips'])
    
    if stat == 'stripped':
        if 'defenses' not in player_json or len(player_json['defenses']) != 1 or 'boonStrips' not in player_json['defenses'][0]:
            config.errors.append("Could not find defenses or an entry for boonStrips in json to determine stripped.")
            return -1
        return int(player_json['defenses'][0]['boonStrips'])

    ################
    ### Interrupts #
    ################

    if stat == 'interrupts':
        if 'statsAll' not in player_json or len(player_json['statsAll']) != 1 or 'interrupts' not in player_json['statsAll'][0]:
            config.errors.append("Could not find statsAll or an entry for interrupts in json to determine interrupts.")
            return -1
        return int(player_json['statsAll'][0]['interrupts'])
    
    ######################
    ### Heal & Barrier ###
    ######################
            
    if stat == 'heal_total':
        # check if healing was logged, save it
        if player_json['name'] not in fight.players_running_healing_addon:
            return -1
        if 'extHealingStats' not in player_json or 'outgoingHealing' not in player_json['extHealingStats']:
            config.errors.append("Could not find extHealingStats or an entry for outgoingHealing in json to determine heal_total.")
            return -1
        return player_json['extHealingStats']['outgoingHealing'][0]['healing']

    if stat == 'heal_players':
        # check if healing was logged, save it
        if player_json['name'] not in fight.players_running_healing_addon:
            return -1
        if 'extHealingStats' not in player_json or 'alliedHealing1S' not in player_json['extHealingStats']:
            config.errors.append("Could not find extHealingStats or an entry for alliedHealing1S in json to determine heal_players.")
            return -1
        return sum([healing[0][-1] for healing in player_json['extHealingStats']['alliedHealing1S']])
    
    if stat == 'heal_other':
        # check if healing was logged, save it
        total_heal = get_stat_from_player_json(player_json, 'heal_total', fight, player_duration_present, config)
        player_heal = get_stat_from_player_json(player_json, 'heal_players', fight, player_duration_present, config)
        if total_heal < 0 or player_heal < 0:
            return -1
        return total_heal - player_heal

    if stat == 'barrier':
        # check if barrier was logged, save it
        if player_json['name'] not in fight.players_running_healing_addon:
            return -1
        if 'extBarrierStats' not in player_json or 'outgoingBarrier' not in player_json['extBarrierStats']:
            config.errors.append("Could not find extBarrierStats or an entry for outgoingBarrier in json to determine barrier.")
            return -1
        return player_json['extBarrierStats']['outgoingBarrier'][0]['barrier']
        
    # TODO fix output for heal from regen
    if stat == 'heal_from_regen':
        # check if healing was logged, look for regen
        if player_json['name'] not in fight.players_running_healing_addon:
            return -1
        if 'extHealingStats' not in player_json or 'totalHealingDist' not in player_json['extHealingStats']:
            config.errors.append("Could not find extHealingStats or an entry for totalHealingDist in json to determine heal_from_regen.")
            return -1
        healing_json = player_json['extHealingStats']['totalHealingDist'][0]
        for healing_json2 in healing_json:
            if 'id' in healing_json2 and healing_json2['id'] == int(config.squad_buff_ids['regen']):
                return healing_json2['totalHealing']
        config.errors.append("Could not find regen in json to determine heal_from_regen.")
        return -1    

    if stat == 'hits_from_regen':
        # check if healing was logged, look for regen
        if player_json['name'] not in fight.players_running_healing_addon:
            return -1
        if 'extHealingStats' not in player_json or 'totalHealingDist' not in player_json['extHealingStats']:
            config.errors.append("Could not find extHealingStats or an entry for totalHealingDist in json to determine hits_from_regen.")
            return -1
        healing_json = player_json['extHealingStats']['totalHealingDist'][0]
        for healing_json2 in healing_json:
            if 'id' in healing_json2 and healing_json2['id'] == int(config.squad_buff_ids['regen']):
                return int(healing_json2['hits'])
        config.errors.append("Could not find regen in json to determine hits_from_regen.")
        return -1

    #############
    ### Auras ###
    #############

    if 'aura' in stat and stat in config.squad_buff_ids:
        if 'buffUptimes' not in player_json:
            config.errors.append("Could not find buffUptimes in json to determine "+stat+".")
            return -1
        for buff in player_json['buffUptimes']:
            if 'id' not in buff:
                continue
            # find right buff
            buffId = buff['id']
            if buffId == int(config.squad_buff_ids[stat]):
                if 'buffData' not in buff or len(buff['buffData']) == 0 or 'uptime' not in buff['buffData'][0]:
                    config.errors.append("Could not find entry for buffData or uptime in json to determine "+stat+".")
                    return -1
                return float(buff['buffData'][0]['uptime'])
        config.errors.append("Could not find the buff "+stat+" in the json. Treating as 0.")
        return 0.
    
    ###################
    ### Squad Buffs ###
    ###################

    if stat in config.squad_buff_ids:
        if 'squadBuffs' not in player_json:
            config.errors.append("Could not find squadBuffs in json to determine "+stat+".")
            return -1
        # get buffs in squad generation -> need to loop over all buffs
        for buff in player_json['squadBuffs']:
            if 'id' not in buff:
                continue 
            # find right buff
            buffId = buff['id']
            if buffId == int(config.squad_buff_ids[stat]):
                if 'buffData' not in buff or len(buff['buffData']) == 0 or 'generation' not in buff['buffData'][0]:
                    config.errors.append("Could not find entry for buffData or generation in json to determine "+stat+".")
                    return -1
                return float(buff['buffData'][0]['generation'])

        config.errors.append("Could not find the buff "+stat+" in the json. Treating as 0.")
        return 0.

    ##################
    ### Self Buffs ###
    ##################

    # for self buffs, only check if they were there (1) or not (0)
    if stat in config.self_buff_ids:
        if 'selfBuffs' not in player_json:
            config.errors.append("Could not find selfBuffs in json to determine "+stat+".")
            return -1
        for buff in player_json['selfBuffs']:
            if 'id' not in buff:
                continue 
            # find right buff
            buffId = buff['id']
            if buffId == int(config.self_buff_ids[stat]):
                if 'buffData' not in buff or len(buff['buffData']) == 0 or 'generation' not in buff['buffData'][0]:
                    config.errors.append("Could not find entry for buffData or generation in json to determine "+stat+".")
                    return -1
                return 1
        config.errors.append("Could not find the buff "+stat+" in the json. Treating as 0.")
        return 0


    if stat not in config.self_buff_abbrev.values() and stat not in config.squad_buff_abbrev.values():
        config.errors.append("Stat ", stat, " is currently not supported! Treating it as 0.")
    return 0


# find the first time a player took or dealt damage after initial_time
# Input:
# initial_time = check for first time this player was in combat after this time in the fight
# player_json = the json data for this player in this fight
# Output:
# First time the player took or dealt damage after initial_time
def get_combat_start_from_player_json(initial_time, player_json):
    start_combat = -1
    if ('healthPercents' not in player_json or len(player_json['healthPercents']) == 0) and ('powerDamage1S' not in player_json or len(player_json['powerDamage1S']) == 0):
        return start_combat
    
    if 'healthPercents' in player_json:
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
    if 'powerDamage1S' in player_json and len(player_json['powerDamage1S']) > 0:
        for i in range(math.ceil(initial_time/1000), len(player_json['powerDamage1S'][0])):
            if i == 0:
                continue
            if player_json['powerDamage1S'][0][i] != player_json['powerDamage1S'][0][i-1]:
                if start_combat == -1:
                    # if start_combat is -1 so far, the player didn't take damage until now -> this is the start of combat
                    start_combat = i*1000
                else:
                    # otherwise he took dmg, check which was first
                    start_combat = min(start_combat, i*1000)
                break

    if start_combat == -1:
        start_combat = initial_time
    return start_combat


    
# find the combat breakpoints, i.e., start and end points of this player being in combat (interrupted by death)
# Input:
# player_json = the json data for this player in this fight
# Output:
# List of start and end timestamps of the player being in combat
def get_combat_time_breakpoints(player_json):
    start_combat = get_combat_start_from_player_json(0, player_json)
    end_combat = (len(player_json['damage1S'][0]))*1000
    if 'combatReplayData' not in player_json:
        print("WARNING: combatReplayData not in json, using activeTimes as time in combat")
        # time_active = duration the player was not dead
        return [start_combat, min(start_combat + get_stat_from_player_json(player_json, 'time_active', None, None, None) * 1000, end_combat)]
    replay = player_json['combatReplayData']
    if 'dead' not in replay:
        return [start_combat, end_combat]

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
    if start_combat != -1 and start_combat < end_combat:
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
        combat_time += (end - start)
    return combat_time

