## Indigo plugin for IdleRPG (the IRC game)

import time
import logging
import socket

import iplug
import idlerpg

################################################################################
class Plugin(iplug.ThreadedPlugin):

    bots = dict()

    #---------------------------------------------------------------------------
    def validatePrefsConfigUi(self, values):
        errors = indigo.Dict()

        iplug.validateConfig_Int('threadLoopDelay', values, errors, min=60, max=3600)

        return ((len(errors) == 0), values, errors)

    #---------------------------------------------------------------------------
    def validateDeviceConfigUi(self, values, typeId, devId):
        errors = indigo.Dict()

        if typeId == "idlebot":
            self._validate_idlebot_config(values, errors)
        elif typeId == "info":
            self._validate_info_config(values, errors)

        return ((len(errors) == 0), values, errors)

    #---------------------------------------------------------------------------
    def deviceStartComm(self, device):
        iplug.ThreadedPlugin.deviceStartComm(self, device)
        typeId = device.deviceTypeId

        # start bots and track them...
        if typeId == "idlebot":
            bot = idlerpg.IdleBot(device.pluginProps)
            bot.on_status_update += self._on_bot_status_update

            self.bots[device.id] = bot
            bot.start()

    #---------------------------------------------------------------------------
    def deviceStopComm(self, device):
        iplug.ThreadedPlugin.deviceStopComm(self, device)
        typeId = device.deviceTypeId

        # stop bots as we close...
        if typeId == "idlebot" and device.id in self.bots:
            bot = self.bots[device.id]
            bot.stop()

            del self.bots[device.id]

    #---------------------------------------------------------------------------
    def runLoopStep(self):
        self.refresh_all_devices()

    #---------------------------------------------------------------------------
    def refresh_all_devices(self):
        self.refresh_player_status()

    #---------------------------------------------------------------------------
    def refresh_player_status(self):
        for device in indigo.devices.itervalues('self'):
            if device.enabled and device.configured:
                self._update_player_status(device)

    #---------------------------------------------------------------------------
    def _update_player_status(self, device):
        self.logger.debug(u'Updating: %s', device.name)

        typeId = device.deviceTypeId

        if typeId == 'info':
            self._update_player_info(device)
        elif typeId == 'idlebot':
            self._update_bot_status(device)

    #---------------------------------------------------------------------------
    def _update_player_info(self, device):
        address = device.pluginProps['address']
        player = idlerpg.PlayerInfo()

        if player.load_from_url(address):
            device.updateStateOnServer('online', player.is_online())
            device.updateStateOnServer('level', player.level)
            device.updateStateOnServer('username', player.username)
            device.updateStateOnServer('lastUpdatedAt', time.strftime('%c'))

            if player.is_online():
                device.updateStateOnServer('status', 'Online')
                device.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
            else:
                device.updateStateOnServer('status', 'Offline')
                device.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

    #---------------------------------------------------------------------------
    def _update_bot_status(self, device):
        bot = self.bots[device.id]

        # this method does not update the player status immediately...  instead,
        # it sends a request for status to the game engine.  this means that the
        # status will be picked up asynchronously by the on_status_update handler
        bot.request_status()

    #---------------------------------------------------------------------------
    def _on_bot_status_update(self, bot):
        # find the indigo device being updated
        device_id = self.bots.index(bot)

        self.logger.debug(u'bot status report: %s => ', bot.rpg_username, device_id)

        if device_id is None:
            self.logger.warn(u'Bot not found: %s', bot.rpg_username)
            return

        device = indigo.devices[device_id]
        if device is None:
            self.logger.error(u'Unknown error: device not found -- %s', device_id)
            return

        device.updateStateOnServer('online', bot.online)

        if bot.online:
            device.updateStateOnServer('level', bot.level)
            device.updateStateOnServer('nextLevel', str(bot.next_level))
            device.updateStateOnServer('status', 'Online')
            device.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
        else:
            device.updateStateOnServer('status', 'Offline')
            device.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

        device.updateStateOnServer('lastUpdatedAt', time.strftime('%c'))

    #---------------------------------------------------------------------------
    def _validate_info_config(self, values, errors):
        iplug.validateConfig_URL('address', values, errors, emptyOk=False)

    #---------------------------------------------------------------------------
    def _validate_idlebot_config(self, values, errors):
        iplug.validateConfig_Hostname('irc_server', values, errors, emptyOk=False)
        iplug.validateConfig_Int('irc_port', values, errors, min=1, max=65536)
        iplug.validateConfig_String('irc_passwd', values, errors, emptyOk=True)

        iplug.validateConfig_String('irc_nickname', values, errors, emptyOk=False)
        iplug.validateConfig_String('irc_fullname', values, errors, emptyOk=False)

        iplug.validateConfig_String('game_channel', values, errors, emptyOk=False)
        iplug.validateConfig_String('game_bot', values, errors, emptyOk=False)

        iplug.validateConfig_String('player_name', values, errors, emptyOk=False)
        iplug.validateConfig_String('player_passwd', values, errors, emptyOk=False)
        iplug.validateConfig_String('player_class', values, errors, emptyOk=False)

        # TODO set address property for display - uname@server
        uname = values['player_name']
        server = values['irc_server']

