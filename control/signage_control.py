from flask import Flask, render_template, request, send_from_directory, session, redirect, url_for
import subprocess
import os
import json
import sys
from functools import wraps

# =============================
# KONFIGURASI PATH IMPORT
# =============================
# Dapatkan path ke root directory proyek
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)  # Satu level naik ke signage_control_panel/

# Tambahkan project_root ke path Python
sys.path.append(project_root)

# Sekarang import logger
from utils.logger import log

app = Flask(__name__)
app.secret_key = 'signage_control_panel_secret_key_2024'  # Ganti dengan secret key yang kuat

# =============================
# KONFIGURASI PATH
# =============================
app.config['UPLOAD_FOLDER_PPTX'] = '/home/sultan/signage/media'
app.config['UPLOAD_FOLDER_VIDEO'] = '/home/sultan/signage/media/video'
app.config['SLIDE_OUTPUT'] = '/home/sultan/signage/media/slide_output'
app.config['MODE_FILE'] = '/home/sultan/signage/config/config.json'
app.config['USERS_FILE'] = os.path.join(project_root, 'config', 'users.json')

# =============================
# KONFIGURASI TEMPLATE FOLDER
# =============================
# Atur template folder ke direktori templates di root
app.template_folder = os.path.join(project_root, 'templates')

# =============================
# FUNGSI AUTHENTIKASI
# =============================

