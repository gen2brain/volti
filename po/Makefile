PYFILES = $(shell find ../src -type f -name "*.py")
GLADEFILES = $(wildcard ../data/*.glade)
POFILES = $(wildcard *.po)

GLADEHFILES := $(GLADEFILES:.glade=.glade.h)

help:
	@echo "USAGE:"
	@echo "make update - updates messages.pot and .po files"
	@echo "make sr.po  - updates sr.po file OR creates new one"
	@echo "              (replace 'sr' with your language code)"

%.h: %
	intltool-extract --type="gettext/glade" $*


messages.pot: $(GLADEHFILES) $(PYFILES)
	xgettext -k_ -kN_ -o messages.pot $(PYFILES) $(GLADEHFILES) --from-code=utf-8

%.po: messages.pot
	@if test -f $@; then \
		echo -n "Updating '$*' language ";\
		msgmerge -U $@ messages.pot;\
	else \
		msginit -l $*.UTF8 -o $@; \
	fi

update: $(POFILES)

clean:
	$(RM) $(GLADEHFILES)

.PHONY:  update
