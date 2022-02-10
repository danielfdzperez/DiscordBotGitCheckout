# bot.py
#Tutorial https://realpython.com/how-to-make-a-discord-bot-python/
"""
doc
https://discord.com/developers/docs/resources/channel#pin-message
https://discord.com/developers/docs/resources/channel#get-channel-messages
https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#ext-commands-api-bot
https://discordpy.readthedocs.io/en/stable/api.html#discord.Member
"""
import os
import random

import re

from discord.ext import commands
from dotenv import load_dotenv

data = {}

HEADER = "Checkout files:"
NOTIFY_HEADER = "Notify users"
CONTROL_CHARACTER = ":"


def AddListMessage(usr, content):
    return f"\n{content} : {usr}"

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')



#@bot.command(name='echo',help='Use !checkout [fileName]\nIf nobody has checked out the file, it is added to the list of checkout files')
#async def echo(ctx):
#    await ctx.send(f"{ctx.author} {ctx.author.name}")
#    member = ctx.author
#    await member.create_dm()
#    await member.dm_channel.send(
#        f'{ctx.guild.name}welcome to my Discord server!'
#    )


@bot.event
async def on_ready():
    for guild in bot.guilds:
        data[guild.id] = []
        print(guild.id)
    print ("Booting up your system")
    print ("I am running on " + str(bot.user.name))
    print ("With the ID: " + str(bot.user.id))


async def GetPinedList(ctx, header):
    pinedMessages = await ctx.channel.pins()
    pinedLists = [i for i in pinedMessages if i.content.startswith(header)]
    if len(pinedLists)>0:
        theList = pinedLists[0]
        lines = theList.content.splitlines(True)
        return theList, lines
    else:
        return None, None

async def GetNotifyPinedList(ctx):
    return await GetPinedList(ctx, NOTIFY_HEADER)

def LookForLine(fileName, lines):
    line = [line for line in lines[1:] if fileName in re.findall("([\w*\s*]*) :",line)]
    if len(line)>0:
        return line[0]
    else:
        return None

def GetAllUsersFromList(line):
    #return re.findall(": ([\w+#\d\s]*)",line)[0].split()
    return re.findall(": ([\d*\s]*)",line)[0].split()

async def GetAllInfo(ctx, fileName, header):
    theList, lines = await GetPinedList(ctx,header)
    users = None
    line = None
    if theList:
        line = LookForLine(fileName, lines)
        if line:
            users = GetAllUsersFromList(line)
    return theList, lines, line, users



#if any(line for line in theList.content.splitlines()[1:] if fileName in re.findall("(\w*) :","hhhh : pedro pableras hola")):
#        re.findall("(\w*) :","hhhh : pedro pableras hola")
@bot.command(name='notify',help='Use !notify [fileName]\nWhen the file is released, the users in the list will be notified ')
async def AddNotifyUser(ctx, fileName:str):
    #Abortar si esta el caracter de control en el nombre del fichero
    if CONTROL_CHARACTER in fileName:
        await ctx.send(f":no_entry: Invalid character => : Please remove it :no_entry:")
        return
    fileName = fileName.upper()

    theList, lines, line, users = await GetAllInfo(ctx, fileName, NOTIFY_HEADER)

    #existe la lista pineada
    if theList:
        if line:
            #If user not in list add
            if (not str(ctx.author.id) in users):
                #if (not a in users):
                lines.remove(line)
                line += f" {ctx.author.id}"
                #line += f" {a}"
                lines.append(line)
                await theList.edit(content=''.join(lines))
        else:
            lines.append(AddListMessage(ctx.author.id, fileName))
            await theList.edit(content=''.join(lines))
        await ctx.send(f"You will be notified when the {fileName} file is released")
    else:
        listMsg = await ctx.send(f"{NOTIFY_HEADER}{AddListMessage(ctx.author.id,fileName)}")
        await listMsg.pin()
        await ctx.send(f"You will be notified when the {fileName} file is released")



@bot.command(name='checkout',help='Use !checkout [fileName]\nIf nobody has checked out the file, it is added to the list of checkout files')
async def checkout(ctx, fileName:str):
    #Abortar si esta el caracter de control en el nombre del fichero
    if CONTROL_CHARACTER in fileName:
        await ctx.send(f":no_entry: Invalid character => : Please remove it :no_entry:")
        return
    fileName = fileName.upper()

    theList, lines, line, users = await GetAllInfo(ctx, fileName, HEADER)

    if theList:
        if line and users and users[0] != str(ctx.author.id):
            await ctx.send(f":no_entry: You can't checkout {fileName} :no_entry:\nYou can be notified when the file is released by typing:\n!notify {fileName}")
        elif users and users[0] == str(ctx.author.id):
            await ctx.send(f"You already had checkout of the file {fileName} :white_check_mark:")
        else:
            content = theList.content + AddListMessage(ctx.author.id, fileName)
            await theList.edit(content=content)
            await ctx.send(f"Checkout of {fileName} done :white_check_mark:")
    else:
        #If no pinned message, create the list
        listMsg = await ctx.send(f"{HEADER}{AddListMessage(ctx.author.id, fileName)}")
        await listMsg.pin()
        await ctx.send(f"Checkout of {fileName} done :white_check_mark:")

@bot.command(name='release',help='Use !release [fileName]\nIf the user has the file in the checkout list, it is removed from the list ')
async def release(ctx, fileName:str):
    if CONTROL_CHARACTER in fileName:
        await ctx.send(f":no_entry: Invalid character => : Please remove it :no_entry:")
        return
    fileName = fileName.upper()

    theList, lines, line, users = await GetAllInfo(ctx, fileName, HEADER)
    if theList:
        #Hay una entrada
        if line:
            #No es el propietario
            if  users and not str(ctx.author.id) in users:
                await ctx.send(f":no_entry: You can't released {fileName}, owner: {users[0]} :no_entry:\nYou can be notified when the file is released by typing:\n!notify {fileName}")
            else:
                #Es el propietario
                lines.remove(line)
                await theList.edit(content=''.join(lines))
                await ctx.send(f"{fileName} released :white_check_mark:")

                theListNotify, linesNotify, lineNotify, usersNotify = await GetAllInfo(ctx, fileName, NOTIFY_HEADER) 
                if usersNotify:
                    msg = ""
                    for usr in usersNotify:
                        msg += "<@"+ usr + "> "
                        #user = await bot.fetch_user(usr)
                        #await user.message("prueba")
                        await ctx.send(f" :warning: {msg} {fileName} has been released :warning:")

                if lineNotify:
                    linesNotify.remove(lineNotify)
                    await theListNotify.edit(content=''.join(linesNotify))


        else:
            await ctx.send(f"{fileName} released :white_check_mark:")
    else:
        await ctx.send(f"{fileName} released :white_check_mark:")

@bot.command(name="list", help="Show the list of checkout files and the owners")
async def TheList(ctx):
    theList, lines =  await GetPinedList(ctx, HEADER)
    if theList:
        content = lines[0]
        for line in lines[1:]:
            fileName = re.findall("([\w*\s*]*) :",line)[0]
            content += "\n" + fileName + " by " 
            users = GetAllUsersFromList(line)
            member = await ctx.guild.fetch_member(users[0])
            content += " " + str(member.display_name)
        await ctx.send(content)
    else:
        await ctx.send(f"Empty")



@bot.event
async def on_command_error(ctx, error):
    await ctx.send(error)


bot.run(TOKEN)
