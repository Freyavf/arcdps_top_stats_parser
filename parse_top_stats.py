#!/usr/bin/env python3.9
from dataclasses import dataclass


@dataclass
class Player:
    account: str
    name: str
    profession: str
    num_fights_present: int = 0
    duration_fights_present: int = 0
    
    total_dmg: int = 0
    total_rips: int = 0
    total_stab: float = 0.
    total_cleanses: int = 0
    total_heal: int = 0

    num_top_x_dmg: int = 0
    num_top_x_rips: int = 0
    num_top_x_stab: int = 0
    num_top_x_cleanses: int = 0
    num_top_x_heal: int = 0
    num_top_x_dist: int = 0

    percentage_top_x_dmg: int = 0
    percentage_top_x_rips: int = 0
    percentage_top_x_stab: int = 0
    percentage_top_x_cleanses: int = 0
    percentage_top_x_heal: int = 0
    percentage_top_x_dist: int = 0


    
p = Point(1.5, 2.5)

print(p)  # Point(x=1.5, y=2.5, z=0.0)
