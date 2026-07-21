<p align="center">
  <img src="https://img.shields.io/badge/HueMedia-Media%20Player-purple" alt="HueMedia">
  <img src="https://img.shields.io/badge/MPV-Engine-green" alt="MPV">
  <img src="https://img.shields.io/badge/Raspberry%20Pi-3B-red" alt="RPi3B">
  <img src="https://img.shields.io/badge/Licence-MIT-orange" alt="Licence">
</p>

# HueMedia

A lightweight media player for **Raspberry Pi OS Desktop**. MPV playback engine, Bluetooth A2DP/AVRCP headphones, Spotify/YouTube streaming, auto-detecting USB storage pooling, SAMBA sharing, and a full-screen Chromium kiosk web interface.

---

## Features

| Feature | Details |
|---|---|
| **Kiosk UI** | Chromium fullscreen on boot — no chrome, edge-to-edge touch interface |
| **Playback** | MPV engine — MP3, FLAC, WAV, AAC, MP4, MKV |
| **Bluetooth** | Pair headphones, AVRCP controls, on-screen management |
| **Spotify / YouTube** | Stream via yt-dlp + MPV; Spotify via librespot |
| **Cover Art** | Reads `cover.png` per song folder |
| **Music Library** | Auto-scans USB drives — alphabetical sort, shuffle, repeat |
| **Web Interface** | React SPA — browse, play, upload, SSH terminal |
| **Dual Drive** | SD card = SYSTEM; USB drives = Music, auto-pooled via mergerfs |
| **SAMBA** | `\\<pi-ip>\MUSIC` — drag-and-drop music |
| **Auto-Update** | Checks for new GitHub tags on boot, updates automatically |

---

## Hardware Requirements

- **Raspberry Pi 3B** or 3B+ (or any device running Raspberry Pi OS Desktop)
- MicroSD card (32GB+)
- USB drive(s) for music (FAT32, exFAT, NTFS, ext4)
- HDMI display with touch (or keyboard/mouse)
- Optional: Bluetooth headphones/speakers

---

## Installation

### One-Line Install

Flash **Raspberry Pi OS Desktop (Bookworm, 64-bit)** to your SD card. Boot the Pi, connect to your network, find its IP, then SSH in:

```bash
ssh pi@<pi-ip>
sudo apt update && sudo apt install -y curl
curl -sSL https://raw.githubusercontent.com/vector-just-technology/HueMedia/main/install.sh | sudo bash
```

After the install completes, the Pi reboots into the HueMedia kiosk — Chromium fullscreen, showing the web interface.

### Post-Installation

| Service | Address | Description |
|---|---|---|
| **Web UI** | `http://<pi-ip>:5000` | Full music management |
| **SAMBA** | `\\<pi-ip>\MUSIC` | Drag-and-drop music |
| **SSH** | `ssh hue@<pi-ip>` | System access |
| **Display** | Built-in kiosk | Chromium fullscreen on HDMI |

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
├── player/                    # Backend modules
│   ├── engine.py              # MPV playback engine
│   ├── library.py             # Music library scanner
│   ├── bluetooth.py           # Bluetooth manager
│   ├── providers.py           # Spotify, YouTube
│   └── config.py              # Config manager
├── server/                    # Flask API server (port 5000)
│   ├── run.py
│   ├── main.py
│   ├── config.py
│   └── api/
├── web/                       # React + Vite web UI
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
├── configs/                   # systemd services, udev, samba, alsa
├── scripts/                   # Auto-update, kiosk session
└── demo/Music/                # Example music folder structure
```

---

## Adding Music

Organize music on any USB drive:

```
/MUSIC/
  Artist Name/
    Song Name/
      Song.mp3
      cover.png
```

USB drives are auto-detected and pooled at `/pool/Music`. Upload via the web UI or SAMBA.

---

## License

MIT
