# pgxnclient Makefile
#
# Copyright (C) 2011 Daniele Varrazzo
#
# This file is part of the PGXN client

.PHONY: env sdist upload docs

PYTHON := python$(PYTHON_VERSION)
PYTHON_VERSION ?= $(shell $(PYTHON) -c 'import sys; print ("%d.%d" % sys.version_info[:2])')
ENV_DIR = $(shell pwd)/env/py-$(PYTHON_VERSION)
ENV_BIN = $(ENV_DIR)/bin
ENV_LIB = $(ENV_DIR)/lib
BUILD_DIR = $(shell pwd)/build/lib.$(PYTHON_VERSION)
EASY_INSTALL ?= easy_install-$(PYTHON_VERSION)
EASY_INSTALL_CMD = PYTHONPATH=$(ENV_LIB) $(EASY_INSTALL) -d $(ENV_LIB) -s $(ENV_BIN)


# Install development dependencies.
# For python 3, use something like:
#     make PYTHON=python3.1 EASY_INSTALL=easy_install3 env
# still, unittest2 shouldn't be installed.

build:
	PYTHONPATH=$(ENV_LIB) $(PYTHON) setup.py build --build-lib $(BUILD_DIR)

env:
	mkdir -p $(ENV_BIN)
	mkdir -p $(ENV_LIB)
	$(EASY_INSTALL_CMD) unittest2
	$(EASY_INSTALL_CMD) mock
ifeq ($(PYTHON_VERSION),2.4)
	$(EASY_INSTALL_CMD) "simplejson==2.0.9"
endif
ifeq ($(PYTHON_VERSION),2.5)
	$(EASY_INSTALL_CMD) simplejson
endif

check: build
	PYTHONPATH=$(BUILD_DIR):$(ENV_LIB) $(PYTHON) setup.py test

sdist:
	$(PYTHON) setup.py sdist --formats=gztar,zip

upload:
	$(PYTHON) setup.py sdist --formats=gztar,zip upload

docs:
	$(MAKE) -C docs

clean:
	rm -rf build pgxnclient.egg-info
	$(MAKE) -C docs $@

