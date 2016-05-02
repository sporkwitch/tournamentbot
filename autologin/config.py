import os
import os.path
import configparser

from discord import User as discord_User

class ConfigDefaults():
    username = None
    password = None

    owner_id = None
    command_prefix = '!'
    bound_channels = set()

    white_list_check = False
    auto_summon = False
    debug_mode = False

    options_file = 'config/login.ini'
    blacklist_file = 'config/blacklist.txt'
    whitelist_file = 'config/whitelist.txt'
    excel_file = 'config/excel/discord-auto-login-c480a18f18c9.json'
    challonge_file = 'config/challonge/challonge.ini'
    saying_file = 'config/jokes/funny.ini'

class ChallongeGroup:
    def __init__(self, name, section_data):
        self.name = name

        self.username = section_data.get('Username', fallback=None)
        self.Api_Key = section_data.get('API_Key', fallback=None)
    
class ChallongeConfig(object):
    def __init__(self, config_file):
        self.challonge_config_file = config_file
        self.challonge_config = configparser.ConfigParser()
        if not self.challonge_config.read(config_file):
            print('[config] Config file not found, copying example_challonge.ini')
            import os, shutil, traceback
             
            try:
                shutil.copy('config/challonge/example_challonge.ini', config_file)

                print("\nPlease configure config/challonge/example_challonge.ini and restart the bot.", flush=True)
                os._exit(1)

            except FileNotFoundError as e:
                traceback.print_exc()
                print("\nWhat happened to your configs?", flush=True)
                os._exit(2)

            except Exception as e:
                traceback.print_exc()
                print("\nUnable to copy config/challonge/example_challonge.ini to %s: %s" % (config_file, e), flush=True)
                os._exit(3)
        print('Reading challonge config file')
        self.challonge_default_group = ChallongeGroup('Default', self.challonge_config['Default'])
        self.challonge_groups = set()

        for section in self.challonge_config.sections():
            self.challonge_groups.add(ChallongeGroup(section, self.challonge_config[section]))
    
    def for_user(self, user):
        '''
        Returns the first PermissionGroup a user belongs to
        :param user: A discord User or Member object
        '''

        for group in self.challonge_groups:
            if str(user) in group.name:
                return group

        # The only way I could search for roles is if I add a `server=None` param and pass that too
        if type(user) == discord_User:
            return self.challonge_default_group

        return self.challonge_default_group

    def create_group(self, name, **kwargs):
        self.config.read_dict({name:kwargs})
        self.groups.add(PermissionGroup(name, self.config[name]))
        # TODO: Test this
    
    def configSectionsExist(self, _section):
        """ configSectionsExist: 
                If true, section does exist in config file
                If false, section does not exist in config file
        """
        return self.challonge_config.has_section(_section)

    def getBySection(self, _sectionName, _sectionContent):
        if(self.configSectionsExist(_sectionName)):
            if self.challonge_config.get(_sectionName, _sectionContent):
                arrayLst = self.challonge_config.get(_sectionName, _sectionContent)
                return arrayLst
            else:
                return "Option does not exist"
        else:
            return "Section does not exist"

class Organization():
    def __init__(self):
        self.organization = None
        self.name = None
        self.website = None
        self.rules = None
        self.checkin_guidelines = None
        self.faq = None
        self.twitch = None
        self.streamme = None
        self.server_id = None
    def setServerId(self, _id):
        self.server_id = _id
    def getServerId(self):
        return self.server_id
    def setOrganization(self, _organization):
        self.organization = _organization
    def getOrganization(self):
        return self.organization
    def setName(self, _name):
        self.name = _name
    def setWebsite(self, _website):
        self.website = _website
    def getWebsite(self):
        return self.website
    def setRules(self, _rules):
        self.rules = _rules
    def getRules(self):
        return self.rules
    def setCheckinGuidelines(self, _guide):
        self.checkin_guidelines = _guide
    def getCheckinGuidelines(self):
        return self.checkin_guidelines
    def setFAQ(self, _faq):
        self.faq = _faq
    def getFAQ(self):
        return self.faq
    def setTwitch(self, _twitch):
        self.twitch = _twitch
    def getTwitch(self):
        return self.twitch
    def setStreamme(self, _streamme):
        self.streamme = _streamme
    def getStreamme(self):
        return self.streamme

