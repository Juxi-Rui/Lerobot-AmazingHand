<p align="center">
  <img alt="LeRobot" src="./media/readme/lerobot-logo-thumbnail.png" width="100%">
</p>

# SO-ARM101 + AmazingHand

LeRobot 的定制分支，为 **SO-ARM101 从动臂 + AmazingHand 灵巧手** 增加完整的遥操作、标定、数据采集与策略部署支持。

> A fork of [huggingface/lerobot](https://github.com/huggingface/lerobot) **v0.6.2** that adds an
> `so101_amazing_hand` robot: an SO-ARM101 follower arm whose gripper is replaced by an
> [AmazingHand](https://github.com/pollen-robotics/AmazingHand) dexterous hand.

- 本仓库 / This fork：<https://github.com/Juxi-Rui/Lerobot-AmazingHand>
- 上游仓库 / Upstream：<https://github.com/huggingface/lerobot>
- 本分支基线版本：`lerobot` 0.6.2，Apache-2.0
- 中文教程：[`tutorials/`](tutorials/README.md)（六阶段 × Windows/Linux）· 单文件速查：[`SO_ARM101_AMAZINGHAND_GUIDE.md`](SO_ARM101_AMAZINGHAND_GUIDE.md)

---

## 本分支相对上游新增了什么

| 内容 | 位置 |
|---|---|
| `so101_amazing_hand` 机器人（从动臂 + 手一体控制） | [`src/lerobot/robots/so_amazing_hand/`](src/lerobot/robots/so_amazing_hand/) |
| 手开合角度专用标定 GUI（`lerobot-calibrate-amazing-hand`） | [`src/lerobot/scripts/lerobot_calibrate_amazing_hand.py`](src/lerobot/scripts/lerobot_calibrate_amazing_hand.py) |
| 机器人注册（`robots/utils.py`） | [`src/lerobot/robots/utils.py`](src/lerobot/robots/utils.py) |
| `amazinghand` 依赖 extra | [`pyproject.toml`](pyproject.toml) |
| 六阶段中文教程（环境/标定/遥操作/采集/训练/部署） | [`tutorials/`](tutorials/README.md) |
| 单文件完整速查指南 | [`SO_ARM101_AMAZINGHAND_GUIDE.md`](SO_ARM101_AMAZINGHAND_GUIDE.md) |

其余目录（`policies/`、`datasets/`、`envs/`、`processor/`、`tests/`、`docs/` 等）与上游一致，持续可从上游合并。

---

## 硬件概览

| 设备 | 串口（示例，因机器而异） | 舵机 | 说明 |
|---|---|---|---|
| 主动臂 Leader | `COM54` | 混合型号，含 6 号夹爪 | 遥操作输入，**保留 6 号夹爪舵机** |
| 从动臂 Follower | `COM58` | `sts3215-C018`（1-5 号） | 执行端，**已拆除 6 号夹爪舵机** |
| AmazingHand 灵巧手 | `COM11` | `scs0009` × 8（ID 1-8） | 从动臂末端执行器，独立串口 |

> **三个设备必须各自独立串口、独立供电。** SCS0009（协议 1）与 STS3215（协议 0）不能共用总线；同进程混用 lerobot 的串口栈会互相污染——本分支让手走 `rustypot` 独立栈来规避，这也是手不使用 lerobot `RangeFinderGUI` 而另做专用标定工具的原因。

硬件改装：用 3D 打印转接件把 AmazingHand 装到从动臂腕部，替换原 6 号夹爪。

---

## 快速开始

### 1. 安装

```bash
git clone https://github.com/Juxi-Rui/Lerobot-AmazingHand.git
cd Lerobot-AmazingHand

# 创建虚拟环境（Windows 上务必显式指定 64 位解释器）
uv venv --python <64位 python 绝对路径> .venv

# 安装本分支 + AmazingHand 依赖
uv pip install -e ".[amazinghand]"
```

`amazinghand` extra 含：`feetech-servo-sdk`（臂电机）、`rustypot`（手电机）、`pygame`（标定 GUI）、`pyserial`（串口）。

### 2. 确认串口

```bash
lerobot-find-port
```

三个设备的 COM 号各不相同，后续命令里的串口名都要换成实际值。

### 3. 标定（顺序：主动臂 → 从动臂+手 → 手角度）

```bash
# 3.1 主动臂
lerobot-calibrate --teleop.type=so101_leader --teleop.port=COM54 --teleop.id=amazing_hand_leader

# 3.2 从动臂（同时连上手串口）
lerobot-calibrate --robot.type=so101_amazing_hand --robot.port=COM58 --robot.hand_port=COM11 --robot.id=amazing_hand_follower

# 3.3 手开合角度（专用 GUI，拖到完全张开点 Save Open，完全握拳点 Save Close，自动保存）
lerobot-calibrate-amazing-hand --hand_port COM11
```

第 3 步会把手角度写入 `hand_angles.json`；机器人每次启动自动加载它，覆盖 config 里的默认值，**无需改代码**。

### 4. 遥操作

```bash
lerobot-teleoperate \
  --robot.type=so101_amazing_hand --robot.port=COM58 --robot.hand_port=COM11 \
  --robot.id=amazing_hand_follower \
  --teleop.type=so101_leader --teleop.port=COM54 --teleop.id=amazing_hand_leader
```

主动臂 5 个关节 → 从动臂跟随；主动臂夹爪 → 手按比例开合。**首次运行务必确认方向**：夹爪张开 ↔ 手张开、捏合 ↔ 手闭合。

### 5. 采集数据

```bash
lerobot-record \
  --robot.type=so101_amazing_hand --robot.port=COM58 --robot.hand_port=COM11 \
  --robot.id=amazing_hand_follower \
  --robot.cameras='{ wrist: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30} }' \
  --teleop.type=so101_leader --teleop.port=COM54 --teleop.id=amazing_hand_leader \
  --dataset.repo_id=<你的HF用户名>/soarm_amazing_hand_pick \
  --dataset.num_episodes=20 \
  --dataset.single_task="Pick up the cube with the dexterous hand"
```

### 6. 训练

```bash
lerobot-train \
  --dataset.repo_id=<你的HF用户名>/soarm_amazing_hand_pick \
  --policy.type=act \
  --output_dir=outputs/train/soarm_amazing_hand_pick \
  --job_name=soarm_amazing_hand_pick \
  --policy.device=cuda \
  --wandb.enable=false --policy.push_to_hub=false \
  --steps=60000
```

### 7. 部署 / 评估

策略部署用 **`lerobot-rollout`**（本版本中 `lerobot-record` 不再接受 `--policy`）：

```bash
lerobot-rollout \
  --strategy.type=base \
  --policy.path=outputs/train/soarm_amazing_hand_pick/checkpoints/last/pretrained_model \
  --robot.type=so101_amazing_hand --robot.port=COM58 --robot.hand_port=COM11 \
  --robot.id=amazing_hand_follower \
  --robot.cameras='{ wrist: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30} }' \
  --task="Pick up the cube with the dexterous hand" \
  --duration=60
```

需要录制过程时用 `--strategy.type=episodic` 或 `sentry`，并加 `--dataset.repo_id=<用户名>/rollout_...`（**数据集名必须以 `rollout_` 开头**）。

---

## 文档

| 文档 | 内容 |
|---|---|
| [`tutorials/`](tutorials/README.md) | 六阶段教程，每阶段分 `win.md` / `linux.md` |
| [`SO_ARM101_AMAZINGHAND_GUIDE.md`](SO_ARM101_AMAZINGHAND_GUIDE.md) | 单文件完整流程 + 故障排查表 + FAQ |
| [`AGENT_GUIDE.md`](AGENT_GUIDE.md) | 面向 AI 助手的 LeRobot 使用指引（上游文档） |
| [`AGENTS.md`](AGENTS.md) / [`CLAUDE.md`](CLAUDE.md) | 仓库结构与开发约定（上游文档） |

---

## 常见坑（详见教程故障排查表）

- `lerobot-record` 不再支持 `--policy.path`，也不接受 `eval_` 前缀的数据集名 → 用 `lerobot-rollout`。
- 手标定必须用 `lerobot-calibrate-amazing-hand`，`lerobot-calibrate` 不会弹出手的 GUI。
- 标定文件在 `~/.cache/huggingface/lerobot/calibration/`，换机器需迁移或重标定。
- Windows 上 `uv` 可能默认选中 32 位 Python，导致 `numpy`/`torch` 安装失败。
- Linux 下需串口权限：`sudo chmod 666 /dev/ttyACM*`。

---

## 上游 / 许可

本仓库是 [huggingface/lerobot](https://github.com/huggingface/lerobot) 的分支，遵循 **Apache License 2.0**（见 [LICENSE](LICENSE)）。原项目版权归 The HuggingFace Inc. team 及其贡献者所有。

引用上游：

```bibtex
@misc{cadene2024lerobot,
    author = {Cadene, Remi and Alibert, Simon and Soare, Alexander and Gallouedec, Quentin and Zouitine, Adil and Palma, Steven and Kooijmans, Pepijn and Aractingi, Michel and Shukor, Mustafa and Aubakirova, Dana and Russi, Martino and Capuano, Francesco and Pascal, Caroline and Choghari, Jade and Meftah, Khalil and Ellerbach, Maxime and Moss, Jess and Wolf, Thomas},
    title = {LeRobot: State-of-the-art Machine Learning for Real-World Robotics in Pytorch},
    howpublished = "\url{https://github.com/huggingface/lerobot}",
    year = {2024}
}
```

上游完整文档：<https://huggingface.co/docs/lerobot/index>
