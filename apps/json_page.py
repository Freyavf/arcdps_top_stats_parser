from flask import request
from app import app
import requests

from parse_top_stats_tools import *
import parser_configs.parser_config_detailed as parser_config
config = fill_config(parser_config)
json_output_filename = "top_stats_detailed.json"


@app.route('/json', methods=['POST'])
def retrieve_data():
    if request.method == 'POST':
        if 'links' in request.json:
            links = request.json['links']
            print(f'LINK: {links}')
            json_dict = get_json_data(links)
            print('Sending back data')
            return json_dict
        return {'msg': 'No links'}
    else:
        print('No POST request')
        return {'msg':'No POST request'}


def get_json_data(json_links):
    if json_links is None:
        return

    #log = open("log_detailed.txt","w")
    log = ''

    print_string = "Considering fights with at least "+str(config.min_allied_players)+" allied players and at least "+str(config.min_enemy_players)+" enemies that took longer than "+str(config.min_fight_duration)+" s."
    print(print_string)

    # healing only in logs if addon was installed
    found_healing = False # Todo what if some logs have healing and some don't
    found_barrier = False    

    players = []        # list of all player/profession combinations
    player_index = {}   # dictionary that matches each player/profession combo to its index in players list
    account_index = {}  # dictionary that matches each account name to a list of its indices in players list

    used_fights = 0
    fights = []
    first = True

    output = ''
            
    for link in json_links:
        filename=link['href']
        try:
            print(f'Getting JSON data')
            json_data = requests.get(link['href']).json()
            print(f'JSON data retrieved')
            print(f'Getting data from json')
            used_fights, first, found_healing, found_barrier = get_stats_from_json_data(json_data, players, player_index, account_index, used_fights, fights, config, first, found_healing, found_barrier, log, filename)
            print(f'Data retrieved')
        except Exception as e:
            print(f'''Could't get json from: {link}''')
            print(e)
    print(f'Getting raid data')
    get_overall_stats(players, used_fights, False, config)
    print("\n")

    print_string = "Welcome to the Records of Valhalla!\n"

    # print overall stats
    overall_squad_stats = get_overall_squad_stats(fights, config)
    #total_fight_duration = print_total_squad_stats(fights, overall_squad_stats, found_healing, found_barrier, config, log)

    #print_fights_overview(fights, overall_squad_stats, config, log)

    # print overall stats
    #overall_squad_stats = get_overall_squad_stats(fights, config)
    #total_fight_duration = print_total_squad_stats(fights, overall_squad_stats, found_healing, found_barrier, config, output)

    #print_fights_overview(fights, overall_squad_stats, config, output)
    #write_fights_overview_xls(fights, overall_squad_stats, config, xls_output_filename)

    overall_raid_stats = get_overall_raid_stats(fights)
    total_fight_duration = print_total_squad_stats(fights, overall_squad_stats, overall_raid_stats, found_healing, found_barrier, config, output)
    
    print_fights_overview(fights, overall_squad_stats, overall_raid_stats, config, output)

    # print top x players for all stats. If less then x
    # players, print all. If x-th place doubled, print all with the
    # same amount of top x achieved.
    num_used_fights = overall_raid_stats['num_used_fights']

    top_total_stat_players = {key: list() for key in config.stats_to_compute}
    top_consistent_stat_players = {key: list() for key in config.stats_to_compute}
    top_average_stat_players = {key: list() for key in config.stats_to_compute}
    top_percentage_stat_players = {key: list() for key in config.stats_to_compute}
    top_late_players = {key: list() for key in config.stats_to_compute}
    top_jack_of_all_trades_players = {key: list() for key in config.stats_to_compute}    
    
    for stat in config.stats_to_compute:
        if (stat == 'heal' and not found_healing) or (stat == 'barrier' and not found_barrier):
            continue

        myprint(output, config.stat_names[stat].upper()+" AWARDS\n")
        
        if stat == 'dist':
            top_consistent_stat_players[stat] = get_top_players(players, config, stat, StatType.CONSISTENT)
            top_total_stat_players[stat] = get_top_players(players, config, stat, StatType.TOTAL)
            top_average_stat_players[stat] = get_top_players(players, config, stat, StatType.AVERAGE)            
            top_percentage_stat_players[stat],comparison_val = get_and_write_sorted_top_percentage(players, config, num_used_fights, stat, output, StatType.PERCENTAGE, top_consistent_stat_players[stat])
        elif stat == 'dmg_taken':
            top_consistent_stat_players[stat] = get_top_players(players, config, stat, StatType.CONSISTENT)
            top_total_stat_players[stat] = get_top_players(players, config, stat, StatType.TOTAL)
            top_percentage_stat_players[stat],comparison_val = get_top_percentage_players(players, config, stat, StatType.PERCENTAGE, num_used_fights, top_consistent_stat_players[stat], top_total_stat_players[stat], list(), list())
            top_average_stat_players[stat] = get_and_write_sorted_average(players, config, num_used_fights, stat, output)
        else:
            top_consistent_stat_players[stat] = get_and_write_sorted_top_consistent(players, config, num_used_fights, stat, output)
            top_total_stat_players[stat] = get_and_write_sorted_total(players, config, total_fight_duration, stat, output)
            top_average_stat_players[stat] = get_top_players(players, config, stat, StatType.AVERAGE)
            top_percentage_stat_players[stat],comparison_val = get_top_percentage_players(players, config, stat, StatType.PERCENTAGE, num_used_fights, top_consistent_stat_players[stat], top_total_stat_players[stat], list(), list())

    json_dict = write_to_json(overall_raid_stats, overall_squad_stats, fights, players, top_total_stat_players, top_average_stat_players, top_consistent_stat_players, top_percentage_stat_players, top_late_players, top_jack_of_all_trades_players, output)

    #print_string = get_fights_overview_string(fights, overall_squad_stats, config)
    print(f'Raid data retrieved')
    return json_dict