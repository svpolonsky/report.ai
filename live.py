# INFO on TPLINK NC2XX Cameras
# https://github.com/reald/nc220

import cv2
import base64

p='s1251097p'
print(base64.b64encode(bytes(p, 'utf-8')))


#print(cv2.getBuildInformation())
addr='http://admin:czEyNTEwOTdw@192.168.0.110:8080/stream/video/mjpeg'
#"http://admin:s1251097p@192.168.0.104:8080/stream/video/mjpeg"
vcap = cv2.VideoCapture(addr)
while(1):
    ret, frame = vcap.read()
    print(ret)
    cv2.imshow('VIDEO', frame)
    cv2.waitKey(1)
