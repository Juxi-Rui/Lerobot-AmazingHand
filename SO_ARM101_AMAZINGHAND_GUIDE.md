# SO-ARM101 + AmazingHand 遥操作复现教程

本教程基于 **LeRobot v0.6.2 定制分支（即本仓库）**，实现 SO-ARM101 从动臂 + AmazingHand 灵巧手的遥操作、数据采集与训练复现。

---

## 1. 系统与硬件概览

| 设备 | 串口（示例） | 舵机型号 | 说明 |
|---|---|---|---|
| 主动臂（Leader） | `COM54` | 1、3 号 `sts3215-C044`；2 号 `sts3125-C001`；4-6 号 `sts3215-C046` | 遥操作输入，**保留 6 号夹爪舵机** |
| 从动臂（Follower） | `COM58` | `sts3215-C018`（仅 1-5 号） | 执行端，**已拆除 6 号夹爪舵机** |
| AmazingHand 灵巧手 | `COM11` | `scs0009`（8 个，ID 1-8） | 从动臂末端执行器，独立串口 |

> **注意：三个设备必须各自独立串口、独立供电**。SCS0009（协议 1）与 STS3215（协议 0）不能共用总线；同进程混用 lerobot 串口栈会互相污染（本项目手走 rustypot 独立栈规避）。

### 硬件准备
- 使用 3D 打印转接件将 AmazingHand 安装到 SO-ARM101 从动臂腕部（替换原 6 号夹爪）
- 三路 USB 转串口分别连接三个设备
- 每个设备独立供电

---

## 2. 环境搭建

### 2.1 安装依赖

```bash
cd D:\Project\Lerobot-AmazingHand   # 换成你克隆本仓库的目录

# 创建虚拟环境（务必使用 64 位 Python，路径换成你本机的解释器）
uv venv --python "<64位 python 的绝对路径>" .venv

# 激活环境（Windows PowerShell）
.\.venv\Scripts\Activate.ps1

# 安装项目含 AmazingHand 支持
uv pip install -e ".[amazinghand]"
```

> **注意 1（Windows 位数）**：`uv run` 在 Windows 上可能默认选中 32 位 Python 导致 `numpy`/`torch` 安装失败。务必用 `uv venv --python <64位解释器绝对路径>` 显式创建。
>
> **注意 2（uv 跨盘缓存）**：若报 `failed to persist temporary file ... (os error 17)`，说明 uv 缓存跨磁盘。执行前设置：
> ```bash
> $env:UV_CACHE_DIR="D:\Project\.uv-cache"; $env:TMPDIR="D:\Project\.uv-tmp"
> ```
>
> **注意 3（本机环境）**：已验证依赖包括 `feetech-servo-sdk`、`rustypot`、`pygame`、`pyserial`，均在 `.[amazinghand]` extra 内。

### 2.2 确认串口

在 Windows 设备管理器 → 端口(COM 和 LPT) 中确认三个设备对应的 COM 口。也可运行：

```bash
lerobot-find-port
```

> **注意**：不同电脑 COM 号不同，后续所有命令中的串口名需替换为实际值。

---

## 3. 标定流程（分三步）

> **标定顺序**：主动臂 → 从动臂+手连接 → 手角度。每步都在**终端交互**执行（需要物理操作）。

### 3.1 标定主动臂

```bash
lerobot-calibrate --teleop.type=so101_leader --teleop.port=COM54 --teleop.id=amazing_hand_leader
```

**交互步骤**：
1. 将主动臂**所有关节移到中间位**，按 Enter
2. 将**每个关节依次推到最大/最小范围**，完成后按 Enter

**验证**：标定文件自动保存到 `C:\Users\<用户名>\.cache\huggingface\lerobot\calibration\teleoperators\so_leader\amazing_hand_leader.json`

> **注意**：标定时机械臂需能自由转动，确保舵机在断电或空载状态。6 号夹爪舵机范围会作为 `gripper.pos`（0~100）的归一化基准，务必标定到位。

### 3.2 标定从动臂（同时连接手）

```bash
lerobot-calibrate --robot.type=so101_amazing_hand --robot.port=COM58 --robot.hand_port=COM11 --robot.id=amazing_hand_follower
```

**交互步骤**：
1. 将从动臂**5 个关节**（无 6 号）移到中间位，按 Enter
2. 将各关节走全行程，按 Enter

**验证**：标定文件保存到 `...\calibration\robots\so101_amazing_hand\amazing_hand_follower.json`

