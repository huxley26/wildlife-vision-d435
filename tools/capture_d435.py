import pyrealsense2 as rs
import cv2
import os
import datetime
import numpy as np

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True)
save_dir = parser.parse_args().output
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
pipeline.start(config)





print("按空格拍照，按ESC退出...")

try:
    while True:
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        if not color_frame:
            continue

        color_image = np.asanyarray(color_frame.get_data())
        cv2.imshow('RealSense', color_image)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC键
            print("退出")
            break
        elif key == 32:  # 空格键
            filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".jpg"
            save_path = os.path.join(save_dir, filename)
            cv2.imwrite(save_path, color_image)
            print(f"已保存：{save_path}")

finally:
    pipeline.stop()
    cv2.destroyAllWindows()
