# Official Order Python API Wrapper
**Hi!**

This repository contains the source code of the Order API wrapper for the Python programming language meant for writing bots. It could be used for typical user accounts as well, and this is not prohibited by the Terms of Service in any way, but not all functions of the API are fully implemented to fulfill every action a human user might take in the app.

**Simple bot example** - sends "Hi!" when in receives "hello"
```py
import order
from order import entities
from order.entities import Message
import time

async def on_message(message, text):
    if text.lower() == 'hello':
        await client.put_entities([
            Message.create(sections=[
                Message.TextSection.create('Hi!')
            ], channel=message.channel)
        ])

async def on_entities(packet):
    for e in packet.entities:
        if isinstance(e, Message):
            # find the first text section
            for s in e.sections:
                if isinstance(s, Message.TextSection):
                    await on_message(e, s.text)
                    break

async def on_connected():
    await client.login_with_bot_token('BOT_TOKEN')

async def on_logged_in(user):
    print('Logged in as ' + user.name + '#' + str(user.tag))

client = order.Order(debug_protocol=False)
client.handler('connected', on_connected)
client.handler('logged_in', on_logged_in)
client.handler('entities',  on_entities)

client.run()
```