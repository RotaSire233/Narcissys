from virtual_node import *
import sys
import os
from udp_driver import UdpTypeStatic, UdpTypeStream
from loguru import logger

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

def sensor_1():
    return 1

def sensor_2():
    return 2

def main():
    
    node: VirtualNode = virtual_node
    sensor_1_struct = SensorRegisterStatic("sensor_1", sensor_1, UdpTypeStatic.INT, sample_rate=5)
    sensor_2_struct = SensorRegisterStatic("sensor_2", sensor_2, UdpTypeStatic.INT,sample_rate=5)
    node.register_sensor(sensor_1_struct)
    node.register_sensor(sensor_2_struct)
    node.run()

if __name__ == "__main__":
    main()