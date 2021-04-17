from typing import List
from copy import deepcopy
import numpy as np
from Model import Ant, Game, Map, Resource, ResourceType
from collections import deque
from x_consts import dx, dy


class Position():
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other) -> bool:
        if type(other) == Position and other != None:
            return self.x == other.x and self.y == other.y
        return False

    def __str__(self) -> str:
        return f'x={self.x} y={self.y}'

    def __repr__(self) -> str:
        return f'x={self.x} y={self.y}'


class MapCell():
    def __init__(self, x, y):
        self.position: Position = Position(x, y)
        self.known: bool = False  # seen at least one time
        self.wall: bool = False
        self.resource: Resource = None
        self.resource_seen: int = None  # How many turns passed since we see the resource
        self.ants: Ant = []
        self.base: bool = None  # True = Enemy Base, False = Our Base

    def __eq__(self, other) -> bool:
        if type(other) == MapCell and other != None:
            return self.position == other.position
        return False

    def __str__(self) -> str:
        return f'Cell[{self.position}]'

    def __repr__(self) -> str:
        return f'Cell[{self.position}]'


class Grid():
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.cells = [[MapCell(i, j) for i in range(width)]
                      for j in range(height)]
        # self.bfs_unknown(Position(1, 1), Position(5, 5))

    def __getitem__(self, position: Position):
        return self.cells[position.y][position.x]

    def __setitem__(self, position: Position, value: MapCell):
        self.cells[position.y][position.x] = deepcopy(value)

    def fix_pos(self, pos: Position):
        if pos.x >= self.width:
            pos.x = 0
        if pos.x < 0:
            pos.x = self.width - 1
        if pos.y >= self.height:
            pos.y = 0
        if pos.y < 0:
            pos.y = self.height - 1
        return pos

    def bfs_unknown(self, start: Position, goal: Position):
        """ self[Position(0, 0)].wall = True
        self[Position(1, 0)].wall = True
        self[Position(2, 0)].wall = True
        #self[Position(0, 1)].wall = True
        self[Position(2, 1)].wall = True
        self[Position(0, 2)].wall = True
        self[Position(1, 2)].wall = True
        self[Position(2, 2)].wall = True """

        for i in range(10):
            s = ''
            for j in range(10):
                if self[Position(i, j)].wall == True:
                    s += '#'
                else:
                    s += '-'

            print(s)

        visited: List[MapCell] = []
        q = deque()
        q.append(self[start])

        cntr = 0

        while len(q) > 0:
            cntr += 1
            if cntr == 20:
                break

            cell: MapCell = q.popleft()
            if cell not in visited:
                visited.append(cell)
            if cell == self[goal]:
                print('yea', cell)
                return

            print(cell)

            # handle childs
            for k in range(4):
                pos: Position = self.fix_pos(
                    Position(dx[k] + cell.position.x, dy[k] + cell.position.y))
                if self[pos] not in visited:
                    q.append(self[pos])

        return None


class Env():
    def __init__(self):
        self.game: Game = None
        self.grid: Grid = None
        self.base_pos: Position = None
        #self.task: Task = None

    def init_grid(self, game):
        self.game = game
        self.grid = Grid(self.game.mapWidth, self.game.mapHeight)
        self.base_pos = Position(self.game.baseX, self.game.baseY)

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


g = Grid(20, 30)
g.bfs_unknown(Position(1, 1), Position(10, 5))
