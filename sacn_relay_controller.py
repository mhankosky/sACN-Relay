import socket, threading, time, json, subprocess, os, re, tempfile, ast
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify, flash, send_file, session
from flask_session import Session
from sacn import sACNreceiver
from PIL import Image, ImageDraw, ImageFont
import board, busio, netifaces
from gpiozero import OutputDevice
import psutil

# -------------------------- APP DIRECTORY --------------------------
APP_DIR = os.path.expanduser('~/sACN-Relay')
os.makedirs(APP_DIR, exist_ok=True)

# -------------------------- Flask Setup --------------------------
app = Flask(__name__, 
            template_folder=os.path.join(APP_DIR, 'assets/html'), 
            static_folder=os.path.join(APP_DIR, 'assets'))
app.secret_key = 'sacn-relay-super-secret-key-2025'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(APP_DIR, 'flask_session')
Session(app)

# -------------------------- VERSION --------------------------
CURRENT_VERSION = "1.2.0"

# -------------------------- GPIO (8 Relays) --------------------------
RELAY_PINS = [17, 18, 27, 22, 23, 24, 25, 26]  # 8 channels
relays = [OutputDevice(p, active_high=False, initial_value=False) for p in RELAY_PINS]

# -------------------------- OLED --------------------------
i2c = busio.I2C(board.SCL, board.SDA)
oled = None
OLED_AVAILABLE = True
try:
    oled = SSD1306_I2C(128, 64, i2c)
    oled.fill(0); oled.show()
except Exception as e:
    print(f"OLED not available: {e}")
    OLED_AVAILABLE = False
    oled = None

image = Image.new("1", (128, 64))
draw = ImageDraw.Draw(image)
font = ImageFont.load_default()
small_font = ImageFont.load_default()

# -------------------------- sACN --------------------------
receiver = None

# -------------------------- Config --------------------------
config_file = os.path.join(APP_DIR, 'config.json')
py_file = os.path.join(APP_DIR, 'sacn_relay_controller.py')

default_config = {
    'network': 'dhcp', 'ip': '192.168.1.100', 'subnet': '255.255.255.0',
    'gateway': '192.168.1.1', 'dns1': '8.8.8.8', 'dns2': '8.8.4.4',
    'hostname': 'raspberrypi',
    'universe': 1,
    'channels': [1, 2, 3, 4, 5, 6, 7, 8],
    'setpoints': [51, 51, 51, 51, 51, 51, 51, 51],
    'mode': '4',
    'version': CURRENT_VERSION,
    'theme': 'light',
    'security_enabled': False,
    'password': 'admin123',
    'py_file': py_file
}
config = default_config.copy()
current_hostname = socket.gethostname()
config['hostname'] = current_hostname

def load_config():
    global config
    try:
        with open(config_file) as f:
            loaded = json.load(f)
        for key, value in default_config.items():
            if key not in loaded:
                loaded[key] = value
        if loaded['version'] != CURRENT_VERSION:
            loaded['version'] = CURRENT_VERSION
        loaded['channels'] = (loaded.get('channels', []) + [1]*8)[:8]
        loaded['setpoints'] = (loaded.get('setpoints', []) + [51]*8)[:8]
        config.update(loaded)
    except FileNotFoundError:
        config.update(default_config)
        config['hostname'] = current_hostname
        save_config()

def save_config():
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4)

load_config()

MAX_CHANNELS = 8
CHANNEL_COUNT = 4 if config['mode'] == '4' else 8
relay_states = [False] * MAX_CHANNELS
current_dmx_values = [0] * MAX_CHANNELS

