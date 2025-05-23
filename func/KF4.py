import numpy as np
import matplotlib.pyplot as plt


class KalmanFilter:
    def __init__(self, first_pt, dt=1, process_noise=1e-1, measurement_noise=1e-1):
        self.dt = dt  # 时间间隔
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise

        # 初始状态估计 [x, y, v_x, v_y]
        self.x = np.array([[first_pt[0]], [first_pt[1]], [first_pt[2]], [first_pt[3]]])  # 初始位置为(0, 0), 初始速度为(0, 0)

        # 初始误差协方差矩阵 P
        self.P = np.eye(4) * 1  # 高估初始误差

        # 状态转移矩阵 A (假设匀速直线运动)
        self.A = np.array([[1, 0, self.dt, 0],
                           [0, 1, 0, self.dt],
                           [0, 0, 1, 0],
                           [0, 0, 0, 1]])

        # 测量矩阵 H (测量的是位置)
        self.H = np.array([[1, 0, 0, 0],
                           [0, 1, 0, 0],
                           [0, 0, 1, 0],
                           [0, 0, 0, 1]])
        # self.H = np.array([[1, 0, 0, 0],
        #                    [0, 1, 0, 0]])
        # 过程噪声协方差矩阵 Q
        self.Q = np.array([[self.process_noise, 0, 0, 0],
                           [0, self.process_noise, 0, 0],
                           [0, 0, self.process_noise, 0],
                           [0, 0, 0, self.process_noise]])

        # 测量噪声协方差矩阵 R
        self.R = np.array([[self.measurement_noise, 0, 0, 0],
                           [0, self.measurement_noise, 0, 0],
                           [0, 0, self.measurement_noise, 0],
                           [0, 0, 0, self.measurement_noise]])
        # self.R = np.array([[self.measurement_noise, 0],
        #                    [0, self.measurement_noise]])

    def predict(self):
        """根据当前状态预测下一时刻的状态"""
        self.x = np.dot(self.A, self.x)  # 预测状态
        self.P = np.dot(np.dot(self.A, self.P), self.A.T) + self.Q  # 预测误差协方差

    def update(self, z):
        """根据测量值更新状态估计"""
        # 计算卡尔曼增益
        K = np.dot(np.dot(self.P, self.H.T), np.linalg.inv(np.dot(np.dot(self.H, self.P), self.H.T) + self.R))

        # 更新状态估计
        y = z - np.dot(self.H, self.x)  # 测量残差
        self.x = self.x + np.dot(K, y)

        # 更新误差协方差矩阵
        self.P = np.dot(np.eye(4) - np.dot(K, self.H), self.P)

    def get_state(self):
        """返回当前的估计状态"""
        return self.x[:2]  # 只返回位置(x, y) np.arr[[x],[y]]

if __name__ == '__main__':
    x_values = []
    y_values = []

    with open('../boxCenter.txt', 'r') as file:
        for line in file:
            # 分割每行数据，并将其转换为整数
            x, y = map(int, line.split())  # map内建函数对指定的序列做映射: int函数应用到['x', 'y']中的可迭代对象上
            x_values.append(x)
            y_values.append(y)
    measured_positions = list(zip(x_values, y_values))
    tmp_positions = []
    for i in range(len(measured_positions)-1):
        tmp = [measured_positions[i][0], measured_positions[i][1], measured_positions[i+1][0]-measured_positions[i][0], measured_positions[i+1][1]-measured_positions[i][1]]
        tmp_positions.append(tmp)
    measurements = np.asarray(tmp_positions)
    kf = KalmanFilter(measurements[0])
    pre_positions = []
    post_positions = []

    for i in range(len(measurements)):
        kf.predict()
        # aaa = list(kf.get_state())
        # print(type(aaa[0]))  np
        pre_positions.append(list(kf.get_state()))
        if i == len(measurements)-1:
            break
        kf.update(np.array([[measurements[i + 1][0]],[measurements[i + 1][1]], [measurements[i + 1][2]], [measurements[i + 1][3]]]))
        post_positions.append(list(kf.get_state()))

    # 转换为列表，便于绘图
    pre_x, pre_y = zip(*pre_positions)  # *：[(),(),()]->(),(),()  即解包
    post_x, post_y = zip(*post_positions)
    cnt = 0
    print(int(pre_x[0]))
    for i in range(len(pre_x) - 1):
        cnt += 1
        print(f"cnt: {cnt}, predicted:({int(pre_x[i])} {int(pre_y[i])}), measured:({x_values[i+1]}, {y_values[i+1]}), post_estimate:({int(post_x[i])}, {int(post_y[i])})")
    # 绘图
    plt.figure(figsize=(16, 9))
    plt.scatter(x_values, y_values, color='red', marker='x')
    plt.scatter(pre_x, pre_y, color='blue', marker='o')
    plt.scatter(post_x, post_y, color='yellow', marker='o')
    plt.xlim(0, 2560)  # X轴范围 [0, 2560]
    plt.ylim(0, 1440)  # Y轴范围 [0, 1440]
    # 设置坐标轴标签
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    # 反转Y轴，使原点在左上角
    plt.gca().invert_yaxis()
    # 设置图表标题
    plt.title('Scatter Plot of Points')
    # 显示图形
    plt.show()
    # 测量数据
    # measurements = np.array([[5, 5], [10, 10], [16, 16], [24, 24]])
    # measurements = np.array([[5, 5, 5, 5], [10, 10, 6, 6], [16, 16, 8, 8], [24, 24, 3, 3]])
    # kf = KalmanFilter(measurements[0])

    # estimated_positions = []
    #
    # for i in range(measurements.shape[0]):
    #     kf.predict()
    #     estimated_positions.append(kf.get_state())
    #     if i == measurements.shape[0] - 1:
    #         break
    #     kf.update(np.array([[measurements[i + 1][0]],[measurements[i + 1][1]], [measurements[i + 1][2]], [measurements[i + 1][3]]]))
    #     # kf.update(np.array([[measurements[i + 1][0]],[measurements[i + 1][1]]]))
    #
    # print(estimated_positions)
    #
    # # 绘制结果
    # estimated_positions = np.array(estimated_positions)
    # plt.plot(estimated_positions[:, 0], estimated_positions[:, 1], label='Estimated Position', color='blue', marker='o')
    # plt.scatter(measurements[:, 0], measurements[:, 1], color='red', label='Measured Position')
    # plt.legend()
    # plt.title("Kalman Filter Position Estimation with Velocity")
    # plt.xlabel('X')
    # plt.ylabel('Y')
    # plt.grid(True)
    # plt.show()
