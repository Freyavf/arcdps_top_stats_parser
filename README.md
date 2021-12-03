# arcdps_top_stats_parser

This project provides a tool for generating top stats from a set of arcdps logs. Currently supported stats are: 
- all damage
- boon rips
- cleanses
- stability output (generation squad)
- healing output
- average distance to tag

Healing output can only be analyzed when contained in the logs, i.e., the healing addon for arcdps is installed.

Provided are two scripts: ```parse_top_stats_overview.py``` and ```parse_top_stats_detailed.py```. The first gives an overview of the best performing players. The second shows the performance of all players contributing to each stat.

To generate the top stats, do the following:
- Install python3 if you don't have it yet (https://www.python.org/downloads/).
- Download this repository or just the file top_stats_parser.py if you don't have it yet. We here assume the path is C:\Users\Example\Downloads\arcdps_top_stats_parser\top_stats_parser.py.
- Generate .xml files from your arcdps logs, e.g., by using a parser like Elite Insights (https://github.com/baaron4/GW2-Elite-Insights-Parser/releases). Enable detailed wvw parsing.
- Put all .xml files you want included in the top stats into one folder. We use the folder C:\Users\Example\Documents\xml_folder as an example here. Note that different file types will be ignored, so no need to move your logs elsewhere if you have them in the same folder.
- Open a windows command line (press Windows key + r, type "cmd", enter).
- Navigate to where the script is located using "cd", in our case this means ```cd Downloads\arcdps_top_stats_parser```.
- Type ```python parse_top_stats_overview.py <folder>```, where \<folder> is the path to your folder with xml files. In our example case, we run ```python parse_top_stats_overview.py C:\Users\Example\Documents\xml_folder```. For the detailed version, use ```parse_top_stats_detailed.py``` instead of ```parse_top_stats_overview.py```.

The output shows you for each supported stat consistency and total awards, and "late but great" and "Jack of all trades" awards if applicable.
Consistency awards are given for players with top scores in the most fights. Total awards are given for overall top stats. Late but great awards are given to players who weren't there for all fights, but who achieved great consistency in the time they were there. Jack of all trades awards are given to people who build swapped at least once and achieved great consistency on one of their builds.

An output file containing the top stats is also generated. By default, it is created in the xml folder as ```top_stats_overview.txt``` or ```top_stats_detailed.txt```, respectively. The output file can be changed using the command line option ```-o <output_file>```, e.g., ```python parse_top_stats_overview.py -o C:\Users\Example\Documents\test.txt xml_folder``` creates ```test.txt``` in ```C:\Users\Example\Documents\```.

A log file that contains information on which files were skipped and why is also created in the xml folder as ```log_overview.txt``` or ```log_detailed.txt```. It can be changed with the command line option ```-l <log_file>```, e.g., ```python parse_top_stats_overview.py -l C:\Users\Example\Documents\test_log.txt xml_folder``` creates ```test_log.txt``` in ```C:\Users\Example\Documents\```.

Settings are defined in a config file. By default, the overview parsing uses the file ```parser_configs/parser_config_overview.py```, and the detailed parsing uses ```parser_configs/parser_config_detailed.py```. You can copy one of the config files in the same folder, rename it and adjust the settings to your liking. Using a different config file can be done by adding ```-c <config_file>``` in the command line call (without the folder name and the ```.py``` ending of the filename).

These settings are available:
- num_players_listed: Maximum number of players listed for each stat in the consistency and damage awards (dictionary).
- num_players_considered_top: Number of players considered "top" in each fight (dictionary).
- percentage_of_top_for_consistent: Based on the total value that the top consistent player reached. Defines the percentage of this value that has to be achieved to be able to get a consistency award.
- percentage_of_top_for_total: Based on the total value that the top total player reached. Defines the percentage of this value that has to be achieved to be able to get a total award.
- percentage_of_top_for_late: Based on the percentage of times the top consistent player achieved top stats in relation to the number of fights they were present. Defines the percentage of this value that has to be achieved in number of top stats achieved divided by number of fights a player was present.
- percentage_of_top_for_buildswap: Based on the percentage of times the top consistent player achieved top stats in relation to the number of fights they were present. Defines the percentage of this value that has to be achieved in number of top stats achieved divided by number of fights a player was present.
- attendance_percentage_for_late: Percentage of fights a player has to be present out of all fights to be considered for a late but great award.
- attendance_percentage_for_buildswap: Percentage of fights a player has to be present on one build out of all fights to be considered for a jack of all trades award.
- min_allied_players: The minimum number of allied players to consider a fight in the stats computation.
- min_fight_duration: The minimum duration of a fight to consider it in the stats computation.
- min_enemy_players: The minimum number of enemy players to consider a fight in the stats computation.
- profession_abbreviations: For each profession, the name it appears as in the stats.
- stat_names: The name as which each stat appears.