# ------------------- System helpers -------------------
def apply_network_config():
    dhcpcd_conf = '/etc/dhcpcd.conf'
    with open(dhcpcd_conf) as f: lines = f.readlines()
    if config['network'] == 'dhcp':
        lines = [l if not l.strip().startswith('static') else f'# {l}' for l in lines]
    else:
        profile = f"""
interface eth0
static ip_address={config['ip']}/{subnet_to_cidr(config['subnet'])}
static routers={config['gateway']}
static domain_name_servers={config['dns1']} {config['dns2']}
"""
        lines = [l for l in lines if not (l.strip().startswith('interface eth0') and not l.strip().startswith('#'))]
        lines.append(profile)

    with tempfile.NamedTemporaryFile('w', delete=False) as tf:
        tf.writelines(lines); tmp = tf.name
    subprocess.run(['sudo', 'cp', tmp, dhcpcd_conf], check=True)
    os.unlink(tmp)
    subprocess.run(['sudo', 'systemctl', 'restart', 'dhcpcd'])
    time.sleep(5)

def subnet_to_cidr(s): return 24 if s == '255.255.255.0' else 24

def apply_hostname_config():
    new = config['hostname']
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9]$', new) or len(new) > 63:
        raise ValueError('Invalid hostname')
    subprocess.run(['sudo', 'hostnamectl', 'set-hostname', new], check=True)
    with open('/etc/hosts') as f: lines = f.readlines()
    lines = [l.replace(f" {current_hostname} ", f" {new} ") for l in lines]
    with tempfile.NamedTemporaryFile('w', delete=False) as tf:
        tf.writelines(lines); tmp = tf.name
    subprocess.run(['sudo', 'cp', tmp, '/etc/hosts'], check=True)
    os.unlink(tmp)
    globals()['current_hostname'] = new

# -------------------------- sACN --------------------------
def init_sacn():
    global receiver
    if receiver: receiver.stop()
    receiver = sACNreceiver()
    receiver.start()
    receiver.join_multicast(config['universe'])

    @receiver.listen_on('universe', universe=config['universe'])
    def pkt(p):
        global current_dmx_values
        if p.dmxStartCode != 0x00: return
        d = p.dmxData
        for i in range(CHANNEL_COUNT):
            ch = config['channels'][i]
            if len(d) < ch: continue
            val = d[ch-1]
            percent = round(val / 255 * 100)
            current_dmx_values[i] = percent
            setpoint = config['setpoints'][i]
            new = percent >= setpoint
            if new != relay_states[i]:
                relay_states[i] = new
                relays[i].on() if new else relays[i].off()
        for i in range(CHANNEL_COUNT, MAX_CHANNELS):
            if relay_states[i]:
                relay_states[i] = False
                relays[i].off()
            current_dmx_values[i] = 0

# --------------------- 5-second pulse --------------------
def pulse_relay(rid):
    i = rid - 1
    if 0 <= i < CHANNEL_COUNT:
        print(f"Pulse Relay {rid} ON for 5s")
        relay_states[i] = True
        relays[i].on()
        threading.Timer(5.0, lambda: _off(i)).start()

def _off(i):
    relay_states[i] = False
    relays[i].off()

# -------------------------- OLED --------------------------
def update_oled():
    while True:
        hn = socket.gethostname()
        ip = 'No IP'
        try:
            if 'eth0' in netifaces.interfaces():
                ip = netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr']
        except: pass
        draw.rectangle((0,0,128,64), fill=0)
        draw.text((0,0), f"{hn[:10]} U:{config['universe']}", font=font, fill=255)
        draw.text((0,20), f"({ip}:8080)", font=font, fill=255)
        bw, bh, m = 15, 12, 2
        sx = (128 - (CHANNEL_COUNT*bw + (CHANNEL_COUNT-1)*m)) // 2
        for i in range(CHANNEL_COUNT):
            x = sx + i*(bw+m); y = 44; ch = str(config['channels'][i])
            fill = 255 if relay_states[i] else 0
            txt  = 0   if relay_states[i] else 255
            draw.rectangle((x,y,x+bw,y+bh), outline=255-fill, fill=fill)
            bb = draw.textbbox((x,y), f"{ch}", font=small_font)
            tx = x + (bw - (bb[2]-bb[0]))//2
            ty = y + (bh - (bb[3]-bb[1]))//2
            draw.text((tx,ty), f"{ch}", font=small_font, fill=txt)
        if OLED_AVAILABLE and oled:
            oled.image(image); oled.show()
        time.sleep(1)

