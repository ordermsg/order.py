from . import types
from enum import Enum

class Entity:
    class Type(Enum):
        USER    = 1
        CHANNEL = 2
        GROUP   = 3
        MESSAGE = 4
        ROLE    = 5

    def __init__(self, tp: int):
        self.tp = Entity.Type(tp)

    def __str__(self) -> str:
        return self.tp.name + ' (' + self._detail() + ')'

    @staticmethod
    def decode(payload: bytes, pos: int):
        e_tp  = types.decode_int(payload[pos:pos+2], 2); pos += 2
        f_cnt = types.decode_int(payload[pos:pos+2], 2); pos += 2

        if _ENTITY_CONSTRUCTORS[e_tp] is not None:
            entity = _ENTITY_CONSTRUCTORS[e_tp]()
            for i in range(f_cnt):
                f_tp   = types.decode_int(payload[pos:pos+2], 2); pos += 2
                f_desc = entity.FIELDS[f_tp]
                if f_desc is not None:
                    f_size = f_desc.size(payload[pos:])
                    f_val  = f_desc.decode(payload[pos:pos+f_size]); pos += f_size
                    setattr(entity, f_desc.attr, f_val)
        else:
            entity = None

        return (entity, pos)

    def encode(self) -> bytes:
        data, cnt = bytes(), 0

        fields = _ENTITY_CONSTRUCTORS[self.tp.value].FIELDS
        for i in range(len(fields)):
            f = fields[i]
            if f is not None and hasattr(self, f.attr):
                data += types.encode_int(i, 2)
                data += f.encode(getattr(self, f.attr))
                cnt  += 1

        data = types.encode_int(self.tp.value, 2) + types.encode_int(cnt, 2) + data
        return data

    def _detail(self) -> str:
        return ''

class EntityField:
    def __init__(self, attr: str, decode_func, size_func, encode_func):
        self.attr   = attr
        self.decode = decode_func
        self.size   = size_func
        self.encode = encode_func

class IntField(EntityField):
    def __init__(self, attr: str, size: int):
        super().__init__(attr,
            lambda p: types.decode_int(p, size),
            lambda p: size,
            lambda p: types.encode_int(p, size))

class IntListField(EntityField):
    def __init__(self, attr: str, size: int):
        super().__init__(attr,
            lambda p: types.decode_int_list(p, size),
            lambda p: types.list_size(p, 2,
                lambda x: size),
            lambda p: types.encode_int_list(p, size))

class BoolField(EntityField):
    def __init__(self, attr: str):
        super().__init__(attr,
            lambda p: types.decode_bool(p),
            lambda p: 1,
            lambda p: types.encode_bool(p))

class StrField(EntityField):
    def __init__(self, attr: str):
        super().__init__(attr,
            lambda p: types.decode_str(p),
            lambda p: types.strlen(p) + 2,
            lambda p: types.encode_str(p))

class MessageSectionsField(EntityField):
    def __init__(self, attr: str):
        super().__init__(attr,
            lambda p: types.decode_list(p, 1,
                lambda x: types.decode_message_section(x),
                lambda x: 11 + types.strlen(x[9:])),
            lambda p: types.list_size(p, 1,
                lambda x: 11 + types.strlen(x[9:])),
            lambda p: types.encode_list(p, 1,
                lambda x: types.encode_message_section(x)))

class User(Entity):
    FIELDS = [
        IntField('id', 8),
        StrField('email'),
        StrField('name'),
        IntField('tag', 4),
        IntField('status', 1),
        StrField('status_text'),
        None,
        IntField('avatar', 8),
        BoolField('mfa_enabled'),
        IntListField('friends', 8),
        IntListField('blocked', 8),
        IntListField('pending_in', 8),
        IntListField('pending_out', 8),
        IntListField('channels', 8),
        IntListField('groups', 8),
        IntListField('roles', 8),
        IntField('color', 4),
        IntListField('badges', 2),
        IntField('bot_owner', 8),
        IntListField('owned_bots', 8)
    ]

    def __init__(self):
        super().__init__(Entity.Type.USER)

    @staticmethod
    def create(**kwargs):
        obj = User()
        for k, v in kwargs.items():
            setattr(obj, k, v)
        return obj

    def _detail(self) -> str:
        return f'ID {str(self.id)}, NAME "{self.name}"'

class Channel(Entity):
    FIELDS = [
        IntField('id', 8),
        StrField('name'),
        IntListField('members', 8),
        IntField('group', 8),
        IntListField('messages', 8),
        IntListField('typing', 8),
        BoolField('rules')
    ]

    def __init__(self):
        super().__init__(Entity.Type.CHANNEL)

    @staticmethod
    def create(**kwargs):
        obj = Channel()
        for k, v in kwargs.items():
            setattr(obj, k, v)
        return obj

    def _detail(self) -> str:
        return f'ID {str(self.id)}, NAME "{self.name}", IN {str(self.group)}'

