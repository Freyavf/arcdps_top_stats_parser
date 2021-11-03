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

The output shows you for each supported stat the 5 (10 for damage and distance to tag) players that achieved top 5 (10) in this stat most often over all fights satisfying the constraints above included in the xml folder. There may be more than 5 (10) players shown if a place is doubled. The number of top players can be changed by command line options:
- ```-n <number_of_top_stats>``` sets the number of players considered to be in top for most stats, i.e. the top n players are considered
- ```-m <number_of_top_stats_dmg_dist>``` sets the number of players considered to be in top for damage and distance to tag, i.e. the top m players are considered for these stats.

For the top players, the number of times that top n (m) was achieved as well as the accumulated stat is given, e.g., the summed up damage over all fights. Additionally, the output gives you the three players with the best total stats. There is a command line option for printing players that achieved top n (m) most often in terms of percentage. This means that only fights in which each player was involved are considered, i.e., someone who was in 8 fights and achieved top n in 4 of them has a percentage of 50%, just as a player who was only in 4 fights and achieved top n in 2 of them.
- ```-p``` enables printing top performing players in terms of percentage

For all stats, players are only listed if they achieve a score that is at least as high as 50% of the top player in that category!

An output file containing the top stats is also generated. By default, it is created in the xml folder as top_stats.txt. The output file can be changed using the command line option ```-o <output_file>```, e.g., ```python parse_top_stats.py -o C:\Users\Example\Documents\test.txt xml_folder``` creates ```test.txt``` in C:\Users\Example\Documents\.

A log file that contains information on which files were skipped is also created in the xml folder as log.txt. It can be changed with the command line option ```-l <log_file>, e.g., ```python parse_top_stats.py -l C:\Users\Example\Documents\test_log.txt xml_folder``` creates ```test_log.txt``` in C:\Users\Example\Documents\.

A call using all command line arguments could be

```python parse_top_stats.py -d 5 -a 7 -n 6 -m 15 -o awesome_stats.txt -p -l mylog.txt xml_folder```

which computes top stats considering all fights contained in
xml_folder that last at least 5s and involve at least 7 players,
prints the 15 players for most top 15 stab and top 15 distance
achieved, prints the top 6 players for each other stat (regarding top
6 achieved top times), prints the 6 (15) players with the highest
percentage of top 6 (15) stats achieved, prints the top 3 players for
each total stat, outputs everything to a file awesome_stats.txt, and
logs the files that were skipped and the reason for it in mylog.txt.