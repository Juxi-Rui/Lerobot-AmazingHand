# 阶段一：环境搭建（Linux）

使用 **Miniforge** 创建独立 Python 环境，安装 LeRobot 及 AmazingHand 支持。本页按**严格顺序**执行，每个代码块可整体复制。

> 环境版本：Python 3.12 · PyTorch ≥ 2.10 · LeRobot 0.6.2（本仓库定制版）· 推荐 Ubuntu 20.04/22.04

---

## 步骤 1：安装 Miniforge

```bash
wget "https://mirrors.tuna.tsinghua.edu.cn/github-release/conda-forge/miniforge/LatestRelease/Miniforge3-$(uname)-$(uname -m).sh"
```

```bash
bash Miniforge3-$(uname)-$(uname -m).sh -b
~/miniforge3/bin/conda init
source ~/.bashrc
```

```bash
conda --version
```

> 官方地址（海外网络）：`https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh`

---

## 步骤 2：配置 conda 国内源（中国大陆网络）

```bash
conda config --remove-key channels
```

```bash
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/
```

> `pkgs/free` 已下线（404），不要添加。网络不限可跳过本步骤。

---

## 步骤 3：安装编译工具（新系统必需）

新装的 Ubuntu 可能缺 `gcc` 等编译工具，安装 `evdev` 等包时需要：

```bash
sudo apt update
sudo apt install -y build-essential
```

---

## 步骤 4：创建虚拟环境

```bash
conda create -y -n lerobot python=3.12
conda activate lerobot
```

```bash
python --version
python -c "import struct; print(struct.calcsize('P')*8, 'bit')"
```

> 预期 `Python 3.12.x` + `64 bit`。

---

## 步骤 5：安装 ffmpeg（视频解码必需）

LeRobot 录制/回放视频数据依赖 ffmpeg：

```bash
conda install ffmpeg -c conda-forge -y
```

---

## 步骤 6：安装项目依赖

```bash
cd ~/Lerobot-AmazingHand   # 换成你克隆本仓库的目录
pip install -e ".[amazinghand]"
```

`amazinghand` 包含：`feetech-servo-sdk`（臂电机）、`rustypot`（手电机）、`pygame`（标定 GUI）、`pyserial`（串口）。

> pip 慢时先配置国内源：
> ```bash
> pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
> ```

---

## 步骤 7：配置串口权限

```bash
sudo chmod 666 /dev/ttyACM*
```

> 永久方案（udev 规则，针对 CP210x 芯片，VID `10c4`）：
> ```bash
> sudo tee /etc/udev/rules.d/99-servo.rules << 'EOF'
> SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", MODE="0666", GROUP="dialout"
> EOF
> sudo udevadm control --reload-rules && sudo udevadm trigger
> ```

---

## 步骤 8：验证环境

```bash
python -c "import scservo_sdk, rustypot, pygame, serial, lerobot; print('all OK')"
lerobot-calibrate-amazing-hand --help
```

> 应显示 `all OK` 和 `usage: lerobot-calibrate-amazing-hand ...`。

---

## 步骤 9：确认串口

```bash
ls -l /dev/ttyACM* /dev/ttyUSB* 2>/dev/null
```

或 `lerobot-find-port`。确认三设备路径（示例 `/dev/ttyACM0`/`/dev/ttyACM1`/`/dev/ttyACM2`，**需替换为你的实际值**）。

---

完成 → [阶段二：标定](../02-calibration/linux.md)

---

## 故障排查

| 现象 | 解决 |
|---|---|
| `conda` 命令找不到 | `source ~/.bashrc` 或 `conda init` 后重开终端 |
| `pkgs/free` 404 | 该通道已下线，不要添加 |
| 串口 `Permission denied` | 步骤 7 `sudo chmod 666` |
| 依赖装不上/慢 | 配置 pip 国内源（步骤 6 提示） |
| 安装报 `evdev` 编译错 | 步骤 3 `sudo apt install build-essential` |
| GPU 训练 CUDA 检查 `False` | 见阶段五训练文档 |
