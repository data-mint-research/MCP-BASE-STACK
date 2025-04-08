# Host

## Step 1: Enable Developer Mode

**Description:** Allow developer features  
**Objective:** Permit advanced debugging & WSL usage  
**Environment:** PowerShell (Admin)  
**Code:**

```
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock" /t REG_DWORD /f /v "AllowDevelopmentWithoutDevLicense" /d "1"
```

## Step 2: Enable Windows Features

**Description:** Activate WSL2 & virtualization  
**Objective:** Prepare system for Hyper-V, VM-Platform, WSL  
**Environment:** PowerShell (Admin)  
**Code:**

```
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
dism.exe /online /enable-feature /featurename:Microsoft-Hyper-V-All /all /norestart
```

## Step 3: Enable Windows Sudo (Win11+ Build 26052)

**Description:** Allow elevated commands via `sudo`  
**Objective:** Simplify privilege escalation  
**Environment:** PowerShell (Admin)  
**Code:**

```
sudo config --enable
```

## Step 4: Install PowerShell 7

**Description:** Modernize PowerShell environment  
**Objective:** Have the latest cross-platform shell  
**Environment:** PowerShell (Admin)  
**Code:**

```
winget install --id Microsoft.Powershell --source winget --accept-package-agreements --accept-source-agreements
```

---

# WSL2

## Step 1: Install WSL2 (no default distro)

**Description:** Set up the core WSL environment  
**Objective:** Ensure WSL2 is active without auto-installing Ubuntu  
**Environment:** PowerShell  
**Code:**

```
wsl --install --no-distribution
wsl --set-default-version 2
```

## Step 2: Install Ubuntu 22.04 LTS

**Description:** Get the correct Ubuntu version for CUDA  
**Objective:** Ensure 22.04 is used (not generic Ubuntu)  
**Environment:** PowerShell  
**Code:**

```
wsl --install -d Ubuntu-22.04
```

_(Or manually download & install the .appx if unavailable.)_

## Step 3: Create Ubuntu User

**Description:** Set username & password  
**Objective:** Establish Ubuntu account  
**Environment:** Ubuntu (interactive)  
**Code:** _(Follow on-screen prompts)_

## Step 4: Update Ubuntu System

**Description:** Bring packages up to date  
**Objective:** Ensure fresh environment  
**Environment:** Ubuntu  
**Code:**

```
sudo apt update && sudo apt upgrade -y
```

## Step 5: Set Ubuntu-22.04 as Default

**Description:** Make 22.04 auto-start  
**Objective:** Simplify WSL usage  
**Environment:** PowerShell  
**Code:**

```
wsl --set-default Ubuntu-22.04
```

## Step 6: Install Basic Dev Packages

**Description:** Get essential build & Python tools  
**Objective:** Provide minimal dev environment  
**Environment:** Ubuntu  
**Code:**

```
sudo apt update && sudo apt install -y build-essential cmake git \
  python3 python3-pip python3-dev python3-venv python3-setuptools \
  curl wget htop neofetch ninja-build pkg-config \
  libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev \
  libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
```

## Step 7: Optimize WSL2 Configuration

**Description:** Tweak memory, swap, GPU support  
**Objective:** Improve performance for AI tasks  
**Environment:** Windows (editing `%USERPROFILE%\.wslconfig`)  
**Code:** _(Create or edit `.wslconfig` with desired `[wsl2]` settings, then `wsl --shutdown`)_

---

# NVIDIA GPU

## Step 1: Check Current Driver

**Description:** Verify existing GPU driver version  
**Objective:** Identify if update is needed  
**Environment:** PowerShell  
**Code:**

```
Get-WmiObject Win32_VideoController | Select-Object Name, DriverVersion
```

## Step 2: Install NVIDIA Studio Driver

**Description:** Obtain the latest Studio driver  
**Objective:** Ensure WSL2-compatible GPU driver  
**Environment:** GUI Installer  
**Code:** _(Download & run the .exe from NVIDIA website)_

## Step 3: Confirm NVIDIA in WSL

**Description:** Validate GPU visibility  
**Objective:** Confirm `nvidia-smi` works in Ubuntu  
**Environment:** Ubuntu  
**Code:**

```
nvidia-smi
```

## Step 4: Install CUDA Toolkit

**Description:** Add CUDA repository & tools  
**Objective:** Enable GPU compute for AI  
**Environment:** Ubuntu  
**Code:**

