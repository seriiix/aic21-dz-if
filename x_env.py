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

    def init_grid(self, game):
        self.game = game
        self.base_pos = Position(self.game.baseX, self.game.baseY)
        self.grid = Grid(self.game.mapWidth, self.game.mapHeight, self.base_pos)
        self.grid[self.base_pos].base = True
        self.position = Position(self.game.ant.currentX, self.game.ant.currentY)
        self.get_data_from_old_messages()

    def get_data_from_old_messages(self):
        for chat in self.game.chatBox.allChats:
            ant_id, msgs = decode(chat.text)
            for msg in msgs:
                cell_pos = msg.data.position
                self.grid[cell_pos].last_seen = - (self.get_last_turn_number()+1 - chat.turn)
                self.grid[cell_pos].known = True
                self.grid[cell_pos].safe = True
                if msg.type == ChatKind.OBSERVATION_SIMPLE:
                    if msg.data.cell_kind == CellKind.WALL.value:
                        self.grid[cell_pos].wall = True
                    elif msg.data.cell_kind == CellKind.UNSAFE.value:
                        self.grid[cell_pos].safe = False
                    # TODO: this may add some bugs to our last_seen
                    # elif msg.data.cell_kind == CellKind.ENEMY_SOLDIER.value:
                    #     self.grid[cell_pos].enemy_soldiers = 1
                    # elif msg.data.cell_kind == CellKind.ENEMY_WORKER.value:
                    #     self.grid[cell_pos].enemy_workers = 1
                    elif msg.data.cell_kind == CellKind.ENEMY_BASE.value:
                        self.grid[cell_pos].safe = False
                        self.grid[cell_pos].enemy_base = True
                        # TODO: May be we should do something urgent!
                
                elif msg.type == ChatKind.OBSERVATION_VALUE:
                    self.grid[cell_pos].wall = False
                    if msg.data.cell_kind == CellKind.BREAD.value:
                        self.grid[cell_pos].bread_value = msg.data.value
                        self.grid[cell_pos].grass_value = 0
                    elif msg.data.cell_kind == CellKind.GRASS.value:
                        self.grid[cell_pos].bread_value = 0
                        self.grid[cell_pos].grass_value = msg.data.value
                    # elif msg.data.cell_kind == CellKind.ENEMY_SOLDIER.value:
                    #     self.grid[cell_pos].enemy_soldiers = msg.data.value
                    # elif msg.data.cell_kind == CellKind.ENEMY_WORKER.value:
                    #     self.grid[cell_pos].enemy_workers = msg.data.value

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
        # TODO : not all chats
        for chat in chats:
            ant_id, msgs = decode(chat.text)
            for msg in msgs:
                cell_pos = msg.data.position
                self.grid[cell_pos].last_seen = -1
                self.grid[cell_pos].known = True
                self.grid[cell_pos].safe = True
                if msg.type == ChatKind.OBSERVATION_SIMPLE:
                    if msg.data.cell_kind == CellKind.WALL.value:
                        self.grid[cell_pos].wall = True
                    elif msg.data.cell_kind == CellKind.UNSAFE.value:
                        self.grid[cell_pos].safe = False
                    elif msg.data.cell_kind == CellKind.ENEMY_SOLDIER.value:
                        self.grid[cell_pos].enemy_soldiers = 1
                    elif msg.data.cell_kind == CellKind.ENEMY_WORKER.value:
                        self.grid[cell_pos].enemy_workers = 1
                    elif msg.data.cell_kind == CellKind.ENEMY_BASE.value:
                        self.grid[cell_pos].safe = False
                        self.grid[cell_pos].enemy_base = True
                        # TODO: May be we should do something urgent!
                
                elif msg.type == ChatKind.OBSERVATION_VALUE:
                    self.grid[cell_pos].wall = False
                    if msg.data.cell_kind == CellKind.BREAD.value:
                        self.grid[cell_pos].bread_value = msg.data.value
                        self.grid[cell_pos].grass_value = 0
                    elif msg.data.cell_kind == CellKind.GRASS.value:
                        self.grid[cell_pos].bread_value = 0
                        self.grid[cell_pos].grass_value = msg.data.value
                    elif msg.data.cell_kind == CellKind.ENEMY_SOLDIER.value:
                        self.grid[cell_pos].enemy_soldiers = msg.data.value
                    elif msg.data.cell_kind == CellKind.ENEMY_WORKER.value:
                        self.grid[cell_pos].enemy_workers = msg.data.value

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
                    self.grid[cell_pos].set_ants(cell.ants) 
                    # TODO: adding info of ants to messages

                    # ENEMY BASE
                    if cell.type == CellType.BASE.value:
                        if not cell_pos == self.base_pos:
                            self.grid[cell_pos].enemy_base = True
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
        # TODO: is it needed? 
        return 
        ant = self.game.ant
        attacks = ant.attacks
        # Moving resources to our base
        
        for attack in attacks:
            # Getting damaged
            if attack.is_attacker_enemy:
                if attack.defender_row == curr_game.baseX and attack.defender_col == curr_game.baseY:
                    # TODO: to be checked --> does it need to calculate based on base's health??
                    reward += REWARD_GOT_DAMAGED_BASE
                elif attack.defender_row == ant.currentX and attack.defender_col == ant.currentY and prev_game.ant.health != ant.health:
                    damage = prev_game.ant.health-ant.health  # damage > 0
                    # damage = 1 # TODO: is this needed or not?
                    if ant.antType == AntType.SARBAAZ.value:
                        reward += damage * REWARD_GOT_DAMAGED_SOLDIER
                    elif ant.antType == AntType.KARGAR.value:
                        reward += damage * REWARD_GOT_DAMAGED_WORKER

            else:
                # Attacking from us
                if attack.attacker_row == ant.currentX and attack.attacker_col == ant.currentY and ant.antType == AntType.SARBAAZ.value:
                    if self.states(0, 0, attack.defender_row, attack.defender_col) == STATE_ENEMY_BASE:
                        reward += REWARD_ATTACK_TO_ENEMY_BASE
                    elif self.states(0, 0, attack.defender_row, attack.defender_col) == STATE_ENEMY_SOLDIER:
                        reward += REWARD_ATTACK_TO_ENEMY_SOLDIER
                    elif self.states(0, 0, attack.defender_row, attack.defender_col) == STATE_ENEMY_WORKER:
                        reward += REWARD_ATTACK_TO_ENEMY_WORKER

    def update_grid(self):
        self.add_vision_to_map()
        self.handle_new_messages()
        self.grid.update_last_seens()

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

    def generate_message(self, direction):
        messages = [(message, message.data.get_score()) for message in self.messages]
        messages.sort(key=lambda item: -item[1])
        messages = [x[0] for x in messages]
        
        # TODO: set priority and ant_id
        message = encode(133, messages)
        priority = 2
        return message, priority

    def run_one_turn(self):
        self.messages = []
        self.position = Position(self.game.ant.currentX, self.game.ant.currentY)
        self.update_grid()
        self.add_attack_data_to_map()
        self.update_task()
        direction = self.grid.get_direction(self.position, self.task.destination)
        if not direction:
            # TODO: here waits for 1 turn. can we do better?
            self.task = None
            direction = Direction.CENTER.value
        print(self.task)
        print(direction)
        message, priority = self.generate_message(direction)
        return message, priority,  direction.value
