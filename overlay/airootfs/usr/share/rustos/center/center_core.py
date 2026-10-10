"""RustOS Center: everything that is not the window (no Qt here, so it can be tested anywhere).
Reads the state of the PC and knows the RustOS tools. The window is rustos_center.py."""
import glob
import os
import re
import shutil
import subprocess

BIN = '/usr/local/bin'
SHARE = '/usr/share/rustos'
CATALOG = os.environ.get('RUSTOS_APPS_CATALOG', SHARE + '/apps.catalog')
CHANGELOG = SHARE + '/CHANGELOG.txt'
EQUIV = SHARE + '/windows-equivalents.txt'
PERF_CONF = '/etc/rustos/performance.conf'
UPDATE_LOG = '/var/log/rustos-update.log'
HOLD = '/var/lib/rustos/update-hold'
HOME = os.path.expanduser('~')
DATA = os.environ.get('XDG_DATA_HOME') or os.path.join(HOME, '.local/share')
APPS_DIR = os.path.join(DATA, 'applications')
Q_USER = os.path.join(DATA, 'rustos-quarantine')
Q_ROOT = '/var/lib/rustos/quarantine'
MODDIR = os.path.join(os.environ.get('XDG_CONFIG_HOME') or os.path.join(HOME, '.config'), 'rustos/mods')
ARCH = os.uname().machine
IS_PC = ARCH == 'x86_64'
ANSI = re.compile(r'\x1b\[[0-9;?]*[A-Za-z]')


def sh(argv, timeout=20, env=None):
    """Run a command, return (exit code, output). Never raises."""
    try:
        e = dict(os.environ, NO_COLOR='1')
        if env:
            e.update(env)
        p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, env=e)
        return p.returncode, p.stdout.decode('utf-8', 'replace')
    except (OSError, subprocess.SubprocessError):
        return 127, ''


def have(cmd):
    return shutil.which(cmd) is not None


def tool(name):
    """Full path of a RustOS tool (falls back to PATH, handy for testing)."""
    p = os.path.join(BIN, name)
    return p if os.path.exists(p) else (shutil.which(name) or p)


def clean(text):
    """Remove colors and progress-bar overwrites (\\r) from tool output."""
    out = []
    for line in ANSI.sub('', text).split('\n'):
        if '\r' in line:
            parts = [x for x in line.split('\r') if x.strip()]
            line = parts[-1] if parts else ''
        out.append(line)
    return '\n'.join(out)


def read(path, default=''):
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            return f.read()
    except OSError:
        return default


def is_live():
    return os.path.isdir('/run/archiso')


# ------------------------------------------------------------------ version and updates
def rustos_version():
    rc, out = sh(['pacman', '-Q', 'rustos-base'], 5)
    if rc == 0 and out.split():
        v = out.split()[-1].rsplit('-', 1)[0]          # 3.0.202610081200-1 -> 3.0.202610081200
        parts = v.split('.')
        if len(parts) >= 3 and len(parts[-1]) >= 8:
            v = '.'.join(parts[:-1])                    # drop the build time stamp
        return v
    m = re.search(r'^== RustOS (\S+) ==', read(CHANGELOG), re.M)
    return m.group(1) if m else '?'


def channel():
    """'stable', 'beta' or 'none' (from the [rustos] Server line)."""
    sect = False
    for line in read('/etc/pacman.conf').splitlines():
        s = line.strip()
        if s.startswith('['):
            sect = s == '[rustos]'
            continue
        if sect and s.startswith('Server'):
            return 'beta' if '/beta/' in s else 'stable'
    return 'none'


def autoupdate_on():
    return sh(['systemctl', 'is-enabled', '--quiet', 'rustos-update.timer'], 5)[0] == 0


def update_hold_until():
    """Unix time automatic updates are paused until, or 0."""
    import time
    try:
        t = int(read(HOLD).strip() or 0)
    except ValueError:
        return 0
    return t if t > time.time() else 0


