<p align="center">
  <img alt="LeRobot" src="./media/readme/lerobot-logo-thumbnail.png" width="100%">
</p>

# SO-ARM101 + AmazingHand

**English** | [简体中文](README.zh-CN.md)

A fork of [huggingface/lerobot](https://github.com/huggingface/lerobot) **v0.6.2** that adds an
`so101_amazing_hand` robot: an SO-ARM101 follower arm whose gripper is replaced by an
[AmazingHand](https://github.com/pollen-robotics/AmazingHand) dexterous hand, with full
teleoperation, calibration, data collection, and policy deployment support.

- **This fork:** <https://github.com/Juxi-Rui/Lerobot-AmazingHand>
- **Upstream:** <https://github.com/huggingface/lerobot>
- **Base version:** `lerobot` 0.6.2, Apache-2.0
- **In-depth docs:** [`tutorials/`](tutorials/README.md) (six stages × Windows/Linux), plus the
  single-file walkthrough [`SO_ARM101_AMAZINGHAND_GUIDE.md`](SO_ARM101_AMAZINGHAND_GUIDE.md).
  Both are currently written in Chinese.

---

## What this fork adds

| Addition | Location |
| --- | --- |
| `so101_amazing_hand` robot (arm and hand driven as one) | [`src/lerobot/robots/so_amazing_hand/`](src/lerobot/robots/so_amazing_hand/) |
| Dedicated calibration GUI for hand open/close angles (`lerobot-calibrate-amazing-hand`) | [`src/lerobot/scripts/lerobot_calibrate_amazing_hand.py`](src/lerobot/scripts/lerobot_calibrate_amazing_hand.py) |
| Robot registration | [`src/lerobot/robots/utils.py`](src/lerobot/robots/utils.py) |
| `amazinghand` dependency extra | [`pyproject.toml`](pyproject.toml) |
| Six-stage tutorial set (setup / calibration / teleop / collection / training / deployment) | [`tutorials/`](tutorials/README.md) |
| Single-file walkthrough + troubleshooting table + FAQ | [`SO_ARM101_AMAZINGHAND_GUIDE.md`](SO_ARM101_AMAZINGHAND_GUIDE.md) |

Everything else (`policies/`, `datasets/`, `envs/`, `processor/`, `tests/`, `docs/`, …) tracks
upstream and can keep merging from it.

---

## Hardware

| Device | Port (example, machine-dependent) | Servos | Notes |
| --- | --- | --- | --- |
| Leader arm | `COM54` | mixed models, includes gripper #6 | teleoperation input, **keeps the #6 gripper servo** |
| Follower arm | `COM58` | `sts3215-C018` (#1–5) | execution side, **#6 gripper servo removed** |
| AmazingHand | `COM11` | `scs0009` × 8 (IDs 1–8) | end effector, separate serial port |

> **All three devices need their own serial port and their own power supply.** SCS0009 (protocol 1)
> and STS3215 (protocol 0) cannot share a bus, and driving both through lerobot's serial stack in one
> process corrupts them. This fork drives the hand over a separate `rustypot` stack to avoid that —
> which is also why the hand gets its own calibration tool instead of lerobot's `RangeFinderGUI`.

Mechanical conversion: a 3D-printed adapter mounts the AmazingHand onto the follower arm's wrist,
replacing the stock #6 gripper.

---

## Quick start

### 1. Install

```bash
git clone https://github.com/Juxi-Rui/Lerobot-AmazingHand.git
cd Lerobot-AmazingHand

# Create the venv (on Windows, always point at a 64-bit interpreter)
uv venv --python <absolute path to a 64-bit python> .venv

# Install this fork with AmazingHand support
uv pip install -e ".[amazinghand]"
```

The `amazinghand` extra pulls in `feetech-servo-sdk` (arm motors), `rustypot` (hand motors),
`pygame` (calibration GUI), and `pyserial`.

### 2. Find the serial ports

```bash
lerobot-find-port
```

Every device gets a different COM port; substitute the real values in all the commands below.

### 3. Calibrate (order matters: leader → follower + hand → hand angles)

```bash
# 3.1 Leader arm
lerobot-calibrate --teleop.type=so101_leader --teleop.port=COM54 --teleop.id=amazing_hand_leader

# 3.2 Follower arm (with the hand port connected too)
lerobot-calibrate --robot.type=so101_amazing_hand --robot.port=COM58 --robot.hand_port=COM11 --robot.id=amazing_hand_follower

# 3.3 Hand open/close angles (dedicated GUI — drag fully open, Save Open; fully closed, Save Close; auto-saved)
lerobot-calibrate-amazing-hand --hand_port COM11
```

Step 3.3 writes the hand angles to `hand_angles.json`. The robot loads it on every startup,
overriding the config defaults — **no code changes needed**.

### 4. Teleoperate

```bash
lerobot-teleoperate \
  --robot.type=so101_amazing_hand --robot.port=COM58 --robot.hand_port=COM11 \
  --robot.id=amazing_hand_follower \
  --teleop.type=so101_leader --teleop.port=COM54 --teleop.id=amazing_hand_leader
```

The leader arm's five joints drive the follower; the leader gripper drives the hand proportionally.
**Verify the direction on the first run:** gripper open ↔ hand open, gripper closed ↔ hand closed.

### 5. Collect data

```bash
lerobot-record \
  --robot.type=so101_amazing_hand --robot.port=COM58 --robot.hand_port=COM11 \
  --robot.id=amazing_hand_follower \
  --robot.cameras='{ wrist: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30} }' \
  --teleop.type=so101_leader --teleop.port=COM54 --teleop.id=amazing_hand_leader \
  --dataset.repo_id=<your-hf-username>/soarm_amazing_hand_pick \
  --dataset.num_episodes=20 \
  --dataset.single_task="Pick up the cube with the dexterous hand"
```

### 6. Train

```bash
lerobot-train \
  --dataset.repo_id=<your-hf-username>/soarm_amazing_hand_pick \
  --policy.type=act \
  --output_dir=outputs/train/soarm_amazing_hand_pick \
  --job_name=soarm_amazing_hand_pick \
  --policy.device=cuda \
  --wandb.enable=false --policy.push_to_hub=false \
  --steps=60000
```

### 7. Deploy / evaluate

Policy deployment uses **`lerobot-rollout`** — in this version `lerobot-record` no longer accepts
`--policy`:

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

To record while rolling out, use `--strategy.type=episodic` (or `sentry`) and add
`--dataset.repo_id=<username>/rollout_...` (**the dataset name must start with `rollout_`**).

---

## Documentation

| Doc | Contents |
| --- | --- |
| [`tutorials/`](tutorials/README.md) | Six-stage tutorial, `win.md` / `linux.md` per stage (Chinese) |
| [`SO_ARM101_AMAZINGHAND_GUIDE.md`](SO_ARM101_AMAZINGHAND_GUIDE.md) | Single-file walkthrough + troubleshooting table + FAQ (Chinese) |
| [`AGENT_GUIDE.md`](AGENT_GUIDE.md) | LeRobot usage guide for AI agents (upstream doc) |
| [`AGENTS.md`](AGENTS.md) / [`CLAUDE.md`](CLAUDE.md) | Repository structure and dev conventions (upstream docs) |

---

## Common pitfalls

- `lerobot-record` no longer supports `--policy.path`, and rejects dataset names with an `eval_`
  prefix → use `lerobot-rollout`.
- Hand calibration must go through `lerobot-calibrate-amazing-hand`; `lerobot-calibrate` will not
  show a hand GUI.
- Calibration files live in `~/.cache/huggingface/lerobot/calibration/` — migrate them or
  recalibrate when moving to a new machine.
- On Windows, `uv` may pick a 32-bit Python by default, which breaks `numpy`/`torch` installs.
- On Linux, grant serial permissions: `sudo chmod 666 /dev/ttyACM*`.

---

## Upstream / License

This repository is a fork of [huggingface/lerobot](https://github.com/huggingface/lerobot), licensed
under the **Apache License 2.0** (see [LICENSE](LICENSE)). Copyright of the original project belongs
to The HuggingFace Inc. team and its contributors.

Please cite upstream if you use LeRobot in your work:

```bibtex
@misc{cadene2024lerobot,
    author = {Cadene, Remi and Alibert, Simon and Soare, Alexander and Gallouedec, Quentin and Zouitine, Adil and Palma, Steven and Kooijmans, Pepijn and Aractingi, Michel and Shukor, Mustafa and Aubakirova, Dana and Russi, Martino and Capuano, Francesco and Pascal, Caroline and Choghari, Jade and Meftah, Khalil and Ellerbach, Maxime and Moss, Jess and Wolf, Thomas},
    title = {LeRobot: State-of-the-art Machine Learning for Real-World Robotics in Pytorch},
    howpublished = "\url{https://github.com/huggingface/lerobot}",
    year = {2024}
}
```

Full upstream documentation: <https://huggingface.co/docs/lerobot/index>
