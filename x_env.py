from typing import List
from enum import Enum
from random import randint, choice
from copy import deepcopy
import numpy as np

from Model import Ant, Direction, Game, Resource, ResourceType, CellType, AntType, AntTeam
from x_consts import *
from x_helpers import Position
from x_message import Chat, ChatKind, ChatObservationSimple, ChatObservationValue, CellKind, decode, encode
from x_task import Task, TaskType
from x_grid import Grid


class Env():
    def __init__(self):
        self.game: Game = None
        self.grid: Grid = None
        self.base_pos: Position = None
        self.task: Task = None
        self.position: Position = None
        self.ant: Ant = None
        self.messages = []
        self.defenders = 0
        self.explorers = 0
        self.soldiers = 0
        self.workers = 0
        self.saw_new_resource = False
        self.is_explorer = False
        self.gathering_position = None
        self.previous_position: Position = None
        # when we are gathered and we want to attack - > sets in handle message on LETS_FUCK
        self.attacking_position = None
        # when defending and enemy is trying to attack - > sets in handle message on HELP_ME
        self.damage_position = None

    def init_grid(self, game):
        self.game = game
        self.base_pos = Position(self.game.baseX, self.game.baseY)
        self.grid = Grid(self.game.mapWidth,
                         self.game.mapHeight, self.base_pos)
        self.grid[self.base_pos].base = True
        self.position = Position(
            self.game.ant.currentX, self.game.ant.currentY)
        self.get_data_from_old_messages()

    def get_last_turn_number(self):
        all_chats = self.game.chatBox.allChats
        return all_chats[-1].turn if len(all_chats) else -1

    def get_last_turn_messages(self):
        last_turn_number = self.get_last_turn_number()
        chats = []
        if last_turn_number != -1:
            for chat in reversed(self.game.chatBox.allChats):
                if chat.turn == last_turn_number:
                    chats.append(chat)
                else:
                    break
        return chats

    def handle_new_messages(self):
        chats = self.get_last_turn_messages()
        for chat in chats:
            ant_id, msgs = decode(chat.text)
            # print("recieve from",ant_id, msgs)
            for msg in msgs:
                cell_pos = msg.data.position
                self.grid[cell_pos].last_seen = -1
                self.grid[cell_pos].known = True
                self.grid[cell_pos].safe = True
                if msg.type == ChatKind.OBSERVATION_SIMPLE:
                    if msg.data.cell_kind == CellKind.WALL:
                        self.grid[cell_pos].wall = True
                    elif msg.data.cell_kind == CellKind.INVALID:
                        self.grid[cell_pos].invalid = True
                    elif msg.data.cell_kind == CellKind.ENEMY_BASE:
                        self.grid[cell_pos].safe = False
                        self.grid[cell_pos].enemy_base = True
                        self.grid.enemy_base = cell_pos
                    elif msg.data.cell_kind == CellKind.WANT_TO_DEFEND:
                        self.grid[cell_pos].want_to_defenders += 1
                        self.defenders += 1
                    elif msg.data.cell_kind == CellKind.WANT_TO_EXPLORE:
                        self.explorers += 1
                    elif msg.data.cell_kind == CellKind.SOLDIER_BORN:
                        self.soldiers += 1
                    # elif msg.data.cell_kind == CellKind.WORKER_BORN:
                        # self.workers += 1
                    elif msg.data.cell_kind == CellKind.HELP_ME:
                        self.damage_position = cell_pos
                    elif msg.data.cell_kind == CellKind.WANT_TO_GATHER:
                        self.gathering_position = cell_pos
                    elif msg.data.cell_kind == CellKind.LETS_FUCK_THIS_SHIT:
                        self.attacking_position = cell_pos
                    elif msg.data.cell_kind == CellKind.ME_SOLDIER:
                        self.grid.make_cells_arround_position_known(cell_pos)
                    elif msg.data.cell_kind == CellKind.ME_WORKER:
                        self.grid.make_cells_arround_position_known(cell_pos)
                    elif msg.data.cell_kind == CellKind.ME_EXPLORER:
                        print("reveded EXPLORER")
                        self.grid.make_cells_arround_position_known(cell_pos)

                elif msg.type == ChatKind.OBSERVATION_VALUE:
                    self.grid[cell_pos].wall = False
                    if msg.data.cell_kind == CellKind.BREAD:
                        if self.grid[cell_pos].get_resource_score() == 0 and msg.data.value != 0 or self.grid[cell_pos].get_resource_score() != 0 and msg.data.value == 0:
                            self.saw_new_resource = True
                        self.grid[cell_pos].bread_value = msg.data.value
                        self.grid[cell_pos].grass_value = 0
                    elif msg.data.cell_kind == CellKind.GRASS:
                        if self.grid[cell_pos].get_resource_score() == 0 and msg.data.value != 0 or self.grid[cell_pos].get_resource_score() != 0 and msg.data.value == 0:
                            self.saw_new_resource = True
                        self.grid[cell_pos].bread_value = 0
                        self.grid[cell_pos].grass_value = msg.data.value

    def get_data_from_old_messages(self):
        for chat in self.game.chatBox.allChats:
            ant_id, msgs = decode(chat.text)
            for msg in msgs:
                cell_pos = msg.data.position
                self.grid[cell_pos].last_seen = - \
                    (self.get_last_turn_number()+1 - chat.turn)
                self.grid[cell_pos].known = True
                self.grid[cell_pos].safe = True
                if msg.type == ChatKind.OBSERVATION_SIMPLE:
                    if msg.data.cell_kind == CellKind.WALL:
                        self.grid[cell_pos].wall = True
                    elif msg.data.cell_kind == CellKind.INVALID:
                        self.grid[cell_pos].invalid = True
                    elif msg.data.cell_kind == CellKind.ENEMY_BASE:
                        self.grid[cell_pos].safe = False
                        self.grid[cell_pos].enemy_base = True
                        self.grid.enemy_base = cell_pos
                    elif msg.data.cell_kind == CellKind.WANT_TO_DEFEND:
                        self.grid[cell_pos].want_to_defenders += 1
                        self.defenders += 1
                    elif msg.data.cell_kind == CellKind.WANT_TO_EXPLORE:
                        self.explorers += 1
                    elif msg.data.cell_kind == CellKind.SOLDIER_BORN:
                        self.soldiers += 1
                    # elif msg.data.cell_kind == CellKind.WORKER_BORN:
                        # self.workers += 1
                    elif msg.data.cell_kind == CellKind.HELP_ME:
                        self.damage_position = cell_pos
                    elif msg.data.cell_kind == CellKind.WANT_TO_GATHER:
                        self.gathering_position = cell_pos
                    elif msg.data.cell_kind == CellKind.LETS_FUCK_THIS_SHIT:
                        self.attacking_position = cell_pos
                    elif msg.data.cell_kind == CellKind.ME_SOLDIER:
                        self.grid.make_cells_arround_position_known(cell_pos)
                    elif msg.data.cell_kind == CellKind.ME_WORKER:
                        self.grid.make_cells_arround_position_known(cell_pos)
                    elif msg.data.cell_kind == CellKind.ME_EXPLORER:
                        self.grid.make_cells_arround_position_known(cell_pos)

                elif msg.type == ChatKind.OBSERVATION_VALUE:
                    self.grid[cell_pos].wall = False
                    if msg.data.cell_kind == CellKind.BREAD:
                        self.grid[cell_pos].bread_value = msg.data.value
                        self.grid[cell_pos].grass_value = 0
                    elif msg.data.cell_kind == CellKind.GRASS:
                        self.grid[cell_pos].bread_value = 0
                        self.grid[cell_pos].grass_value = msg.data.value

    def add_vision_to_map(self) -> None:
        "the ant adds its vision information to the grid"
        vision = self.game.ant.visibleMap
        for cell_row in vision.cells:
            for cell in cell_row:
                if cell:
                    cell_pos = Position(cell.x, cell.y)
                    # TODO: add ant's position to messages?

                    self.grid[cell_pos].last_seen = 0

                    self.grid[cell_pos].known = True

                    # WALL
                    if cell.type == CellType.WALL.value:
                        if not self.grid[cell_pos].wall:
                            self.grid[cell_pos].wall = True
                            new_message = Chat(
                                type=ChatKind.OBSERVATION_SIMPLE,
                                data=ChatObservationSimple(
                                    cell_pos, CellKind.WALL)
                            )
                            self.messages.append(new_message)
                    else:
                        self.grid[cell_pos].wall = False

                    # RESOURCES
                    if cell.resource_type == ResourceType.BREAD.value:
                        if self.grid[cell_pos].get_resource_score() == 0:
                            self.saw_new_resource = True
                        if self.grid[cell_pos].bread_value != cell.resource_value:
                            self.grid[cell_pos].bread_value = cell.resource_value
                            self.grid[cell_pos].grass_value = 0
                            new_message = Chat(
                                type=ChatKind.OBSERVATION_VALUE,
                                data=ChatObservationValue(
                                    cell_pos, CellKind.BREAD, cell.resource_value)
                            )
                            self.messages.append(new_message)
                    if cell.resource_type == ResourceType.GRASS.value:
                        if self.grid[cell_pos].get_resource_score() == 0:
                            self.saw_new_resource = True
                        if self.grid[cell_pos].grass_value != cell.resource_value:
                            self.grid[cell_pos].grass_value = cell.resource_value
                            self.grid[cell_pos].bread_value = 0
                            new_message = Chat(
                                type=ChatKind.OBSERVATION_VALUE,
                                data=ChatObservationValue(
                                    cell_pos, CellKind.GRASS, cell.resource_value)
                            )
                            self.messages.append(new_message)
                    if cell.resource_value == 0:
                        if self.grid[cell_pos].get_resource_score() != 0:
                            self.saw_new_resource = True
                        if self.grid[cell_pos].grass_value != cell.resource_value:
                            self.grid[cell_pos].grass_value = 0
                            new_message = Chat(
                                type=ChatKind.OBSERVATION_VALUE,
                                data=ChatObservationValue(
                                    cell_pos, CellKind.GRASS, cell.resource_value)
                            )
                            self.messages.append(new_message)
                        if self.grid[cell_pos].bread_value != cell.resource_value:
                            self.grid[cell_pos].bread_value = 0
                            new_message = Chat(
                                type=ChatKind.OBSERVATION_VALUE,
                                data=ChatObservationValue(
                                    cell_pos, CellKind.BREAD, cell.resource_value)
                            )
                            self.messages.append(new_message)
                    # ANTS
                    self.grid.set_ants(cell.ants, cell_pos)
                    # TODO: adding info of ants to messages

                    # ENEMY BASE
                    if cell.type == CellType.BASE.value:
                        if not cell_pos == self.base_pos:
                            self.grid[cell_pos].enemy_base = True
                            self.grid.enemy_base = cell_pos
                            new_message = Chat(
                                type=ChatKind.OBSERVATION_SIMPLE,
                                data=ChatObservationSimple(
                                    cell_pos, CellKind.ENEMY_BASE)
                            )
                            self.messages.append(new_message)
                            # TODO: here we can set to False all other cells but may be not necessary
                    else:
                        self.grid[cell_pos].enemy_base = False

    def add_attack_data_to_map(self):
        ant = self.game.ant
        attacks = ant.attacks

        for attack in attacks:
            attacker_pos = Position(
                x=attack.attacker_col, y=attack.attacker_row)
            defender_pos = Position(
                x=attack.defender_col, y=attack.defender_row)
            # Getting damaged
            if attack.is_attacker_enemy:
                if not self.grid.enemy_base:
                    if self.previous_position and defender_pos == self.previous_position and (self.grid.manhattan(defender_pos, attacker_pos) > 4 or not self.grid[attacker_pos].enemy_soldiers) and attacker_pos != self.base_pos:
                        # ENEMY BASE IS FOUND!
                        self.grid[defender_pos].safe = False
                        self.grid[attacker_pos].enemy_base = True
                        self.grid.enemy_base = attacker_pos
                        self.grid.unsafe_zone_seen = True
                        self.messages.append(Chat(
                            type=ChatKind.OBSERVATION_SIMPLE,
                            data=ChatObservationSimple(
                                attacker_pos, CellKind.ENEMY_BASE)
                        ))
                        self.gathering_position = self.grid.get_gathering_position(
                            self.position)
                        self.messages.append(Chat(
                            type=ChatKind.OBSERVATION_SIMPLE,
                            data=ChatObservationSimple(
                                self.gathering_position, CellKind.WANT_TO_GATHER)
                        ))

                elif self.task.type == TaskType.DEFEND:
                    self.messages.append(Chat(
                        type=ChatKind.OBSERVATION_SIMPLE,
                        data=ChatObservationSimple(
                            attacker_pos, CellKind.HELP_ME)
                    ))

    def check_for_enemy_base_estimate(self):
        pass

    def update_grid(self):
        self.grid.enemies_in_sight_prev = np.copy(
            self.grid.enemies_in_sight_curr)
        self.grid.enemies_in_sight_curr = np.zeros(
            (self.grid.height, self.grid.width))
        self.add_vision_to_map()
        self.handle_new_messages()
        self.add_attack_data_to_map()
        self.check_for_enemy_base_estimate()
        self.grid.update_last_seens()

    def can_we_attack(self):
        "basically telling us that is enemy base seen?"
        # تعداد سربازا به حد نصاب برسه
        # از طریق تقارن بیس انمی رو داشته باشیم
        # ترن بازی از یه تعدادی بیشتر بشه
        #
        # TODO : More analysis can be done here. Ex. condition on current soldiers
        return self.grid.unsafe_zone_seen or self.grid.enemy_base

    def update_worker_task(self):
        if self.game.ant.currentResource and self.game.ant.currentResource.value >= MIN_CARRY_FOR_ANT:
            self.task = Task(type=TaskType.RETURN,
                             destination=self.base_pos)
            return
        if self.task:
            if self.task.type == TaskType.RETURN:
                if self.position == self.base_pos:
                    self.task = None
                    return self.update_task()
                else:
                    return

            elif self.task.type == TaskType.HARVEST:
                if self.position == self.task.destination:
                    if self.game.ant.currentResource and self.game.ant.currentResource.value > 0:
                        harvest_location = self.grid.get_over_harvest_location(
                            self.game.ant.currentResource, self.position
                        )
                        if harvest_location:
                            self.task = Task(
                                type=TaskType.HARVEST, destination=harvest_location)
                            return
                        else:
                            self.task = Task(type=TaskType.RETURN,
                                             destination=self.base_pos)
                            return
                    else:
                        self.task = None
                        self.update_task()
                        return

                if self.saw_new_resource:
                    harvest_location = self.grid.get_harvest_location(
                        self.position)
                    if harvest_location and self.task.change_idea_times < MAX_CHANGE_IDEA_COUNT:
                        self.task.destination = harvest_location
                        self.task.change_idea_times += 1
                        new_message = Chat(
                            type=ChatKind.OBSERVATION_SIMPLE,
                            data=ChatObservationSimple(
                                self.task.destination, CellKind.WANT_TO_HARVEST)
                        )

                # Assume that the worker is insisting to do its task
                # Resource has been eaten by others
                if not self.grid[self.task.destination].get_resource_score():
                    self.task = None
                    self.update_task()
                    return
                else:
                    return

            elif self.task.type == TaskType.EXPLORE:
                # به مورچه کارگر اگه منبع برا جمع کردن هست اکسپلور نمیدیم!
                harvest_location = self.grid.get_harvest_location(
                    self.position)
                if harvest_location:
                    self.task = Task(type=TaskType.HARVEST,
                                     destination=harvest_location)
                    new_message = Chat(
                        type=ChatKind.OBSERVATION_SIMPLE,
                        data=ChatObservationSimple(
                            self.task.destination, CellKind.WANT_TO_HARVEST)
                    )
                    self.messages.append(new_message)
                    return
                if not self.grid.is_good_to_explore(self.task.destination):
                    self.task = None
                    self.update_task()
                    return
                if self.position == self.task.destination:
                    self.task = None
                    self.update_task()
                    return

        else:
            harvest_location = self.grid.get_harvest_location(
                self.position)
            if harvest_location:
                self.task = Task(type=TaskType.HARVEST,
                                 destination=harvest_location)
                new_message = Chat(
                    type=ChatKind.OBSERVATION_SIMPLE,
                    data=ChatObservationSimple(
                        self.task.destination, CellKind.WANT_TO_HARVEST)
                )
                self.messages.append(new_message)
                return
            else:
                destination = self.grid.get_explore_location(self.position)
                self.task = Task(type=TaskType.EXPLORE,
                                 destination=destination)
                # new_message = Chat(
                #         type=ChatKind.OBSERVATION_SIMPLE,
                #         data=ChatObservationSimple(
                #         self.task.destination, CellKind.WANT_TO_EXPLORE)
                #     )
                # self.messages.append(new_message)
                return

    def update_soldier_task(self):
        # print("OUR SOLDIERS=", self.grid[self.position].our_soldiers)
        if self.attacking_position:
            self.task = Task(TaskType.BASE_ATTACK,
                             destination=self.attacking_position)

        elif self.get_last_turn_number() > 72:
            self.task = Task(
                TaskType.EXPLORE, destination=self.grid.get_explore_location(self.position))

        elif self.gathering_position:
            self.task = Task(
                TaskType.GATHER, destination=self.gathering_position)

        if not self.task:
            if self.explorers < MIN_EXPLORERS:
                self.is_explorer = True
                destination = self.grid.get_explore_location(self.position)
                self.task = Task(TaskType.EXPLORE, destination)
                self.messages.append(Chat(
                    type=ChatKind.OBSERVATION_SIMPLE,
                    data=ChatObservationSimple(
                        self.task.destination, CellKind.WANT_TO_EXPLORE)
                ))
            else:
                destination = self.grid.where_to_defend(position=self.position)
                self.task = Task(TaskType.DEFEND, destination=destination)
                self.messages.append(Chat(
                    type=ChatKind.OBSERVATION_SIMPLE,
                    data=ChatObservationSimple(
                        self.task.destination, CellKind.WANT_TO_DEFEND)
                ))
        else:
            if self.task.type == TaskType.BASE_ATTACK:
                return
            elif self.task.type == TaskType.GATHER:
                # TODO: or waiting until certain time
                if self.grid[self.position].our_soldiers >= MIN_GATHER_ANTS:
                    self.attacking_position = self.grid.where_to_attack(
                        self.position)
                    self.task = Task(TaskType.BASE_ATTACK,
                                     destination=self.attacking_position)
                    self.messages.append(Chat(
                        type=ChatKind.OBSERVATION_SIMPLE,
                        data=ChatObservationSimple(
                            self.task.destination, CellKind.LETS_FUCK_THIS_SHIT)
                    ))
                return
            elif self.task.type == TaskType.DEFEND:
                if self.damage_position:
                    self.task.destination = self.damage_position
                    return
                elif self.grid.is_enemy_in_sight():
                    self.task = Task(
                        TaskType.KILL, destination=self.grid.get_one_enemy_position())
                    return
                else:
                    if self.get_last_turn_number() % 2 == 0:
                        self.task.destination = self.grid.where_to_defend(
                            self.position)
            elif self.task.type == TaskType.KILL:
                if self.grid.is_enemy_in_sight():
                    self.task.destination = self.grid.get_one_enemy_position()
                else:
                    self.task.destination = self.grid.where_to_defend(
                        self.position)
            elif self.task.type == TaskType.EXPLORE:
                if self.grid.is_good_to_explore(self.task.destination):
                    return
                else:
                    self.task.destination = self.grid.get_explore_location(
                        self.position)

    def update_task(self):
        "analyzes the map and trys to get the most important task"
        if self.game.ant.antType == AntType.KARGAR.value:
            self.update_worker_task()

        elif self.game.ant.antType == AntType.SARBAAZ.value:
            self.update_soldier_task()

    def generate_message(self, direction, ant_id):
        # print("> sending from",ant_id, self.messages)
        message, priority = encode(ant_id, self.messages)
        return message, priority

    def get_direction(self):
        if not self.task:
            return Direction.CENTER

        direction = self.grid.get_direction(
            self.position, self.task.destination)
        if direction is None:
            self.grid[self.task.destination].invalid = True
            self.task = None
            self.update_task()
            self.messages.append(Chat(
                type=ChatKind.OBSERVATION_SIMPLE,
                data=ChatObservationSimple(
                    self.task.destination, CellKind.INVALID)
            ))
            direction = self.grid.get_direction(
                self.position, self.task.destination)
            if direction is None:
                self.grid[self.task.destination].invalid = True
                self.task = None
                self.messages.append(Chat(
                    type=ChatKind.OBSERVATION_SIMPLE,
                    data=ChatObservationSimple(
                        self.task.destination, CellKind.INVALID)
                ))
                direction = Direction.CENTER
        return direction

    def get_self_type_message(self):
        if self.game.ant.antType == AntType.KARGAR.value:
            return Chat(
                type=ChatKind.OBSERVATION_SIMPLE,
                data=ChatObservationSimple(
                    self.position, CellKind.ME_WORKER)
            )
        elif self.game.ant.antType == AntType.SARBAAZ.value:
            if self.is_explorer:
                return Chat(
                    type=ChatKind.OBSERVATION_SIMPLE,
                    data=ChatObservationSimple(
                        self.position, CellKind.ME_EXPLORER)
                )
            else:
                return Chat(
                    type=ChatKind.OBSERVATION_SIMPLE,
                    data=ChatObservationSimple(
                        self.position, CellKind.ME_SOLDIER)
                )

    def run_one_turn(self, ant_id):
        self.messages = [self.get_self_type_message()]
        self.saw_new_resource = False
        self.damage_position = None
        self.position = Position(
            self.game.ant.currentX, self.game.ant.currentY)
        self.update_grid()
        self.update_task()
        direction = self.get_direction()
        self.previous_position = self.position

        # print(direction, self.task)
        message, priority = self.generate_message(direction, ant_id)
        # return message, priority, Direction.RIGHT.value
        return message, priority,  direction.value
