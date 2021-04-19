class Position():
    def __init__(self, x, y):
        self.x = x
        self.y = y

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
