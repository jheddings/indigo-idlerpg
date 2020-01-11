## wrapper for reading idlerpg data
# http://idlerpg.net/source.php

import logging

import irc

################################################################################
class PlayerInfo():

    #---------------------------------------------------------------------------
    def __init__(self):
        self.logger = logging.getLogger('Plugin.idlerpg.PlayerInfo')

        self.username = None
        self.online = None
        self.ttl = None
        self.level = None

    #---------------------------------------------------------------------------
    def load_from_url(self, url):
        if (url is None):
            self.logger.warn(u'url is empty')
            return None

        self.logger.debug(u'loading player info from url: %s', url)
        player_data = self._get_url(url)
        return self.load_from_string(player_data)

    #---------------------------------------------------------------------------
    def load_from_file(self, path):
        if (path is None):
            self.logger.warn(u'path is empty')
            return None

        self.logger.debug(u'loading player info from file: %s', path)
        player_data = self._read_file(path)
        return self.load_from_string(player_data)

    #---------------------------------------------------------------------------
    def load_from_string(self, xml):
        import xml.etree.ElementTree as ElementTree

        if (xml is None):
            self.logger.warn(u'data is empty')
            return None

        self.logger.debug(u'loading player info from data: %d bytes', len(xml))

        # TODO consider using xmljson to parse xml into python dict

        try:
            root = ElementTree.fromstring(xml)
            return self.load_from_document(root)
        except ElementTree.ParseError as err:
            self.logger.error(u'XML Error: %s', err)

        return False

    #---------------------------------------------------------------------------
    def load_from_document(self, doc):
        if (doc is None):
            self.logger.warn(u'document is empty')
            return None

        self.logger.debug(u'loading player info from XML document: %s', doc.tag)

        # parse basic info
        self.username = self._parse_text(doc, 'username')
        if (self.username == None): return False

        self.online = self._parse_text(doc, 'online')
        if (self.online == None): return False

        self.level = self._parse_text(doc, 'level')
        if (self.level == None): return False

        self.ttl = self._parse_text(doc, 'ttl')
        if (self.ttl == None): return False

        # load positon as a tuple
        xpos = self._parse_text(doc, 'xpos')
        if (xpos == None): return False

        ypos = self._parse_text(doc, 'ypos')
        if (ypos == None): return False

        self.pos = (xpos, ypos)

        # load items & penalties
        self.penalty = self._parse_dict(doc, 'penalties')
        if (self.penalty == None): return False

        self.items = self._parse_dict(doc, 'items')
        if (self.items == None): return False

        return True

    #---------------------------------------------------------------------------
    def _parse_value(self, val):
        if (val is None):
            return None

        if (val.isdigit()):
            return int(val)

        return val

    #---------------------------------------------------------------------------
    def _parse_text(self, doc, field):
        text = doc.findtext(field)
        self.logger.debug(u'%s[%s] = %s', doc.tag, field, text)
        return self._parse_value(text)

    #---------------------------------------------------------------------------
    def _parse_dict(self, doc, field):
        obj = dict()

        for node in doc.find(field):
            self.logger.debug(u'%s[%s/%s] = %s', doc.tag, field, node.tag, node.text)
            obj[node.tag] = self._parse_value(node.text)

        return obj

    #---------------------------------------------------------------------------
    def is_online(self): return (self.online == 1)

    #---------------------------------------------------------------------------
    def _read_file(self, path):
        if (path is None): return None

        data = None

        try:
            with open(path) as fh:
                data = fh.read()
        except IOError as err:
            self.logger.error(u'%s', err)

        return data

    #---------------------------------------------------------------------------
    def _get_url(self, url):
        import urllib2

        if (url is None): return None
        self.logger.debug(u'downloading data: %s', url)

        data = None

        try:
            resp = urllib2.urlopen(url)
            self.logger.debug(u'HTTP: %d', resp.getcode())

            data = resp.read()
            self.logger.debug(u'downloaded %d bytes', len(data))

        except urllib2.HTTPError as err:
            self.logger.warn(u'HTTP Error (%d): %s', err.code, err.reason)

        except urllib2.URLError as err:
            self.logger.warn(u'URL Error: %s', err.reason)

        return data

################################################################################
class IdleBot():

    #---------------------------------------------------------------------------
    def __init__(self, conf):
        self.logger = logging.getLogger('Plugin.idlerpg.IdleBot')

        self.irc_server = conf['irc_server']
        self.irc_port = int(conf['irc_port'])
        #self.irc_passwd = conf['irc_passwd']

        self.irc_nickname = conf['irc_nickname']
        self.irc_fullname = conf['irc_fullname']

        self.rpg_channel = conf['game_channel']
        self.rpg_bot = conf['game_bot']

        self.rpg_username = conf['player_name']
        self.rpg_password = conf['player_passwd']
        self.rpg_class = conf['player_class']

        self.online = False
        self.next = None
        self.level = None

        self.client = irc.Client(self.irc_nickname, self.irc_fullname)
        self.client.on_welcome += self.on_welcome
        self.client.on_privmsg += self.on_privmsg

    #---------------------------------------------------------------------------
    def on_welcome(self, client, txt):
        self.logger.debug('welcome received... joining IdleRPG')

        client.join(self.rpg_channel)

        # TODO register if needed - maybe put a button on the device settings?
        #client.msg('bot', 'REGISTER {0} {1} {2}'.format(username, password, faction))

        login_msg = 'LOGIN ' + self.rpg_username + ' ' + self.rpg_password
        client.msg(self.rpg_bot, login_msg)

    #---------------------------------------------------------------------------
    def on_privmsg(self, client, origin, recip, txt):
        self.logger.debug('privmsg - %s:%s => %s', origin, recip, txt)

    #---------------------------------------------------------------------------
    def start(self):
        self.client.connect(self.irc_server, port=self.irc_port)

    #---------------------------------------------------------------------------
    def stop(self):
        if self.client.connected is True:
            # parting causes quite a penalty...
            self.client.part(self.rpg_channel, 'goodbye')

            # close everything up
            self.client.quit()

    #---------------------------------------------------------------------------
    def update(self):
        if self.client.connected is not True:
            return False

        # this will cause the server to respond for parsing in on_privmsg
        self.client.msg('bot', 'WHOAMI')

        return True