class Saying:
    def __init__(self, _saying_file):
        self.saying_file = _saying_file
        sayingConfig = configparser.ConfigParser()
        if not sayingConfig.read(_saying_file):
            print('[config] Config file not found, copying example_login.ini')
            import os, shutil, traceback
            try:
                shutil.copy('config/jokes/example_funny.ini', _saying_file)

                print("\nPlease configure config/jokes/funny.ini and restart the bot.", flush=True)
                os._exit(1)

            except FileNotFoundError as e:
                traceback.print_exc()
                print("\nWhat happened to your configs?", flush=True)
                os._exit(2)

            except Exception as e:
                traceback.print_exc()
                print("\nUnable to copy config/jokes/example_funny.ini to %s: %s" % (_saying_file, e), flush=True)
                os._exit(3)
        sayingConfig.read(_saying_file)
        self.nudes = sayingConfig.get('Sayings', 'nudes', fallback=0)
        self.config = sayingConfig
    def setNudes(self, _nudes):
        self.nudes = _nudes
    def getNudes(self):
        return self.nudes
    def writeFunnyConfigLst(self, PATH = 'config/jokes/funny.ini'):
        print("Path Name: " + PATH)
        #print("Path OS: " + str(os.path.dirname(PATH)))
        #print("Path exist: " + str(os.path.exists(os.path.dirname(PATH))))
        if not os.path.exists(os.path.dirname(PATH)):
            print("Path does not exists")
            os.makedirs(os.path.dirname(PATH), exist_ok=True)
            with open(PATH, 'w') as configfile:
                self.config.write(configfile)
        else:
            if not os.path.exists(PATH):
                with open(PATH, 'w') as configfile:
                    self.config.write(configfile)
            else:
                if not os.path.isfile(PATH) or not os.access(PATH, os.R_OK):
                    PATH = './config/jokes/funny.ini'
                with open(PATH, 'w+') as configfile:
                    self.config.write(configfile)

