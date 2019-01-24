## wrapper for reading idlerpg data

import logging
import urllib2
import threading

import xml.etree.ElementTree as ElementTree

################################################################################
class Player():

    #---------------------------------------------------------------------------
    def __init__(self):
        self.logger = logging.getLogger('Plugin.idlerpg.Player')
        self.lock = threading.Lock()

        self.username = None
        self.online = None

    #---------------------------------------------------------------------------
    def load_from_url(self, url):
        self.logger.debug(u'loading player info from url: %s', url)
        player_data = self._get_url(url)
        return self.load_from_string(player_data)

    #---------------------------------------------------------------------------
    def load_from_file(self, path):
        self.logger.debug(u'loading player info from file: %s', path)
        player_data = self._read_file(path)
        return self.load_from_string(player_data)

    #---------------------------------------------------------------------------
    def load_from_string(self, xml):
        self.logger.debug(u'loading player info from data: %d bytes', len(xml))

        try:
            root = ElementTree.fromstring(xml)
            return self.load_from_document(root)
        except ElementTree.ParseError as err:
            self.logger.error(u'XML Error: %s', err)

        return False

    #---------------------------------------------------------------------------
    def load_from_document(self, doc):
        self.logger.debug(u'loading player info from XML document: %s', doc.tag)

        self.username = self._find_field_str(doc, 'username')
        if (self.username == None): return False

        self.online = self._find_field_int(doc, 'online')
        if (self.online == None): return False

        self.level = self._find_field_int(doc, 'level')
        if (self.level == None): return False

        return True

    #---------------------------------------------------------------------------
    def _find_field_str(self, doc, field):
        text = doc.findtext(field)
        self.logger.debug(u'%s[%s] = %s', doc.tag, field, text)

        return text

    #---------------------------------------------------------------------------
    def _find_field_int(self, doc, field):
        text = self._find_field_str(doc, field)

        if (text is None): return None
        if (not text.isdigit()): return None

        return int(text)

    #---------------------------------------------------------------------------
    def isOnline(self): return (self.online == 1)

    #---------------------------------------------------------------------------
    def _read_file(self, path):
        data = None

        with open(path) as fh:
            data = fh.read()

        return data

    #---------------------------------------------------------------------------
    def _get_url(self, url):
        self.logger.debug(u'downloading data: %s', url)

        data = None

        try:
            resp = urllib2.urlopen(url)
            self.logger.debug(u'HTTP: %d', resp.getcode())

            data = resp.read()
            self.logger.debug(u'downloaded %d bytes', len(data))

        except urllib2.HTTPError as err:
            self.logger.warn(u'HTTP Error: %s', err.reason)

        return data

