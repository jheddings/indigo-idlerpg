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

        return ((len(errors) == 0), values, errors)

    #---------------------------------------------------------------------------
    def deviceStartComm(self, device):
        iplug.ThreadedPlugin.deviceStartComm(self, device)
        # update device status

    #---------------------------------------------------------------------------
    def deviceStopComm(self, device):
        iplug.ThreadedPlugin.deviceStopComm(self, device)

    #---------------------------------------------------------------------------
    def loadPluginPrefs(self, prefs):
        iplug.ThreadedPlugin.loadPluginPrefs(self, prefs)

    #---------------------------------------------------------------------------
    def runLoopStep(self):
        self.refreshAllDevices()

    #---------------------------------------------------------------------------
    def refreshAllDevices(self):
        self.refreshPlayerStatus()

    #---------------------------------------------------------------------------
    def refreshPlayerStatus(self):
        for device in indigo.devices.itervalues('self'):
            if device.enabled:
                self._update(device)
            else:
                self.logger.debug(u'Device disabled: %s', device.name)

    #---------------------------------------------------------------------------
    def _update(self, device):
        self.logger.debug(u'Updating: %s', device.name)

        typeId = device.deviceTypeId

        if typeId == 'player':
            self._updatePlayerInfo(device)

    #---------------------------------------------------------------------------
    def _updatePlayerInfo(self, device):
        url = device.pluginProps['url']
        self.logger.debug(u'Updating from URL: %s', url)

        player = idlerpg.Player()

        if (player.load_from_url(url)):
            device.updateStateOnServer('online', player.isOnline())
            device.updateStateOnServer('level', player.level)
            device.updateStateOnServer('username', player.username)
            device.updateStateOnServer('lastUpdatedAt', time.strftime('%c'))

            if (player.isOnline()):
                device.updateStateOnServer('status', 'Active')
            else:
                device.updateStateOnServer('status', 'Inactive')