class Config(object):
    def __init__(self, config_file):
        self.config_file = config_file
        
        config = configparser.ConfigParser()
        if not config.read(config_file):
            print('[config] Config file not found, copying example_login.ini')
            import os, shutil, traceback
             
            try:
                shutil.copy('config/example_login.ini', config_file)

                print("\nPlease configure config/login.ini and restart the bot.", flush=True)
                os._exit(1)

            except FileNotFoundError as e:
                traceback.print_exc()
                print("\nWhat happened to your configs?", flush=True)
                os._exit(2)

            except Exception as e:
                traceback.print_exc()
                print("\nUnable to copy config/example_login.ini to %s: %s" % (config_file, e), flush=True)
                os._exit(3)
        print('Reading config file')
        #Maybe wrap these in a helper and change ConfigDefaults names to their config values
        config.read(config_file)
        
        #Config itself assigned
        self.config = config
        
        #Permissions
        self.username = config.get('Credentials', 'Username', fallback=ConfigDefaults.username)
        self.password = config.get('Credentials', 'Password', fallback=ConfigDefaults.password)
        self.owner_id = config.get('Permissions', 'OwnerID', fallback=ConfigDefaults.owner_id)
        
        #Chat Commands
        self.command_prefix = config.get('Chat', 'CommandPrefix', fallback=ConfigDefaults.command_prefix)
        self.bound_channels = config.get('Chat', 'BindToChannels', fallback=ConfigDefaults.bound_channels)
        
        #Bot Info
        self.auto_summon = config.getboolean('AutoLoginBot', 'AutoSummon', fallback=False)
        self.debug_mode = config.getboolean('AutoLoginBot', 'DebugMode', fallback=ConfigDefaults.debug_mode)
        self.white_list_check = config.getboolean('AutoLoginBot', 'WhiteListCheck', fallback=ConfigDefaults.white_list_check)
        
        #blacklist
        self.userslist = config.get('Security', 'users', fallback=None)
        self.userslist_check = config.getboolean('Security', 'whitelist', fallback=False)
        self.admins = config.get('Security', 'admins', fallback=self.owner_id)
        
        #Channels
        self.channels = config.get('Channel', 'channels', fallback=None)
        self.whitelistchannels = config.getboolean('Channel', 'whitelist', fallback=False)
        
        #Excel
        self.excel_email = config.get('Excel', 'Email', fallback=None)
        
        #Files
        self.blacklist_file = config.get('Files', 'BlacklistFile', fallback=ConfigDefaults.blacklist_file)
        self.whitelist_file = config.get('Files', 'WhitelistFile', fallback=ConfigDefaults.whitelist_file)
        self.excel_file = config.get('Files', 'ExcelFile', fallback=ConfigDefaults.excel_file)
        self.challonge_file = config.get('Files', 'ChallongeFile', fallback=ConfigDefaults.challonge_file)
        self.saying_file = config.get('Files', 'SayingFile', fallback=ConfigDefaults.saying_file)

        #Organization
        self.organization = Organization()
        self.organization.organization = config.get('Organization',
                                                    'organization',
                                                    fallback=None)
        self.organization.name = config.get('Organization',
                                            'organization_name',
                                            fallback=None)
        self.organization.website = config.get('Organization',
                                               'organization_website',
                                               fallback=None)
        self.organization.rules = config.get('Organization',
                                             'organization_website_rules',
                                             fallback=None)
        self.organization.checkin_guidelines = config.get('Organization',
                                                          'organization_checkin_guidelines',
                                                          fallback=None)
        self.organization.faq = config.get('Organization',
                                           'organization_faq',
                                           fallback=None)
        self.organization.twitch = config.get('Organization',
                                              'organization_twitch',
                                              fallback=None)
        self.organization.streamme = config.get('Organization',
                                                'organization_streamme',
                                                fallback=None)
        self.organization.server_id = config.get('Organization',
                                                 'organization_server_id',
                                                 fallback=None)
        self.organization.prohibit_channels = config.get('Organization',
                                                         'organization_prohibit_channels',
                                                         fallback = set())
        #Tournament
        self.casters = self.manipulateSettings('Tournament', 'casters')#config.get('Tournament', 'casters', fallback=None)
        self.caster1 = config.get('Tournament', 'caster1', fallback=None)
        self.caster2 = config.get('Tournament', 'caster2', fallback=None)
        self.caster3 = config.get('Tournament', 'caster3', fallback=None)
        self.tourneychannel = config.get('Tournament', 'tourneychannel', fallback=None)
        self.tourneylobby = config.get('Tournament', 'lobby', fallback=None)
        
        #Funny catch phrases
        self.funny = Saying(self.saying_file)
        
        # Validation logic for bot settings.
        if not self.username or not self.password:
            raise ValueError('A username or password was not specified in the configuration file.')

        if not self.owner_id:
            raise ValueError("An owner is not specified in the configuration file")
        
        if self.organization.prohibit_channels:
            try:
                self.organization.prohibit_channels = set(x for x in self.organization.prohibit_channels.split() if x)
            except:
                print('[Warning] ProhibitChannels data invalid, will not bind to any channels')
                self.organization.prohibit_channels = set()
        if self.bound_channels:
            try:
                self.bound_channels = set(x for x in self.bound_channels.split() if x)
            except:
                print("[Warning] BindToChannels data invalid, will not bind to any channels")
                self.bound_channels = set()
        
        
    def setCommandPrefix(self, _prefix):
        self.command_prefix = _prefix

    def getCommandPrefix(self):
        return self.command_prefix

    def discord_user_email(self):
        """ email: the discord login email address of the bot """
        return self.username

    def discord_user_password(self):
        """ password: the bot's discord password """
        return self.password
        
    def UserWhiteList(self):
        """ 
        whitelist: If true, only Users and Admins will be able to issue non-admin
        commands to the bot; if false, Users are prohibited from issuing commands
        but all others may issue non-admin commands. Default: True
        """
        return self.userslist_check #config.get("Security", "whitelist")

    def userList(self):
        """ Users: A list of users; behaviour determined by whitelist setting """
        return self.userslist #config.get("Security", "Users")

    def adminList(self):
        """ Admins: A list of users who will have admin access to the bot """
        return self.admins #config.get("Security", "Admins")
        
    def channelList(self):
        """ Channel: A list of channels accessable to the bot """
        return self.channels #config.get("Channel", "channels")
        
    def getTourneyChannel(self):
        """ Channel: the Tourney Channel id """
        return self.tourneychannel #config.get('Tournament', 'tourneychannel')

    def casterLst(self):
        return self.casters #config.get('Tournament', 'casters')

    def getOwner(self):
        """ User: the owner of the bot """
        return self.owner_id #getOwnerId("login", "ownerId")

    def getLobbyChannel(self):
        """ Channel: the lobby Channel id """
        return self.tourneylobby #config.get('Tournament', 'lobby')

    def getDebugBool(self):
        return self.debug_mode #config.get('Debug', 'debugToggle')

    def ChannelWhiteList(self):
        """
        whitelist: If true, bot will join the channels listed, if False, will join all except those listed
        """
        return self.whitelistchannels #config.get("Channel", "whitelist")

    def configSectionList(self):
        return self.config.sections()
        
    def configSectionsExist(self, _section):
        """ configSectionsExist: 
                If true, section does exist in config file
                If false, section does not exist in config file
        """
        return self.config.has_section(_section)

    
    def getSettings(self, PATH='./config/login.ini'):
        """ Reads in the config file """
        self.__init__(PATH)
    
    def manipulateSettings(self, _sectionName, _sectionContent):
        if(self.configSectionsExist(_sectionName)):
            if self.config.get(_sectionName, _sectionContent):
                arrayLst = self.config.get(_sectionName, _sectionContent).split("\n")
                #pop first arrayLst
                arrayLst.pop(0)
                return arrayLst
            else:
                print('Option is not existent')
                return None
        else:
            print('Section is not existing')
            return None

    def getOwnerId(_sectionName, _sectionContent):
        if(configSectionsExist(_sectionName)):
            if self.config.get(_sectionName, _sectionContent):
                return self.config.get(_sectionName, _sectionContent)
            else:
                return "Option does not exist"
        else:
            return "Section does not exist"
            
    def addToList(_sectionName, _sectionContent, _contentID):
        #validating to see if sectionName and sectionContent exist
        manSectionHolder = manipulateSettings(_sectionName, _sectionContent)
        if type(manSectionHolder) is list:
            #valid response
            if _contentID not in manSectionHolder:
                manSectionHolder.append(_contentID)
                config.set(_sectionName, _sectionContent, "\n".join(manSectionHolder))
                return "Configuration has been modified and has been overwritten."
            else:
                if(_sectionContent == ("Channels")):
                    return "<#" + _contentID + "> already exists in the " + _sectionContent + " list."
                else:
                    return "<@" + _contentID + "> already exists in the " + _sectionContent + " list."
        else:
            return manSectionHolder
        #return "Validating to see if ID is already in list"
    def removeToList(_sectionName, _sectionContent,_contentID):
        manSectionHolder = manipulateSettings(_sectionName, _sectionContent)
        if type(manSectionHolder) is list:
            #valid response
            if (_contentID in manSectionHolder):
                userOwnerId = getOwnerId("login", "ownerId")
                if userOwnerId == _contentID and (_sectionContent == ("Admins")):
                    return "<@" + userOwnerId + "> cannot be removed from the " + _sectionContent + " list due to ownership of the bot."
                else:
                    manSectionHolder.remove(_contentID)
                    config.set(_sectionName, _sectionContent, "\n".join(manSectionHolder))
                return "Configuration has been modified and has been overwritten."
            else:
                if(_sectionContent == ("Channels")):
                    return "<#" + _contentID + "> is not in the " + _sectionContent + " list."
                else:
                    return "<@" + _contentID + "> is not in the " + _sectionContent + " list."
        else:
            return manSectionHolder

    def writeConfigLst(PATH = '.\config\login.ini'):
        #print("Path Name: " + PATH)
        #print("Path OS: " + str(os.path.dirname(PATH)))
        #print("Path exist: " + str(os.path.exists(os.path.dirname(PATH))))
        if not os.path.exists(os.path.dirname(PATH)):
            print("Path does not exists")
            os.makedirs(os.path.dirname(PATH), exist_ok=True)
            with open(PATH, 'w') as configfile:
                config.write(configfile)
        else:
            if not os.path.exists(PATH):
                with open(PATH, 'w') as configfile:
                    config.write(configfile)
            else:
                if not os.path.isfile(PATH) or not os.access(PATH, os.R_OK):
                    PATH = '.\config\login.ini'
                with open(PATH, 'w+') as configfile:
                    config.write(configfile)
