import numpy as np

class MyBox:
    def __init__(self, box):
        self.x1 = round(box[0]) * 2
        self.y1 = round(box[1]) * 2
        self.x2 = round(box[2]) * 2
        self.y2 = round(box[3]) * 2
        self.conf = round(box[4], 2)
        self.cls = round(box[5])
        self.w = self.x2 - self.x1
        self.h = self.y2 - self.y1
        self.rate = round(self.w / self.h, 2)
        self.center = [round(self.x1 + self.w / 2), round(self.y1 + self.h / 2)]

    def print_box(self):
        print(f"xyxy: {self.x1}, {self.y1}, {self.x2}, {self.y2}, conf={self.conf}, cls={self.cls}, w={self.w}, h={self.h}")