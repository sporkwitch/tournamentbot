import os
import sys
sys.path.append(os.path.join('gspread', 'gspread'))
sys.path.append(os.path.join('pychallonge', 'challonge'))
import time
import shlex
import shutil
import inspect
import discord
import asyncio
import traceback
import gspread
from gspread import exceptions
import challonge
import requests
import re
import json
import platform

from oauth2client.service_account import ServiceAccountCredentials

from discord import utils
from discord.object import Object
from discord.enums import ChannelType
from discord.voice_client import VoiceClient

import random
#from random import choice
import string
from functools import wraps
from textwrap import dedent
from datetime import datetime, timedelta

from autologin.config import Config, ConfigDefaults, ChallongeConfig
from autologin.permissions import Permissions, PermissionsDefaults
from autologin.utils import load_file, extract_user_id, write_file
#from Queue import Queue
#from threading import Thread

from .opus_loader import load_opus_lib
from .constants import DISCORD_MSG_CHAR_LIMIT
from .exceptions import CommandError, PermissionsError, HelpfulError

load_opus_lib()
start = time.time()

class Lmgtfy:
    def __init__(self):
        #nothing
        self.name = 'Lmgtfy'
    def lmgtfy_url(self, query):
        print('query in lmgtfy: ' + str(query))
        newQuery = query.replace(' ', "+")
        print('newQuery in lmgtfy: ' + str(newQuery))
        return 'http://lmgtfy.com/?q=' + str(''.join([word.replace(" ", "+") for word in query.strip()]))
        #return 'http://lmgtfy.com/?q=' + '+'.join([word.strip().replace(" ", "+") for word in query.strip()])

    def short_url(self, query):
        print('query in lmgtfy: ' + str(query))
        payload = {'format': 'json', 'url': self.lmgtfy_url(query)}
        r = requests.get('http://is.gd/create.php', params=payload)
        print('response shortlink: ' + str(r.json()['shorturl'])) 
        return r.json()['shorturl']
     
class Challonge:
    def __init__(self):
        self.username = None
        self.api_key = None
        self.login = False
        self.currenttournament = None
        self.tourneyLoaded = False
        self.tourneyLink = None
        self.channelLock = None
    def setUsername(self, _username):
        self.username = _username
    def getUsername(self):
        return self.username
    def setApiKey(self, _apiKey):
        self.api_key = _apiKey
    def getApiKey(self):
        return self.api_key
    def setChallonge(self, _username, _apiKey):
        self.username = _username
        self.api_key = _apiKey
    def setLogin(self, _login):
        self.login = _login
    def getLogin(self):
        return self.login
    def setCurrentTourney(self, _tourney):
        self.currenttournament = _tourney
    def getCurrentTourney(self):
        return self.currenttournament
    def setTourneyLoaded(self, _tourney):
        self.tourneyLoaded = _tourney
    def getTourneyLoaded(self):
        return self.tourneyLoaded
    def getTourneyLink(self):
        if self.currenttournament is None:
            return self.currenttournament
        return self.currenttournament['full-challonge-url']
    def getLiveImgUrl(self):
        if self.currenttournament is None:
            return self.currenttournament
        return self.currenttournament['live-image-url']
    def getTimeStartedAt(self):
        if self.currenttournament is None:
            return self.currenttournament
        return self.currenttournament['started-at']
    def getTourneyProgress(self):
        if self.currenttournament is None:
            return self.currenttournament
        return self.currenttournament['progress-meter']
    def getTourneyState(self):
        """
        Gets the current state of the running tourney

        States: underway, pending, in_progress, ended

        Returns: string
        """
        if self.currenttournament is None:
            return self.currenttournament
        return self.currenttournament['state']
    def getTourneyId(self):
        if self.currenttournament is None:
            return self.currenttournament
        return self.currenttournament['id']
    def getTourneyName(self):
        if self.currenttournament is None:
            return self.currenttournament
        return self.currenttournament['name']
    def getChallongeParticipantId(_name):
        tourneyPartId = self.getTourneyId()
        if tourneyPartId is None:
            return tourneyPartId
        participants = challonge.participants.index(tourneyPartId)
        requestedParticipant = ""
        for participant in participants:
            if (participant["name"] == str(_name)) and participant["tournament-id"] == tourneyPartId:
                requestedParticipant = participant["id"]
                break
        if str(requestedParticipant).isdigit():
           return requestedParticipant
        return "not found"
    def setChallongeLink(self, _tLink):
        self.tourneyLink = _tLink
    def getChallongeLink(self):
        return self.tourneyLink
    def setChannelLock(self, _tLock):
        self.channelLock = _tLock
    def getChannelLock(self):
        return self.channelLock
class PlatformSpecs:
    def __init__(self):
        self.platformObj = platform
        self.machine = platform.machine()
        self.version = platform.version()
        self.platform = platform.platform()
        self.uname = platform.uname()
        self.system = platform.system()
        self.processor = platform.processor()
    def getPlatObj(self):
        return self.platformObj
    def getMachine(self):
        return self.machine
    def getVersion(self):
        return self.version
    def getPlatform(self):
        return self.platform
    def getPlatUName(self):
        return self.uname
    def getSys(self):
        return self.system
    def getProcessor(self):
        return self.processor

class ExcelGSpread:
    def __init__(self):
        self.excelKey = None
        self.url = None
        self.ws = None
        self.gc = None
        self.gss_client = None
        self.excelfile = None
        self.scope = ['https://spreadsheets.google.com/feeds']
        self.keyType = None
        self.email = None
        self.gspreadCred = None
    def setExcelKey(self, _key):
        self.excelKey = _key
    def getExcelKey(self):
        return self.excelKey
    def setURL(self, _url):
        self.url = _url
    def getURL(self):
        return self.url
    def setWS(self, _ws):
        self.ws = _ws
    def getWS(self):
        return self.ws
    def setGC(self, _gc):
        self.gc = _gc
    def getGC(self):
        return self.gc
    def setGSS(self, _gss):
        self.gss_client = _gss
    def getGSS(self):
        return self.gss_client
    def setExcelFile(self, _excelFile):
        self.excelfile = _excelFile
    def getExcelFile(self):
        return self.excelfile
    def setScope(self, _scope):
        self.scope = _scope
    def getScope(self):
        return self.scope
    def setExcelKeyType(self, _type):
        self.keyType = _type
    def getExcelKeyType(self):
        return self.keyType
    def setEmail(self, _email):
        self.email = _email
    def getEmail(self):
        return self.email
    def setCred(self, _cred):
        self.gspreadCred = _cred
    def getCred(self):
        return self.gspreadCred
    def checkExpired(self):
        if self.getCred().access_token_expired:
            self.getGSS().login()
            return True
        return True
    def setCredentials(self):
        excelFile = self.excelfile
        if excelFile.find('.json') != -1:
            gspreadCredentials = ServiceAccountCredentials.from_json_keyfile_name(excelFile, self.getScope())
            self.setCred(gspreadCredentials)
            gss_client = gspread.authorize(gspreadCredentials)
            if gspreadCredentials.access_token_expired:
                gss_client.login()
            self.setGSS(gss_client)
    def getSpecificCellVal(self, specificContent, wks):
        cellContent = ""
        try:
            specific_Cell = wks.find(specificContent)
            specific_Row = specific_Cell.row
            specific_Col = specific_Cell.col
            nextColOver = wks.cell(specific_Row, specific_Col + 1)
            cellContent = nextColOver.value
        except gspread.exceptions.CellNotFound:
            return "No Information available"
        return cellContent
    def checkDuplicateNames(self, member, wks, _caseSense):
        pattern = re.compile('(\W|^)' + re.escape(str(member.name)) + '(\W|$)',
                             re.IGNORECASE)
        try:
            user_Cell_list = ''
            if _caseSense:
                user_Cell_list = wks.findall(pattern)
            else:
                user_Cell_list = wks.findall(str(member.name))
            if len(user_Cell_list) > 1:
                return True #should be True when duplicate is found
        except gspread.exceptions.CellNotFound:
            return False
        return False #should be False when no duplicate is found
    def checkUserCheckedInSpreadSheet(self, member, wks, _caseSense):
        pattern = re.compile('(\W|^)' + re.escape(str(member.id)) + '(\W|$)',
                             re.IGNORECASE)
        try:
            #if _caseSense:
            #    user_Cell = wks.find(pattern)
            #else:
            #    user_Cell = wks.find(str(member.id))
            if wks.find(pattern):
                return True
        except gspread.exceptions.CellNotFound:
            return False
    def checkUserExistInSpreadSheet(self, member, wks, _caseSense):
        pattern = re.compile('(\W|^)' + re.escape(member.name) + '(\W|$)',
                             re.IGNORECASE)
        try:
            if _caseSense:
                user_Cell = wks.find(pattern)
            else:
                user_Cell = wks.find(str(member.name))
            user_Row = user_Cell.row
            user_Col = user_Cell.col
            wks.update_cell(user_Row, user_Col + 1, member.id)
        except gspread.exceptions.CellNotFound:
            return False
        return True
    def checkDuplicateTeamNames(self, _teamName, wks, _caseSense):
        pattern = re.compile('(\W|^)' + re.escape(str(_teamName)) + '(\W|$)',
                             re.IGNORECASE)
        try:
            if _caseSense:
                user_Cell_list = wks.findall(pattern)
            else:
                user_Cell_list = wks.findall(str(_teamName))
            if len(user_Cell_list) > 1:
                return 'Error: Duplicate name entry'
        except gspread.exceptions.CellNotFound:
            return False
        return True
    def checkTeamExistInSpreadSheet(self, _teamName, wks, _caseSense, _tourneyType):
        pattern = re.compile('(\W|^)' + re.escape(str(_teamName)) + '(\W|$)',
                             re.IGNORECASE)
        try:
            user_Cell = ''
            if _caseSense:
                user_Cell = wks.find(pattern)
            else:
                user_Cell = wks.find(_teamName)
            if user_Cell != -1:
                user_Row = user_Cell.row
                user_Col = user_Cell.col
                user_Cell_Array = []
                if _tourneyType == '1v1':
                    cCol = wks.cell(user_Row, user_Col + 1)
                    user_Cell_Array.append(cCol.value)
                elif _tourneyType == '2v2':
                    cCol = wks.cell(user_Row, user_Col - 3)
                    user_Cell_Array.append(cCol.value)
                    eCol = wks.cell(user_Row, user_Col - 1)
                    user_Cell_Array.append(eCol.value)
                elif _tourneyType == '3v3':
                    cCol = wks.cell(user_Row, user_Col - 5)
                    user_Cell_Array.append(cCol.value)
                    eCol = wks.cell(user_Row, user_Col - 3)
                    user_Cell_Array.append(eCol.value)
                    gCol = wks.cell(user_Row, user_Col - 1)
                    user_Cell_Array.append(gCol.value)
                return user_Cell_Array
        except gspread.exceptions.CellNotFound:
            return False
        return False

class Response(object):
    def __init__(self, content, reply=False, delete_after=0):
        self.content = content
        self.reply = reply
        self.delete_after = delete_after
        #self.delete_after = 0 #default set

