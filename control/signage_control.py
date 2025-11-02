#sudo nano /home/sultan/signage/control/signage_control.py

from flask import Flask, render_template, request, send_from_directory
import subprocess
import os
import json

app = Flask(__name__)

# =============================
# KONFIGURASI PATH
# =============================
app.config['UPLOAD_FOLDER_PPTX'] = '/home/sultan/signage/media'
app.config['UPLOAD_FOLDER_VIDEO'] = '/home/sultan/signage/media/video'
app.config['SLIDE_OUTPUT'] = '/home/sultan/signage/media/slide_output'
app.config['MODE_FILE'] = '/home/sultan/signage/config/config.json'

# =============================
# FUNGSI UTILITAS
# =============================

def load_config():
    """
    Memuat konfigurasi dari file JSON.
    Jika file tidak ada, buat konfigurasi default.
    
    Returns:
        dict: Konfigurasi yang dimuat
    """
    default_config = {
        "mode": "video",
        "web_url": "https://example.com"
    }
    
    try:
        # Coba baca file konfigurasi
        with open(app.config['MODE_FILE'], "r") as f:
            config = json.load(f)
            print(f"✅ Config loaded: {config}")
            return config
    except FileNotFoundError:
        # Jika file tidak ada, buat direktori dan file default
        print("⚠️  Config file not found, creating default...")
        os.makedirs(os.path.dirname(app.config['MODE_FILE']), exist_ok=True)
        with open(app.config['MODE_FILE'], "w") as f:
            json.dump(default_config, f, indent=2)
        return default_config
    except Exception as e:
        # Handle error lainnya
        print(f"❌ Error loading config: {e}")
        return default_config

def save_config(config):
    """
    Menyimpan konfigurasi ke file JSON.
    
    Args:
        config (dict): Konfigurasi yang akan disimpan
    """
    try:
        with open(app.config['MODE_FILE'], "w") as f:
            json.dump(config, f, indent=2)
        print(f"✅ Config saved: {config}")
    except Exception as e:
        print(f"❌ Error saving config: {e}")

