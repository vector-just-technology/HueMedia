#!/bin/bash
# SAMBA file sharing setup

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/00-utils.sh" 2>/dev/null || true

require_root

head "SAMBA Server Setup"

cat > /etc/samba/smb.conf << 'SAMBA'
[global]
   workgroup = WORKGROUP
   server string = HueMedia
   netbios name = HUEMEDIA
   security = user
   map to guest = Bad User
   guest account = nobody
   dns proxy = no
   log level = 0
   load printers = no
   printing = bsd
   disable spoolss = yes
   socket options = TCP_NODELAY IPTOS_LOWDELAY

[MUSIC]
   comment = HueMedia Music Pool
   path = /pool/Music
   browseable = yes
   read only = no
   guest ok = yes
   create mask = 0777
   directory mask = 0777
   force user = hue
   veto files = /lost+found/.Trashes/.Trash-$recycle.bin/
   delete veto files = yes

[SYSTEM]
   comment = HueMedia System (read-only)
   path = /opt/hue-media
   browseable = yes
   read only = yes
   guest ok = no
   valid users = hue
SAMBA

systemctl restart smbd
PI_IP=$(hostname -I | awk '{print $1}')
log "SAMBA shares available at \\\\${PI_IP}\\MUSIC and \\\\${PI_IP}\\SYSTEM"
