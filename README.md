### RASPBERRY PI - SIGNAGE

### GITHUB

```git
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/edycoleee/signa-raspi.git
git push -u origin main
```
```py
# reset koneksi ssh
ssh-keygen -R 192.168.171.138
# koneksi ssh
ssh sultan@192.168.171.138
#INSTALL LIBRARY
sudo apt install mpv -y
sudo apt install unclutter -y
sudo apt install libreoffice-impress -y
sudo apt install jq -y
```


### PLAY MEDIA

1. play video

```py
#MEMBUAT .SH UNTUK RUNNING
nano /home/sultan/signage/executor/play_videos.sh
#========================================================#
#/home/sultan/signage/executor/play_videos.sh
#!/bin/bash 
 
VIDEO_DIR="/home/sultan/signage/media/video" 
 
while true; do 
  for video in "$VIDEO_DIR"/; do 
    mpv "$video" --fs --no-border --no-window-dragging --cursor-autohide=always --loop-playlist=yes --image-display-duration=5
  done 
done

#========================================================#
#Supaya bisa di eksekusi
chmod +x /home/sultan/signage/executor/play_videos.sh
bash /home/sultan/signage/executor/play_videos.sh
# Untuk raspberry os trixie, pada mpv : --v0=x11
```
2. play slide ppt

```py
nano /home/sultan/signage/executor/play_ppt.sh

#========================================================#
#!/bin/bash

SOURCE_DIR="/home/sultan/signage"
OUTPUT_DIR="/home/sultan/signage/media/slide_output"
PPTX_FILE="$SOURCE_DIR/media/mode_slide.pptx"

# Pastikan direktori output ada; buat jika belum ada
mkdir -p "$OUTPUT_DIR"

# Konversi file PPTX ke serangkaian file PNG tanpa menampilkan GUI
libreoffice --headless --convert-to png --outdir "$OUTPUT_DIR" "$PPTX_FILE"

# Ambil file PNG pertama dari direktori output
SLIDE=$(ls "$OUTPUT_DIR"/*.png | head -n 1)

# Tampilkan gambar pertama menggunakan mpv dalam mode layar penuh
mpv "$SLIDE" \
  --fs \
  --image-display-duration=9999 \
  --loop-file=inf \
  --no-border \
  --cursor-autohide=always
#========================================================#
chmod +x /home/sultan/signage/executor/play_ppt.sh
bash /home/sultan/signage/executor/play_ppt.sh

```
3. play kiosk web

```py
#contoh menjalankan browser dengan firefox
firefox --kiosk https://www.microsoft.com/id-id
#MEMBUAT .SH UNTUK RUNNING
nano /home/sultan/signage/executor/play_kiosk.sh

#========================================================#
#!/bin/bash

# Ganti URL ini dengan URL yang ingin Anda tampilkan
URL="https://fakestoreapi.com/"

# Perintah untuk meluncurkan Firefox dalam mode kios (full screen)
firefox --kiosk "$URL"
#========================================================#
chmod +x /home/sultan/signage/executor/play_kiosk.sh
bash /home/sultan/signage/executor/play_kiosk.sh

```
4. play all dengan mode dari config.json

```py
# membuat file json untuk perubahan mode player
nano /home/sultan/signage/config/config.json
```
```json
{
  "mode": "web",
  "web_url": "https://daftar.rsudsulfat.id/admin/bed_kosong/tv"
}
```
```py
#membuat file executor
nano /home/sultan/signage/executor/signage_auto.sh
#========================================================#
# ~/signage/executor/signage_auto.sh
#!/bin/bash

# Path ke file konfigurasi
CONFIG_PATH="/home/sultan/signage/config/config.json"
BASE_DIR="/home/sultan/signage"
VIDEO_DIR="$BASE_DIR/media/video"
SLIDE_FILE="$BASE_DIR/media/slide.pptx"
SLIDE_OUT="$BASE_DIR/media/slide_output"

# Fungsi untuk membaca nilai dari config.json menggunakan jq
get_config_value() {
  key=$1
  jq -r ".$key" "$CONFIG_PATH"
}

MODE=$(get_config_value "mode")

if [ "$MODE" = "web" ]; then
  WEB_URL=$(get_config_value "web_url")
  if [[ "$WEB_URL" == http* ]]; then
    echo "Menjalankan signage mode web..."
    firefox --kiosk "$WEB_URL"
  else
    echo "URL tidak valid: $WEB_URL"
    exit 1
  fi

elif [ "$MODE" = "video" ]; then
  echo "Menjalankan signage mode video..."
  if compgen -G "$VIDEO_DIR/*" > /dev/null; then
    mpv "$VIDEO_DIR"/* --fs --no-border --no-window-dragging --cursor-autohide=always --loop-playlist=inf --image-display-duration=5
  else
    echo "Tidak ada file video di $VIDEO_DIR"
    exit 1
  fi

elif [ "$MODE" = "slide" ]; then
  echo "Menjalankan signage mode slide..."
  if [ -f "$SLIDE_FILE" ]; then
    mkdir -p "$SLIDE_OUT"
    libreoffice --headless --convert-to png --outdir "$SLIDE_OUT" "$SLIDE_FILE"
    FIRST_SLIDE=$(ls "$SLIDE_OUT"/*.png | head -n 1)
    if [ -n "$FIRST_SLIDE" ]; then
      mpv "$FIRST_SLIDE" --fs --image-display-duration=9999 --loop-file=inf --no-border --cursor-autohide=always 
    else
      echo "Gagal menemukan slide hasil konversi."
      exit 1
    fi
  else
    echo "File slide tidak ditemukan: $SLIDE_FILE"
    exit 1
  fi

else
  echo "Mode tidak dikenali: $MODE"
  echo "Gunakan mode 'web', 'video', atau 'slide' dalam config.json"
  exit 1
fi

#========================================================#
#Supaya bisa di eksekusi
sudo chmod +x /home/sultan/signage/executor/signage_auto.sh
sudo bash /home/sultan/signage/executor/signage_auto.sh

```

