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

### FLASK - CONTROL

### FLASK - CONTROL - SHUTDOWN

### FLASK - CONTROL - SHUTDOWN - USER ROLE