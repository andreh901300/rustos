"""RustOS EXE Center: everything that is not the window (finding programs, sorting files, DLLs, icons, settings).
Kept free of Qt so it can be tested on its own:  python3 exe_core.py selftest"""
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import tempfile

HOME = os.path.expanduser('~')
ROOT = os.environ.get('RUSTOS_EXE_HOME', os.path.join(HOME, 'EXE-Center'))
SETUPS = os.path.join(ROOT, 'Setups')
RUNTIMES = os.path.join(ROOT, 'Runtimes')
DLLS = os.path.join(ROOT, 'DLLs')
PROGS = os.path.join(ROOT, 'Programs')
FOLDERS = {'Setups': SETUPS, 'Runtimes': RUNTIMES, 'DLLs': DLLS, 'Programs': PROGS}
PREFIX = os.environ.get('WINEPREFIX', os.path.join(HOME, '.wine'))
DATA = os.environ.get('XDG_DATA_HOME', os.path.join(HOME, '.local', 'share'))
WINEMENU = os.path.join(DATA, 'applications', 'wine')
CONFIG = os.path.join(os.environ.get('XDG_CONFIG_HOME', os.path.join(HOME, '.config')), 'rustos', 'exe-center.json')
CACHE = os.path.join(os.environ.get('XDG_CACHE_HOME', os.path.join(HOME, '.cache')), 'rustos-exe-center')
RUN = os.environ.get('RUSTOS_RUN_EXE', '/usr/local/bin/rustos-run-exe')

README = """RustOS EXE Center folder
========================
Put your Windows files here, or drag them onto the RustOS EXE Center window.

  Setups    installers, like "cs1.6 setup.exe" or "game-setup.msi"
  Runtimes  .NET, Visual C++ and DirectX installers
  DLLs      extra .dll files a program asks for
  Programs  portable programs and games you just run (a whole game folder works too)
"""

RUNNABLE = ('.exe', '.bat', '.lnk', '.msi', '.cmd')
# files in a game folder that are not the game itself
NOT_A_PROGRAM = re.compile(r'(unins\d*|uninstall|setup|install|crashreport|crashhandler|vcredist|vc_redist|dxsetup|'
                           r'directx|dotnet|ue4prereq|easyanticheat|battleye|be_service|updater|redist|helper|'
                           r'launcherpatcher|notification|dxwebsetup|oalinst|physx)', re.I)
CORE_DLLS = {'kernel32', 'kernelbase', 'ntdll', 'user32', 'gdi32', 'advapi32', 'win32u', 'ucrtbase', 'msvcrt',
             'shell32', 'ole32', 'combase', 'rpcrt4', 'ws2_32', 'wow64', 'wow64cpu', 'wow64win'}

# one-click downloads (winetricks verbs)
EXTRAS = [
    ('vcrun2022', 'Visual C++ 2015-2022', 'Many programs and games need this', True),
    ('dxvk', 'DXVK', 'Faster DirectX 9, 10 and 11 games (uses Vulkan)', False),
    ('vkd3d', 'VKD3D-Proton', 'DirectX 12 games (uses Vulkan)', False),
    ('d3dx9', 'DirectX 9 extras', 'Older games ask for d3dx9_xx.dll', False),
    ('d3dcompiler_47', 'DirectX shader compiler', 'Some newer programs ask for it', False),
    ('corefonts', 'Windows fonts', 'Arial, Times New Roman, Verdana...', False),
    ('dotnet48', '.NET Framework 4.8', 'Slow to install and may fail. Wine Mono already runs many .NET programs', False),
    ('xna40', 'XNA 4.0', 'Some indie games made with XNA', False),
    ('physx', 'PhysX', 'Some older games with NVIDIA physics', False),
]


def make_folders():
    for d in FOLDERS.values():
        os.makedirs(d, exist_ok=True)
    rd = os.path.join(ROOT, 'README.txt')
    if not os.path.exists(rd):
        with open(rd, 'w') as f:
            f.write(README)


def classify(name):
    b = os.path.basename(name).lower()
    if b.endswith(('.dll', '.ocx')):
        return 'DLLs'
    if re.search(r'dotnet|ndp\d|windowsdesktop-runtime|aspnetcore|netfx|vcredist|vc_redist|vcruntime|directx|dxsetup|'
                 r'xnafx|oalinst', b):
        return 'Runtimes'
    if re.search(r'setup|install', b) or b.endswith('.msi'):
        return 'Setups'
    return 'Programs'


