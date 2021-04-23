from Model import *
import random
import json
from typing import *
from random import randint
from x_env import Env

class Brain:
    def __init__(self):
        self.env = Env()
        self.ant_id = randint(0, 2 ^ 12 - 1)
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
        # print(brain.ant_turn_number)
        # try:
        message, value, direction = brain.env.run_one_turn(brain.ant_id)
        # except Exception as e:
            # message, value, direction = str(e) if len(str(e))<32 else str(e)[0:31], 103, 0
            # print(e)
            # return (message,value, direction)

        return (message, value, direction)
