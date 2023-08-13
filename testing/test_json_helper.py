#!/usr/bin/env python3

import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

import unittest
import importlib
from stat_classes import *
from json_helper import *

# TODOs
# test getting start of combat
# test getting time of death
# test getting timestamps of tag until death
#

class TestCombatTime(unittest.TestCase):
    def test_get_combat_start_from_player_json(self):
        # player1 initial time 0s, no healthPercents, no powerDamage1S
        player1_dict = {}
        start_combat = get_combat_start_from_player_json(0, player1_dict)
        self.assertEqual(start_combat, -1)
        
        # player2 initial time 0s, empty healthPercents (took no dmg), no powerDamage1S
        player2_dict = {}
        player2_dict['healthPercents'] = list()
        start_combat = get_combat_start_from_player_json(0, player2_dict)
        self.assertEqual(start_combat, -1)
        
        # player3 initial time 0s, empty healthPercents, empty powerDamage1S
        player3_dict = {}
        player3_dict['healthPercents'] = list()
        player3_dict['powerDamage1S'] = list()
        start_combat = get_combat_start_from_player_json(0, player3_dict)
        self.assertEqual(start_combat, -1)

        # player4 initial time 0s, empty healthPercents (took no dmg), dealt power dmg
        player4_dict = {}
        player4_dict['healthPercents'] = list()
        player4_dict['powerDamage1S'] = list()
        player4_dict['powerDamage1S'].append([0, 0, 3, 4, 10])
        start_combat = get_combat_start_from_player_json(0, player4_dict)
        self.assertEqual(start_combat, 2000)

        # player5 initial time 0, took dmg, no powerDamage1S
        player5_dict = {}
        player5_dict['healthPercents'] = list()
        # health going down after 200ms to 98%, then each 100 ms by 1%
        for i in range(2,11):
            player5_dict['healthPercents'].append([i*100,100-i])
        start_combat = get_combat_start_from_player_json(0, player5_dict)
        self.assertEqual(start_combat, 200)

        # player6 initial time 0s, no healthPercents, dealt power dmg
        player6_dict = {}
        player6_dict['powerDamage1S'] = list()
        player6_dict['powerDamage1S'].append([0, 0, 3, 4, 10])
        start_combat = get_combat_start_from_player_json(0, player6_dict)
        self.assertEqual(start_combat, 2000)
        
        # player7 initial time 0s, took dmg before dealing power dmg
        player7_dict = {}
        player7_dict['healthPercents'] = list()
        # health going down after 200ms to 98%, then each 100 ms by 1%
        for i in range(2,11):
            player7_dict['healthPercents'].append([i*100,100-i])
        player7_dict['powerDamage1S'] = list()
        player7_dict['powerDamage1S'].append([0, 0, 3, 4, 10])
        start_combat = get_combat_start_from_player_json(0, player7_dict)
        self.assertEqual(start_combat, 200)

        # player8 initial time 0s, took dmg before dealing power dmg
        player8_dict = {}
        player8_dict['healthPercents'] = list()
        # health going down after 3000ms to 97%, then each 1000 ms by 1%
        for i in range(3,11):
            player8_dict['healthPercents'].append([i*1000,100-i])
        player8_dict['powerDamage1S'] = list()
        player8_dict['powerDamage1S'].append([0, 0, 3, 4, 10])
        start_combat = get_combat_start_from_player_json(0, player8_dict)
        self.assertEqual(start_combat, 2000)
        
        # player9 initial time 10s, empty healthPercents (took no dmg), dealt power dmg only before initial time
        player9_dict = {}
        player9_dict['healthPercents'] = list()
        player9_dict['powerDamage1S'] = list()
        player9_dict['powerDamage1S'].append([0, 0, 3, 4, 10])
        start_combat = get_combat_start_from_player_json(10000, player9_dict)
        self.assertEqual(start_combat, 10000)
        
        # player10 initial time 10s, took dmg only before initial time, dealt power dmg only before initial time
        player10_dict = {}
        player10_dict['healthPercents'] = list()
        # health going down after 3000ms to 97%, then each 1000 ms by 1% until 9000ms
        for i in range(3,9):
            player10_dict['healthPercents'].append([i*1000,100-i])
        player10_dict['powerDamage1S'] = list()
        player10_dict['powerDamage1S'].append([0, 0, 3, 4, 10])
        start_combat = get_combat_start_from_player_json(10000, player10_dict)
        self.assertEqual(start_combat, 10000)
        
        # player11 initial time 10s, took dmg only after inital time, dealt power dmg only before initial time
        player11_dict = {}
        player11_dict['healthPercents'] = list()
        # health going down after 11000ms to 97%, then each 1000 ms by 1% 
        for i in range(11,19):
            player11_dict['healthPercents'].append([i*1000,100-i])
        player11_dict['powerDamage1S'] = list()
        player11_dict['powerDamage1S'].append([0, 0, 3, 4, 10])
        start_combat = get_combat_start_from_player_json(10000, player11_dict)
        self.assertEqual(start_combat, 11000)
        
        # player12 initial time 3s, took dmg only before initial time, dealt power dmg only after inital time
        player12_dict = {}
        player12_dict['healthPercents'] = list()
        # health going down after 100ms to 99%, then each 100 ms by 1% 
        for i in range(1,9):
            player12_dict['healthPercents'].append([i*100,100-i])
        player12_dict['powerDamage1S'] = list()
        player12_dict['powerDamage1S'].append([0, 0, 0, 0, 3, 5])
        start_combat = get_combat_start_from_player_json(3000, player12_dict)
        self.assertEqual(start_combat, 4000)
        
        # player13 inital time 3s, took dmg after inital time, dealt power dmg after inital time
        player13_dict = {}
        player13_dict['healthPercents'] = list()
        # health going down after 5000ms to 95%, then each 1000 ms by 1% 
        for i in range(5,9):
            player13_dict['healthPercents'].append([i*1000,100-i])
        player13_dict['powerDamage1S'] = list()
        player13_dict['powerDamage1S'].append([0, 0, 0, 0, 0, 0, 0, 5])
        start_combat = get_combat_start_from_player_json(3000, player13_dict)
        self.assertEqual(start_combat, 5000)
        
        # player14 inital time 3s, took dmg before and after initial time, only dealt power dmg before initial time
        player14_dict = {}
        player14_dict['healthPercents'] = list()
        # health going down until 2000ms, then again after 5000ms
        for i in range(2):
            player14_dict['healthPercents'].append([i*1000,100-i])
        for i in range(5, 9):
            player14_dict['healthPercents'].append([i*1000,100-i])
        player14_dict['powerDamage1S'] = list()
        player14_dict['powerDamage1S'].append([1, 3, 3, 3, 3, 3, 3, 3, 3])
        start_combat = get_combat_start_from_player_json(3000, player14_dict)
        self.assertEqual(start_combat, 5000)
        
        # player15 initial time 3s, dealth dmg before and after
        player15_dict = {}
        player15_dict['healthPercents'] = list()
        # health going down until 2000ms
        for i in range(2):
            player15_dict['healthPercents'].append([i*1000,100-i])
        player15_dict['powerDamage1S'] = list()
        player15_dict['powerDamage1S'].append([1, 3, 3, 3, 3, 3, 6, 6, 8])
        start_combat = get_combat_start_from_player_json(3000, player15_dict)
        self.assertEqual(start_combat, 6000)

        # player16 initial time 3s, health going only up after initial time, only dmg dealt before initial time
        player16_dict = {}
        player16_dict['healthPercents'] = list()
        # health going down until 2000ms, then going up after 5000ms
        for i in range(3):
            player16_dict['healthPercents'].append([i*1000, 100 - 10 * i])
        for i in range(5, 9):
            player16_dict['healthPercents'].append([i*1000, 100 - 20 + i])
        player16_dict['powerDamage1S'] = list()
        player16_dict['powerDamage1S'].append([1, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4])
        start_combat = get_combat_start_from_player_json(3000, player16_dict)
        self.assertEqual(start_combat, 3000)