def load_users():
    """Memuat data user dari file JSON"""
    try:
        with open(app.config['USERS_FILE'], 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Buat file users default jika tidak ada
        default_users = {
            "users": {
                "admin": {
                    "password": "raspberry",
                    "role": "admin"
                },
                "user": {
                    "password": "signage",
                    "role": "user"
                }
            }
        }
        os.makedirs(os.path.dirname(app.config['USERS_FILE']), exist_ok=True)
        with open(app.config['USERS_FILE'], 'w') as f:
            json.dump(default_users, f, indent=2)
        return default_users
    except Exception as e:
        log("ERROR", f"Error loading users: {e}")
        return {"users": {}}

def authenticate_user(username, password):
    """Autentikasi user"""
    users_data = load_users()
    users = users_data.get('users', {})
    
    if username in users and users[username]['password'] == password:
        return users[username]
    return None

def login_required(f):
    """Decorator untuk memerlukan login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator untuk memerlukan role admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            return "❌ Access denied. Admin privileges required.", 403
        return f(*args, **kwargs)
    return decorated_function

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
            log("CONFIG", f"Config loaded: {config}")
            return config
    except FileNotFoundError:
        # Jika file tidak ada, buat direktori dan file default
        log("CONFIG", "Config file not found, creating default configuration")
        os.makedirs(os.path.dirname(app.config['MODE_FILE']), exist_ok=True)
        with open(app.config['MODE_FILE'], "w") as f:
            json.dump(default_config, f, indent=2)
        return default_config
    except Exception as e:
        # Handle error lainnya
        log("ERROR", f"Error loading config: {e}")
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
        log("CONFIG", f"Config saved: {config}")
    except Exception as e:
        log("ERROR", f"Error saving config: {e}")

def ensure_directories():
    """
    Memastikan semua direktori yang diperlukan ada.
    """
    directories = [
        app.config['UPLOAD_FOLDER_PPTX'],
        app.config['UPLOAD_FOLDER_VIDEO'],
        app.config['SLIDE_OUTPUT'],
        os.path.dirname(app.config['MODE_FILE']),
        os.path.dirname(app.config['USERS_FILE'])
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        log("SYSTEM", f"Directory ensured: {directory}")

def execute_system_command(command, action_name):
    """
    Eksekusi perintah system dengan error handling.
    
    Args:
        command (list): Perintah system yang akan dijalankan
        action_name (str): Nama aksi untuk logging
        
    Returns:
        tuple: (success, output_message)
    """
    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        log("SYSTEM", f"{action_name} command executed successfully by {session.get('username', 'unknown')}")
        return True, f"✅ {action_name} initiated successfully"
    except subprocess.CalledProcessError as e:
        error_msg = f"❌ {action_name} failed: {e.stderr.strip() if e.stderr else str(e)}"
        log("ERROR", f"{action_name} failed: {e.stderr.strip() if e.stderr else str(e)}")
        return False, error_msg
    except Exception as e:
        error_msg = f"❌ Unexpected error during {action_name}: {str(e)}"
        log("ERROR", f"Unexpected error during {action_name}: {str(e)}")
        return False, error_msg

# =============================
# ROUTES AUTHENTIKASI
# =============================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Route untuk login"""
    # Jika sudah login, redirect ke control panel
    if 'username' in session:
        return redirect(url_for('control_panel'))
    
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        user = authenticate_user(username, password)
        if user:
            session['username'] = username
            session['role'] = user['role']
            log("AUTH", f"User {username} logged in successfully")
            return redirect(url_for('control_panel'))
        else:
            error = "Invalid username or password"
            log("AUTH", f"Failed login attempt for user: {username}")
    
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    """Route untuk logout"""
    username = session.get('username', 'unknown')
    session.clear()
    log("AUTH", f"User {username} logged out")
    return redirect(url_for('login'))

# =============================
# ROUTE UTAMA
# =============================

@app.route("/", methods=["GET", "POST"])
@login_required
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
                log("ACTION", f"User {session['username']} requested service status")
                output = subprocess.check_output(
                    ["/usr/bin/systemctl", "status", "signage-auto.service"], 
                    stderr=subprocess.STDOUT
                ).decode()
                log("SYSTEM", "Service status retrieved successfully")
            
            # 🎞️ Set Video Mode
            elif action == "video":
                config["mode"] = "video"
                save_config(config)
                output = "✅ Mode changed to: VIDEO"
                log("MODE", f"User {session['username']} switched to VIDEO mode")
            
            # 🖼️ Set Slide Mode
            elif action == "slide":
                config["mode"] = "slide"
                save_config(config)
                output = "✅ Mode changed to: SLIDE"
                log("MODE", f"User {session['username']} switched to SLIDE mode")
            
            # 🌐 Set Web Mode
            elif action == "web":
                config["mode"] = "web"
                save_config(config)
                output = "✅ Mode changed to: WEB"
                log("MODE", f"User {session['username']} switched to WEB mode")
            
            # 🔁 Restart Service
            elif action == "restart":
                log("ACTION", f"User {session['username']} requested service restart")
                subprocess.run(
                    ["/usr/bin/sudo", "/usr/bin/systemctl", "restart", "signage-auto.service"], 
                    check=True
                )
                output = "✅ Service restarted successfully"
                log("SYSTEM", "Service restarted successfully")
            
            # 🔄 Reboot System (Admin only)
            elif action == "reboot":
                if session.get('role') != 'admin':
                    output = "❌ Access denied. Admin privileges required for reboot."
                    log("SECURITY", f"User {session['username']} attempted reboot without admin privileges")
                else:
                    log("ACTION", f"User {session['username']} initiated system reboot")
                    success, message = execute_system_command(
                        ["/usr/bin/sudo", "/sbin/reboot"],
                        "System reboot"
                    )
                    output = message
                    if success:
                        output += "\n\n🔄 System will reboot in a few seconds..."
                        output += "\n📱 Please wait 1-2 minutes for the system to come back online."
            
            # ⭕ Shutdown System (Admin only)
            elif action == "shutdown":
                if session.get('role') != 'admin':
                    output = "❌ Access denied. Admin privileges required for shutdown."
                    log("SECURITY", f"User {session['username']} attempted shutdown without admin privileges")
                else:
                    log("ACTION", f"User {session['username']} initiated system shutdown")
                    success, message = execute_system_command(
                        ["/usr/bin/sudo", "/sbin/shutdown", "-h", "now"],
                        "System shutdown"
                    )
                    output = message
                    if success:
                        output += "\n\n🔴 System is shutting down..."
                        output += "\n⚡ You will need to manually power on the Raspberry Pi to restart it."
            
            # 📤 Upload Files
            elif "upload" in request.form:
                # Upload PPTX File
                if "pptx_file" in request.files and request.files["pptx_file"].filename:
                    file = request.files["pptx_file"]
                    if file.filename.endswith(".pptx"):
                        filepath = os.path.join(app.config['UPLOAD_FOLDER_PPTX'], "slide.pptx")
                        file.save(filepath)
                        output = f"✅ Slide uploaded: {file.filename}"
                        log("UPLOAD", f"User {session['username']} uploaded PPTX: {file.filename}")
                    else:
                        output = "❌ Error: Only .pptx files are allowed"
                        log("ERROR", f"User {session['username']} attempted invalid file type: {file.filename}")
                
                # Upload Video File
                elif "video_file" in request.files and request.files["video_file"].filename:
                    file = request.files["video_file"]
                    if file.filename.endswith(('.mp4', '.avi', '.mov', '.mkv','.jpeg', '.jpg')):
                        filepath = os.path.join(app.config['UPLOAD_FOLDER_VIDEO'], file.filename)
                        file.save(filepath)
                        output = f"✅ Video uploaded: {file.filename}"
                        log("UPLOAD", f"User {session['username']} uploaded video: {file.filename}")
                    else:
                        output = "❌ Error: Only video files (MP4, AVI, MOV, MKV) and images (JPG, JPEG) are allowed"
                        log("ERROR", f"User {session['username']} attempted invalid file type: {file.filename}")
            
            # 🗑️ Delete Video File
            elif "delete_video" in request.form:
                filename = request.form["delete_video"]
                filepath = os.path.join(app.config['UPLOAD_FOLDER_VIDEO'], filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
                    output = f"✅ Video deleted: {filename}"
                    log("DELETE", f"User {session['username']} deleted file: {filename}")
                else:
                    output = f"❌ File not found: {filename}"
                    log("ERROR", f"User {session['username']} attempted to delete non-existent file: {filename}")
            
            # 🔧 Update Web URL
            elif "update_web_url" in request.form:
                new_url = request.form.get("new_web_url", "").strip()
                if new_url and new_url.startswith(('http://', 'https://')):
                    old_url = config["web_url"]
                    config["web_url"] = new_url
                    save_config(config)
                    output = f"✅ Web URL updated to: {new_url}"
                    log("CONFIG", f"User {session['username']} changed Web URL from {old_url} to {new_url}")
                else:
                    output = "❌ Error: Please enter a valid URL starting with http:// or https://"
                    log("ERROR", f"User {session['username']} entered invalid URL: {new_url}")
        
        except subprocess.CalledProcessError as e:
            output = f"❌ Command error: {str(e)}"
            log("ERROR", f"Subprocess command failed: {str(e)}")
        except Exception as e:
            output = f"❌ Unexpected error: {str(e)}"
            log("ERROR", f"Unexpected error: {str(e)}")
    
    # Log akses ke halaman
    log("ACCESS", f"Control panel accessed by {session['username']}")
    
    # Render template dengan data yang diperlukan
    return render_template(
        "control.html",
        output=output,
        video_files=video_files,
        slide_image=slide_image,
        config_data=config,
        username=session.get('username'),
        role=session.get('role')
    )

# =============================
# ROUTE UNTUK SERVING FILE
# =============================

@app.route("/files/video/<path:filename>")
@login_required
def serve_video(filename):
    """
    Route untuk melayani file video.
    
    Args:
        filename (str): Nama file video
        
    Returns:
        Response: File video
    """
    log("ACCESS", f"Video file served to {session['username']}: {filename}")
    return send_from_directory(app.config['UPLOAD_FOLDER_VIDEO'], filename)

@app.route("/files/slide/<path:filename>")
@login_required
def serve_slide(filename):
    """
    Route untuk melayani file slide/gambar.
    
    Args:
        filename (str): Nama file slide
        
    Returns:
        Response: File gambar slide
    """
    log("ACCESS", f"Slide file served to {session['username']}: {filename}")
    return send_from_directory(app.config['SLIDE_OUTPUT'], filename)

# =============================
# ERROR HANDLERS
# =============================

@app.errorhandler(404)
def not_found(error):
    log("ERROR", f"404 Page not found: {request.url}")
    return "❌ Page not found", 404

@app.errorhandler(500)
def internal_error(error):
    log("ERROR", f"500 Internal server error: {str(error)}")
    return "❌ Internal server error", 500

# =============================
# INISIALISASI APLIKASI
# =============================

if __name__ == "__main__":
    print("🚀 Starting Signage Control Panel...")
    log("SYSTEM", "Signage Control Panel starting up")
    
    print("📁 Project structure:")
    print(f"   - Current directory: {current_dir}")
    print(f"   - Project root: {project_root}")
    print(f"   - Template folder: {app.template_folder}")
    
    print("📁 Config paths:")
    print(f"   - PPTX Upload: {app.config['UPLOAD_FOLDER_PPTX']}")
    print(f"   - Video Upload: {app.config['UPLOAD_FOLDER_VIDEO']}")
    print(f"   - Slide Output: {app.config['SLIDE_OUTPUT']}")
    print(f"   - Config File: {app.config['MODE_FILE']}")
    print(f"   - Users File: {app.config['USERS_FILE']}")
    print(f"   - Log File: /home/sultan/signage/logs/signage.log")
    
    # Pastikan direktori ada saat startup
    ensure_directories()
    
    # Muat konfigurasi awal
    initial_config = load_config()
    print(f"📋 Initial config: {initial_config}")
    
    # Muat users
    users = load_users()
    print(f"👥 Loaded {len(users.get('users', {}))} users")
    
    # Jalankan aplikasi
    print("🌐 Server running on http://0.0.0.0:5000")
    log("SYSTEM", "Flask application started on http://0.0.0.0:5000")
    
    app.run(host="0.0.0.0", port=5000, debug=True)

