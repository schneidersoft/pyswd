.PHONY: test install uninstall

all: test install

test:
	@echo TESTING
	@python3 -m unittest discover

install:
	@echo INSTALLING
	@pip3 install --upgrade .

uninstall:
	@echo UNINSTALLING
	@pip3 uninstall pyswd
