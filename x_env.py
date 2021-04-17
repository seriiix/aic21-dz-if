from typing import List
from enum import Enum
from random import randint
from copy import deepcopy
import numpy as np
from Model import Ant, Game, Resource, ResourceType


class Position():
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other: Position):
        return self.x == other.x and self.y == other.y

    def __sub__(self, other):
        "Manhatan distance"
        return abs(self.x - other.x) + abs(self.y - other.y)


class MapCell():
    def __init__(self, x, y):
        self.position = Position(x, y)
        self.known: bool = False  # seen at least one time
        self.wall: bool = False
        self.resource: Resource = None
        self.resource_seen: int = None  # How many turns passed since we see the resource
        self.ants: Ant = []
        self.base: bool = None  # True = Enemy Base, False = Our Base
        # TODO: میشه یه متغیرتعریف کرد که مورچه های اساین شده به منبع رو نشون بده


class Grid():
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.cells = [[MapCell(i, j) for i in range(width)]
                      for j in range(height)]

    def __getitem__(self, position:Position):
        return self.cells[position.y][position.x]   

    def __setitem__(self, position:Position, value:MapCell):
        self.cells[position.y][position.x] = deepcopy(value)
    
    def get_harvest_location(self, position:Position)-> Position:
        # we assume the nearest location is the best
        # TODO: but may be there are better choices!
        locations = [self[Position(x,y)] for x in range(self.width) for y in range(self.height) 
                        if self[Position].resource]
        min_distance = np.inf
        min_location = None
        for location in locations:
            distance = location - position
            if distance < min_distance:
                min_distance = distance
                min_location = location

        return min_location
        
    def get_explore_location(self)-> Position:
        # TODO
        return Position(randint(0, self.height), randint(0, self.width))


class TaskType(Enum):
    EXPLORE = 0
    HARVEST = 1
    RETURN = 2


class Task:
    def __init__(self, type:TaskType, destination:Position):
        self.type:TaskType = type
        self.destination:Position = destination


class Env():
    def __init__(self):
        self.game: Game = None
        self.grid: Grid = None
        self.base_pos: Position = None
        self.task: Task = None
        self.position: Position = None
        self.ant: Ant = None

    def init_grid(self, game):
        self.game = game
        self.grid = Grid(self.game.mapWidth, self.game.mapHeight)
        self.base_pos = Position(self.game.baseX, self.game.baseY)
        self.position = Position(self.game.ant.x, self.game.ant.y)
        self.ant = self.game.ant

    def update_walls(self):
        messages = self.game.chatBox.allChats
        for msg in messages:
            pass
            # TODO: update walls

    def update_task(self):
        "analyzes the map and trys to get the most important task"
        if self.task:
            if self.task.type == TaskType.RETURN:
                if self.position == self.base_pos:
                    self.task = None
                    return self.update_task()
                else:
                    return

            elif self.task.type == TaskType.HARVEST:
                if self.ant.resource:
                    self.task = Task(type=TaskType.RETURN, destination=self.base_pos)
                    return

                harvest_location = self.grid.get_harvest_location(self.position)
                if harvest_location != self.task.destination:
                    self.task = Task(type=TaskType.HARVEST, destination=harvest_location)
                    return
                else:
                    return

            elif self.task.type == TaskType.EXPLORE:
                harvest_location = self.grid.get_harvest_location(self.position)
                if harvest_location:
                    self.task = Task(type=TaskType.HARVEST, destination=harvest_location)
                    return

        elif not self.task:
            harvest_location = self.grid.get_harvest_location(self.position)
            if harvest_location:
                self.task = Task(type=TaskType.HARVEST, destination=harvest_location)
                return
            else:
                destination = self.grid.get_explore_location()
                self.task = Task(type=TaskType.EXPLORE, destination=destination)
                return