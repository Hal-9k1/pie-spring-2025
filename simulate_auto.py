import time
import importlib
import sys
build = importlib.import_module(sys.argv[1])
build.autonomous_setup()
while True:
    time.sleep(1 / 1000)
    build.autonomous_main()
