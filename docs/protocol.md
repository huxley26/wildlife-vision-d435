# 整理版 ROS 消息

类型：`std_msgs/String`；话题：`/animal_detections`；内容：JSON。

```json
{
  "schema_version": 1,
  "stamp": 123.4,
  "coordinate_frame": "image_center_x_right_y_down",
  "method": "fixed_height_plane",
  "height_cm": 120,
  "window_frames": 5,
  "animals": [
    {"code": "01", "name": "elephant", "count": 1, "mean_offset_cm": [2.0, -3.0]},
    {"code": "02", "name": "tiger", "count": 0, "mean_offset_cm": null},
    {"code": "03", "name": "wolf", "count": 0, "mean_offset_cm": null},
    {"code": "04", "name": "monkey", "count": 0, "mean_offset_cm": null},
    {"code": "05", "name": "peacock", "count": 0, "mean_offset_cm": null}
  ]
}
```

stamp 是发布时 ROS 时间，不是硬件采集时间。count 是最近5帧众数，平票沿用 Counter 首次出现顺序；mean_offset_cm 是该类窗口内全部检测中心的均值，不保证与众数数量一一对应，不是逐个目标轨迹。首5帧不足时不发布，数量为0时位置为空。

位置是相对图像中央ROI中心的估算厘米偏移，x向右、y向下。用指定高度和焦距计算 ROI，再按像素比例换算，不使用深度图。相机倾斜、畸变、错误高度、目标离地、窗口延迟都会造成误差。原点不是相机主点或地面全局原点。