5. buat systemd

```py
#Untuk mengaktifkan signage-auto

#⚙️ Service systemd 
nano /home/sultan/signage/systemd/signage-auto.service

#========================================================#

[Unit]
Description=Signage Auto Mode (triggered by mode.txt)
After=graphical.target

[Service]
User=sultan
Environment=DISPLAY=:0
ExecStart=/home/sultan/signage/executor/signage_auto.sh
Restart=always

[Install]
WantedBy=graphical.target

#========================================================#
#Copykan ke system
sudo cp /home/sultan/signage/systemd/signage-auto.service /etc/systemd/system/
#Melihat isi nya : nano /etc/systemd/system/signage-auto.service

#Aktifkan:
sudo systemctl daemon-reexec
sudo systemctl enable signage-auto.service
sudo systemctl start signage-auto.service
sudo systemctl status signage-auto.service

#setelah reboot maka sistem akan langsung jalan

#jika mau editing config json dengan mengubah menu 
#jalankan ulang: 
sudo systemctl restart signage-auto.service

```

### FLASK - DASAR
```git
git branch 01_flask_dasar         # Membuat branch baru
git checkout 01_flask_dasar        # Berpindah ke branch tersebut
# (lakukan perubahan pada file sesuai kebutuhan)
git add .                       # Menambahkan semua perubahan ke staging area
git commit -m "finish"          # Commit dengan pesan "finish"
git push -u origin 01_flask_dasar  # Push ke remote dan set tracking branch
```
```text
INSTALL RUST DESK
wget -qO- https://raw.githubusercontent.com/Botspot/pi-apps/master/install | bash

lanjut install rustdesk dari pi apps >> internet >> rust desk
setting password Sulfat123#! 
setting jaringan >> relay
SETTING MANUAL
ID SERVER : rust.rsudsulfat.id
RELAY SERVER : rust.rsudsulfat.id
KEY : ========pdf

```
```py
# login dg ssh
sultan@raspberrypi:~ $ cd signage
sultan@raspberrypi:~/signage $

#1. Pastikan python3-full dan venv tersedia
sudo apt install python3-full python3-venv

#2. Buat virtual environment
python3 -m venv signage-venv

#3. Aktifkan virtual environment
source signage-venv/bin/activate
#Setelah aktif, prompt kamu akan berubah jadi:
(signage-venv) sultan@raspberrypi:~/signage $

#4. Install Flask di dalam venv
pip install flask

#5. Jalankan Flask app
nano /home/sultan/signage/control/flask_coba.py
python /home/sultan/signage/control/flask_coba.py

#========================================================#
#/home/sultan/signage/control/flask_coba.py
### untuk mencoba buat script sederhana :
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello World dari Raspberry Pi 5!'

@app.route('/info')
def info():
    return 'Ini adalah halaman info'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
#========================================================#

# melihat IP raspberry
hostname -I
```


