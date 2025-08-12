import numpy as np


class KalmanFilter:
    def __init__(self,
                 initial_state,
                 generate_F,
                 generate_Q,
                 H,
                 R,
                 process_noise_std=0.1):
        """
        卡尔曼滤波器
        参数：
        initial_state: 初始状态向量（n维）
        generate_F: 状态转移矩阵生成函数 f(dt) -> np.ndarray
        generate_Q: 过程噪声协方差生成函数 f(dt) -> np.ndarray
        H: 观测矩阵（m×n）
        R: 测量噪声协方差矩阵（m×m）
        process_noise_std: 过程噪声强度
        """

        self.x = np.array(initial_state)
        self.n = len(initial_state)

        self.P = np.eye(self.n) * 100

        self.generate_F = generate_F
        self.generate_Q = generate_Q
        self.H = H
        self.R = R
        self.process_noise_std = process_noise_std

        self.last_t = None

    def predict(self, current_t):
        if self.last_t is None:
            self.last_t = current_t
            return

        dt = current_t - self.last_t

        self.F = self.generate_F(dt)
        self.Q = self.generate_Q(dt, self.process_noise_std)

        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        self.last_t = current_t

    def update(self, z, current_t):
        self.predict(current_t)
        y = z - self.H @ self.x

        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)

        self.x = self.x + K @ y
        self.P = (np.eye(self.n) - K @ self.H) @ self.P

    def get_estimate(self, current_t):
        self.predict(current_t)
        return self.x.copy()



