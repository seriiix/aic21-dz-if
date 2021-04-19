from typing import List
from enum import Enum
from random import randint, choice
from copy import deepcopy
import numpy as np
from Model import Ant, Direction, Game, Map, Resource, ResourceType, CellType, AntType, AntTeam
from collections import deque
from x_consts import *
from x_helpers import Position


class MapCell():
    def __init__(self, x, y):
        self.position: Position = Position(x, y)
        self.known: bool = False  # seen at least one time
        self.invalid: bool = False  # برای جاهایی که اصلا غیر ممکنه مورچه بره اونجا ها
        self.wall: bool = False  # TODO: wall needs to be None at first because we dont know!
        self.last_seen: int = -np.inf  # How many turns passed since we see the resource

        self.resource: Resource = None
        self.grass_value = 0
        self.bread_value = 0

        self.base: bool = False
        # None means we dont know but false means that it is not! and true is true
        self.enemy_base = None
        # TODO: میشه یه متغیرتعریف کرد که مورچه های اساین شده به منبع رو نشون بده
        self.our_workers = 0
        self.our_soldiers = 0
        self.enemy_workers = 0
        self.enemy_soldiers = 0

    def __eq__(self, other) -> bool:
        if type(other) == MapCell:
            return self.position == other.position
        return False

    def __str__(self) -> str:
        return f'Cell[{self.position}]'

    def __repr__(self) -> str:
        return f'Cell[{self.position}]'

    def get_resource_score(self):
        return self.grass_value * GRASS_SCORE + self.bread_value * BREAD_SCORE

    def set_ants(self, ants):
        self.our_workers = 0
        self.our_soldiers = 0
        self.enemy_workers = 0
        self.enemy_soldiers = 0
        for ant in ants:
            if ant.antTeam == AntTeam.ALLIED.value:
                if ant.antType == AntType.KARGAR.value:
                    self.our_workers += 1
                elif ant.antType == AntType.SARBAAZ.value:
                    self.our_soldiers += 1
            elif ant.antTeam == AntTeam.ENEMY.value:
                if ant.antType == AntType.KARGAR.value:
                    self.enemy_workers += 1
                elif ant.antType == AntType.SARBAAZ.value:
                    self.enemy_soldiers += 1


class Grid():
    def __init__(self, width, height, base_pos):
        self.width = width
        self.height = height
        self.base_pos = base_pos
        self.cells = [[MapCell(i, j) for i in range(width)]
                      for j in range(height)]

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

    def get_direction(self, start: Position, goal: Position):
        path = self.bfs_unknown(start, goal)
        if path is None:
            self[goal].invalid = True
            # TODO: here we should assign INVALID to the cell. Can we deduce more from this?
            return None
        if start == goal:
            return Direction.CENTER

        # print(path)
        # input()

        curr_step = path[0]
        next_step = path[1]

        if self.fix_pos(Position(curr_step.x + 1, curr_step.y)).x == next_step.x:
            return Direction.RIGHT
        if self.fix_pos(Position(curr_step.x - 1, curr_step.y)).x == next_step.x:
            return Direction.LEFT
        if self.fix_pos(Position(curr_step.x, curr_step.y + 1)).y == next_step.y:
            return Direction.DOWN
        if self.fix_pos(Position(curr_step.x, curr_step.y - 1)).y == next_step.y:
            return Direction.UP

        return -1

    def get_strategic_score(self, position: Position, cell: MapCell)-> int:
        if cell.invalid:
            return -np.inf
        # if not cell.known:
        #     return -np.inf

        path = self.bfs_unknown(position, cell.position)
        if not path: 
            return -np.inf
        else:
            distance = len(path)
            path_to_base = self.bfs_unknown(position, self.base_pos)
            distance_to_base = len(path_to_base)
            resource_score = cell.get_resource_score()
            resource_reliableness = cell.last_seen
            self_soldiers_in_cell = cell.our_soldiers
            unknown = int(not cell.known)
            # self_workers_in_cell = cell.get_self_workers_count()

            return distance + distance_to_base + resource_score/ abs(resource_reliableness)
        
    def get_strategic_points(self, position: Position) :
        "returns list of (score, cells) decsending by score "
        cells = []
        for row in self.cells:
            for cell in row:
                cells.append((self.get_strategic_score(position, cell), cell))
        cells.sort(key=lambda item: -item[0])
        return cells

    def where_to_watch(self, position: Position) -> Position:
        # strategic_points = [(position: Position, priority: int)]
        strategic_points = self.get_strategic_points(position)
        # TODO: may be we can add some randomness here if needed
        best_point_score, best_point = strategic_points[0]
        if self.get_strategic_score(position, self[position]) != best_point_score:
            return best_point.position
        else:
            return position

    def update_last_seens(self):
        for row in self.cells:
            for cell in row:
                cell.last_seen -= 1

    def get_harvest_location(self, position: Position) -> Position:
        # we assume the nearest location is the best
        # TODO: but may be there are better choices!
        locations = [self[Position(x, y)].position for x in range(self.width) for y in range(self.height)
                     if self[Position(x, y)].resource]
        min_distance = np.inf
        min_location = None
        for location in locations:
            path = self.bfs_unknown(position, location)
            distance = len(path) if path is not None else np.inf
            # distance = location - position
            if distance < min_distance:
                min_distance = distance
                min_location = location

        return min_location

    def get_neighbour(self, position, direction):
        if direction == Direction.RIGHT:
            return self.fix_pos(Position(position.x+1, position.y))
        elif direction == Direction.LEFT:
            return self.fix_pos(Position(position.x-1, position.y))
        elif direction == Direction.DOWN:
            return self.fix_pos(Position(position.x, position.y+1))
        elif direction == Direction.UP:
            return self.fix_pos(Position(position.x, position.y-1))
        elif direction == Direction.CENTER:
            return Position(position.x, position.y)

    def is_good_to_explore(self, position):
        return self[position].known == False and self[position].invalid == False and self[position].wall == False

    def get_seen_cells_neighbours(self):
        directions = [Direction.RIGHT, Direction.LEFT,
                      Direction.UP, Direction.DOWN]
        locations = []
        for row in self.cells:
            for cell in row:
                if cell.known:
                    for direction in directions:
                        position = self.get_neighbour(cell.position, direction)
                        if self.is_good_to_explore(position) and not position in locations:
                            locations.append(position)
        print(locations)
        return locations

    def get_explore_location(self, start: Position) -> Position:
        # currently we just pick a random unseen but near to seens position
        locations = self.get_seen_cells_neighbours()
        return choice(locations) if len(locations) else start