threading.Thread(target=update_oled, daemon=True).start()
init_sacn()

# -------------------------- Flask --------------------------
@app.route('/assets/<path:filename>')
def assets(filename):
    return send_from_directory(os.path.join(APP_DIR, 'assets'), filename)

# -------------------------- Helper --------------------------
def get_current_ip():
    try:
        if 'eth0' in netifaces.interfaces():
            return netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr']
    except: pass
    return 'No IP'

def get_system_stats():
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    return {
        'cpu_percent': round(cpu, 1),
        'mem_used_mb': round(mem.used / 1024 / 1024, 1),
        'mem_total_mb': round(mem.total / 1024 / 1024, 1)
    }

# -------------------------- Auth --------------------------
def require_auth():
    if not config['security_enabled']:
        return True
    if 'authenticated' not in session:
        return False
    return True

@app.before_request
def check_auth():
    if request.path.startswith('/assets/') or request.path in ['/login', '/static']:
        return
    if not require_auth():
        return redirect(url_for('login', next=request.path))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == config['password']:
            session['authenticated'] = True
            return redirect(request.args.get('next') or url_for('main'))
        else:
            flash("Invalid password", "danger")
    return render_template('login.html', version=CURRENT_VERSION)

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('login'))

# -------------------------- Routes --------------------------
@app.route('/', methods=['GET','POST'])
def main():
    ip = get_current_ip()
    if request.method == 'POST':
        config['universe'] = int(request.form['universe'])
        for i in range(CHANNEL_COUNT):
            config['channels'][i] = int(request.form[f'ch{i+1}'])
            config['setpoints'][i] = int(request.form[f'sp{i+1}'])
        save_config()
        init_sacn()
        return redirect(url_for('main'))

    return render_template('main.html',
        hostname=config['hostname'], universe=config['universe'],
        channels=config['channels'][:CHANNEL_COUNT],
        setpoints=config['setpoints'][:CHANNEL_COUNT],
        channel_count=CHANNEL_COUNT,
        current_ip=ip, version=CURRENT_VERSION, theme=config['theme'],
        security_enabled=config['security_enabled'])

@app.route('/status')
def status():
    ip = get_current_ip()
    status_data = [{
        'channel': config['channels'][i],
        'dmx_percent': current_dmx_values[i],
        'setpoint': config['setpoints'][i],
        'relay_state': 'ON' if relay_states[i] else 'OFF'
    } for i in range(CHANNEL_COUNT)]
    return render_template('status.html',
        hostname=config['hostname'], current_ip=ip, status=status_data,
        channel_count=CHANNEL_COUNT,
        version=CURRENT_VERSION, theme=config['theme'],
        security_enabled=config['security_enabled'])

@app.route('/status/data')
def status_data():
    status_data = [{
        'channel': config['channels'][i],
        'dmx_percent': current_dmx_values[i],
        'setpoint': config['setpoints'][i],
        'relay_state': 'ON' if relay_states[i] else 'OFF'
    } for i in range(CHANNEL_COUNT)]
    
    system = get_system_stats()
    
    return jsonify({
        'status': status_data,
        'system': system
    })

@app.route('/test')
def test():
    return render_template('test.html',
        hostname=config['hostname'],
        channels=config['channels'][:CHANNEL_COUNT],
        channel_count=CHANNEL_COUNT,
        version=CURRENT_VERSION, theme=config['theme'],
        security_enabled=config['security_enabled'])

@app.route('/pulse/<int:rid>', methods=['POST'])
def pulse(rid):
    if rid <= CHANNEL_COUNT:
        pulse_relay(rid)
    return redirect(url_for('test'))

