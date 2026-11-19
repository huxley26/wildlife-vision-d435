import cv2
import numpy as np
import os
import glob
import random
import re

import argparse
parser = argparse.ArgumentParser(description='Rotate RGBA foreground onto square background blocks')
parser.add_argument('--blocks', required=True)
parser.add_argument('--foreground', required=True)
parser.add_argument('--output', required=True)
parser.add_argument('--name', required=True, choices=['wolf', 'tiger', 'monkey', 'peacock', 'elephant'])
parser.add_argument('--length-cm', required=True, type=float)
parser.add_argument('--samples', type=int, default=30)
parser.add_argument('--seed', type=int, default=42)
args = parser.parse_args()
if args.length_cm <= 0 or args.samples <= 0:
    parser.error('length and samples must be positive')
random.seed(args.seed)
block_dir = os.path.join(args.blocks, '')
elephant_img_path = args.foreground
output_img_dir = os.path.join(args.output, 'images')
output_txt_dir = os.path.join(args.output, 'labels')
os.makedirs(output_img_dir, exist_ok=True)
os.makedirs(output_txt_dir, exist_ok=True)
animal_class_id = ['wolf', 'tiger', 'monkey', 'peacock', 'elephant'].index(args.name)

def rotate_bound(image, angle):
    (h, w) = image.shape[:2]
    (cX, cY) = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D((cX, cY), angle, 1.0)
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    nW = int((h * sin) + (w * cos))
    nH = int((h * cos) + (w * sin))
    M[0, 2] += (nW / 2) - cX
    M[1, 2] += (nH / 2) - cY
    return cv2.warpAffine(image, M, (nW, nH), borderValue=(0,0,0,0))

# 递增编号自动查找最大
def get_next_counter(img_dir, prefix='elephant_'):
    files = glob.glob(os.path.join(img_dir, f"{prefix}*.jpg"))
    max_num = 0
    for fname in files:
        basename = os.path.splitext(os.path.basename(fname))[0]
        m = re.match(rf"{prefix}(\d+)", basename)
        if m:
            num = int(m.group(1))
            if num > max_num:
                max_num = num
    return max_num + 1

# 格子图片尺寸
backgrounds = sorted(glob.glob(block_dir + '*.png'))
if not backgrounds:
    raise ValueError('No PNG background blocks found')
sample_block = cv2.imread(backgrounds[0])
if sample_block is None or sample_block.shape[0] != sample_block.shape[1]:
    raise ValueError('Backgrounds must be readable square images')
block_px = sample_block.shape[0]
block_cm = 50
px_per_cm = block_px / block_cm

# 读取大象并缩放
elephant_rgba = cv2.imread(elephant_img_path, cv2.IMREAD_UNCHANGED)
if elephant_rgba is None or elephant_rgba.shape[2] != 4:
    raise ValueError("大象图片读取失败或不是透明PNG！")
h0, w0 = elephant_rgba.shape[:2]
long_edge = max(h0, w0)
scale = (args.length_cm * px_per_cm) / long_edge
new_w, new_h = int(w0 * scale), int(h0 * scale)
elephant_rgba = cv2.resize(elephant_rgba, (new_w, new_h), interpolation=cv2.INTER_AREA)

# 递增编号
counter = get_next_counter(output_img_dir, prefix=args.name + '_')

for block_path in backgrounds:
    block_img = cv2.imread(block_path)
    if block_img is None or block_img.shape[:2] != (block_px, block_px):
        raise ValueError("All backgrounds must have the same square dimensions")
    for i in range(args.samples):
        # 随机旋转
        angle = random.randint(0, 359)
        elephant_rot = rotate_bound(elephant_rgba, angle)
        eh, ew = elephant_rot.shape[:2]
        if ew > block_px or eh > block_px:
            raise ValueError("Rotated foreground does not fit background")
        # 随机位置
        bx = random.randint(ew//2, block_px - (ew - ew//2))
        by = random.randint(eh//2, block_px - (eh - eh//2))
        x1 = bx - ew//2
        y1 = by - eh//2

        img_out = block_img.copy()
        # ROI安全贴图
        x_start_bg = max(x1, 0)
        y_start_bg = max(y1, 0)
        x_start_fg = 0 if x1 >= 0 else -x1
        y_start_fg = 0 if y1 >= 0 else -y1
        x_end_bg = min(x1 + ew, block_px)
        y_end_bg = min(y1 + eh, block_px)
        x_end_fg = x_end_bg - x1 + x_start_fg
        y_end_fg = y_end_bg - y1 + y_start_fg

        bg_roi = img_out[y_start_bg:y_end_bg, x_start_bg:x_end_bg]
        fg_roi = elephant_rot[y_start_fg:y_end_fg, x_start_fg:x_end_fg]
        fg_alpha = fg_roi[:,:,3] / 255.0
        for c in range(3):
            bg_roi[:,:,c] = fg_roi[:,:,c]*fg_alpha + bg_roi[:,:,c]*(1-fg_alpha)
        img_out[y_start_bg:y_end_bg, x_start_bg:x_end_bg] = bg_roi

        # 保存图片
        out_img_name = f"{args.name}_{counter:06d}.jpg"
        out_img_path = os.path.join(output_img_dir, out_img_name)
        cv2.imwrite(out_img_path, img_out)

        # YOLO标签
        x_center_norm = bx / block_px
        y_center_norm = by / block_px
        w_norm = ew / block_px
        h_norm = eh / block_px
        txt_content = f"{animal_class_id} {x_center_norm:.6f} {y_center_norm:.6f} {w_norm:.6f} {h_norm:.6f}\n"
        out_txt_name = f"{args.name}_{counter:06d}.txt"
        out_txt_path = os.path.join(output_txt_dir, out_txt_name)
        with open(out_txt_path, 'w') as f:
            f.write(txt_content)
        counter += 1

print('Synthetic images and YOLO labels written. Split original sources before augmentation.')