def last_update():
    lines = [x for x in read(UPDATE_LOG).splitlines() if x.startswith('===')]
    return lines[-1].strip('= ').strip() if lines else ''


def parse_checkupdates(text):
    """'name old -> new' lines -> [(name, old, new)]"""
    out = []
    for line in clean(text).splitlines():
        m = re.match(r'^(\S+)\s+(\S+)\s+->\s+(\S+)', line.strip())
        if m:
            out.append(m.groups())
    return out


def changelog_versions(text=None):
    """[(version, body)] newest first, from CHANGELOG.txt"""
    text = read(CHANGELOG) if text is None else text
    out, cur, body = [], None, []
    for line in text.splitlines():
        m = re.match(r'^== RustOS (\S+) ==', line)
        if m:
            if cur:
                out.append((cur, '\n'.join(body).strip()))
            cur, body = m.group(1), []
        elif cur:
            body.append(line)
    if cur:
        out.append((cur, '\n'.join(body).strip()))
    return out


# ------------------------------------------------------------------ apps catalog
def catalog(path=CATALOG):
    apps = []
    for line in read(path).splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        f = line.split('|')
        if len(f) < 7:
            continue
        flags = [x.strip() for x in f[6].split(',') if x.strip() and x.strip() != '-']
        if 'x86' in flags and not IS_PC:
            continue
        apps.append({'cat': f[0], 'id': f[1], 'label': f[2],
                     'pkgs': [] if f[3].strip() == '-' else f[3].split(),
                     'flatpaks': [] if f[4].strip() == '-' else f[4].split(),
                     'flags': flags})
    return apps


def split_label(label):
    """'VLC: plays almost everything' -> ('VLC', 'plays almost everything')"""
    if ': ' in label:
        a, b = label.split(': ', 1)
        return a, b[:1].upper() + b[1:]
    return label, ''


def installed_packages():
    rc, out = sh(['pacman', '-Qq'], 15)
    return set(out.split()) if rc == 0 else set()


def installed_flatpaks():
    if not have('flatpak'):
        return set()
    rc, out = sh(['flatpak', 'list', '--app', '--columns=application'], 15)
    return set(out.split()) if rc == 0 else set()


def app_installed(app, pkgs, flats):
    """True / False, or None when it cannot be told (special entries)."""
    if app['id'] == 'windows':
        return have('wine')
    if 'ui' in app['flags']:
        return None
    if app['pkgs']:
        return app['pkgs'][0] in pkgs
    if app['flatpaks']:
        return app['flatpaks'][0] in flats
    return None


# ------------------------------------------------------------------ power, battery, performance
PERF_DEFAULTS = {'MODE': 'auto', 'AC_PROFILE': 'performance', 'BAT_PROFILE': 'power-saver', 'BAT_TURBO': '1',
                 'BAT_FPS_CAP': '60', 'AC_FPS_CAP': '0', 'GAME_BOOST': '1', 'LATENCY_TWEAKS': '1',
                 'SHOW_FPS': '0', 'CHARGE_LIMIT': '0'}


def perf_conf(path=PERF_CONF):
    c = dict(PERF_DEFAULTS)
    for line in read(path).splitlines():
        line = line.split('#', 1)[0].strip()
        if '=' in line:
            k, v = line.split('=', 1)
            k, v = k.strip(), v.strip().strip('"\'')
            if k in c:
                c[k] = v
    return c


def perf_changes(old, new):
    """KEY=VALUE strings for what differs (for rustos-performance setmany)."""
    return ['%s=%s' % (k, new[k]) for k in sorted(new) if str(new[k]) != str(old.get(k, ''))]


PS = '/sys/class/power_supply'


def _num(path):
    try:
        return int(read(path).strip())
    except ValueError:
        return None