> **注意 1（手扭矩）**：此命令会**自动启用 8 个手舵机的扭矩**（日志显示 `enabling AmazingHand torque`），标定结束手会张开，属正常现象。
>
> **注意 2（GUI 不出现）**：手角度**不使用** lerobot 的 `RangeFinderGUI`，改用第 3 步的专用工具。因此从动臂标定结束后即完成，不会弹出手的 GUI。

### 3.3 标定手角度（专用 GUI）

```bash
lerobot-calibrate-amazing-hand --hand_port COM11
```

**GUI 操作**：
1. 拖动 4 根手指滑块（index/middle/ring/thumb），使手**完全张开**，点击 **`Save Open`**
2. 拖动滑块使手**完全握拳**，点击 **`Save Close`**
3. **自动保存**：两个状态都设置后，窗口顶部弹出绿色横幅 `AUTO-SAVED to ...\hand_angles.json`，终端同步打印路径
4. 关闭窗口（手自动解除扭矩）

**验证**：角度保存到 `...\calibration\robots\so101_amazing_hand\hand_angles.json`，机器人启动时自动加载。

> **注意 1（自动加载）**：机器人每次启动都会读取 `hand_angles.json` 覆盖 config 默认值，**无需改代码**。
>
> **注意 2（滑块语义）**：滑块向 `+` 方向使该指 m1 舵机向 `+angle` 运动、m2 向 `-angle` 运动（镜像）。标定时以**手的实际姿态**为准判断"张开/握拳"，不必关注角度数值。
>
> **注意 3（重复标定）**：只需重标手时，可仅运行本步（前两步已标定可跳过）。

---

## 4. 遥操作

```bash
lerobot-teleoperate \
  --robot.type=so101_amazing_hand \
  --robot.port=COM58 \
  --robot.hand_port=COM11 \
  --robot.id=amazing_hand_follower \
  --teleop.type=so101_leader \
  --teleop.port=COM54 \
  --teleop.id=amazing_hand_leader
```

**效果**：
- 主动臂 5 关节 → 从动臂跟随
- 主动臂夹爪 → AmazingHand 开合（比例跟随：半捏 = 半闭）

> **注意 1（方向验证）**：首次运行务必确认——**夹爪张开 → 手张开；夹爪捏合 → 手闭合**。若方向反了：
> - 手开合方向反 → 调整 `hand_angles.json` 中 `hand_open_angles`/`hand_close_angles` 交换后重新标定
> - 夹爪映射方向反 → 调整 config 中 `gripper_open_pos`/`gripper_close_pos`（本机实测：张开≈97、捏合≈2，故为 `open=100, close=0`）
>
> **注意 2（比例映射）**：`gripper_open_pos=100, gripper_close_pos=0` 表示夹爪张开时 `gripper.pos≈100`、捏合时≈0。若你的主动臂装配方向不同，实测后调整。
>
> **注意 3（可视化）**：加 `--display_data=true` 可打开 rerun 可视化窗口，但需额外安装 `lerobot[viz]` 且 Windows 下可能缺少 Rerun Viewer 可执行文件。不影响遥操作，可不加。
>
> **注意 4（退出）**：按 `Ctrl+C` 停止，程序会自动解除手扭矩并断开连接。

---

## 5. 数据采集（录制数据集）

```bash
lerobot-record \
  --robot.type=so101_amazing_hand \
  --robot.port=COM58 \
  --robot.hand_port=COM11 \
  --robot.id=amazing_hand_follower \
  --robot.cameras='{
    wrist: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30},
    top: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30}
  }' \
  --teleop.type=so101_leader \
  --teleop.port=COM54 \
  --teleop.id=amazing_hand_leader \
  --dataset.repo_id=<你的HF用户名>/soarm_amazing_hand_pick \
  --dataset.num_episodes=20 \
  --dataset.single_task="Pick up the cube with the dexterous hand" \
  --display_data=true
```

**关键参数**：

| 参数 | 说明 |
|---|---|
| `--robot.cameras` | 相机配置。`index_or_path` 为相机索引或视频流路径，`width/height/fps` 必填 |
| `--dataset.repo_id` | 数据集 HF 标识，格式 `{用户名}/{数据集名}` |
| `--dataset.num_episodes` | 录制轮数 |
| `--dataset.single_task` | 任务描述，写入数据集元数据 |

> **注意 1（相机索引）**：`index_or_path` 需先用 `lerobot-find-cameras` 确认相机编号，不同电脑不同。
>
> **注意 2（录制协议）**：录制时主动臂操作 → 从动臂+手执行 → 数据（关节角 + 相机图像）同步记录。每轮录制结束按键确认，按提示操作。
>
> **注意 3（数据集位置）**：未推送到 HF 时，数据保存在本地缓存，训练时用同一 `--dataset.repo_id` 引用。

---

## 6. 训练策略