def unique_path(folder, name):
    dest = os.path.join(folder, name)
    if not os.path.exists(dest):
        return dest
    stem, ext = os.path.splitext(name)
    n = 2
    while os.path.exists(os.path.join(folder, f'{stem} ({n}){ext}')):
        n += 1
    return os.path.join(folder, f'{stem} ({n}){ext}')


def add_paths(paths):
    """Copy files (sorted by kind) and folders (into Programs). Returns [(name, folder name)]."""
    make_folders()
    done = []
    for p in paths:
        p = os.path.abspath(p)
        if os.path.isdir(p):
            dest = unique_path(PROGS, os.path.basename(p.rstrip('/')))
            shutil.copytree(p, dest, symlinks=True)
            done.append((os.path.basename(dest), 'Programs'))
        elif os.path.isfile(p):
            kind = classify(p)
            dest = unique_path(FOLDERS[kind], os.path.basename(p))
            shutil.copy2(p, dest)
            done.append((os.path.basename(dest), kind))
    return done


def files_in(folder, exts, depth=3):
    out = []
    base = folder.rstrip('/')
    for top, dirs, files in os.walk(base):
        if top[len(base):].count(os.sep) >= depth:
            dirs[:] = []
        dirs.sort()
        for f in sorted(files):
            if f.lower().endswith(exts):
                out.append(os.path.join(top, f))
    return out


def pe_bits(path):
    """32 or 64 from the Windows file header, 0 if unknown."""
    try:
        with open(path, 'rb') as f:
            if f.read(2) != b'MZ':
                return 0
            f.seek(60)
            off = struct.unpack('<I', f.read(4))[0]
            f.seek(off)
            if f.read(4) != b'PE\0\0':
                return 0
            mach = struct.unpack('<H', f.read(2))[0]
            return {0x14c: 32, 0x8664: 64, 0xaa64: 64}.get(mach, 0)
    except (OSError, struct.error):
        return 0


def human_size(n):
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024 or unit == 'GB':
            return f'{n:.0f} {unit}' if unit == 'B' else f'{n:.1f} {unit}'
        n /= 1024


# ------------------------------------------------------------------ settings
def load_config():
    try:
        with open(CONFIG) as f:
            c = json.load(f)
        if isinstance(c, dict):
            c.setdefault('programs', {})
            c.setdefault('extra', [])
            c.setdefault('hidden', [])
            return c
    except (OSError, ValueError):
        pass
    return {'programs': {}, 'extra': [], 'hidden': [], 'show_log': False}


def save_config(c):
    os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
    tmp = CONFIG + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(c, f, indent=1)
    os.replace(tmp, CONFIG)


# ------------------------------------------------------------------ the library
class Program:
    def __init__(self, key, name, kind, path=None, exec_line=None, icon=None, folder=None):
        self.key = key            # stable id: file path, or the .desktop file
        self.name = name
        self.kind = kind          # 'portable' | 'installed' | 'added'
        self.path = path          # .exe for portable/added
        self.exec_line = exec_line  # Exec= for installed (wine menu)
        self.icon = icon          # png path or theme icon name
        self.folder = folder

    def __repr__(self):
        return f'Program({self.name!r}, {self.kind})'


def nice_name(path):
    stem = os.path.splitext(os.path.basename(path))[0]
    parent = os.path.basename(os.path.dirname(path))
    # "Game/bin/game.exe" -> "Game"; "Programs/tool.exe" -> "tool"
    if parent and parent not in ('Programs', 'bin', 'Bin', 'x64', 'x86', 'win64', 'win32', 'Binaries', 'Win64'):
        if stem.lower() in parent.lower().replace(' ', '') or len(stem) <= 3 or stem.lower() in ('game', 'launcher', 'start', 'play'):
            return parent
    return stem.replace('_', ' ')


def desktop_value(text, key):
    m = re.search(rf'^{key}=(.*)$', text, re.M)
    return m.group(1).strip() if m else ''


def find_icon_file(name):
    if not name:
        return None
    if os.path.isabs(name) and os.path.exists(name):
        return name
    for size in ('256x256', '128x128', '64x64', '48x48', '32x32'):
        p = os.path.join(DATA, 'icons', 'hicolor', size, 'apps', name + '.png')
        if os.path.exists(p):
            return p
    return None


