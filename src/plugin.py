## Indigo plugin for IdleRPG (the IRC game)

import time
import logging
import socket

import iplug
import idlerpg

################################################################################
class Plugin(iplug.ThreadedPlugin):

    #---------------------------------------------------------------------------
    def validatePrefsConfigUi(self, values):
        errors = indigo.Dict()

        iplug.validateConfig_Int('threadLoopDelay', values, errors, min=60, max=3600)

        return ((len(errors) == 0), values, errors)

    #---------------------------------------------------------------------------
    def validateDeviceConfigUi(self, values, typeId, devId):
        errors = indigo.Dict()

        if (typeId == "idlebot"):
            self._validate_idlebot_config(values, errors)
        elif (typeId == "info"):
            self._validate_info_config(values, errors)

        return ((len(errors) == 0), values, errors)

    #---------------------------------------------------------------------------
    def deviceStartComm(self, device):
        iplug.ThreadedPlugin.deviceStartComm(self, device)

    #---------------------------------------------------------------------------
    def deviceStopComm(self, device):
        iplug.ThreadedPlugin.deviceStopComm(self, device)

    #---------------------------------------------------------------------------
    def runLoopStep(self):
        self.refresh_all_devices()

    #---------------------------------------------------------------------------
    def refresh_all_devices(self):
        self.refresh_player_status()

    #---------------------------------------------------------------------------
    def refresh_player_status(self):
        for device in indigo.devices.itervalues('self'):
            if (device.enabled and device.configured):
                self._update(device)

    #---------------------------------------------------------------------------
    def _update(self, device):
        self.logger.debug(u'Updating: %s', device.name)

        typeId = device.deviceTypeId

        if typeId == 'info':
            self._update_player_info(device)

    #---------------------------------------------------------------------------
    def _update_player_info(self, device):
        address = device.pluginProps['address']
        player = idlerpg.PlayerInfo()

        if (player.load_from_url(address)):
            device.updateStateOnServer('online', player.is_online())
            device.updateStateOnServer('level', player.level)
            device.updateStateOnServer('username', player.username)
            device.updateStateOnServer('lastUpdatedAt', time.strftime('%c'))

            if (player.is_online()):
                device.updateStateOnServer('status', 'Online')
                device.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
            else:
                device.updateStateOnServer('status', 'Offline')
                device.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

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

