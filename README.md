<p align="center">
  <img src="https://img.shields.io/badge/HueMedia-Media%20Player-purple" alt="HueMedia">
  <img src="https://img.shields.io/badge/MPV-Engine-green" alt="MPV">
  <img src="https://img.shields.io/badge/SDL2-UI-blue" alt="SDL2">
  <img src="https://img.shields.io/badge/Raspberry%20Pi-3B-red" alt="RPi3B">
  <img src="https://img.shields.io/badge/Licence-MIT-orange" alt="Licence">
</p>

# HueMedia

A lightweight, touch-optimized media player for **Raspberry Pi 3B**. SDL2-based UI, MPV playback engine, Bluetooth A2DP/AVRCP headphones, Spotify/YouTube streaming, auto-detecting USB storage pooling, dual-drive isolation ([SYSTEM] vs [MUSIC]), SAMBA sharing, and a full React web management interface.

---

## Features

| Feature | Details |
|---|---|
| **Touch UI** | SDL2 on framebuffer — 44px+ touch targets, swipeable, zero X11 overhead |
| **Playback** | MPV engine with hardware video decode — MP3, FLAC, WAV, AAC, MP4, MKV |
| **Video** | Full video playback on the 3.5" LCD |
| **Bluetooth** | Pair headphones, AVRCP buttons (play/pause/skip/back), on-screen management |
| **Spotify / YouTube** | Stream via yt-dlp + MPV; Spotify via librespot |
| **Cover Art** | Reads `cover.png` per song folder, displays on both LCD and web UI |
| **Music Library** | Auto-scans `Music/Artist/Song/song.mp3 + cover.png` — alphabetical sort, shuffle, repeat |
| **Web Interface** | React SPA at `10.0.0.174:5000` — browse, play, upload, SSH terminal, plugin manager |
| **Dual Drive** | SD card = [SYSTEM] (read-only for music); USB drives = [MUSIC], auto-pooled via mergerfs |
| **SAMBA** | `\\10.0.0.174\MUSIC` — drag-and-drop music onto pooled drives |
| **Power Efficiency** | Runs on framebuffer, no X11/Wayland, CPU governor powersave, USB autosuspend |

---

## Hardware Requirements

- **Raspberry Pi 3B** or 3B+
- MicroSD card (16GB+ recommended, 32GB+ for larger libraries)
- USB drive(s) for music storage (FAT32, exFAT, NTFS, or ext4)
- Optional: Bluetooth headphones/speakers
- Optional: USB WiFi dongle if using WiFi

---

## Installation

### One-Line Install (recommended)

Flash **Raspberry Pi OS Lite (Bookworm, 64-bit)** to your SD card. Boot the Pi, then:

```bash
curl -sSL https://raw.githubusercontent.com/vector-just-technology/HueMedia/main/install.sh | sudo bash
```

### Step-by-Step Manual Install

If you prefer to understand each step or the one-liner fails:

#### 1. Prepare Raspberry Pi OS

Flash Raspberry Pi OS Lite (Bookworm 64-bit) to your SD card. Before booting, mount the `boot` partition and create an empty `ssh` file to enable SSH:

```bash
touch /media/$USER/boot/ssh
```

Optionally, configure WiFi by creating `/media/$USER/boot/wpa_supplicant.conf`:
```
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
network={
    ssid="YourWiFiSSID"
    psk="YourWiFiPassword"
    key_mgmt=WPA-PSK
}
```

#### 2. Boot and Connect

Insert SD card and boot the Pi. Find its IP from your router, then SSH in:

```bash
ssh pi@<pi-ip-address>
# default password: raspberry
```

#### 3. Download and Run Installer

```bash
sudo apt update && sudo apt install -y git
git clone https://github.com/vector-just-technology/HueMedia.git /opt/hue-media
cd /opt/hue-media
sudo bash install.sh
```

#### 4. What Happens During Installation

```
  ├── Creates 'hue' system user
  ├── Sets static IP 10.0.0.174
  ├── Installs system deps (MPV, SDL2, BlueZ, SAMBA, mergerfs, etc.)
  ├── Creates Python venv, installs pysdl2, python-mpv, Flask
  ├── Configures Bluetooth (A2DP + AVRCP)
  ├── Configures SAMBA shares
  ├── Sets up udev rules for auto-mounting USB drives
  ├── Enables systemd services (player, API, Bluetooth)
  └── REBOOTS into HueMedia
```

