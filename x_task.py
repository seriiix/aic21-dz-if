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
    STAND_ATTACK = 8
    DEVIATE = 9  # سربازا از هم فاصله میگیرن
    EXPLORE_FOR_ATTACK = 10

    KILL_BY_POSITION = 11
    
    GATHER_EXPLORE = 12

    GATHER_THEN_DEFEND = 13

    EXPLORE_FOR_KILL = 14

class Task:
    # TODO: tasks can expire -> especially explore
    def __init__(self, type: TaskType, destination: Position):
        self.type: TaskType = type
        self.destination: Position = destination
        self.change_idea_times: int = 0

    def __str__(self):
        return f"Task(type={self.type}, dest={self.destination})"
