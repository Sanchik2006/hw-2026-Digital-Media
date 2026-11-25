import cv2
import numpy as np
#请调用image_compress(img,age)函数，输入图像和压缩年限（0-50，年份越大，压缩越狠），返回压缩后的图像
def map_year(age):
    age=max(1,min(50,age))
    t = (age - 1) / 49.0
    repeat_times = round(1 + t * 5)
    quality_factor = round(2 + t * 3)
    scale_percent = round(0.98 - t * 0.9, 2)
    return repeat_times, quality_factor, scale_percent

def resize(img,scale_percent):

     h,w,channel=img.shape
     target_width=int(w*scale_percent)
     target_height=int(h*scale_percent)

     resized=np.zeros((target_height,target_width,channel),dtype=img.dtype)

     for i in range(0,target_height):
          for j in range(0,target_width):

               prev_h=int(i/scale_percent)
               prev_w=int(j/scale_percent)

               if prev_w>=w: prev_w=w-1
               if prev_h>=h: prev_h=h-1

               resized[i,j]=img[prev_h,prev_w]
     return resized

def JPEG_compress(img,quality_factor,repeat_times):
    YCbCr=cv2.cvtColor(img,cv2.COLOR_BGR2YCrCb)
    YCbCr_float=YCbCr.astype(np.float32)
    h,w,c=YCbCr_float.shape

    pad_h = (8 - h % 8) % 8
    pad_w = (8 - w % 8) % 8
    padded = np.pad(YCbCr_float, ((0, pad_h), (0, pad_w), (0, 0)), mode='edge')
    ph, pw, _ = padded.shape

    base_quant_table = np.array([
        [16, 11, 10, 16,  24,  40,  51,  61],
        [12, 12, 14, 19,  26,  58,  60,  55],
        [14, 13, 16, 24,  40,  57,  69,  56],
        [14, 17, 22, 29,  51,  87,  80,  62],
        [18, 22, 37, 56,  68, 109, 103, 77],
        [24, 35, 55, 64,  81, 104, 113, 92],
        [49, 64, 78, 87, 103, 121, 120, 101],
        [72, 92, 95, 98, 112, 100, 103, 99]
    ], dtype=np.float32)

    quant_table = base_quant_table * quality_factor


    for r in range(repeat_times):
        for i in range(0, ph, 8):
            for j in range(0, pw, 8):
               for ch in range(c):
                    block = padded[i:i+8, j:j+8, ch].astype(np.float32)
                    block -= 128
                    
                    dct_block = cv2.dct(block)
                    quantized = np.round(dct_block / quant_table) * quant_table
                    
                    idct_block = cv2.idct(quantized)
                    idct_block += 128
                    
                    padded[i:i+8, j:j+8, ch] = idct_block

    result_ycbcr = padded[:h, :w]
    result_bgr = cv2.cvtColor(result_ycbcr.astype(np.uint8), cv2.COLOR_YCrCb2BGR)
    return result_bgr

def image_compress(img,age):
    repeat_times, quality_factor, scale_percent=map_year(age)
    resized=resize(img,scale_percent)
    compressed=JPEG_compress(resized,quality_factor,repeat_times)
    return compressed