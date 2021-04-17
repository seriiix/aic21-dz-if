from enum import Enum


class TaskType(Enum):
    EXPLORE = 0
    HARVEST = 1
    START = 2


class Task():

    def __init__(self, priority, task_type):
        self.priority = priority
        self.task_type = task_type