class Group(Entity):
    FIELDS = [
        IntField('id', 8),
        StrField('name'),
        IntListField('channels', 8),
        IntField('owner', 8),
        IntListField('roles', 8),
        IntField('icon', 8),
        None,                          # TODO: StrListField
        IntField('everyone_role', 8)
    ]

    def __init__(self):
        super().__init__(Entity.Type.GROUP)

    @staticmethod
    def create(**kwargs):
        obj = Channel()
        for k, v in kwargs.items():
            setattr(obj, k, v)
        return obj

    def _detail(self) -> str:
        return f'ID {str(self.id)}, NAME "{self.name}", OWNER {str(self.owner)}'

class Message(Entity):
    FIELDS = [
        IntField('id', 8),
        MessageSectionsField('sections'),
        IntField('channel', 8),
        BoolField('edited'),
        IntField('sender', 8)
    ]

    def __init__(self):
        super().__init__(Entity.Type.MESSAGE)

    @staticmethod
    def create(sections: list, channel: int):
        e = Entity(Entity.Type.MESSAGE)
        e.id       = 0
        e.sections = sections
        e.channel  = channel
        return e

    def _detail(self) -> str:
        return f'ID {str(self.id)}, SECTION CNT {str(len(self.sections))}, IN {str(self.channel)}'

    class Section:
        class Type(Enum):
            TEXT  = 0
            FILE  = 1
            CODE  = 2
            QUOTE = 3

        def __init__(self, type: int, blob: int, text: str):
            self.type = Message.Section.Type(type)
            self.blob = blob
            self.text = text

        @staticmethod
        def decode(type: int, blob: int, text: str):
            CONSTRUCTORS = [
                Message.TextSection,
                Message.FileSection,
                Message.CodeSection,
                Message.QuoteSection
            ]
            return CONSTRUCTORS[type](type, blob, text)

    class TextSection(Section):
        @staticmethod
        def create(text: str):
            return Message.Section(Message.Section.Type.TEXT, 0, text)

    class FileSection(Section):
        @staticmethod
        def create(blob: int):
            return Message.Section(Message.Section.Type.FILE, blob, '')

    class CodeSection(Section):
        @staticmethod
        def create(text: str):
            return Message.Section(Message.Section.Type.CODE, 0, text)

    class QuoteSection(Section):
        @staticmethod
        def create(text: str, reply_to: int):
            return Message.Section(Message.Section.Type.QUOTE, reply_to, text)

class Role(Entity):
    FIELDS = [
        IntField('id', 8),
        StrField('name'),
        IntField('color', 4),
        IntField('group', 8),
        IntField('priority', 2),
        IntField('permissions', 6),
        IntListField('members', 8)
    ]

    def __init__(self):
        super().__init__(Entity.Type.GROUP)

    @staticmethod
    def create(**kwargs):
        obj = Channel()
        for k, v in kwargs.items():
            setattr(obj, k, v)
        return obj

    def _detail(self) -> str:
        return f'ID {str(self.id)}, NAME "{self.name}", GROUP {str(self.group)}'



class EntityGetRequest:
    class Pagination:
        def __init__(self, field: int, direction: bool, id: int, count: int):
            self.field = field
            self.dir   = direction
            self.id    = id
            self.cnt   = count
        def encode(self) -> bytes:
            return types.encode_int(self.field, 2) + types.encode_bool(self.dir) + types.encode_int(self.id, 8) + types.encode_int(self.cnt, 1)
    class Contexting:
        def __init__(self, tp: int, id: int):
            self.tp = tp
            self.id = id
        def encode(self) -> bytes:
            return types.encode_int(self.tp, 2) + types.encode_int(self.id, 8)

    def __init__(self, tp: int, id: int, pagination: Pagination =None, contexting: Contexting =None):
        self.tp   = Entity.Type(tp)
        self.id   = id
        self.page = pagination
        self.ctx  = contexting

    def __str__(self) -> str:
        return f'{self.tp.name} (ID {str(self.id)} CTX {str(self.ctx)} PAGE {str(self.page)})'

    def encode(self) -> bytes:
        data = bytes()
        data += types.encode_int(self.tp.value, 2)
        data += types.encode_int(self.id,       8)

        data += types.encode_bool(self.page is not None)
        data += types.encode_bool(self.ctx  is not None)
        if self.page is not None:
            data += self.page.encode()
        if self.ctx  is not None:
            data += self.ctx .encode()

        return data

_ENTITY_CONSTRUCTORS = [None,
    User,
    Channel,
    Group,
    Message,
    Role
]