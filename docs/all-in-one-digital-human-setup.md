# All-in-one digital-human kiosk setup

Deploy a digital-human display on x86 hardware such as a mini PC, industrial PC, or desktop. The system opens a full-screen kiosk browser at boot and runs a background wake-word detector for voice interaction.

This example uses an Intel N100 mini PC (Tianhong QN10-100B4). Adapt network and audio-device settings for other x86 machines.

## Environment

| Item | Example |
| --- | --- |
| Hardware | Tianhong QN10-100B4, Intel N100 |
| OS | Ubuntu 24.04 LTS (Noble Numbat) |
| User | xz; replace with your actual username |
| Network | Wi-Fi with a fixed IP; wired networking is also possible |

## Deployment sequence

Initialize package mirrors/networking, install graphics and the browser, configure automatic login/X11, deploy Python wake-word detection and the microphone, then tune boot behavior.

These commands change OS configuration, permissions, login behavior, audio volume, and service state. They are retained setup examples and were not run during translation.

### Initialize the system and network

Back up the package source list and configure the example mirrors/IPv4 preference:

```
sudo cp /etc/apt/sources.list /etc/apt/sources.list.bak

sudo tee /etc/apt/sources.list > /dev/null <<EOF
deb http://mirrors.aliyun.com/ubuntu/ noble main restricted universe multiverse
# deb-src http://mirrors.aliyun.com/ubuntu/ noble main restricted universe multiverse

deb http://mirrors.aliyun.com/ubuntu/ noble-security main restricted universe multiverse
# deb-src http://mirrors.aliyun.com/ubuntu/ noble-security main restricted universe multiverse

deb http://mirrors.aliyun.com/ubuntu/ noble-updates main restricted universe multiverse
# deb-src http://mirrors.aliyun.com/ubuntu/ noble-updates main restricted universe multiverse

deb http://mirrors.aliyun.com/ubuntu/ noble-proposed main restricted universe multiverse
# deb-src http://mirrors.aliyun.com/ubuntu/ noble-proposed main restricted universe multiverse

deb http://mirrors.aliyun.com/ubuntu/ noble-backports main restricted universe multiverse
# deb-src http://mirrors.aliyun.com/ubuntu/ noble-backports main restricted universe multiverse
EOF

echo 'Acquire::ForceIPv4 "true";' | sudo tee /etc/apt/apt.conf.d/99force-ipv4
```

Install NetworkManager if needed:

```
sudo apt update
sudo apt install network-manager -y
sudo systemctl start NetworkManager
sudo systemctl enable NetworkManager
```

Set Wi-Fi credentials and a fixed IP. Replace the example SSID, password, IP, gateway, and DNS settings with your own:

```
sudo nmcli device wifi connect "MERCURY_1812" password "12345678"

sudo nmcli connection modify "MERCURY_1812" ipv4.addresses "192.168.0.86/24" ipv4.gateway "192.168.0.1" ipv4.dns "8.8.8.8,114.114.114.114" ipv4.method "manual"

sudo nmcli connection up "MERCURY_1812"
```

### Step 1: Install graphics and browser components

Use X11 and Openbox instead of a full GNOME/KDE desktop. Install audio utilities, a pointer-hiding tool, and the browser. The original prose calls it Chromium, but the commands install Google Chrome:

```
sudo timedatectl set-timezone Asia/Shanghai


sudo apt install net-tools vim fonts-wqy-microhei fonts-wqy-zenhei alsa-utils pulseaudio -y
sudo apt install --no-install-recommends xserver-xorg x11-xserver-utils xinit openbox unclutter -y

wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb -y
rm google-chrome-stable_current_amd64.deb

sudo apt purge snapd -y

```

### Step 2: Enable automatic login on TTY1

Configure systemd to log in as `xz` without entering a password at boot. This is an unattended-kiosk tradeoff, not a security guarantee.

Create the override directory:

```
sudo mkdir -p /etc/systemd/system/getty@tty1.service.d/
```

Write the auto-login rule:

```
echo -e "[Service]\nExecStart=\nExecStart=-/sbin/agetty --autologin xz --noclear %I \$TERM" | sudo tee /etc/systemd/system/getty@tty1.service.d/override.conf
```

Reload systemd and set the boot target:

```
sudo systemctl daemon-reload
sudo systemctl set-default multi-user.target
```

### Step 3: Start X11 after login

Append the following to your user profile so TTY1 login starts X11:

```
cat << 'EOF' >> ~/.bash_profile
if [ -z "$DISPLAY" ] && [ "$(fgconsole)" -eq 1 ]; then
    exec startx
fi
EOF
```

Tell `startx` to launch Openbox:

```
echo "exec openbox-session" > ~/.xinitrc
```

### Step 4: Configure Openbox and the kiosk browser

Disable screen blanking, hide the pointer, and relaunch the browser after an exit/crash.

Create the Openbox directory:

```
mkdir -p ~/.config/openbox
```

Write its `autostart` file:

```
cat << 'EOF' > ~/.config/openbox/autostart
# Disable screen blanking and power management
xset -dpms
xset s noblank
xset s off

# Hide the pointer
unclutter -idle 0.1 -root &

# Restart the browser in a loop after exit or crash
while true; do
    google-chrome \
        --kiosk \
        --no-first-run \
        --no-default-browser-check \
        --disable-infobars \
        --disable-session-crashed-bubble \
        --disable-translate \
        --disable-external-intent-requests \
        --autoplay-policy=no-user-gesture-required \
        --use-fake-ui-for-media-stream \
        "https://www.douyin.com"
    sleep 2
done &
EOF
```

The original initial URL remains `https://www.douyin.com`; the later wake-word setup below replaces it with the local test page.

