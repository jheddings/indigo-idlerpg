## a very basic socket-level IRC client

# helpful resources:
# https://tools.ietf.org/html/rfc1459 - the full IRC spec
# https://pythonspot.com/building-an-irc-bot/
# https://stackoverflow.com/questions/2968408/how-do-i-program-a-simple-irc-bot-in-python
# https://stackoverflow.com/a/822788/197772 - socket line buffering
#
# https://github.com/jaraco/irc - full IRC client in Python
# consider using the client or simple bot implementation

import socket
import threading
import logging

# XXX should probably protect the receive buffer with a lock in case the caller
# is running multi-threaded (especially communicate() and quit())

# XXX may want to track connection state to help provide meaningful error messages

# XXX need more error handling for events and daemon execution

################################################################################
# a simple event-based IRC client
#
# users may wish to handle server messages directly, in which case, they must
# use next() or communicate() to handle server messages.  this will also cause
# events to dispatch appropriately and PING's to get answered
class Client:

    sock = None
    logger = None
    nick = None
    name = None

    recvbuf = ''
    daemon = None

    on_welcome = []  # function(msg)
    on_connect = []  # function()
    on_quit = []  # function(msg)
    on_error = []  # function(msg)
    on_ping = []  # function(txt)

    #---------------------------------------------------------------------------
    # Client initialization
    #   nick: the nickname used by this client
    #   name: the full name used by this client
    #   daemon: start a daemon to manage server messages
    def __init__(self, nick, name, daemon=True):
        self.logger = logging.getLogger('Plugin.idlerpg.IRC.Client')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.nick = nick
        self.name = name

        if (daemon):
            self.daemon = threading.Thread(name='IRC.Client.Daemon',
                                           target=self.communicate)
            self.daemon.setDaemon(True)

    #---------------------------------------------------------------------------
    # iterate over server responses - this iterator will block until data is read
    def __iter__(self): return self

    #---------------------------------------------------------------------------
    # send a message to the connected server followed by a newline
    #   msg: the message to send to the server
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
    # generate events from the given server message
    #   msg: the full text of the server message
    def _dispatcher(self, msg):

        if (msg is None):
            raise ValueError('message cannot be None')

        elif (msg.startswith(':')):
            txt = msg.split(':', 1)[1]
            self._handle_message(txt)

        elif (msg.startswith('PING')):
            txt = msg.split(':', 1)[1]
            self._on_ping(txt)

        elif (msg.startswith('ERROR')):
            txt = msg.split(':', 1)[1]
            self._on_error(txt)

        else:
            self.logger.warn(u'Unknown message -- %s', msg)

    #---------------------------------------------------------------------------
    # handle general server messages
    #   msg: the message from the server
    def _handle_message(self, msg):
        (origin, name, content) = msg.split(' ', 2)

        if (name == '001'):
            txt = msg.split(':', 1)[1]
            self._on_welcome(txt)

    #---------------------------------------------------------------------------
    # fire on_welcome event
    #   txt: the welcome message from the server
    def _on_welcome(self, txt):
        # notify on_welcome event handlers
        for handler in self.on_welcome:
            handler(self, txt)

    #---------------------------------------------------------------------------
    # handle PING commands
    #   txt: the server challenge text in the PING
    def _on_ping(self, txt):
        self._send('PONG :%s' % txt)

        # notify on_ping event handlers
        for handler in self.on_ping:
            handler(self, txt)

    #---------------------------------------------------------------------------
    # handle ERROR commands from the server - NOTE servers send ERROR on QUIT
    #   msg: error message supplied by the server
    def _on_error(self, msg):
        #XXX should we be logging this?
        self.logger.warn(msg)

        # notify on_error event handlers
        for handler in self.on_error:
            handler(self, msg)

    #---------------------------------------------------------------------------
    # connect this client to the given IRC server
    #   server: the address or hostname of the server
    #   port: the IRC port to connect to (default=6667)
    #   passwd: a password if required to access the server (default=None)
    def connect(self, server, port=6667, passwd=None):
        self.logger.debug(u'connecting to IRC server: %s:%d', server, port)
        self.sock.connect((server, port))

        # notify on_connect event handlers
        for handler in self.on_connect: handler(self)

        # startup the daemon if configured...
        if (self.daemon): self.daemon.start()

        if (passwd is not None):
            self._send('PASS %s' % passwd)

        self._send('NICK %s' % self.nick)
        self._send('USER %s - - %s' % (self.nick, self.name))

    #---------------------------------------------------------------------------
    # join this client to the given channel
    #   channel: the channel to join
    def join(self, channel):
        self._send('JOIN %s' % channel)

    #---------------------------------------------------------------------------
    # leave the given channel with a parting message
    #   channel: the channel to leave
    #   msg: a parting message
    def part(self, channel, msg):
        self._send('PART %s :%s' % (channel, msg))

    #---------------------------------------------------------------------------
    # send a private message to the intended recipient
    #   recip: the user or channel to receive the message
    #   msg: the text of the message
    def msg(self, recip, msg):
        self._send('PRIVMSG %s :%s' % (recip, msg))

    #---------------------------------------------------------------------------
    # set the mode of the given user or channel
    #   nick: the user nickname or channel name
    #   flags: the flags to set on the target
    def mode(self, nick, flags):
        self._send('MODE %s %s' % (nick, flags))

    #---------------------------------------------------------------------------
    # close the connection to the server and process all remaining server messages
    #   msg: an optional message to provide when quitting (default=None)
    def quit(self, msg=None):
        if (msg is None):
            self._send('QUIT')
        else:
            self._send('QUIT :%s' % msg)

        # wait for the deamon to exit...
        if (self.daemon is not None):
            self.daemon.join()

        # notify on_quit event handlers
        for handler in self.on_quit: handler(self, msg)

        self.sock.close()
        self.logger.debug(u': connection closed')

    #---------------------------------------------------------------------------
    # this method is blocking and should usually be called on a separate thread
    # NOTE events and PING's are not handled by this method
    def next(self): return self._recv()

    #---------------------------------------------------------------------------
    # this method is blocking and should usually be called on a separate thread
    # process server messages and generate events as needed until interrupted
    def communicate(self):
        for message in self:
            if (message is None):
                break

            self._dispatcher(message)

