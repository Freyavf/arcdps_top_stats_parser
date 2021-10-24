# arcdps_top_stats_parser

This project provides a tool for generating top stats from a set of arcdps logs. Currently supported stats are: 
- all damage
- boon rips
- cleanses
- stability output (generation squad)
- average distance to tag

To generate the top stats, do the following:
- Install python3 if you don't have it yet (https://www.python.org/downloads/).
- Download this repository or just the file top_stats_parser.py if you don't have it yet. We here assume the path is C:\Users\Example\Downloads\arcdps_top_stats_parser\top_stats_parser.py.
- Generate .xml files from your arcdps logs, e.g., by using a parser like Elite Insights (https://github.com/baaron4/GW2-Elite-Insights-Parser/releases). 
- Put all .xml files you want included in the top stats into one folder. We use the folder C:\Users\Example\Documents\xml_folder as an example here. Note that different file types will be ignored, so no need to move your logs elsewhere if you have them in the same folder.
- Open a windows command line (press Windows key + r, type "cmd", enter).
- Navigate to where the script is located using "cd", in our case this means ```cd Downloads\arcdps_top_stats_parser```.
- Type ```python parse_top_stats.py <folder>```, where \<folder> is the path to your folder with xml files. In our example case, we run ```python parse_top_stats.py C:\Users\Example\Documents\xml_folder```.

The output shows you for each supported stat the three players that achieved top 3 in this stat most often over all fights included in the xml folder. There may be more than three players shown if a place is doubled. For each mentioned player, the number of times that top 3 was achieved as well as the accumulated stat is given, e.g., the summed up damage over all xml fights.
  Additionally, the output gives you the three players with the best total stats.