def batteries(base=PS):
    out = []
    for d in sorted(glob.glob(base + '/*')):
        if read(d + '/type').strip() != 'Battery':
            continue
        if read(d + '/scope').strip() == 'Device':       # mouse or headset battery
            continue
        b = {'name': os.path.basename(d), 'capacity': _num(d + '/capacity'),
             'status': read(d + '/status').strip() or 'Unknown',
             'limit_supported': os.path.exists(d + '/charge_control_end_threshold'),
             'limit': _num(d + '/charge_control_end_threshold')}
        # power in W and energy in Wh (some laptops only give current/charge: convert with the voltage)
        p, e, full = _num(d + '/power_now'), _num(d + '/energy_now'), _num(d + '/energy_full')
        if p is None:
            cur, volt = _num(d + '/current_now'), _num(d + '/voltage_now')
            if cur is not None and volt:
                p = cur * volt // 1000000
                ch, chf = _num(d + '/charge_now'), _num(d + '/charge_full')
                e = ch * volt // 1000000 if ch is not None else None
                full = chf * volt // 1000000 if chf is not None else None
        b['watts'] = (p or 0) / 1e6
        b['wh'] = (e or 0) / 1e6
        b['wh_full'] = (full or 0) / 1e6
        design = _num(d + '/energy_full_design') or _num(d + '/charge_full_design')
        now_full = _num(d + '/energy_full') or _num(d + '/charge_full')
        b['health'] = round(100 * now_full / design) if design and now_full else None
        out.append(b)
    return out


def on_battery(base=PS):
    anybat = ac = False
    for d in glob.glob(base + '/*'):
        t = read(d + '/type').strip()
        if t == 'Battery' and read(d + '/scope').strip() != 'Device':
            anybat = True
        elif t in ('Mains', 'USB', 'USB_C', 'USB_PD') and read(d + '/online').strip() == '1':
            ac = True
    return anybat and not ac


def time_left(bats):
    """'3 h 20 min' to empty (on battery) or to full (charging), or ''."""
    w = sum(b['watts'] for b in bats)
    if w < 0.5:
        return ''
    if all(b['status'] == 'Discharging' for b in bats):
        h = sum(b['wh'] for b in bats) / w
    elif any(b['status'] == 'Charging' for b in bats):
        h = sum(max(b['wh_full'] - b['wh'], 0) for b in bats) / w
    else:
        return ''
    if h <= 0 or h > 48:
        return ''
    return '%d h %02d min' % (int(h), int(round((h - int(h)) * 60)) % 60)


def power_profile():
    rc, out = sh(['powerprofilesctl', 'get'], 4)
    return out.strip() if rc == 0 and out.strip() else 'unknown'


def turbo_state():
    p = '/sys/devices/system/cpu/intel_pstate/no_turbo'
    if os.path.exists(p):
        return 'on' if read(p).strip() == '0' else 'off'
    p = '/sys/devices/system/cpu/cpufreq/boost'
    if os.path.exists(p):
        return 'on' if read(p).strip() == '1' else 'off'
    f = sorted(glob.glob('/sys/devices/system/cpu/cpufreq/policy*/boost'))
    if f:
        return 'on' if read(f[0]).strip() == '1' else 'off'
    return 'not supported'


