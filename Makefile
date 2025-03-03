MAKEFLAGS += --no-builtin-rules

eq = $(and $(findstring $(1),$(2)),$(findstring $(2),$(1)))

build_module := mainbuild
build_name := $(build_module).py

.PHONY: all test copy clean
all: $(build_name)
test: $(build_name)
	python simulate_auto.py $(build_module)
copy: $(build_name)
	vim -c 'normal ggvG$$"+y' -c ':q' $<
clean:
	rm -f Makefile.depends $(build_name)

# Makefile.depends contains a rule to remake itself, if it exists
ifeq (,$(wildcard Makefile.depends))
Makefile.depends:
	python preprocessor.py main.py --dependency-file=Makefile.depends --build-file=$(build_name)
endif

ifeq (,$(call eq,clean,$(MAKECMDGOALS)))
include Makefile.depends
endif
