# pgxnclient Makefile
#
# Copyright (C) 2011 Daniele Varrazzo
# 
# This file is part of the PGXN client

.PHONY: env sdist upload

PYTHON := python$(PYTHON_VERSION)
PYTHON_VERSION ?= $(shell $(PYTHON) -c 'import sys; print ("%d.%d" % sys.version_info[:2])')
ENV_DIR = $(shell pwd)/env
ENV_BIN = $(ENV_DIR)/bin
ENV_LIB = $(ENV_DIR)/lib
EASY_INSTALL = PYTHONPATH=$(ENV_LIB) $(ENV_BIN)/easy_install-$(PYTHON_VERSION) -d $(ENV_LIB) -s $(ENV_BIN)
EZ_SETUP = $(ENV_BIN)/ez_setup.py

check:
	PYTHONPATH=.:$(ENV_LIB) $(ENV_BIN)/unit2 discover


# Install development dependencies.

env: easy_install
	mkdir -p $(ENV_BIN)
	mkdir -p $(ENV_LIB)
	$(EASY_INSTALL) unittest2
	$(EASY_INSTALL) mock

easy_install: ez_setup
	PYTHONPATH=$(ENV_LIB) $(PYTHON) $(EZ_SETUP) -d $(ENV_LIB) -s $(ENV_BIN) setuptools

ez_setup:
	mkdir -p $(ENV_BIN)
	mkdir -p $(ENV_LIB)
	wget -O $(EZ_SETUP) http://peak.telecommunity.com/dist/ez_setup.py

sdist:
	$(PYTHON) setup.py sdist --manifest-only
	$(PYTHON) setup.py sdist --force-manifest --formats=gztar,zip

upload:
	$(PYTHON) setup.py sdist --formats=gztar,zip upload

