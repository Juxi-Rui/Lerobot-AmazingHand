# 阶段三：遥操作（Windows）

本阶段启动遥操作闭环：主动臂控制从动臂运动、夹爪控制 AmazingHand 开合。这是验证整套系统是否正常工作的关键阶段。

---

## 前置条件

- 已完成 [阶段一：环境搭建](../01-environment/win.md) 和 [阶段二：标定](../02-calibration/win.md)
- 三设备已上电、串口已记录

---

## 运行遥操作

```powershell
lerobot-teleoperate --robot.type=so101_amazing_hand --robot.port=<从动臂COM> --robot.hand_port=<手COM> --robot.id=amazing_hand_follower --teleop.type=so101_leader --teleop.port=<主动臂COM> --teleop.id=amazing_hand_leader
```

> 将 `<从动臂COM>` / `<手COM>` / `<主动臂COM>` 替换为你机器实际的 COM 号（示例 `COM58` / `COM11` / `COM54`）。

**预期效果**：
- 主动臂 5 关节 → 从动臂跟随
- 主动臂夹爪 → AmazingHand 开合（比例跟随：半捏 = 半闭）

> **💡 参数说明**：
> - `--robot.type=so101_amazing_hand`：从动臂 + 手组合机器人
> - `--robot.port`：从动臂串口
> - `--robot.hand_port`：手串口
> - `--teleop.type=so101_leader`：主动臂遥操作器
> - `--teleop.port`：主动臂串口

---

## 首次运行必做：方向验证

启动后，先做**方向测试**，确认以下两点都正确：

| 测试 | 操作 | 正确现象 |
|---|---|---|
| 臂跟随 | 转动主动臂各关节 | 从动臂同向跟随 |
| 手开合 | 张开/捏合主动臂夹爪 | 夹爪张开 → 手张开；夹爪捏合 → 手闭合 |

> **⚠️ 注意（方向反了怎么办）**：
> - **手开合方向反**（张开夹爪手反而闭合）：说明手角度标定不准，重新执行标定工具（含夹爪方向标定），保存后自动生效，**无需手动改文件**。参见 [阶段二：标定](../02-calibration/win.md)。
> - **夹爪映射方向反**（夹爪张开手反而闭合）：同上，标定时在主动臂夹爪**张开**时点 `[Capture Open]`、**捏合**时点 `[Capture Close]`，工具自动记录并保存 `gripper_open_pos`/`gripper_close_pos`，启动时自动加载。
>
> 修改后**重新运行遥操作**验证。

---

## 比例跟随验证

方向正确后，验证比例细腻度：
1. **缓慢**张开夹爪 → 手应**平滑**张开（无跳变）
2. 夹爪停在**中间** → 手也应停在中间
3. 快速张合 → 手快速响应，无卡顿

> **⚠️ 注意（手开合过度的历史问题）**：若手在夹爪开一半时就闭合，多为手角度标定时"张开/握拳"位置不准。重新执行标定步骤 3（手角度 GUI），标定更精确的开合位置。

---

## 可选：带摄像头的可视化

加 `--robot.cameras` 接入相机、`--display_data=true` 打开 Rerun 可视化窗口（实时显示相机图像 + 关节状态）：

```powershell
lerobot-teleoperate `
  --robot.type=so101_amazing_hand `
  --robot.port=<从动臂COM> `
  --robot.hand_port=<手COM> `
  --robot.id=amazing_hand_follower `
  --teleop.type=so101_leader `
  --teleop.port=<主动臂COM> `
  --teleop.id=amazing_hand_leader `
  --robot.cameras='{
    wrist: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30, fourcc: "MJPG"},
    top: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30, fourcc: "MJPG"}
  }' `
  --display_data=true
```

> **💡 说明**：
> - `index_or_path` 为相机索引，先用 `lerobot-find-cameras` 确认（不同机器编号不同）。
> - `fourcc: "MJPG"` 可选，可显著降低 USB 摄像头带宽占用（改用 MJPEG 压缩），卡顿时可加。
> - 相机只需一个时，删掉对应一行（如 `top`）即可。

> **⚠️ 注意（rerun 依赖）**：`--display_data=true` 需要 rerun 可视化包，未安装时执行：
> ```powershell
> pip install "rerun-sdk>=0.24.0,<0.34.0"
> ```
> 需要 Rerun Viewer 可执行文件。Windows 下若报 `Failed to find Rerun Viewer executable`，说明缺 GUI 查看器。**不影响遥操作**，去掉 `--display_data=true` 即可。

---

## 退出

按 `Ctrl+C` 停止。程序自动：
1. 解除 8 个手舵机扭矩
2. 断开从动臂/主动臂串口
3. 断开相机（如有）

> **⚠️ 注意**：正常退出前**不要直接关终端**，否则可能残留串口占用。若异常退出后串口被占用，重插 USB 或重启终端进程。

---

## 故障排查

| 现象 | 原因 | 解决 |
|---|---|---|
| 手方向反 | 手角度或夹爪映射反 | 见上文"方向验证"，交换角度或调整映射 |
| 手开合过度/不足 | 手角度标定不准 | 重标手角度 GUI |
| 臂不跟随 | 标定缺失/串口错 | 确认从动臂已标定、`--robot.port` 正确 |
| rerun 报错 | 可视化依赖缺失 | 去掉 `--display_data=true` |
| 串口被占用 | 上次异常退出 | 关闭占用进程或重插 USB |
