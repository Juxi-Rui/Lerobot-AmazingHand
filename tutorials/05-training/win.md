# 阶段五：模型训练（Windows）

本阶段使用采集的数据集训练策略（ACT 等），产出可部署的模型。训练是最耗时的一步，**建议使用 NVIDIA GPU**。

---

## 前置条件

- 已完成 [阶段四：数据采集](../04-data-collection/win.md)
- NVIDIA GPU（推荐）、CUDA 驱动
- 数据集已录制（本地缓存可见）

---

## 步骤 1：确认 GPU 环境

```powershell
python -c "import torch; print('CUDA:', torch.cuda.is_available(), '| GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
```

**期望输出**：`CUDA: True | GPU: <你的显卡名>`

> **⚠️ 注意（CUDA torch）**：若 `CUDA: False`，说明装的是 CPU 版 torch。需重装 CUDA 版：
> ```powershell
> # 官方源（海外网络）
> pip install torch --index-url https://download.pytorch.org/whl/cu128
>
> # 中国大陆网络优先用阿里云镜像
> pip install torch --index-url https://mirrors.aliyun.com/pytorch-wheels/cu128
> ```
> 或用 CPU 训练（`--policy.device=cpu`，但速度慢很多，复杂任务不现实）。

---

## 步骤 2：训练

```powershell
lerobot-train `
  --dataset.repo_id=soarm_amazing_hand_pick `
  --dataset.root=D:\lerobot_data `
  --policy.type=act `
  --output_dir=outputs/train/soarm_amazing_hand_pick `
  --job_name=soarm_amazing_hand_pick `
  --policy.device=cuda `
  --wandb.enable=false `
  --policy.push_to_hub=false `
  --steps=60000
```

> **💡 说明**：`--dataset.repo_id` 和 `--dataset.root` 必须与[阶段四录制](../04-data-collection/win.md)时**完全一致**（`repo_id=soarm_amazing_hand_pick`、`root=D:\lerobot_data`），即可读取本地数据集，无需 HF 登录。

---

## 参数说明

| 参数 | 说明 |
|---|---|
| `--dataset.repo_id` | 数据集名称（与录制时一致） |
| `--dataset.root` | 数据集本地路径（与录制时一致） |
| `--policy.type` | 策略类型，`act` 为常用选择 |
| `--output_dir` | 训练输出目录（checkpoints、日志） |
| `--job_name` | 任务名（用于日志区分） |
| `--policy.device` | `cuda`（GPU）或 `cpu` |
| `--wandb.enable` | 权重日志，`false` 关闭（无需 wandb 账号） |
| `--policy.push_to_hub` | 是否推送模型到 HF，`false` 仅本地 |
| `--steps` | 训练步数 |

---

## 训练过程说明

- **checkpoints**：每步自动保存到 `outputs/train/soarm_amazing_hand_pick/checkpoints/`
- **日志**：终端实时显示 loss 等指标
- **时长**：60000 步在消费级 GPU 上通常数小时（具体取决显卡）

> **⚠️ 注意 1（步数调整）**：`--steps=60000` 为 ACT 典型值。任务简单可减至 30000，复杂任务可加至 100000+。观察 loss 收敛情况。
>
> **⚠️ 注意 2（训练中断续跑）**：中断后重新运行**同参数命令**会从最后 checkpoint 继续。
>
> **⚠️ 注意 3（wandb）**：如需可视化 loss 曲线，可开 `--wandb.enable=true`（需 `wandb login`）。默认关闭。
>
> **⚠️ 注意 4（内存/显存）**：显存不足可加 `--policy.batch_size=8`（降低批大小）；视频解码内存不足可减小 `width/height`。

---

完成本阶段后，进入 [阶段六：部署与评估](../06-deployment/win.md)。

---

## 故障排查

| 现象 | 原因 | 解决 |
|---|---|---|
| `CUDA: False` | CPU 版 torch | 重装 CUDA 版 torch |
| 显存不足（OOM） | 批大小过大 | `--policy.batch_size=8` 或更低 |
| 数据集找不到 | repo_id/root 不一致 | 确认与录制时 `--dataset.repo_id` 和 `--dataset.root` 完全一致 |
| 训练慢 | CPU 训练 | 用 GPU；或减小 `--steps` |
| `wandb` 报错 | 未登录 | `--wandb.enable=false` 或 `wandb login` |
