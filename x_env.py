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
        if type(other) == Position:
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
        if type(other) == MapCell:
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
        if start == goal:
            return [start]
        visited = np.zeros((self.height, self.width))
        queue = deque([(start, [])])

        while queue:
            current, path = queue.popleft()
            visited[current.y][current.x] = 1

            for k in range(4):
                x_ = dx[k] + current.x
                y_ = dy[k] + current.y
                neighbor = self.fix_pos(Position(x_, y_))
                if neighbor == goal:
                    return path + [current, neighbor]
                if visited[neighbor.y][neighbor.x] == 0 and self[neighbor].wall == False:
                    queue.append((neighbor, path + [current]))
                    visited[neighbor.y][neighbor.x] = 1

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