def scan_library(cfg=None):
    cfg = cfg or load_config()
    hidden = set(cfg.get('hidden', []))
    progs = []
    # installed with a setup: Wine puts menu entries here
    if os.path.isdir(WINEMENU):
        for top, _, files in os.walk(WINEMENU):
            for f in sorted(files):
                if not f.endswith('.desktop'):
                    continue
                p = os.path.join(top, f)
                try:
                    text = open(p, errors='replace').read()
                except OSError:
                    continue
                name = desktop_value(text, 'Name')
                if not name or re.search(r'uninstall|readme|manual|help|website|wine', name, re.I):
                    continue
                if p in hidden:
                    continue
                progs.append(Program(p, name, 'installed', exec_line=desktop_value(text, 'Exec'),
                                     icon=find_icon_file(desktop_value(text, 'Icon')), folder=desktop_value(text, 'Path') or None))
    # portable programs and game folders
    if os.path.isdir(PROGS):
        for p in files_in(PROGS, ('.exe', '.bat', '.lnk'), depth=4):
            b = os.path.basename(p)
            if NOT_A_PROGRAM.search(b) or p in hidden:
                continue
            progs.append(Program(p, nice_name(p), 'portable', path=p, folder=os.path.dirname(p)))
    # added by hand from anywhere
    for p in cfg.get('extra', []):
        if os.path.exists(p) and p not in hidden:
            progs.append(Program(p, nice_name(p), 'added', path=p, folder=os.path.dirname(p)))
    # custom names from the settings
    for pr in progs:
        s = cfg['programs'].get(pr.key, {})
        if s.get('name'):
            pr.name = s['name']
    # favourites first, then by name
    progs.sort(key=lambda x: (not cfg['programs'].get(x.key, {}).get('fav', False), x.name.lower()))
    return progs


# ------------------------------------------------------------------ icons from .exe files (needs icoutils)
def exe_icon(path):
    """A PNG of the program's own icon, cached. None when it cannot be read."""
    if not path or not path.lower().endswith('.exe') or not shutil.which('wrestool') or not shutil.which('icotool'):
        return None
    try:
        st = os.stat(path)
    except OSError:
        return None
    key = hashlib.sha1(f'{path}:{st.st_mtime}:{st.st_size}'.encode()).hexdigest()
    out = os.path.join(CACHE, 'icons', key + '.png')
    if os.path.exists(out):
        return out if os.path.getsize(out) > 0 else None
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        try:
            subprocess.run(['wrestool', '-x', '-t', '14', '-o', td, path], capture_output=True, timeout=20)
            icos = sorted((os.path.join(td, f) for f in os.listdir(td)), key=os.path.getsize, reverse=True)
            if icos:
                pd = os.path.join(td, 'png')
                os.makedirs(pd)
                subprocess.run(['icotool', '-x', '-o', pd, icos[0]], capture_output=True, timeout=20)
                pngs = [os.path.join(pd, f) for f in os.listdir(pd) if f.endswith('.png')]

                def size_of(f):
                    m = re.search(r'_(\d+)x(\d+)x(\d+)\.png$', f)
                    return (int(m.group(1)), int(m.group(3))) if m else (0, 0)
                if pngs:
                    shutil.copy(max(pngs, key=size_of), out)
                    return out
        except (OSError, subprocess.SubprocessError):
            pass
    open(out, 'w').close()        # remember that there is no icon
    return None


# ------------------------------------------------------------------ Wine
def wine_version():
    if not shutil.which('wine'):
        return None
    try:
        return subprocess.run(['wine', '--version'], capture_output=True, text=True, timeout=10).stdout.strip() or 'wine'
    except (OSError, subprocess.SubprocessError):
        return 'wine'


