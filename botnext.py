import numpy as np
import os
import os.path
import discord
import asyncio
import json as js
import datetime as dt

TOKEN = 'XXXXXXXX'
LOCK = 0
outfile = 'w12.json'
backup = 'w12-backup.json'
logging = True
unclaimers = {'Cthulhu#4513', 'IceHawk#3658', 'Bonsai#4738', 'SilentDeath#2050', 'LostSoul#9238', 'SexyMinxy#6797'}

client = discord.Client()


@client.event
async def on_ready():
    channel = discord.utils.get(client.get_all_channels(), name='botlog')
    await client.send_message(channel, 'Initializing...')
    await checkFile()
    await client.send_message(channel, 'Complete.')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    channel = discord.utils.get(client.get_all_channels(), name='botlog')
    correctSyntax = '!claim xxx:xxx <eta or notes> \nall fields mandatory'

    if message.content.startswith('!claim'):
        if (LOCK == 0):
            tmp = message.content.split(None, 2)

            coords = tmp[1]
            keyBuilder = coords.split(':')
            key = keyBuilder[0] + keyBuilder[1]
            if len(tmp) < 3:
                eta = ''
            else:
                eta = tmp[2]

            if len(key) != 6:
                await client.send_message(message.channel, 'Coordinates must be a pair of 3 digit numbers. Valid: 123:456. Invalid: 1:5.')
                return

            await client.send_message(channel, tmp)

            with open(outfile, 'r+') as f:
                data = js.load(f)
                content = await checkCoords(key, data)

            await backup(data)

            if content == None:
                await addCoords(coords, eta, str(message.author), data)
                await client.send_message(message.channel, 'Successfully claimed ' + coords + ' for ' + str(message.author))
                await client.send_message(channel, 'Successfully claimed ' + coords + ' for ' + str(message.author))
            else:
                await client.send_message(message.channel, coords + ': ' + content)
        else:
            await client.send_message(message.channel, "File lock active, try again later " + message.author.mention)

    if message.content.startswith('!check'):
        if (LOCK == 0):
            tmp = message.content.split(None, 1)
            coords = tmp[1]
            keyBuilder = coords.split(':')
            key = keyBuilder[0] + keyBuilder[1]

            with open(outfile, 'r+') as f:
                data = js.load(f)
                content = await checkCoords(key, data)
                if content != None:
                    await client.send_message(message.channel, coords + ': ' + content)
                else:
                    await client.send_message(message.channel, 'No data.')
        else:
            await client.send_message(message.channel, "File lock active, try again later " + message.author.mention)

    if message.content.startswith('!usage'):
        await client.send_message(message.channel, correctSyntax)

    if message.content.startswith('!help'):
        await client.send_message(message.channel, correctSyntax)

    if message.content.startswith('!rewind'):
        if str(message.author) in unclaimers:
            await rewind()

    if message.content.startswith('!unclaim'):
        if (LOCK == 0):
            if str(message.author) in unclaimers:
                tmp = message.content.split(None, 1)
                coords = tmp[1]
                await client.send_message(channel, "Unclaim of " + coords + " requested by: " + message.author)
                keyBuilder = coords.split(':')
                key = keyBuilder[0] + keyBuilder[1]
                if len(key) != 6:
                    await client.send_message(message.channel, 'Coordinates must be a pair of 3 digit numbers. Valid: 001:500. Invalid: 1:5.')
                    return

                with open(outfile, 'r+') as f:
                    data = js.load(f)
                    content = await checkCoords(key, data)

                if (content == None):
                    await client.send_message(message.channel, 'No claim exists for: ' + key)
                    return

                await unclaim(key, data)
                await client.send_message(message.channel, 'Unclaim successful')
            else:
                await client.send_message(message.channel, 'Not authorized')
        else:
            await client.send_message(message.channel, "File lock active, try again later " + message.author.mention)


@asyncio.coroutine
def unclaim(coords, claims):
    channel = discord.utils.get(client.get_all_channels(), name='botlog')
    LOCK = 1
    yield from client.send_message(channel, "File Lock initiated")

    with open(outfile, 'w+') as f:
        del claims[coords]
        js.dump(claims, f)

    LOCK = 0
    yield from client.send_message(channel, "File Lock released")


@asyncio.coroutine
def backup(data):
    with open('w12-backup.json', 'w+') as f:
        js.dump(data, f)

@asyncio.coroutine
def rewind():
    with open('w12-backup.json', 'r') as f:
        data = js.load(f)

    with open(outfile, 'w+') as fp:
        js.dump(data, fp)

@asyncio.coroutine
def checkCoords(key, claims):
    channel = discord.utils.get(client.get_all_channels(), name='botlog')

    yield from client.send_message(channel, key)

    if claims == None:
        return
    else:
        if key in claims:
            return claims[key]
        else:
            return

@asyncio.coroutine
def addCoords(coords, eta, claimer, claims):
    channel = discord.utils.get(client.get_all_channels(), name='botlog')
    tmp = coords.split(':')
    key = tmp[0] + tmp[1]
    val = str(dt.datetime.utcnow()) + ' Claimed by ' + claimer + ' with notes: ' + eta
    with open(outfile, 'w+') as f:
        claims[key] = val
        js.dump(claims, f)

@asyncio.coroutine
def checkFile():
    channel = discord.utils.get(client.get_all_channels(), name='botlog')
    dict = {'000000':'Test coords'}
    yield from client.send_message(channel, 'Checking file')
    if not os.path.exists(outfile):
        with open(outfile, 'w+') as f:
            js.dump(dict, f)
            yield from client.send_message(channel, 'File initialized.')
    else:
        with open(outfile, 'r+') as f:
            if f.read() == '':
                js.dump(dict, f)
                yield from client.send_message(channel, 'File re-initialized.')

client.run(TOKEN)
