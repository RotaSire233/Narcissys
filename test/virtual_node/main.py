from virtual_node import *
import sys
import os
from loguru import logger

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

def main():
    
    node: VirtualNode = virtual_node
    node.run()

if __name__ == "__main__":
    main()