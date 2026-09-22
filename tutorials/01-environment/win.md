# 阶段一：环境搭建（Windows）

使用 **Miniconda** 创建独立 Python 环境，安装 LeRobot 及 AmazingHand 支持。本页按**严格顺序**执行，每个代码块可整体复制。

> 环境版本：Python 3.12 · PyTorch ≥ 2.10 · LeRobot 0.6.2（本仓库定制版）

---

## 步骤 1：安装 Miniconda

**命令行安装**（PowerShell，推荐）——中国大陆网络用清华镜像：

```powershell
curl.exe -L -o Miniconda3-latest-Windows-x86_64.exe https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-Windows-x86_64.exe
```

```powershell
$installDir = "C:\Users\$env:USERNAME\miniconda3"
Start-Process -Wait .\Miniconda3-latest-Windows-x86_64.exe -ArgumentList "/S", "/D=$installDir"
```

```powershell
C:\Users\$env:USERNAME\miniconda3\Scripts\conda.exe init powershell
```

重开 PowerShell 后验证：

```powershell
conda --version
```

> **图形化安装**（可选）：从官网 https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe 下载安装包，双击安装，勾选 **"Add to PATH"**。
>
> 若 `conda` 命令找不到，用 **Anaconda Prompt**（开始菜单）代替 PowerShell。

---

## 步骤 2：配置 conda 国内源（中国大陆网络）

**先清空默认源，再添加清华镜像**（新 Miniconda 会默认带 `repo.anaconda.com` 官方源，触发 ToS 检查且慢）：

```powershell
conda config --remove-key channels
```

```powershell
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/
```

> `pkgs/free` 已下线（404），不要添加。网络不限可跳过本步骤。

---

## 步骤 3：创建虚拟环境

```powershell
conda create -y -n lerobot python=3.12
conda activate lerobot
```

```powershell
python --version
python -c "import struct; print(struct.calcsize('P')*8, 'bit')"
```

> 预期 `Python 3.12.x` + `64 bit`。若 `conda activate` 无 `(lerobot)` 前缀，见文末故障排查。

---

## 步骤 4：安装 ffmpeg（视频解码必需）

LeRobot 录制/回放视频数据依赖 ffmpeg：

```powershell
conda install ffmpeg -c conda-forge -y
```

> 国内网络若慢，可用已配置的清华 conda-forge 通道。不装会导致录数据/播放视频报错。

---

## 步骤 5：安装项目依赖

```powershell
cd D:\Project\Lerobot-AmazingHand   # 换成你克隆本仓库的目录
pip install -e ".[amazinghand]"
```

`amazinghand` 包含：`feetech-servo-sdk`（臂电机）、`rustypot`（手电机）、`pygame`（标定 GUI）、`pyserial`（串口）。

> pip 慢时先配置国内源：
> ```powershell
> pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
> ```

---

## 步骤 6：验证环境

```powershell
python -c "import scservo_sdk, rustypot, pygame, serial, lerobot; print('all OK')"
lerobot-calibrate-amazing-hand --help
```

> 应显示 `all OK` 和 `usage: lerobot-calibrate-amazing-hand ...`。

---

## 步骤 7：确认串口

```powershell
lerobot-find-port
```

在设备管理器 → 端口(COM 和 LPT) 确认三设备 COM 号（示例 `COM54`/`COM58`/`COM11`，**需替换为你的实际值**）。COM 号插拔后会变，重跑确认。

---

完成 → [阶段二：标定](../02-calibration/win.md)

---

## 故障排查

| 现象 | 解决 |
|---|---|
| `conda` 不是命令 | 重开终端 / Anaconda Prompt / `conda init powershell` |
| ToS 错误（repo.anaconda.com） | 步骤 2 清空 channels 只留清华源；或 `conda tos accept ...` |
| `pkgs/free` 404 | 该通道已下线，不要添加 |
| `conda activate` 无前缀 | 执行策略问题，见下 |
| 依赖装不上/慢 | 配置 pip 国内源（步骤 5 提示） |

**conda activate 无 `(lerobot)` 前缀**（Windows 常见）：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
& "D:\Software\Miniconda3\shell\condabin\conda-hook.ps1"
conda activate lerobot
```

> `D:\Software\Miniconda3` 替换为你的 Miniconda 安装路径。