```
# Remove old CUDA repos, add new keyring, enable CUDA repo:
sudo rm -f /etc/apt/sources.list.d/cuda-*.list
sudo rm -rf /var/cuda-repo-*
sudo apt-get clean && sudo apt-get update
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb -O cuda-keyring.deb
sudo dpkg -i cuda-keyring.deb && rm cuda-keyring.deb
echo "deb [signed-by=/usr/share/keyrings/cuda-archive-keyring.gpg] https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64 /" | sudo tee /etc/apt/sources.list.d/cuda-wsl-ubuntu.list
sudo apt-get update

# Install CUDA 12.3
sudo apt-get install -y cuda-toolkit-12-3
sudo ln -sfn /usr/local/cuda-12.3 /usr/local/cuda
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

---

# Docker

## Step 1: Remove Old Docker

**Description:** Clean out any legacy Docker packages  
**Objective:** Avoid conflicts  
**Environment:** Ubuntu  
**Code:**

```
sudo apt-get remove docker docker-engine docker.io containerd runc
```

## Step 2: Install Docker (Engine & CLI)

**Description:** Add official Docker repo & install  
**Objective:** Have Docker CE on WSL2  
**Environment:** Ubuntu  
**Code:**

```
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io
sudo docker run hello-world
```

## Step 3: Non-Root Docker Usage

**Description:** Use Docker without sudo  
**Objective:** Add user to `docker` group  
**Environment:** Ubuntu  
**Code:**

```
sudo usermod -aG docker $USER
newgrp docker
docker run hello-world
```

## Step 4: NVIDIA Container Toolkit

**Description:** Let Docker containers access GPU  
**Objective:** GPU acceleration in Docker containers  
**Environment:** Ubuntu  
**Code:**

```
distribution=$(. /etc/os-release && echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/nvidia-docker/gpgkey | sudo gpg --dearmor -o /etc/apt/keyrings/nvidia-docker.gpg
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sed 's#deb https://#deb [signed-by=/etc/apt/keyrings/nvidia-docker.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

## Step 5: Make NVIDIA Runtime Default

**Description:** Set `nvidia` as default in Docker  
**Objective:** Simplify GPU usage  
**Environment:** Ubuntu (editing `/etc/docker/daemon.json`)  
**Code:**

```
cat <<EOF | sudo tee /etc/docker/daemon.json
{
    "default-runtime": "nvidia",
    "runtimes": {
        "nvidia": {
            "path": "nvidia-container-runtime",
            "runtimeArgs": []
        }
    }
}
EOF

sudo systemctl restart docker
```

## Step 6: Verify GPU in Containers

**Description:** Check `nvidia-smi` in Docker  
**Objective:** Ensure GPU is available  
**Environment:** Ubuntu  
**Code:**

```
docker run --rm --gpus all nvidia/cuda:12.3.0-base-ubuntu22.04 nvidia-smi
```

## Step 7: Install Docker Compose

**Description:** Manage multi-container apps  
**Objective:** Add standalone Compose  
**Environment:** Ubuntu  
**Code:**

```
sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.3/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
docker-compose --version
```

---

# Git

## Step 1: Configure Git Globally

**Description:** Set name, email, editor  
**Objective:** Standardize commits & branches  
**Environment:** Ubuntu  
**Code:**

```
git config --global user.name "YOUR NAME"
git config --global user.email "your.email@provider.com"
git config --global init.defaultBranch main
git config --global core.editor nano
git config --list
```

## Step 2: Create & Register SSH Key

**Description:** Generate and add SSH key to Git provider  
**Objective:** Secure passwordless access  
**Environment:** Ubuntu  
**Code:**

```
ssh-keygen -t ed25519 -C "your.email@provider.com"
cat ~/.ssh/id_ed25519.pub
ssh -T git@github.com
```

---

# VS Code

## Step 1: Install VS Code on Windows

**Description:** Basic setup via installer  
**Objective:** Prepare IDE on host  
**Environment:** GUI Installer  
**Code:** _(Download from [https://code.visualstudio.com/download](https://code.visualstudio.com/download) and install.)_

## Step 2: Install Remote WSL Extension

**Description:** Integrate VS Code with WSL2  
**Objective:** Edit Linux files from Windows  
**Environment:** VS Code Extensions  
**Code:** _(Search "Remote - WSL" and install.)_

## Step 3: Install Docker Extension

**Description:** Manage Docker from VS Code  
**Objective:** Streamline container workflows  
**Environment:** VS Code Extensions  
**Code:** _(Search "Docker" and install.)_

## Step 4: Connect VS Code to WSL

**Description:** Open WSL environment in VS Code  
**Objective:** Work seamlessly inside Ubuntu  
**Environment:** VS Code Command Palette  
**Code:** _(“WSL: Connect to WSL”)_

## Step 5: Essential Extensions

**Description:** Python, ESLint, etc.  
**Objective:** Basic dev functionality in WSL  
**Environment:** WSL Terminal within VS Code  
**Code:**

```
code --install-extension ms-python.python
code --install-extension dbaeumer.vscode-eslint
code --install-extension esbenp.prettier-vscode
code --install-extension ms-azuretools.vscode-docker
code --install-extension redhat.vscode-yaml
code --install-extension eamodio.gitlens
code --install-extension yzhang.markdown-all-in-one
code --install-extension mohsen1.prettify-json
```

---

**End of Guide.**