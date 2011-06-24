# pgxnclient Makefile
#
# Copyright (C) 2011 Daniele Varrazzo
#
# This file is part of the PGXN client

.PHONY: sdist upload docs

PYTHON := python$(PYTHON_VERSION)
PYTHON_VERSION ?= $(shell $(PYTHON) -c 'import sys; print ("%d.%d" % sys.version_info[:2])')

build:
	$(PYTHON) setup.py build

check:
	$(PYTHON) setup.py test

sdist:
	$(PYTHON) setup.py sdist --formats=gztar

upload:
	$(PYTHON) setup.py sdist --formats=gztar upload

docs:
	$(MAKE) -C docs

clean:
	rm -rf build pgxnclient.egg-info
	rm -rf simplejson-*.egg mock-*.egg unittest2-*.egg
	$(MAKE) -C docs $@

