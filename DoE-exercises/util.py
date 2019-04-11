import sys, os

# Disable
def block_print():
    sys.stdout = open(os.devnull, 'w')

# Restore
def enable_print(pipe=sys.stdout):
    sys.stdout = pipe