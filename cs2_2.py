from PIL import ImageGrab
import cv2
import numpy as np
from ultralytics import YOLO
import keyboard
import func.my_PID as PID
from time import sleep
from math import sqrt
import threading
import winsound

model=YOLO('best.pt')

pid = PID.PID()

k1 = 1.5
k2 = 3
k3 = 4.5

first = 'head'
enemy = 'T'
fire = 'off'
pause = False

keyboard.wait('1') # 等待按下1
running = True
winsound.Beep(800, 200)

def near_p(s):
    if len(s) == 1:
        return s[0]
    near_p = s[0]
    last_xy = abs(s[0][0]) + abs(s[0][1])
    for p in s:
        xy = abs(p[0]) + abs(p[1])
        if xy < last_xy:
            near_p = p
        last_xy = xy
    return near_p

def near_area_h(p):
    new_p = []
    k = p[3] / p[2] # h / w
    if abs(p[1] / p[0]) >= k:
        if p[1] >= 0:
            err_y = p[1] - p[3] / 2 # err_y - h / 2
            err_x = err_y * p[0] / p[1]
        elif p[1] < 0:
            err_y = p[1] + p[3] / 2 # err_y + h / 2
            err_x = err_y * p[0] / p[1]
    elif abs(p[1] / p[0]) < k:
        if p[0] >= 0:
            err_x = p[0] - p[2] / 2 # err_x - w / 2
            err_y = err_x * p[1] / p[0]
        elif p[0] < 0:
            err_x = p[0] + p[2] / 2 # err_x + w / 2
            err_y = err_x * p[1] / p[0]
    new_p = [int(err_x), int(err_y)]
    return new_p

def near_area_b(p):
    w1 = p[2]
    h1 = p[3] * 0.6
    p1 = [p[0], p[1], w1, h1]
    return near_area_h(p1)

def first_h_b():
    global first
    if first == 'head':
        first = 'body'
    elif first == 'body':
        first = 'head'
    winsound.Beep(600, 200)
    print('优先打: ', first)

def enemy_c_t():
    global enemy
    if enemy == 'CT':
        enemy = 'T'
    elif enemy == 'T':
        enemy = 'CT'
    winsound.Beep(600, 200)
    print('敌人: ', enemy)

def fire_auto():
    global fire
    if fire == 'on':
        fire = 'off'
    elif fire == 'off':
        fire = 'on'
    winsound.Beep(600, 200)
    print('自动开火: ', fire)

def pause_or_not():
    global pause
    pause = not pause
    winsound.Beep(600, 200)
    print('是否暂停: ', pause)

def select():
    keyboard.add_hotkey('/', first_h_b)
    keyboard.add_hotkey('*', enemy_c_t)
    keyboard.add_hotkey('-', fire_auto)
    keyboard.add_hotkey('+', pause_or_not)
    keyboard.wait('=')
    global running
    running =False
    winsound.Beep(400, 200)

threading.Thread(target=select, daemon=True).start()

while running:
    print('优先打: ', first)
    print('敌人: ', enemy)
    print('自动开火: ', fire)
    # sleep(1)
    #2560*1600
    while pause:
        sleep(0.01)
    region = (960, 480, 1600, 1120) #（left, top, right, bottom）
    screenshot = ImageGrab.grab(bbox=region)
    frame = np.array(screenshot)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    results=model.predict(frame, save=False, conf=0.5)

    head = []
    body = []

    for result in results:
        for box in result.boxes:
            # Extract bounding box, confidence, and class
            x1, y1, x2, y2 = map(int, box.xyxy[0])  # Bounding box coordinates

            w = x2 - x1 # 宽
            h = y2 -y1 # 高
            #面积太大
            if w * h >= 50000:
                continue  
            #在角落
            if (x1 >= 532 and y1 >= 532) or (x1 <= 108 and y1 >= 532) or (x1 <= 108 and y1 <= 108) or (x1 >= 532 and y1 <= 108):
                continue  # 改用continue跳过无效检测
            confidence = box.conf[0].item()  # Confidence score
            cls = int(box.cls[0].item())  # Class ID

            # 离屏幕中心的距离
            if cls == 1 or cls == 3: # 头：正中心
                err_x = (x1 + x2) // 2 - 320
                err_y = (y1 + y2) // 2 - 320
            elif cls == 0 or cls == 2: # 身体：三七开，更接近上面
                err_x = (x1 + x2) // 2 - 320
                err_y = (y1 * 7 + y2 * 3) // 10 - 320

            if enemy == 'T':
                if cls ==  3:  # 头部类别
                    head.append([err_x, err_y, w, h])
                if cls ==  2:  # 身体类别
                    body.append([err_x, err_y, w, h])
            elif enemy == 'CT':
                if cls ==  1:  # 头部类别
                    head.append([err_x, err_y, w, h])
                if cls ==  0:  # 身体类别
                    body.append([err_x, err_y, w, h])

    print(head)
    print(body)

    if first == 'head':
        if head:
            new_p = []
            p = near_p(head) # 取离得最近的坐标
            if abs(p[0]) > p[2] * 0.5 and abs(p[1]) > p[3] * 0.5:
                new_p = near_area_h(p)
                print(new_p)
            sum = sqrt(p[0] ** 2 + p[1] ** 2)
            if fire == 'on' and abs(p[0]) <= p[2] * 0.3 and abs(p[1]) <= p[3] * 0.3: # 自动开火
                pid._click()
            if new_p:
                pid.PIDMoveTo(new_p[0], new_p[1], P= 1 / k2)
            elif p:
                pid.PIDMoveTo(p[0], p[1], P= 1 / k3)
            continue
        elif body:
            new_p = []
            p = near_p(body) # 取离得最近的坐标
            if abs(p[0]) > p[2] * 0.6 and abs(p[1]) > p[3] * 0.6:
                new_p = near_area_h(p)
            sum = sqrt(p[0] ** 2 + p[1] ** 2)
            if fire == 'on' and abs(p[0]) <= p[2] * 0.3 and abs(p[1]) <= p[3] * 0.3: # 自动开火
                pid._click()
            if new_p:
                pid.PIDMoveTo(new_p[0], new_p[1], P= 1 / k2)
            elif p:
                pid.PIDMoveTo(p[0], p[1], P= 1 / k3)
    elif first == 'body':
        if body:
            new_p = []
            p = near_p(body) # 取离得最近的坐标
            if abs(p[0]) > p[2] * 0.6 and abs(p[1]) > p[3] * 0.6:
                new_p = near_area_h(p)
            sum = sqrt(p[0] ** 2 + p[1] ** 2)
            if fire == 'on' and abs(p[0]) <= p[2] * 0.3 and abs(p[1]) <= p[3] * 0.3: # 自动开火
                pid._click()
            if new_p:
                pid.PIDMoveTo(new_p[0], new_p[1], P= 1 / k2)
            elif p:
                pid.PIDMoveTo(p[0], p[1], P= 1 / k3)
            continue
        elif head:
            new_p = []
            p = near_p(head) # 取离得最近的坐标
            if abs(p[0]) > p[2] * 0.6 and abs(p[1]) > p[3] * 0.6:
                new_p = near_area_h(p)
            sum = sqrt(p[0] ** 2 + p[1] ** 2)
            if fire == 'on' and abs(p[0]) <= p[2] * 0.3 and abs(p[1]) <= p[3] * 0.3: # 自动开火
                pid._click()
            if new_p:
                pid.PIDMoveTo(new_p[0], new_p[1], P= 1 / k2)
            elif p:
                pid.PIDMoveTo(p[0], p[1], P= 1 / k3)

