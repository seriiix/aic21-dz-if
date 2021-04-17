from typing import List
from copy import deepcopy
import numpy as np
from Model import Ant, Game, Resource, ResourceType


class MapCell():
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.known: bool = False  # seen at least one time
        self.wall: bool = False
        self.resource: Resource = None
        self.resource_seen: int = None  # How many turns passed since we see the resource
        self.ants: Ant = []
        self.base: bool = None  # True = Enemy Base, False = Our Base


class Grid():
    def __init__(self, width, height):
        self.cells = [[MapCell(i, j) for i in range(width)]
                      for j in range(height)]

    def __getitem__(self, position:Position):
        return self.cells[position.y][position.x]   

    def __setitem__(self, position:Position, value:Cell):
        self.cells[position.y][position.x] = deepcopy(value)


class Position():
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Task:
    def 


class Env():
    def __init__(self):
        self.game: Game = None
        self.grid: Grid = None
        self.width = None
        self.height = None
        self.base_pos: Position = None
        self.task: Task = None

    def init_grid(self, game):
        self.game = game
        self.width = self.game.mapWidth
        self.height = self.game.mapHeight
        self.grid = Grid(self.width, self.height)
        self.base_pos = Position(self.game.baseX, self.game.baseY)
        self.partition_zones()

    def update_walls(self):
        messages = self.game.chatBox.allChats
        for msg in messages:
            pass
            # TODO: update walls

    def x_plus(self, x, dist):
        return (x + dist) % self.width

    def y_plus(self, y, dist):
        return (y + dist) % self.height

    def select_task(self):
        "analyzes the map and trys to get the most important task"
        pass