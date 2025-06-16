include Makefile.distcommon

# Makefile.depends contains the rules to make $(build_name) and remake itself.
# This bootstrap rule is disabled if the dependency file already exists:
ifeq (,$(wildcard Makefile.depends))
Makefile.depends:
	$(python) preprocessor.py main.py --dependency-file=Makefile.depends --build-file=$(build_name)
endif

# Avoid building dependency file if we're cleaning anyway
ifeq (,$(call eq,clean,$(MAKECMDGOALS)))
include Makefile.depends
endif
