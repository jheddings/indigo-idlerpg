## very basic IRC client

# helpful resources:
# https://github.com/jaraco/irc - full IRC client in Python
# https://pythonspot.com/building-an-irc-bot/
# https://stackoverflow.com/questions/2968408/how-do-i-program-a-simple-irc-bot-in-python
# https://stackoverflow.com/a/822788/197772 - socket line buffering

import socket
import logging

# XXX should commands like JOIN and PART wait until the server acks before returning?

################################################################################
class Client:

    sock = None
    logger = None
    nick = None
    name = None

    recvbuf = ''

    #---------------------------------------------------------------------------
    def __init__(self, nick, name):
        self.logger = logging.getLogger('Plugin.idlerpg.IRC')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.nick = nick
        self.name = name

    #---------------------------------------------------------------------------
    # iterate over server responses - this iterator will block until data is read
    def __iter__(self):
        return self

    #---------------------------------------------------------------------------
    # send one line of text
    def _send(self, msg):
        self.logger.debug(u'> %s', msg)
        self.sock.sendall("%s\n" % msg)

    #---------------------------------------------------------------------------
    # receive one line of text
    def _recv(self):
        text = None

        # do the newline check first to ensure any new data is processed after receiving

        # XXX this doesn't seem like the most efficient way to read and process
        # new lines...  having to look for a \n twice seems redundant

        # if there are no lines in the buffer, we need more data
        if (not "\n" in self.recvbuf):
            self.logger.debug(u': no lines in buffer; reading data from socket')

            # receive a block of data at a time
            more = self.sock.recv(4096)
            if (more is not None and len(more) > 0):
                self.recvbuf += more

        # if there is a newline in the buffer, we can process the next line
        if ("\n" in self.recvbuf):
            self.logger.debug(u': reading next line from buffer; recvbuf:%d', len(self.recvbuf))

            (text, newbuf) = self.recvbuf.split("\n", 1)
            text = text.strip()
            self.recvbuf = newbuf

            if (len(text) == 0):
                text = None
            else:
                self.logger.debug(u'< %s', text)

        return text

    #---------------------------------------------------------------------------
    # processes the next server response and only returns the reply code
    def _next_code(self):
        line = self.next()

        if (line is not None and line.startswith(':')):
            return line.split(' ', 2)[1]

        return None

    #---------------------------------------------------------------------------
    def join(self, channel):
        self._send('JOIN %s' % channel)

    #---------------------------------------------------------------------------
    def part(self, channel, msg):
        self._send('PART %s :%s' % (channel, msg))

    #---------------------------------------------------------------------------
    def connect(self, server, port=6667, passwd=None):
        self.logger.debug(u'connecting to IRC server: %s:%d', server, port)
        self.sock.connect((server, port))

        if (passwd is not None):
            self._send('PASS %s' % passwd)

        self._send('NICK %s' % self.nick)
        self._send('USER %s - - %s' % (self.nick, self.name))

    #---------------------------------------------------------------------------
    def msg(self, recip, msg):
        self._send('PRIVMSG %s :%s' % (recip, msg))

    #---------------------------------------------------------------------------
    def mode(self, nick, flags):
        self._send('MODE %s %s' % (nick, flags))

    #---------------------------------------------------------------------------
    def quit(self, msg=None):
        if (msg is None):
            self._send('QUIT')
        else:
            self._send('QUIT :%s' % msg)

        # read all remaining data from server
        while self.next(): pass

        self.sock.close()

    #---------------------------------------------------------------------------
    # this method blocks (handling PING) until it sees the welcome message
    # NOTE if the connection is already registered, this will block forever!
    def register(self, clearGreetings=True):
        reply = None

        # TODO probably need some error checking here...

        # read until RPL_WELCOME (001)
        while (not reply == '001'):
            self.logger.debug(u': waiting for welcome banner')
            reply = self._next_code()

        # XXX the only problem with clearing all greeting messages is that the
        # client could end up blocking for a very long time if the server just
        # happens to stop sending messages right after the last greeting...
        # this approach assumes there will always be another reply after the last
        # 0xx reply from the server

        # read until end of greetings...
        if (clearGreetings):
            self.logger.debug(u': clearing all greetings >>>')
            while (reply.startswith('0')):
                reply = self._next_code()
            self.logger.debug(u': greeting messages cleared <<<')

        # what about MOTD (376) or no MOTD (422) ?

    #---------------------------------------------------------------------------
    # this method is blocking and should usually be called on a separate thread
    def next(self):
        reply = self._recv()

        # TODO are there other responses we should handle automatically?

        if (reply is not None and reply.startswith('PING')):
            msg = reply.split(':', 1)[1]
            self._send('PONG :%s' % msg)

        return reply

