#!/bin/bash 

# Pastikan jq terinstal untuk membaca JSON
if ! command -v jq &> /dev/null; then
    echo "Error: 'jq' tidak ditemukan. Harap instal dengan: sudo apt install jq"
    exit 1
fi

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

# Ambil mode dari config.json
MODE=$(get_config_value "mode") 

# --- Logika Eksekusi Berdasarkan Mode ---

if [ "$MODE" = "web" ]; then 
  WEB_URL=$(get_config_value "web_url") 
  if [[ "$WEB_URL" == http* ]]; then 
    echo "Menjalankan signage mode web di URL: $WEB_URL" 
    # Gunakan chromium-browser atau firefox, tergantung yang terinstal di Pi Anda
    firefox --kiosk "$WEB_URL"
  else 
    echo "URL tidak valid: $WEB_URL" 
    exit 1 
  fi 

elif [ "$MODE" = "video" ]; then 
  echo "Menjalankan signage mode video dari: $VIDEO_DIR" 
  # Periksa keberadaan file video dengan lebih baik
  if ls "$VIDEO_DIR"/* &> /dev/null; then 
    mpv "$VIDEO_DIR"/* --fs --no-border --no-window-dragging --cursor-autohide=always --loop-playlist=inf --image-display-duration=5 
  else 
    echo "Tidak ada file video di $VIDEO_DIR" 
    exit 1 
  fi 

elif [ "$MODE" = "slide" ]; then 
  echo "Menjalankan signage mode slide dari: $SLIDE_FILE" 
  if [ -f "$SLIDE_FILE" ]; then 
    mkdir -p "$SLIDE_OUT" 
    # Hapus slide lama dulu agar tidak tercampur
    rm -f "$SLIDE_OUT"/*.png
    
    # Jalankan konversi dan tangkap error jika gagal
    libreoffice --headless --convert-to png --outdir "$SLIDE_OUT" "$SLIDE_FILE"
    if [ $? -ne 0 ]; then
        echo "Error: Konversi LibreOffice gagal."
        exit 1
    fi
    
    # Ambil file PNG pertama
    FIRST_SLIDE=$(ls "$SLIDE_OUT"/*.png 2>/dev/null | head -n 1) 
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
