# What is it all about? #

Did you ever wonder how well you did compared to your squad mates, not only in a single fight, but over the whole raid? Do you want to know who to ask for help with a specific class? Or do you want to hand out an award to a guildie who did the most damage in all raids over a whole week? This project provides a tool for generating top stats from a set of arcdps logs, allowing you to easily identify top performing players in different stats.
Currently supported stats are: 
- all damage
- damage dealt to target (in wvw: equivalent to damage dealt to players)
- damage dealt to everything else (in wvw: siege, npcs, ...)
- all condition damage
- condition damage dealt to target (in wvw: equivalent to damage dealt to players)
- condition damage dealt to everything else (in wvw: siege, npcs, ...)
- all power damage
- power damage dealt to target (in wvw: equivalent to damage dealt to players)
- power damage dealt to everything else (in wvw: siege, npcs, ...)
- spike damage (maximum damage dealt within 1s)
- killing hits
- downing hits
- damage against downed players
- down contribution
- boon rips
- interrupts
- cleanses
- dodges
- blocks
- stability (output to squad, uptime)
- protection (output to squad, uptime)
- aegis (output to squad, uptime)
- resistance (output to squad, uptime)
- resolution (output to squad, uptime)
- quickness (output to squad, uptime)
- might (output to squad, uptime)
- fury (output to squad, uptime)
- alacrity (output to squad, uptime)
- superspeed (output to squad, uptime)
- swiftness (output to squad, uptime)
- vigor (output to squad, uptime)
- stealth (output to squad, uptime)
- all healing output
- healing dealt to target (in wvw: equivalent to healing on players)
- healing dealt to everything else (in wvw: npcs, pets, ...)
- healing from regen
- barrier output
- resurrects
- average distance to tag
- stripped boons (boons that were stripped from the player)
- total damage taken
- damage absorbed by barrier
- hp lost (= total damage taken - damage absorbed by barrier)
- condition damage taken
- power damage taken
- downstates
- deaths

Healing and barrier output can only be analyzed when contained in the logs, i.e., the [healing addon for arcdps](https://github.com/Krappa322/arcdps_healing_stats/releases) is installed. They will only be analyzed for players who also have the addon installed, since data may be incomplete for others.

The script ```parse_top_stats_detailed.py``` shows the performance of all players contributing to each desired stat considering total values, average values, consistency and percentage of top stats reached for all desired stats.

Output is given as .xlsx and .json file for further processing. 
Here are some example output files: ![example output](/example_output/). They are explained in detail on the ![wiki](https://github.com/Freyavf/arcdps_top_stats_parser/wiki/Output-Files).

Note that currently, this tool is meant mainly for analyzing wwv fights, and I am not sure how applicable it is for pve raids since I don't do them - feel free to test and give me a shout if anything is not working though (contact details below).

# How does it work? #
## Preparation ##
To be able to generate the top stats, you need to install/download a few things.
1. Install python3 if you don't have it yet (https://www.python.org/downloads/).
2. Get the Elite Insights parser for arcdps logs (https://github.com/baaron4/GW2-Elite-Insights-Parser/releases). For parsing including barrier, you will need version 2.41 or higher. In the following, we assume the path to it is ```C:\Users\Example\Downloads\EliteInsights\```.
3. Download this repository if you don't have it yet. We here assume the path is ```C:\Users\Example\Downloads\arcdps_top_stats_parser\```.
4. Install the necessary python dependencies if you don't have them yet: Open a terminal (on windows press windows key + r, type "cmd", enter), go to the folder where you put the repository by typing ```cd Downloads\arcdps_top_stats_parser```, enter, and type ```pip3 install -r requirements.txt```, enter.


There are two methods for generating the top stats, one requires more manual control, the other is more automated.
## Manual Top Stats Generation ##
1. Generate .json files from your arcdps logs by using Elite Insights. Enable detailed wvw parsing and combat replay computation. You can also use the EI settings file stored in this repository under ```EI_config\EI_detailed_json_combat_replay.conf```, which will generate .json files with detailed wvw parsing and combat replay.
2. Put all .json files you want included in the top stats into one folder. We use the folder ```C:\Users\Example\Documents\json_folder``` as an example here. Note that different file types will be ignored, so no need to move your .evtc/.zevtc logs elsewhere if you have them in the same folder.
3. Open a terminal / windows command line (press Windows key + r, type "cmd", enter).
4. Navigate to where the script is located using "cd", in our case this means ```cd Downloads\arcdps_top_stats_parser```.
5. Type ```python parse_top_stats_detailed.py <folder>```, where \<folder> is the path to your folder with json files. In our example case, we run ```python parse_top_stats_detailed.py C:\Users\Example\Documents\json_folder```.

## Automated Top Stats Generation ##
For a more automated version, you can use the batch script ```parsing_arc_top_stats.bat``` as follows:
1. Move all logs you want included in the stats in one folder. We will use ```C:\Users\Example\Documents\log_folder\``` as an example.
2. Open a windows command line (press Windows key + r, type "cmd", enter).
3. Type ```<repo_folder>\parsing_arc_top_stats.bat "<log_folder>" "<Elite Insights folder>" "<repo_folder>"```. The full call in our example would be ```C:\Users\Example\Downloads\arcdps_top_stats_parser\parsing_arc_top_stats.bat "C:\Users\Example\Documents\log_folder\" "C:\Users\Example\Downloads\EliteInsights\" "C:\Users\Example\Downloads\arcdps_top_stats_parser\"```. This parses all logs in the log folder using EI with suitable settings and runs both scripts for generating the overview and detailed stats.

## Output ##
Output files containing the tops stats are also generated in the input folder. By default, a top_stats_detailed.xlsx and a top_stats_detailed.json file with the same names are also created. Furthermore, a log file that contains information on which files were skipped and why is also created in the input folder as ```log_detailed.txt```. 

## Settings ##
For changing any of the default settings, check out the wiki pages on ![command line options](https://github.com/Freyavf/arcdps_top_stats_parser/wiki/Command-line-options) and ![configuration options](https://github.com/Freyavf/arcdps_top_stats_parser/wiki/Configuration-options).

# Getting involved

If you find this tool helpful, you can make a donation to support it: [![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/donate/?hosted_button_id=C5CSPXYHBGR2U) 

Ingame donations are also welcome on the account Freya.1384. If you have any ideas or suggestions for further improvements, let me know ingame or by email (freya.arcdps.topstats@gmail.com). Please note that I might not have time to reply right away, but I will try to come back to you. Thank you :)