@app.route('/networking', methods=['GET', 'POST'])
def networking():
    ip = get_current_ip()
    if request.method == 'POST':
        config['network'] = request.form['network']
        if config['network'] == 'static':
            config['ip'] = request.form['ip']
            config['subnet'] = request.form['subnet']
            config['gateway'] = request.form['gateway']
            config['dns1'] = request.form['dns1']
            config['dns2'] = request.form['dns2']
        else:
            config['dns1'] = '8.8.8.8'
            config['dns2'] = '8.8.4.4'
        save_config()
        apply_network_config()
        return redirect(url_for('networking'))
    return render_template('networking.html',
        hostname=config['hostname'], network=config['network'],
        ip=config['ip'], subnet=config['subnet'], gateway=config['gateway'],
        dns1=config['dns1'], dns2=config['dns2'],
        current_ip=ip, version=CURRENT_VERSION, theme=config['theme'],
        security_enabled=config['security_enabled'])

@app.route('/device', methods=['GET', 'POST'])
def device():
    ip = get_current_ip()
    reboot_needed = False
    if request.method == 'POST':
        new_hostname = request.form['hostname'].strip()
        new_mode = request.form['mode']
        if re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9]$', new_hostname) and len(new_hostname) <= 63:
            old_mode = config['mode']
            config['hostname'] = new_hostname
            config['mode'] = new_mode

            target_count = 4 if new_mode == '4' else 8
            config['channels'] = config['channels'][:target_count] + [1]*(target_count - len(config['channels']))
            config['setpoints'] = config['setpoints'][:target_count] + [51]*(target_count - len(config['setpoints']))

            save_config()
            apply_hostname_config()
            if old_mode != new_mode:
                reboot_needed = True
            global CHANNEL_COUNT
            CHANNEL_COUNT = target_count
            init_sacn()
            flash("Settings saved!", "success")
        else:
            flash("Invalid hostname", "danger")
    return render_template('device.html',
        hostname=config['hostname'], current_ip=ip,
        mode=config['mode'],
        reboot_needed=reboot_needed,
        version=CURRENT_VERSION, theme=config['theme'],
        security_enabled=config['security_enabled'])

@app.route('/reboot', methods=['POST'])
def reboot_pi():
    if config['security_enabled'] and 'authenticated' not in session:
        return "Unauthorized", 403
    flash("Rebooting Pi... Please wait 30 seconds.", "info")
    threading.Timer(1.0, lambda: subprocess.run(['sudo', 'reboot'])).start()
    return redirect(url_for('device'))

@app.route('/interface', methods=['GET', 'POST'])
def interface():
    if request.method == 'POST':
        config['theme'] = request.form.get('theme', 'light')
        save_config()
        return redirect(url_for('interface'))
    return render_template('interface.html',
        hostname=config['hostname'], current_ip=get_current_ip(),
        version=CURRENT_VERSION, theme=config['theme'],
        security_enabled=config['security_enabled'])

@app.route('/security', methods=['GET', 'POST'])
def security():
    if request.method == 'POST':
        config['security_enabled'] = 'enable' in request.form
        new_password = request.form.get('password', '').strip()
        if new_password:
            config['password'] = new_password
        save_config()
        flash("Security settings updated!", "success")
        return redirect(url_for('security'))
    return render_template('security.html',
        hostname=config['hostname'], current_ip=get_current_ip(),
        version=CURRENT_VERSION, theme=config['theme'],
        security_enabled=config['security_enabled'],
        config=config)

@app.route('/backup')
def backup():
    return render_template('backup.html',
        hostname=config['hostname'], current_ip=get_current_ip(),
        version=CURRENT_VERSION, theme=config['theme'],
        security_enabled=config['security_enabled'])

@app.route('/backup/download')
def backup_download():
    hostname = config['hostname']
    mode = "8" if config['mode'] == '8' else "4"
    filename = f"{hostname}-sACN-Relay{mode}-config-v{CURRENT_VERSION}.json"
    return send_file(config_file, as_attachment=True, download_name=filename)

