# -*- coding: UTF-8 -*-
#!/usr/bin/python3
"""
This code reads data from the serial port and displays it as an image preview.
It supports three formats of images (96x96 Grayscale, 240x320 Grayscale, 240x320 YUV).
The program also allows the user to select the image format.
"""

import serial
import serial.tools.list_ports
import numpy as np
import cv2
import math
import time
import getopt
import sys

np.set_printoptions(formatter={'int':hex})

# Convert YUV format to an image
def YUVToMat(data,Width,Height, color_mode):
    codeMap = {
        0:cv2.COLOR_YUV2BGR_YUYV,
        1:cv2.COLOR_YUV2BGR_YVYU,
        2:cv2.COLOR_YUV2BGR_UYVY,
        3:cv2.COLOR_YUV2BGR_Y422,
        4:cv2.COLOR_YUV2BGR_YUY2,
    }
    image = np.frombuffer(data, np.uint8).reshape(Height, Width, 2)
    return cv2.cvtColor(image,codeMap[color_mode])

# Convert RGB565 format to an image
def RGB565ToMat(data,Width,Height):
    arr = np.frombuffer(data,dtype='<u2').astype(np.uint32)
    arr = ((arr & 0xFF00) >> 8) + ((arr & 0x00FF) << 8)
    arr = 0xFF000000 + ((arr & 0xF800) << 8) + ((arr & 0x07E0) << 5) + ((arr & 0x001F) << 3)
    arr.dtype = np.uint8
    image = arr.reshape(Height,Width,4)
    return image

# Select the serial port to use
def selectSerialPort():
    ports_list = list(_serial.tools.list_ports.comports())
    print("可用的串口设备如下：")
    idx = 0
    for comport in ports_list:
        print("[{}]:".format(idx),comport.description,comport.device)
        idx+=1
    index = input("please seletc: ")
    return ports_list[int(index)].device

def openSerialPort(port='COM6',baudrate=961200,parity='N',rtscts=False,timeout=1,xonxoff=False,rts=None,dtr=None,exclusive=True,quiet=False) -> serial.Serial :
    try:
        _serialInstance = serial.serial_for_url(
            url=port,
            baudrate=baudrate,
            parity=parity,
            rtscts=rtscts,
            timeout=timeout,
            xonxoff=xonxoff,
            do_not_open=True)

        if not hasattr(_serialInstance, 'cancel_read'):
            # enable timeout for alive flag polling if cancel_read is not available
            _serialInstance.timeout = 1

        if dtr is not None:
            if not quiet:
                sys.stderr.write('--- forcing DTR {}\n'.format('active' if dtr else 'inactive'))
            _serialInstance.dtr = dtr
        if rts is not None:
            if not quiet:
                sys.stderr.write('--- forcing RTS {}\n'.format('active' if rts else 'inactive'))
            _serialInstance.rts = rts

        if isinstance(_serialInstance, serial.Serial):
            _serialInstance.exclusive = exclusive
        # print(serial_instance,args)
        _serialInstance.open()
        return _serialInstance
    except _serial.SerialException as e:
        sys.stderr.write('could not open port {!r}: {}\n'.format(port, e))

def serialPortReceivingDataCorrection(frameBuffer:list,bytesPerFrame):
    previousFrameCache = bytesPerFrame % 4096
    if previousFrameCache:
        frameBuffer = frameBuffer[previousFrameCache:] + frameBuffer[:previousFrameCache]
    return frameBuffer

cameraWidth = 320
cameraHeight = 240
useGrayScale = True
baudRate = 921600

cameraBytesPerPixel =  1 if useGrayScale  else  2
cameraPixelCount = cameraWidth * cameraHeight
bytesPerFrame = cameraPixelCount * cameraBytesPerPixel
timeout =  math.ceil(bytesPerFrame / (baudRate/10))

def runProgressBar(percentage):
    print("[",end=' ')
    for i in range(0,30,1):
        if i < percentage:
            print("#",end='')
        else:
            print(" ", end='')
    print(" ] fps:{}".format(percentage), end='\r')


def display_fps():
    display_fps.frame_count += 1

    current = time.time()
    if current - display_fps.start >= 1:
            print("")
            display_fps.frame_count = 0
            display_fps.start = current
    runProgressBar(display_fps.frame_count)
    
display_fps.start = time.time()
display_fps.frame_count = 0

if __name__=="__main__":
    print("camera info:")
    print(f"camera width: {cameraWidth}, camera width: {cameraHeight}")
    print(f"Grayscale: {useGrayScale}")

    _serial = openSerialPort(port='COM6',baudrate=baudRate,timeout=timeout)
    if _serial.isOpen():
        print(f"[{ _serial.name }] opened successfully, baud rate is { _serial.baudrate }.")

    else:
        print("打开%s串口失败。"%_serial.name)
    # Read data from the serial port and display it as an image preview
    while _serial.isOpen():
        _serial.write(b'\x01')
        frameBuffer=_serial.read(size=bytesPerFrame)        
        # frameBuffer = serialPortReceivingDataCorrection(frameBuffer,bytesPerFrame)
        if (len(frameBuffer) == bytesPerFrame) :
            if useGrayScale :
                image = np.frombuffer(frameBuffer,dtype =np.uint8).reshape(cameraHeight,cameraWidth)
            else :
                image = RGB565ToMat(frameBuffer,cameraWidth,cameraHeight)
            frameBuffer = b''
            cv2.imshow("preview", image)
            display_fps()
        else :
            print("[warinng]: Serial port received data: {} and display the required amount of data {}".format(len(frameBuffer),bytesPerFrame))
        if (cv2.waitKey(1) == ord('q')):
            break
        
    _serial.close()