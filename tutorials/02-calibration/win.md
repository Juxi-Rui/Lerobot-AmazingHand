# 阶段二：标定（Windows）

本阶段对三个设备进行标定：主动臂、从动臂、AmazingHand 手。标定是遥操作正确性的前提，**必须完成本阶段才能进入遥操作**。

> **标定顺序**：主动臂 → 从动臂+手 → 手角度。每步都需**终端交互**（物理操作 + 按键）。
>
> **⚠️ 通用提醒**：本页命令中的串口参数为**示例占位**，必须替换为你机器实际的 COM 号（见[阶段一](../01-environment/win.md)记录的串口）。

---

## 前置条件

- 已完成 [阶段一：环境搭建](../01-environment/win.md)
- conda 环境 `lerobot` 已激活
- 三设备串口已记录
- 设备已上电、独立供电

---

## 步骤 1：标定主动臂

```powershell
lerobot-calibrate `
  --teleop.type=so101_leader --teleop.port=<主动臂COM> --teleop.id=amazing_hand_leader
```

> 将 `<主动臂COM>` 替换为你机器的实际 COM 号（示例 `COM54`）。

**交互步骤**：
1. 将主动臂**所有关节移到中间位**，按 Enter
2. 将**每个关节依次推到最大/最小范围**，完成后按 Enter

**验证**：标定文件自动保存到
`C:\Users\<用户名>\.cache\huggingface\lerobot\calibration\teleoperators\so_leader\amazing_hand_leader.json`

> **⚠️ 注意 1（夹爪必标）**：6 号夹爪舵机范围会作为 `gripper.pos`（0~100）的归一化基准。夹爪务必从全开推到全闭，标定到位，否则后续手开合比例会失真。
>
> **⚠️ 注意 2（自由转动）**：标定时机械臂需能自由转动，确保舵机空载。
>
> **⚠️ 注意 3（标定文件位置）**：Windows 下路径为用户目录 `%USERPROFILE%\.cache\huggingface\lerobot\calibration\`。

---

## 步骤 2：标定从动臂（同时连接手）

```powershell
lerobot-calibrate `
  --robot.type=so101_amazing_hand --robot.port=<从动臂COM> --robot.hand_port=<手COM> --robot.id=amazing_hand_follower
```

> 将 `<从动臂COM>` / `<手COM>` 替换为实际 COM 号（示例 `COM58` / `COM11`）。

**交互步骤**：
1. 将从动臂 **5 个关节**（无 6 号）移到中间位，按 Enter
2. 将各关节走全行程，按 Enter

**验证**：标定文件保存到
`C:\Users\<用户名>\.cache\huggingface\lerobot\calibration\robots\so101_amazing_hand\amazing_hand_follower.json`

> **⚠️ 注意 1（手扭矩自动启用）**：此命令连接时**自动启用 8 个手舵机扭矩**（日志显示 `enabling AmazingHand torque`），标定结束手会张开，属正常现象。
>
> **⚠️ 注意 2（不会弹手 GUI）**：手角度**不使用** lerobot 的 `RangeFinderGUI`，从动臂标定结束即完成。手角度用步骤 3 的专用工具。
>
> **⚠️ 注意 3（串口占用）**：此步骤占用手串口。**不要**同时运行其他占用该串口的进程。

---

## 步骤 3：标定手角度 + 夹爪方向（专用 GUI）

```powershell
lerobot-calibrate-amazing-hand --hand_port <手COM> --leader_port <主动臂COM>
```

> 将 `<手COM>` / `<主动臂COM>` 替换为实际 COM 号（示例 `COM11` / `COM54`）。`--leader_port` 用于同步标定**夹爪方向**（见下）。

**GUI 操作**：
1. 拖动 4 根手指滑块（index/middle/ring/thumb），使手**完全张开**，点击 **`Save Open`**
2. 拖动滑块使手**完全握拳**，点击 **`Save Close`**
3. **主动臂夹爪张开**，点击 **`Capture Open`**（GUI 实时显示 `gripper.pos`，张开时应接近 100）
4. **主动臂夹爪捏合**，点击 **`Capture Close`**（捏合时应接近 0）
5. **自动保存**：以上四个值都设置后，窗口顶部弹出绿色横幅 `AUTO-SAVED to ...\hand_angles.json`，终端同步打印路径
6. 关闭窗口（手自动解除扭矩）

**验证**：角度与夹爪映射保存到
`C:\Users\<用户名>\.cache\huggingface\lerobot\calibration\robots\so101_amazing_hand\hand_angles.json`

> **⚠️ 注意 1（必须标定）**：**每台新电脑/每只手都必须执行本步骤**。config 里的角度是 AmazingHand 官方通用默认，仅作后备；`hand_angles.json` 存在时优先加载你的实测值。不标定可能导致开合方向/范围错误。
>
> **⚠️ 注意 2（自动加载）**：机器人每次启动读取 `hand_angles.json`（含 `gripper_open_pos`/`gripper_close_pos`）覆盖 config 默认值，**无需改代码**。夹爪方向会因主动臂而异，标定一次即可。
>
> **⚠️ 注意 3（滑块语义）**：滑块向 `+` 方向使该指 m1 向 `+angle`、m2 向 `-angle`（镜像）。以**手的实际姿态**判断张开/握拳，不必关注角度数值。
>
> **⚠️ 注意 4（精确标定）**：标定"完全张开"时不要过度（手指歪斜/散开），"完全握拳"时不要过度挤压（舵机持续受压）。否则遥操作时开合会过头。
>
> **⚠️ 注意 5（Capture 顺序）**：`Capture Open` / `Capture Close` 对应**主动臂夹爪**的开合，不是手手指。若手张开方向反了，多半是这里标反或手角度标反，重标即可。
>
> **⚠️ 注意 6（GUI 打不开）**：确认已安装 `pygame`（`amazinghand` extra 内含）。若仍打不开，检查是否有图形桌面环境。

---

## 重标定

只需重标某一部分时：
- **只重标手** → 仅运行步骤 3
- **只重标从动臂** → 仅运行步骤 2（会顺带启用手扭矩）
- **全部重标** → 步骤 1 → 2 → 3

> **⚠️ 注意**：步骤 2 和步骤 3 **不能同时运行**（都占用手串口）。

---

完成本阶段后，进入 [阶段三：遥操作](../03-teleoperation/win.md)。

---

## 故障排查

| 现象 | 原因 | 解决 |
|---|---|---|
| 主动臂标定报 2307 型号错误 | 臂总线被污染/串口冲突 | 确认未同时连手串口；本项目手走 rustypot 已规避 |
| 标定手无 GUI 弹出 | 用了错误命令 | 必须用 `lerobot-calibrate-amazing-hand`（不是 `lerobot-calibrate`） |
| 手驱动报 `Operation timed out` | 串口忙碌/时序 | 确认手串口未被占用，重试 |
| 标定文件找不到 | 路径不对 | 检查 `%USERPROFILE%\.cache\huggingface\lerobot\calibration\` |
| 串口打不开 | COM 号错 | 用 `lerobot-find-port` 重新确认 |
