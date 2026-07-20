<p align="center">
  <img src="https://img.shields.io/badge/HueMedia-Media%20Player-purple" alt="HueMedia">
  <img src="https://img.shields.io/badge/MPV-Engine-green" alt="MPV">
  <img src="https://img.shields.io/badge/LVGL-UI-blue" alt="LVGL">
  <img src="https://img.shields.io/badge/Raspberry%20Pi-3B-red" alt="RPi3B">
  <img src="https://img.shields.io/badge/Licence-MIT-orange" alt="Licence">
</p>

# HueMedia

A lightweight, touch-optimized media player for **Raspberry Pi 3B** with **Hosyond 3.5" GPIO touchscreen (LCD-35-Show)**. Bluetooth headphones, Spotify/YouTube streaming, auto-storage pooling, dual-drive isolation, and a web management interface at `10.0.0.174:5000`.

---

## Features

| Feature | Description |
|---|---|
| **Touch UI** | LVGL-powered interface built for the 3.5" display — big buttons, swipeable screens |
| **Audio Playback** | MPV engine with hardware acceleration — plays MP3, FLAC, WAV, AAC, and more |
| **Video Playback** | Full video support on the 3.5" screen |
| **Bluetooth** | Pair headphones, handle AVRCP buttons (play/pause/skip/back), on-screen device management |
| **Spotify / YouTube** | Stream via `yt-dlp` + MPV; Spotify via `librespot` |
| **Music Library** | Auto-scans `Music/Artist/Song/song.mp3 + cover.png` structure; alphabetical sort, shuffle, repeat |
| **Cover Art** | Reads `cover.png` per song folder; displays on screen and web UI |
| **Web Interface** | Rich React-based UI at `10.0.0.174:5000` — browse library, manage playback, upload songs, SSH terminal, plugin manager |
| **Dual Drive** | `[SYSTEM]` drive (SD card) is read-only for music; `[MUSIC]` drives (USB) are auto-detected and pooled via mergerfs |
| **SAMBA** | Network file sharing to easily drop music onto your pooled drives |
| **Recovery System** | First-boot webpage at `10.0.0.174:3000` handles LCD driver installation, SSH re-enable, diagnostics |
| **Battery Optimized** | Idle CPU scaling, USB autosuspend, lightweight stack |

---

## Hardware Requirements

- Raspberry Pi 3B (or 3B+)
- Hosyond 3.5" GPIO touchscreen (LCD-35-Show driver)
- MicroSD card (16GB+ recommended)
- USB drive(s) for music storage
- Optional: Bluetooth headphones/speakers

---

## Quick Install

```bash
curl -sSL https://raw.githubusercontent.com/vector-just-technology/HueMedia/main/install.sh | bash
```

The installer will:
1. Set up a **recovery web server** on `10.0.0.174:3000`
2. Install the LCD-35-Show driver
3. Reboot
4. Recovery server checks all systems — if OK, proceeds with full setup
5. Installs MPV, LVGL, Bluetooth, SAMBA, pooling, web UI
6. Reboots into HueMedia

> **If something goes wrong** after the LCD install, navigate to `http://10.0.0.174:3000` to see diagnostics, re-enable SSH, or retry.

---

## Folder Structure

```
HueMedia/
├── install.sh                 # One-shot installer
├── setup/                     # Modular install scripts
├── recovery/                  # Recovery web server (port 3000)
├── player/                    # LVGL touchscreen player
├── server/                    # Flask API server (port 5000)
├── web/                       # React + Vite web UI
├── configs/                   # systemd services, udev rules, samba
└── scripts/                   # Storage detection, pool management
```

### Music Library Layout

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

Songs are sorted alphabetically by default. Shuffle and repeat are supported.

---

## Web Interface

| Endpoint | Description |
|---|---|
| `http://10.0.0.174:5000` | Full web UI — music library, playback, bluetooth, settings |
| `http://10.0.0.174:5000/terminal` | Web-based SSH terminal |
| `http://10.0.0.174:5000/plugins` | Plugin manager |

---

## Storage Architecture

| Drive | Purpose | Writable |
|---|---|---|
| `/dev/mmcblk0` (SD) | System, apps, configs | Read-only for music |
| `/mnt/music/*` (USB) | Pooled music storage | SAMBA, uploads |
| `/pool/Music` (mergerfs) | Unified view of all music drives | — |

---

## Bluetooth Controls

HueMedia supports AVRCP buttons on Bluetooth headphones:
- **Play/Pause** — single press
- **Next** — double press or forward
- **Previous** — triple press or back
- Volume control via on-screen slider or headphones

---

## Development

```bash
# Clone
git clone https://github.com/vector-just-technology/HueMedia.git
cd HueMedia

# Install dependencies (on RPi)
sudo bash install.sh

# Or for development on desktop (SDL2 mode):
pip install -r server/requirements.txt
cd player && python main.py --sdl
```

---

## License

MIT
