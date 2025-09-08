from virtual_node import *
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
def sensor_1():
    return 1

def sensor_2():
    return 2

def main():
    virtual_node = VirtualNode()
    sensor_1_struct = SensorRegisterStatic("sensor_1", sensor_1)
    sensor_2_struct = SensorRegisterStatic("sensor_2", sensor_2)
    virtual_node.register_sensor(sensor_1_struct)
    virtual_node.register_sensor(sensor_2_struct)
    virtual_node.run()

if __name__ == "__main__":
    main()