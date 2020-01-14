# Makefile for Indigo IdleRPG plugin

PLUGIN_NAME = IdleRPG
DEPLOY_HOST = jarvis@lcars.local

include iplug/iplug.mk

################################################################################
build_post:
	$(COPY) $(BASEDIR)/idlebot/src/irc.py "$(PLUGIN_SRC)"
	$(COPY) $(BASEDIR)/idlebot/src/idlerpg.py "$(PLUGIN_SRC)"

