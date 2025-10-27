# Anubeam

### Redragon Anubis keyboard input sources backlight indicator for Fedora
Tested with Fedora 42 (GNOME 48), Python 3.13.9


## Idea
A GNOME extension detects input source changes and exposes them over D-Bus so a Python script can adjust the keyboard backlight

***
## How It Works
The Anubeam system connects the GNOME input source events with direct hardware control of your Redragon Anubis keyboard backlight

### 1. GNOME Extension (`input-source-monitor@eshfield`)
- Listens for input source changes in GNOME Shell
- Emits a D-Bus signal `SourceChanged` with the current layout ID (e.g. `us`, `ru`)

### 2. D-Bus Interface (`org.gnome.InputSourceMonitor`)
- Provides a communication channel between the GNOME Shell and user-space applications
- The Python script subscribes to these signals to react instantly when the layout changes

### 3. udev Rule (`99-keyboard.rules`)
- Grants non-root access to the keyboard’s HID interface
- Ensures the Python script can send commands to the device without elevated privileges

### 4. Python Script
- Runs continuously as a `systemd --user` service
- Connects to D-Bus and listens for `SourceChanged` signals
- Maps each layout ID to a color (e.g. white for English, red for Russian)
- Sends HID commands directly to the keyboard to change the backlight color

Together, these components form a fully automated system: **Change your keyboard layout** → **GNOME extension detects it** → **D-Bus broadcasts it** → **Python service updates the keyboard light**

***
## Installation

### Step I: Install Input Source Monitor GNOME extension

This extension listens for changes in the current keyboard input source and broadcasts these events through
a custom D-Bus interface

1. Copy the directory `input-source-monitor@eshfield` to:

```
~/.local/share/gnome-shell/extensions/
```

2. Restart GNOME Shell (log out and back in, or press Alt + F2, type `r`, and hit `Enter`)


3. Enable the extension:

```
gnome-extensions enable input-source-monitor@eshfield
```

### Step II: Set up udev Rules

To allow your script to control the keyboard device without root privileges, configure the proper udev permissions

1. Create a new udev rules file:

```
sudo nano /etc/udev/rules.d/99-keyboard.rules
```

2. Add the following rule:

```
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="258a", ATTRS{idProduct}=="0049", MODE="0666"
```

3. Reload udev and apply the new rule:

```
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### Step III: Install Python Dependencies
Install required packages (create new virtual environment or use system):
```
pip install -r requirements.txt
```

### Step IV: Add the Python Script to System Startup

To make sure the keyboard light controller starts automatically with your desktop session, create a user-level `systemd`
service

1. Create a log file for runtime output:

```
sudo touch /var/log/anubeam.log
sudo chown eshfield:eshfield /var/log/anubeam.log
```

2. Create the service file:

```
mkdir -p ~/.config/systemd/user
nano ~/.config/systemd/user/anubeam.service
```

3. Add the following content (adjust paths to match your environment):

```
[Unit]
Description=Anubeam keyboard light controller
After=graphical-session.target
Wants=graphical-session.target

[Service]
ExecStart=<PATH_TO_PYTHON_BIN> <PATH_TO_MAIN_PY_FILE>
WorkingDirectory=<PATH_TO_PROJECT_DIRECTORY>
Restart=always
Environment=PYTHONUNBUFFERED=1
StandardOutput=append:/var/log/anubeam.log

[Install]
WantedBy=default.target
```

4. Reload the daemon and enable the service:

```
systemctl --user daemon-reload
systemctl --user enable anubeam.service
systemctl --user start anubeam.service
```

Done! The Anubeam Python script will now start automatically when you log in and listen for keyboard layout changes over
D-Bus to adjust the backlight color

***
## Bytes Packets Structure Overview
To change the keyboard backlight, you need to send two packets, each 1032 bytes long (padded with zeroes after the following structure)

### Packet 1
```
06 08 b8 00 40 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 __ __ __ 00 00 ff 00 ff 00 ff ff 00 ff 00 ff 00 ff ff ff ff ff ff 00 00 00 00 ff 00 ff 00 ff ff 00 ff 00 ff 00 ff ff ff ff ff ff 00 00 00 00 ff 00 ff 00 ff ff 00 ff 00 ff 00 ff ff ff ff ff ff 00 00 00 00 ff 00 ff 00 ff ff 00 ff 00 ff 00 ff ff ff ff ff ff 00 00 00 00 ff 00 ff 00 ff ff 00 ff 00 ff 00 ff ff ff ff ff ff 00 00 00 00 ff 00 ff 00 ff ff 00 ff 00 ff 00 ff ff ff ff ff ff 00 00 00 00 ff 00 ff 00 ff ff 00 ff 00 ff 00 ff ff ff ff ff ff 00 00 00 00 ff 00 ff 00 ff ff 00 ff 00 ff 00 ff ff ff ff ff ff 00 00 00 00 ff 00 ff 00 ff ff 00 ff 00 ff 00 ff ff ff ff ff ff 00 00 00 00 ff 00 ff 00 ff ff 00 ff 00 ff 00 ff ff ff ff ff ff 00 00 00 00 ff 00 ff 00 ff ff 00 ff 00 ff 00 ff ff ff ff ff ff 00 00 00 00 ff 00 ff 00 ff ff 00 ff 00 ff 00 ff ff ff ff ff ff 00 00 00 00 ff 00 ff 00 ff ff 00 ff 00 ff 00 ff ff ff ff ff ff 00 00 00 00 ff 00 ff 00 ff ff 00 ff 00 ff 00 ff ff ff ff ff ff 00 00 00 00 ff 00 ff 00 ff ff 00 ff 00 ff 00 ff ff ff ff ff ff 00 00 00 00 ff 00 ff 00 ff ff 00 ff 00 ff 00 ff ff ff ff ff ff 00 00 00 00 ff 00 ff 00 ff ff 00 ff 00 ff 00 ff ff ff ff ff ff 00 00 00 00 ff 00 ff 00 ff ff 00 ff 00 ff 00 ff ff ff ff ff ff 00 00 00 00 ff 00 ff 00 ff ff 00 ff 00 ff 00 ff ff ff ff ff ff ff ff 00 00 ff 00 ff 00 ff ff 00 ff 00 ff 00 ff ff ff ff ff ff 00 00 00 00 ff 00 ff 00 ff ff 00 ff 00 ff 00 ff ff ff ff ff ff 00 00 00 00 ff 00 ff 00 ff ff 00 ff 00 ff 00 ff ff ff ff ff
```

`__ __ __` — light color values, e.g. `ff 00 00` for red

### Packet 2
```
06 03 b6 00 00 00 00 00 00 00 00 00 00 00 5a a5 03 03 00 00 00 01 20 01 00 00 00 00 55 55 01 00 00 00 00 00 ff ff 00 __ 07 33 07 33 07 33 07 33 07 33 07 33 07 33 07 33 07 33 07 33 07 33 07 33 07 33 07 33 07 33 07 33 07 33 07 33 07 33 5a a5 00 10 07 44 07 44 07 44 07 44 07 44 07 44 07 44 04 04 04 04 04 04 04 04 04 04 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 5a a5 03 03
```

`__` — light intensity values:

- `30` → off
- `31` → level 1
- `32` → level 2
- `33` → level 3
- `34` → level 4
