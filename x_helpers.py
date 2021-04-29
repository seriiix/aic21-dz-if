class Position():
    def __init__(self, x, y, parent=None):
        self.x = x
        self.y = y

        # A* stuff
        self.parent: Position = parent
        self.g: int = 0
        self.h: int = 0
        self.f: int = 0

    def __eq__(self, other) -> bool:
        if type(other) == Position:
            return self.x == other.x and self.y == other.y
        return False

    def __str__(self) -> str:
        return f'x={self.x} y={self.y}'

    def __repr__(self) -> str:
        return f'x={self.x} y={self.y}'

    def __sub__(self, other):
        "Manhatan distance"
        return abs(self.x - other.x) + abs(self.y - other.y)

    # defining less than for purposes of heap queue
    def __lt__(self, other):
        return self.f < other.f

    # defining greater than for purposes of heap queue
    def __gt__(self, other):
        return self.f > other.f
