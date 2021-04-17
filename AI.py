from Model import *
import random
import json
from typing import *
from random import randint
from x_env import Env


class Brain:
    def __init__(self):
        self.env = Env()
        self.ant_id = randint(0, 2 ^ 16 - 1)
        self.ant_turn_number = 0


brain = Brain()


class AI:
    def __init__(self):
        # Current Game State
        self.game: Game = None

    def turn(self):
        if brain.ant_turn_number == 0:
            brain.env.init_grid(self.game)
        brain.env.game = self.game

        brain.ant_turn_number += 1

        return ('asd', 2, 1)
