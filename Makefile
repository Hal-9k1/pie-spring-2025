include Makefile.distcommon

# Not being able to conditionally disable this rule emits a warning when Makefile.depends already
# exists since it contains its own rule. This also always rebuilds the deps file. GNU Make ftw!
.INTERMEDIATE: Makefile.depends
Makefile.depends:
	$(python) preprocessor.py main.py --dependency-file=Makefile.depends --build-file=$(build_name)

include Makefile.depends