def running_programs():
    """Windows programs running now: [(pid, name)]."""
    out = []
    try:
        ps = subprocess.run(['ps', '-u', str(os.getuid()), '-o', 'pid=,args='], capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return out
    for line in ps.splitlines():
        line = line.strip()
        pid, _, args = line.partition(' ')
        # Wine shows the Windows program path as the first word of its command line
        m = re.match(r'^(?:[A-Za-z]:\\.*?|/\S*?)([^\\/]+\.exe)(?:\s|$)', args, re.I)
        if not m:
            continue
        name = m.group(1)
        if re.match(r'(wineserver|services|winedevice|explorer|plugplay|svchost|rpcss|conhost|start|winemenubuilder|tabtip)\.exe$', name, re.I):
            continue
        out.append((int(pid), name))
    return out


def run_command(prog, cfg, game=None):
    """The command that starts a program, as a list (for QProcess) and an env dict."""
    s = cfg['programs'].get(prog.key, {})
    env = {}
    if s.get('log'):
        env['RUSTOS_WINEDEBUG'] = 'err+all,fixme-all'
    if s.get('dxvk_hud'):
        env['DXVK_HUD'] = 'fps'
    if s.get('no_warn'):
        env['RUSTOS_NOWARN'] = '1'
    as_game = s.get('game', False) if game is None else game
    if prog.kind == 'installed':
        return ['bash', '-c', prog.exec_line], env
    args = [RUN] + (['--game'] if as_game else []) + [prog.path]
    extra = s.get('args', '').strip()
    if extra:
        import shlex
        args += shlex.split(extra)
    return args, env


def dll_install(path, where='windows'):
    """Copy a DLL into Windows (or a program folder) and make Wine prefer it. Returns a message."""
    base = os.path.basename(path)
    stem = os.path.splitext(base)[0].lower()
    bits = pe_bits(path)
    if where == 'windows':
        win = os.path.join(PREFIX, 'drive_c', 'windows')
        if not os.path.isdir(win):
            raise RuntimeError('The Windows environment is not set up yet. Run any program once, then try again.')
        sub = 'syswow64' if bits == 32 and os.path.isdir(os.path.join(win, 'syswow64')) else 'system32'
        dest = os.path.join(win, sub)
        shutil.copy2(path, os.path.join(dest, base))
        reg = ['wine', 'C:\\windows\\syswow64\\regsvr32.exe' if sub == 'syswow64' else 'regsvr32', '/s', base]
        subprocess.run(reg, capture_output=True, timeout=60, env=dict(os.environ, WINEDEBUG='-all'))
    else:
        shutil.copy2(path, os.path.join(where, base))
        sub = where
    subprocess.run(['wine', 'reg', 'add', 'HKCU\\Software\\Wine\\DllOverrides', '/v', stem, '/d', 'native,builtin', '/f'],
                   capture_output=True, timeout=60, env=dict(os.environ, WINEDEBUG='-all'))
    return f'{base} ({bits or "?"}-bit) is installed in {os.path.basename(sub)}.'


def is_core_dll(path):
    return os.path.splitext(os.path.basename(path))[0].lower() in CORE_DLLS


def make_menu_entry(prog):
    """A normal app-menu entry for a portable program."""
    d = os.path.join(DATA, 'applications')
    os.makedirs(d, exist_ok=True)
    safe = re.sub(r'[^A-Za-z0-9]+', '-', prog.name).strip('-').lower() or 'program'
    f = os.path.join(d, f'rustos-exe-{safe}.desktop')
    icon = exe_icon(prog.path) or 'wine'
    with open(f, 'w') as fh:
        fh.write('[Desktop Entry]\nType=Application\n'
                 f'Name={prog.name}\nComment=Windows program (RustOS EXE Center)\n'
                 f'Exec={RUN} "{prog.path}"\nPath={os.path.dirname(prog.path)}\nIcon={icon}\n'
                 'Categories=Wine;\nTerminal=false\n')
    return f


def prefix_size():
    total = 0
    for top, _, files in os.walk(PREFIX):
        for f in files:
            try:
                total += os.lstat(os.path.join(top, f)).st_size
            except OSError:
                pass
    return total


# ------------------------------------------------------------------ self test (no Wine needed)
if __name__ == '__main__':
    import sys
    if sys.argv[1:] == ['selftest']:
        assert classify('cs1.6 setup.exe') == 'Setups'
        assert classify('vc_redist.x64.exe') == 'Runtimes'
        assert classify('d3dx9_43.DLL') == 'DLLs'
        assert classify('hl.exe') == 'Programs'
        assert nice_name('/x/Programs/Half-Life/hl.exe') == 'Half-Life'
        assert nice_name('/x/Programs/notepad2.exe') == 'notepad2'
        print('selftest ok')
