INSTALL_DIR := ~/travail/mpsi/challengeMPSI/challengeMPSI/static/img/ondes/
PDF_FILES := $(wildcard *.pdf)
PNG_FILES := $(patsubst %.pdf, %.png, $(PDF_FILES))
INSTALLED_PNG_FILES = $(addprefix $(INSTALL_DIR),$(PNG_FILES))

all: $(PNG_FILES)
	@echo $(PNG_FILES)

copy: $(PNG_FILES)
		cp $^ $(INSTALL_DIR)


%.png: %.pdf
		convert -density 300 $< $@
		cp $@ $(INSTALL_DIR)$($@)

.PHONY: all
