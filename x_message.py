from typing import List
from enum import Enum
from x_helpers import Position
from copy import deepcopy

MESSAGE_LENGTH = 32
CHAR_BITS = 8
#
ANT_ID_BITS = 12
CHAT_KIND_BITS = 2
CELL_KIND_BITS = 5

# hashes
hash_index = 0
hash_index_to_pos = []
hash_pos_to_index = {}

for i in range(35):
    for j in range(35):
        hash_index_to_pos.append([i, j])
        hash_pos_to_index[(i, j)] = hash_index
        hash_index += 1


class ChatKind(Enum):
    OBSERVATION_VALUE = '00'  # [position + kind + value]
    OBSERVATION_SIMPLE = '01'  # [position + kind]
    SINGLE_CELL_KIND = '10'  # [kind]

    END = '11'  # not needed


class CellKind(Enum):
    WALL = 0
    GRASS = 1
    BREAD = 2
    INVALID = 3
    SWAMP = 4
    TRAP = 5

    ENEMY_BASE = 6
    ME_WORKER = 7
    ME_SOLDIER = 8

    WANT_TO_DEFEND = 9
    WANT_TO_HARVEST = 10
    WANT_TO_GATHER = 11
    WANT_TO_EXPLORE = 12

    # NO POSITION NEEDED
    EXPLORER_DIED = 14
    HELP_ME = 15
    LETS_FUCK_THIS_SHIT = 16
    ME_EXPLORER = 17
    WORKER_BORN = 18
    WORKER_DIED = 19
    SOLDIER_BORN = 20
    SOLDIER_DIED = 21
    INVALID_FOR_WORKER = 22
    DEFENDER_DIED = 23

    @staticmethod
    def get_value(kind: int):
        if kind == 0:
            return CellKind.WALL
        if kind == 1:
            return CellKind.GRASS
        if kind == 2:
            return CellKind.BREAD
        if kind == 3:
            return CellKind.INVALID
        if kind == 4:
            return CellKind.SWAMP
        if kind == 5:
            return CellKind.TRAP
        if kind == 6:
            return CellKind.ENEMY_BASE
        if kind == 7:
            return CellKind.ME_WORKER
        if kind == 8:
            return CellKind.ME_SOLDIER
        if kind == 9:
            return CellKind.WANT_TO_DEFEND
        if kind == 10:
            return CellKind.WANT_TO_HARVEST
        if kind == 11:
            return CellKind.WANT_TO_GATHER
        if kind == 12:
            return CellKind.WANT_TO_EXPLORE
        if kind == 14:
            return CellKind.EXPLORER_DIED
        if kind == 15:
            return CellKind.HELP_ME
        if kind == 16:
            return CellKind.LETS_FUCK_THIS_SHIT
        if kind == 17:
            return CellKind.ME_EXPLORER
        if kind == 18:
            return CellKind.WORKER_BORN
        if kind == 19:
            return CellKind.WORKER_DIED
        if kind == 20:
            return CellKind.SOLDIER_BORN
        if kind == 21:
            return CellKind.SOLDIER_DIED
        if kind == 22:
            return CellKind.INVALID_FOR_WORKER
        if kind == 23:
            return CellKind.DEFENDER_DIED
        return None


def get_kind_score(kind: CellKind):
    if kind == CellKind.WALL:
        return 5
    if kind == CellKind.GRASS:
        return 5
    if kind == CellKind.BREAD:
        return 5
    if kind == CellKind.INVALID:
        return 100
    if kind == CellKind.INVALID_FOR_WORKER:
        return 100
    if kind == CellKind.SWAMP:
        return 10
    if kind == CellKind.TRAP:
        return 10
    if kind == CellKind.ME_WORKER:
        return 3
    if kind == CellKind.ME_SOLDIER:
        return 6
    if kind == CellKind.ENEMY_BASE:
        return 2000

    if kind == CellKind.WANT_TO_DEFEND:
        return 10
    if kind == CellKind.WANT_TO_HARVEST:
        return 10
    if kind == CellKind.WANT_TO_GATHER:
        return 1500
    if kind == CellKind.WANT_TO_EXPLORE:
        return 200

    if kind == CellKind.HELP_ME:
        return 150
    if kind == CellKind.LETS_FUCK_THIS_SHIT:
        return 3000
    if kind == CellKind.ME_EXPLORER:
        return 100

    if kind == CellKind.WORKER_BORN:
        return 250
    if kind == CellKind.WORKER_DIED:
        return 254
    if kind == CellKind.SOLDIER_BORN:
        return 251
    if kind == CellKind.SOLDIER_DIED:
        return 253
    if kind == CellKind.DEFENDER_DIED:
        return 250
    if kind == CellKind.EXPLORER_DIED:
        return 250

    return 0


