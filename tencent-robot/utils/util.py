import base64
import cv2
import numpy as np
def convertBase64(path):
    img_stream = ''
    with open(path, 'rb') as imgFile:
        img_stream = imgFile.read()
        img_stream = base64.b64encode(img_stream).decode()
    return img_stream

def sobel (img):
	'''
	Detects edges using sobel kernel
	'''
	opImgx = cv2.Sobel(img,cv2.CV_8U,0,1,ksize=3)	#detects horizontal edges
	opImgy = cv2.Sobel(img,cv2.CV_8U,1,0,ksize=3)	#detects vertical edges
	#combine both edges
	return cv2.bitwise_or(opImgx,opImgy)	#does a bitwise OR of pixel values at each pixel

def sketch(ori_img):
	img_gray = cv2.cvtColor(np.asarray(ori_img), cv2.COLOR_BGR2GRAY)

	img_gray_inv = 255 - img_gray
	img_blur = cv2.GaussianBlur(img_gray_inv, ksize=(21, 21),
															sigmaX=0, sigmaY=0)
	img_blend = dodgeV2(img_gray, img_blur)
	return img_blend


def dodgeV2(image, mask):
    return cv2.divide(image, 255 - mask, scale=256)
