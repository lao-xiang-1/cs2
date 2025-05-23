from . import logi
from pynput import mouse
import time


class PID:
    """PID"""

    def __init__(self, P=0.35, I=0, D=0):
        """PID"""
        self.kp = P  # 比例
        self.ki = I  # 积分
        self.kd = D  # 微分
        self.uPrevious = 0  # 上一次控制量
        self.uCurent = 0  # 这一次控制量
        self.setValue = 0  # 目标值
        self.lastErr = 0  # 上一次差值
        self.errSum = 0  # 所有差值的累加
        self.errSumLimit = 10  # 近两次的差值累加

    def pidPosition(self, setValue, curValue):
        """位置式 PID 输出控制量"""
        self.setValue = setValue  # 更新目标值
        err = self.setValue - curValue  # 计算差值, 作为比例项
        dErr = err - self.lastErr  # 计算近两次的差值, 作为微分项
        self.errSum += err  # 累加这一次差值,作为积分项
        outPID = (self.kp * err) + (self.ki * self.errSum) + (self.kd * dErr)  # PID
        self.lastErr = err  # 保存这一次差值,作为下一次的上一次差值
        return outPID  # 输出

    def pidIncrease(self, setValue, curValue):
        """增量式 PID 输出控制量的差值"""
        self.uCurent = self.pidPosition(setValue, curValue)  # 计算位置式
        outPID = self.uCurent - self.uPrevious  # 计算差值
        self.uPrevious = self.uCurent  # 保存这一次输出量
        return outPID  # 输出


def PIDMoveTo(target_x, target_y, min_x=1, min_y=1):
    control = mouse.Controller()
    now_x, now_y = control.position
    pid_x = PID()
    pid_y = PID()
    cnt = 0
    while True:
        if now_x == target_x and now_y == target_y:
            break
        move_x = int(pid_x.pidPosition(target_x, now_x))
        move_y = int(pid_y.pidPosition(target_y, now_y))
        if 0 < move_x < min_x:
            move_x = min_x
        elif 0 > move_x > -min_x:  # 限制负最小值
            move_x = -min_x
        if 0 < move_y < min_y:
            move_y = min_y
        elif 0 > move_y > -min_y:
            move_y = -min_y
        logi.Logitech.mouse.move(int(move_x), int(move_y))
        now_x, now_y = control.position
        cnt += 1
        print(now_x, now_y, move_x, move_y, cnt)
        time.sleep(0.01)

def moveTo(target_x, target_y):
    control = mouse.Controller()
    now_x, now_y = control.position
    while True:
        if now_x == target_x and now_y == target_y:
            break
        moveX = target_x - now_x
        moveY = target_y - now_y
        logi.Logitech.mouse.move(moveX, moveY)

if __name__ == '__main__':
    target_y = 720
    target_x = 1280
    control1 = mouse.Controller()
    control1.position = (2400, 120)
    PIDMoveTo(target_x, target_y)
    # moveTo(target_x, target_y)