#!/bin/bash

# --- Konfigurasi ---
SOURCE_DIR="/home/sultan/signage"
OUTPUT_DIR="/home/sultan/signage/media/slide_output"
PPTX_FILE="$SOURCE_DIR/media/slide.pptx"

# Tambahkan logging untuk debugging
echo "Memulai script konversi dan tampilan slide..."
echo "File sumber: $PPTX_FILE"
echo "Direktori output: $OUTPUT_DIR"

# Pastikan direktori output ada; buat jika belum ada
mkdir -p "$OUTPUT_DIR"

# Hapus file PNG lama terlebih dahulu untuk memastikan hanya slide baru yang diproses
rm -f "$OUTPUT_DIR"/*.png

# --- Proses Konversi ---
echo "Memulai konversi PPTX ke PNG..."
# Menggunakan 'soffice' karena 'libreoffice' terkadang hanya wrapper script
soffice --headless --convert-to png --outdir "$OUTPUT_DIR" "$PPTX_FILE"

# Periksa apakah konversi berhasil
if [ $? -eq 0 ]; then
    echo "Konversi berhasil. Mencari file PNG..."
else
    echo "ERROR: Konversi gagal. Periksa apakah file PPTX ada dan dapat diakses, dan apakah semua dependensi LibreOffice terinstal (termasuk Java common)."
    exit 1
fi

# Ambil file PNG pertama dari direktori output, diurutkan berdasarkan nama (ls -v untuk pengurutan numerik)
SLIDE=$(ls -v "$OUTPUT_DIR"/*.png 2>/dev/null | head -n 1)

# Periksa apakah file PNG ditemukan
if [ -f "$SLIDE" ]; then
    echo "File slide pertama ditemukan: $SLIDE"
else
    echo "ERROR: Tidak ada file PNG yang ditemukan di $OUTPUT_DIR. Script berhenti."
    exit 1
fi

# --- Tampilkan Gambar ---
echo "Menampilkan gambar menggunakan mpv..."
mpv "$SLIDE" \
  --fs \
  --image-display-duration=9999 \
  --loop-file=inf \
  --no-border \
  --cursor-autohide=always

