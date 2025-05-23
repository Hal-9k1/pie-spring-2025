MAKEFLAGS += --no-builtin-rules

eq = $(and $(findstring $(1),$(2)),$(findstring $(2),$(1)))

build_module := mainbuild
build_name := $(build_module).py

.PHONY: all test simauto simteleop simulate copy clean
all: $(build_name)

test:
	python -m unittest discover -s tests -t . -p '*.py'

simulate: simauto

simteleop: $(build_name)
	python simulate.py mainbuild teleop

simauto: $(build_name)
	python simulate.py mainbuild autonomous

copy: $(build_name)
	vim -c 'normal ggvG$$"+y' -c ':q' $<

clean:
	rm -f Makefile.depends $(build_name)

# Makefile.depends contains the rules to make $(build_name) and remake itself, if it exists
ifeq (,$(wildcard Makefile.depends))
Makefile.depends:
	python preprocessor.py main.py --dependency-file=Makefile.depends --build-file=$(build_name)
endif

ifeq (,$(call eq,clean,$(MAKECMDGOALS)))
include Makefile.depends
endif