```bash
lerobot-train \
  --dataset.repo_id=<你的HF用户名>/soarm_amazing_hand_pick \
  --policy.type=act \
  --output_dir=outputs/train/soarm_amazing_hand_pick \
  --job_name=soarm_amazing_hand_pick \
  --policy.device=cuda \
  --wandb.enable=false \
  --policy.push_to_hub=false \
  --steps=60000
```

> **注意 1（GPU）**：`--policy.device=cuda` 需要 CUDA 版 torch。Windows 上如未装 CUDA torch 会报错，改用 `--policy.device=cpu`（训练慢很多）或安装对应 CUDA 版本。
>
> **注意 2（步骤数）**：`--steps=60000` 为 ACT 策略典型值。任务复杂可加大，简单任务可减小。
>
> **注意 3（wandb）**：`--wandb.enable=false` 关闭权重日志，避免需要 wandb 账号。

---

## 7. 部署 / 评估

```bash
lerobot-rollout \
  --strategy.type=episodic \
  --policy.path=outputs/train/soarm_amazing_hand_pick/checkpoints/last/pretrained_model \
  --robot.type=so101_amazing_hand \
  --robot.port=COM58 \
  --robot.hand_port=COM11 \
  --robot.id=amazing_hand_follower \
  --robot.cameras='{
    wrist: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30},
    top: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30}
  }' \
  --dataset.repo_id=<你的HF用户名>/rollout_soarm_amazing_hand_eval \
  --dataset.num_episodes=10 \
  --dataset.single_task="Pick up the cube with the dexterous hand" \
  --task="Pick up the cube with the dexterous hand" \
  --display_data=true
```

策略加载后由模型自主控制从动臂+手执行任务，并逐轮录制评估数据。

> **注意**：策略部署**必须用 `lerobot-rollout`**。本版本 `lerobot-record` 不再接受 `--policy.path`，且缺少 `--teleop.type` 时会直接报错。`--strategy.type=episodic` 的录制行为与 `lerobot-record` 一致（按 `dataset.num_episodes` 逐轮录制 + 轮间复位）；只想空跑不录制则用 `--strategy.type=base`（此时不能带 `--dataset`）。数据集名**必须以 `rollout_` 开头**。

---

## 8. 故障排查

| 现象 | 原因 | 解决 |
|---|---|---|
| `uv run` 报 32/64 位 / numpy 导入错误 | 解释器位数不对 | 用 `uv venv --python <64位解释器>` 重建 |
| `uv` 报跨盘 `os error 17` | 缓存跨磁盘 | 设置 `UV_CACHE_DIR`/`TMPDIR` 到同盘 |
| 主动臂标定报 2307 型号错误 | 臂总线被污染 | 确认未同时连接手总线；本项目手走 rustypot 已规避 |
| 手开合方向反 | 角度语义反 | 重标手或交换 `hand_angles.json` 的 open/close |
| 手张合比例不匹配 | 夹爪映射方向错 | 实测夹爪开/合对应 `gripper.pos`，调整 `gripper_open_pos/close_pos` |
| 手驱动报 `Operation timed out` | 串口忙碌/时序 | 确认手串口未被占用，重试 |
| 标定手无 GUI | 使用了错误命令 | 必须用 `lerobot-calibrate-amazing-hand`（不是 `lerobot-calibrate`） |
| `--display_data=true` 报 rerun 错误 | 可视化依赖缺失 | 去掉该参数，或装 `lerobot[viz]` + Rerun Viewer |

---

## 9. 常见问题（FAQ）

**Q：为什么手不用 lerobot 的 `RangeFinderGUI` 标定？**
A：手走 rustypot 独立串口栈（规避 lerobot 双总线污染缺陷），不使用 `FeetechMotorsBus`。因此用专用的 `lerobot-calibrate-amazing-hand` GUI 标定开合角度。

**Q：`hand_angles.json` 和 config 默认值的关系？**
A：config 里的 `hand_open_angles`/`hand_close_angles` 是后备默认值；`hand_angles.json` 存在时**优先加载**。重新标定手后无需改代码。

**Q：换一台电脑需要重标定吗？**
A：标定文件在 `~/.cache/huggingface/lerobot/calibration/`，换机器需迁移该目录（或重新标定）。`hand_angles.json` 也在此目录。

**Q：Windows/Linux/Mac 差异？**
A：命令相同；差异在**串口名**（Windows `COMx` / Linux `/dev/ttyACM*` / Mac `/dev/cu.*`）、**调用方式**（`.venv\Scripts\` vs `.venv/bin/`）和 **UV 位数/设备权限**（Linux 需 `sudo chmod 666 /dev/ttyACM*`）。
