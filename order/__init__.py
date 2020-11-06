# Official Order API for Python
# Full docs: https://docs.ordermsg.tk (new), https://ordermsg.tk/docs (legacy)

import asyncio, time, threading
import ssl, gzip

from . import packets, types, errors, entities

class Order:
    PACKET_EVENTS = {
        packets.PongPacket:      'pong',
        packets.StatusPacket:    'status',
        packets.ContTokenPacket: 'continuation',
        packets.EntitiesPacket:  'entities'
    }

    def __init__(self, debug_protocol: bool =False):
        self.HOSTNAME      = 'ordermsg.tk'
        self.PORT_PRIMARY  = 1746
        self.PORT_BLOB     = 1747
        self.PROTO_VERSION = 3

        self.debug_protocol   = debug_protocol
        self.next_packet_id   = 1
        self.events           = {}
        self.packet_callbacks = {}
        self.ping_time        = -1
        self.ping_thread      = None

    # Sends a byte array
    async def _send_bytes(self, data: bytes) -> None:
        self._writer.write(data)
        await self._writer.drain()

    # Sends a packet
    async def send(self, packet: packets.OrderPacket, callback=None) -> None:
        # Set the sequential ID
        packet.seq = self.next_packet_id
        self.next_packet_id += 1
        # Create a callback
        if callback is not None:
            self._reg_packet_callback(packet.seq, callback)
        # Encode the payload
        payload = packet.encode_payload()
        # Encode the data header
        data = bytes()
        data += types.encode_int(packet.type.value, 1)
        data += types.encode_int(packet.seq, 4)
        data += types.encode_int(packet.reply, 4)
        data += payload
        # Compress data
        compressed = len(data) >= 32
        if compressed:
            data = gzip.compress(data)
        # Add the compression header
        data = types.encode_bool(compressed) + types.encode_int(len(data), 4) + data
        # Send bytes
        if self.debug_protocol:
            print(' <-- ' + str(packet))
        await self._send_bytes(data)

    # Reads one packet
    async def _read_bytes(self) -> None:
        # Read the compression header
        compression_hdr = await self._reader.readexactly(5)
        compressed = types.decode_bool(compression_hdr[:1])
        data_len   = types.decode_int (compression_hdr[1:], 4)
        # Read and decompress data
        data = await self._reader.readexactly(data_len)
        if compressed:
            data = gzip.decompress(data)
        # Decode the data header
        packet_type    = types.decode_int(data[ :1], 1)
        packet_seq     = types.decode_int(data[1:5], 4)
        packet_reply   = types.decode_int(data[5:9], 4)
        packet_payload = data[9:]
        # Decode the payload
        packet = packets.OrderPacket.decode(packet_type, packet_seq, packet_reply, packet_payload)
        if self.debug_protocol:
            print(' --> ' + str(packet))
        # Fire a callback
        handled = await self._fire_packet_callback(packet.reply, [packet])
        # Fire an event
        for k in self.PACKET_EVENTS:
            v =  self.PACKET_EVENTS[k]
            if not handled and isinstance(packet, k) and await self._fire_event(v, [packet]):
                handled = True
                break
        if not handled:
            await self._fire_event('packet', [packet])

    # Initializes the connection
    # DOES _NOT_ RETURN
    def run(self) -> None:
        loop = asyncio.get_event_loop()
        # Connect to the server
        self._ctx = ssl.create_default_context()
        self._reader, self._writer = loop.run_until_complete(asyncio.open_connection(
            self.HOSTNAME, self.PORT_PRIMARY, ssl=self._ctx, loop=loop))
        # We are connected
        loop.run_until_complete(self._fire_event('connected', ()))
        # Read packets
        try:
            while True:
                loop.run_until_complete(self._read_bytes())
        except asyncio.IncompleteReadError:
            print(' XXX DISCONNECTED')
            loop.run_until_complete(self._fire_event('disconnected', []))

    # Sends a ping packet periodically
    def _do_send_pings(self):
        async def write_ping_time(p):
            self.ping_time = (time.time_ns() - self._sent_ping) // 1000000
            
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while True:
            time.sleep(10)
            self._sent_ping = time.time_ns()
            loop.run_until_complete(self.send(packets.PingPacket(0, 123), write_ping_time))

    # Registers a packet callback
    def _reg_packet_callback(self, seq: int, func) -> None:
        self.packet_callbacks[seq] = func

    # Fires and deletes a packet callback
    async def _fire_packet_callback(self, reply: int, args: tuple) -> bool:
        if reply not in self.packet_callbacks:
            return False
        if args is None:
            args = tuple()
        await self.packet_callbacks[reply](*args)
        del self.packet_callbacks[reply]
        return True

    # Fires a callback
    async def _fire_event(self, name: str, args: tuple) -> bool:
        if name in self.events:
            await self.events[name](*args)
            return True
        return False

    # Registers an event handler
    def handler(self, name: str, func) -> None:
        self.events[name] = func

    # Packet-specific methods

    # Logs in
    async def login(self, email: str, password: str):
        async def cb1(p):
            self.ping_thread = threading.Thread(target=self._do_send_pings, name='PingThread').start()
            self.handler('got_identity', cb2)
            await self.resolve_identity()
        async def cb2(user):
            await self._fire_event('logged_in', (user,))

        await self.send(packets.LoginPacket(0, self.PROTO_VERSION, email, password), cb1)

    # Logs in with a bot token
    async def login_with_bot_token(self, token: str):
        await self.login('___@bot@token@___', token)

    # Gets entities
    async def get_entities(self, requests: list, callback=None):
        async def cb(p):
            if callback is not None:
                await callback(p.entities)

        await self.send(packets.EntityGetPacket(0, requests), cb)

    # Puts entities
    async def put_entities(self, entities: list):
        await self.send(packets.EntitiesPacket(reply=0, ents=entities))

    # Gets the ID of the current user
    async def resolve_identity(self):
        async def cb(ents):
            user = ents[0]
            await self._fire_event('got_identity', (user,))

        await self.get_entities([entities.EntityGetRequest(entities.Entity.Type.USER, 0)], cb)
        