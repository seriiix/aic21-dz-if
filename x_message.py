
# 32 * 8 = 256 bit message
#
# antID | ChatKind | fixedLengthMessages(n)

# Types
# OBSERVATION_SIMPLE:
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
CHAT_KIND_BITS = 3

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
    OBSERVATION_SIMPLE = '000'  # [position + kind]
    OBSERVATION_VALUE = '001'  # [position + kind + value]
    SINGLE_CELL_KIND = '010'  # [kind]

    END = '111'


class CellKind(Enum):
    WALL = 0
    GRASS = 1
    BREAD = 2
    UNSAFE = 3
    # if need more set CELL_KIND_BITS(s) to 3

    ENEMY_BASE = 4
    ENEMY_WORKER = 5
    ENEMY_SOLDIER = 6

    WANT_TO_DEFEND = 7
    WANT_TO_HARVEST = 8
    # if need more set CELL_KIND_BITS(s) to 4
    WANT_TO_GATHER = 9
    WANT_TO_EXPLORE = 10

    # NO POSITION NEEDED
    # ONLY IF DAMAGED
    SOLDIER_BORN = 11
    EXPLORER_DIED = 12
    HELP_ME = 13
    LETS_FUCK_THIS_SHIT = 14
    WORKER_DIED = 15

    # if need more set CELL_KIND_BITS(s) to 5

    @staticmethod
    def get_value(kind: int):
        if kind == 0:
            return CellKind.WALL
        if kind == 1:
            return CellKind.GRASS
        if kind == 2:
            return CellKind.BREAD
        if kind == 3:
            return CellKind.UNSAFE
        if kind == 4:
            return CellKind.ENEMY_BASE
        if kind == 5:
            return CellKind.ENEMY_WORKER
        if kind == 6:
            return CellKind.ENEMY_SOLDIER
        if kind == 7:
            return CellKind.WANT_TO_DEFEND
        if kind == 8:
            return CellKind.WANT_TO_HARVEST
        if kind == 9:
            return CellKind.WANT_TO_GATHER
        if kind == 10:
            return CellKind.WANT_TO_EXPLORE
        if kind == 13:
            return CellKind.HELP_ME
        if kind == 14:
            return CellKind.LETS_FUCK_THIS_SHIT

        return None


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
        self.score = self.get_score()

        # CONSTS
        self.POSITION_BITS = 15
        self.CELL_KIND_BITS = 4
        self.MESSAGE_BITS = self.POSITION_BITS + self.CELL_KIND_BITS

    def get_score(self) -> int:
        if self.cell_kind == CellKind.WALL:
            return 1
        if self.cell_kind == CellKind.UNSAFE:
            return 1
        if self.cell_kind == CellKind.ENEMY_WORKER:
            return 3
        if self.cell_kind == CellKind.ENEMY_SOLDIER:
            return 6
        if self.cell_kind == CellKind.HELP_ME:
            return 175
        if self.cell_kind == CellKind.WANT_TO_DEFEND:
            return 180
        if self.cell_kind == CellKind.WANT_TO_EXPLORE:
            return 185
        if self.cell_kind == CellKind.WANT_TO_GATHER:
            return 190
        if self.cell_kind == CellKind.LETS_FUCK_THIS_SHIT:
            return 196
        if self.cell_kind == CellKind.ENEMY_BASE:
            return 210
        return 0

    def __str__(self) -> str:
        return f"{self.position} {self.cell_kind}"

    def __repr__(self) -> str:
        return self.__str__()


class ChatObservationValue():
    def __init__(self, position=None, cell_kind=None, value=None) -> None:
        self.position: Position = position
        self.cell_kind: CellKind = cell_kind
        self.value: int = value
        self.score = self.get_score()

        # CONSTS
        self.POSITION_BITS = 15
        self.CELL_KIND_BITS = 4
        self.VALUE_BITS = 10
        self.MESSAGE_BITS = self.POSITION_BITS + self.CELL_KIND_BITS + self.VALUE_BITS

    def get_score(self) -> int:
        if self.cell_kind == CellKind.GRASS:
            return 5
        if self.cell_kind == CellKind.BREAD:
            return 5
        return 0

    def __str__(self) -> str:
        return f"{self.position} {self.cell_kind} {self.value}"

    def __repr__(self) -> str:
        return self.__str__()


class ChatSingleCellKind():
    def __init__(self, cell_kind=None) -> None:
        self.cell_kind = cell_kind
        self.score = self.get_score()

        # CONSTS
        self.CELL_KIND_BITS = 4
        self.MESSAGE_BITS = self.CELL_KIND_BITS

    def get_score(self) -> int:
        if self.cell_kind == CellKind.SOLDIER_BORN:
            return 3
        return 0

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
            bin = bin[chat.CELL_KIND_BITS:]
            msgs.append(
                Chat(type=ChatKind.SINGLE_CELL_KIND, data=deepcopy(chat)))

    return ant_id, msgs


def decode(msg: str):
    "decode a message into multi-message format"
    s = ''
    for m in msg:
        s += to_bin_with_fixed_length(ord(m), CHAR_BITS)
    return parser(s)


# tests
if __name__ == '__main__':
    f_msg1 = Chat(type=ChatKind.OBSERVATION_SIMPLE,
                  data=ChatObservationSimple(
                      Position(15, 12), CellKind.WALL))

    f_msg2 = Chat(type=ChatKind.OBSERVATION_VALUE,
                  data=ChatObservationValue(
                      Position(3, 4), CellKind.GRASS, 55))

    f_msg3 = Chat(type=ChatKind.SINGLE_CELL_KIND,
                  data=ChatSingleCellKind(CellKind.SOLDIER_BORN))

    m, sc = encode(
        1337, [f_msg1, f_msg2, f_msg3, f_msg1, f_msg2])
    print('length of encoded msg:', len(m))
    ant_id, msgs = decode(m)
    print('decoded msg:', ant_id, msgs)
    print("x", msgs[0].data.cell_kind==CellKind.GRASS)
    print("x",msgs[0].type)
