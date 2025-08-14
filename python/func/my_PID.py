import func.logi as logi
from time import sleep


class PID:
    """PID"""

    def __init__(self, P=0.35, I=0, D=0.1):
        """PID"""
        self.kp = P  # 比例
        self.ki = I  # 积分
        self.kd = D  # 微分
        self.uPrevious = 0  # 上一次控制量
        self.uCurent = 0  # 这一次控制量
        self.setValue = 0  # 目标值
        self.x_lastErr = 0  # 上一次差值
        self.y_lastErr = 0  # 上一次差值
        self.errSum = 0  # 所有差值的累加
        self.errSumLimit = 10  # 近两次的差值累加

    def pidPosition(self, err, code):
        """位置式 PID 输出控制量"""
        if code == 'x':
            dErr = err - self.x_lastErr  # 计算近两次的差值, 作为微分项
            outPID = (self.kp * err) + (self.kd * dErr)  # PD
            self.x_lastErr = err  # 保存这一次差值,作为下一次的上一次差值
            return outPID  # 输出
        if code == 'y':
            dErr = err - self.y_lastErr  # 计算近两次的差值, 作为微分项
            outPID = (self.kp * err) + (self.kd * dErr)  # PD
            self.y_lastErr = err  # 保存这一次差值,作为下一次的上一次差值
            return outPID  # 输出
    
    def PIDMoveTo(self, err_x, err_y, P=0.35, I=0, D=0.12):
        self.kp = P  # 比例
        self.ki = I  # 积分
        self.kd = D  # 微分
        move_x = int(self.pidPosition(err_x, 'x'))
        move_y = int(self.pidPosition(err_y, 'y'))
        logi.Logitech.mouse.move(int(move_x), int(move_y))
        print('最终：',[int(move_x), int(move_y)])

    def _click(self):
        logi.Logitech.mouse.press(1)
        sleep(0.1)
        logi.Logitech.mouse.release(1)


if __name__ == '__main__':
    from pynput import mouse
    target_y = 720
    target_x = 1280
    control1 = mouse.Controller()
    control1.position = (2400, 120)
    # PIDMoveTo(target_x, target_y)
    # moveTo(target_x, target_y)