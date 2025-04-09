import time
import importlib
import sys
build = importlib.import_module(sys.argv[1])
build.autonomous()
