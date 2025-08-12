import numpy as np
import json


class Velocity:
    H = np.array([[1, 0, 0]])
    R = np.array([[0.5 ** 2]])

    @staticmethod
    def F(dt):
        return np.array([[1, dt],
                    [0, 1]])

    @staticmethod
    def Q(dt, noise_std):
        return np.array([[(dt**4)/4, (dt**3)/2],
                    [(dt**3)/2,  dt**2]]) * noise_std**2


class Acceleration:
    H = np.array([[1, 0, 0]])
    R = np.array([[0.5 ** 2]])

    @staticmethod
    def F(dt):
        return np.array([[1, dt, 0.5 * dt ** 2],
                         [0, 1, dt],
                         [0, 0, 1]])

    @staticmethod
    def Q(dt, noise_std):
        return np.array([[dt ** 4 / 4, dt ** 3 / 2, dt ** 2 / 2],
                         [dt ** 3 / 2, dt ** 2, dt],
                         [dt ** 2 / 2, dt, 1]]) * noise_std ** 2


class HRFQ:
    def __init__(self, json_path):
        with open(json_path, "r") as file:
            self.values = json.load(file)
        self.H = np.array(self.values["H"])
        self.R = np.array(self.values["R"])

    def F(self, dt):
        return dt * np.array(self.values["F"])

    def Q(self, dt, noise_std):
        return dt * np.array(self.values["Q"]) * noise_std ** 2

