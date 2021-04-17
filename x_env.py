from typing import List
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


class Position():
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Env():
    def __init__(self):
        self.game: Game = None
        self.grid: Grid = None
        self.width = None
        self.height = None
        self.base_pos: Position = None
        self.Q = []

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

    def partition_zones(self):
        # fuck = [['-' for i in range(self.width)]
        #         for j in range(self.height)]
        zones: List[Position] = []

        i = 0
        while i < self.width:
            if (i / 4) % 2 == 0:
                j = 0
            else:
                j = 4

            while j < self.height:
                zones.append(Position(i, j))
                j += 8
            i += 4

        # for i in range(len(zones)):
        #     zones[i].x = self.x_plus(zones[i].x, self.base_pos.x)
        #     zones[i].y = self.y_plus(zones[i].y, self.base_pos.y)
        #     fuck[zones[i].y][zones[i].x] = '#'

        # fuck[self.base_pos.y][self.base_pos.x] = '$'

        # for i in range(self.height):
        #     cunt = ''
        #     for j in range(self.width):
        #         cunt += fuck[i][j]
        #     print(cunt)

        self.zones = zones
