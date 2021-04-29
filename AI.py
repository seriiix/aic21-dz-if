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

        # FOR DEBUG ONLY
        self.DEBUG = False
        self.DEBUG_MOVES = [Direction.LEFT, Direction.DOWN, Direction.DOWN,
                            Direction.DOWN, Direction.DOWN, Direction.DOWN, Direction.DOWN, Direction.DOWN, Direction.DOWN, Direction.DOWN]

    def get_debug_move(self) -> Direction:
        if self.ant_turn_number <= len(self.DEBUG_MOVES):
            return self.DEBUG_MOVES[self.ant_turn_number - 1]
        return Direction.CENTER


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
        try:
            message, value, direction = brain.env.run_one_turn(brain.ant_id)
        except Exception as e:
            import traceback
            h = traceback.format_exc()
            message, value, direction = h, 404, 0
        # print(e)
        # return (message,value, direction)
        if brain.DEBUG:
            return (message, value, brain.get_debug_move().value)

        return (message, value, direction)
