# Portfolio adaptation of the saved last.txt candidate; see docs/provenance.md.
import argparse
import json
from pathlib import Path
import pyrealsense2 as rs
import numpy as np
from ultralytics import YOLO
import rospy
from std_msgs.msg import String
from collections import deque
from detection_core import class_mapping, summarize

# 2. 输出编号顺序，永远是 01-elephant, 02-tiger, 03-wolf, 04-monkey, 05-peacock
name_to_num = {
    'elephant': '01',
    'tiger':    '02',
    'wolf':     '03',
    'monkey':   '04',
    'peacock':  '05'
}
output_order = ['elephant', 'tiger', 'wolf', 'monkey', 'peacock']

def get_d435_intrinsics(width=1280, height=720, fps=30):
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, fps)
    profile = pipeline.start(config)
    color_stream = profile.get_stream(rs.stream.color)
    intr = color_stream.as_video_stream_profile().get_intrinsics()
    pipeline.stop()
    return intr

def get_center_roi(width, height, fx, fy, camera_height_cm, roi_size_cm=50):
    roi_w = int(roi_size_cm * fx / camera_height_cm)
    roi_h = int(roi_size_cm * fy / camera_height_cm)
    x1 = width // 2 - roi_w // 2
    y1 = height // 2 - roi_h // 2
    x2 = x1 + roi_w
    y2 = y1 + roi_h
    return x1, y1, x2, y2

def main():
    parser = argparse.ArgumentParser(description="D435 color + YOLOv8 fixed-height planar offsets")
    parser.add_argument('--weights', required=True, type=Path)
    parser.add_argument('--height-cm', type=float, required=True)
    parser.add_argument('--roi-cm', type=float, default=50)
    parser.add_argument('--conf', type=float, default=0.25)
    parser.add_argument('--topic', default='/animal_detections')
    args = parser.parse_args()
    if not args.weights.is_file():
        parser.error('weights file does not exist')
    if not (0 < args.height_cm < float('inf') and 0 < args.roi_cm < float('inf')):
        parser.error('height and ROI must be finite positive numbers')
    if not 0 <= args.conf <= 1:
        parser.error('conf must be between 0 and 1')
    rospy.init_node('animal_publisher', anonymous=True)
    pub = rospy.Publisher(args.topic, String, queue_size=10)

    model = YOLO(str(args.weights))
    clsid_to_name = class_mapping(model.names)

    # 获取D435内参
    intr = get_d435_intrinsics(width=1280, height=720, fps=30)
    camera_height_cm = args.height_cm
    x1, y1, x2, y2 = get_center_roi(intr.width, intr.height, intr.fx, intr.fy, camera_height_cm, roi_size_cm=args.roi_cm)
    if not (0 <= x1 < x2 <= intr.width and 0 <= y1 < y2 <= intr.height):
        raise ValueError("ROI outside image or too small; check height/ROI")
    roi_pixel_w = x2 - x1
    roi_pixel_h = y2 - y1
    x_cm_per_pix = args.roi_cm / roi_pixel_w
    y_cm_per_pix = args.roi_cm / roi_pixel_h
    roi_cx = (x1 + x2) // 2
    roi_cy = (y1 + y2) // 2

    pipeline = None
    started = False

    # 滑动窗口队列
    window_size = 5
    counts_queue = deque(maxlen=window_size)
    offsets_queue = deque(maxlen=window_size)

    print(f"Publishing fixed-height planar estimates to {args.topic}; Ctrl+C to stop.")
    try:
        pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.color, intr.width, intr.height, rs.format.bgr8, 30)
        pipeline.start(config)
        started = True

        while not rospy.is_shutdown():
            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            if not color_frame:
                continue
            frame = np.asanyarray(color_frame.get_data())

            results = model(frame, conf=args.conf, verbose=False)

            # 统计本帧所有目标（按真实动物名计数/偏移）
            det_count = {name: 0 for name in output_order}
            offsets_list = {name: [] for name in output_order}
            boxes = results[0].boxes
            for box in boxes:
                cls_id = int(box.cls[0].item())
                if cls_id in clsid_to_name:
                    name = clsid_to_name[cls_id]
                    x_min, y_min, x_max, y_max = box.xyxy[0].cpu().numpy()
                    animal_cx = int((x_min + x_max) / 2)
                    animal_cy = int((y_min + y_max) / 2)
                    if x1 <= animal_cx < x2 and y1 <= animal_cy < y2:
                        det_count[name] += 1
                        dx_pix = animal_cx - roi_cx
                        dy_pix = animal_cy - roi_cy
                        dx_cm = dx_pix * x_cm_per_pix
                        dy_cm = dy_pix * y_cm_per_pix
                        offsets_list[name].append((dx_cm, dy_cm))

            counts_queue.append(det_count.copy())
            offsets_queue.append({k: v[:] for k, v in offsets_list.items()})

            # 当队列满时进行投票/均值稳定输出
            if len(counts_queue) == window_size:
                records = summarize(counts_queue, offsets_queue)
                payload = {'schema_version': 1, 'stamp': rospy.Time.now().to_sec(),
                           'coordinate_frame': 'image_center_x_right_y_down',
                           'method': 'fixed_height_plane', 'height_cm': args.height_cm,
                           'window_frames': window_size, 'animals': records}
                msg_str = json.dumps(payload, allow_nan=False)
                pub.publish(msg_str)
                rospy.loginfo(f"发布: {msg_str}")

    finally:
        if pipeline is not None and started:
            pipeline.stop()

if __name__ == "__main__":
    main()