def cpu_temp():
    """Hottest CPU-ish temperature in C, or None."""
    best = None
    for z in glob.glob('/sys/class/hwmon/hwmon*'):
        name = read(z + '/name').strip()
        if name not in ('coretemp', 'k10temp', 'zenpower', 'cpu_thermal', 'acpitz'):
            continue
        for t in glob.glob(z + '/temp*_input'):
            v = _num(t)
            if v and 0 < v < 130000:
                best = max(best or 0, v // 1000)
    return best


def kernel_info():
    rel = os.uname().release
    zen = sh(['pacman', '-Q', 'linux-zen'], 5)[0] == 0
    lts = sh(['pacman', '-Q', 'linux-lts'], 5)[0] == 0
    base = read('/usr/lib/modules/%s/pkgbase' % rel).strip()
    return {'running': rel, 'pkgbase': base or '?', 'zen_running': base == 'linux-zen' or (not base and 'zen' in rel),
            'zen_installed': zen, 'lts_running': base == 'linux-lts' or (not base and rel.endswith('-lts')),
            'lts_installed': lts, 'headers': os.path.isdir('/usr/lib/modules/%s/build' % rel),
            'dkms': have('dkms')}


def gpus():
    rc, out = sh(['lspci', '-nn'], 5)
    lines = [x for x in out.splitlines() if re.search(r'vga|3d controller|display controller', x, re.I)]
    names = []
    for x in lines:
        n = re.sub(r'^\S+\s+', '', x)
        n = re.sub(r'\[[0-9a-f]{4}:[0-9a-f]{4}\]', '', n)
        n = re.sub(r'\(rev [0-9a-f]+\)', '', n).strip()
        names.append(n[:90])
    text = '\n'.join(lines)
    return {'names': names, 'nvidia': '[10de:' in text, 'amd': '[1002:' in text, 'intel': '[8086:' in text}


def gaming_installed():
    return read('/var/lib/rustos/gaming-installed').split()


def virt():
    rc, out = sh(['systemd-detect-virt'], 3)
    v = out.strip()
    return '' if v in ('', 'none') else v


# ------------------------------------------------------------------ antivirus
def clam_ready():
    return have('clamscan') and bool(glob.glob('/var/lib/clamav/*.c[vl]d'))


def clam_db_date():
    import time
    f = glob.glob('/var/lib/clamav/*.c[vl]d')
    if not f:
        return 'not installed yet'
    return time.strftime('%a %d %b %Y', time.localtime(max(os.path.getmtime(x) for x in f)))


SCAN_EXCLUDES = ['--exclude-dir=/rustos-quarantine', '--exclude-dir=^/(proc|sys|dev|run)(/|$)', '--exclude-dir=^/var/lib/clamav']


def scan_argv(paths):
    # every file is printed ("path: OK"), so the window can show the progress
    return ['clamscan', '-r'] + SCAN_EXCLUDES + list(paths)


def parse_found(line):
    """'/path/file: Win.Trojan.X FOUND' -> ('/path/file', 'Win.Trojan.X') or None"""
    m = re.match(r'^(.*): (\S+) FOUND$', line.strip())
    return m.groups() if m else None


def user_dirs():
    out = []
    for k in ('DOWNLOAD', 'DESKTOP', 'DOCUMENTS'):
        rc, d = sh(['xdg-user-dir', k], 3)
        d = d.strip()
        if rc == 0 and d and d != HOME and os.path.isdir(d):
            out.append(d)
    return out or [HOME]


def quarantine_user(files):
    """Move files into the user quarantine and lock them. Returns how many."""
    os.makedirs(Q_USER, exist_ok=True)
    os.chmod(Q_USER, 0o700)
    n = 0
    for f in files:
        if not os.path.isfile(f):
            continue
        dest = os.path.join(Q_USER, os.path.basename(f))
        i = 1
        while os.path.exists(dest):
            dest = os.path.join(Q_USER, '%s.~%d~' % (os.path.basename(f), i))
            i += 1
        try:
            shutil.move(f, dest)
            os.chmod(dest, 0)
            n += 1
        except OSError:
            pass
    return n


# ------------------------------------------------------------------ education
EDU = [
    # id, name, what, kind ('prog' = installed program, 'web' = menu shortcut), url, icon
    ('pdf', 'Okular', 'PDF reader with notes', 'prog', '', 'okular'),
    ('pdfedit', 'PDF tools', 'Xournal++ (write on PDFs, sign) and PDF Arranger (merge, split)', 'prog', '', 'xournalpp'),
    ('books', 'Calibre', 'E-books', 'prog', '', 'calibre-gui'),
    ('anki', 'Anki', 'Flashcards', 'prog', '', 'anki'),
    ('zotero', 'Zotero', 'Research and references', 'prog', '', 'zotero'),
    ('obsidian', 'Obsidian', 'Notes', 'prog', '', 'obsidian'),
    ('scratch', 'Scratch', 'Learn coding', 'prog', '', 'scratch'),
    ('geogebra', 'GeoGebra', 'Maths', 'prog', '', 'geogebra'),
    ('stars', 'Stellarium', 'Astronomy', 'prog', '', 'stellarium'),
    ('zoom', 'Zoom', 'Video lessons and meetings', 'prog', '', 'Zoom'),
    ('canva', 'Canva', 'Design (website: Canva has no Linux program)', 'web', 'https://www.canva.com', 'applications-graphics'),
    ('gdocs', 'Google Docs', 'Docs, Sheets and Slides', 'web', 'https://docs.google.com', 'x-office-document'),
    ('classroom', 'Google Classroom', 'School classes', 'web', 'https://classroom.google.com', 'applications-education'),
    ('m365', 'Microsoft 365 (online)', 'Word, Excel, PowerPoint in the browser', 'web', 'https://www.office.com', 'x-office-document'),
    ('khan', 'Khan Academy', 'Free lessons', 'web', 'https://www.khanacademy.org', 'applications-education'),
    ('duolingo', 'Duolingo', 'Learn languages', 'web', 'https://www.duolingo.com', 'applications-education'),
]
EDU_CHECK = {'pdf': ('pkg', 'okular'), 'pdfedit': ('pkg', 'xournalpp'), 'books': ('pkg', 'calibre'),
             'stars': ('pkg', 'stellarium'), 'anki': ('fp', 'net.ankiweb.Anki'), 'zotero': ('fp', 'org.zotero.Zotero'),
             'obsidian': ('fp', 'md.obsidian.Obsidian'), 'scratch': ('fp', 'edu.mit.Scratch'),
             'geogebra': ('fp', 'org.geogebra.GeoGebra'), 'zoom': ('fp', 'us.zoom.Zoom')}


def webapp_path(eid):
    return os.path.join(APPS_DIR, 'rustos-web-%s.desktop' % eid)


def edu_installed(item, pkgs, flats):
    eid, kind = item[0], item[3]
    if kind == 'web':
        return os.path.exists(webapp_path(eid))
    how = EDU_CHECK.get(eid)
    if not how:
        return False
    return how[1] in (pkgs if how[0] == 'pkg' else flats)


def write_webapp(item):
    eid, name, _what, _kind, url, icon = item
    os.makedirs(APPS_DIR, exist_ok=True)
    browser = 'firefox --new-window' if have('firefox') else 'xdg-open'
    with open(webapp_path(eid), 'w') as f:
        f.write('[Desktop Entry]\nType=Application\nName=%s\nComment=%s (opens in the browser)\nExec=%s %s\n'
                'Icon=%s\nTerminal=false\nCategories=Education;Network;\n' % (name, name, browser, url, icon))


def remove_webapp(eid):
    try:
        os.remove(webapp_path(eid))
    except OSError:
        pass


# ------------------------------------------------------------------ look, mods, fixes
def kread(group, key, file='kdeglobals'):
    for k in ('kreadconfig6', 'kreadconfig5'):
        if have(k):
            return sh([k, '--file', file, '--group', group, '--key', key], 4)[1].strip()
    return ''


def look_state():
    return {'dark': kread('General', 'ColorScheme') == 'BreezeDark',
            'accent': kread('General', 'AccentColor'),
            'noanim': kread('KDE', 'AnimationDurationFactor') == '0'}


def bootsplash_on():
    rc, out = sh([tool('rustos-bootsplash'), 'status'], 6)
    return ': ON' in out


def parse_mods(text):
    """'[ON ] name   desc' / '[off] name desc' lines from 'rustos-debug mods' -> [(name, on, desc)]"""
    out = []
    for line in clean(text).splitlines():
        m = re.match(r'^\s*\[(ON |off)\]\s+(\S+)\s*(.*)$', line)
        if m:
            out.append((m.group(2), m.group(1) == 'ON ', m.group(3).strip()))
    return out


# mods that change the whole PC: run as root (one password) instead of through sudo in a terminal
ROOT_MODS = {
    'autoupdate': {'on': [BIN + '/rustos-autoupdate', 'on'], 'off': [BIN + '/rustos-autoupdate', 'off']},
    'bootsplash': {'on': [BIN + '/rustos-bootsplash', 'on'], 'off': [BIN + '/rustos-bootsplash', 'off']},
    'beta': {'on': [BIN + '/rustos-channel', 'beta'], 'off': [BIN + '/rustos-channel', 'stable']},
    'devtools': {'on': ['/usr/bin/pacman', '-S', '--needed', '--noconfirm', 'base-devel', 'git'], 'off': None},
}

# id, button text, what it is for, needs root
FIXES = [
    ('plasma', 'Restart the desktop', 'The panel or desktop froze or vanished', False),
    ('audio', 'Fix sound', 'No sound: restart the sound system', False),
    ('network', 'Fix the network', 'Wi-Fi or cable stuck: restart NetworkManager', True),
    ('dns', 'Fix websites', 'Websites do not open but the network is up', True),
    ('pacman-lock', 'Unlock updates', '"unable to lock database"', True),
    ('keyring', 'Refresh package keys', '"signature is invalid / unknown trust"', True),
    ('time', 'Fix the clock', 'The time is wrong', True),
    ('flatpak', 'Repair Flatpak apps', 'Flatpak apps broken', True),
    ('fonts', 'Rebuild fonts', 'Letters look wrong or are missing', False),
    ('icons', 'Rebuild menu icons', 'Icons missing in the menu', False),
    ('ipad', 'Leave iPad mode', 'Stuck in iPad mode: normal desktop back', False),
    ('mirrors', 'Faster downloads', 'Pick the fastest package servers', True),
    ('initramfs', 'Rebuild start-up files', 'After a driver problem', True),
    ('grub', 'Rebuild boot menu', 'Windows missing from the GRUB menu', True),
    ('bootsplash', 'Boot screen off', 'The boot screen causes trouble', True),
    ('exe', 'Repair the app windows', 'The EXE Center or RustOS Center window does not open', True),
]


def selftest_summary(text):
    """(passed, warnings, failed) from 'rustos-debug selftest' output, or None"""
    m = re.search(r'(\d+) passed,\s*(\d+) warnings?,\s*(\d+) failed', clean(text))
    return tuple(int(x) for x in m.groups()) if m else None


# ------------------------------------------------------------------ hardware development (rustos-devhw)
FPGA_TOOLS = [
    # catalog id, command, what it is, note
    ('yosys', 'yosys', 'Verilog synthesis', 'Open source. Targets iCE40, ECP5, Gowin and more with nextpnr.'),
    ('iverilog', 'iverilog', 'Verilog simulator', 'Open source. Good for testbenches.'),
    ('verilator', 'verilator', 'Fast Verilog / SystemVerilog simulator', 'Open source. Compiles the design to C++.'),
    ('gtkwave', 'gtkwave', 'Waveform viewer', 'Opens the .vcd / .fst files the simulators write.'),
    ('openfpgaloader', 'openFPGALoader', 'Programs FPGA boards', 'Open source. Over FTDI, CMSIS-DAP, Digilent and more.'),
]
DEVHW_STATUSES = ('supported', 'unavailable', 'untested', 'info')


def parse_devhw(text):
    """'rustos-devhw check --machine' -> {'checks': [...], 'pci': [...], 'usb': [...], 'summary': (s, u, t) or None}"""
    out = {'checks': [], 'pci': [], 'usb': [], 'summary': None}
    for line in clean(text).splitlines():
        f = line.split('\t')
        if f[0] == 'CHECK' and len(f) >= 4 and f[2] in DEVHW_STATUSES:
            out['checks'].append({'item': f[1], 'status': f[2], 'text': f[3], 'fix': f[4] if len(f) > 4 else ''})
        elif f[0] == 'PCI' and len(f) >= 11:
            out['pci'].append({'slot': f[1], 'ids': f[2], 'class': f[3], 'driver': '' if f[4] == '-' else f[4],
                               'modules': '' if f[5] == '-' else f[5], 'group': '' if f[6] == '-' else f[6],
                               'vfio': f[7], 'why': f[8], 'name': f[9], 'kept': f[10] == 'yes'})
        elif f[0] == 'USB' and len(f) >= 4:
            out['usb'].append({'ids': f[1], 'name': f[2], 'access': f[3]})
        elif f[0] == 'SUMMARY' and len(f) >= 4:
            try:
                out['summary'] = (int(f[1]), int(f[2]), int(f[3]))
            except ValueError:
                pass
    return out


def devhw_check(out, item):
    """status of one item from parse_devhw, or ''"""
    for c in out['checks']:
        if c['item'] == item:
            return c['status']
    return ''


def cpu_vendor():
    t = read('/proc/cpuinfo')
    return 'intel' if 'GenuineIntel' in t else 'amd' if 'AuthenticAMD' in t else 'other'


# ------------------------------------------------------------------ switching from Windows
def ntfs_drives():
    rc, out = sh(['lsblk', '-rnpo', 'NAME,FSTYPE,LABEL,SIZE,MOUNTPOINT'], 5)
    drives = []
    for line in out.splitlines():
        f = line.split(' ')
        if len(f) >= 2 and f[1] == 'ntfs':
            label = f[2].replace('\\x20', ' ') if len(f) > 2 and f[2] else 'Windows drive'
            drives.append({'dev': f[0], 'label': label, 'size': f[3] if len(f) > 3 else '',
                           'mount': f[4].replace('\\x20', ' ') if len(f) > 4 else ''})
    return drives


def mount_drive(dev):
    """(ok, mount point or error text)"""
    rc, out = sh(['udisksctl', 'mount', '-b', dev], 30)
    if rc != 0:
        return False, out.strip()
    m = re.search(r' at (.*?)\.?$', out.strip())
    return True, m.group(1) if m else ''


def wine_ready():
    return have('wine')


def selftest():
    """Quick check of the parts above (python3 center_core.py)."""
    assert parse_checkupdates('firefox 1.0-1 -> 1.1-1\nrustos-base 2.11.1-1 -> 3.0.2-1\n')[1][0] == 'rustos-base'
    assert parse_mods('  [ON ] dark        Dark theme\n  [off] noanim      No animations\n') == \
        [('dark', True, 'Dark theme'), ('noanim', False, 'No animations')]
    assert parse_found('/home/a/x.exe: Win.Test.EICAR_HDB-1 FOUND') == ('/home/a/x.exe', 'Win.Test.EICAR_HDB-1')
    assert parse_found('/home/a/x.exe: OK') is None
    assert selftest_summary('\x1b[1m23 passed, 4 warnings, 0 failed\x1b[0m') == (23, 4, 0)
    assert perf_changes({'MODE': 'auto', 'X': '1'}, {'MODE': 'battery', 'X': '1'}) == ['MODE=battery']
    assert split_label('VLC: plays almost everything') == ('VLC', 'Plays almost everything')
    assert clean('a\rb\r\n\x1b[31mred\x1b[0m') == 'b\nred'
    v = changelog_versions('== RustOS 3.0 ==\n- a\n\n== RustOS 2.11 ==\n- b\n')
    assert v == [('3.0', '- a'), ('2.11', '- b')]
    d = parse_devhw('CHECK\tIOMMU\tunavailable\tnot active\tTurn on VT-d\n'
                    'PCI\t0000:03:00.0\t10ee:7024\t0580\t-\t-\t14\tyes\t\tXilinx Device\tno\n'
                    'USB\t0403:6010\tFTDI FT2232\tyes\nSUMMARY\t3\t2\t1\n')
    assert d['checks'][0]['fix'] == 'Turn on VT-d' and d['pci'][0]['group'] == '14' and d['pci'][0]['driver'] == ''
    assert d['usb'][0]['access'] == 'yes' and d['summary'] == (3, 2, 1) and devhw_check(d, 'IOMMU') == 'unavailable'
    print('center_core: all checks passed')


if __name__ == '__main__':
    selftest()
