from enum import Enum
from x_helpers import Position

class TaskType(Enum):
    EXPLORE = 0
    HARVEST = 1
    RETURN = 2
    FLEE = 3

    BASE_ATTACK = 4
    KILL = 5
    DEFEND = 6
    GATHER = 7


class Task:
    # TODO: tasks can expire -> especially explore
    def __init__(self, type: TaskType, destination: Position):
        self.type: TaskType = type
        self.destination: Position = destination

    def __str__(self):
        return f"Task(type={self.type}, dest={self.destination})"

