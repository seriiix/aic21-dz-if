from enum import IntFlag
from random import randint, choice, shuffle, choices
from copy import deepcopy
from collections import deque
from typing import List
import numpy as np

import x_consts as cv
from Model import Ant, Direction, Game, Map, Resource, ResourceType, CellType, AntType, AntTeam
from x_consts import *
from x_helpers import Position
from x_task import TaskType


class MapCell():
    def __init__(self, x, y):
        self.position: Position = Position(x, y)
        self.known: bool = False  # seen at least one time
        self.invalid: bool = False  # برای جاهایی که اصلا غیر ممکنه مورچه بره اونجا ها
        self.wall: bool = False
        self.swamp: bool = False
        self.trap: bool = False
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

        # TODO:
        self.want_to_defenders = 0
        self.want_to_harvesters = 0

    def __eq__(self, other) -> bool:
        if type(other) == MapCell:
            return self.position == other.position
        return False

    def __str__(self) -> str:
        return f'Cell[{self.position}]'

    def __repr__(self) -> str:
        return f'Cell[{self.position}]'

    def get_resource_score(self, type=None):
        if self.invalid:
            return 0
        else:
            if not type:
                return self.grass_value * GRASS_SCORE + self.bread_value * BREAD_SCORE
            else:
                if type == ResourceType.GRASS.value:
                    return self.grass_value
                elif type == ResourceType.BREAD.value:
                    return self.bread_value


