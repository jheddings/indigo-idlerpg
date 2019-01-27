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

        # TODO

        return ((len(errors) == 0), values, errors)

    #---------------------------------------------------------------------------
    def runLoopStep(self):
        self.refreshAllDevices()

    #---------------------------------------------------------------------------
    def refreshAllDevices(self):
        self.refreshPlayerStatus()

    #---------------------------------------------------------------------------
    def refreshPlayerStatus(self):
        for device in indigo.devices.itervalues('self'):
            if (device.enabled and device.configured):
                self._update(device)

    #---------------------------------------------------------------------------
    def _update(self, device):
        self.logger.debug(u'Updating: %s', device.name)

        typeId = device.deviceTypeId

        if typeId == 'info':
            self._updatePlayerInfo(device)

    #---------------------------------------------------------------------------
    def _updatePlayerInfo(self, device):
        address = device.pluginProps['address']
        player = idlerpg.Player()

        if (player.load_from_url(address)):
            device.updateStateOnServer('online', player.isOnline())
            device.updateStateOnServer('level', player.level)
            device.updateStateOnServer('username', player.username)
            device.updateStateOnServer('lastUpdatedAt', time.strftime('%c'))

            if (player.isOnline()):
                device.updateStateOnServer('status', 'Online')
                device.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
            else:
                device.updateStateOnServer('status', 'Offline')
                device.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