def ensure_directories():
    """
    Memastikan semua direktori yang diperlukan ada.
    """
    directories = [
        app.config['UPLOAD_FOLDER_PPTX'],
        app.config['UPLOAD_FOLDER_VIDEO'],
        app.config['SLIDE_OUTPUT'],
        os.path.dirname(app.config['MODE_FILE'])
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Directory ensured: {directory}")

# =============================
# ROUTE UTAMA
# =============================

@app.route("/", methods=["GET", "POST"])
def control_panel():
    """
    Route utama untuk control panel signage.
    Menangani semua aksi dan menampilkan interface.
    """
    output = ""
    config = load_config()
    
    # Pastikan direktori ada
    ensure_directories()
    
    # Dapatkan daftar file video
    video_files = []
    if os.path.isdir(app.config['UPLOAD_FOLDER_VIDEO']):
        video_files = sorted([
            f for f in os.listdir(app.config['UPLOAD_FOLDER_VIDEO']) 
            if f.endswith(('.mp4', '.avi', '.mov', '.mkv', '.jpeg', '.jpg'))
        ])
    
    # Dapatkan gambar slide terbaru
    slide_image = None
    if os.path.isdir(app.config['SLIDE_OUTPUT']):
        slides = sorted([
            f for f in os.listdir(app.config['SLIDE_OUTPUT']) 
            if f.endswith(('.png', '.jpg', '.jpeg'))
        ])
        if slides:
            slide_image = slides[-1]  # Ambil slide terbaru
    
    # Handle POST requests (aksi dari user)
    if request.method == "POST":
        try:
            action = request.form.get("action")
            
            # 🔍 Get Service Status
            if action == "status":
                output = subprocess.check_output(
                    ["/usr/bin/systemctl", "status", "signage-auto.service"], 
                    stderr=subprocess.STDOUT
                ).decode()
            
            # 🎞️ Set Video Mode
            elif action == "video":
                config["mode"] = "video"
                save_config(config)
                output = "✅ Mode changed to: VIDEO"
            
            # 🖼️ Set Slide Mode
            elif action == "slide":
                config["mode"] = "slide"
                save_config(config)
                output = "✅ Mode changed to: SLIDE"
            
            # 🌐 Set Web Mode
            elif action == "web":
                config["mode"] = "web"
                save_config(config)
                output = "✅ Mode changed to: WEB"
            
            # 🔁 Restart Service
            elif action == "restart":
                subprocess.run(
                    ["/usr/bin/sudo", "/usr/bin/systemctl", "restart", "signage-auto.service"], 
                    check=True
                )
                output = "✅ Service restarted successfully"
            
            # 📤 Upload Files
            elif "upload" in request.form:
                # Upload PPTX File
                if "pptx_file" in request.files and request.files["pptx_file"].filename:
                    file = request.files["pptx_file"]
                    if file.filename.endswith(".pptx"):
                        filepath = os.path.join(app.config['UPLOAD_FOLDER_PPTX'], "slide.pptx")
                        file.save(filepath)
                        output = f"✅ Slide uploaded: {file.filename}"
                    else:
                        output = "❌ Error: Only .pptx files are allowed"
                
                # Upload Video File
                elif "video_file" in request.files and request.files["video_file"].filename:
                    file = request.files["video_file"]
                    if file.filename.endswith(('.mp4', '.avi', '.mov', '.mkv','.jpeg', '.jpg')):
                        filepath = os.path.join(app.config['UPLOAD_FOLDER_VIDEO'], file.filename)
                        file.save(filepath)
                        output = f"✅ Video uploaded: {file.filename}"
                    else:
                        output = "❌ Error: Only video files (MP4, AVI, MOV, MKV) are allowed"
            
            # 🗑️ Delete Video File
            elif "delete_video" in request.form:
                filename = request.form["delete_video"]
                filepath = os.path.join(app.config['UPLOAD_FOLDER_VIDEO'], filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
                    output = f"✅ Video deleted: {filename}"
                else:
                    output = f"❌ File not found: {filename}"
            
            # 🔧 Update Web URL
            elif "update_web_url" in request.form:
                new_url = request.form.get("new_web_url", "").strip()
                if new_url and new_url.startswith(('http://', 'https://')):
                    config["web_url"] = new_url
                    save_config(config)
                    output = f"✅ Web URL updated to: {new_url}"
                else:
                    output = "❌ Error: Please enter a valid URL starting with http:// or https://"
        
        except subprocess.CalledProcessError as e:
            output = f"❌ Command error: {str(e)}"
        except Exception as e:
            output = f"❌ Unexpected error: {str(e)}"
    
    # Render template dengan data yang diperlukan
    return render_template(
        "control.html",  # Menggunakan file template terpisah
        output=output,
        video_files=video_files,
        slide_image=slide_image,
        config_data=config
    )

# =============================
# ROUTE UNTUK SERVING FILE
# =============================

@app.route("/files/video/<path:filename>")
def serve_video(filename):
    """
    Route untuk melayani file video.
    
    Args:
        filename (str): Nama file video
        
    Returns:
        Response: File video
    """
    return send_from_directory(app.config['UPLOAD_FOLDER_VIDEO'], filename)

@app.route("/files/slide/<path:filename>")
def serve_slide(filename):
    """
    Route untuk melayani file slide/gambar.
    
    Args:
        filename (str): Nama file slide
        
    Returns:
        Response: File gambar slide
    """
    return send_from_directory(app.config['SLIDE_OUTPUT'], filename)

# =============================
# ERROR HANDLERS
# =============================

@app.errorhandler(404)
def not_found(error):
    return "❌ Page not found", 404

@app.errorhandler(500)
def internal_error(error):
    return "❌ Internal server error", 500

# =============================
# INISIALISASI APLIKASI
# =============================

if __name__ == "__main__":
    print("🚀 Starting Signage Control Panel...")
    print("📁 Config paths:")
    print(f"   - PPTX Upload: {app.config['UPLOAD_FOLDER_PPTX']}")
    print(f"   - Video Upload: {app.config['UPLOAD_FOLDER_VIDEO']}")
    print(f"   - Slide Output: {app.config['SLIDE_OUTPUT']}")
    print(f"   - Config File: {app.config['MODE_FILE']}")
    
    # Pastikan direktori template ada
    os.makedirs('templates', exist_ok=True)
    
    # Pastikan direktori ada saat startup
    ensure_directories()
    
    # Muat konfigurasi awal
    initial_config = load_config()
    print(f"📋 Initial config: {initial_config}")
    
    # Jalankan aplikasi
    print("🌐 Server running on http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
