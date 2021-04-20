from random import randint, choice, shuffle
from copy import deepcopy
from collections import deque
from typing import List
import numpy as np


from Model import Ant, Direction, Game, Map, Resource, ResourceType, CellType, AntType, AntTeam
from x_consts import *
from x_helpers import Position


class MapCell():
    def __init__(self, x, y):
        self.position: Position = Position(x, y)
        self.known: bool = False  # seen at least one time
        self.invalid: bool = False  # برای جاهایی که اصلا غیر ممکنه مورچه بره اونجا ها
        self.wall: bool = False  # TODO: wall needs to be None at first because we dont know!
        self.last_seen: int = -np.inf  # How many turns passed since we see the resource

        self.grass_value: int = 0
        self.bread_value: int = 0

        # None means we dont know but false means that it is not! and true is true
        self.base: bool = False
        self.safe: bool = None
        self.enemy_base: bool = None
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
            neighbours = []

            for k in range(4):
                x_ = dx[k] + current.x
                y_ = dy[k] + current.y
                neighbor = self.fix_pos(Position(x_, y_))
                if neighbor == goal:
                    return path + [current, neighbor]
                if visited[neighbor.y][neighbor.x] == 0 and self[neighbor].wall == False:
                    neighbours.append((neighbor, path + [current]))
                    visited[neighbor.y][neighbor.x] = 1

            shuffle(neighbours)
            for n in neighbours:
                queue.append(n)

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

    def get_strategic_score(self, position: Position, cell: MapCell) -> int:
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

            return distance + distance_to_base + resource_score / abs(resource_reliableness)

    def get_strategic_points(self, position: Position):
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
                     if self[Position(x, y)].bread_value or self[Position(x, y)].grass_value]
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
