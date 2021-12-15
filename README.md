# What is it all about? #

Did you ever wonder how well you or your squad mates did, not only in a single fight, but over the whole raid? Do you want to know who to ask for help with a specific class? Or do you want to hand out an award to a guildie who did the most damage in all raids over a whole week? This projects provides a tool for generating top stats from a set of arcdps logs, allowing you to easily identify top performing players in different stats.
Currently supported stats are: 
- all damage
- boon rips
- cleanses
- stability output (generation squad)
- healing output
- average distance to tag

Healing output can only be analyzed when contained in the logs, i.e., the healing addon for arcdps is installed.

Provided are three scripts: ```parse_top_stats_sneak_peek.py```, ```parse_top_stats_overview.py``` and ```parse_top_stats_detailed.py```. The first gives an overview of the best performing players only in total damage, boon rips and cleanses. The second gives an overview of top players considering consistency and total values of all stats. The third shows the performance of all players contributing to each stat.

Here is an example txt output file: ![example output](/example_output/top_stats_detailed.txt?raw=true).
Output is also given as .xls file for further processing. I'm planning to add more example output files soon<sup>TM</sup>.

# How does it work? #
## Preparation ##
To be able to generate the top stats, you need to install/download a few things.
1. Install python3 if you don't have it yet (https://www.python.org/downloads/).
2. Install xlrd, xlutils and xlwt it you don't have them yet: Open a terminal (on windows press windows key + r, type "cmd", enter), and type ```pip3 install xlrd xlutils xlwt```, enter.
3. Get the Elite Insights parser for arcdps logs (https://github.com/baaron4/GW2-Elite-Insights-Parser/releases). In the following, we assume the path to it is ```C:\Users\Example\Downloads\EliteInsights\```.
4. Download this repository if you don't have it yet. We here assume the path is ```C:\Users\Example\Downloads\arcdps_top_stats_parser\```.

There are two methods for generating the top stats, one requires more manual control, the other is more automated.
## Manual Top Stats Generation ##
1. Generate .xml files from your arcdps logs by using Elite Insights. Enable detailed wvw parsing. You can also use the settings file stored in this repository under ```EI_config\detailed_wvw_parsing-output_xml.conf```.
2. Put all .xml files you want included in the top stats into one folder. We use the folder ```C:\Users\Example\Documents\xml_folder``` as an example here. Note that different file types will be ignored, so no need to move your logs elsewhere if you have them in the same folder.
3. Open a terminal / windows command line (press Windows key + r, type "cmd", enter).
4. Navigate to where the script is located using "cd", in our case this means ```cd Downloads\arcdps_top_stats_parser```.
5. Type ```python parse_top_stats_overview.py <folder>```, where \<folder> is the path to your folder with xml files. In our example case, we run ```python parse_top_stats_overview.py C:\Users\Example\Documents\xml_folder```. For the detailed version, use ```parse_top_stats_detailed.py``` instead of ```parse_top_stats_overview.py```, and for the sneak peak use ```parse_top_stats_sneak_peek.py```.

## Automated Top Stats Generation ##
For a more automated version, you can use the batch script ```parsing_arc_top_stats.bat``` as follows:
1. Move all logs you want included in the stats in one folder. We will use ```C:\Users\Example\Documents\log_folder\``` as an example.
2. Open a windows command line (press Windows key + r, type "cmd", enter).
3. Type ```<repo_folder>\parsing_arc_top_stats.bat "<log_folder>" "<Elite Insights folder>" "<repo_folder>"```. The full call in our example would be ```C:\Users\Example\Downloads\arcdps_top_stats_parser\parsing_arc_top_stats.bat "C:\Users\Example\Documents\log_folder\" "C:\Users\Example\Downloads\EliteInsights\" "C:\Users\Example\Downloads\arcdps_top_stats_parser\"```. This parses all logs in the log folder using EI with suitable settings and runs all three scripts for generating the sneak peek, overview and detailed stats.

## Output ##
The console output shows you for each supported stat consistency and total awards, and "late but great" and "Jack of all trades" awards if applicable.
Consistency awards are given for players with top scores in the most fights. Total awards are given for overall top stats. Late but great awards are given to players who weren't there for all fights, but who achieved great consistency in the time they were there. Jack of all trades awards are given to people who swapped build at least once and achieved great consistency on one of their builds.

An output file containing the top stats is also generated. By default, it is created in the xml folder as ```top_stats_overview.txt``` or ```top_stats_detailed.txt```, respectively. The output file can be changed using the command line option ```-o <output_file>```, e.g., ```python parse_top_stats_overview.py -o C:\Users\Example\Documents\test.txt xml_folder``` creates ```test.txt``` in ```C:\Users\Example\Documents\```. A second output file in .xls format is generated. It has the same default name as the .txt files, which can be changed with the command line option ```-x```.

A log file that contains information on which files were skipped and why is also created in the xml folder as ```log_overview.txt``` or ```log_detailed.txt```. It can be changed with the command line option ```-l <log_file>```, e.g., ```python parse_top_stats_overview.py -l C:\Users\Example\Documents\test_log.txt xml_folder``` creates ```test_log.txt``` in ```C:\Users\Example\Documents\```.

## Settings ##
Settings are defined in a config file. By default, the overview parsing uses the file ```parser_configs/parser_config_overview.py```, the detailed parsing uses ```parser_configs/parser_config_detailed.py```, and the sneak peek parsing uses ```parser_configs/parser_config_sneak_peek.py```. You can copy one of the config files in the same folder, rename it and adjust the settings to your liking. Using a different config file can be done by adding ```-c <config_file>``` in the command line call (without the folder name and the ```.py``` ending of the filename).

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

# Getting involved

If you find this tool helpful, you can make a donation to support it: [![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/donate/?hosted_button_id=C5CSPXYHBGR2U) 

Ingame donations are also welcome on the account Freya.1384. If you have any ideas or suggestions for further improvements, let me know ingame or by email (freya.arcdps.topstats@gmail.com). Please note that I might not have time to reply right away, but I will try to come back to you. Thank you :)
