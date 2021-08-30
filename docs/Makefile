# PGXN Client -- documentation makefile
#
# Building docs requires virtualenv already installed in the system.
#
# Use'make html' to build the HTML documentation.
#
# Copyright (C) 2011-2021 Daniele Varrazzo

PYTHON := python
ENV_DIR = $(shell pwd)/env
ENV_BIN = $(ENV_DIR)/bin

SPHINXOPTS    =
SPHINXBUILD   = $(ENV_BIN)/sphinx-build
PAPER         =
BUILDDIR      = .

.PHONY: env clean html

default: html

html: env
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) \
		. $(BUILDDIR)/html

# The environment is currently required to build the documentation.
# It is not clean by 'make clean'
env:
	[ -d "$(ENV_DIR)" ] || ( \
		virtualenv -p "$(PYTHON)" "$(ENV_DIR)" \
		&& "$(ENV_BIN)/pip" install -r requirements.txt)

clean:
	$(RM) -r html
