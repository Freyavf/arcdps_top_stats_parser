for %%i in (%1\*.zevtc) do (%2\GuildWars2EliteInsights.exe -c %3\EI_config\detailed_wvw_parsing-output_json.conf "%%i")
python %3/parse_top_stats_sneak_peek.py %1
python %3/parse_top_stats_overview.py %1
python %3/parse_top_stats_detailed.py %1
