
# 32 * 8 = 256 bit message
#
# antID | ChatKind | fixedLengthMessages(n)

# Types
# Observation:
# ChatKind = 000
# messages | type

from typing import List
from enum import Enum
from x_helpers import Position
from copy import deepcopy

MESSAGE_LENGTH = 32
CHAR_BITS = 8
#
ANT_ID_BITS = 12
MESSAGE_TYPE_BITS = 3

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
    OBSERVATION = '111'

    END = '111'


class CellKind(Enum):
    WALL = 0
    GRASS = 1
    BREAD = 2

    @staticmethod
    def get_value(kind: int):
        if kind == 0:
            return CellKind.WALL
        if kind == 1:
            return CellKind.GRASS
        if kind == 2:
            return CellKind.BREAD
        return None


class Chat():
    def __init__(self, type, data) -> None:
        self.type: ChatKind = type
        self.data = data

    def __str__(self) -> str:
        return f"{self.type} {self.data}"

    def __repr__(self) -> str:
        return self.__str__()


class ChatObservation():
    def __init__(self, position=None, cell_kind=None) -> None:
        self.position: Position = position  # 15 bits
        self.cell_kind: CellKind = cell_kind  # 4 bits

        # CONSTS
        self.POSITION_BITS = 15
        self.CELL_KIND_BITS = 4
        self.MESSAGE_BITS = self.POSITION_BITS + self.CELL_KIND_BITS

    def __str__(self) -> str:
        return f"{self.position} {self.cell_kind}"

    def __repr__(self) -> str:
        return self.__str__()


def to_bin_with_fixed_length(dec: int, goal_len: int):
    "converts dec to bin and make it goal_len"
    bin = f"{dec:b}"
    bin = f"{'0'*(goal_len-len(bin))}{bin}"
    return bin


def encode(ant_id, messages: List[Chat]) -> str:
    "encode a message into multi-message format"
    s = ''
    bits_remaining = 32 * 8

    # create ant id with ANT_ID_BITS bits
    ant_id_bin = to_bin_with_fixed_length(ant_id, ANT_ID_BITS)
    bits_remaining -= len(ant_id_bin)
    s += ant_id_bin

    # handling observations
    if bits_remaining >= MESSAGE_TYPE_BITS:
        s += ChatKind.OBSERVATION.value
        bits_remaining -= MESSAGE_TYPE_BITS
    else:
        return s

    for msg in messages:
        if msg.type == ChatKind.OBSERVATION:
            if bits_remaining >= msg.data.MESSAGE_BITS:
                idx = hash_pos_to_index[(
                    msg.data.position.x, msg.data.position.y)]
                s += to_bin_with_fixed_length(idx, msg.data.POSITION_BITS)
                s += to_bin_with_fixed_length(msg.data.cell_kind.value,
                                              msg.data.CELL_KIND_BITS)
                bits_remaining -= msg.data.MESSAGE_BITS

    if bits_remaining >= MESSAGE_TYPE_BITS:
        s += ChatKind.END.value

    final = ''

    while len(s) % CHAR_BITS != 0:
        s += '0'

    cntr = len(s) // CHAR_BITS

    for i in range(cntr):
        char = s[i*CHAR_BITS:(i+1)*CHAR_BITS]
        char = int(char, 2)
        final += chr(char)

    return final


def parser(bin):
    ant_id = int(bin[:ANT_ID_BITS], 2)
    bin = bin[ANT_ID_BITS:]

    msgs = []

    while len(bin) > MESSAGE_TYPE_BITS:

        chat_kind = bin[:MESSAGE_TYPE_BITS]
        bin = bin[MESSAGE_TYPE_BITS:]
        if chat_kind == ChatKind.OBSERVATION.value:
            chat = ChatObservation()
            while len(bin) >= chat.MESSAGE_BITS:
                pos = ord(chr(int(bin[:chat.POSITION_BITS], 2)))
                pos = hash_index_to_pos[pos]
                chat.position = Position(pos[0], pos[1])
                bin = bin[chat.POSITION_BITS:]
                kind = ord(chr(int(bin[:chat.CELL_KIND_BITS], 2)))
                chat.cell_kind = CellKind(kind)
                bin = bin[chat.CELL_KIND_BITS:]
                msgs.append(
                    Chat(type=ChatKind.OBSERVATION, data=deepcopy(chat)))

    return ant_id, msgs


def decode(msg: str):
    "decode a message into multi-message format"
    s = ''
    for m in msg:
        s += to_bin_with_fixed_length(ord(m), CHAR_BITS)
    return parser(s)


# tests
""" observation_msg = Chat(type=ChatKind.OBSERVATION,
                       data=ChatObservation(
                           Position(34, 34), CellKind.WALL))

observation_msg = Chat(type=ChatKind.OBSERVATION,
                       data=ChatObservation(
                           Position(0, 0), CellKind.GRASS))

e = encode(1337, [observation_msg, observation_msg, observation_msg])
id, msgs = decode(e)
print('decoded', id, msgs)
 """
