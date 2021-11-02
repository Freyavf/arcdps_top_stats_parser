# arcdps_top_stats_parser

This project provides a tool for generating top stats from a set of arcdps logs. Currently supported stats are: 
- all damage
- boon rips
- cleanses
- stability output (generation squad)
- healing output
- average distance to tag

Healing output can only be analyzed when contained in the logs, i.e., the healing addon for arcdps is installed.

To generate the top stats, do the following:
- Install python3 if you don't have it yet (https://www.python.org/downloads/).
- Download this repository or just the file top_stats_parser.py if you don't have it yet. We here assume the path is C:\Users\Example\Downloads\arcdps_top_stats_parser\top_stats_parser.py.
- Generate .xml files from your arcdps logs, e.g., by using a parser like Elite Insights (https://github.com/baaron4/GW2-Elite-Insights-Parser/releases). 
- Put all .xml files you want included in the top stats into one folder. We use the folder C:\Users\Example\Documents\xml_folder as an example here. Note that different file types will be ignored, so no need to move your logs elsewhere if you have them in the same folder.
- Open a windows command line (press Windows key + r, type "cmd", enter).
- Navigate to where the script is located using "cd", in our case this means ```cd Downloads\arcdps_top_stats_parser```.
- Type ```python parse_top_stats.py <folder>```, where \<folder> is the path to your folder with xml files. In our example case, we run ```python parse_top_stats.py C:\Users\Example\Documents\xml_folder```.

By default, all fights that took less than 30s or included less than 10 allied players are filtered out. To change these settings, use the command line options:
- ```-d <duration>``` sets the minimum fight duration to \<duration> in s
- ```-a <num_allies>``` sets the minimum number of allied players to \<num_allies>

As an example, running ```python parse_top_stats.py -d 5 -a 7 xml_folder``` will generate the top stats on all xml files in xml_folder with a duration of at least 5s and at least 7 players involved.

The output shows you for each supported stat the three players that achieved top 3 in this stat most often over all fights satisfying the above constraints included in the xml folder. There may be more than three players shown if a place is doubled. The number of players that gets printed can be changed via command line option:
- ```-n <number of players>``` sets the number of top players that get printed to \<number of players>

For the top players, the number of times that top 3 was achieved as well as the accumulated stat is given, e.g., the summed up damage over all fights. Additionally, the output gives you the players with the best total stats. There is a command line option for printing players that achieved top 3 most often in terms of percentage. This means that only fights in which each player was involved are considered, i.e., someone who was in 4 fights and achieved top 3 in 2 of them has a percentage of 50%, just as a player who was only in 2 fights and achieved top 3 in 1 of them.
- ```-p``` enables printing top performing players in terms of percentage

An output file containing the top stats is also generated. By default, it is created in the xml folder as top_stats.txt. The output file can be changed using the command line option ```-o <output_file>```, e.g., ```python parse_top_stats.py -o C:\Users\Example\Documents\test.txt xml_folder``` creates ```test.txt``` in C:\Users\Example\Documents\.

A call using all command line arguments could be
```python parse_top_stats.py -d 5 -a 7 -o awesome_stats.txt -n 6 -p xml_folder```

which results in computing top stats considering all fights contained in xml_folder that last at least 5s, involve at least 7 players, prints the top 6 players for each stat, prints the players with the highest percentage of top stats achieved, and outputs everything to a file awesome_stats.txt.