class Chat():
    def __init__(self, type, data) -> None:
        self.type: ChatKind = type
        self.data = data
        self.score = self.data.score

    def __str__(self) -> str:
        return f"({self.type} {self.data} sc={self.score})"

    def __repr__(self) -> str:
        return self.__str__()


class ChatObservationSimple():
    def __init__(self, position=None, cell_kind=None) -> None:
        self.position: Position = position
        self.cell_kind: CellKind = cell_kind
        self.score = 0
        self.get_score()

        # CONSTS
        self.POSITION_BITS = 15
        self.CELL_KIND_BITS = CELL_KIND_BITS
        self.MESSAGE_BITS = self.POSITION_BITS + self.CELL_KIND_BITS

    def get_score(self) -> int:
        self.score = get_kind_score(self.cell_kind)

    def __str__(self) -> str:
        return f"{self.position} {self.cell_kind}"

    def __repr__(self) -> str:
        return self.__str__()


class ChatObservationValue():
    def __init__(self, position=None, cell_kind=None, value=None) -> None:
        self.position: Position = position
        self.cell_kind: CellKind = cell_kind
        self.value: int = value
        self.score = 0
        self.get_score()

        # CONSTS
        self.POSITION_BITS = 15
        self.CELL_KIND_BITS = CELL_KIND_BITS
        self.VALUE_BITS = 10
        self.MESSAGE_BITS = self.POSITION_BITS + self.CELL_KIND_BITS + self.VALUE_BITS

    def get_score(self) -> int:
        self.score = get_kind_score(self.cell_kind)

    def __str__(self) -> str:
        return f"{self.position} {self.cell_kind} {self.value}"

    def __repr__(self) -> str:
        return self.__str__()


class ChatSingleCellKind():
    def __init__(self, cell_kind=None) -> None:
        self.cell_kind = cell_kind
        self.score = 0
        self.get_score()

        # CONSTS
        self.CELL_KIND_BITS = CELL_KIND_BITS
        self.MESSAGE_BITS = self.CELL_KIND_BITS

    def get_score(self) -> int:
        self.score = get_kind_score(self.cell_kind)

    def __str__(self) -> str:
        return f"{self.cell_kind}"

    def __repr__(self) -> str:
        return self.__str__()


def to_bin_with_fixed_length(dec: int, goal_len: int):
    "converts dec to bin and make it goal_len"
    bin = f"{dec:b}"
    bin = f"{'0'*(goal_len-len(bin))}{bin}"
    return bin


def encode(ant_id, messages: List[Chat]) -> str:
    "encode a message into multi-message format"
    messages.sort(key=lambda x: x.score, reverse=True)
    s = ''
    total_score = 0
    bits_remaining = MESSAGE_LENGTH * CHAR_BITS

    # create ant id with ANT_ID_BITS bits
    ant_id_bin = to_bin_with_fixed_length(ant_id, ANT_ID_BITS)
    s += ant_id_bin
    bits_remaining -= len(ant_id_bin)

    for msg in messages:

        # for OBSERVATION_SIMPLE
        if msg.type == ChatKind.OBSERVATION_SIMPLE:
            if bits_remaining >= msg.data.MESSAGE_BITS + CHAT_KIND_BITS:
                s += ChatKind.OBSERVATION_SIMPLE.value
                idx = hash_pos_to_index[(
                    msg.data.position.x, msg.data.position.y)]
                s += to_bin_with_fixed_length(idx, msg.data.POSITION_BITS)
                s += to_bin_with_fixed_length(msg.data.cell_kind.value,
                                              msg.data.CELL_KIND_BITS)
                bits_remaining -= msg.data.MESSAGE_BITS + CHAT_KIND_BITS
                total_score += msg.data.score

        # for OBSERVATION_VALUE
        if msg.type == ChatKind.OBSERVATION_VALUE:
            if bits_remaining >= msg.data.MESSAGE_BITS + CHAT_KIND_BITS:
                s += ChatKind.OBSERVATION_VALUE.value
                idx = hash_pos_to_index[(
                    msg.data.position.x, msg.data.position.y)]
                s += to_bin_with_fixed_length(idx, msg.data.POSITION_BITS)
                s += to_bin_with_fixed_length(msg.data.cell_kind.value,
                                              msg.data.CELL_KIND_BITS)
                s += to_bin_with_fixed_length(msg.data.value,
                                              msg.data.VALUE_BITS)
                bits_remaining -= msg.data.MESSAGE_BITS + CHAT_KIND_BITS
                total_score += msg.data.score

        # for SINGLE_CELL_KIND
        if msg.type == ChatKind.SINGLE_CELL_KIND:
            if bits_remaining >= msg.data.MESSAGE_BITS + CHAT_KIND_BITS:
                s += ChatKind.SINGLE_CELL_KIND.value
                s += to_bin_with_fixed_length(msg.data.cell_kind.value,
                                              msg.data.CELL_KIND_BITS)
                bits_remaining -= msg.data.MESSAGE_BITS + CHAT_KIND_BITS
                total_score += msg.data.score

    final = ''

    while len(s) % CHAR_BITS != 0:
        s += '0'
        bits_remaining -= 1

    cntr = len(s) // CHAR_BITS

    for i in range(cntr):
        char = s[i*CHAR_BITS:(i+1)*CHAR_BITS]
        char = int(char, 2)
        final += chr(char)

    return final, total_score


