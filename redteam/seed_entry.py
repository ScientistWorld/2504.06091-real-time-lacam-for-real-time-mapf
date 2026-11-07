"""Run an unmodified entry point with reproducible Python RNG initialization."""
import random
import runpy
import sys

seed, entry, *args = sys.argv[1:]
random.seed(int(seed))
sys.argv = [entry, *args]
runpy.run_path(entry, run_name="__main__")
