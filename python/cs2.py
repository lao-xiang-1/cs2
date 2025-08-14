from PIL import ImageGrab
import cv2
import numpy as np
from ultralytics import YOLO
import keyboard
from time import sleep
import threading
import winsound
from time import time
import func.logi as logi

model=YOLO('best.pt')

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

def attack(p):
    if fire == 'on' and abs(p[0]) <= p[2] * 0.3 and abs(p[1]) <= p[3] * 0.3: # 自动开火
        logi.Logitech.mouse.press(1)
        sleep(0.1)
        logi.Logitech.mouse.release(1)
    else:
        logi.Logitech.mouse.move(p[0], p[1])
        sleep(0.07)

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
    start_time = time()
    # print('优先打: ', first)
    # print('敌人: ', enemy)
    # print('自动开火: ', fire)
    # sleep(1)
    #2560*1600
    while pause:
        sleep(0.01)
    region = (960, 480, 1600, 1120) #（left, top, right, bottom）
    screenshot = ImageGrab.grab(bbox=region)
    frame = np.array(screenshot)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    results=model.predict(frame, save=False, conf=0.5, verbose=False)

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
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    head.append([err_x, err_y, w, h])
                if cls ==  2:  # 身体类别
                    body.append([err_x, err_y, w, h])
            elif enemy == 'CT':
                if cls ==  1:  # 头部类别
                    head.append([err_x, err_y, w, h])
                if cls ==  0:  # 身体类别
                    body.append([err_x, err_y, w, h])

    # cv2.imshow('frame', frame)
    # if cv2.waitKey(1) & 0xFF == ord('q'):
    #     break

    if first == 'head':
        if head:
            p = near_p(head) # 取离得最近的坐标
            attack(p)
        elif body:
            p = near_p(body) # 取离得最近的坐标
            attack(p)
    elif first == 'body':
        if body:
            p = near_p(body) # 取离得最近的坐标
            attack(p)
        elif head:
            p = near_p(head) # 取离得最近的坐标
            attack(p)
    end_time = time()
    print(f"Frame processed in {(end_time - start_time) * 1000} ms")

cv2.destroyAllWindows()
