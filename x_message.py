
#
# __|___|__________|
# 2_|_3_|____27____|


def encode(id):
    msg = ''

    # create id
    id_str_bin = f"{id:b}"
    while len(id_str_bin) < 16:
        id_str_bin = '0' + id_str_bin
    msg[0] = chr(id_str_bin[:8])
    msg[1] = chr(id_str_bin[8:])

    # temp
    while len(msg) < 32:
        msg += 'g'

    return msg


def decode(msg):
    id_p1 = ord(msg[0])
    id_p2 = ord(msg[1])
    id_p1_str = f"{id_p1:b}"
    id_p2_str = f"{id_p2:b}"
    while len(id_p1_str) < 8:
        id_p1_str = '0' + id_p1_str
    while len(id_p2_str) < 8:
        id_p2_str = '0' + id_p2_str

    id_str = id_p1_str + id_p2_str
    id = int(id_str, 2)

    return id
