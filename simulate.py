import importlib
import sys
getattr(importlib.import_module(sys.argv[1]), sys.argv[2])()
