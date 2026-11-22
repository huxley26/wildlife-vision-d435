# UAV wildlife detection and ground-plane localization

[中文说明](#中文说明)

I led the vision module for a UAV survey task in the 2025 National Undergraduate Electronic Design Contest. Using color images from an Intel RealSense D435, the system detects five animal classes, counts those inside a central survey area and publishes their offsets to an onboard computer over ROS. Our team earned second prize in Jiangsu.

## From camera frames to survey results

I collected and labeled images, trained the YOLOv8n detector, and integrated camera acquisition, localization and ROS messaging. When the initial model overfit, I supplemented the synthetic training images with field photographs and retrained the detector.

1. **Detect and filter.** A color frame goes through YOLOv8n. The camera intrinsics and known camera height define a central 50 × 50 cm region on the ground plane.
2. **Estimate position.** The system converts image offsets to centimeters assuming a downward-facing camera and approximately level ground. It uses the color stream and a supplied height; the output is relative to the image center.
3. **Aggregate and publish.** A five-frame vote stabilizes class counts. The module averages offsets by class and publishes the results as JSON in a ROS 1 string message. A class mean describes the group when multiple targets share a class.

[Detection and aggregation logic](inference/detection_core.py) · [ROS publisher](inference/ros_publisher.py) · [Message fields and coordinate convention](docs/protocol.md)

## Historical validation results

The repository includes the [train13 checkpoint](models/best.pt), its [checksum](models/SHA256SUMS) and the [epoch log](reports/train13/results.csv). The model was trained for 88 epochs at image size 960 with batch size 16. Its five classes are wolf, tiger, monkey, peacock and elephant.

| Historical validation record | mAP@0.50 | mAP@0.50:0.95 |
| --- | ---: | ---: |
| Published best checkpoint, epoch 35 | 99.25% | 65.32% |
| Final logged epoch, epoch 88 | 97.12% | 61.34% |

These scores describe the saved training run. Field performance and end-to-end latency would need separate measurements. A later [dataset audit](reports/dataset_audit.json) found that 19 of the 72 available validation images lacked matching label files. Their status as intentional background examples or missing annotations remains unresolved. The full image dataset is outside this release.

[Training curves](reports/train13/results.png) · [Confusion matrix](reports/train13/confusion_matrix.png) · [Training entry point](training/train.py)

## Run the project

**Without hardware.** Run the [five regression tests](tests/test_logic.py) from the repository root. They cover class ordering, count and offset aggregation, fixed-height geometry and checkpoint integrity.

```bash
python -m unittest discover -s tests -v
```

**With a D435 and ROS 1.** The historical setup used Ubuntu 20.04 and ROS Noetic. Prepare ROS, RealSense and the Python dependencies using the [deployment guide (Chinese)](docs/deployment.md). Source the ROS environment in each terminal. Start `roscore` in the first terminal, then run the following from the repository root in two more terminals.

```bash
# Terminal 2: set the height to the measured camera-to-plane distance in cm.
python inference/ros_publisher.py --weights models/best.pt --height-cm 120
```

```bash
# Terminal 3: inspect the messages published on /animal_detections.
python inference/ros_subscriber.py
```

This release reconstructs the vision module from competition materials. Hardware-independent checks have been run; the published snapshot still awaits an end-to-end D435/ROS retest. Flight control and route planning belonged to other parts of the team project.

[Dataset configuration](config/data.example.yaml) · [Collection and dataset tools](tools/) · [Source history and changes](docs/provenance.md) · [Third-party components](THIRD_PARTY.md)

## 中文说明

### D435 + YOLOv8 野生动物识别与平面定位

电赛野生动物巡查项目的视觉部分：用 Intel RealSense D435 获取彩色图像，使用本地训练的 YOLOv8 检测五类动物，在中央区域统计数量，以相机内参和固定高度估计平面偏移，通过 ROS 发布结果。

**个人负责：数据采集与标注、YOLOv8 训练、D435 定位及 ROS 通信。** 无人机飞控、航线规划和地面站不在本仓库实现范围内。

本仓库由保存的比赛材料整理而成。定位方式已确认是固定高度换算，主程序没有读取深度图。代码是整理后的展示版本，不是逐字复原的赛场快照；修改范围见 [来源与变更](docs/provenance.md)。

## 处理流程

```text
D435 彩色图像 + 同分辨率内参
          ↓
YOLOv8 检测框、类别、置信度
          ↓
中央 50 cm × 50 cm ROI 筛选
          ↓
给定高度 → 像素偏移换算为厘米
          ↓
5 帧数量投票 + 按类别平均偏移
          ↓
ROS String(JSON) 发布 / 订阅展示
```

该偏移以图像中心为原点、向右和向下为正，依赖相机近似垂直地面、地面近似平坦和高度已知。不是地理坐标、飞控坐标或动态三维测距；不包含逐目标跟踪与跨方格去重。

## 目录

| 路径 | 内容 |
|---|---|
| `training/train.py` | YOLOv8n 训练入口 |
| `config/data.example.yaml` | 五类数据配置模板 |
| `tools/` | D435 采集、内参读取、合成数据与标签检查 |
| `inference/` | D435 识别及 ROS 发布、订阅 |
| `models/best.pt` | 按比赛使用版本整理的 train13 模型权重 |
| `reports/train13/` | 88 轮历史训练日志、曲线、混淆矩阵 |
| `docs/` | 运行说明、消息协议、问题复盘、证据边界 |
| `tests/` | 不需要相机的逻辑回归检查 |

## 模型与训练证据

仓库按项目作者回忆的比赛使用版本，附带 train13 的 `best.pt` 权重，来自本地 `runs/detect/train13/weights/best.pt`，配套保存训练配置、日志与评估曲线。权重字节保持不变；SHA-256 见 [校验文件](models/SHA256SUMS)。

checkpoint 中的类别顺序为 `wolf, tiger, monkey, peacock, elephant`，版本元数据为 Ultralytics 8.2.103；训练记录为 YOLOv8n、88 epochs、imgsz 960、batch 16。best.pt 保存的历史验证指标对应第35轮：mAP50 为 0.99254、mAP50-95 为 0.65320；第88轮日志分别为 0.97116 和 0.61344。最佳权重与最后一轮结果分开记录，这些都不是赛场实测准确率或本次重新评估结果。

![历史训练曲线](reports/train13/results.png)

![历史混淆矩阵](reports/train13/confusion_matrix.png)

## 开始使用

完整步骤见 [运行说明](docs/deployment.md)。具备 D435、ROS 1 及依赖环境后，从仓库根目录运行：

```bash
python inference/ros_publisher.py --weights models/best.pt --height-cm 120
python inference/ros_subscriber.py
```

两个程序分别在两个终端运行，ROS master 需已启动。默认发布话题为 `/animal_detections`，使用整理版 JSON 协议，不能直接替换旧 `/animal_result` 字符串接口。运行频率随模型推理耗时变化，30 FPS 相机配置不等于端到端处理达到 30 FPS。

## 数据与验证边界

不附带整套训练图片、原始聊天记录、比赛报告、第三方框架源码和飞控代码。合成脚本需要自备有权使用的背景与透明前景图，合成时必须保持标签顺序一致。

当前磁盘数据检查发现训练集 3929 张、验证集 72 张图片，其中分别有 167 张和 19 张没有同名标签。这些可能是背景图，也可能是漏标，尚未逐张确认；不能据此认为数据已完全清理。按原始照片、视频或合成素材分组后再划分训练验证集，避免相近素材泄漏。

整理阶段验证 Python 语法、关键逻辑、文件校验和数据标签格式。未在 D435/ROS 实机环境执行、未重新训练或加载模型推理；历史结果与整理后代码的实测表现分开看待。

第三方组件与模型说明见 [THIRD_PARTY.md](THIRD_PARTY.md)。
