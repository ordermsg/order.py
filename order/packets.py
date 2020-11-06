from enum import Enum
from . import types, entities

class PacketType(Enum):
    LOGIN         = 1
    PING          = 2
    PONG          = 3
    STATUS        = 4
    SIGNUP        = 5
    ENTITY_GET    = 6
    ENTITIES      = 7
    BLOB_GET      = 8
    BLOB_RESPONSE = 9
    MFA_SECRET    = 10
    BLOB_PUT      = 11
    CONT_TOKEN    = 12
    CONTACTS_MNG  = 13

class StatusCode(Enum):
    OUTDATED                      = 1
    INVALID_CONNECTION_STATE      = 2
    LOGIN_ERROR                   = 3
    MFA_REQUIRED                  = 4
    LOGIN_SUCCESS                 = 5
    SIGNUP_ERROR                  = 6
    RATE_LIMITING                 = 7
    INVALID_ID                    = 8
    BLOB_TOO_LARGE                = 9
    PERMISSION_DENIED             = 10
    INVALID_CONT_TOKEN            = 11
    USER_NOT_PENDING              = 12
    CONTACT_ACTION_NOT_APPLICABLE = 13
    INVALID_USERNAME              = 14
    INVALID_ENTITY                = 15
    ENTITY_NOT_PAGINABLE          = 16
    INVALID_INVITE                = 17
    INTERNAL_ERROR                = 18
    UNKNOWN_PACKET                = 19

class OrderPacket:
    def __init__(self):
        pass

    def __init__(self, type: int, seq: int, reply: int, payload: bytes):
        self.type    = PacketType(type)
        self.seq     = seq
        self.reply   = reply
        self.payload = payload

    @staticmethod
    def decode(type: int, seq: int, reply: int, payload: bytes):
        CONSTRUCTORS = [None,
            None,               # login
            None,               # ping
            PongPacket,
            StatusPacket,
            None,               # signup
            None,               # entity get
            EntitiesPacket,
            None,               # blob get
            None,               # blob response
            None,               # MFA secret
            None,               # blob put
            ContTokenPacket,
            None                # contacts manage
        ]
        packet = CONSTRUCTORS[type](payload=payload)
        packet.type    = PacketType(type)
        packet.seq     = seq
        packet.reply   = reply
        packet.payload = payload
        return packet

    def __str__(self) -> str:
        return f'{str(self.type)} (SEQ {str(self.seq)} <- REP {str(self.reply)}) PAYLOAD [{self._detail()}]'

    def _detail(self):
        return ''

    def encode_payload(self) -> bytes:
        pass


class LoginPacket(OrderPacket):
    def __init__(self, reply: int, proto: int, email: str, password: str):
        super().__init__(PacketType.LOGIN, 0, reply, None)
        self.proto    = proto
        self.email    = email
        self.password = password

    def encode_payload(self) -> bytes:
        return types.encode_int(self.proto, 2) + types.encode_str(self.email) + types.encode_str(self.password)

    def _detail(self):
        # hide the password behind asterisks
        return f'EMAIL "{self.email}", PASSWORD "{"*" * len(self.password)}"'


class PingPacket(OrderPacket):
    def __init__(self, reply: int, echo: int):
        super().__init__(PacketType.PING, 0, reply, None)
        self.echo = echo

    def encode_payload(self) -> bytes:
        return types.encode_int(self.echo, 4)

    def _detail(self):
        return f'ECHO {self.echo}'


class PongPacket(OrderPacket):
    def __init__(self, payload: bytes):
        self.echo = types.decode_int(payload, 4)

    def _detail(self):
        return f'ECHO {str(self.echo)}'


class StatusPacket(OrderPacket):
    def __init__(self, payload: bytes):
        self.code = StatusCode(types.decode_int(payload[:2], 2))
        self.msg  = types.decode_str(payload[2:])

    def _detail(self):
        return f'CODE {str(self.code)}, MSG "{self.msg}"'


class EntityGetPacket(OrderPacket):
    def __init__(self, reply: int, requests):
        super().__init__(PacketType.ENTITY_GET, 0, reply, None)
        self.requests = requests

    def encode_payload(self) -> bytes:
        data = types.encode_int(len(self.requests), 2)
        for r in self.requests:
            data += r.encode()
        return data

    def _detail(self):
        return ' ; '.join([f'[{str(i)}] {str(self.requests[i])}' for i in range(len(self.requests))])

class EntitiesPacket(OrderPacket):
    def __init__(self, reply: int =None, ents =None, payload: bytes =None):
        if payload is None:
            super().__init__(PacketType.ENTITIES, 0, reply, None)
            self.entities = ents
        else:
            pos, self.entities = 0, []
            cnt = types.decode_int(payload[:2], 2); pos += 2
            for i in range(cnt):
                entity, pos = entities.Entity.decode(payload, pos)
                self.entities.append(entity)

    def encode_payload(self) -> bytes:
        data = types.encode_int(len(self.entities), 2)
        for e in self.entities:
            data += e.encode()
        return data

    def _detail(self):
        # yuck
        return ' ; '.join([f'[{str(i)}] {str(self.entities[i])}' for i in range(len(self.entities))])


class ContTokenPacket(OrderPacket):
    def __init__(self, payload: bytes):
        self.token = types.decode_str(payload)

    def _detail(self):
        return f'TOKEN "{self.token}"'