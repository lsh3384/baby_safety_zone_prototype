#!/usr/bin/python
import cv2
import numpy as np
import base64
import socketio
from shapely.geometry import Polygon, Point
import time

class BabyZone:

    coordinates_from_html = []
    sio = socketio.Client()
    flag = 0
    
    def __init__(self):
        
        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
          
        self.facedetector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
        self.poly = Polygon([[0,0], [0,0], [0,0]])
    
    def sio_setup(self):
        self.call_backs()
        self.sio.connect('http://localhost:3000')
    
    def call_backs(self):        
        @self.sio.event
        def coordinates(coords):
            BabyZone.coordinates_from_html = coords
            try:
                for i in bz.coordinates_from_html:
                    print(i)
            except:
                print(coords)
            self.flag = 0
        
        @self.sio.event
        def resetFromHtml(reset):
            self.flag = 1
            BabyZone.coordinates_from_html = []
            self.setup()
    
    
    # 첫화면에서 좌표 설정하도록 변경
    def setup(self):
        self.flag = 1
        BabyZone.coordinates_from_html = []
        ret, frame = self.capture.read()
        result, buffer = cv2.imencode('.jpg', frame)
        stringData = base64.b64encode(buffer)
        self.poly = Polygon([[0,0], [0,0], [0,0]])
        pts = np.array(BabyZone.coordinates_from_html, dtype=np.int32)  #좌표를 numpy 배열 형태로 변환
        cv2.polylines(frame, [pts], True, (0,0,255), 5)        # 받은 좌표로 다각형 생성
        
        self.sio.emit('data', stringData)
        # 좌표가 들어올 때까지 무한루프
        while len(BabyZone.coordinates_from_html) < 1:
            print(len(BabyZone.coordinates_from_html))
            print('waiting coordinates from web server')
            
        # 들어온 좌표로 다각형 객체 설정
        self.poly = Polygon(BabyZone.coordinates_from_html)
        self.flag = 0
    # opencv 통해서 영상 보내기
    def video(self):
        #OpenCV를 이용해서 webcam으로 부터 이미지 추출
        ret, frame = self.capture.read()
        
        #다각형 그리기
        pts = np.array(BabyZone.coordinates_from_html, dtype=np.int32)  #좌표를 numpy 배열 형태로 변환
        cv2.polylines(frame, [pts], True, (0,0,255), 5)        # 받은 좌표로 다각형 생성
        
        #얼굴 인식하기
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # 회색으로 프레임 변경
        faces = self.facedetector.detectMultiScale(gray, 1.2, 5, minSize=(30, 30)) #얼굴 인식 시작해서 인식된 좌표 faces변수에 리턴
        for (x, y, w, h) in faces:   # 받은 좌표로 사각형 그리기
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 4)
            print(x, y)
        
        # 좌표를 기준으로 다각형 안에 있는지 확인 후 알람 보내기
        for (x, y, w, h) in faces:
            presentCordinate1 = Point(x, y)
            presentCordinate2 = Point(x+w, y)
            presentCordinate3 = Point(x, y+h)
            presentCordinate4 = Point(x+w, y+h)
            if not presentCordinate1.within(self.poly):
                print("baby out of safezone")
                self.sio.emit('baby_out', 'out') # 웹서버로 baby_out 이벤트 발생
                time.sleep(3)
            elif not presentCordinate2.within(self.poly):
                print("baby out of safezone")
                self.sio.emit('baby_out', 'out') # 웹서버로 baby_out 이벤트 발생
                time.sleep(3)
            elif not presentCordinate3.within(self.poly):
                print("baby out of safezone")
                self.sio.emit('baby_out', 'out') # 웹서버로 baby_out 이벤트 발생
                time.sleep(3)
            elif not presentCordinate4.within(self.poly):
                print("baby out of safezone")
                self.sio.emit('baby_out', 'out') # 웹서버로 baby_out 이벤트 발생
                time.sleep(3)
                
        # 보낼 frame을 jpg 포맷으로 변환
        result, buffer = cv2.imencode('.jpg', frame)
        #jpg를 base64포맷으로 인코딩
        stringData = base64.b64encode(buffer)
        # 웹서버로 data 이벤트 발생
        self.sio.emit('data', stringData)
        
    
    
if __name__ == '__main__':    
    bz = BabyZone()
    bz.sio_setup()
    bz.setup()
    
    while True:
        while bz.flag < 1:
            bz.video()
    
    # capture객체 반환
    bz.capture.release()
    #영상 뜨는 화면 모두 끄기
    cv2.destroyAllWindows()