@app.route('/backup/upload', methods=['POST'])
def backup_upload():
    if 'file' not in request.files:
        flash("No file uploaded", "danger")
        return redirect(url_for('backup'))
    file = request.files['file']
    if file.filename == '':
        flash("No file selected", "danger")
        return redirect(url_for('backup'))

    try:
        uploaded = json.load(file)
    except:
        flash("Invalid JSON file", "danger")
        return redirect(url_for('backup'))

    if 'version' not in uploaded:
        flash("Config missing version", "danger")
        return redirect(url_for('backup'))
    if uploaded['version'] > CURRENT_VERSION:
        flash(f"Config version {uploaded['version']} is newer than current {CURRENT_VERSION}", "danger")
        return redirect(url_for('backup'))

    required = ['universe', 'channels', 'setpoints', 'network', 'ip', 'subnet', 'gateway', 'hostname']
    missing = [k for k in required if k not in uploaded]
    if missing:
        flash(f"Missing keys: {', '.join(missing)}", "danger")
        return redirect(url_for('backup'))

    session['uploaded_config'] = uploaded
    return render_template('backup_confirm.html',
        hostname=config['hostname'], current_ip=get_current_ip(),
        version=CURRENT_VERSION, theme=config['theme'],
        uploaded=uploaded,
        security_enabled=config['security_enabled'])

@app.route('/backup/confirm', methods=['POST'])
def backup_confirm():
    if 'uploaded_config' not in session:
        flash("No config to apply", "danger")
        return redirect(url_for('backup'))
    
    new_config = session.pop('uploaded_config')
    for key, value in default_config.items():
        if key not in new_config:
            new_config[key] = value
    new_config['version'] = CURRENT_VERSION

    target_count = 4 if new_config['mode'] == '4' else 8
    new_config['channels'] = (new_config.get('channels', []) + [1]*8)[:target_count]
    new_config['setpoints'] = (new_config.get('setpoints', []) + [51]*8)[:target_count]

    global config, CHANNEL_COUNT
    config.update(new_config)
    CHANNEL_COUNT = target_count
    save_config()
    init_sacn()
    apply_network_config()
    apply_hostname_config()

    flash("Config restored successfully!", "success")
    return redirect(url_for('main'))

# -------------------------- OTA UPDATE --------------------------
@app.route('/ota', methods=['GET', 'POST'])
def ota_update():
    if not require_auth():
        return redirect(url_for('login', next='/ota'))

    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file uploaded", "danger")
            return redirect(url_for('ota_update'))
        file = request.files['file']
        if file.filename == '' or not file.filename.endswith('.py'):
            flash("Invalid file", "danger")
            return redirect(url_for('ota_update'))

        try:
            content = file.read().decode('utf-8')
            ast.parse(content)
        except Exception as e:
            flash(f"Syntax error: {e}", "danger")
            return redirect(url_for('ota_update'))

        version_match = re.search(r'CURRENT_VERSION\s*=\s*"([^"]+)"', content)
        if not version_match:
            flash("No version found", "danger")
            return redirect(url_for('ota_update'))
        new_version = version_match.group(1)
        if new_version <= CURRENT_VERSION:
            flash(f"Version {new_version} not newer than {CURRENT_VERSION}", "danger")
            return redirect(url_for('ota_update'))

        backup_path = os.path.join(APP_DIR, f"sacn_relay_controller.py.bak.v{CURRENT_VERSION}")
        os.rename(config['py_file'], backup_path)

        with open(config['py_file'], 'w') as f:
            f.write(content)

        flash(f"Updated to v{new_version}! Restarting...", "success")
        threading.Timer(2.0, lambda: subprocess.run(['sudo', 'systemctl', 'restart', 'sacn-relay'])).start()
        return redirect(url_for('ota_update'))

    return render_template('ota.html',
        current_version=CURRENT_VERSION,
        security_enabled=config['security_enabled'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)