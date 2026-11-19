# 材料来源与整理变更

用户确认最终路线是 D435 + YOLOv8，使用固定高度换算平面偏移。原比赛报告中描述的其他视觉方案不作为最终实现证明。个人贡献为数据采集与标注、训练、定位和 ROS 通信。

| 整理后内容 | 原材料 | 处理 |
|---|---|---|
| ros_publisher.py | 电赛记录 last.txt | 保留 ROI、固定高度换算、5帧投票与分类均值思路；移除写死类别映射，增加路径参数；消息明确绑定类别 |
| ros_subscriber.py | animal_subscriber.txt 的接收展示用途 | 重新编写 JSON 接收端，不宣称为原赛场订阅器 |
| training/train.py | yolov8/train.py、train13/args.yaml | 路径参数化；保留88轮、960输入、16批次；修正固定输出目录提示 |
| capture_d435.py | python/paizhao.py | 输出路径参数化，保存名加入微秒 |
| synthesize_data.py | python/1jiaoben_30.py | 前景、背景、类别、尺寸、数量参数化；统一类别编号；检查旋转后贴图尺寸 |
| inspect_intrinsics.py | python/d435.py 和发布端内参读取 | 仅提取内参检查用途，不复制去畸变显示实验 |
| audit_dataset.py | 整理阶段新增 | 只读统计，排除 classes.txt 辅助文件 |
| 模型与图表 | runs/detect/train13 | 权重、CSV和两张曲线图原样复制；args中的本机绝对数据路径替换为模板路径 |

## 重要变更不是赛场功能

旧 main/last 中的类别 ID 映射与 train13 checkpoint 不一致。整理版以 `model.names` 为准，再映射为通信编号 01象、02虎、03狼、04猴、05孔雀。

旧消息将数量和匿名偏移串在一起，接收端无法可靠知道偏移属于哪一类。整理版改用 `/animal_detections` 上的 JSON，每类始终带名称、编号、数量与均值位置。它是独立展示协议，**与旧 `/animal_result` 接口不兼容**。数量为0时均值设null，避免显示空类别的历史位置。

不增加自动飞行、逐目标跟踪、深度图测距或世界坐标变换。原逻辑对同类所有目标和窗口帧取均值，该均值不一定落在某只动物身上，不应直接用作多目标激光指向。

## 比赛最终模型

项目作者于2026年11月20日回忆比赛使用的是 train13，并指定按该版本整套整理。当前模型来源为本地 train13/weights/best.pt。仓库以 models/best.pt 保存，文件字节未改动。SHA-256：

`fea01cd19b0191f8dbae888c29d24ad9c1b04397c1a11b9ef23a1cbe30ca2ba1`

比赛版本依据项目作者回忆与本次指定；checkpoint 的 names 和版本通过静态 pickle 操作码读取，文件复制一致性通过 SHA-256 校验。本次整理未重新加载模型推理，未额外核验赛场设备副本。

## 未纳入公开仓库

原始过程聊天、Word、PDF、全量训练图与赛题动物素材、桌面录屏、虚拟环境、框架源码、C++编译产物、USB相机及HSV传统视觉实验、通用RealSense教程。教程中的示例与建议不等于实际执行记录。