---

## Post-Installation

After installation completes, you'll see:

| Service | Address | Description |
|---|---|---|
| **Web UI** | `http://10.0.0.174:5000` | Music library, playback, bluetooth, settings, SSH terminal |
| **SAMBA** | `\\10.0.0.174\MUSIC` | Drag-and-drop music onto pooled USB drives |
| **SSH** | `ssh hue@10.0.0.174` | System access |
| **Display** | Built-in | Now Playing, Library, Bluetooth, Settings |

### Adding Music

Organize your music on any USB drive with this folder structure:

```
/MUSIC/
  Artist Name/
    Song Name/
      Song_MP3.mp3
      cover.png
    Song Name 2/
      Song_MP3.mp3
      cover.png
```

USB drives are auto-detected and pooled at `/pool/Music`. You can also upload via the web UI or SAMBA.

### Controls on the Display

| Action | How |
|---|---|
| Play/Pause | Tap center button |
| Next/Prev | Tap arrows |
| Volume | Slide the volume bar (top-right) |
| Shuffle | Tap shuffle button |
| Repeat | Tap repeat button |

### Web Interface

The web UI at `10.0.0.174:5000` mirrors the LCD and adds:

- Full music library browsing and search
- Upload songs and cover art
- Bluetooth device pairing
- SSH web terminal
- System settings and resource monitor
- Service logs viewer

---

## Project Structure

```
HueMedia/
├── install.sh                 # One-shot installer
├── setup/                     # Modular install scripts
│   ├── 00-utils.sh
│   ├── 02-finalize.sh
│   ├── 03-storage.sh
│   ├── 04-bluetooth.sh
│   ├── 05-player.sh
│   ├── 06-samba.sh
│   └── 07-web.sh
├── player/                    # SDL2 touchscreen player
│   ├── main.py
│   ├── engine.py              # MPV playback engine
│   ├── library.py             # Music library scanner
│   ├── bluetooth.py           # Bluetooth manager
│   ├── providers.py           # Spotify, YouTube, Radio
│   ├── config.py              # Config manager
│   └── ui/
│       ├── sdl_app.py         # SDL2 display + screen manager
│       ├── widgets.py         # Button, Slider, CoverArt
│       └── screens.py         # All 4 screen implementations
├── server/                    # Flask API server (port 5000)
│   ├── run.py
│   ├── main.py
│   ├── config.py
│   └── api/
│       ├── music.py
│       ├── playback.py
│       ├── bluetooth.py
│       └── system.py
├── web/                       # React + Vite web UI
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── App.tsx
│       ├── api.ts
│       ├── types.ts
│       ├── components/
│       └── pages/
├── configs/                   # systemd services, udev, samba, bluetooth, alsa
├── scripts/                   # Storage detection, IP setup
└── demo/Music/                # Example music folder structure
```

---

## Storage Architecture

| Drive | Mount | Purpose | Writable |
|---|---|---|---|
| SD card (`/dev/mmcblk0`) | `/` | System, apps, configs | SYSTEM only |
| USB drive 1 | `/mnt/music/usb-1` | Music files | Yes (via SAMBA) |
| USB drive 2 | `/mnt/music/usb-2` | Music files | Yes (via SAMBA) |
| MergerFS pool | `/pool/Music` | Unified view of all USB drives | Yes |

The [SYSTEM] drive is never used for music storage. USB drives are auto-detected when plugged in via udev rules and immediately pooled.

---

## Bluetooth Controls

HueMedia supports AVRCP buttons on Bluetooth headphones:

| Button | Action |
|---|---|
| Single press center | Play / Pause |
| Double press | Next track |
| Triple press | Previous track |
| Volume rocker | Volume up/down |

You can also manage everything from the LCD's Bluetooth screen or the web UI.

---

## Development

```bash
# Clone
git clone https://github.com/vector-just-technology/HueMedia.git
cd HueMedia

# Install deps
pip install pysdl2 python-mpv flask flask-cors Pillow psutil

# Run player in SDL2 X11 mode (for desktop development)
cd player
SDL_VIDEODRIVER=x11 python main.py --sdl --debug

# Run API server standalone
cd ../server
python run.py

# Build web UI
cd ../web
npm install
npm run build
```

---

## License

MIT
