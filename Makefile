LIB = /usr/lib/python3/dist-packages
TARGETS := $(patsubst %.py,$(LIB)/%.py,$(wildcard *.py))

$(LIB)/%.py: %.py
	sudo cp $< $@
	sudo chown root:root $@
	sudo chmod 0775 $@

install: $(TARGETS)
