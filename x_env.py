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
            print("recieve from",ant_id, msgs)
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
                        self.messages.append(Chat(
                            type=ChatKind.OBSERVATION_SIMPLE,
                            data=ChatObservationSimple(
                            cell_pos, CellKind.ENEMY_BASE)
                        ))
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
                    elif msg.data.cell_kind == CellKind.WANT_TO_DEFEND.value:
                        self.grid[cell_pos].want_to_defenders += 1
                        self.defenders += 1
                    elif msg.data.cell_kind == CellKind.SOLDIER_BORN:
                        self.soldiers += 1
                    elif msg.data.cell_kind == CellKind.WORKER_BORN:
                        self.workers += 1

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

    def is_attak_from_enemy_base(self):
        pass
        # TODO:distance from enemy > 4 || position of attacker has no enemy soldier whitin

    def add_attack_data_to_map(self):
        ant = self.game.ant
        attacks = ant.attacks
        
        for attack in attacks:
            # Getting damaged
            attacker_pos = Position(x=attack.attacker_col, y=attack.attacker_row)
            defender_pos = Position(x=attack.defender_col, y=attack.defender_row)
            if attack.is_attacker_enemy:
                # if defender_pos == self.base_pos:
                #     # TODO: to be checked --> does it need to calculate based on base's health??
                #     reward += REWARD_GOT_DAMAGED_BASE
                # elif defender_pos == self.position:
                if not self.grid.enemy_base:
                    if self.grid.manhattan(defender_pos, attacker_pos) > 4 or not self.grid[attacker_pos].enemy_soldiers:
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
                    
            # else:
            #     # Attacking from us
            #     if attack.attacker_row == ant.currentX and attack.attacker_col == ant.currentY and ant.antType == AntType.SARBAAZ.value:
            #         if self.states(0, 0, attack.defender_row, attack.defender_col) == STATE_ENEMY_BASE:
            #             reward += REWARD_ATTACK_TO_ENEMY_BASE
            #         elif self.states(0, 0, attack.defender_row, attack.defender_col) == STATE_ENEMY_SOLDIER:
            #             reward += REWARD_ATTACK_TO_ENEMY_SOLDIER
            #         elif self.states(0, 0, attack.defender_row, attack.defender_col) == STATE_ENEMY_WORKER:
            #             reward += REWARD_ATTACK_TO_ENEMY_WORKER

    def update_grid(self):
        self.grid.enemies_in_sight_prev = np.copy(self.grid.enemies_in_sight_curr)
        self.grid.enemies_in_sight_curr = np.zeros((self.grid.height, self.grid.width))
        self.add_vision_to_map()
        self.handle_new_messages()
        self.add_attack_data_to_map()
        self.grid.update_last_seens()
    
    def can_we_attack(self):
        "basically telling us that is enemy base seen?"
        # TODO : More analysis can be done here. Ex. condition on current soldiers
        return self.grid.unsafe_zone_seen or self.grid.enemy_base

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
                    if self.position == self.task.destination:
                        # TODO: if not full search and harvest more!
                        if self.game.ant.currentResource and self.game.ant.currentResource.value > 0:
                            self.task = Task(type=TaskType.RETURN,
                                            destination=self.base_pos)
                            return
                        else:
                            self.task = None
                            self.update_task()
                            return
                    
                    # Assume that the worker is insisting to do its task
                    if not self.grid[self.task.destination].get_resource_score():  # Resource has been eaten by others
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
                    new_message = Chat(
                            type=ChatKind.OBSERVATION_SIMPLE,
                            data=ChatObservationSimple(
                            self.task.destination, CellKind.WANT_TO_EXPLORE)
                        )
                    self.messages.append(new_message)
                    return
        
        elif self.game.ant.antType == AntType.SARBAAZ.value:
            if self.can_we_attack():
                self.task = Task(TaskType.BASE_ATTACK, 
                    destination=self.grid.where_to_attack(
                        position=self.position
                    ))
                return

            if self.task:
                if self.task.type == TaskType.BASE_ATTACK:
                    if self.position == self.task.destination:
                        return
                elif self.task.type == TaskType.DEFEND:
                    if self.grid.is_enemy_in_sight():
                        destination = self.grid.get_one_enemy_position()
                        self.task = Task(type=TaskType.KILL,
                                destination=destination
                            )
                        return
                    # self.task.destination=self.grid.where_to_defend(
                    #     position=self.position, current_destination=self.task.destination)
                    return
                # defend is different with watch and it does not follow the enemy
                elif self.task.type == TaskType.WATCH:
                    if self.grid.is_enemy_in_sight():
                        destination = self.grid.get_one_enemy_position()
                        self.task = Task(type=TaskType.KILL,
                                destination=destination
                            )
                        return
                    elif self.position == self.task.destination:
                        self.task.destination=self.grid.where_to_watch(
                            self.position, current_destination=None)
                elif self.task.type == TaskType.KILL:
                    if self.grid.is_enemy_killed():
                        destination = self.grid.where_to_watch(self.position, current_destination=self.task.destination)
                        self.task = Task(TaskType.WATCH, destination)
                        return
                    else:
                        self.task.destination = self.grid.get_one_enemy_position()
                        return
            else:
                if self.defenders < MIN_DEFENDERS:
                    self.task = Task(TaskType.DEFEND,
                        destination=self.grid.where_to_defend(
                            position=self.position, current_destination=None
                        ))
                    new_message = Chat(
                            type=ChatKind.OBSERVATION_SIMPLE,
                            data=ChatObservationSimple(
                            self.task.destination, CellKind.WANT_TO_DEFEND)
                        )
                    self.messages.append(new_message)
                else:
                    self.task = Task(TaskType.WATCH,
                        destination=self.grid.where_to_watch(
                            self.position, current_destination=None
                        ))

    def generate_message(self, direction, ant_id):
        print("> sending from",ant_id, self.messages)
        message, priority = encode(ant_id, self.messages)
        return message, priority

    def get_direction(self):
        direction = self.grid.get_direction(self.position, self.task.destination)
        if direction is None:
            self.task = None
            self.update_task()
            direction = self.grid.get_direction(self.position, self.task.destination)
            if direction is None:
                self.task = None
                direction = Direction.CENTER
        return direction

    def run_one_turn(self, ant_id):
        self.messages = []
        self.position = Position(self.game.ant.currentX, self.game.ant.currentY)
        self.update_grid()
        self.update_task()
        direction = self.get_direction()

        print(direction, self.task)
        message, priority = self.generate_message(direction, ant_id)
        return message, priority,  direction.value