class AutoLoginBot(discord.Client):
    def __init__(self, config_file=ConfigDefaults.options_file, perms_file=PermissionsDefaults.perms_file, excel_file=ConfigDefaults.excel_file, challonge_file=ConfigDefaults.challonge_file, saying_file=ConfigDefaults.saying_file):
        super().__init__()
        self.uptime = datetime.utcnow()
        self.voice_clients = {}
        self.voice_client_connect_lock = asyncio.Lock()
        self.config = Config(config_file)
        self.challongeconfig = ChallongeConfig(challonge_file)
        self.excel_file = excel_file
        self.permissions = Permissions(perms_file)
        self.challonge = Challonge()
        self.excelSpread = ExcelGSpread()
        self.excelSpread.setExcelFile(self.excel_file)
        self.excelSpread.setCredentials()
        self.excelSpread.setEmail(self.config.excel_email)
        self.lock_checkin = False
        self.lmgtfy = Lmgtfy()
        self.platform = PlatformSpecs()
        self.blacklist = set(map(int, load_file(self.config.blacklist_file)))
        self.whitelist = set(map(int, load_file(self.config.whitelist_file)))
        self.checkinActive = False #bool to handle checkin loop        

    # noinspection PyMethodOverriding
    def run(self):
        return super().run(self.config.username, self.config.password)
    
    async def on_ready(self):
        print('---------------------------------------')
        print('Connected!\n')

        self.safe_print("Bot:   %s/%s" % (self.user.id, self.user.name))

        owner = self._get_owner(voice=True) or self._get_owner()
        if owner:
            self.safe_print("Owner: %s/%s" % (owner.id, owner.name))
        else:
            print("Owner could not be found on any server (id: %s)" % self.config.owner_id)

        if self.config.owner_id == self.user.id:
            print("\n"
                  "[NOTICE] You have either set the OwnerID config option to the bot's id instead "
                  "of yours, or you've used your own credentials to log the bot in instead of the "
                  "bot's account (the bot needs its own account to work properly).")
        print()

        if self.servers:
            print('Server List:')
            [self.safe_print(' - ' + s.name + ' - ' + str(s.id)) for s in self.servers]
        else:
            print("No servers have been joined yet.")

        print()

        if self.config.bound_channels:
            print("Bound to channels:")
            chlist = [self.get_channel(i) for i in self.config.bound_channels if i]
            [self.safe_print(' - %s/%s' % (ch.server.name.rstrip(), ch.name.lstrip())) for ch in chlist if ch]
        else:
            print("Not bound to any channels")

        print()

        self.safe_print("Command prefix is %s" % self.config.command_prefix)
        print("Whitelist check is %s" % ['disabled', 'enabled'][self.config.white_list_check])
        print()

        status_text = discord.Game(name='by acksoftware.com')
        await self.change_status(status_text)
        print()
        
    def owner_only(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Only allow the owner to use these commands
            orig_msg = self._get_variable('message')

            if not orig_msg or orig_msg.author.id == self.config.owner_id:
                return await func(self, *args, **kwargs)
            else:
                raise PermissionsError("only the owner can use this command")

        return wrapper
    
    def _get_variable(self, name):
        stack = inspect.stack()
        try:
            for frames in stack:
                current_locals = frames[0].f_locals
                if name in current_locals:
                    return current_locals[name]
        finally:
            del stack
    
    def _get_owner(self, voice=False):
        if voice:
            for server in self.servers:
                for channel in server.channels:
                    for m in channel.voice_members:
                        if m.id == self.config.owner_id:
                            return m
        else:
            return discord.utils.find(lambda m: m.id == self.config.owner_id, self.get_all_members())
    
    def _fixg(self, x, dp=2):
        return ('{:.%sf}' % dp).format(x).rstrip('0').rstrip('.')

    async def _wait_delete_msg(self, message, after):
        await asyncio.sleep(after)
        await self.safe_delete_message(message)
        
    async def safe_send_message(self, dest, content, *, tts=False, expire_in=0, also_delete=None, quiet=False):
        msg = None
        try:
            msg = await self.send_message(dest, content, tts=tts)

            if msg and expire_in:
                asyncio.ensure_future(self._wait_delete_msg(msg, expire_in))

            if also_delete and isinstance(also_delete, discord.Message):
                asyncio.ensure_future(self._wait_delete_msg(also_delete, expire_in))

        except discord.Forbidden:
            if not quiet:
                self.safe_print("Warning: Cannot send message to %s, no permission" % dest.name)
        except discord.NotFound:
            if not quiet:
                self.safe_print("Warning: Cannot send message to %s, invalid channel?" % dest.name)
        return msg
    
    async def safe_delete_message(self, message, *, quiet=False):
        try:
            return await self.delete_message(message)

        except discord.Forbidden:
            if not quiet:
                self.safe_print("Warning: Cannot delete message \"%s\", no permission" % message.clean_content)
        except discord.NotFound:
            if not quiet:
                self.safe_print("Warning: Cannot delete message \"%s\", message not found" % message.clean_content)

    async def safe_edit_message(self, message, new, *, send_if_fail=False, quiet=False):
        try:
            return await self.edit_message(message, new)

        except discord.NotFound:
            if not quiet:
                self.safe_print("Warning: Cannot edit message \"%s\", message not found" % message.clean_content)
            if send_if_fail:
                if not quiet:
                    print("Sending instead")
                return await self.safe_send_message(message.channel, new)

    def safe_print(self, content, *, end='\n', flush=True):
        sys.stdout.buffer.write((content + end).encode('utf-8', 'replace'))
        if flush: sys.stdout.flush()

    async def cmd_help(self, message):
        """
        Usage: {command_prefix}help
        Prints a help message
        """
        helpmsg = "**Commands**\n```"
        commands = []
        
        user_permissions = self.permissions.for_user(message.author)
        for att in dir(self):
            if att.startswith('cmd_') and att != 'cmd_help':
                command_name = att.replace('cmd_', '')
                if command_name in user_permissions.command_whitelist:
                    commands.append("{}{}".format(self.config.command_prefix, command_name))
        helpmsg += ' '.join(commands)
        helpmsg += "```"
        return Response(helpmsg, reply=True)

    async def cmd_timer(self, message, minutes, description=None):
        """
        Waits [minutes] and sends [description] as a PM to the caller.
        """
        if minutes.isdigit():
            minutes = int(minutes)
        if not isinstance(minutes, int) or not (minutes > 0 and minutes < 31):
            return await self.postLink(message,'The time must be an integer between 1 and 30, '
                            + 'inclusive')
        await self.safe_send_message(message.channel, str(minutes) + ' minute timer has been '
                                     + 'set')
        await asyncio.sleep(60*minutes)
        if description is None:
            return await self.postLink(message, str(minutes) + ' minute timer has '
                                         + 'expired')
        else:
            return await self.postLink(message, str(description))
            
    async def cmd_info(self, message):
        '''
        Usage: {command_prefix}info
        Provides information in regards to the ownership of the bot
        '''
        return Response('Protocol Bot is a product of ACK Software. '
                        'https://acksoftware.com/', reply=True)

    async def cmd_ban(self, message, username):
        """
        Usage: {command_prefix}ban @Username
        Command to ban the user for x number of days if user has permissions to authorize
        """
        user_id = extract_user_id(username)
        member = discord.utils.find(lambda mem: mem.id == str(user_id), message.channel.server.members)
        try:
            await self.ban(member, delete_message_days=7)
        except discord.Forbidden:
            return Response("You do not have the proper permissions to ban.", reply=True)
        except discord.HTTPException:
            return Response("Banning failed due to HTTPException error.", reply=True)
    
    async def cmd_unban(self, message, username):
        """
        Usage: {command_prefix}unban @Username
        Command to unban the user for 7 days if the bot has permissions to authorize
        """
        user_id = extract_user_id(username)
        member = discord.utils.find(lambda mem: mem.id == str(user_id), message.channel.server.members)
        try:
            await self.unban(member, delete_message_days=7)
        except discord.Forbidden:
            return Response("You do not have the proper permissions to unban.", reply=True)
        except discord.HTTPException:
            return Response("Unbanning failed due to HTTPException error.", reply=True)
    
    async def cmd_kick(self, message, username):
        """
        Usage: {command_prefix}kick @Username
        Command to kick the person from the server if the bot has permissions to authorize that kick
        """
        user_id = extract_user_id(username)
        member = discord.utils.find(lambda mem: mem.id == str(user_id), message.channel.server.members)
        try:
            await self.kick(member)
        except discord.Forbidden:
            return Response("You do not have the proper permissions to kick.", reply=True)
        except discord.HTTPException:
            return Response("Kicking failed due to HTTPException error.", reply=True)
        
    def _get_uptime(self):
        """
        Usage: {command_prefix}uptime
        Displays how long the bot has been up for
        """
        stop = datetime.utcnow()
        delta = stop - self.uptime
        hours, remainder = divmod(int(delta.total_seconds()),3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        if days:
            time_parse = '{d} days, {h} hours, {m} minutes, and {s} seconds'
        else:
            time_parse = '{h} hours, {m} minutes, and {s} seconds'
        return time_parse.format(d=days, h=hours, m=minutes, s=seconds)
    
    async def cmd_uptime(self, message):
        """
        Usage: {command_prefix}uptime
        Displays how long the bot has been up for
        """
        msgUptime = 'Uptime: **{}**'.format(self._get_uptime())
        await self.safe_send_message(message.channel, msgUptime)
    
    async def cmd_nudes(self, message):
        """
        Usage: {command_prefix}nudes
        Updates the counter by 1 for the number of times this command was called
        """
        self.config.funny.nudes = int(self.config.funny.nudes) + 1
        return Response('The number of times that this was requested is now: ' + str(self.config.funny.nudes), reply=True)
    
    async def cmd_updatefunny(self, message):
        if message.content.find('funny') != -1:
            self.config.funny.writeFunnyConfigLst()
            return Response('Funny count updated', reply=True)
        else:
            return Response('Sorry, that command does not exist', reply=True)
    
    async def cmd_compspecs(self, message):
        """
        Usage: {command_prefix}compspecs
        Displays the computer specs currently running this bot
        """
        platform = 'Platform: ' + str(self.platform.getPlatform())
        platformVersion = 'Version: ' + str(self.platform.getVersion())
        platformMachine = 'Machine: ' + str(self.platform.getMachine())
        platformUName = 'Specs: ' + str(self.platform.getPlatUName())
        platformSys = 'Sys: ' + str(self.platform.getSys())
        platformProcessor = 'Processor: ' + str(self.platform.getProcessor())
        compSpecs = '**PC Specs**:' 
        compSpecs += '\n\t' + platform
        compSpecs += '\n\t' + platformVersion
        compSpecs += '\n\t' + platformMachine
        compSpecs += '\n\t' + platformUName
        compSpecs += '\n\t' + platformSys
        compSpecs += '\n\t' + platformProcessor
        return Response(compSpecs, reply=True)

    async def cmd_say(self, message):
        """
        Usage: {command_prefix}say
        Echos what the user says back
        """
        content2 = message.content[len(self.config.command_prefix + 'say'):].strip()
        if content2.rfind(self.config.command_prefix) != -1:
            content = 'this is a warning; nested code execution prevented'
            content = '%s, %s' % (message.author.mention, content)
            await self.safe_send_message(message.channel, content)
        elif len(content2) >= 1:
            content = content2
            content = '%s, %s' % (message.author.mention, content)
            await self.safe_send_message(message.channel, content)

    async def cmd_whitelist(self, message, option, username):
        """
        Usage: {command_prefix}whitelist <+ | - | add | remove> @UserName
        Adds or removes the user to the whitelist. When the whitelist is enabled,
        whitelisted users are permitted to use bot commands.
        """
        user_id = extract_user_id(username)
        if not user_id:
            raise CommandError('Invalid user specified')
            
        if option not in ['+', '-', 'add', 'remove']:
            raise CommandError('Invalid option "%s" specified, use +, -, add, or remove' % option)

        if option in ['+', 'add']:
            self.whitelist.add(user_id)
            write_file('./config/whitelist.txt', self.whitelist)
            
            return Response('user has been added to the whitelist', reply=True)
        else:
            if option in ['-', 'remove']:
                if user_id not in self.whitelist:
                    return Response('user is not in the whitelist', reply=True)
                else:
                    self.whitelist.remove(user_id)
                    write_file('./config/whitelist.txt', self.whitelist)

                    return Response('user has been removed from the whitelist', reply=True)

    async def cmd_blacklist(self, message, option, username):
        """
        Usage: {command_prefix}blacklist <+ | - | add | remove> @UserName
        Adds or removes the user to the blacklist. Blacklisted users are forbidden from
        using bot commands. Blacklisting a user also removes them from the whitelist.
        """
        user_id = extract_user_id(username)
        if not user_id:
            raise CommandError('Invalid user specified')

        if str(user_id) == self.config.owner_id:
            return Response("The owner cannot be blacklisted.")

        if option not in ['+', '-', 'add', 'remove']:
            raise CommandError('Invalid option "%s" specified, use +, -, add, or remove' % option)

        if option in ['+', 'add']:
            self.blacklist.add(user_id)
            write_file('./config/blacklist.txt', self.blacklist)

            if user_id in self.whitelist:
                self.whitelist.remove(user_id)
                write_file('./config/whitelist.txt', self.whitelist)
                return Response('user has been added to the blacklist and removed from the whitelist', reply=True)

            else:
                return Response('user has been added to the blacklist', reply=True)

        else:
            if user_id not in self.blacklist:
                return Response('user is not in the blacklist', reply=True)

            else:
                self.blacklist.remove(user_id)
                write_file('./config/blacklist.txt', self.blacklist)

                return Response('user has been removed from the blacklist', reply=True)
    
    async def postLink(self, message, linkMessage, username=None):
        """
        Posts a message to the caller or the user specified
        """
        self.safe_print(linkMessage)
        if username is not None:
            user_id = extract_user_id(username)
            if not user_id:
                return Response(linkMessage, reply=True)
            linkMessage = str(username) + ', ' + linkMessage
            await self.safe_send_message(message.channel, linkMessage)
            return True
        return Response(linkMessage, reply=True)
    
    async def cmd_website(self, message,username=None):
        """
        Usage: {command_prefix}website
        It will tell you the website about an organization
        """
        linkMessage = 'the website is: ' + str(self.config.organization.website)
        return await self.postLink(message, linkMessage, username)
    
    async def cmd_guidelines(self, message, username=None):
        """
        Usage: {command_prefix}guidelines
        It will tell you the checkin guidelines about an organization
        """
        linkMessage = 'the check-in guidelines can be found at: ' + str(self.config.organization.checkin_guidelines)
        return await self.postLink(message, linkMessage, username)
    
    async def cmd_rules(self, message,username=None):
        """
        Usage: {command_prefix}rules
        It will tell you the rules about an organization
        """
        # below linkMessage should be in the configuration file -- EAA
        #
        #### As part of localization, all text messages should be stored externally,
        #### but that can come later -- RFK
        linkMessage = (str(self.config.organization.rules) + 'Discord Rules:\n'
                       '```'
                       '1) Use correct channels specific to your needs.\n'
                       '2) Spamming, name calling, racism, harassing or threatening\n'
                       '   other people will not be tolerated.\n'
                       '3) Be respectful to Admins/Mods and abide their decisions.\n'
                       '4) Do not post links to malicious or NSFW content.\n'
                       '5) Impersonating other people or an Admin/Moderator is not\n'
                       '   allowed.\n'
                       '6) Admins and Moderators reserve the right to kick or ban\n'
                       '   a person if they feel it is necessary.\n'
                       '7) Self promotion requires a Moderator\'s approval.'
                       '```')
        return await self.postLink(message, linkMessage, username)
    
    async def cmd_faq(self, message, username=None):
        """
        Usage: {command_prefix}faq
        It will tell you the faq about an organization
        """
        linkMessage = 'the FAQ is located at: ' + str(self.config.organization.faq)
        return await self.postLink(message, linkMessage, username)
    
    async def cmd_name(self, message, username=None):
        """
        Usage: {command_prefix}name
        It will tell you the name about an organization
        """
        linkMessage = 'the name of the organization is: ' + str(self.config.organization.name)
        return await self.postLink(message, linkMessage, username)

    async def cmd_watch(self, message, streamType, username=None):
        """
        Usage: {command_prefix}twitch
        It will tell you the twitch link of an organization
        """
        if (streamType.lower() == 'twitch' or
            streamType.lower() == 'twitch.tv'):
            linkMessage = ('the twitch stream is located at: ' +
                           str(self.config.organization.twitch))
        elif (streamType.lower() == 'streamme' or
              streamType.lower() == 'stream.me'):
            linkMessage = ('the stream.me stream is located at: ' +
                           str(self.config.organization.streamme))
        else:
            linkMessage = 'The streamtype must be Twitch or Stream.me'

        return await self.postLink(message, linkMessage, username)
        
    async def cmd_loadtourney(self, message, excelKey, challongeKey):
        """
        Usage: {command_prefix}loadTourney <excelKey> <challongeKey> @UserName
        Loads and logins to both excel and challonge
        """
        self.challonge.setChannelLock(None)

        if not await self.cmd_load(message, 'excel', excelKey):
            #send message "bad excel sheet"
            return False
        if not await self.cmd_login(message, 'excel'):
            #send message "bad excel username"
            return False
        if not await self.cmd_login(message, 'challonge'):
            #send message "bad challonge login"
            return False
        if not await self.cmd_load(message, 'challonge', challongeKey):
            #send message "bad challonge key"
            return False
        else:
            #send message "The tournament is ready"
            await self.safe_send_message(message.channel, 'The tournament is ready')
            return True

    async def cmd_login(self, message, option):
        """
        Usage: {command_prefix}login <excel | challonge> @UserName
        Logins to either the excel api or the challonge api
        """
        user_id = None
                
        if option in ['excel', 'challonge']:
            if option == 'excel':
                if self.excelSpread.getExcelKey() is None:
                    await self.send_message(message.channel, 
                                            'The Excel Spreadsheet key was not '
                                            'set correctly.')
                    return False                    
                else:
                    if self.excelSpread.getExcelKeyType() == 'key':
                        self.excelSpread.checkExpired()
                        gss_client = self.excelSpread.getGSS()
                        if gss_client is None:
                            self.excelSpread.setCredentials()
                            gss_client = self.excelSpread.getGSS()
                        gc = gss_client.open_by_key(self.excelSpread.getExcelKey())
                        wks = gc.sheet1
                        self.excelSpread.setGC(gc)
                        self.excelSpread.setWS(wks)
                    elif self.excelSpread.getExcelKeyType() == 'link':
                        self.excelSpread.checkExpired()
                        gss_client = self.excelSpread.getGSS()
                        if gss_client is None:
                            self.excelSpread.setCredentials()
                            gss_client = self.excelSpread.getGSS()
                        gc = gss_client.open_by_url(self.excelSpread.getExcelKey())
                        self.excelSpread.setGC(gc)
                        self.excelSpread.setWS(wks)
            elif option == 'challonge':
                print('userID: ' + str(user_id))
                challongeContainer = self.challongeconfig.for_user(user_id)
                #default is mockit bot credentials
                username = challongeContainer.username
                user_api_key = challongeContainer.Api_Key
                self.challonge.setChallonge(username, user_api_key)
                challonge.set_credentials(self.challonge.getUsername(), self.challonge.getApiKey())
                self.challonge.setLogin(True)
                await self.send_message(message.channel, ('Credentials have '
                                        'been loaded'))
                return True
            await self.send_message(message.channel, 'Successfully logged into ' + str(option))
            return True
        else:
            await self.send_message(message.channel, 'That is not a valid command')
            return False
    
    async def cmd_load(self, message, option, keyType):
        """
        Usage: {command_prefix}load <excel | challonge> <url_link | key | number>
        Loads either the excel or challonge file based on url_link, key, or number with the credentials from the login command
        """
        if option in ['excel', 'challonge']:
            if option == 'excel':
                if keyType.startswith('https://docs.google.com/spreadsheets/d/'):
                    self.excelSpread.setExcelKey(keyType)
                    self.excelSpread.setExcelKeyType('link')
                else:
                    self.excelSpread.setExcelKey(keyType)
                    self.excelSpread.setExcelKeyType('key')
                #now we need to reload the credentials with the spreadsheet
                self.excelSpread.checkExpired()
                gss_client = self.excelSpread.getGSS()
                try:
                    gc = gss_client.open_by_key(self.excelSpread.getExcelKey())
                except gspread.exceptions.SpreadsheetNotFound:
                    await self.safe_send_message(message.channel,
                                                 'Spreadsheet not found')
                    self.excelSpread.setExcelKey(None)
                    self.excelSpread.setExcelKeyType(None)
                    return False
                wks = gc.sheet1
                self.excelSpread.setGC(gc)
                self.excelSpread.setWS(wks)
                await self.safe_send_message(message.channel, ('The spreadsheet '
                                                          'was set by ' +
                                                          str(self.excelSpread.getExcelKeyType())))
                return True
            elif option == 'challonge':
                print('keyType: ' + str(keyType))
                if self.challonge.getLogin():
                    if (keyType.startswith('http://') and keyType.find('challonge.com') != -1) or keyType.isdigit():
                        #load in by url or by digit only
                        if not keyType.isdigit():
                            tournament_no_http = keyType[len('http://'):]
                            tourneySubInt = tournament_no_http.find('.')
                            tournamentSubDomain = tournament_no_http[:tourneySubInt]
                            tournamentEndUrl = tournament_no_http[len(tournamentSubDomain + '.challonge.com/'):]
                            self.safe_print("tournament_no_http: " + str(tournament_no_http) + "\ntournamentSubDomain: " + str(tournamentSubDomain) + "\ntournamentEndUrl: " + tournamentEndUrl)
                            tournament_url = tournamentSubDomain + '-' + tournamentEndUrl
                            self.safe_print("tournament_url: " + tournament_url)
                            if keyType.find('.challonge.com') == -1:
                                await self.safe_send_message(message.channel, 'Link format incorrect, please use "subdomain.challonge.com/mytourney"')
                                return False
                            else:
                                tempTourney = challonge.tournaments.show(tournament_url)
                                self.challonge.setCurrentTourney(tempTourney)
                                self.challonge.setTourneyLoaded(True)
                                await self.safe_send_message(message.channel, 'your tournament has been loaded')
                                self.challonge.setChallongeLink(keyType)
                                return True
                        else:
                            tempTourney = challonge.tournaments.show(keyType)
                            self.challonge.setCurrentTourney(tempTourney)
                            self.challonge.setTourneyLoaded(True)
                            self.challonge.setChallongeLink(keyType)
                            await self.safe_send_message(message.channel, 'your tournament has been loaded')
                            return True
                        self.safe_print('logged in. Permission to load tournament')
                else:
                    await self.safe_send_message(message.channel, 'Credentials have not been loaded yet.  Please use the login command first.')
                    return False
        else:
            await self.safe_send_message(message.channel, ('That is not a valid command'))
            return False
    
    async def cmd_unlockchannel(self, message, option):
        """
        Usage: {command_prefix}unlockchannel <channel Name>
        This will unlock the channel name that the bot is requesting to unlock based on permissions it has
        """
        if option is not None:
            responseWKS = ''
            if not self.excelSpread.getWS():
                self.excelSpread.setCredentials()
                gss_client = self.excelSpread.getGSS()
                if not self.excelSpread.getExcelKey():
                    return Response('The key has not been set by an admin.', reply=True)
                gc = gss_client.open_by_key(self.excelSpread.getExcelKey())
                wks = gc.sheet1
                self.excelSpread.setGC(gc)
                self.excelSpread.setWS(wks)
            responseWKS = self.excelSpread.getWS()
            if self.challonge.getLogin():
                #not False, allowed to enter in Tourney Check-In for everyone
                deny_cmd = discord.Permissions.none()
                deny_cmd.speak = True
                deny_cmd.use_voice_activation = True
                allow_cmd = discord.Permissions.none()
                allow_cmd.create_instant_invite = True
                allow_cmd.connect = True
                Channel_Name = 'Tourney Check-In' if option != '' else 'Tourney Check-In'
                Channel_Id = self.config.tourneychannel
                channel = [channel for channel in message.channel.server.channels if channel.type == discord.ChannelType.voice and str(Channel_Id) == str(channel.id)]
                if len(channel) == 0:
                    await self.safe_send_message(mesage.channel, 'The channel, ' + Channel_Name + ', does not exist or was typed incorrectly.')
                else:
                    channel = channel[0]
                    target = message.channel.server.default_role
                    self.safe_print("channel: " + str(channel.id) + "\ntarget: " + str(target))
                    await self.edit_channel_permissions(channel, target, allow=allow_cmd, deny=deny_cmd)
                    self.challonge.setChannelLock(False)
                    
                    tourney_setup_channel = [channel for channel in
                                             message.channel.server.channels if
                                             str(122608820919861248) == str(channel.id)]
                   
                    if len(tourney_setup_channel) == 0:
                        await self.safe_send_message(message.channel, ('The channel, ' +
                                        str(122608820919861248) + ', does '
                                        'not exist or was typed incorrectly. '
                                        'Unable to send message to everyone.'))
                    else:
                        tourney_setup_channel = tourney_setup_channel[0]
                        await self.safe_send_message(tourney_setup_channel,
                                    (str(target)) + (', __Check in has officially '
                                     'begun.__ Please proceed to the ' +
                                     str(Channel_Name) + ' to be processed by '
                                     'the bot.'))

            else:
                return Response('The tournament is not open yet.', reply=True)
   
    def _check_challonge_perms(self, requestStr):
        """
        Function that returns True if allowed to post what is being requested
        Function that returns False if not allowed to post what is being
        requested
        """
        if self.challonge.getChallongeLink() is None:
            return (False, 'The challonge link was not set.')
        else:
            if self.challonge.getChannelLock(): 
                return (True, requestStr)
            else:
                contentResp = ''
                p1 = False
                if not self.challonge.getChannelLock() or self.challonge.getChallongeLock() is None:
                    contentResp += ('Check-in is not complete')
                return (False,contentResp)

    async def cmd_bracket(self, message):
        """
        Usage: {command_prefix}bracket
        This returns the challonge bracket that is set
        """
        responseCheck = self._check_challonge_perms(('Bracket link: ' + str(self.challonge.getChallongeLink())))
        if bool(responseCheck[0]):
            return Response(str(responseCheck[1]), reply=True)
        else:
            return Response(str(responseCheck[1]), reply=True)
        '''
        if self.challonge.getChallongeLink() is None:
            return Response('The challonge link was not set.', reply=True)
        else:
            if self.challonge.getChannelLock() and self.challonge.getChannelLock() is not None:
                await self.safe_send_message(message.channel, 'Bracket link: ' + str(self.challonge.getChallongeLink()))
                return True
            else:
                contentResp = ''
                p1 = False
                if not self.challonge.getChannelLock() or self.challonge.getChallongeLock() is None:
                    contentResp += ('The channel has not been locked yet or has '
                                   'not finished being checked-in.')
                    p1 = True
                if not self.challonge.getChallongeLink() or self.challonge.getChallongeLink() is None:
                    if p1:
                        contentResp += '\n'
                    contentResp += ('The challonge link was not set.')
                await self.safe_send_message(message.channel, contentResp)
                return False
        '''
    async def cmd_lockchannel(self, message, option):
        """
        Usage: {command_prefix}lockChannel <channel Name>
        This will lock the channel name that the bot is requesting to lock based on permissions it has
        """
        if option is not None:
            responseWKS = ''
            if not self.excelSpread.getWS():
                self.excelSpread.setCredentials()
                gss_client = self.excelSpread.getGSS()
                if not self.excelSpread.getExcelKey():
                    return Response('The key has not been set by an admin.', reply=True)
                gc = gss_client.open_by_key(self.excelSpread.getExcelKey())
                wks = gc.sheet1
                self.excelSpread.setGC(gc)
                self.excelSpread.setWS(wks)
            responseWKS = self.excelSpread.getWS()
            if self.challonge.getLogin():
                allow_cmd = discord.Permissions.none()
                allow_cmd.create_instant_invite = True
                deny_cmd = discord.Permissions.none()
                deny_cmd.speak = True
                deny_cmd.use_voice_activation = True
                deny_cmd.connect = True
                Channel_Name = 'Tourney Check-In' if option != '' else 'Tourney Check-In'
                Channel_Id = self.config.tourneychannel
                channel = [channel for channel in message.channel.server.channels if channel.type == discord.ChannelType.voice and str(Channel_Id) == str(channel.id)]
                if len(channel) == 0:
                    await self.safe_send_message(mesage.channel, 'The channel, ' + Channel_Name + ', does not exist or was typed incorrectly.')
                else:
                    channel = channel[0]
                    target = message.channel.server.default_role
                    self.safe_print("channel: " + str(channel.id) + "\ntarget: " + str(target))
                    await self.edit_channel_permissions(channel, target, allow=allow_cmd, deny=deny_cmd)
                    self.challonge.setChannelLock(True)
                    tourney_setup_channel_id = 122608820919861248
                    tourney_setup_channel = [channel for channel in
                               message.channel.server.channels if
                               str(tourney_setup_channel_id) == str(channel.id)]
                    if len(tourney_setup_channel) == 0:
                        await self.safe_send_message(mesage.channel, ('The channel, ' + 
                                        str(tourney_setup_channel_id) + 
                                        ', does not exist or was typed incorrectly.'))
                    else:
                        tourney_setup_channel = tourney_setup_channel[0]
                        await self.safe_send_message(tourney_setup_channel,
                                        (str(target)) + (', __Check in has officially '
                                         'closed.__ Please stay in the ' +
                                         str(Channel_Name) + ' to be verified by '
                                         'one of the managers and/or moderators.'))
            else:
                return Response('The tournament is not open yet.', reply=True)                
        else:
            return Response('Cannot send any messages since it does not have a specific channel', reply=True)

    async def cmd_getcasters(self, message):
        """
        Usage: {command_prefix}getcasters
        Function that gets the list of casters
        """
        return Response('Casters: ' + str(self.config.casters), reply=True)

    async def cmd_holdmatch(self, message, number):
        """
        Usage: {command_prefix}holdmatch <number>
        Function that PM's the members asking them to hold their match
        """
        await self.cmd_stream(message, number, hold=True)

    async def cmd_unholdmatch(self, message, number):
        """
        Usage: {command_prefix}unholdmatch <number>
        Function that PM's the members asking them to play their match
            normally, if told to hold previously.

        Does not check if they were previously held, simply sends the message to
        play their game normally.
        """
        await self.cmd_stream(message, number, unhold=True)

    async def cmd_stream(self, message, number, hold=False, unhold=False):
        """
        Usage: {command_prefix}stream <number>
        Calls the streaming command for the tournament
        """
        if number.isdigit():
            if self.challonge.getTourneyId() is None:
                return Response('Tournament is not set up.', reply=True)
            tourneyID = self.challonge.getTourneyId()
            tourneyName = self.challonge.getTourneyName()
            tourneyType = ''
            if tourneyName.find('1v1') != -1:
                tourneyType = '1v1'
            elif tourneyName.find('2v2') != -1:
                tourneyType = '2v2'
            elif tourneyName.find('3v3') != -1:
                tourneyType = '3v3'
            if tourneyType != '':
                requestedMatches = challonge.matches.index(tourneyID)
                suggested_play_order_num = 0
                suggested_play_order_id = 0
                for attrVal in requestedMatches:
                    if int(attrVal['suggested-play-order']) == int(number):
                        suggested_play_order_num = int(attrVal['suggested-play-order'])
                        suggested_play_order_id = int(attrVal["id"])
                        break
                if int(number) >= 1 and int(number) <= len(requestedMatches):
                    matchNum = suggested_play_order_id
                    requestedMatchShow = challonge.matches.show(tourneyID, matchNum)
                    requestedNumMatch_id = requestedMatchShow["id"]
                    requestedNumMatch_tournamentId = requestedMatchShow["tournament-id"]
                    requestedNumMatch_play_order = requestedMatchShow["suggested-play-order"]
                    requestedNumMatch_groupId = requestedMatchShow["group-id"]
                    requestedNumMatch_Identifier = requestedMatchShow["identifier"]
                    requestedNumMatch_round = requestedMatchShow["round"]
                    requestedNumMatch_P1_Id = requestedMatchShow["player1-id"]
                    requestedNumMatch_P2_Id = requestedMatchShow["player2-id"]
                    participants = challonge.participants.index(tourneyID)
                    requestedNumMatch_P1_Name = ""
                    requestedNumMatch_P2_Name = ""
                    foundName1 = False
                    foundName2 = False
                    for participant in participants:
                        if (participant["id"] == requestedNumMatch_P1_Id or participant["id"] == requestedNumMatch_P2_Id) and participant["tournament-id"] == tourneyID:
                            if participant["id"] == requestedNumMatch_P1_Id:
                                requestedNumMatch_P1_Name = participant["name"]
                                foundName1 = True
                            if participant["id"] == requestedNumMatch_P2_Id:
                                requestedNumMatch_P2_Name = participant["name"]
                                foundName2 = True
                        if foundName1 == foundName2 and foundName1:
                            break
                    
                    printMsg =  "Match " + str(matchNum) + " identifier: " + str(requestedNumMatch_Identifier)
                    printMsg += "\nMatch " + str(matchNum) + " tourney id: " + str(requestedNumMatch_tournamentId)
                    printMsg += "\nMatch " + str(matchNum) + " group id: " + str(requestedNumMatch_groupId)
                    printMsg += "\nMatch " + str(matchNum) + " id: " + str(requestedNumMatch_id)
                    printMsg += "\nMatch " + str(matchNum) + " round: " + str(requestedNumMatch_round)
                    printMsg += "\nMatch " + str(matchNum) + " Player 1 Id: " + str(requestedNumMatch_P1_Id) 
                    printMsg += "\nMatch " + str(matchNum) + " Player 1 name: " + str(requestedNumMatch_P1_Name)
                    printMsg += "\nMatch " + str(matchNum) + " Player 2 Id: " + str(requestedNumMatch_P2_Id)
                    printMsg += "\nMatch " + str(matchNum) + " Player 2 name: " + str(requestedNumMatch_P2_Name)
                    self.safe_print(printMsg)
                    self.safe_print("Matches: " + str(requestedMatches))
                    finalChallongeMsg = '<@' + str(message.author.id) + '>, for Round ' + str(requestedNumMatch_round) + ', Seed ' + str( (number) ) + ', the team/individual names are '
                    if foundName1:
                        finalChallongeMsg += '\" ' + requestedNumMatch_P1_Name + '\"'
                    if foundName2:
                        if foundName1:
                            finalChallongeMsg += ' and '
                        finalChallongeMsg += '\" ' + requestedNumMatch_P2_Name + '\"'
                    finalChallongeMsg +=  '.'
                    if foundName1 and foundName2:
                        game_username = "mock"
                        game_password = ('```' +
                                         str(''.join(random.choice(string.digits[1:]) for _ in range(6))) + '```')
                        genericMsg = 'Hey, your game is going to be casted.  The casters will be creating the game.'
                        genericMsg += '\n\n' + str(requestedNumMatch_P1_Name) + ' will be the blue team.'
                        genericMsg += '\n' + str(requestedNumMatch_P2_Name) + ' will be the orange team.'
                        genericMsg += '\nStay on these colors for the duration of the series.'
                        if hold:
                            genericMsg += '\n\nThe match username and password will be DM\'d to you when it is ready to be casted.'
                            genericMsg += ('\n\n**Do not start your game '
                                           'until contacted by the '
                                           'casters.**')
                        elif unhold:
                            genericMsg = ('Sorry, you were either told to '
                                'hold in error, or the plan has changed. Please '
                                'contact your opponent for match number ' +
                                str(number) + ' and play as normal.  We\'re '
                                'sorry for the trouble.')

                        else:
                            genericMsg += '\n\nThe username for the lobby is: '
                            genericMsg += game_username + '\nThe password is: ' + game_password
                            genericMsg += '\n\nDo not join teams until all players are in as well as the 2 casters.  Otherwise the match will not count.'
                        caseSensitivity = True
                        groupName1Loop = False
                        groupName2Loop = False
                        teamLstNames1 = ''
                        teamLstNames2 = ''
                        self.excelSpread.checkExpired()
                        if tourneyType == '1v1':
                            responseWKS = ''
                            if not self.excelSpread.getWS():
                                self.excelSpread.setCredentials()
                                gss_client = self.excelSpread.getGSS()
                                if not self.excelSpread.getExcelKey():
                                    return Response('The key has not been set by an admin.', reply=True)
                                gc = gss_client.open_by_key(self.excelSpread.getExcelKey())
                                wks = gc.sheet1
                                self.excelSpread.setGC(gc)
                                self.excelSpread.setWS(wks)
                            responseWKS = self.excelSpread.getWS()
                            member_p1_id = self.excelSpread.checkTeamExistInSpreadSheet(requestedNumMatch_P1_Name, responseWKS, caseSensitivity, tourneyType)
                            member_p2_id = self.excelSpread.checkTeamExistInSpreadSheet(requestedNumMatch_P2_Name, responseWKS, caseSensitivity, tourneyType)
                            self.safe_print('member 1 id: ' +
                                            str(member_p1_id))
                            self.safe_print('member 2 id: ' +
                                            str(member_p2_id))
                            member_p1 = discord.utils.find(lambda mem: mem.id == str(member_p1_id[0]), message.channel.server.members)
                            member_p2 = discord.utils.find(lambda mem: mem.id == str(member_p2_id[0]), message.channel.server.members)
                            #if(type(member_p1) is not None):
                            if(isinstance(member_p1, discord.Member)):
                                groupName1Loop = True
                                await self.safe_send_message(member_p1, genericMsg)
                            #if(type(member_p2) is not None):
                            if(isinstance(member_p2, discord.Member)):
                                groupName2Loop = True
                                await self.safe_send_message(member_p2, genericMsg)
                        elif tourneyType == '2v2':
                            responseWKS = ''
                            if not self.excelSpread.getWS():
                                self.excelSpread.setCredentials()
                                gss_client = self.excelSpread.getGSS()
                                if not self.excelSpread.getExcelKey():
                                    return Response('The key has not been set by an admin.', reply=True)
                                gc = gss_client.open_by_key(self.excelSpread.getExcelKey())
                                wks = gc.sheet1
                                self.excelSpread.setGC(gc)
                                self.excelSpread.setWS(wks)
                            responseWKS = self.excelSpread.getWS()
                            group1Name = requestedNumMatch_P1_Name
                            group2Name = requestedNumMatch_P2_Name
                            teamLstNames1 = self.excelSpread.checkTeamExistInSpreadSheet(group1Name, responseWKS, caseSensitivity, tourneyType)
                            teamLstNames2 = self.excelSpread.checkTeamExistInSpreadSheet(group2Name, responseWKS, caseSensitivity, tourneyType)
                            if teamLstNames1 == False:
                                #something happened, cannot populate list
                                owner1 = discord.utils.find(lambda mem3: mem3.id == str(self.config.owner_id), message.channel.server.members)
                                errorMsg = 'Something went wrong when retrieving the list.  Can you check it out?'
                                await self.safe_send_message(owner1, errorMsg)
                            else:
                                groupName1Loop = True
                                for playerName in teamLstNames1:
                                    memberName1 = discord.utils.find(lambda mem: mem.id == str(playerName), message.channel.server.members)
                                    await self.safe_send_message(memberName1, genericMsg)
                            if teamLstNames2 == False:
                                #something happened, cannot populate list
                                owner1 = discord.utils.find(lambda mem3: mem3.id == str(self.config.owner_id), message.channel.server.members)
                                errorMsg = 'Something went wrong when retrieving the list.  Can you check it out?'
                                await self.safe_send_message(owner1, errorMsg)
                            else:
                                groupName2Loop = True
                                for playerName in teamLstNames2:
                                    memberName2 = discord.utils.find(lambda mem: mem.id == str(playerName), message.channel.server.members)
                                    await self.safe_send_message(memberName2, genericMsg)
                        elif tourneyType == '3v3':
                            responseWKS = ''
                            if not self.excelSpread.getWS():
                                self.excelSpread.setCredentials()
                                gss_client = self.excelSpread.getGSS()
                                if not self.excelSpread.getExcelKey():
                                    return Response('The key has not been set by an admin.', reply=True)
                                gc = gss_client.open_by_key(self.excelSpread.getExcelKey())
                                wks = gc.sheet1
                                self.excelSpread.setGC(gc)
                                self.excelSpread.setWS(wks)
                            responseWKS = self.excelSpread.getWS()
                            group1Name = requestedNumMatch_P1_Name
                            group2Name = requestedNumMatch_P2_Name
                            teamLstNames1 = self.excelSpread.checkTeamExistInSpreadSheet(group1Name, responseWKS, caseSensitivity, tourneyType)
                            teamLstNames2 = self.excelSpread.checkTeamExistInSpreadSheet(group2Name, responseWKS, caseSensitivity, tourneyType)
                            if teamLstNames1 == False:
                                #something happened, cannot populate list
                                owner1 = discord.utils.find(lambda mem3: mem3.id == str(self.config.owner_id), message.channel.server.members)
                                errorMsg = 'Something went wrong when retrieving the list.  Can you check it out?'
                                await self.safe_send_message(owner1, errorMsg)
                            else:
                                groupName1Loop = True
                                for playerName in teamLstNames1:
                                    memberName1 = discord.utils.find(lambda mem: mem.id == str(playerName), message.channel.server.members)
                                    await self.safe_send_message(memberName1, genericMsg)
                            if teamLstNames2 == False:
                                #something happened, cannot populate list
                                owner2 = discord.utils.find(lambda mem3: mem3.id == str(self.config.owner_id), message.channel.server.members)
                                errorMsg = 'Something went wrong when retrieving the list.  Can you check it out?'
                                await self.safe_send_message(owner2, errorMsg)
                            else:
                                groupName2Loop = True
                                for playerName in teamLstNames2:
                                    memberName2 = discord.utils.find(lambda mem: mem.id == str(playerName), message.channel.server.members)
                                    await self.safe_send_message(memberName2, genericMsg)
                        if groupName1Loop and groupName2Loop and groupName1Loop:
                            adminMsg = '\n\n' + str(requestedNumMatch_P1_Name) + ' will be the blue team.'
                            adminMsg += '\n' + str(requestedNumMatch_P2_Name) + ' will be the orange team.'
                            #adminMsg += '\n\nThe username for the lobby is: '
                            #adminMsg += game_username + '\nThe password is: ' + game_password
                            if hold:
                                adminMsg += ('\n\n**The players have been told '
                                            'to wait** for the match name and '
                                            'password. Please use the !stream '
                                            'command for this match when '
                                            'ready')
                            elif unhold:
                                adminMsg = ('**Match number ' + str(number) +
                                ' is no longer being '
                                'held**\n\nThe players have been told to '
                                'play their game as normal.')

                            else:
                                adminMsg += '\n\nThe username for the lobby is: '
                                adminMsg += game_username + '\nThe password is: ' + game_password

                            
                            for caster_id in self.config.casters:
                                self.safe_print('caster id: ' +
                                                str(caster_id))
                                member_caster = discord.utils.find(lambda mem3: mem3.id == str(caster_id), message.channel.server.members)
                                if (isinstance(member_caster, discord.Member)):
                                    self.safe_print('caster name: ' + str(member_caster.name))
                                    await self.safe_send_message(member_caster,(finalChallongeMsg + '\n' + adminMsg))
                            await self.safe_send_message(message.channel,
                                                         finalChallongeMsg +
                                                         '\n' + adminMsg)
                    else:
                        errorNoOtherPlayer = '<@' + str(message.author.id) + '>, there is currently only one player in the match that you have selected.'
                        await self.safe_send_message(message.channel, errorNoOtherPlayer)
                else:
                    errorOutOfRangeMsg = '<@' + str(message.author.id) + '>, please have the number be in between 1 and ' + str(len(requestedMatches))
                    await self.safe_send_message(message.channel, errorOutOfRangeMsg)
            else:
                await self.safe_send_message(message.channel, 'Tournament Type was not set.  Cannot be casted due to configuration below')
        else:
            await self.safe_send_message(message.channel, '<@' + str(message.author.id) + '>, it must either be the name of the person or be a group number')

    async def cmd_lmgtfy(self, message, searchTerm):
        """
        Usage: {command_prefix}lmgtfy <content>
        Gives you a short lmgtfy link
        """
        searchTerm = searchTerm.replace('\'', '')
        print('Lmgtfy url: ' + self.lmgtfy.lmgtfy_url(searchTerm))
        try:
            longterm = self.lmgtfy.lmgtfy_url(searchTerm)
            content = 'Lmgtfy url: (%s)' % (str(longterm))
            return Response(content,reply=True)
        except requests.exceptions.ConnectionError:
            self.safe_print('No Internet Connection')
    
    async def cmd_togglecheckin(self, message):
        """
        Usage: {command_prefix}togglecheckin
        Toggles the checkinactive boolean
        """
        self.checkinActive = not self.checkinActive
        if not self.checkinActive:
            await self.safe_send_message(message.channel, 
                    ('Check-In is closed.  checkinActive: ' +
                     str(self.checkinActive)))
    
    def _check_on_probation(self, member):
        if member.server.id == self.config.organization.server_id:
            for role in member.roles:
                if role.id == 161617080079220736:
                    return True
            return False
        return False

    async def cmd_checkin(self, message, channel_Name=None):
        """
        Usage: {command_prefix}checkin [channel name]
        Checks in the user or the entire channel
        """
        _caseSense = True
        if not self.lock_checkin:
            self.lock_checkin = True
        
        if self.lock_checkin:
            _caseSense = True
            if channel_Name is None:
                username_id = str(message.author.id)
                if self._check_on_probation(message.author):
                    return Response(('You are on probation and unable to sign up for this tournament.'), reply=True)
                member = discord.utils.find(lambda mem: mem.id == str(username_id), message.channel.server.members)
                loginConfirm = "Checking your name in the spreadsheet to see if you are registered, <@" + str(message.author.id) + ">."
                await self.safe_send_message(message.channel, loginConfirm)
                self.excelSpread.checkExpired()
                if not self.excelSpread.getWS():
                    self.excelSpread.setCredentials()
                    #print('result: ' + str(self.excelSpread.getWS()))
                    if not self.excelSpread.getExcelKey():
                        return Response('The key has not been set by an admin.', reply=True)
                    gss_client = self.excelSpread.getGSS()
                    gc = gss_client.open_by_key(self.excelSpread.getExcelKey())
                    wks = gc.sheet1
                    self.excelSpread.setGC(gc)
                    self.excelSpread.setWS(wks)
                validDup = self.excelSpread.checkDuplicateNames(member, self.excelSpread.getWS(), _caseSense)
                validCheckedIn = self.excelSpread.checkUserCheckedInSpreadSheet(member, self.excelSpread.getWS(), _caseSense)
                if not validDup and (validDup is not None) and not validCheckedIn:
                    #no duplicate entry and no id found
                    responseValid = self.excelSpread.checkUserExistInSpreadSheet(member, self.excelSpread.getWS(), True)
                    if responseValid:
                        content = '%s, %s' % (member.name, 'you are all checked in and can move to another channel.')
                        await self.safe_send_message(member, content)
                    else:
                        content = '%s, %s' % (member.name, 'you are not checked in and cannot move to another channel.')
                        await self.safe_send_message(member, content)
                    self.lock_checkin = False
                elif not validDup and validCheckedIn:
                    content = '%s, %s' % (member.name, 'you have already checked in.')
                    await self.safe_send_message(member, content)
                elif not validDup:
                    content = '%s, %s' % (member.name, 'You have never signed up for this tournament.')
                    await self.safe_send_message(member, content)
                elif validDup:
                    content = 'Your name is entered twice, please contact a moderator or Tourney Assistant.'
                    await self.safe_send_message(member, content)
            else:
                self.checkinActive = True
                while self.checkinActive:
                    channel_Name = channel_Name.replace('\'', '')
                    await self.safe_send_message(message.channel, 'Checking in '
                                                 + 'members of the ' + channel_Name
                                                 + " channel.")
                    channel = [channel for channel in message.channel.server.channels if channel.type == discord.ChannelType.voice and channel.name == channel_Name]
                    if len(channel) == 0:
                        await self.safe_send_message(message.channel, 'The channel, ' + str(channel_Name) + ', does not exist or was typed incorrectly.')
                        self.checkinActive = False
                        break
                    else:
                        channel = channel[0]
                        members = channel.voice_members
                        sorted_members = sorted(channel.voice_members, key=lambda x: x.name.lower())
                        sorted_members.reverse()
                        members = sorted_members
                        self.excelSpread.checkExpired()
                        for tempMem in sorted_members:
                            if self._check_on_probation(tempMem):
                                await self.safe_send_message(tempMem, ('You are on probation and unable to sign up for this tournament.'))
                                continue
                            userName2 = (tempMem.name)
                            self.safe_print('Username: ' + str(userName2))
                            member_p1 = tempMem
                            member_p1_name = ''
                            error=False
                            if member_p1 is not None:
                                member_p1_name = member_p1.name
                            else:
                                await self.safe_send_message(message.channel,  'Member was not found')
                                error = True
                            if error == False:
                                if not self.excelSpread.getWS():
                                    self.excelSpread.setCredentials()
                                    gss_client = self.excelSpread.getGSS()
                                    if not self.excelSpread.getExcelKey():
                                        return Response('The key has not been set by an admin.', reply=True)
                                    gc = gss_client.open_by_key(self.excelSpread.getExcelKey())
                                    wks = gc.sheet1
                                    self.excelSpread.setGC(gc)
                                    self.excelSpread.setWS(wks)
                                validDup = self.excelSpread.checkDuplicateNames(member_p1, self.excelSpread.getWS(), _caseSense)
                                validCheckedIn = self.excelSpread.checkUserCheckedInSpreadSheet(member_p1, self.excelSpread.getWS(), _caseSense)
                                self.safe_print('validDup: ' + str(validDup))
                                self.safe_print('validCheckIn: ' +
                                                str(validCheckedIn))
                                if (not validDup and validDup is not None) and not validCheckedIn:
                                    responseValid = self.excelSpread.checkUserExistInSpreadSheet(member_p1, self.excelSpread.getWS(), True)
                                    if responseValid:
                                        await self.safe_send_message(member_p1, 'Hello ' + str(member_p1_name) + ', we just want to let you know that you are checked in and can move to another channel.')
                                        ownerMember = discord.utils.find(lambda mem2: mem2.id == str(self.config.owner_id), message.channel.server.members)
                                        Channel_Id = self.config.tourneylobby
                                        try:
                                            channel2 = discord.utils.find(lambda wantChannel: wantChannel.id == str(Channel_Id), message.channel.server.channels)
                                            if channel2 is None:
                                                if self.config.debug_mode:
                                                    await self.safe_send_message(member_p1, 'Tried moving you to the ' + str(Channel_Id) + ' voice channel.')
                                                    await self.safe_send_message(ownerMember, 'Tried moving you to the ' + str(Channel_Id) + ' voice channel.')
                                            else:
                                                finalChannel = channel2
                                                await self.move_member(member_p1, finalChannel)
                                                if self.config.debug_mode:
                                                    await self.safe_send_message(member_p1, 'Moved to the ' + str(finalChannel.name) + ' voice channel.')
                                                    await self.safe_send_message(ownerMember, 'Tried moving ' + str(member_p1.name) + ' to the ' + str(finalChannel.name) + ' voice channel.')
                                        except discord.errors.InvalidArgument:
                                            if self.config.debug_mode:
                                                await self.safe_send_message(member_p1, 'The channel provided is not a voice channel.')
                                                await self.safe_send_message(ownerMember, 'Tried moving ' + str(member_p1.name) + ' to the ' + str(finalChannel.name) + ' voice channel but failed because of InvalidArgument.')
                                            #logs(client, message)   
                                        except discord.errors.HTTPException:
                                            if self.config.debug_mode:
                                                await self.safe_send_message(member_p1, 'Moving the member failed.')
                                                await self.safe_send_message(ownerMember, 'Tried moving ' + str(member_p1.name) + ' to the ' + str(finalChannel.name) + ' voice channel but failed because of HTTPException.')
                                            #logs(client, message)
                                        except discord.errors.Forbidden:
                                            if self.config.debug_mode:
                                                await self.safe_send_message(member_p1, 'You do not have permissions to move the member.')
                                                await self.safe_send_message(ownerMember, 'Tried moving ' + str(member_p1.name) + ' to the ' + str(finalChannel.name) + ' voice channel but failed because of Forbidden.')
                                            #logs(client, message)
                                    else:
                                        await self.send_message(member_p1, 'You have never signed up for this tournament.')
                                elif not validDup and validDup is not None and validCheckedIn:
                                    Channel_ID = self.config.tourneylobby
                                    currentVoiceChannel = member_p1.voice_channel
                                    channel2 = discord.utils.find(lambda wantChannel: wantChannel.id == str(Channel_ID), message.channel.server.channels)
                                    try:
                                        await self.move_member(member_p1, channel2)
                                    except discord.errors.InvalidArgument:
                                        if self.config.debug_mode:
                                            await self.send_message(member_p1, 'The channel provided is not a voice channel.')
                                            await self.send_message(ownerMember, 'Tried moving ' + str(member_p1.name) + ' to the ' + str(finalChannel.name) + ' voice channel but failed because of InvalidArgument.')
                                    except discord.errors.HTTPException:
                                        if self.config.debug_mode:
                                            await self.send_message(member_p1, 'Moving the member failed.')
                                            await self.send_message(ownerMember, 'Tried moving ' + str(member_p1.name) + ' to the ' + str(finalChannel.name) + ' voice channel but failed because of HTTPException.')
                                    except discord.errors.Forbidden:
                                        if self.config.debug_mode:
                                            await self.send_message(member_p1, 'You do not have permissions to move the member.')
                                            await self.send_message(ownerMember, 'Tried moving ' + str(member_p1.name) + ' to the ' + str(finalChannel.name) + ' voice channel but failed because of Forbidden.')
                                elif not validDup and not validCheckedIn:
                                    content = '%s, %s' % (member_p1.name, 'You have never signed up for this tournament.')
                                    await self.safe_send_message(member_p1, content)
                                elif validDup:
                                    content = 'you have already signed up twice for this tournament.  Please contact a moderator or Tourney Assistant.'
                                    await self.safe_send_message(member_p1, content)
                                else:
                                    await self.send_message(member_p1, 'Hello ' + str(member_p1_name) + ', we just wanted to let you know that you are not checked in and/or have not registered for the tournament')
                    #wait 60s before running again
                    #time.sleep(60)
                    await asyncio.sleep(60)
            self.lock_checkin = False
    
    async def cmd_reloadfile(self, message, keyType):
        """
        Usage: {command_prefix}reloadFile <login>
        Reloads the ini file 
        """
        if keyType in ['login']:
            content = 'Reloading the current path for ' + str(keyType) + '.... but this is a work-in-progress'
            content = '%s, %s' % (message.author.mention, content)
            self.config.getSettings()
            await self.safe_send_message(message.channel, content)
        else:
            return Response('That is not the correct commands', reply=True)
    async def cmd_participant(self, message, option, username):
        """
        Usage: {command_prefix}participant <challonge> @Username
        Checks to see if the username is a partipant on challonge
        """
        user_id = extract_user_id(username)
        
        if option in ['challonge']:
            if not user_id:
                #assuming it is the original person
                participantUsername = str(message.author.name)
                responseMsg = 'the ID for ' + str(participantUsername) + ' is ' + str(getChallongeParticipantId(participantUsername))
                if responseMsg.find(' is not found') == -1:
                    errorMsg = 'Did you possibly sign up for the wrong tournament?'
                    return Response(errorMsg, reply=True)
                else:
                    return Response(responseMsg, reply=True)
            else:
                responseMsg = 'the ID for ' + str(username) + ' is ' + str(getChallongeParticipantId(username))
                if responseMsg.find(' is not found') == -1:
                    errorMsg = 'Did you possibly sign up for the wrong tournament?'
                    return Response(errorMsg, reply=True)
                else:
                    return Response(responseMsg, reply=True)
        else:
            return Response('That is not a valid command', reply=True)
                
    async def cmd_id(self, message, author, username=None):
        """
        Usage: {command_prefix}id @Username
        Tells the user their own id or the user that they tagged.
        """
        orgStr = ', your id is `%s`:'
        if username is not None:
            user_id = extract_user_id(username)
            if not user_id:
                return Response(orgStr % author.id, reply=True)
            member = discord.utils.find(lambda mem: mem.id == str(user_id), message.channel.server.members)
            orgStr = str(username) + ', ' + orgStr % member.id
            await self.safe_send_message(message.channel, orgStr)
            return True
        return Response(orgStr % author.id, reply=True)
        
    @owner_only
    async def cmd_joinserver(self, message, server_link):
        """
        Usage: {command_prefix}joinserver invite_link

        Asks the bot to join a server.
        """

        try:
            await self.accept_invite(server_link)
            return Response(":+1:")

        except:
            raise CommandError('Invalid URL provided:\n{}\n'.format(server_link))
    
    @owner_only
    async def cmd_leaveserver(self, server):
        """
        Usage: {command_prefix}leaveserver

        Asks the bot to leave a server.
        """
        #await self.leave_server(server)
        return Response('Feature implementing shortly', reply=True)
        
    async def cmd_clean(self, message, channel, author, amount):
        """
        Usage: {command_prefix}clean amount

        Removes amount messages the bot has posted in chat.
        """

        try:
            float(amount)  # lazy check
            amount = int(amount)
        except:
            return Response("Enter a number.  NUMBER.  That means digits.  `5`.  Etc.", reply=True)

        def is_possible_command_invoke(entry):
            valid_call = any(
                entry.content.startswith(prefix) for prefix in [self.config.command_prefix])  # can be expanded
            return valid_call and not entry.content[1:2].isspace()

        await self.safe_delete_message(message)

        msgs = 0
        delete_invokes = True
        async for entry in self.logs_from(channel, limit=int(amount)):
            if entry.author == self.user:
                await self.safe_delete_message(entry)
                msgs += 1

            if is_possible_command_invoke(entry) and delete_invokes:
                try:
                    await self.safe_delete_message(entry)
                except discord.Forbidden:
                    delete_invokes = False
                else:
                    msgs += 1

        # Becuase of how this works, you can do `clean 20` and <20 messages will get deleted

        return Response('Cleaned up {} message{}.'.format(msgs, '' if msgs == 1 else 's'))
    
    def _get_member_count(self, channel):
        return len(channel.voice_members)
    
    async def cmd_listchannelspecs(self, server, author, message, channel_Name=None):
        """
        Usage: {command_prefix}listchannel <channel_Name>
        Gives a list of channel based on the name entered in
        """
        if channel_Name is not None:
            channel_Name = channel_Name.replace('\'', '')
        else:
            return Response('Channel name is set to None', reply=True)
        if not self._check_server_exist(server):
            return Response('You cannot use this bot in private messages.', reply=True)
        lines = ['Channel list for %s' % server.name, '```', '```']
        if channel_Name is not None:
            serverChannels = [ch for ch in server.channels if ch.name.find(channel_Name) != -1]
            if channel_Name.find('In-Game') != -1:
                sorted_serverChannels = sorted(serverChannels, key=lambda x: int(x.name.split(" ")[-1]))
                for channel in sorted_serverChannels:
                    nextline = channel.id + ' ' + channel.name + ' members: ' + str(self._get_member_count(channel))
                    if len('\n'.join(lines)) + len(nextline) < DISCORD_MSG_CHAR_LIMIT:
                        lines.insert(len(lines) - 1, nextline)
                    else:
                        await self.send_message(author, '\n'.join(lines))
                        lines = ['```', '```']
                        lines.insert(len(lines) - 1, nextline)
            else:
                serverChannels = server.channels
                sorted_serverChannels = sorted(serverChannels, key=lambda x: x.name.lower())
                for channel in sorted_serverChannels:
                    if channel.name.find(channel_Name) != -1:
                        nextline = channel.id + ' ' + channel.name
                        if len('\n'.join(lines)) + len(nextline) < DISCORD_MSG_CHAR_LIMIT:
                            lines.insert(len(lines) - 1, nextline)
                        else:
                            await self.send_message(author, '\n'.join(lines))
                            lines = ['```', '```']
            await self.send_message(author, '\n'.join(lines))
            return Response(":mailbox_with_mail:")
    
    async def cmd_register(self, message, author, tournamentType='1v1', member_2=None, member_3=None):
        """
        Usage: {command_prefix}register <tournamentType> [member_2] [member_3]
        Handles with bugs if people cannot sign in via the webpage
        """
        _caseSense = False
        if tournamentType is not None:
            if tournamentType == '1v1':
                #1v1 signup
                member = author
                if self.excelSpread.getWS():
                    #logged in
                    self.excelSpread.checkExpired()
                    validDup = self.excelSpread.checkDuplicateNames(member, self.excelSpread.getWS(), _caseSense)
                    #find last empty cell in B
                    if validDup and validDup != None:
                        #no duplicate entry
                        if validDup == True:
                            cell_list = self.excelSpread.getWS().range('B2:B985')
                            cell_row = 0
                            cell_col = 0
                            for cell in cell_list:
                                if cell.value == '':
                                    cell_row = cell.row
                                    cell_col = cell.col
                                    break
                            ts = datetime.now() + timedelta(hours=-3)
                            print('ts: ' + str(ts))
                            st = ts.strftime('%m/%d/%Y %H:%M:%S')
                            self.excelSpread.getWS().update_cell(cell_row, (cell_col - 1), st)
                            self.excelSpread.getWS().update_cell(cell_row, cell_col, member.name)
                            return Response('You are all signed up!', reply=True)
                        else:
                            return Response('You must not have registered for this tournament', reply=True)
                    else:
                        return Response('You have already signed up for this tournament.', reply=True)
                else:
                    return Response('The tournament has not been opened yet to sign up for', reply=True)
            elif tournamentType == '2v2':
                #2v2 signup
                member = author
            elif tournamentType == '3v3':
                #3v3 signup`
                member = author
    async def cmd_livebracketlink(self, message):
        """
        Usage: {command_prefix}livebracketlink
        Command that gets the full tournament link
        """
        strLink = 'Live link: ' + str(self.challonge.getTourneyLink()) 
        responseCheck = self._check_challonge_perms(str(strLink))
        
        if bool(responseCheck[0]):
            return Response(str(responseCheck[1]), reply=True)
        else:
            return Response(str(responseCheck[1]), reply=True)
        '''
        return Response('Live link: ' + str(self.challonge.getTourneyLink()), reply=True)
        '''
    async def cmd_livebracketimg(self, message):
        """
        Usage: {command_prefix}livebracketimg
        Command that returns the live bracket in an image
        """
        strLink = 'Live bracket image link: ' + str(self.challonge.getLiveImgUrl())

        responseCheck = self._check_challonge_perms(str(strLink))
        
        if bool(responseCheck[0]):
            return Response(str(responseCheck[1]), reply=True)
        else:
            return Response(str(responseCheck[1]), reply=True)
        '''
        return Response('Live bracket image link: ' + self.challonge.getLiveImgUrl(), reply=True)
        '''
    async def cmd_livebracketstarted(self, message):
        """
        Usage: {command_prefix}livebracketstarted
        Command that returns the live bracket when it started
        """ 
        strLink = 'Live bracket started at: ' + str(self.challonge.getTimeStartedAt())

        responseCheck = self._check_challonge_perms(str(strLink))
        
        if bool(responseCheck[0]):
            return Response(str(responseCheck[1]), reply=True)
        else:
            return Response(str(responseCheck[1]), reply=True)
        '''
        return Response('Live bracket started at: ' + str(self.challonge.getTimeStartedAt()), reply=True)
        '''

    async def cmd_livebracketprogress(self, message):
        """
        Usage: {command_prefix}livebracketprogress
        Command that gets the progress of the live bracket (out of 100 percent)
        """ 
        strLink = 'Live bracket image link: ' + str(self.challonge.getTourneyProgress())

        responseCheck = self._check_challonge_perms(str(strLink))
        
        if bool(responseCheck[0]):
            return Response(str(responseCheck[1]), reply=True)
        else:
            return Response(str(responseCheck[1]), reply=True)
        '''
        return Response('Progress: ' + str(self.challonge.getTourneyProgress()), reply=True)
        '''

    async def cmd_livebracketstate(self, message):
        """
        Usage: {command_prefix}livebracketstate
        Command that gets the progress of the live bracket state
        """ 
        strLink = 'Live tournament bracket state: ' + str(self.challonge.getTourneyState())

        return Response(str(self._check_challonge_perms(str(strLink)[1])),reply=True)

        '''
        return Response('Current state of the bracket: ' + str(self.challonge.getTourneyState()), reply=True)
        '''

    async def cmd_getscores(self, message, author, matchNum=None):
        """
        Usage: {command_prefix}getscores <match number>
        Command that gets the score from challonge based on the format of the
        match number and score
        Example format:
            {command_prefix}getscores 10
        The above example will get the score for match 10
        """
        if matchNum is None:
            return Response('Format for getting scores is invalid')
        if matchNum is not None:
            print('matchNum: ' + str(matchNum))
            if self.excelSpread.getWS() and self.challonge.getLogin():
                self.excelSpread.checkExpired()
                if self.excelSpread.getWS():
                    tourneyID = self.challonge.getTourneyId()
                    tourneyName = self.challonge.getTourneyName()
                    requestedMatches = challonge.matches.index(tourneyID)
                    if matchNum.isdigit():
                        if int(matchNum) >= 1 and int(matchNum) <= len(requestedMatches):
                            suggested_num = ''
                            suggested_num_id = ''
                            for attrVal in requestedMatches:
                                if int(attrVal['suggested-play-order']) == int(matchNum):
                                    suggested_num = int(attrVal['suggested-play-order'])
                                    suggested_num_id = int(attrVal['id'])
                                    break
                            
                            if(type(suggested_num) is int and suggested_num != '') and (type(suggested_num_id) is int and suggested_num_id != ''):
                                requestedMatchShow = challonge.matches.show(tourneyID, suggested_num_id)
                                scores = requestedMatchShow['scores-csv']
                                if scores is not None and scores != '':
                                    #everything is fine, continue
                                    requestedNumMatch_P1_Id = requestedMatchShow["player1-id"]
                                    requestedNumMatch_P2_Id = requestedMatchShow["player2-id"]
                                    participants = challonge.participants.index(tourneyID)
                                    requestedNumMatch_P1_Name = ""
                                    requestedNumMatch_P2_Name = ""
                                    foundName1 = False
                                    foundName2 = False
                                    for participant in participants:
                                        if (participant["id"] == requestedNumMatch_P1_Id or participant["id"] == requestedNumMatch_P2_Id) and participant["tournament-id"] == tourneyID:
                                            if participant["id"] == requestedNumMatch_P1_Id:
                                                requestedNumMatch_P1_Name = participant["name"]
                                                foundName1 = True
                                            if participant["id"] == requestedNumMatch_P2_Id:
                                                requestedNumMatch_P2_Name = participant["name"]
                                                foundName2 = True
                                        if foundName1 == foundName2 and foundName1:
                                            break
                                    requestedNumMatch_round = requestedMatchShow["round"]
                                    if foundName1 and foundName2:
                                        statusMatch = challonge.matches.show(tourneyID, requestedMatchShow["id"])
                                        matchOverStatus = ("Match " + str(matchNum) +
                                        " is " + str(statusMatch["state"]) + ". " +
                                        str(requestedNumMatch_P1_Name) + " " +
                                        str(scores)  + " " +
                                        str(requestedNumMatch_P2_Name) + ".")
                                        return Response(matchOverStatus,reply=True)
                                else:
                                    statusMatch = challonge.matches.show(tourneyID, requestedMatchShow['id'])
                                    matchOverStatus = ("Match " + str(matchNum)
                                                       + " is " +
                                                       str(statusMatch["state"])
                                                       + ". There is no score "
                                                       "currently.")
                                    return Response(matchOverStatus, reply=True)
                            else:
                                return Response('Match not found.', reply=True)
                        else:
                            return Response('Match must be in between 1 and ' + str(len(requestedMatches)), reply=True)
                    else:
                        return Response('Match must be a number.', reply=True)
                else:
                    return Response('Excel spreadsheet was not set.', reply=True)
            else:
                contentResp = ''
                if not self.excelSpread.getWS():
                    contentResp += 'Excel Spreadsheet not loaded correctly.'
                if not self.challonge.getLogin():
                    contentResp += '\nChallonge is not logged in correctly.'
                return Response(contentResp, reply=True)
    
    async def cmd_reportscores(self, message, author, matchNum=None, score=None):
        """
        Usage: {command_prefix}reportscores <match number> <score>
        Command that reports the score to challonge based on the format of match number and score
        Example format:
        {command_prefix}reportscores 10 2-0
        The above example says that the first player won 2-0 for match 10
        """
        #TODO if channel is not report scores channel, do nothing else.
        #checking this anywhere else is wasteful, the only time we care about
        #the channel is with this command.  If we check this in on_message, then
        #we are introducing two additional checks (is it this command and is it
        #from the report scores channel) for EVERY message event.  By placing it
        #here, it only adds one additional check (is it the report scores
        #channel), and it only does this check if this one command was the one
        #called.  It only makes sense to check the channel in on_message if we
        #want ALL commands to be prohibited in a channel or ALL commands to be
        #allowed ONLY if they're in a channel.
        if int(message.channel.id) != int(127903851994021888):
            return
        if matchNum is None or score is None:
            return Response('Format for reporting scores is invalid')
        if matchNum is not None and score is not None:
            #valid response
            print('matchNum: ' + str(matchNum))
            print('score: ' + str(score))
            if self.excelSpread.getWS() and self.challonge.getLogin():
                #both are logged in
                self.excelSpread.checkExpired()
                if self.excelSpread.getWS():
                    #valid worksheet login
                    tourneyID = self.challonge.getTourneyId()
                    tourneyName = self.challonge.getTourneyName()
                    requestedMatches = challonge.matches.index(tourneyID)
                    if matchNum.isdigit():
                        if int(matchNum) >= 1 and int(matchNum) <= len(requestedMatches):
                            suggested_num = ''
                            suggested_num_id = ''
                            for attrVal in requestedMatches:
                                if int(attrVal['suggested-play-order']) == int(matchNum):
                                    suggested_num = int(attrVal['suggested-play-order'])
                                    suggested_num_id = int(attrVal['id'])
                                    break
                            if(type(suggested_num) is int and suggested_num != '') and (type(suggested_num_id) is int and suggested_num_id != ''):
                                requestedMatchShow = challonge.matches.show(tourneyID, suggested_num_id)
                                scoreSplit = score.split("\d+-\d+")
                                scoreHolder = []
                                scoreLoserHolder = []
                                scoreCountArr = []
                                winCountArr = []
                                for offScore in scoreSplit:
                                    scoreDash = score.split('-')
                                    if len(scoreDash) == 2:
                                        leftSide = scoreDash[0]
                                        rightSide = scoreDash[1]
                                        if leftSide.isdigit() and rightSide.isdigit() and leftSide.isdigit() == True:
                                            scoreLoserHolder.append(str(rightSide) + '-' + str(leftSide))
                                            if int(leftSide) > int(rightSide):
                                                winCountArr.append('P1')
                                            elif int(leftSide) < int(rightSide):
                                                winCountArr.append('P2')
                                        else:
                                            errorNotANumMsg = "The error(s) have occurred: "
                                            firstDigitValid = False
                                            secondDigitValid = False
                                            if not leftSide.isdigit():
                                                errorNotANumMsg += str(leftSide) + " is not a digit"
                                                firstDigitValid = True
                                            if not rightSide.isdigit():
                                                if firstDigitValid:
                                                    errorNotANumMsg += ' and '
                                                    secondDigitValid = True
                                                errorNotANumMsg += str(rightSide) + " is not a digit"
                                                firstDigitValid = True
                                            return Response(str(errorNotANumMsg), reply=True)
                                            
                                    else:
                                        errorNotFormatCorrectly = "The format for a score is with no spaces (i.e. 2-1) and it indicates that the top player (when looking in a match) is the first number and not the second number."
                                        return Response(str(errorNotFormatCorrectly), reply=True)
                                #everything is fine, continue
                                requestedNumMatch_P1_Id = requestedMatchShow["player1-id"]
                                requestedNumMatch_P2_Id = requestedMatchShow["player2-id"]
                                participants = challonge.participants.index(tourneyID)
                                requestedNumMatch_P1_Name = ""
                                requestedNumMatch_P2_Name = ""
                                foundName1 = False
                                foundName2 = False
                                for participant in participants:
                                    if (participant["id"] == requestedNumMatch_P1_Id or participant["id"] == requestedNumMatch_P2_Id) and participant["tournament-id"] == tourneyID:
                                        if participant["id"] == requestedNumMatch_P1_Id:
                                            requestedNumMatch_P1_Name = participant["name"]
                                            foundName1 = True
                                        if participant["id"] == requestedNumMatch_P2_Id:
                                            requestedNumMatch_P2_Name = participant["name"]
                                            foundName2 = True
                                    if foundName1 == foundName2 and foundName1:
                                        break
                                requestedNumMatch_round = requestedMatchShow["round"]
                                if foundName1 and foundName2:
                                    finalWinnerId = ""
                                    dbWinner = ""
                                    if int(winCountArr.count("P1")) > int(winCountArr.count("P2")):
                                        finalWinnerId = requestedNumMatch_P1_Id
                                        dbWinner = requestedNumMatch_P1_Name
                                    elif int(winCountArr.count("P1")) < int(winCountArr.count("P2")):
                                        finalWinnerId = requestedNumMatch_P2_Id
                                        dbWinner = requestedNumMatch_P2_Name
                                    print("finalWinnerId: " + str(finalWinnerId))
                                    print("dbWinner: " + str(dbWinner))
                                    concatWinnerScores = ','.join(scoreSplit)
                                    challonge.matches.update(tourneyID, requestedMatchShow["id"], scores_csv=str(concatWinnerScores), winner_id=str(finalWinnerId))
                                    statusMatch = challonge.matches.show(tourneyID, requestedMatchShow["id"])
                                    matchOverStatus = ("Match " + str(matchNum) +
                                    " is " + str(statusMatch["state"]) + ". " +
                                    str(requestedNumMatch_P1_Name) + " " +
                                    str(concatWinnerScores)  + " " +
                                    str(requestedNumMatch_P2_Name) + ".")
                                    return Response(matchOverStatus,reply=True)
                    else:
                        return Response('The match is not a number.', reply=True)
            else:
                contentResp = ''
                if not self.excelSpread.getWS():
                    contentResp += 'Excel Spreadsheet not loaded correctly.'
                if not self.challonge.getLogin():
                    contentResp += '\nChallonge is not logged in correctly.'
                return Response(contentResp, reply=True)

    def _suggest_cmds(self, message, triedCommand=None):
        """
        Assist with finding the correct command if it is a wrong command
        """
        helpmsg = "**Suggested Commands**\n```"
        suggestions = []
        user_permissions = self.permissions.for_user(message.author)
        if triedCommand is not None:
            for command in dir(self):
                if command.startswith('cmd_') and command != 'cmd_help':
                    command = command.replace('cmd_', '')
                    if command.find(triedCommand) != -1 and command in user_permissions.command_whitelist:
                        suggestions.append("{}{}".format(self.config.command_prefix, command_name))
            helpmsg += ", ".join(suggestions)
            helpmsg += "```"
            if len(suggestions) == 0:
                helpmsg = ''
            return helpmsg
        return ''

    async def cmd_listchannels(self, server, author):
        """
        Usage: {command_prefix}listchannels
        
        List the channels on the server for setting up permissions
        """
        if not self._check_server_exist(server):
            return await self.send_message(author, 'You cannot use this bot in private messages.')
        
        lines = ['Channel list for %s' % server.name, '```', '```']
        for channel in server.channels:
            nextline = channel.id + ' ' + channel.name
            if len('\n'.join(lines)) + len(nextline) < DISCORD_MSG_CHAR_LIMIT:
                lines.insert(len(lines) - 1, nextline)
            else:
                await self.send_message(author, '\n'.join(lines))
                lines = ['```', '```']
        await self.send_message(author, '\n'.join(lines))
        return Response(":mailbox_with_mail:")
        
    async def cmd_listroles(self, server, author):
        """
        Usage: {command_prefix}listroles

        Lists the roles on the server for setting up permissions
        """
        if not self._check_server_exist(server):
            return await self.send_message(author, 'You cannot use this bot in private messages.')

        lines = ['Role list for %s' % server.name, '```', '```']
        for role in server.roles:
            role.name = role.name.replace('@everyone', '@\u200Beveryone')  # ZWS for sneaky names
            nextline = role.id + " " + role.name

            if len('\n'.join(lines)) + len(nextline) < DISCORD_MSG_CHAR_LIMIT:
                lines.insert(len(lines) - 1, nextline)
            else:
                await self.send_message(author, '\n'.join(lines))
                lines = ['```', '```']

        await self.send_message(author, '\n'.join(lines))
        return Response(":mailbox_with_mail:")

    def _check_server_exist(self, server):
        """
        Checks to see if the server exist or not
        """
        if server is not None:
            return True
        return False
    
    async def cmd_perms(self, author, channel, server, permissions):
        '''
        Usage: {command_prefix}perms

        Sends the user a list of their permissions.
        '''
        if not self._check_server_exist(server):
            return await self.send_message(author, 'You cannot use this bot in private messages.')
        lines = ['Command permissions in %s\n' % server.name, '```', '```']

        for perm in permissions.__dict__:
            if perm in ['user_list'] or permissions.__dict__[perm] == set():
                continue

            lines.insert(len(lines) - 1, "%s: %s" % (perm, permissions.__dict__[perm]))

        await self.send_message(author, '\n'.join(lines))
        return Response(":mailbox_with_mail:", reply=True)
        
    async def on_message(self, message):
        """
        Handler that handles the on_message state of the application
        It handles whenever a message is sent or said
        """
        message_content = message.content.strip()
        if not message_content.startswith(self.config.command_prefix):
            return

        if message.author == self.user:
            self.safe_print("Ignoring command from myself (%s)" % message.content)
            return

        #TODO rewrite as prohibited channels, put the music channel in the list.  now
        #it ignores the music channel
        if message.channel.id in self.config.organization.prohibit_channels:
            self.safe_print('Ignoring command in prohibit channel list')
            return #Music bot channel - - dont want anything to display
        
        if self.config.bound_channels and message.channel.id not in self.config.bound_channels and not message.channel.is_private:
            return  # if I want to log this I just move it under the prefix check

        '''
            http://stackoverflow.com/questions/2785755/how-to-split-but-ignore-separators-in-quoted-strings-in-python
        '''
        PATTERN = re.compile(r'''((?:[^ "']|"[^"]*"|'[^']*')+)''')
        print('pattern: ' + str(PATTERN.split(message_content)[1::2]))
        command, *args = message_content.split()  # Uh, doesn't this break prefixes with spaces in them (it doesn't, config parser already breaks them)
        command, *args = PATTERN.split(message_content)[1::2]
        command = command[len(self.config.command_prefix):].strip()
        self.safe_print('Command: (%s) and args: (%s)' % ((command), (args)))
        self.safe_print("[Command] {0.id}/{0.name} ({1})".format(message.author,
                                                                 message.content))
        handler = getattr(self, 'cmd_%s' % command, None)
        if not handler:
            responseMsg = self._suggest_cmds(message, command)
            if len(responseMsg) > 0:
                await self.safe_send_message(message.channel, responseMsg)
            self.safe_print('Command does not exist (%s) ' % command )
            return

        #TODO checking if from owner is done three times, check it once and move
        #the rest under the conditional
        if message.channel.is_private and command != 'joinserver' and message.author.id != self.config.owner_id:
            await self.send_message(message.channel, 'You cannot use this bot in private messages.')
            return

        if int(message.author.id) in self.blacklist and message.author.id != self.config.owner_id:
            self.safe_print("[User blacklisted] {0.id}/{0.name} ({1})".format(message.author, message_content))
            return

        elif self.config.white_list_check and int(
                message.author.id) not in self.whitelist and message.author.id != self.config.owner_id:
            self.safe_print("[User not whitelisted] {0.id}/{0.name} ({1})".format(message.author, message_content))
            return

        else:
            self.safe_print("[Command] {0.id}/{0.name} ({1})".format(message.author, message_content))

        user_permissions = self.permissions.for_user(message.author)

        argspec = inspect.signature(handler)
        params = argspec.parameters.copy()

        # noinspection PyBroadException
        try:
            handler_kwargs = {}
            if params.pop('message', None):
                handler_kwargs['message'] = message

            if params.pop('channel', None):
                handler_kwargs['channel'] = message.channel

            if params.pop('author', None):
                handler_kwargs['author'] = message.author

            if params.pop('server', None):
                handler_kwargs['server'] = message.server

            if params.pop('permissions', None):
                handler_kwargs['permissions'] = user_permissions

            if params.pop('user_mentions', None):
                handler_kwargs['user_mentions'] = list(map(message.server.get_member, message.raw_mentions))

            if params.pop('channel_mentions', None):
                handler_kwargs['channel_mentions'] = list(map(message.server.get_channel, message.raw_channel_mentions))

            if params.pop('voice_channel', None):
                handler_kwargs['voice_channel'] = message.server.me.voice_channel

            if params.pop('leftover_args', None):
                handler_kwargs['leftover_args'] = args

            args_expected = []
            for key, param in list(params.items()):
                doc_key = '[%s=%s]' % (key, param.default) if param.default is not inspect.Parameter.empty else key
                args_expected.append(doc_key)

                if not args and param.default is not inspect.Parameter.empty:
                    params.pop(key)
                    continue

                if args:
                    arg_value = args.pop(0)
                    handler_kwargs[key] = arg_value
                    params.pop(key)

            #TODO this should be moved to the individual commands. If the
            #command requires the user have a certain role, we check it there.
            #Now when we write a new command, if it applies to an existing role,
            #we simply have that command check if they have that role. If it
            #warrants a totally new role, then, and only then, do we add a new
            #role category to the config file.
            if message.author.id != self.config.owner_id:
                if user_permissions.command_whitelist and command not in user_permissions.command_whitelist:
                    raise PermissionsError(
                        "Reason: This command is not whitelisted for your group (%s)." % user_permissions.name)

                elif user_permissions.command_blacklist and command in user_permissions.command_blacklist:
                    raise PermissionsError(
                        "Reason: This command is blacklisted for your group (%s)." % user_permissions.name)

            if params:
                docs = getattr(handler, '__doc__', None)
                if not docs:
                    docs = 'Usage: {}{} {}'.format(
                        self.config.command_prefix,
                        command,
                        ' '.join(args_expected)
                    )

                docs = '\n'.join(l.strip() for l in docs.split('\n'))
                await self.safe_send_message(
                    message.channel,
                    '```\n%s\n```' % docs.format(command_prefix=self.config.command_prefix))
                return

            response = await handler(**handler_kwargs)
            if response and isinstance(response, Response):
                content = response.content
                if response.reply:
                    content = '%s, %s' % (message.author.mention, content)

                sentmsg = await self.safe_send_message(message.channel, content,
                                                       expire_in=response.delete_after)  # also_delete=message
                # TODO: Add options for deletion toggling

        except CommandError as e:
            await self.safe_send_message(message.channel, '```\n%s\n```' % e.message, expire_in=e.expire_in)

        except Exception as e:
            if self.config.debug_mode:
                await self.safe_send_message(message.channel, '```\n%s\n```' % traceback.format_exc())
            traceback.print_exc()
            
    async def on_voice_state_update(self, before, after):
        notImplementing = False
        _caseSense = True
        if notImplementing and after != None and after.voice_channel != None and after.voice_channel.id == self.config.tourneychannel and (before == None or before.voice_channel == None or before.voice_channel.name != after.voice_channel.name):
            member = after
            currentVoiceChannel = member.voice_channel
            if member.id != self.user.id:
                self.excelSpread.checkExpired()
                if self.excelSpread.getWS():
                    responseWKS = self.excelSpread.getWS()
                    validDup = self.excelSpread.checkDuplicateNames(member, self.excelSpread.getWS(), _caseSense)
                    validCheckedIn = self.excelSpread.checkUserCheckedInSpreadSheet(member, self.excelSpread.getWS(), _caseSense)
                    if validDup == True and validCheckedIn == False:
                        responseValid = self.excelSpread.checkUserExistInSpreadSheet(member, responseWKS, True)
                        if responseValid:
                            content = 'you are checked in.  You are able to leave now and head to an In-Game Channel in the meantime if the bot does not move you.'
                            content = '%s, %s' % (member.name, content)
                            await self.send_message(member, content)
                            Channel_ID = self.config.tourneylobby
                            ownerMember = discord.utils.find(lambda m: m.id == str(member.id), currentVoiceChannel.server.members)
                            try:
                                channel2 = discord.utils.find(lambda wantChannel: wantChannel.id == str(Channel_ID), currentVoiceChannel.server.channels)
                                if not channel2:
                                    if self.config.debug_mode:
                                        await self.send_message(member, 'Tried moving you to the ' + Channel_Name + ' voice channel.')
                                        await self.send_message(ownerMember, 'Tried moving you to the ' + Channel_Name + ' voice channel.')
                                else:
                                    finalChannel = channel2
                                    await self.move_member(member, finalChannel)
                                    if self.config.debug_mode:
                                        await self.send_message(member, 'Moved to the ' + str(finalChannel.name) + ' voice channel.')
                                        await self.send_message(ownerMember, 'Tried moving ' + str(member.name) + ' to the ' + str(finalChannel.name) + ' voice channel.')
                            except discord.errors.InvalidArgument:
                                if self.config.debug_mode:
                                    await self.send_message(member, 'The channel provided is not a voice channel.')
                                    await self.send_message(ownerMember, 'Tried moving ' + str(member.name) + ' to the ' + str(finalChannel.name) + ' voice channel but failed because of InvalidArgument.')
                            except discord.errors.HTTPException:
                                if self.config.debug_mode:
                                    await self.send_message(member, 'Moving the member failed.')
                                    await self.send_message(ownerMember, 'Tried moving ' + str(member.name) + ' to the ' + str(finalChannel.name) + ' voice channel but failed because of HTTPException.')
                            except discord.errors.Forbidden:
                                if self.config.debug_mode:
                                    await self.send_message(member, 'You do not have permissions to move the member.')
                                    await self.send_message(ownerMember, 'Tried moving ' + str(member.name) + ' to the ' + str(finalChannel.name) + ' voice channel but failed because of Forbidden.')
                        else:
                            content = 'you are not logged in or have registered for the tournament.'
                            content = '%s, %s' % (member.name, content)
                            await self.send_message(member, content)
                    elif(validDup == True and validCheckedIn):
                        Channel_ID = self.config.tourneylobby
                        channel2 = discord.utils.find(lambda wantChannel: wantChannel.id == str(Channel_ID), currentVoiceChannel.server.channels)
                        await self.move_member(member, channel2)
                    elif(validDup is None):
                        await self.send_message(member, 'You never signed up for this tournament')
                    else:
                        await self.send_message(member, 'Your name is entered twice, please contact a moderator or Tourney Assistant.')
                else:
                    content = 'the tournament has not opened up yet nor checkin is available at this time of request.'
                    content = '%s, %s' % (member.name, content)
                    await self.send_message(member, content)
                    currentVoiceChannel = member.voice_channel
                    if before == None:
                        Channel_ID = self.config.tourneylobby
                        channel = discord.utils.find(lambda wantChannel: wantChannel.id == str(Channel_ID), currentVoiceChannel.server.channels)
                        if channel is None:
                            await self.send_message(mesage.channel, 'The channel, ' + Channel_Name + ', does not exist or was typed incorrectly.')
                        else:
                            await self.move_member(member, channel)
                    else:
                        if before.voice_channel == None:
                            Channel_ID = self.config.tourneylobby
                            channel = discord.utils.find(lambda wantChannel: wantChannel.id == str(Channel_ID), currentVoiceChannel.server.channels)
                            if channel is None:
                                await self.send_message(mesage.channel, 'The channel, ' + Channel_Name + ', does not exist or was typed incorrectly.')
                            else:
                                await self.move_member(member, channel)
                        else:
                            await self.move_member(member, before.voice_channel)
        elif before is None or before is not None or after is None or after is not None or before.voice_channel == after.voice_channel:
            return  # they didn't move channels
        else:
            if after is not None:
                my_voice_channel = after.server.me.voice_channel
                if not my_voice_channel:
                    return

                if before.voice_channel == my_voice_channel:
                    joining = False
                elif after.voice_channel == my_voice_channel:
                    joining = True
                else:
                    return  # Not my channel
                moving = before == before.server.me

if __name__ == '__main__':
    bot = AutoLoginBot()
    bot.run()
