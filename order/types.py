from . import errors, entities

def encode_int(data: int, size: int) -> bytes:
    if size not in range(1, 9):
        raise errors.EncodeError('int size should be in the [1; 8] range')
    return data.to_bytes(size, 'big')

def decode_int(data: bytes, expect: int = -1) -> int:
    if len(data) not in range(1, 9):
        raise errors.DecodeError('int size should be in the [1; 8] range')
    if len(data) != expect and expect >= 1:
        raise errors.DecodeError('data len is not as expected')
    return int.from_bytes(data, 'big')


def encode_bool(data: bool) -> bytes:
    return encode_int(1 if data else 0, 1)
    
def decode_bool(data: bytes) -> bool:
    if len(data) != 1:
        raise errors.DecodeError('data len should be 1')
    return decode_int(data) >= 1


def encode_str(data: str) -> bytes:
    raw = bytes(data, 'utf-8')
    if len(raw) > 65536:
        raise errors.EncodeError('str length should be no more than 65536 (utf-8 encoding)')
    return encode_int(len(raw), 2) + raw

def strlen(data: bytes) -> int:
    return decode_int(data[:2], 2)

def decode_str(data: bytes) -> str:
    l = strlen(data)
    raw = data[2:2+l]
    if len(raw) != l:
        raise errors.DecodeError('data len not as expected')
    return raw.decode('utf-8')


def decode_list(data: bytes, cnt_size: int, decoding_func, sizing_func) -> list:
    cnt = list_elm_cnt(data, cnt_size)
    l, pos = [], cnt_size
    for i in range(cnt):
        size = sizing_func(data[pos:])
        elm = decoding_func(data[pos:pos+size]); pos += size
        l.append(elm)
    return l

def list_elm_cnt(data: bytes, cnt_size: int) -> int:
    return decode_int(data[:cnt_size], cnt_size)

def list_size(data: bytes, cnt_size: int, sizing_func) -> int:
    cnt = list_elm_cnt(data, cnt_size)
    l, pos = [], cnt_size
    for i in range(cnt):
        pos += sizing_func(data[pos:])
    return pos

def encode_list(data: list, cnt_size: int, encoding_func) -> bytes:
    p = encode_int(len(data), cnt_size)
    for i in range(len(data)):
        p += encoding_func(data[i])
    return p


def decode_int_list(data: bytes, size: int):
    return decode_list(data, 2,
        lambda p: decode_int(p, size),
        lambda p: size)

def encode_int_list(data, size: int) -> bytes:
    return encode_list(data, 2,
        lambda p: encode_int(p, size))


def decode_message_section(data: bytes) -> entities.Message.Section:
    return entities.Message.Section.decode(
        decode_int(data[ :1], 1),
        decode_int(data[1:9], 8),
        decode_str(data[9: ]))

def encode_message_section(data: entities.Message.Section) -> bytes:
    p = bytes()
    p += encode_int(data.type.value, 1)
    p += encode_int(data.blob, 8)
    p += encode_str(data.text)
    return p