def parser(bin):
    ant_id = int(bin[:ANT_ID_BITS], 2)
    bin = bin[ANT_ID_BITS:]

    msgs = []

    while len(bin) > CHAT_KIND_BITS:

        chat_kind = bin[:CHAT_KIND_BITS]
        bin = bin[CHAT_KIND_BITS:]

        # OBSERVATION_SIMPLE
        if chat_kind == ChatKind.OBSERVATION_SIMPLE.value:
            chat = ChatObservationSimple()
            if len(bin) < chat.MESSAGE_BITS:
                break
            pos = ord(chr(int(bin[:chat.POSITION_BITS], 2)))
            pos = hash_index_to_pos[pos]
            chat.position = Position(pos[0], pos[1])
            bin = bin[chat.POSITION_BITS:]
            kind = ord(chr(int(bin[:chat.CELL_KIND_BITS], 2)))
            chat.cell_kind = CellKind(kind)
            chat.get_score()
            bin = bin[chat.CELL_KIND_BITS:]
            msgs.append(
                Chat(type=ChatKind.OBSERVATION_SIMPLE, data=deepcopy(chat)))

        # OBSERVATION_VALUE
        if chat_kind == ChatKind.OBSERVATION_VALUE.value:
            chat = ChatObservationValue()
            if len(bin) < chat.MESSAGE_BITS:
                break
            pos = ord(chr(int(bin[:chat.POSITION_BITS], 2)))
            pos = hash_index_to_pos[pos]
            chat.position = Position(pos[0], pos[1])
            bin = bin[chat.POSITION_BITS:]
            kind = ord(chr(int(bin[:chat.CELL_KIND_BITS], 2)))
            chat.cell_kind = CellKind(kind)
            chat.get_score()
            bin = bin[chat.CELL_KIND_BITS:]
            value = ord(chr(int(bin[:chat.VALUE_BITS], 2)))
            chat.value = value
            bin = bin[chat.VALUE_BITS:]
            msgs.append(
                Chat(type=ChatKind.OBSERVATION_VALUE, data=deepcopy(chat)))

        # SINGLE_CELL_KIND
        if chat_kind == ChatKind.SINGLE_CELL_KIND.value:
            chat = ChatSingleCellKind()
            if len(bin) < chat.MESSAGE_BITS:
                break
            kind = ord(chr(int(bin[:chat.CELL_KIND_BITS], 2)))
            chat.cell_kind = CellKind(kind)
            chat.get_score()
            bin = bin[chat.CELL_KIND_BITS:]
            msgs.append(
                Chat(type=ChatKind.SINGLE_CELL_KIND, data=deepcopy(chat)))

    return ant_id, msgs


def decode(msg: str):
    "decode a message into multi-message format"
    try:
        s = ''
        for m in msg:
            s += to_bin_with_fixed_length(ord(m), CHAR_BITS)
        return parser(s)
    except Exception:
        return 0, []


# tests
if __name__ == '__main__':
    f_msg1 = Chat(type=ChatKind.OBSERVATION_SIMPLE,
                  data=ChatObservationSimple(
                      Position(15, 12), CellKind.ME_EXPLORER))

    f_msg2 = Chat(type=ChatKind.OBSERVATION_VALUE,
                  data=ChatObservationValue(
                      Position(3, 4), CellKind.BREAD, 16))

    f_msg3 = Chat(type=ChatKind.SINGLE_CELL_KIND,
                  data=ChatSingleCellKind(CellKind.HELP_ME))

    m, sc = encode(
        1337, [f_msg1, f_msg2, f_msg3, f_msg1, f_msg2])

    id, e = decode(m)

    print(id, e)
