# ROS 2 System Monitor

[![ROS 2 Humble](https://github.com/lotus1282/ros2-system-monitor/actions/workflows/ros2-humble.yml/badge.svg)](https://github.com/lotus1282/ros2-system-monitor/actions/workflows/ros2-humble.yml)

一个基于 **ROS 2 Humble + Python + Qt** 的实时系统状态监视示例，包含两个包：

| 包 | 类型 | 作用 |
| --- | --- | --- |
| `system_monitor_interfaces` | `ament_cmake` | 定义自定义消息 `SystemStatus.msg` |
| `system_monitor_gui` | `ament_python` | 采集本机状态并发布；用 Qt 窗口订阅并展示 |

## 功能

- 每秒采集一次系统状态
- 记录采样时间、主机名
- CPU 使用率
- 内存使用率、总内存、已用内存、可用内存
- 网络累计接收/发送字节数
- 根据相邻两次采样计算网络接收/发送速率
- Qt 深色仪表盘：CPU/内存进度条、网络卡片、LIVE/STALE 状态
- 无桌面环境时可只启动发布者，用 `ros2 topic echo` 查看数据

## 架构

```text
┌──────────────────────────────┐
│ system_status_publisher      │
│  psutil → SystemStatus.msg   │
└──────────────┬───────────────┘
               │  /system_status
               ▼
┌──────────────────────────────┐
│ system_status_gui            │
│  rclpy subscription + PyQt5  │
└──────────────────────────────┘
```

两个可执行程序都在 `system_monitor_gui` 包中：一个负责采集/发布，一个负责 Qt 展示；消息定义独立放在接口包中。

## 环境要求

- Ubuntu 22.04
- ROS 2 Humble
- Python 3.10+
- `python3-pyqt5`
- `python3-psutil`

安装依赖：

```bash
sudo apt update
sudo apt install -y \
  ros-humble-desktop \
  python3-pyqt5 \
  python3-psutil \
  python3-colcon-common-extensions \
  python3-rosdep
```

如果已经安装 ROS 2 Humble，只需补装：

```bash
sudo apt install -y python3-pyqt5 python3-psutil
```

## 构建

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
git clone https://github.com/lotus1282/ros2-system-monitor.git
cd ~/ros2_ws

source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

## 运行

一键启动发布者和 Qt 窗口：

```bash
ros2 launch system_monitor_gui system_monitor.launch.py
```

也可以分开启动：

```bash
# 终端 1：采集并发布
ros2 run system_monitor_gui system_status_publisher

# 终端 2：打开 Qt 窗口
ros2 run system_monitor_gui system_status_gui
```

## 无桌面 / SSH 环境

只启动发布者，然后用命令行检查：

```bash
ros2 run system_monitor_gui system_status_publisher
ros2 topic echo /system_status
ros2 topic hz /system_status
```

Qt 窗口需要 `DISPLAY` 或 `WAYLAND_DISPLAY`。通过 SSH 使用时，请用 `ssh -X` / `ssh -Y`，或在带桌面的机器上运行 GUI。

## 消息定义

`system_monitor_interfaces/msg/SystemStatus.msg`：

```text
builtin_interfaces/Time stamp
string hostname
float32 cpu_percent
float32 memory_percent
uint64 memory_total
uint64 memory_used
uint64 memory_available
uint64 net_bytes_recv
uint64 net_bytes_sent
float32 net_recv_rate
float32 net_send_rate
```

字段说明：

- `stamp`：采样时间（ROS 时间）
- `hostname`：主机名
- `cpu_percent`：全系统 CPU 使用率，0–100
- `memory_percent`：物理内存使用率，0–100
- `memory_total` / `memory_used` / `memory_available`：字节
- `net_bytes_recv` / `net_bytes_sent`：自开机以来累计字节数
- `net_recv_rate` / `net_send_rate`：相邻采样间的速率，字节/秒

## 参数

发布者支持一个参数：

```bash
ros2 run system_monitor_gui system_status_publisher \
  --ros-args -p publish_rate_hz:=2.0
```

默认 `1.0` Hz。频率必须大于 0，否则会回退到 `1.0` Hz。

## 目录结构

```text
ros2-system-monitor/
├── system_monitor_interfaces/
│   ├── CMakeLists.txt
│   ├── package.xml
│   └── msg/SystemStatus.msg
└── system_monitor_gui/
    ├── launch/system_monitor.launch.py
    ├── resource/system_monitor_gui
    ├── system_monitor_gui/
    │   ├── formatting.py
    │   ├── gui_node.py
    │   └── publisher_node.py
    ├── test/test_formatting.py
    ├── package.xml
    ├── setup.cfg
    └── setup.py
```

## 测试

格式化函数的单元测试不依赖 ROS 运行时：

```bash
cd ~/ros2_ws
colcon test --packages-select system_monitor_gui
colcon test-result --verbose
```

也可以直接运行：

```bash
python3 -m pytest src/ros2-system-monitor/system_monitor_gui/test
```

## 常见问题

**`ModuleNotFoundError: No module named 'system_monitor_interfaces'`**

先构建接口包，并确认已 `source install/setup.bash`：

```bash
colcon build --packages-select system_monitor_interfaces
source install/setup.bash
```

**Qt 报错 `could not connect to display`**

当前会话没有图形显示。请在桌面终端运行 GUI，或使用 `ssh -X`。

**窗口一直显示 `WAITING`**

确认发布者已启动：

```bash
ros2 node list
ros2 topic echo /system_status
```

## License

MIT