### FLASK - CONTROL
```git
git branch 02_flask_control         # Membuat branch baru
git checkout 02_flask_control        # Berpindah ke branch tersebut
# (lakukan perubahan pada file sesuai kebutuhan)
git add .                       # Menambahkan semua perubahan ke staging area
git commit -m "finish"          # Commit dengan pesan "finish"
git push -u origin 02_flask_control  # Push ke remote dan set tracking branch
```
```py
#sudo nano /home/sultan/signage/control/signage_control.py
```
```html
<!-- nano /home/sultan/signage/control.templates/control.html -->
```
```py
#2. Buat File Service systemd====== UPDATE SEBELUMNYA
nano /home/sultan/signage/systemd/signage-flask.service

Isi dengan:
#========================================================#
[Unit]
Description=Flask Web Server for Signage Control
After=network.target

[Service]
User=sultan
WorkingDirectory=/home/sultan/signage/control
Environment="PATH=/home/sultan/signage/signage-venv/bin"
ExecStart=/home/sultan/signage/signage-venv/bin/python signage_control.py
Restart=always

[Install]
WantedBy=multi-user.target
#========================================================#
#3. Aktifkan dan Jalankan Service

sudo cp /home/sultan/signage/systemd/signage-flask.service /etc/systemd/system/
#Melihat isi nya : nano /etc/systemd/system/signage-flask.service

sudo systemctl daemon-reexec
sudo systemctl enable signage-flask.service
sudo systemctl start signage-flask.service
sudo systemctl restart signage-flask.service

#Cek status:

sudo systemctl status signage-flask.service
#4. Akses Web Server
•	Di Raspberry Pi: http://localhost:5000
•	Dari jaringan lain: http://<IP-RASPBERRY>:5000
#Tips Debugging
#Jika ada error:
journalctl -u signage-flask.service -e

```


### FLASK - CONTROL - LOGGER
```git
git branch 03_flask_logger        # Membuat branch baru
git checkout 03_flask_logger        # Berpindah ke branch tersebut
# (lakukan perubahan pada file sesuai kebutuhan)
git add .                       # Menambahkan semua perubahan ke staging area
git commit -m "finish"          # Commit dengan pesan "finish"
git push -u origin 03_flask_logger  # Push ke remote dan set tracking branch
```
```py
#📁 /home/sultan/signage/utils/logger.py
import os
import datetime

LOG_DIR = "/home/sultan/signage/logs"
LOG_PATH = os.path.join(LOG_DIR, "signage.log")

# Pastikan folder log ada
os.makedirs(LOG_DIR, exist_ok=True)

def log(action, message):
    """Catat event ke signage.log"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {action.upper()}: {message}\n"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)

#========================================================#
# 🔍 Cara Melihat Log:
# Lihat log real-time
tail -f /home/sultan/signage/logs/signage.log

# Lihat seluruh log
cat /home/sultan/signage/logs/signage.log

# Cari error saja
grep "ERROR" /home/sultan/signage/logs/signage.log
```
```py
#sudo nano /home/sultan/signage/control/signage_control.py
```
```text
<!-- nano /home/sultan/signage/control.templates/control.html -->
File: templates/control.html (Tetap sama)
File template HTML tetap sama seperti sebelumnya
```

### FLASK - CONTROL - SHUTDOWN - USER ROLE
```git
git branch 04_flask_user        # Membuat branch baru
git checkout 04_flask_user         # Berpindah ke branch tersebut
# (lakukan perubahan pada file sesuai kebutuhan)
git add .                       # Menambahkan semua perubahan ke staging area
git commit -m "finish"          # Commit dengan pesan "finish"
git push -u origin 04_flask_user   # Push ke remote dan set tracking branch
```
nano /home/sultan/signage/config/users.json
```json
{
  "users": {
    "admin": {
      "password": "admin",
      "role": "admin"
    },
    "user": {
      "password": "user",
      "role": "user"
    }
  }
}
```

```html
<!-- nano /home/sultan/signage/control/templates/login.html -->
```
```py
#sudo nano /home/sultan/signage/control/signage_control.py
```
```html
<!-- nano /home/sultan/signage/control.templates/control.html -->
```

### CATATAN
```git
git clone -b 04_flask_user https://github.com/edycoleee/signa-raspi.git signage

#PELAJARAN TENTANG KEPEMILIKAN FILE
#user file >> sudo file
# 1. Buat dan edit file awal tanpa sudo
nano /home/sultan/my_script.sh

# 2. Ubah kepemilikan ke root 
#(membutuhkan sudo untuk eksekusi perintah ini)
sudo chown root:root /home/sultan/my_script.sh

# 3. Beri izin eksekusi
sudo chmod +x /home/sultan/my_script.sh

#sudo file >> user file
sudo chown sultan:sultan /home/sultan/my_script.sh

#Use code with caution.
#Penjelasan:
#•	sudo: Menjalankan perintah sebagai superuser (root).
#•	chown: Perintah untuk mengubah pemilik file (change owner).
#•	sultan:sultan: 
#Mengatur pemilik (sultan) dan grup (sultan) kembali ke nama pengguna Anda. 
#Sesuaikan sultan jika nama pengguna Anda berbeda.
```