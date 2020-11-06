# Official Order Python API Wrapper
**Hi!**

This repository contains the source code of the Order API wrapper for the Python programming language meant for writing bots. It could be used for typical user accounts as well, and this is not prohibited by the Terms of Service in any way, but not all functions of the API are fully implemented to fulfill every action a human user might take in the app.

## How do I get a bot token?
Head into the app. Open user settings by clicking on you avatar in the bottom-right corner. Navigate to the "Developers" tab

![](promo/settings.png)

Choose a cool name and hit the "create" button. Below that you will see the list of bot IDs you have created previously.

![](promo/creation.png)

Once you did that, you should see a big popup. Copy the bot ID and token and save them in a separate file. **You will only see this token once!**

![](promo/created.png)

## How do I use my bot?
Bots can only be used in groups. In order to add a bot, you should know its ID.\
Head into the app. Choose or create a group you would like to add the bot into. Open its settings by clicking on its title in the top-left corner. Navigate to the "Invites" tab. Paste your bot ID into the "Bot ID" field. Click the "Invite bot" button. You're all set!

## Simple bot example
Sends "Hi!" when it receives "hello"

![](promo/promo.png)
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