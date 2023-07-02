#!/usr/bin/env python3


import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

import unittest
import importlib
from io_helper import *
from stat_classes import *

class TestIoHelper(unittest.TestCase):
    def test_get_professions_and_length(self):
        professions = ["Scourge", "Reaper", "Harbinger", "Necromancer",
                       "Vindicator", "Herald", "Revenant", "Renegade",
                       "Guardian", "Willbender", "Dragonhunter", "Firebrand",
                       "Chronomancer", "Mirage", "Mesmer", "Virtuoso",
                       "Elementalist", "Tempest", "Weaver", "Catalyst",
                       "Engineer", "Scrapper", "Holosmith", "Mechanist",
                       "Thief", "Deadeye", "Daredevil", "Specter",
                       "Warrior", "Spellbreaker", "Bladesworn", "Berserker",
                       "Ranger", "Druid", "Soulbeast", "Untamed"
                       ]
        players = list()
        for i in range(len(professions)):
            p = Player("acc", "name"+str(i), professions[i])
            players.append(p)

        parser_config = importlib.import_module("parser_configs.parser_config_detailed" , package=None) 
        config = fill_config(parser_config, None)

        # Test each string and string length individually
        for i in range(len(professions)):
            indices = [i]
            profession_strings, profession_length = get_professions_and_length(players, indices, config)
            self.assertEqual(profession_strings, [professions[i]])
            self.assertEqual(profession_length, len(professions[i]))

        # Test with a few strings
        indices = [0, 3, 14]
        profession_strings, profession_length = get_professions_and_length(players, indices, config)
        self.assertEqual(profession_strings, ["Scourge", "Necromancer", "Mesmer"])
        self.assertEqual(profession_length, len("Necromancer"))

        # Test with some other strings
        indices = [1, 6, 16, 29]
        profession_strings, profession_length = get_professions_and_length(players, indices, config)
        self.assertEqual(profession_strings, ["Reaper", "Revenant", "Elementalist", "Spellbreaker"])
        self.assertEqual(profession_length, len("Spellbreaker"))

        # Test with all strings
        indices = range(len(professions))
        profession_strings, profession_length = get_professions_and_length(players, indices, config)
        self.assertEqual(profession_strings, professions)
        self.assertEqual(profession_length, 12)


    def test_get_total_fight_duration_in_hms(self):
        fight_duration = "11743"
        total_fight_duration = get_total_fight_duration_in_hms(fight_duration)
        self.assertEqual(total_fight_duration['h'], 3)
        self.assertEqual(total_fight_duration['m'], 15)
        self.assertEqual(total_fight_duration['s'], 43)

        fight_duration = "10800"
        total_fight_duration = get_total_fight_duration_in_hms(fight_duration)
        self.assertEqual(total_fight_duration['h'], 3)
        self.assertEqual(total_fight_duration['m'], 0)
        self.assertEqual(total_fight_duration['s'], 0)

        fight_duration = "3600"
        total_fight_duration = get_total_fight_duration_in_hms(fight_duration)
        self.assertEqual(total_fight_duration['h'], 1)
        self.assertEqual(total_fight_duration['m'], 0)
        self.assertEqual(total_fight_duration['s'], 0)

        fight_duration = "60"
        total_fight_duration = get_total_fight_duration_in_hms(fight_duration)
        self.assertEqual(total_fight_duration['h'], 0)
        self.assertEqual(total_fight_duration['m'], 1)
        self.assertEqual(total_fight_duration['s'], 0)

        fight_duration = "6"
        total_fight_duration = get_total_fight_duration_in_hms(fight_duration)
        self.assertEqual(total_fight_duration['h'], 0)
        self.assertEqual(total_fight_duration['m'], 0)
        self.assertEqual(total_fight_duration['s'], 6)

        fight_duration = "0"
        total_fight_duration = get_total_fight_duration_in_hms(fight_duration)
        self.assertEqual(total_fight_duration['h'], 0)
        self.assertEqual(total_fight_duration['m'], 0)
        self.assertEqual(total_fight_duration['s'], 0)

        
if __name__ == '__main__':
    unittest.main()
