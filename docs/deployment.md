# 运行说明

## 环境

历史记录使用 Ubuntu 20.04 / ROS Noetic 的 Python 环境。ROS 1 的 `rospy`、`std_msgs` 由 ROS 安装提供，不是普通 pip 依赖。D435 还需要工作正常的 RealSense 驱动、USB 连接和 Python SDK。

本仓库固定历史 Ultralytics 8.2.103；其余依赖没有完整历史锁定清单。先为目标硬件安装兼容的 PyTorch/torchvision，再安装 requirements.txt。GPU 是训练设备选项，不代表历史 NUC 推理一定使用 GPU。

```bash
source /opt/ros/noetic/setup.bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python tools/inspect_intrinsics.py
```

相机程序读取 1280×720、BGR8、30 FPS 彩色流。读取内参和推理必须使用相同模式。程序直接使用 SDK，不要让另一个 RealSense ROS 相机节点同时占用同一台设备。

## 数据采集和制作

```bash
python tools/capture_d435.py --output captures
python tools/synthesize_data.py --blocks my_blocks --foreground elephant.png --name elephant --length-cm 30 --output synthetic
python tools/audit_dataset.py --root /path/to/dataset
```

采集窗口空格拍照、Esc 退出。合成背景是同尺寸的正方形 PNG，每张对应 50cm 方格；前景必须是 RGBA。脚本保留原始旋转贴图思路，框为旋转后图像的外接矩形，可能包含透明留白；需要人工抽查。图片合成不是比赛现场采集的替代品。

先按源照片/视频/背景素材分训练验证，再合成增强。不要随机拆分同一素材的近重复版本。缺失标签应明确是背景图或补齐标注，不自动当作漏标修复。

## 训练

复制配置模板为 `config/data.local.yaml`，将 path 改为本机数据集根目录，包含 images/train、images/val、labels/train、labels/val。默认模型标签顺序为狼、虎、猴、孔雀、象。

```bash
python training/train.py --data config/data.local.yaml --device 0
```

CPU 可用 `--device cpu`。默认从 yolov8n.pt 初始化；首次需要获得对应预训练权重。运行入口沿用保存的训练主参数，不保证重训逐位复现历史 best.pt。查看实际输出目录，不依赖旧脚本中写死的 train13 提示。

## 识别与 ROS

终端一：source ROS 环境后运行 `roscore`。

终端二：source ROS 环境并激活 Python 环境，从仓库根运行：

```bash
python inference/ros_publisher.py --weights models/best.pt --height-cm 120
```

终端三：同样准备环境，运行：

```bash
python inference/ros_subscriber.py
```

`--height-cm` 是相机到目标平面的实际设定距离，不是从深度流自动测得。`--roi-cm` 默认为 50，`--conf` 默认为 0.25。YOLO 推理未显式设置 imgsz，使用安装框架的预测默认值；训练 imgsz=960 不代表推理也固定为960。

## 验证

```bash
python -m unittest discover -s tests -v
```

测试不访问相机、不启动 ROS、不执行飞行控制。实机还需确认类别、位置轴向、延迟、空场误检、目标移出后输出归零、稳定窗口以及高度变化误差。