class TaskType(Enum):
    EXPLORE = 0
    HARVEST = 1
    RETURN = 2

    WATCH = 3


class Task:
    def __init__(self, type: TaskType, destination: Position):
        self.type: TaskType = type
        self.destination: Position = destination

    def __str__(self):
        return f"Task(type={self.type}, dest={self.destination})"


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
        self.base_pos = Position(self.game.baseX, self.game.baseY)
        self.grid = Grid(self.game.mapWidth, self.game.mapHeight, self.base_pos)
        self.grid[self.base_pos].base = True
        self.position = Position(
            self.game.ant.currentX, self.game.ant.currentY)

    def add_vision_to_map(self) -> None:
        "the ant adds its vision information to the grid"
        vision = self.game.ant.visibleMap
        for cell_row in vision.cells:
            for cell in cell_row:
                if cell:
                    cell_pos = Position(cell.x, cell.y)

                    self.grid[cell_pos].last_seen = 0

                    self.grid[cell_pos].known = True

                    # WALL
                    if cell.type == CellType.WALL.value:
                        self.grid[cell_pos].wall = True
                    else:
                        self.grid[cell_pos].wall = False

                    # RESOURCES
                    if cell.resource_type == ResourceType.BREAD.value:
                        self.grid[cell_pos].resource = Resource(
                            ResourceType.BREAD.value, cell.resource_value)
                        self.grid[cell_pos].bread_value = cell.resource_value
                    if cell.resource_type == ResourceType.GRASS.value:
                        self.grid[cell_pos].resource = Resource(
                            ResourceType.GRASS.value, cell.resource_value)
                        self.grid[cell_pos].grass_value = cell.resource_value
                    if cell.resource_value == 0:
                        self.grid[cell_pos].resource = None
                        self.grid[cell_pos].bread_value = 0
                        self.grid[cell_pos].grass_value = 0
                
                    # ANTS
                    self.grid[cell_pos].set_ants(cell.ants)                    

                    # ENEMY BASE
                    if cell.type == CellType.BASE.value:
                        if not cell_pos == self.base_pos:
                            self.grid[cell_pos].enemy_base = True
                            # TODO: here we can set to False all other cells but may be not necessary
                    else:
                        self.grid[cell_pos].enemy_base = False
        self.grid.update_last_seens()

    def update_grid(self):
        # own vision
        self.add_vision_to_map()

        # from messages
        messages = self.game.chatBox.allChats
        for msg in messages:
            break
            # TODO: update walls

    def update_task(self):
        "analyzes the map and trys to get the most important task"
        if self.game.ant.antType == AntType.KARGAR.value:
            if self.task:
                if self.task.type == TaskType.RETURN:
                    if self.position == self.base_pos:
                        self.task = None
                        return self.update_task()
                    else:
                        return

                elif self.task.type == TaskType.HARVEST:
                    # TODO: resource threshold
                    if self.game.ant.currentResource and self.game.ant.currentResource.value > 0:
                        self.task = Task(type=TaskType.RETURN,
                                         destination=self.base_pos)
                        return

                    harvest_location = self.grid.get_harvest_location(
                        self.position)
                    if not harvest_location:  # Resource has been eaten by others
                        self.task = None
                        self.update_task()
                        return
                    elif harvest_location != self.task.destination:
                        self.task = Task(type=TaskType.HARVEST,
                                         destination=harvest_location)
                        return
                    else:
                        return

                elif self.task.type == TaskType.EXPLORE:
                    harvest_location = self.grid.get_harvest_location(
                        self.position)
                    if harvest_location:
                        self.task = Task(type=TaskType.HARVEST,
                                         destination=harvest_location)
                        return
                    if not self.grid.is_good_to_explore(self.task.destination):
                        self.task = None
                        self.update_task()
                    if self.position == self.task.destination:
                        self.task = None
                        self.update_task()

            elif not self.task:
                harvest_location = self.grid.get_harvest_location(
                    self.position)
                if harvest_location:
                    self.task = Task(type=TaskType.HARVEST,
                                     destination=harvest_location)
                    return
                else:
                    destination = self.grid.get_explore_location(self.position)
                    self.task = Task(type=TaskType.EXPLORE,
                                     destination=destination)
                    return
        elif self.game.ant.antType == AntType.SARBAAZ.value:
            destination = self.grid.where_to_watch(self.position)
            self.task = Task(TaskType.WATCH, destination)

    def run_one_turn(self):
        self.position = Position(
            self.game.ant.currentX, self.game.ant.currentY)
        self.update_grid()
        self.update_task()
        print(self.task)
        direction = self.grid.get_direction(
            self.position, self.task.destination)
        if not direction:
            self.task = None
            direction = Direction.CENTER.value
            print("=====WAITING=====")
            # TODO: here waits for 1 turn. can we do better?
        print(direction)
        message = "asd"
        value = 2
        return message, value, direction.value
