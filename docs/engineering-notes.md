# 问题复盘与验证边界

以下区分过程记录中的现象、建议排查与本次整理修正，不将聊天中的建议自动视为已验证解决。

| 问题 | 记录/代码证据 | 整理与排查 |
|---|---|---|
| ROS master 未启动 | Unable to register with master / Connection refused | 先启动 roscore，检查终端 ROS 环境和 master 地址 |
| RealSense 节点不可执行或找不到 | Cannot locate realsense2_camera_node | 检查对应驱动安装和工作空间；当前入口直接使用 SDK，不依赖该相机节点 |
| ROS launch 参数整数溢出 | int exceeds XML-RPC limits | 核对超长编号等参数是否误解析成整数；记录中有显式类型方案，不能当作全部环境已修好 |
| D435 未连接或 RGB 模块异常 | No device connected / RGB modules inconsistency | 检查USB、设备枚举、进程占用和驱动匹配 |
| 普通 VideoCapture 索引打不开 | 多个 /dev/video 设备、camera index out of range | 保存记录后续采用 pyrealsense2 指定彩色流，减少索引歧义 |
| venv 创建失败 | ensurepip unavailable | 安装匹配的 Python venv 支持后重建 |
| 找不到 ultralytics / 找不到脚本 | 未激活环境、运行目录不匹配 | 在目标解释器安装依赖，确认当前目录 |
| 安装依赖出现代理拒绝连接 | ProxyError、Connection refused | 检查代理与网络，不能仅据此判断包不存在 |
| C++/catkin 编译错误 | CMake配置错误、代码行尾多余字符 | 属于历史环境及实验过程；当前公开主线为 Python |
| 类别错位 | main、last、data.yaml顺序冲突 | 本次改为读取 checkpoint names，消除手写序号假设 |
| 偏移无类别身份 | 旧字符串只有dx/dy | 本次为每类绑定编号、名称与均值，使用独立JSON话题 |
| 训练输出提示错误 | train.py写死输出目录名称，不能反映每次实际保存路径 | 采用框架实际输出，不据提示字符串判断模型版本 |

## 数据检查

当前数据快照：训练3929张、验证72张；无同名标签分别167张、19张，可能有背景样本或漏标。classes.txt 为辅助类别表，不是检测框文件。无标签图片需人工确认，不自动补造标注。

检查两组图片的SHA-256未发现字节完全相同的图片交叉，但不能排除同源照片、相邻视频帧或同一合成素材产生的泄漏。没有历史不可变数据快照，所以不能证明现在的目录与训练当时完全一致。

## 保留的限制

没有目标跟踪或跨ROI去重；不能由单帧计数累加得到整场不同动物总数。固定高度误差会缩放位置结果，相机倾斜和图像畸变未补偿。相机30FPS不代表推理速度；5帧窗口可能造成延迟。报告的 mAP 是历史验证日志，不是飞行现场指标。

## 建议实机验证

依次验证五类名称与通信编号、空场与单目标、多只同类动物、目标移出后归零、不同高度与已知标尺偏移、ROS延迟。未验证前，不将整理版输出直接接入无人机闭环控制。