#class TestDurations(unittest.TestCase):
#    def test_get_time_in_combat(self):
#        # player1 in combat all the time, no deaths
#        player1 = Player("acc1", "player1", "Scrapper")
#        player1_dict = {}
#        player1_dict['healthPercents'] = list()
#        # health going down each 100 time steps by 1%
#        for i in range(10):
#            player1_dict['healthPercents'].append([i*100,100-i])
#        player1_dict['combatReplayData'] = dict()
#        player1_dict['combatReplayData']['down'] = list()
#        player1_dict['combatReplayData']['dead'] = list()
#        player1_dict['damage1S'] = list()
#
#        
#        if 'dead' not in replay:
#        return [start_combat, get_stat_from_player_json(player_json, 'time_active', None, None, None) * 1000]
#
#        
#        # player2 not in combat from the start, no deaths
#        # player3 in combat from the start, dying once, not entering combat again
#        # player4 in combat from the start, dying once, going back into combat
#        # player5 in combat from the start, dying once, going back into combat, dying again
#        # player6 in combat from the start, dying once, going back into combat, dying again, going back into combat
#        # player7 not in combat from the start, dying once, not entering combat again
#        # player8 not in combat from the start, dying once, going back into combat
#        # player9 not in combat from the start, dying once, going back into combat, dying again
#        # player10 not in combat from the start, dying once, going back into combat, dying again, going back into combat
#        # player11 never took dmg
#                
#    def test_get_time_not_running_back(self):
#        # create tag with timestamps and time of death
#        # create player1 with death before tag
#        # create player2 with death after tag
#        # create player3 too far away
#        # create player4 without death
#        
#        # create tag with timestamps and no death
#        # create player1 with death
#        # create player2 with no death
#        # create player3 too far away
        


if __name__ == '__main__':
    unittest.main()
