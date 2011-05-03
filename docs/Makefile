# PGXN Client -- documentation makefile
#
# Use 'make env', then 'make html' to build the HTML documentation
#
# Copyright (C) 2011 Daniele Varrazzo

PYTHON := python$(PYTHON_VERSION)
PYTHON_VERSION ?= $(shell $(PYTHON) -c 'import sys; print ("%d.%d" % sys.version_info[:2])')
BUILD_DIR = $(shell pwd)/build/lib.$(PYTHON_VERSION)
ENV_DIR = $(shell pwd)/env/py-$(PYTHON_VERSION)
ENV_BIN = $(ENV_DIR)/bin
ENV_LIB = $(ENV_DIR)/lib
EASY_INSTALL = PYTHONPATH=$(ENV_LIB) $(ENV_BIN)/easy_install-$(PYTHON_VERSION) -d $(ENV_LIB) -s $(ENV_BIN)
EZ_SETUP = $(ENV_BIN)/ez_setup.py

SPHINXOPTS    =
SPHINXBUILD   = $(ENV_BIN)/sphinx-build
PAPER         =
BUILDDIR      = .

.PHONY: env clean html

default: html

html:
	PYTHONPATH=$(ENV_LIB) $(SPHINXBUILD) -b html $(ALLSPHINXOPTS) \
		. $(BUILDDIR)/html

# The environment is currently required to build the documentation.
# It is not clean by 'make clean'

env: easy_install
	mkdir -p $(ENV_BIN)
	mkdir -p $(ENV_LIB)
	$(EASY_INSTALL) docutils
	$(EASY_INSTALL) sphinx

easy_install: ez_setup
	PYTHONPATH=$(ENV_LIB) $(PYTHON) $(EZ_SETUP) -d $(ENV_LIB) -s $(ENV_BIN) setuptools

ez_setup:
	mkdir -p $(ENV_BIN)
	mkdir -p $(ENV_LIB)
	wget -O $(EZ_SETUP) http://peak.telecommunity.com/dist/ez_setup.py

clean:
	$(RM) -r html

