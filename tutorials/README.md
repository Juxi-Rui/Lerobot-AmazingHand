# SO-ARM101 + AmazingHand 使用教程

本教程面向复现 **SO-ARM101 从动臂 + AmazingHand 灵巧手** 的遥操作、数据采集与训练全流程，基于 LeRobot（本仓库定制版）。

教程按**阶段**组织，每个阶段独立成目录，内部按操作系统拆分 `win.md`（Windows）与 `linux.md`（Linux）两个文档。请根据你的操作系统选择对应文档阅读。

---

## 硬件与软件概览

| 设备 | 串口（示例，需替换） | 舵机型号 | 说明 |
|---|---|---|---|
| 主动臂（Leader） | `COM54` / `/dev/ttyACM1` | 混合型号 | 遥操作输入，保留 6 号夹爪 |
| 从动臂（Follower） | `COM58` / `/dev/ttyACM0` | `sts3215-C018`（1-5 号） | 执行端，拆除 6 号夹爪 |
| AmazingHand 灵巧手 | `COM11` / `/dev/ttyACM2` | `scs0009`（8 个，ID 1-8） | 从动臂末端，独立串口 |

> **⚠️ 串口名因机器而异**：上表为示例。每台电脑的 COM 号/设备路径都不同，务必用 `lerobot-find-port` 确认本机实际值，并替换所有命令中的占位参数。

> 三个设备必须**各自独立串口、独立供电**。SCS0009（协议 1）与 STS3215（协议 0）不兼容于同一总线。

---

## 教程目录结构

```
tutorials/
├── README.md                          # 本文件（总览）
├── 01-environment/                    # 阶段一：环境搭建
│   ├── win.md                         #   Windows 环境搭建
│   └── linux.md                       #   Linux 环境搭建
├── 02-calibration/                    # 阶段二：标定
│   ├── win.md
│   └── linux.md
├── 03-teleoperation/                  # 阶段三：遥操作
│   ├── win.md
│   └── linux.md
├── 04-data-collection/                # 阶段四：数据采集
│   ├── win.md
│   └── linux.md
├── 05-training/                       # 阶段五：模型训练
│   ├── win.md
│   └── linux.md
└── 06-deployment/                     # 阶段六：部署与评估
    ├── win.md
    └── linux.md
```

---

## 推荐阅读路径

| 步骤 | 阶段 | Windows | Linux |
|---|---|---|---|
| 1 | 环境搭建 | [01-environment/win.md](01-environment/win.md) | [01-environment/linux.md](01-environment/linux.md) |
| 2 | 标定 | [02-calibration/win.md](02-calibration/win.md) | [02-calibration/linux.md](02-calibration/linux.md) |
| 3 | 遥操作 | [03-teleoperation/win.md](03-teleoperation/win.md) | [03-teleoperation/linux.md](03-teleoperation/linux.md) |
| 4 | 数据采集 | [04-data-collection/win.md](04-data-collection/win.md) | [04-data-collection/linux.md](04-data-collection/linux.md) |
| 5 | 模型训练 | [05-training/win.md](05-training/win.md) | [05-training/linux.md](05-training/linux.md) |
| 6 | 部署与评估 | [06-deployment/win.md](06-deployment/win.md) | [06-deployment/linux.md](06-deployment/linux.md) |

---

## 各阶段核心差异速查

| 方面 | Windows | Linux |
|---|---|---|
| Python 环境 | Miniconda + `conda create -n lerobot python=3.12` | Miniforge + 同样命令 |
| 串口名 | `COM54` / `COM58` / `COM11`（示例） | `/dev/ttyACM0/1/2`（示例） |
| 串口权限 | 无需特殊配置 | 需 `sudo chmod 666 /dev/ttyACM*` 或 udev 规则 |
| 命令调用 | conda 激活后 `lerobot-xxx` | conda 激活后 `lerobot-xxx` |
| CUDA 训练 | 需手动装 CUDA torch | 官方支持，解析顺畅 |

---

## 通用注意事项

1. **先跑通阶段一，再进入后续阶段**——环境是后续所有命令的前提。
2. **每台电脑必须重新标定**：尤其是手角度（`lerobot-calibrate-amazing-hand`），config 里的角度是 AmazingHand 官方通用默认，仅作后备；`hand_angles.json` 存在时优先加载本机实测值。
3. **标定文件位置**：`~/.cache/huggingface/lerobot/calibration/`，换机器需迁移或重标定。
4. **首次遥操作务必验证方向**：夹爪张开 ↔ 手张开、捏合 ↔ 手闭合。
5. 每个阶段的 `win.md` / `linux.md` 内均包含**该平台特有的注意事项**，请完整阅读。

---

## 故障排查入口

阶段文档内附各平台故障排查表。常见问题：
- conda 未初始化/命令找不到
- 串口权限不足（Linux）
- 手/臂方向映射错误
- 手角度未标定导致开合异常

详见各阶段文档。
