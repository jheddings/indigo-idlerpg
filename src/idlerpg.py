## wrapper for reading idlerpg data
# http://idlerpg.net/source.php

import logging
import urllib2

import irc

import xml.etree.ElementTree as ElementTree

################################################################################
class IdleBot():

    #---------------------------------------------------------------------------
    def __init__(self):
        self.logger = logging.getLogger('Plugin.idlerpg.IdleBot')

        self.online = None

    #---------------------------------------------------------------------------
    def is_online(self): return (self.online == 1)

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
    def __init__(self, client):
        self.logger = logging.getLogger('Plugin.idlerpg.IdleBot')

        self.online = False
        self.level = None

        self.username = None
        self.password = None
        self.faction = None

        self.client = client

    #---------------------------------------------------------------------------
    def start():
        pass

        # XXX something like client.connect here...

    #---------------------------------------------------------------------------
    def stop():
        pass

    #---------------------------------------------------------------------------
    def update():
        pass

        # XXX ask the bot "whoami" here and parse the results