Disable the Openbox `Alt+F4` shortcut:

```
cp /etc/xdg/openbox/rc.xml ~/.config/openbox/
sed -i '/<keybind key="A-F4">/,/<\/keybind>/d' ~/.config/openbox/rc.xml
```

### Step 5: Reboot and verify

If you do not need to wait for all network interfaces (for example, with an unplugged Ethernet cable), disable the wait-online services to avoid boot delays:

```
sudo systemctl mask systemd-networkd-wait-online.service
sudo systemctl mask NetworkManager-wait-online.service
```

Hide GRUB/boot status messages:

```
sudo sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT="quiet loglevel=3 systemd.show_status=false vt.global_cursor_default=0"/g' /etc/default/grub

echo 'GRUB_TIMEOUT_STYLE="hidden"' | sudo tee -a /etc/default/grub
echo 'GRUB_RECORDFAIL_TIMEOUT=0' | sudo tee -a /etc/default/grub

sudo update-grub
```

Set master audio to 100%, unmute, and reboot:

```
amixer -q sset Master 100% unmute
sudo reboot
```

### Deploy the wake-word service

Install Python, upload the module, configure the camera microphone, and enable startup.

#### 1. Install Miniconda

```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
~/miniconda3/bin/conda init bash
source ~/.bashrc
rm Miniconda3-latest-Linux-x86_64.sh
```

Ensure login loads `.bashrc` and its Conda initialization:

```bash
if ! grep -q '.bashrc' ~/.bash_profile; then
    cat << 'EOF' >> ~/.bash_profile

if [ -f ~/.bashrc ]; then
    . ~/.bashrc
fi
EOF
fi
```

#### 2. Create the Python environment

```bash
conda create -n test python=3.10 -y
conda activate test
```

If Conda reports that Terms of Service have not been accepted, review those terms before accepting them with the original commands:

```bash
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
```

#### 3. Upload project files

From the development machine, copy the entire `main/digital-human/` directory to `~/digital-human/` on the kiosk. Replace `<一体机IP>`, the original “kiosk IP” placeholder, with the actual IP:

```bash
# Run on the development machine; replace the kiosk IP placeholder
scp -r main/digital-human/ xz@<一体机IP>:~/digital-human/
```

#### 4. Install system dependencies

The wake-word service requires audio capture libraries and ALSA's PulseAudio plugin:

```bash
sudo apt install libportaudio2 portaudio19-dev libasound2-plugins -y
```

#### 5. Install Python dependencies

```bash
cd ~/digital-human/wakeword_runtime
pip install numpy
pip install -r requirements.txt
```

#### 6. Download wake-word models

Model files are not included. Follow the model-download section in the [wake-word guide](digital-human-wakeword.md).

#### 7. Update Openbox autostart

Add PulseAudio and microphone settings, then point Chrome at the local test page.

Find the camera microphone's PulseAudio source name:

```bash
pulseaudio --start
pactl list sources short
```

Locate the line containing `USB_Camera` and copy its full name, such as:

```
alsa_input.usb-SN0002_2K_USB_Camera_46435000_P030D00_SN0002-02.mono-fallback
```

Replace the entire `autostart` file below. Set `TARGET_MIC` to your actual device name:

```bash
cat << 'EOF' > ~/.config/openbox/autostart
# 1. Start the audio service and wait briefly
pulseaudio --start
sleep 1

# 2. Select the camera microphone (replace with your device name)
TARGET_MIC="alsa_input.usb-SN0002_2K_USB_Camera_46435000_P030D00_SN0002-02.mono-fallback"

# 3. Set the system default microphone
pactl set-default-source "$TARGET_MIC"

# 4. Unmute
pactl set-source-mute "$TARGET_MIC" 0

# 5. Set volume to 100%
pactl set-source-volume "$TARGET_MIC" 100%

# --- Minimal desktop and browser configuration ---

# Disable screen blanking and power management
xset -dpms
xset s noblank
xset s off

# Hide the pointer
unclutter -idle 0.1 -root &

# Restart the browser in a loop after exit or crash
while true; do
    google-chrome \
        --kiosk \
        --no-first-run \
        --no-default-browser-check \
        --disable-infobars \
        --disable-session-crashed-bubble \
        --disable-translate \
        --disable-external-intent-requests \
        --autoplay-policy=no-user-gesture-required \
        --use-fake-ui-for-media-stream \
        "http://127.0.0.1:8006/index.html"
    sleep 2
done &
EOF
```

#### 8. Start the runtime at boot

Check your user's UID:

```bash
id -u $(whoami)
```

Replace `1000` below with that UID (the first user's UID is often 1000), then create the systemd service:

```bash
sudo tee /etc/systemd/system/digital-human.service << 'EOF'
[Unit]
Description=Digital Human Runtime
After=network.target sound.target

[Service]
Type=simple
User=xz
Environment=XDG_RUNTIME_DIR=/run/user/1000
Environment=PULSE_SERVER=unix:/run/user/1000/pulse/native
WorkingDirectory=/home/xz/digital-human
ExecStartPre=/bin/sleep 10
ExecStart=/home/xz/miniconda3/envs/test/bin/python start.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

Replace `User=xz`, both `/run/user/1000` values, `WorkingDirectory`, and the `ExecStart` path to match your account and installation. Keep the PulseAudio environment variables: they let the runtime and browser share the camera microphone.

Enable and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable digital-human
sudo systemctl start digital-human
```

#### 9. Service management commands

```bash
sudo systemctl start digital-human     # Start now
sudo systemctl stop digital-human      # Stop
sudo systemctl restart digital-human   # Restart
sudo systemctl status digital-human    # Show status
journalctl -u digital-human -f         # Follow logs
```