class Grid():
    def __init__(self, width, height, base_pos):
        self.width = width
        self.height = height
        self.base_pos: Position = base_pos
        self.unsafe_zone_seen: bool = False
        self.enemy_base: Position = None
        self.cells = [[MapCell(i, j) for i in range(width)]
                      for j in range(height)]
        self.enemies_in_sight_prev = np.zeros((height, width))
        self.enemies_in_sight_curr = np.zeros((height, width))

    def __getitem__(self, position: Position):
        return self.cells[position.y][position.x]

    def __setitem__(self, position: Position, value: MapCell):
        self.cells[position.y][position.x] = deepcopy(value)

    def manhattan(self, p1: Position, p2: Position):
        x1 = min(p1.x, p2.x)
        x2 = max(p1.x, p2.x)
        fx1 = abs(x1 - x2)
        fx2 = abs(x1 + self.width - x2)
        #
        y1 = min(p1.y, p2.y)
        y2 = max(p1.y, p2.y)
        fy1 = abs(y1 - y2)
        fy2 = abs(y1 + self.height - y2)

        return min(fx1, fx2) + min(fy1, fy2)

    def get_defenders_count(self):
        # TODO: باید یه جوری در بیاریم که الان چن نفر دارن دفاع میکنن از بیس
        return MIN_DEFENDERS

    def is_enemy_killed(self):
        "useful for soldiers when they chase enemy ants"
        return int(np.sum(self.enemies_in_sight_curr - self.enemies_in_sight_prev)) == 0

    def set_ants(self, ants, position):
        self[position].our_workers = 0
        self[position].our_soldiers = 0
        self[position].enemy_workers = 0
        self[position].enemy_soldiers = 0
        for ant in ants:
            if ant.antTeam == AntTeam.ALLIED.value:
                if ant.antType == AntType.KARGAR.value:
                    self[position].our_workers += 1
                elif ant.antType == AntType.SARBAAZ.value:
                    self[position].our_soldiers += 1
            elif ant.antTeam == AntTeam.ENEMY.value:
                if ant.antType == AntType.KARGAR.value:
                    self[position].enemy_workers += 1
                    self.enemies_in_sight_curr[position.y, position.x] += 1
                elif ant.antType == AntType.SARBAAZ.value:
                    self[position].enemy_soldiers += 1
                    self.enemies_in_sight_curr[position.y, position.x] += 1

    def is_enemy_in_sight(self):
        return int(np.sum(self.enemies_in_sight_curr)) > 0

    def get_one_enemy_position(self):
        # TODO: بهتره اونی که دورتر از بیس خودمونه رو بگیریم
        if int(np.sum(self.enemies_in_sight_curr)) > 0:
            ind = np.unravel_index(
                self.enemies_in_sight_curr.argmax(), self.enemies_in_sight_curr.shape)
            return Position(ind[1], ind[0])
        else:
            ind = np.unravel_index(
                self.enemies_in_sight_prev.argmax(), self.enemies_in_sight_prev.shape)
            return Position(ind[1], ind[0])

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

    def bfs(self, start: Position, goal: Position, known: bool = False, random: bool = True):
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
                    if known == True and self[neighbor].known == False:
                        continue
                    neighbours.append((neighbor, path + [current]))
                    visited[neighbor.y][neighbor.x] = 1

            if random:
                shuffle(neighbours)
            for n in neighbours:
                queue.append(n)

        return None

    def count_unknown_cells(self, path: List[Position]) -> int:
        cntr = 0
        for p in path:
            if self[p].known:
                cntr += 1
        return cntr

    def get_direction(self, start: Position, goal: Position, task=None):
        random = True
        if task and task.type == TaskType.BASE_ATTACK:
            random = False
        path = self.bfs(start, goal, random=random)
        if path is None:
            self[goal].invalid = True
            return None
        if start == goal:
            return Direction.CENTER

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

        path = self.bfs(position, cell.position)
        if not path:
            return -np.inf
        else:
            distance = len(path)
            path_to_base = self.bfs(cell.position, self.base_pos)
            distance_to_base = len(path_to_base)
            resource_score = cell.get_resource_score()
            resource_reliableness = cell.last_seen
            self_soldiers_in_cell = cell.our_soldiers
            unknown = int(not cell.known)
            # self_workers_in_cell = cell.get_self_workers_count()

            # return distance_to_base + resource_score / abs(resource_reliableness/(distance_to_base/2))
            return distance_to_base + resource_score

    def get_strategic_points(self, position: Position):
        "returns list of (score, cells) decsending by score "
        cells = []
        for row in self.cells:
            for cell in row:
                cells.append((self.get_strategic_score(position, cell), cell))
        cells.sort(key=lambda item: -item[0])
        return cells

    def where_to_watch(self, position: Position, current_destination=None) -> Position:
        # TODO: use destination
        # strategic_points = [(position: Position, priority: int)]
        strategic_points = self.get_strategic_points(position)
        # TODO: may be we can add some randomness here if needed
        best_point_score, best_point = strategic_points[0]
        if self.get_strategic_score(position, self[position]) != best_point_score:
            return best_point.position
        else:
            return position

    def where_to_defend(self, position: Position, current_destination=None):
        """ اینجا حرکتی که میزنیم اینه که یه شعاع از بیس در نظر میگیریم و سربازامونو شانسی میچینیم دورش
        بعد هر سرباز میگه من الان اینجام و ما چک میکنیم اونجایی که الان داره دفاع میکنه خوبه یا نه
        اگه خوب نباشه یه جای بهتر میدیم بهش. چون ممکنه قبلا اون نقطه دیده نمیشده و بهش اساین شده
        نکته اینه که به مرور زمان میتونیم شعاع دفاع رو بیشتر کنیم."""
        # TODO: check if there are defenders there?
        radius_cells = [cell.position for row in self.cells for cell in row
                        if self.manhattan(cell.position, self.base_pos) == DEFEND_RADIUS and not cell.invalid
                        ]
        radius_cell_paths = [
            self.bfs(self.base_pos, position, known=True) for position in radius_cells]
        radius_cell_points = [
            len(path) if path else .001 for path in radius_cell_paths]
        return choices(radius_cells, weights=radius_cell_points, k=1)[0]

    def where_to_attack(self, position: Position, current_destination=None) -> Position:
        for row in self.cells:
            for cell in row:
                if self.manhattan(position, self.enemy_base) < MAX_ATTACK_DISTANCE_SOLDIER and cell.known:
                    return

        return self.enemy_base

    def update_last_seens(self):
        for row in self.cells:
            for cell in row:
                cell.last_seen -= 1
                if cell.last_seen == 0:
                    cell.last_seen = -1

    def get_effective_distance(self, start, location):
        path = self.bfs(start, location)
        if path is None:
            return np.inf
        distance = len(path)
        unknown_distance = self.count_unknown_cells(path)
        known_distance = distance - unknown_distance
        effective_distance = known_distance + UNKNOWN_DISTANCE_PENALTY * unknown_distance
        return effective_distance

    def get_harvest_score(self, start, location):
        effective_distance = self.get_effective_distance(start, location)
        resource_value = self[location].get_resource_score()
        score = resource_value/(effective_distance**GREEDYNESS_HARVEST_FACTOR)
        return score

    def get_harvest_location(self, position: Position) -> Position:
        locations = [self[Position(x, y)].position
                     for x in range(self.width) for y in range(self.height)
                     if self[Position(x, y)].get_resource_score()]
        weights = [self.get_harvest_score(
            position, location) for location in locations]
        if len(locations):
            return choices(locations, weights=weights, k=1)[0]
        else:
            return None

    def get_over_harvest_location(self, current_resource, position):
        if current_resource.value >= MIN_CARRY_FOR_ANT:
            return None
        else:
            locations = [self[Position(x, y)].position
                         for x in range(self.width) for y in range(self.height)
                         if self[Position(x, y)].get_resource_score(type=current_resource.type)]
            weights = [self.get_harvest_score(
                position, location) for location in locations]
            if len(locations):
                return choices(locations, weights=weights, k=1)[0]
            else:
                return None

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
        return locations

    def get_gathering_position(self, position):
        # TODO: better option you shoud get optimal value by knowing soldier distances
        path = self.bfs(self.base_pos, position, known=True)
        return path[int(len(path)/cv.GATHERING_PORTION)]

    def get_explore_location(self, start: Position) -> Position:
        locations = self.get_seen_cells_neighbours()
        weights = [1/self.manhattan(start, location) for location in locations]
        location = choices(locations, weights=weights, k=1)[
            0] if len(locations) else start
        return location

    def make_cells_arround_position_known(self, position):
        for row in self.cells:
            for cell in row:
                if self.manhattan(position, cell.position) <= MAX_AGENT_VIEW_DISTANCE:
                    cell.known = True
