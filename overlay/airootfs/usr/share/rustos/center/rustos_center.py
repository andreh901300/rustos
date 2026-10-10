#!/usr/bin/env python3
"""RustOS Center: RustOS's own settings app (RustOS 3.0).
Updates, Apps, Gaming, Battery and power, Antivirus, Education, Look and iPad, Mods, Windows apps and System in one window.
Start it from the menu ("RustOS Center") or run  rustos-center  (rustos-center --page gaming  opens one page).
Every RustOS tool still works on its own in a terminal; this window runs those same tools for you."""
import os
import pwd
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import center_core as core  # noqa: E402

from PyQt6.QtCore import QEasingCurve, QProcess, QProcessEnvironment, QPropertyAnimation, QSize, Qt, QTimer, QUrl  # noqa: E402
from PyQt6.QtGui import QColor, QDesktopServices, QGuiApplication, QIcon, QPixmap  # noqa: E402
from PyQt6.QtNetwork import QLocalServer, QLocalSocket  # noqa: E402
from PyQt6.QtWidgets import (  # noqa: E402
    QApplication, QButtonGroup, QCheckBox, QColorDialog, QComboBox, QFileDialog, QFrame, QGraphicsOpacityEffect,
    QGridLayout, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
    QMessageBox, QPlainTextEdit, QProgressBar, QPushButton, QRadioButton, QScrollArea, QSizePolicy, QStackedWidget,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

TITLE = 'RustOS Center'
ROLE = Qt.ItemDataRole.UserRole
USER = pwd.getpwuid(os.getuid()).pw_name
B = core.BIN

STYLE = """
QWidget { background: #121d1a; color: #e9ede8; font-size: 14px; }
QLabel { background: transparent; }
QLabel#h1 { font-size: 24px; font-weight: 800; }
QLabel#big { font-size: 30px; font-weight: 900; }
QLabel#huge { font-size: 46px; font-weight: 900; color: #ff9a3c; }
QLabel#h2 { font-size: 17px; font-weight: 800; color: #ff9a3c; }
QLabel#muted { color: #a9b8b1; }
QLabel#ok { color: #5fd38d; font-weight: 700; }
QLabel#warn { color: #ffcc66; font-weight: 700; }
QLabel#bad { color: #ff7a6b; font-weight: 700; }
QLabel#pill { background: #1b2a26; border: 1px solid #33463f; border-radius: 12px; padding: 4px 12px; color: #cfd9d4; }
QLabel#statv { font-size: 22px; font-weight: 800; }
QListWidget#side { background: #0d1513; border: none; padding-top: 6px; outline: 0; }
QListWidget#side::item { padding: 10px 12px; margin: 2px 8px; border-radius: 9px; }
QListWidget#side::item:selected { background: #26382f; color: #ffffff; border-left: 3px solid #ff9a3c; }
QListWidget#side::item:hover { background: #1b2a26; }
QPushButton { background: #26382f; border: 1px solid #33463f; padding: 8px 14px; border-radius: 9px; }
QPushButton:hover { background: #30463c; border-color: #4a6358; }
QPushButton:pressed { background: #1b2a26; }
QPushButton:disabled { color: #6b7873; background: #1b2a26; }
QPushButton#primary { background: #ff9a3c; color: #121d1a; font-weight: 800; border: none; }
QPushButton#primary:hover { background: #ffb066; }
QPushButton#primary:disabled { background: #6b4a2c; color: #2a1e14; }
QPushButton#danger { background: #4a1f1b; border-color: #7a2e27; }
QPushButton#tile { text-align: left; padding: 16px; border-radius: 14px; background: #1b2a26; border: 1px solid #26382f; font-size: 15px; font-weight: 700; }
QPushButton#tile:hover { border-color: #ff9a3c; background: #22342e; }
QPushButton#link { background: transparent; border: none; color: #ff9a3c; padding: 2px 4px; }
QPushButton#link:hover { text-decoration: underline; }
QLineEdit, QComboBox { background: #1b2a26; border: 1px solid #33463f; border-radius: 9px; padding: 7px 10px; }
QLineEdit:focus, QComboBox:focus { border-color: #ff9a3c; }
QComboBox QAbstractItemView { background: #1b2a26; selection-background-color: #30463c; border: 1px solid #33463f; }
QListWidget, QTreeWidget { background: #1b2a26; border: 1px solid #26382f; border-radius: 10px; outline: 0; }
QListWidget::item, QTreeWidget::item { padding: 7px; }
QListWidget::item:selected, QTreeWidget::item:selected { background: #30463c; color: #ffffff; }
QHeaderView::section { background: #1b2a26; color: #a9b8b1; border: none; padding: 6px; }
QPlainTextEdit { background: #0f1816; border: 1px solid #26382f; border-radius: 10px; font-family: monospace; font-size: 12px; color: #cfd9d4; }
QPlainTextEdit#log { background: #0a100e; border: none; border-top: 1px solid #26382f; border-radius: 0; }
QFrame#card { background: #17241f; border: 1px solid #26382f; border-radius: 16px; }
QFrame#stat { background: #17241f; border: 1px solid #26382f; border-radius: 16px; }
QFrame#stat:hover { border-color: #ff9a3c; }
QFrame#hero { border-radius: 20px; border: none;
  background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ff9a3c, stop:0.55 #d9622b, stop:1 #7a2e17); }
QFrame#hero QLabel { color: #1a0f08; }
QFrame#hero QLabel#pill { background: rgba(0,0,0,0.18); border: 1px solid rgba(0,0,0,0.25); color: #1a0f08; }
QFrame#row { background: #1b2a26; border: 1px solid #26382f; border-radius: 12px; }
QFrame#banner { background: #3a2412; border: 1px solid #ff9a3c; border-radius: 12px; }
QScrollArea { border: none; }
QCheckBox, QRadioButton { spacing: 10px; background: transparent; }
QCheckBox::indicator, QRadioButton::indicator { width: 20px; height: 20px; border: 2px solid #4a6358; background: #121d1a; }
QCheckBox::indicator { border-radius: 6px; }
QRadioButton::indicator { border-radius: 11px; }
QCheckBox::indicator:checked, QRadioButton::indicator:checked { background: #ff9a3c; border-color: #ff9a3c; }
QCheckBox::indicator:disabled { border-color: #33463f; background: #26382f; }
QCheckBox::indicator:checked:disabled { background: #6b4a2c; }
QProgressBar { background: #1b2a26; border: none; border-radius: 6px; height: 12px; text-align: center; color: transparent; }
QProgressBar::chunk { background: #ff9a3c; border-radius: 6px; }
QStatusBar { background: #0d1513; color: #a9b8b1; }
QStatusBar QLabel { padding: 0 6px; }
QScrollBar:vertical { background: transparent; width: 10px; }
QScrollBar::handle:vertical { background: #33463f; border-radius: 5px; min-height: 30px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
QToolTip { background: #1b2a26; color: #e9ede8; border: 1px solid #33463f; }
"""

PAGES = [
    ('home', 'Home', ('go-home', 'user-home')),
    ('updates', 'Updates', ('system-software-update', 'update-none')),
    ('apps', 'Apps', ('plasmadiscover', 'system-software-install')),
    ('gaming', 'Gaming', ('applications-games', 'input-gaming')),
    ('power', 'Battery and power', ('battery-good', 'preferences-system-power-management')),
    ('antivirus', 'Antivirus', ('security-high', 'security-medium')),
    ('education', 'Education', ('applications-education', 'accessories-dictionary')),
    ('look', 'Look and iPad', ('preferences-desktop-theme', 'preferences-desktop-color')),
    ('mods', 'Mods', ('preferences-plugin', 'application-x-addon')),
    ('windows', 'Windows apps', ('wine', 'applications-other')),
    ('devhw', 'Hardware dev', ('cpu', 'computer', 'preferences-desktop-peripherals')),
    ('system', 'System', ('utilities-system-monitor', 'preferences-system')),
]
SUBTITLES = {
    'home': 'Everything RustOS in one place',
    'updates': 'New versions, automatic updates, the update channel and what changed',
    'apps': 'Add programs with one click. RustOS stays light because nothing here is installed until you pick it.',
    'gaming': 'Steam, graphics drivers and the RustOS game boost',
    'power': 'Longer battery life, cooler laptop, or full speed: you pick',
    'antivirus': 'Scans only when you ask. Nothing runs in the background.',
    'education': 'PDF tools, study apps and shortcuts to school websites',
    'look': 'Colors, animations, the boot screen and the iPad-style desktop',
    'mods': 'Little switches for RustOS, and your own mods (the same as ".debug mods" in a terminal)',
    'windows': 'Run .exe programs, open your Windows files and find replacements for Windows apps',
    'devhw': 'FPGA boards and DMA-capable PCIe devices: diagnostics, protected VFIO, board access, developer kernel',
    'system': 'Self-test, quick fixes and information for when something is wrong',
}
FPS_CAPS = [('No cap', 0), ('30 FPS', 30), ('40 FPS', 40), ('45 FPS', 45), ('60 FPS', 60), ('75 FPS', 75),
            ('90 FPS', 90), ('120 FPS', 120), ('144 FPS', 144), ('165 FPS', 165)]
GAMING_PICKS = [('steam', 'Steam', 'Plays Windows games with Proton', True),
                ('tools', 'Performance tools', 'GameMode, MangoHud overlay and Gamescope (needed for the game boost)', True),
                ('wine', 'Windows programs', 'Run .exe files with Wine (EXE Center)', False),
                ('lutris', 'Lutris', 'Other Windows game launchers', False),
                ('heroic', 'Heroic Games Launcher', 'Epic, GOG and Amazon games', False),
                ('protonup', 'ProtonUp-Qt', 'Download GE-Proton for even more games', False),
                ('discord', 'Discord', 'Chat while you play', False)]
MODES = [('auto', 'Automatic (recommended)', 'Full speed when plugged in, battery saving when not. Switches by itself.'),
         ('performance', 'Performance', 'Always full speed. Best FPS, more heat and fan noise, shorter battery.'),
         ('balanced', 'Balanced', 'Good speed, quieter. The normal setting.'),
         ('battery', 'Battery saver', 'Always save power: longest battery and a cool, quiet laptop.')]


# ------------------------------------------------------------------ small helpers
def theme_icon(*names):
    for n in names:
        ic = QIcon.fromTheme(n)
        if not ic.isNull():
            return ic
    return QIcon()


def button(text, slot=None, kind=None, tip=None):
    b = QPushButton(text)
    if kind:
        b.setObjectName(kind)
    if tip:
        b.setToolTip(tip)
    if slot:
        b.clicked.connect(slot)
    return b


def label(text, kind=None, wrap=False):
    lab = QLabel(text)
    if kind:
        lab.setObjectName(kind)
    lab.setWordWrap(wrap)
    lab.setTextFormat(Qt.TextFormat.RichText if '<' in text else Qt.TextFormat.AutoText)
    return lab


def set_kind(lab, kind):
    lab.setObjectName(kind)
    lab.style().unpolish(lab)
    lab.style().polish(lab)


def card(title=None, text=None):
    fr = QFrame()
    fr.setObjectName('card')
    v = QVBoxLayout(fr)
    v.setContentsMargins(20, 16, 20, 18)
    v.setSpacing(10)
    if title:
        v.addWidget(label(title, 'h2'))
    if text:
        v.addWidget(label(text, 'muted', wrap=True))
    return fr, v


def hrow(*widgets, stretch=True):
    h = QHBoxLayout()
    h.setSpacing(10)
    for w in widgets:
        if w is None:
            h.addStretch(1)
        elif isinstance(w, (QHBoxLayout, QVBoxLayout, QGridLayout)):
            h.addLayout(w)
        else:
            h.addWidget(w)
    if stretch:
        h.addStretch(1)
    return h


def check(text, sub=None, on=False):
    c = QCheckBox(text if not sub else '%s  -  %s' % (text, sub))
    c.setChecked(on)
    return c


def combo(items, current=None):
    c = QComboBox()
    for text, data in items:
        c.addItem(text, data)
    if current is not None:
        for i in range(c.count()):
            if str(c.itemData(i)) == str(current):
                c.setCurrentIndex(i)
    return c


def clear_layout(lay):
    n = lay.count()
    for i in reversed(range(n if isinstance(n, int) else 0)):
        it = lay.takeAt(i)
        if it is not None and it.widget():
            it.widget().deleteLater()


def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


class Main(QMainWindow):
    def __init__(self, start_page='home', scan=None):
        super().__init__()
        self.job = None
        self.bgs = []
        self.loaded = set()
        self.pkgs = set()
        self.flats = set()
        self.updates = []
        self.upd_result = None
        self.scan_found = []
        self.scan_root = False
        self.perf = core.perf_conf()
        self.setWindowTitle(TITLE)
        self.setWindowIcon(theme_icon('rustos', 'preferences-system'))
        self.resize(1200, 800)
        self.setMinimumSize(900, 600)

        root = QWidget()
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ---- sidebar
        sidew = QWidget()
        sidew.setObjectName('sidew')
        sidew.setStyleSheet('QWidget#sidew { background: #0d1513; }')
        sv = QVBoxLayout(sidew)
        sv.setContentsMargins(0, 14, 0, 10)
        brand = QHBoxLayout()
        brand.setContentsMargins(18, 0, 12, 8)
        logo = QLabel()
        pm = QPixmap(core.SHARE + '/logo-64.png')
        if not pm.isNull():
            logo.setPixmap(pm.scaled(34, 34, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        brand.addWidget(logo)
        bl = label('<b style="font-size:17px">RustOS</b><br><span style="color:#a9b8b1">Center</span>')
        brand.addWidget(bl)
        brand.addStretch(1)
        sv.addLayout(brand)
        self.side = QListWidget()
        self.side.setObjectName('side')
        self.side.setFixedWidth(232)
        self.side.setIconSize(QSize(22, 22))
        for key, name, icons in PAGES:
            it = QListWidgetItem(theme_icon(*icons), name)
            it.setData(ROLE, key)
            self.side.addItem(it)
        self.side.currentRowChanged.connect(self.show_page)
        sv.addWidget(self.side, 1)
        self.side_ver = label('', 'muted')
        self.side_ver.setContentsMargins(18, 0, 0, 0)
        sv.addWidget(self.side_ver)
        outer.addWidget(sidew)

        # ---- right side
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(22, 16, 22, 0)
        rv.setSpacing(6)
        outer.addWidget(right, 1)
        self.title = label('Home', 'h1')
        self.subtitle = label('', 'muted', wrap=True)
        rv.addWidget(self.title)
        rv.addWidget(self.subtitle)

        self.stack = QStackedWidget()
        rv.addWidget(self.stack, 1)
        self.keys = [p[0] for p in PAGES]
        builders = {'home': self.page_home, 'updates': self.page_updates, 'apps': self.page_apps,
                    'gaming': self.page_gaming, 'power': self.page_power, 'antivirus': self.page_antivirus,
                    'education': self.page_education, 'look': self.page_look, 'mods': self.page_mods,
                    'windows': self.page_windows, 'devhw': self.page_devhw, 'system': self.page_system}
        for key in self.keys:
            self.stack.addWidget(builders[key]())

        self.log = QPlainTextEdit()
        self.log.setObjectName('log')
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(5000)
        self.log.setFixedHeight(180)
        self.log.setVisible(False)
        rv.addWidget(self.log)
        self.setCentralWidget(root)

        # ---- status bar: what is running
        self.status = self.statusBar()
        self.busy_bar = QProgressBar()
        self.busy_bar.setRange(0, 0)
        self.busy_bar.setFixedWidth(140)
        self.busy_bar.setVisible(False)
        self.busy_label = label('', 'muted')
        self.cancel_btn = button('Stop', self.cancel_job, 'danger')
        self.cancel_btn.setVisible(False)
        self.status.addWidget(self.busy_bar)
        self.status.addWidget(self.busy_label, 1)
        self.status.addPermanentWidget(self.cancel_btn)
        self.log_btn = button('Show log', self.toggle_log)
        self.log_btn.setFlat(True)
        self.status.addPermanentWidget(self.log_btn)

        self.power_timer = QTimer(self, interval=4000)
        self.power_timer.timeout.connect(self.refresh_power_live)

        self.side_ver.setText('RustOS ' + core.rustos_version())
        start = self.keys.index(start_page) if start_page in self.keys else 0
        self.side.setCurrentRow(start)
        if start == 0:
            self.show_page(0)
        if scan:
            QTimer.singleShot(400, lambda: self.start_scan(scan, False))

    # ================================================================ running tools
    def root_argv(self, argv):
        lang = os.environ.get('LANG', 'C.UTF-8')
        return ['pkexec', 'env', 'LANG=' + lang, 'SUDO_USER=' + USER, 'NO_COLOR=1',
                'PATH=/usr/local/sbin:/usr/local/bin:/usr/bin'] + list(argv)

    def run(self, title, argv, root=False, done=None, line=None, show=None, cancellable=None):
        """Run one tool with its output in the log. root=True asks for the password (pkexec)."""
        if self.job:
            QMessageBox.information(self, TITLE, 'Please wait: "%s" is still running.' % self.job['title'])
            return False
        if root:
            argv = self.root_argv(argv)
        p = QProcess(self)
        p.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        env = QProcessEnvironment.systemEnvironment()
        env.insert('NO_COLOR', '1')
        env.insert('RUSTOS_CLASSIC', '1')
        p.setProcessEnvironment(env)
        self.job = {'proc': p, 'title': title, 'buf': '', 'out': [], 'done': done, 'line': line,
                    'show': show, 'root': root, 'cancelled': False}
        p.readyReadStandardOutput.connect(self.job_read)
        p.finished.connect(self.job_finished)
        p.errorOccurred.connect(self.job_error)
        self.log_add('\n== %s' % title)
        if show is None:
            self.set_log(True)
        self.busy_bar.setVisible(True)
        self.busy_label.setText(title + '…' + ('  (type your password in the window that opens)' if root else ''))
        self.cancel_btn.setVisible(not root if cancellable is None else cancellable)
        p.start(argv[0], argv[1:])
        return True

    def job_read(self):
        j = self.job
        if not j:
            return
        j['buf'] += bytes(j['proc'].readAllStandardOutput()).decode('utf-8', 'replace')
        *lines, j['buf'] = j['buf'].split('\n')
        for ln in lines:
            self.job_line(core.clean(ln))

    def job_line(self, ln):
        j = self.job
        j['out'].append(ln)
        if len(j['out']) > 20000:
            del j['out'][:5000]
        if j['show'] is None or j['show'](ln):
            self.log_add(ln)
        if j['line']:
            j['line'](ln)

    def job_error(self, err):
        if err == QProcess.ProcessError.FailedToStart and self.job:
            self.log_add('Could not start: %s' % self.job['proc'].program())
            self.job_finished(127, None)

    def job_finished(self, code, _status=None):
        j = self.job
        if not j:
            return
        if j['buf']:
            self.job_line(core.clean(j['buf']))
            j['buf'] = ''
        self.job = None
        self.busy_bar.setVisible(False)
        self.cancel_btn.setVisible(False)
        out = '\n'.join(j['out'])
        if j['cancelled']:
            code = -2
            self.busy_label.setText('Stopped.')
        elif j['root'] and code in (126, 127) and len(j['out']) < 3:
            code = -1
            self.busy_label.setText('Cancelled (no password was given).')
        else:
            self.busy_label.setText('%s: %s' % (j['title'], 'done' if code == 0 else 'finished with a problem (see the log)'))
        self.log_add('== %s (exit %s)' % ('stopped' if code == -2 else 'cancelled' if code == -1 else 'finished', code))
        j['proc'].deleteLater()
        if j['done']:
            j['done'](code, out)

    def cancel_job(self):
        if self.job and not self.job['root']:
            self.job['cancelled'] = True
            self.job['proc'].kill()

    def bg(self, argv, cb, env=None):
        """Run a tool quietly in the background and give its output to cb(code, text)."""
        p = QProcess(self)
        p.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        e = QProcessEnvironment.systemEnvironment()
        e.insert('NO_COLOR', '1')
        for k, v in (env or {}).items():
            e.insert(k, v)
        p.setProcessEnvironment(e)
        self.bgs.append(p)

        def fin(code, _st=None):
            text = core.clean(bytes(p.readAll()).decode('utf-8', 'replace'))
            if p in self.bgs:
                self.bgs.remove(p)
            p.deleteLater()
            try:
                cb(code, text)
            except RuntimeError:          # the window was closed meanwhile
                pass

        def err(e2):
            if e2 == QProcess.ProcessError.FailedToStart:
                fin(127)
        p.finished.connect(fin)
        p.errorOccurred.connect(err)
        p.start(argv[0], argv[1:])

    def detach(self, argv):
        env = dict(os.environ, RUSTOS_CLASSIC='1')
        try:
            import subprocess
            subprocess.Popen(argv, env=env, start_new_session=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except OSError:
            QMessageBox.warning(self, TITLE, 'Could not start %s' % argv[0])
            return False

    def terminal(self, cmd):
        """A visible terminal window (for things that need you to watch or type)."""
        self.detach(['konsole', '--hold', '-e', 'bash', '-c', cmd])

    def log_add(self, text):
        self.log.appendPlainText(text)

    def set_log(self, on):
        self.log.setVisible(on)
        self.log_btn.setText('Hide log' if on else 'Show log')

    def toggle_log(self):
        self.set_log(not self.log.isVisible())

    def info(self, text, title=TITLE):
        QMessageBox.information(self, title, text)

    def ask(self, text, yes='Yes', no='Cancel'):
        m = QMessageBox(self)
        m.setWindowTitle(TITLE)
        m.setText(text)
        y = m.addButton(yes, QMessageBox.ButtonRole.AcceptRole)
        m.addButton(no, QMessageBox.ButtonRole.RejectRole)
        m.exec()
        return m.clickedButton() == y

    # ================================================================ pages
    def scroll_page(self):
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 10, 8, 18)
        v.setSpacing(14)
        sa.setWidget(w)
        return sa, v

    def show_page(self, row):
        if row < 0:
            return
        key = self.keys[row]
        self.title.setText(PAGES[row][1])
        self.subtitle.setText(SUBTITLES.get(key, ''))
        self.stack.setCurrentIndex(row)
        w = self.stack.currentWidget()
        eff = QGraphicsOpacityEffect(w)
        w.setGraphicsEffect(eff)
        self.anim = QPropertyAnimation(eff, b'opacity', self)
        self.anim.setDuration(180)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.finished.connect(lambda: w.setGraphicsEffect(None))
        self.anim.start()
        if key == 'power':
            self.refresh_power_live()
            self.power_timer.start()
        else:
            self.power_timer.stop()
        loader = getattr(self, 'load_' + key, None)
        if loader and (key not in self.loaded or key in ('home', 'power')):
            self.loaded.add(key)
            loader()

    def go(self, key):
        if key in self.keys:
            self.side.setCurrentRow(self.keys.index(key))

    # ---------------------------------------------------------------- Home
    def page_home(self):
        sa, v = self.scroll_page()
        hero = QFrame()
        hero.setObjectName('hero')
        hl = QHBoxLayout(hero)
        hl.setContentsMargins(26, 22, 26, 22)
        hl.setSpacing(20)
        logo = QLabel()
        pm = QPixmap(core.SHARE + '/logo-128.png')
        if not pm.isNull():
            logo.setPixmap(pm.scaled(96, 96, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        hl.addWidget(logo)
        txt = QVBoxLayout()
        self.hero_title = label('RustOS', 'big')
        name = (pwd.getpwuid(os.getuid()).pw_gecos.split(',')[0] or USER).split(' ')[0]
        txt.addWidget(self.hero_title)
        txt.addWidget(label('Welcome back, %s. Fast, light, and yours.' % esc(name)))
        self.hero_pills = QHBoxLayout()
        self.hero_pills.setSpacing(8)
        txt.addLayout(self.hero_pills)
        hl.addLayout(txt, 1)
        v.addWidget(hero)

        grid = QGridLayout()
        grid.setSpacing(12)
        self.stats = {}
        for i, (key, name, page) in enumerate([('updates', 'Updates', 'updates'), ('power', 'Power', 'power'),
                                               ('mode', 'Performance mode', 'power'), ('safety', 'Self-test', 'system')]):
            fr = QFrame()
            fr.setObjectName('stat')
            fr.setCursor(Qt.CursorShape.PointingHandCursor)
            fl = QVBoxLayout(fr)
            fl.setContentsMargins(16, 14, 16, 14)
            fl.addWidget(label(name, 'muted'))
            val = label('…', 'statv')
            sub = label('', 'muted', wrap=True)
            fl.addWidget(val)
            fl.addWidget(sub)
            fr.mousePressEvent = (lambda _e, p=page: self.go(p))
            self.stats[key] = (val, sub)
            grid.addWidget(fr, 0, i)
        v.addLayout(grid)

        v.addWidget(label('Quick actions', 'h2'))
        tiles = QGridLayout()
        tiles.setSpacing(12)
        acts = [('Check for updates', 'system-software-update', lambda: (self.go('updates'), self.check_updates())),
                ('Add apps', 'plasmadiscover', lambda: self.go('apps')),
                ('Game boost and FPS', 'applications-games', lambda: self.go('gaming')),
                ('Longer battery', 'battery-good', lambda: self.go('power')),
                ('Scan for viruses', 'security-high', lambda: (self.go('antivirus'), self.scan_quick())),
                ('Run a Windows .exe', 'wine', self.open_exe_center),
                ('Dark or light look', 'preferences-desktop-theme', lambda: self.go('look')),
                ('iPad mode', 'preferences-desktop-tablet', lambda: self.go('look')),
                ('Something is wrong', 'help-hint', lambda: self.go('system'))]
        for i, (text, icon, slot) in enumerate(acts):
            b = button('   ' + text, slot, 'tile')
            b.setIcon(theme_icon(icon, 'rustos'))
            b.setIconSize(QSize(28, 28))
            b.setMinimumHeight(66)
            tiles.addWidget(b, i // 3, i % 3)
        v.addLayout(tiles)
        v.addStretch(1)
        return sa

    def load_home(self):
        ver = core.rustos_version()
        self.hero_title.setText('RustOS ' + ver)
        clear_layout(self.hero_pills)
        ch = core.channel()
        pills = ['Updates: ' + ('beta channel' if ch == 'beta' else 'normal'),
                 'Automatic updates ' + ('on' if core.autoupdate_on() else 'off'),
                 'PC (x86_64)' if core.IS_PC else 'ARM edition']
        for p in pills:
            self.hero_pills.addWidget(label(p, 'pill'))
        self.hero_pills.addStretch(1)
        # power
        bats = core.batteries()
        val, sub = self.stats['power']
        if bats:
            cap = bats[0]['capacity']
            val.setText('%s%%' % cap if cap is not None else '?')
            left = core.time_left(bats)
            sub.setText(('On battery' if core.on_battery() else 'Plugged in') + (' · ' + left if left else ''))
        else:
            val.setText('Plugged in')
            sub.setText('Desktop PC (no battery)')
        self.perf = core.perf_conf()
        val, sub = self.stats['mode']
        val.setText(dict((m[0], m[1].split(' (')[0]) for m in MODES).get(self.perf['MODE'], self.perf['MODE']))
        sub.setText('Profile now: ' + core.power_profile())
        val, sub = self.stats['safety']
        val.setText('Run it')
        sub.setText('Checks 25+ things in a few seconds')
        val, sub = self.stats['updates']
        if self.upd_result:
            self.home_updates(*self.upd_result)
        elif core.is_live():
            val.setText('Live disk')
            sub.setText('Install RustOS to get updates')
        elif core.have('checkupdates'):
            val.setText('…')
            sub.setText('Looking for updates')
            self.bg(['checkupdates'], self.home_updates)
        else:
            val.setText('Updates')
            sub.setText('Open the Updates page')

    def home_updates(self, code, text):
        self.upd_result = (code, text)
        val, sub = self.stats['updates']
        if code == 2:
            val.setText('Up to date')
            sub.setText('Last automatic update: ' + (core.last_update() or 'never'))
        elif code == 0:
            ups = core.parse_checkupdates(text)
            self.updates = ups
            val.setText('%d new' % len(ups))
            sub.setText('Including a new RustOS version' if any(u[0] == 'rustos-base' for u in ups) else 'Click to install')
        else:
            val.setText('Offline?')
            sub.setText('Could not check right now')

    # ---------------------------------------------------------------- Updates
    def page_updates(self):
        sa, v = self.scroll_page()
        c, cv = card()
        top = QHBoxLayout()
        left = QVBoxLayout()
        self.up_ver = label('RustOS', 'big')
        self.up_info = label('', 'muted', wrap=True)
        left.addWidget(self.up_ver)
        left.addWidget(self.up_info)
        top.addLayout(left, 1)
        cv.addLayout(top)
        self.up_check_btn = button('Check for updates', self.check_updates, 'primary')
        self.up_install_btn = button('Install updates', self.install_updates)
        cv.addLayout(hrow(self.up_check_btn, self.up_install_btn,
                          button('Undo the last update', lambda: self.detach([B + '/rustos-rollback']),
                                 tip='Puts programs back to the versions they had before the last update'),
                          button('Update history', self.update_history)))
        self.up_state = label('', 'muted', wrap=True)
        cv.addWidget(self.up_state)
        self.up_tree = QTreeWidget()
        self.up_tree.setHeaderLabels(['Program', 'Now', 'New'])
        self.up_tree.setRootIsDecorated(False)
        self.up_tree.setMinimumHeight(180)
        self.up_tree.setVisible(False)
        cv.addWidget(self.up_tree)
        v.addWidget(c)

        c, cv = card('Automatic updates', 'RustOS installs updates by itself once a day, only when you are online and plugged in. '
                                          'It makes a restore point first, so an update can always be undone.')
        self.up_auto = check('Install updates automatically')
        self.up_auto.clicked.connect(self.toggle_autoupdate)
        self.up_hold = label('', 'warn')
        cv.addLayout(hrow(self.up_auto))
        cv.addLayout(hrow(self.up_hold, button('Pause for 7 days', lambda: self.run(
            'Pausing automatic updates', [B + '/rustos-autoupdate', 'pause', '7'], True, lambda *_: self.load_updates())),
            button('Resume now', lambda: self.run('Resuming automatic updates', [B + '/rustos-autoupdate', 'resume'], True,
                                                  lambda *_: self.load_updates()))))
        v.addWidget(c)

        c, cv = card('Update channel', 'Beta gets the test versions first. They can break things, so it is for testers. '
                                       'Going back to Normal puts the normal versions back right away.')
        self.ch_group = QButtonGroup(self)
        self.ch_stable = QRadioButton('Normal updates (recommended)')
        self.ch_beta = QRadioButton('Beta: test versions first')
        self.ch_group.addButton(self.ch_stable)
        self.ch_group.addButton(self.ch_beta)
        cv.addWidget(self.ch_stable)
        cv.addWidget(self.ch_beta)
        cv.addLayout(hrow(button('Switch channel', self.switch_channel)))
        v.addWidget(c)

        c, cv = card("What's new")
        self.wn_combo = QComboBox()
        self.wn_combo.currentIndexChanged.connect(self.show_whatsnew)
        cv.addLayout(hrow(label('Version:'), self.wn_combo))
        self.wn_text = QPlainTextEdit()
        self.wn_text.setReadOnly(True)
        self.wn_text.setMinimumHeight(260)
        cv.addWidget(self.wn_text)
        v.addWidget(c)
        v.addStretch(1)
        return sa

    def load_updates(self):
        if core.is_live():
            self.up_state.setText('This is the live disk: install RustOS first, then updates come by themselves.')
            self.up_check_btn.setEnabled(False)
            self.up_install_btn.setEnabled(False)
        ver = core.rustos_version()
        self.up_ver.setText('RustOS ' + ver)
        ch = core.channel()
        self.up_info.setText('Channel: %s   ·   Last automatic update: %s' %
                             ('beta' if ch == 'beta' else 'normal', core.last_update() or 'never'))
        self.up_auto.setChecked(core.autoupdate_on())
        hold = core.update_hold_until()
        import time
        self.up_hold.setText('Paused until %s' % time.strftime('%a %d %b', time.localtime(hold)) if hold else '')
        (self.ch_beta if ch == 'beta' else self.ch_stable).setChecked(True)
        if self.wn_combo.count() == 0:
            self.versions = core.changelog_versions()
            for vv, _ in self.versions:
                self.wn_combo.addItem('RustOS ' + vv)
            if not self.versions:
                self.wn_text.setPlainText('No list of changes was found on this system.')

    def show_whatsnew(self, i):
        if 0 <= i < len(getattr(self, 'versions', [])):
            self.wn_text.setPlainText(self.versions[i][1])

    def check_updates(self):
        if not core.have('checkupdates'):
            self.up_state.setText('The update checker is missing (pacman-contrib). Install updates with the button anyway.')
            return
        self.up_state.setText('Looking for updates…')
        self.up_check_btn.setEnabled(False)
        self.bg(['checkupdates'], self.got_updates)

    def got_updates(self, code, text):
        self.up_check_btn.setEnabled(True)
        self.up_tree.clear()
        if code == 2:
            self.updates = []
            self.up_state.setText('<b>You are up to date.</b> Nothing to install right now.')
            self.up_tree.setVisible(False)
        elif code == 0:
            self.updates = core.parse_checkupdates(text)
            new_os = any(u[0] == 'rustos-base' for u in self.updates)
            self.up_state.setText('<b>%d updates are available.</b>%s Install them now: it takes a few minutes and you can keep working.'
                                  % (len(self.updates), ' This includes a <b>new RustOS version</b>.' if new_os else ''))
            for name, old, new in self.updates:
                it = QTreeWidgetItem([('★ RustOS  ' if name == 'rustos-base' else '') + name, old, new])
                self.up_tree.addTopLevelItem(it)
            for col in range(3):
                self.up_tree.resizeColumnToContents(col)
            self.up_tree.setVisible(True)
        else:
            self.up_state.setText('Could not check for updates. Are you online?')
        self.home_updates(code, text)

    def install_updates(self):
        def done(code, out):
            if code == 0:
                self.up_state.setText('<b>Updates installed.</b> If the kernel or RustOS was updated, restart when it suits you.')
                self.updates = []
                self.check_updates()
            elif code >= 0:
                self.up_state.setText('The update did not finish. See the log for the first error, or try again.')
        self.run('Installing updates', [B + '/rustos-update', '--now'], True, done)

    def update_history(self):
        txt = core.read(core.UPDATE_LOG, '(no updates yet)')
        self.text_dialog('Update history', '\n'.join(txt.splitlines()[-200:]))

    def toggle_autoupdate(self):
        on = self.up_auto.isChecked()
        self.run('Automatic updates ' + ('on' if on else 'off'), [B + '/rustos-autoupdate', 'on' if on else 'off'], True,
                 lambda *_: self.load_updates())

    def switch_channel(self):
        want = 'beta' if self.ch_beta.isChecked() else 'stable'
        if want == core.channel():
            self.info('This PC already gets %s updates.' % ('beta' if want == 'beta' else 'normal'))
            return
        if want == 'beta' and not self.ask('Beta updates are test versions and can break things.<br>Switch to beta?', 'Switch to beta'):
            self.load_updates()
            return
        self.run('Switching the update channel to ' + want, [B + '/rustos-channel', want], True, lambda *_: self.load_updates())

    def text_dialog(self, title, text):
        m = QMessageBox(self)
        m.setWindowTitle(title)
        m.setText(title)
        m.setDetailedText(text)
        m.setInformativeText('Press "Show Details" to read it.')
        m.exec()

    # ---------------------------------------------------------------- Apps
    def page_apps(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 10, 0, 10)
        top = QHBoxLayout()
        self.app_search = QLineEdit()
        self.app_search.setPlaceholderText('Search apps… (try "video", "office", "discord")')
        self.app_search.setClearButtonEnabled(True)
        self.app_search.textChanged.connect(self.fill_apps)
        top.addWidget(self.app_search, 1)
        v.addLayout(top)
        mid = QHBoxLayout()
        self.app_cats = QListWidget()
        self.app_cats.setFixedWidth(210)
        self.app_cats.currentRowChanged.connect(self.fill_apps)
        mid.addWidget(self.app_cats)
        self.app_list = QListWidget()
        self.app_list.setIconSize(QSize(32, 32))
        self.app_list.setSpacing(2)
        self.app_list.itemChanged.connect(self.app_ticked)
        self.app_list.itemDoubleClicked.connect(self.app_open_special)
        mid.addWidget(self.app_list, 1)
        v.addLayout(mid, 1)
        self.app_count = label('', 'muted')
        self.app_go = button('Install the ticked apps', self.install_apps, 'primary')
        v.addLayout(hrow(self.app_count, None, button('Refresh', self.load_apps), self.app_go, stretch=False))
        return w

    def load_apps(self):
        self.apps = core.catalog()
        self.app_sel = set(self.app_sel) if hasattr(self, 'app_sel') else set()
        self.pkgs = core.installed_packages()
        self.flats = core.installed_flatpaks()
        cats = []
        for a in self.apps:
            if a['cat'] not in cats:
                cats.append(a['cat'])
        self.app_cats.blockSignals(True)
        self.app_cats.clear()
        for c in ['All apps', 'Installed'] + cats:
            self.app_cats.addItem(c)
        self.app_cats.setCurrentRow(0)
        self.app_cats.blockSignals(False)
        if not self.apps:
            self.app_count.setText('The app list is missing (%s). Run a RustOS update.' % core.CATALOG)
        self.fill_apps()

    def fill_apps(self, *_):
        if not hasattr(self, 'apps'):
            return
        cat = self.app_cats.currentItem().text() if self.app_cats.currentItem() else 'All apps'
        q = self.app_search.text().strip().lower()
        self.app_list.blockSignals(True)
        self.app_list.clear()
        icons = {'Office and study': 'applications-office', 'Internet and chat': 'applications-internet',
                 'Music and video': 'applications-multimedia', 'Pictures and design': 'applications-graphics',
                 'Programming': 'applications-development', 'Tools': 'applications-utilities',
                 'Games': 'applications-games', 'Windows programs': 'wine'}
        for a in self.apps:
            inst = core.app_installed(a, self.pkgs, self.flats)
            if cat == 'Installed' and not inst:
                continue
            if cat not in ('All apps', 'Installed') and a['cat'] != cat:
                continue
            if q and q not in (a['label'] + ' ' + a['cat'] + ' ' + a['id']).lower():
                continue
            name, what = core.split_label(a['label'])
            special = a['id'] in ('edu', 'games', 'fpgaaccess')
            tail = '   ✓ installed' if inst else ('   → opens its own page' if special else '')
            it = QListWidgetItem(theme_icon(a['id'], name.lower().split(' ')[0], icons.get(a['cat'], 'application-x-executable')),
                                 '%s%s\n%s' % (name, tail, what))
            it.setData(ROLE, a['id'])
            if special:
                it.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                it.setToolTip('Double-click to open')
            elif inst:
                it.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            else:
                it.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsUserCheckable)
                it.setCheckState(Qt.CheckState.Checked if a['id'] in self.app_sel else Qt.CheckState.Unchecked)
            self.app_list.addItem(it)
        self.app_list.blockSignals(False)
        self.count_apps()

    def app_ticked(self, it):
        aid = it.data(ROLE)
        if it.checkState() == Qt.CheckState.Checked:
            self.app_sel.add(aid)
        else:
            self.app_sel.discard(aid)
        self.count_apps()

    def count_apps(self):
        n = len(self.app_sel)
        self.app_count.setText('%d ticked' % n if n else 'Tick the apps you want, then press Install. You need an internet connection.')
        self.app_go.setEnabled(n > 0)
        self.app_go.setText('Install %d app%s' % (n, '' if n == 1 else 's') if n else 'Install the ticked apps')

    def app_open_special(self, it):
        aid = it.data(ROLE)
        if aid == 'edu':
            self.go('education')
        elif aid == 'games':
            self.go('gaming')
        elif aid == 'fpgaaccess':
            self.go('devhw')

    def install_apps(self):
        ids = sorted(self.app_sel)
        if not ids:
            return

        def done(code, out):
            self.pkgs = core.installed_packages()
            self.flats = core.installed_flatpaks()
            if code == 0 and core.read('/run/rustos-apps.status').strip() == 'ok':
                msg = '<b>Done!</b> Find your new apps in the menu.'
                if 'windows' in ids:
                    msg += '<br><br>Windows programs: double-click an .exe, or open the <b>EXE Center</b>.'
                if 'print' in ids:
                    msg += '<br><br>Add your printer in System Settings, Printers.'
                if 'docker' in ids:
                    msg += '<br><br>Docker: run <tt>sudo usermod -aG docker $USER</tt> and log in again.'
                self.app_sel.clear()
                self.info(msg)
            elif code >= 0:
                self.info('Not everything was installed. The log at the bottom shows the first error.')
            self.fill_apps()
        self.run('Installing %d app(s)' % len(ids), [B + '/rustos-apps', '--install'] + ids, True, done)

    # ---------------------------------------------------------------- Gaming
    def page_gaming(self):
        sa, v = self.scroll_page()
        if not core.IS_PC:
            c, cv = card('Not on this device', 'Gaming setup (Steam, Proton) needs an Intel or AMD PC. '
                                               'This is the ARM edition of RustOS, so it is not available here.')
            v.addWidget(c)
            v.addStretch(1)
            return sa
        c, cv = card('Your PC')
        self.g_hw = label('…', wrap=True)
        cv.addWidget(self.g_hw)
        v.addWidget(c)

        c, cv = card('Set up gaming', 'Pick what you want. Everything is optional. The graphics driver for your card is added for you.')
        self.g_picks = {}
        for key, name, what, on in GAMING_PICKS:
            cb = check(name, what, on)
            self.g_picks[key] = cb
            cv.addWidget(cb)
        self.g_nvidia = check('Use the NVIDIA driver', 'only for GeForce RTX, GTX 16 series or newer. Older cards: leave it off')
        self.g_nvidia.setVisible(False)
        cv.addWidget(self.g_nvidia)
        self.g_done = label('', 'muted', wrap=True)
        cv.addWidget(self.g_done)
        cv.addLayout(hrow(button('Install', self.install_gaming, 'primary')))
        v.addWidget(c)

        c, cv = card('Game boost', 'RustOS makes games faster when you play: full CPU speed, the game gets priority, '
                                   'fewer stutters. On battery it caps the FPS instead, so the battery lasts much longer.')
        self.g_boost = check('Game boost when plugged in', 'GameMode: full speed and priority for the game')
        self.g_lat = check('Low-latency tweaks', 'fewer stutters: split-lock fix, no watchdog, more memory maps for big games')
        self.g_fps = check('Show FPS in games', 'MangoHud overlay: FPS, frame time, temperatures, battery')
        self.g_accap = combo(FPS_CAPS)
        for w in (self.g_boost, self.g_lat, self.g_fps):
            cv.addWidget(w)
        cv.addLayout(hrow(label('FPS cap when plugged in:'), self.g_accap, label('(a cap at your screen\'s refresh rate gives smoother, cooler games)', 'muted')))
        cv.addLayout(hrow(button('Save', self.save_gaming, 'primary'), label('The FPS cap on battery is on the Battery and power page.', 'muted')))
        v.addWidget(c)

        c, cv = card('Use it in Steam', 'Steam: right-click a game, Properties, Launch Options, and paste this. '
                                        'Games you start with "Run as game" (right-click an .exe) get it by themselves.')
        self.g_launch = QLineEdit('rustos-game %command%')
        self.g_launch.setReadOnly(True)
        cv.addLayout(hrow(self.g_launch, button('Copy', lambda: (QGuiApplication.clipboard().setText(self.g_launch.text()),
                                                                 self.busy_label.setText('Copied: ' + self.g_launch.text()))), stretch=False))
        v.addWidget(c)

        c, cv = card('Low-latency kernel (zen)', 'An optional Linux kernel tuned for games and a snappy desktop: lower input lag and '
                                                 'fewer stutters. The normal kernel stays in the boot menu as a backup.')
        self.g_kernel = label('', wrap=True)
        cv.addWidget(self.g_kernel)
        self.g_zen_btn = button('Install the zen kernel', self.zen_kernel)
        cv.addLayout(hrow(self.g_zen_btn))
        v.addWidget(c)
        v.addStretch(1)
        return sa

    def load_gaming(self):
        if not core.IS_PC:
            return
        g = core.gpus()
        vm = core.virt()
        txt = 'Graphics: <b>%s</b>' % esc(', '.join(g['names']) or 'not found')
        if vm:
            txt += '<br><span style="color:#ffcc66">RustOS runs in a virtual machine (%s): there is no real graphics card, so games will be slow.</span>' % esc(vm)
        self.g_hw.setText(txt)
        self.pkgs = self.pkgs or core.installed_packages()
        has_nv_driver = 'nvidia-open' in self.pkgs or 'nvidia-open-dkms' in self.pkgs
        self.g_nvidia.setVisible(g['nvidia'] and not has_nv_driver)
        done = core.gaming_installed()
        self.g_done.setText('Installed before: ' + ', '.join(done) if done else '')
        self.perf = core.perf_conf()
        self.g_boost.setChecked(self.perf['GAME_BOOST'] == '1')
        self.g_lat.setChecked(self.perf['LATENCY_TWEAKS'] == '1')
        self.g_fps.setChecked(self.perf['SHOW_FPS'] == '1')
        i = self.g_accap.findData(int(self.perf['AC_FPS_CAP'] or 0))
        self.g_accap.setCurrentIndex(max(i, 0))
        if 'mangohud' not in self.pkgs:
            self.g_fps.setToolTip('Needs the Performance tools from "Set up gaming"')
        k = core.kernel_info()
        if k['zen_running']:
            self.g_kernel.setText('<b style="color:#5fd38d">The zen kernel is running.</b> (%s)' % esc(k['running']))
            self.g_zen_btn.setText('Back to the normal kernel')
        elif k['zen_installed']:
            self.g_kernel.setText('The zen kernel is installed. Restart the PC to use it. Running now: %s' % esc(k['running']))
            self.g_zen_btn.setText('Back to the normal kernel')
        else:
            self.g_kernel.setText('Running now: normal kernel (%s)' % esc(k['running']))
            self.g_zen_btn.setText('Install the zen kernel')

    def install_gaming(self):
        picks = [k for k, cb in self.g_picks.items() if cb.isChecked()]
        if not picks:
            self.info('Tick at least one thing.')
            return
        if self.g_nvidia.isVisible() and self.g_nvidia.isChecked():
            picks.append('nvidia')
        elif 'nvidia-open' in self.pkgs:
            picks.append('nvidia')
        if not self.ask('Ready to install. This downloads a few GB and takes a few minutes.', 'Install'):
            return

        def done(code, out):
            self.pkgs = core.installed_packages()
            if code == 0 and core.read('/run/rustos-gaming.status').strip() == 'ok':
                extra = '<br><br><b>Restart your computer</b> once so the NVIDIA driver is used.' if 'nvidia' in picks else ''
                self.info('<b>Gaming setup finished!</b>%s<br><br>In Steam use the launch option <tt>rustos-game %%command%%</tt> '
                          '(copy it on this page) for the game boost and the battery FPS cap.' % extra)
            elif code >= 0:
                self.info('The setup did not finish. The log at the bottom shows the first error.')
            self.load_gaming()
        self.run('Gaming setup', [B + '/rustos-gaming', '--install'] + picks, True, done)

    def save_perf(self, new, what):
        changes = core.perf_changes(self.perf, new)
        if not changes:
            self.busy_label.setText('Nothing changed.')
            return

        def done(code, out):
            self.perf = core.perf_conf()
            if code == 0:
                self.busy_label.setText(what + ' saved.')
            if 'gaming' in self.loaded:
                self.load_gaming()
            self.load_power()
        self.run('Saving ' + what.lower(), [B + '/rustos-performance', 'setmany'] + changes, True, done, show=lambda _l: True)

    def save_gaming(self):
        new = dict(self.perf)
        new['GAME_BOOST'] = '1' if self.g_boost.isChecked() else '0'
        new['LATENCY_TWEAKS'] = '1' if self.g_lat.isChecked() else '0'
        new['SHOW_FPS'] = '1' if self.g_fps.isChecked() else '0'
        new['AC_FPS_CAP'] = str(self.g_accap.currentData())
        if new['SHOW_FPS'] == '1' and 'mangohud' not in self.pkgs:
            self.info('The FPS overlay needs the Performance tools. Tick them in "Set up gaming" and press Install.')
        self.save_perf(new, 'Game settings')

    def zen_kernel(self):
        k = core.kernel_info()
        if k['zen_running'] or k['zen_installed']:
            if not self.ask('Go back to the normal kernel? The extra kernels (zen, LTS) that are not running are removed. '
                            'Restart afterwards.', 'Back to normal'):
                return
            self.run('Going back to the normal kernel', [B + '/rustos-performance', 'kernel', 'default'], True,
                     lambda *_: self.load_gaming())
            return
        if not self.ask('<b>Install the zen kernel?</b><br><br>It downloads about 150 MB and takes a few minutes. '
                        'After a restart RustOS starts with it. The normal kernel stays in the boot menu, so you can always go back.'
                        '<br><br>NVIDIA users: the driver is rebuilt for it automatically.', 'Install'):
            return

        def done(code, out):
            self.load_gaming()
            if code == 0:
                self.info('Done. <b>Restart</b> to use the zen kernel.')
        self.run('Installing the zen kernel', [B + '/rustos-performance', 'kernel', 'zen'], True, done)

    # ---------------------------------------------------------------- Battery and power
    def page_power(self):
        sa, v = self.scroll_page()
        c, cv = card()
        row = QHBoxLayout()
        self.p_pct = label('–', 'huge')
        row.addWidget(self.p_pct)
        col = QVBoxLayout()
        self.p_state = label('', 'h2')
        self.p_left = label('', 'muted')
        col.addWidget(self.p_state)
        col.addWidget(self.p_left)
        row.addLayout(col, 1)
        cv.addLayout(row)
        self.p_bar = QProgressBar()
        self.p_bar.setRange(0, 100)
        cv.addWidget(self.p_bar)
        self.p_details = label('', 'muted', wrap=True)
        cv.addWidget(self.p_details)
        v.addWidget(c)

        c, cv = card('Mode')
        self.p_modes = QButtonGroup(self)
        for key, name, what in MODES:
            rb = QRadioButton(name)
            rb.setProperty('mode', key)
            self.p_modes.addButton(rb)
            cv.addWidget(rb)
            sub = label(what, 'muted', wrap=True)
            sub.setContentsMargins(32, 0, 0, 4)
            cv.addWidget(sub)
        v.addWidget(c)

        c, cv = card('On battery', 'Laptop gaming on battery: an FPS cap is the biggest battery saver. '
                                   '60 FPS on battery often gives 2x the play time, and the laptop stays cool.')
        self.p_batprof = combo([('Power saver (longest battery)', 'power-saver'), ('Balanced (faster)', 'balanced')])
        self.p_turbo = check('CPU turbo on battery', 'faster, but the battery drains much quicker and the laptop gets hot')
        self.p_batcap = combo(FPS_CAPS)
        cv.addLayout(hrow(label('Power profile on battery:'), self.p_batprof))
        cv.addWidget(self.p_turbo)
        cv.addLayout(hrow(label('FPS cap for games on battery:'), self.p_batcap))
        self.p_bat_widgets = [self.p_batprof, self.p_turbo, self.p_batcap]
        v.addWidget(c)

        c, cv = card('Battery care', 'Stop charging early so the battery lasts more years. '
                                     'Great when the laptop is plugged in most of the time.')
        self.p_limit = combo([('Off: charge to 100%', 0), ('Stop at 90%', 90), ('Stop at 85%', 85),
                              ('Stop at 80% (best for the battery)', 80), ('Stop at 60%', 60)])
        self.p_limit_note = label('', 'muted', wrap=True)
        cv.addLayout(hrow(label('Charge limit:'), self.p_limit))
        cv.addWidget(self.p_limit_note)
        v.addWidget(c)

        c, cv = card('More battery tips')
        cv.addWidget(label('&bull; A lower screen refresh rate (60 Hz) and brightness save a lot.<br>'
                           '&bull; Close the browser while gaming on battery.<br>'
                           '&bull; Battery saver mode + a 40-60 FPS cap is the longest laptop gaming you can get.', wrap=True))
        cv.addLayout(hrow(button('Screen settings', lambda: self.detach(['kcmshell6', 'kcm_kscreen'])),
                          button('Power settings (KDE)', lambda: self.detach(['kcmshell6', 'kcm_powerdevilprofilesconfig']))))
        v.addWidget(c)
        v.addLayout(hrow(button('Save', self.save_power, 'primary')))
        v.addStretch(1)
        return sa

    def load_power(self):
        self.perf = core.perf_conf()
        for b in self.p_modes.buttons():
            b.setChecked(b.property('mode') == self.perf['MODE'])
        i = self.p_batprof.findData(self.perf['BAT_PROFILE'])
        self.p_batprof.setCurrentIndex(max(i, 0))
        self.p_turbo.setChecked(self.perf['BAT_TURBO'] == '1')
        i = self.p_batcap.findData(int(self.perf['BAT_FPS_CAP'] or 0))
        self.p_batcap.setCurrentIndex(max(i, 0))
        bats = core.batteries()
        supported = any(b['limit_supported'] for b in bats)
        i = self.p_limit.findData(int(self.perf['CHARGE_LIMIT'] or 0))
        self.p_limit.setCurrentIndex(max(i, 0))
        self.p_limit.setEnabled(supported)
        self.p_limit_note.setText('' if supported else ('This laptop does not let RustOS set a charge limit.' if bats else
                                                         'No battery: this is a desktop PC.'))
        for w in self.p_bat_widgets:
            w.setEnabled(bool(bats))
        self.refresh_power_live()

    def refresh_power_live(self):
        bats = core.batteries()
        prof = core.power_profile()
        turbo = core.turbo_state()
        temp = core.cpu_temp()
        extra = []
        if bats:
            b = bats[0]
            cap = b['capacity'] or 0
            self.p_pct.setText('%d%%' % cap)
            self.p_bar.setValue(cap)
            self.p_bar.setVisible(True)
            st = {'Discharging': 'On battery', 'Charging': 'Charging', 'Full': 'Full', 'Not charging': 'Plugged in (not charging)'}
            self.p_state.setText(st.get(b['status'], b['status']))
            left = core.time_left(bats)
            self.p_left.setText((('About %s left' if b['status'] == 'Discharging' else 'Full in about %s') % left) if left else '')
            if b['watts'] >= 0.5:
                extra.append('Power use: %.1f W' % sum(x['watts'] for x in bats))
            if b['health']:
                extra.append('Battery health: %d%%' % b['health'])
        else:
            self.p_pct.setText('⚡')
            self.p_bar.setVisible(False)
            self.p_state.setText('Desktop PC')
            self.p_left.setText('No battery: the mode and the game settings still work.')
        extra.append('Profile: %s' % prof)
        extra.append('CPU turbo: %s' % turbo)
        if temp:
            extra.append('CPU: %d °C' % temp)
        self.p_details.setText('   ·   '.join(extra))

    def save_power(self):
        new = dict(self.perf)
        for b in self.p_modes.buttons():
            if b.isChecked():
                new['MODE'] = b.property('mode')
        new['BAT_PROFILE'] = self.p_batprof.currentData()
        new['BAT_TURBO'] = '1' if self.p_turbo.isChecked() else '0'
        new['BAT_FPS_CAP'] = str(self.p_batcap.currentData())
        if self.p_limit.isEnabled():
            new['CHARGE_LIMIT'] = str(self.p_limit.currentData())
        self.save_perf(new, 'Power settings')

    # ---------------------------------------------------------------- Antivirus
    def page_antivirus(self):
        sa, v = self.scroll_page()
        c, cv = card()
        self.av_state = label('…', 'h2')
        self.av_db = label('', 'muted')
        cv.addWidget(self.av_state)
        cv.addWidget(self.av_db)
        self.av_install = button('Install the antivirus', self.av_do_install, 'primary')
        self.av_update = button('Update the virus list', self.av_do_update)
        cv.addLayout(hrow(self.av_install, self.av_update,
                          button('Open the quarantine folder', self.av_open_quarantine)))
        v.addWidget(c)

        c, cv = card('Scan')
        grid = QGridLayout()
        grid.setSpacing(10)
        for i, (text, sub, slot) in enumerate([
                ('Quick scan', 'Downloads, Desktop, Documents', self.scan_quick),
                ('Scan a folder or drive…', 'A USB stick, a game folder…', self.scan_folder),
                ('Scan my home folder', 'Everything that is yours', lambda: self.start_scan([core.HOME], False)),
                ('Scan the whole PC', 'Slow, asks for your password', lambda: self.start_scan(['/'], True))]):
            b = button('%s\n%s' % (text, sub), slot, 'tile')
            b.setMinimumHeight(70)
            grid.addWidget(b, i // 2, i % 2)
        cv.addLayout(grid)
        self.av_progress = label('', 'muted', wrap=True)
        cv.addWidget(self.av_progress)
        v.addWidget(c)

        c, cv = card('Results')
        self.av_result = label('No scan yet.', wrap=True)
        cv.addWidget(self.av_result)
        self.av_list = QListWidget()
        self.av_list.setMinimumHeight(140)
        self.av_list.setVisible(False)
        cv.addWidget(self.av_list)
        self.av_q = button('Lock the ticked files away (quarantine)', lambda: self.av_act('quarantine'), 'primary')
        self.av_del = button('Delete the ticked files', lambda: self.av_act('delete'), 'danger')
        self.av_q.setVisible(False)
        self.av_del.setVisible(False)
        cv.addLayout(hrow(self.av_q, self.av_del))
        v.addWidget(c)

        c, cv = card('What this does and does not do')
        cv.addWidget(label('It uses ClamAV, a well-known open-source scanner. It finds known viruses, including Windows ones hiding in '
                           'downloads or on a USB stick. It is not real-time protection and will miss brand-new malware. '
                           'Install programs from Discover or RustOS Apps, not from random websites. '
                           'Tip: right-click any file or folder and choose "Scan for viruses".', 'muted', wrap=True))
        v.addWidget(c)
        v.addStretch(1)
        return sa

    def load_antivirus(self):
        ready = core.clam_ready()
        if core.is_live():
            self.av_state.setText('Install RustOS first to use the antivirus.')
        else:
            self.av_state.setText('Antivirus is ready' if ready else 'Antivirus is not installed yet')
        self.av_db.setText('Virus list last updated: %s' % core.clam_db_date() if ready else
                           'It downloads a few hundred MB for the virus list. It only runs when you scan.')
        self.av_install.setVisible(not ready)
        self.av_update.setVisible(ready)

    def av_do_install(self, then=None):
        def done(code, out):
            self.load_antivirus()
            if core.clam_ready() and then:
                then()
        self.run('Installing the antivirus', [B + '/rustos-antivirus', '--install'], True, done)

    def av_do_update(self):
        self.run('Updating the virus list', [B + '/rustos-antivirus', '--update'], True, lambda *_: self.load_antivirus())

    def av_open_quarantine(self):
        os.makedirs(core.Q_USER, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(core.Q_USER))

    def scan_quick(self):
        self.start_scan(core.user_dirs(), False)

    def scan_folder(self):
        d = QFileDialog.getExistingDirectory(self, 'Scan which folder?', core.HOME)
        if d:
            self.start_scan([d], False)

    def start_scan(self, paths, root):
        self.go('antivirus')
        if not core.clam_ready():
            if self.ask('The antivirus is not installed yet. It downloads a few hundred MB once.<br>Install it now and then scan?',
                        'Install and scan'):
                self.av_do_install(lambda: self.start_scan(paths, root))
            return
        self.scan_found = []
        self.scan_root = root
        self.scan_count = 0
        self.av_list.clear()
        self.av_list.setVisible(False)
        self.av_q.setVisible(False)
        self.av_del.setVisible(False)
        self.av_result.setText('Scanning: %s' % esc(', '.join(paths)))

        def line(ln):
            if ln.endswith(': OK') or ln.endswith(': Empty file') or ln.endswith(' FOUND'):
                self.scan_count += 1
                if self.scan_count % 25 == 0 or ln.endswith(' FOUND'):
                    self.av_progress.setText('%d files checked · %d found · now: %s' %
                                             (self.scan_count, len(self.scan_found), esc(ln.rsplit(':', 1)[0][-90:])))
            f = core.parse_found(ln)
            if f:
                self.scan_found.append(f)

        def done(code, out):
            self.av_progress.setText('%d files checked.' % self.scan_count)
            if code == -2:
                self.av_result.setText('The scan was stopped. %d infected file(s) found so far.' % len(self.scan_found))
            if self.scan_found:
                self.av_result.setText('<b style="color:#ff7a6b">%d infected file(s) found.</b> What should RustOS do with them? '
                                       'Quarantine is safe and can be undone.' % len(self.scan_found))
                for path, virus in self.scan_found:
                    it = QListWidgetItem('%s\n%s' % (path, virus))
                    it.setData(ROLE, path)
                    it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    it.setCheckState(Qt.CheckState.Checked)
                    self.av_list.addItem(it)
                self.av_list.setVisible(True)
                self.av_q.setVisible(True)
                self.av_del.setVisible(True)
            elif code == 0:
                self.av_result.setText('<b style="color:#5fd38d">No threats found.</b> Everything that was scanned is clean.')
            elif code >= 0:
                self.av_result.setText('The scan had problems (some files could not be read), so it may not be complete. '
                                       'No infected files were found in what was scanned.')

        argv = core.scan_argv(paths)
        self.run('Virus scan', argv, root, done, line=line, show=lambda ln: ln.endswith(' FOUND') or 'SCAN SUMMARY' in ln
                 or ln.startswith(('Infected files', 'Scanned files', 'Time:', 'ERROR', 'WARNING')), cancellable=not root)

    def av_act(self, mode):
        files = [self.av_list.item(i).data(ROLE) for i in range(self.av_list.count())
                 if self.av_list.item(i).checkState() == Qt.CheckState.Checked]
        if not files:
            return
        if mode == 'delete' and not self.ask('Delete %d file(s) for good?' % len(files), 'Delete'):
            return

        def finish(*_):
            left = [f for f in files if os.path.exists(f)]
            self.av_list.clear()
            self.av_list.setVisible(False)
            self.av_q.setVisible(False)
            self.av_del.setVisible(False)
            if left:
                self.av_result.setText('%d file(s) could not be moved (see the log).' % len(left))
            elif mode == 'quarantine':
                self.av_result.setText('Done. The files are locked in %s' % esc(core.Q_ROOT if self.scan_root else core.Q_USER))
            else:
                self.av_result.setText('The infected files were deleted.')
        if self.scan_root:
            fd, lst = tempfile.mkstemp(prefix='rustos-av-', suffix='.txt')
            with os.fdopen(fd, 'w') as f:
                f.write('\n'.join(files) + '\n')
            os.chmod(lst, 0o644)
            self.run('Moving infected files', [B + '/rustos-antivirus', '--act', mode, lst, core.Q_ROOT], True,
                     lambda *a: (finish(), os.remove(lst)))
        else:
            if mode == 'quarantine':
                core.quarantine_user(files)
            else:
                for f in files:
                    try:
                        os.remove(f)
                    except OSError as e:
                        self.log_add('Could not delete %s: %s' % (f, e))
            finish()

    # ---------------------------------------------------------------- Education
    def page_education(self):
        sa, v = self.scroll_page()
        self.edu_checks = {}
        for kind, title, text in [('prog', 'Programs', 'Installed from the internet. Untick does not remove them.'),
                                  ('web', 'Website shortcuts', 'Canva, Google Docs and others have no Linux program, so they get a '
                                                               'menu shortcut that opens them in the browser. Untick to remove one.')]:
            c, cv = card(title, text)
            grid = QGridLayout()
            grid.setHorizontalSpacing(24)
            n = 0
            for item in core.EDU:
                if item[3] != kind:
                    continue
                cb = check(item[1], item[2])
                self.edu_checks[item[0]] = (cb, item)
                grid.addWidget(cb, n // 2, n % 2)
                n += 1
            cv.addLayout(grid)
            v.addWidget(c)
        self.edu_state = label('', 'muted', wrap=True)
        v.addLayout(hrow(button('Apply', self.apply_education, 'primary'), self.edu_state))
        v.addStretch(1)
        return sa

    def load_education(self):
        self.pkgs = self.pkgs or core.installed_packages()
        self.flats = self.flats or core.installed_flatpaks()
        for eid, (cb, item) in self.edu_checks.items():
            inst = core.edu_installed(item, self.pkgs, self.flats)
            cb.setChecked(inst)
            cb.setProperty('was', inst)
            if item[3] == 'prog':
                cb.setEnabled(not inst)
                cb.setText('%s  -  %s%s' % (item[1], item[2], '   ✓ installed' if inst else ''))

    def apply_education(self):
        progs, added, removed = [], [], []
        for eid, (cb, item) in self.edu_checks.items():
            was = bool(cb.property('was'))
            if item[3] == 'web':
                if cb.isChecked() and not was:
                    core.write_webapp(item)
                    added.append(item[1])
                elif was and not cb.isChecked():
                    core.remove_webapp(eid)
                    removed.append(item[1])
            elif cb.isChecked() and not was:
                progs.append(eid)
        if added or removed:
            self.detach(['kbuildsycoca6'])
        msg = []
        if added:
            msg.append('Added to the menu: ' + ', '.join(added))
        if removed:
            msg.append('Removed: ' + ', '.join(removed))
        self.edu_state.setText('. '.join(msg))
        if not progs:
            self.load_education()
            return

        def done(code, out):
            self.pkgs = core.installed_packages()
            self.flats = core.installed_flatpaks()
            self.load_education()
            if code == 0:
                self.edu_state.setText(('. '.join(msg) + '. ' if msg else '') + 'Programs installed: find them in the menu.')
            elif code >= 0:
                self.edu_state.setText('Not everything was installed. The log shows the first error.')
        self.run('Installing study programs', [B + '/rustos-education', '--install'] + progs, True, done)

    # ---------------------------------------------------------------- Look and iPad
    def page_look(self):
        sa, v = self.scroll_page()
        c, cv = card('Colors')
        self.lk_dark = button('Dark', lambda: self.mod('dark', 'on'))
        self.lk_light = button('Light', lambda: self.mod('dark', 'off'))
        cv.addLayout(hrow(label('Theme:'), self.lk_dark, self.lk_light))
        self.lk_swatch = QLabel()
        self.lk_swatch.setFixedSize(28, 28)
        cv.addLayout(hrow(label('Accent color:'), self.lk_swatch, button('Pick a color…', self.pick_accent),
                          button('RustOS orange', lambda: self.mod('accent', 'on', '255,154,60')),
                          button('Default', lambda: self.mod('accent', 'off'))))
        self.lk_anim = check('Animations', 'turn them off for an instant, snappier feel on old PCs and on the iPad')
        self.lk_anim.clicked.connect(lambda: self.mod('noanim', 'off' if self.lk_anim.isChecked() else 'on'))
        cv.addWidget(self.lk_anim)
        v.addWidget(c)

        c, cv = card('Terminal')
        self.lk_prompt = check('Colorful RustOS prompt')
        self.lk_prompt.clicked.connect(lambda: self.mod('prompt', 'on' if self.lk_prompt.isChecked() else 'off'))
        self.lk_banner = check('Show the RustOS logo (fastfetch) when a terminal opens')
        self.lk_banner.clicked.connect(lambda: self.mod('nobanner', 'off' if self.lk_banner.isChecked() else 'on'))
        cv.addWidget(self.lk_prompt)
        cv.addWidget(self.lk_banner)
        v.addWidget(c)

        if core.IS_PC:
            c, cv = card('Boot screen', 'The RustOS logo and a progress bar while the PC starts, and a RustOS boot menu (GRUB).')
            self.lk_boot = label('', 'muted')
            cv.addLayout(hrow(self.lk_boot, None,
                              button('Turn on', lambda: self.run('Boot screen on', [B + '/rustos-bootsplash', 'on'], True,
                                                                 lambda *_: self.load_look()), 'primary'),
                              button('Turn off', lambda: self.run('Boot screen off', [B + '/rustos-bootsplash', 'off'], True,
                                                                  lambda *_: self.load_look())), stretch=False))
            v.addWidget(c)

        c, cv = card('iPad mode', 'An iPad-style desktop: floating dock, app grid, big touch targets and a touch keyboard. '
                                  'Works with a mouse too. "Normal desktop" puts back exactly what you had.')
        self.lk_ipad = label('', 'muted')
        cv.addWidget(self.lk_ipad)
        ip = B + '/rustos-ipad-mode'
        cv.addLayout(hrow(button('iPad mode', lambda: self.ipad(['on']), 'primary'),
                          button('Touch only (keep my desktop)', lambda: self.ipad(['touch'])),
                          button('Normal desktop', lambda: self.ipad(['off'])),
                          button('Touch keyboard', lambda: self.detach([ip, 'keyboard']))))
        v.addWidget(c)
        v.addStretch(1)
        return sa

    def load_look(self):
        st = core.look_state()
        self.lk_dark.setObjectName('primary' if st['dark'] else '')
        self.lk_light.setObjectName('' if st['dark'] else 'primary')
        for b in (self.lk_dark, self.lk_light):
            b.style().unpolish(b)
            b.style().polish(b)
        acc = st['accent'] or ''
        col = 'rgb(%s)' % acc if acc.count(',') == 2 else '#3a4a44'
        self.lk_swatch.setStyleSheet('background: %s; border-radius: 14px; border: 2px solid #33463f;' % col)
        self.lk_anim.setChecked(not st['noanim'])
        bashrc = core.read(os.path.join(core.HOME, '.bashrc'))
        self.lk_prompt.setChecked('# >>> rustos-mod:prompt >>>' in bashrc)
        self.lk_banner.setChecked('# >>> rustos-mod:nobanner >>>' not in bashrc)
        if core.IS_PC:
            self.lk_boot.setText('Now: ' + ('ON' if core.bootsplash_on() else 'off'))
        rc, out = core.sh([core.tool('rustos-ipad-mode'), 'status'], 6)
        self.lk_ipad.setText('Now: ' + (out.strip().splitlines()[0] if out.strip() else 'off'))

    def pick_accent(self):
        st = core.look_state()
        start = QColor(*[int(x) for x in st['accent'].split(',')]) if st['accent'].count(',') == 2 else QColor(255, 154, 60)
        c = QColorDialog.getColor(start, self, 'Accent color')
        if c.isValid():
            self.mod('accent', 'on', '%d,%d,%d' % (c.red(), c.green(), c.blue()))

    def mod(self, name, state, arg=None):
        argv = [B + '/rustos-debug', 'mod', name, state] + ([arg] if arg else [])

        def done(*_):
            self.load_look()
            if 'mods' in self.loaded:
                self.load_mods()
        self.run('%s %s' % (name, state), argv, False, done, show=lambda _l: True)

    def ipad(self, args):
        self.run('iPad mode: ' + args[0], [B + '/rustos-ipad-mode'] + args, False, lambda *_: self.load_look())

    # ---------------------------------------------------------------- Mods
    def page_mods(self):
        sa, v = self.scroll_page()
        c, cv = card(None, 'Mods are small switches. Your own mods are little scripts in ~/.config/rustos/mods with an on() and '
                           'off() part. In a terminal: .debug mods, .debug mod NAME on, .debug mainmod')
        cv.addLayout(hrow(button('Make my own mod', self.new_mod, 'primary'),
                          button('Open my mods folder', self.open_mods), button('Refresh', self.load_mods)))
        v.addWidget(c)
        self.mods_box = QVBoxLayout()
        self.mods_box.setSpacing(8)
        v.addLayout(self.mods_box)
        v.addStretch(1)
        return sa

    def load_mods(self):
        self.bg([B + '/rustos-debug', 'mods'], self.got_mods)

    def got_mods(self, code, text):
        clear_layout(self.mods_box)
        mods = core.parse_mods(text)
        if not mods:
            self.mods_box.addWidget(label('Could not read the mods (is rustos-debug installed?).', 'muted'))
            return
        for name, on, desc in mods:
            fr = QFrame()
            fr.setObjectName('row')
            h = QHBoxLayout(fr)
            h.setContentsMargins(14, 10, 14, 10)
            cb = QCheckBox()
            cb.setChecked(on)
            cb.clicked.connect(lambda checked, n=name: self.toggle_mod(n, checked))
            h.addWidget(cb)
            h.addWidget(label('<b>%s</b><br><span style="color:#a9b8b1">%s</span>' % (esc(name), esc(desc)), wrap=True), 1)
            mine = os.path.exists(os.path.join(core.MODDIR, name + '.sh'))
            if mine:
                h.addWidget(button('Edit', lambda _c=False, n=name: self.detach(['xdg-open', os.path.join(core.MODDIR, n + '.sh')])))
            self.mods_box.addWidget(fr)

    def toggle_mod(self, name, on):
        state = 'on' if on else 'off'
        if name in core.ROOT_MODS:
            cmd = core.ROOT_MODS[name][state]
            if cmd is None:
                self.info('The programming tools stay installed (other apps may need them).')
                self.load_mods()
                return
            self.run('Mod %s %s' % (name, state), cmd, True, lambda *_: self.load_mods())
        elif name == 'ipad':
            self.ipad([state])
        else:
            self.run('Mod %s %s' % (name, state), [B + '/rustos-debug', 'mod', name, state], False, lambda *_: self.load_mods(),
                     show=lambda _l: True)

    def new_mod(self):
        name, ok = QInputDialog.getText(self, TITLE, 'Name for your mod (small letters, numbers, - or _):')
        name = name.strip()
        if not ok or not name:
            return

        def done(code, out):
            self.load_mods()
            f = os.path.join(core.MODDIR, name + '.sh')
            if os.path.exists(f):
                self.detach(['xdg-open', f])
        self.run('Making mod ' + name, [B + '/rustos-debug', 'mod', 'new', name], False, done, show=lambda _l: True)

    def open_mods(self):
        os.makedirs(core.MODDIR, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(core.MODDIR))

    # ---------------------------------------------------------------- Windows apps
    def page_windows(self):
        sa, v = self.scroll_page()
        c, cv = card('RustOS EXE Center', 'Run Windows programs and games (.exe), install setups, runtimes and DLLs.')
        self.w_state = label('', 'muted', wrap=True)
        cv.addWidget(self.w_state)
        self.w_install = button('Install Windows support', self.install_wine)
        cv.addLayout(hrow(button('Open the EXE Center', self.open_exe_center, 'primary'), self.w_install))
        v.addWidget(c)

        c, cv = card('My Windows files', 'Open the files on a Windows drive in this PC (NTFS).')
        self.w_drives = QListWidget()
        self.w_drives.setMaximumHeight(130)
        cv.addWidget(self.w_drives)
        cv.addLayout(hrow(button('Open the drive', self.open_drive, 'primary'), button('Look again', self.load_windows)))
        v.addWidget(c)

        c, cv = card('Find a replacement for a Windows app')
        self.w_find = QLineEdit()
        self.w_find.setPlaceholderText('Type a Windows app, like "Photoshop" or "Notepad++"')
        self.w_find.textChanged.connect(self.find_equivalent)
        self.w_eq = QPlainTextEdit()
        self.w_eq.setReadOnly(True)
        self.w_eq.setMinimumHeight(220)
        cv.addWidget(self.w_find)
        cv.addWidget(self.w_eq)
        v.addWidget(c)

        c, cv = card('Good to know when you switch')
        cv.addWidget(label('&bull; The <b>Windows key</b> opens the menu. Alt+Tab switches windows like in Windows.<br>'
                           '&bull; Install programs from <b>Apps</b> here or from Discover, not from websites.<br>'
                           '&bull; Updates happen by themselves (see <b>Updates</b>).<br>'
                           '&bull; Steam games usually just work. Games with anti-cheat often do not: check protondb.com before you buy.<br>'
                           '&bull; Microsoft Office and Adobe programs do not run well. LibreOffice, GIMP and the web versions replace most of it.',
                           wrap=True))
        v.addWidget(c)
        v.addStretch(1)
        return sa

    def load_windows(self):
        if not core.IS_PC:
            self.w_state.setText('Windows .exe programs need an Intel or AMD PC. This is the ARM edition, so they cannot run here.')
            self.w_install.setVisible(False)
        elif core.wine_ready():
            self.w_state.setText('<span style="color:#5fd38d">Windows support is installed.</span> Double-click any .exe, '
                                 'or right-click it and choose "Run as game" for games.')
            self.w_install.setVisible(False)
        else:
            self.w_state.setText('Windows support (Wine) is not installed yet. It is a few hundred MB, once.')
            self.w_install.setVisible(True)
        self.w_drives.clear()
        for d in core.ntfs_drives():
            it = QListWidgetItem(theme_icon('drive-harddisk'), '%s  %s  (%s)%s' % (d['size'], d['label'], d['dev'],
                                                                                   '  · open' if d['mount'] else ''))
            it.setData(ROLE, d)
            self.w_drives.addItem(it)
        if not self.w_drives.count():
            self.w_drives.addItem('No Windows drives found. (BitLocker-encrypted drives must be unlocked in Windows first.)')
        self.find_equivalent('')

    def find_equivalent(self, q):
        text = core.read(core.EQUIV)
        q = (q or '').strip().lower()
        if q:
            lines = [ln for ln in text.splitlines() if q in ln.lower()]
            text = '\n'.join(lines) if lines else 'Nothing found for "%s". Try another word, or search in Discover.' % q
        self.w_eq.setPlainText(text)

    def open_drive(self):
        it = self.w_drives.currentItem() or (self.w_drives.item(0) if self.w_drives.count() == 1 else None)
        d = it.data(ROLE) if it else None
        if not d:
            return
        if d['mount']:
            QDesktopServices.openUrl(QUrl.fromLocalFile(d['mount']))
            return
        ok, where = core.mount_drive(d['dev'])
        if ok:
            QDesktopServices.openUrl(QUrl.fromLocalFile(where))
            self.load_windows()
        else:
            self.info('Could not open %s.<br><br>%s<br><br>If it says the drive is in use or hibernated, Windows did not shut down fully '
                      '(Fast Startup). In Windows hold <b>Shift</b> while clicking Shut down.' % (esc(d['dev']), esc(where)))

    def open_exe_center(self):
        self.detach([B + '/rustos-exe-center'])

    def install_wine(self):
        self.run('Installing Windows support', [B + '/rustos-gaming', '--install', 'wine'], True, lambda *_: self.load_windows())

    # ---------------------------------------------------------------- Hardware dev (FPGA boards, DMA devices)
    def page_devhw(self):
        sa, v = self.scroll_page()
        c, cv = card(None, 'For people who build or test real hardware: FPGA boards and DMA-capable PCIe cards. '
                           'This checks what your PC and its Linux kernel support and sets up safe access. '
                           'It does not replace hardware: you still need the board or card and its driver.')
        self.dh_sum = label('', 'h2')
        cv.addLayout(hrow(button('Run the check', self.load_devhw, 'primary'), button('Copy the report', self.devhw_copy),
                          button('Read the guide', self.devhw_guide), self.dh_sum))
        v.addWidget(c)

        c, cv = card('Status', 'supported = works as far as RustOS can check · unavailable = missing or off (with a fix) · '
                               'untested = needs your hardware or driver to really test it')
        self.dh_tree = QTreeWidget()
        self.dh_tree.setHeaderLabels(['', 'What', 'Result', 'How to fix'])
        self.dh_tree.setRootIsDecorated(False)
        self.dh_tree.setMinimumHeight(300)
        self.dh_tree.setWordWrap(True)
        cv.addWidget(self.dh_tree)
        self.dh_iommu_btn = button('Turn on the IOMMU (Intel)', self.devhw_iommu_on,
                                   tip='Adds intel_iommu=on to the kernel options. VT-d must also be on in the firmware settings.')
        self.dh_iommu_btn.setVisible(False)
        cv.addLayout(hrow(self.dh_iommu_btn))
        v.addWidget(c)

        c, cv = card('PCIe devices and VFIO', 'VFIO gives one PCIe device to a program (a user-space driver) or a development VM. '
                                             'RustOS only does it with the IOMMU on, so the device can only reach the memory it is given. '
                                             'Bridges, the screen\'s graphics card and disks in use are never given away.')
        self.dh_pci = QTreeWidget()
        self.dh_pci.setHeaderLabels(['Slot', 'Device', 'Driver', 'IOMMU group', 'VFIO'])
        self.dh_pci.setRootIsDecorated(False)
        self.dh_pci.setMinimumHeight(220)
        self.dh_pci.currentItemChanged.connect(lambda *_: self.devhw_pick())
        cv.addWidget(self.dh_pci)
        self.dh_why = label('', 'muted', wrap=True)
        cv.addWidget(self.dh_why)
        self.dh_bind = button('Give to VFIO', lambda: self.devhw_vfio('bind'), 'primary', 'Until the next restart')
        self.dh_release = button('Give back', lambda: self.devhw_vfio('release'))
        self.dh_keep = button('Do it at every start', lambda: self.devhw_vfio('keep'))
        self.dh_forget = button('Stop doing it at start', lambda: self.devhw_vfio('forget'))
        cv.addLayout(hrow(self.dh_bind, self.dh_release, self.dh_keep, self.dh_forget))
        v.addWidget(c)

        c, cv = card('FPGA boards and adapters (USB)', 'JTAG cables and debug probes work for whoever is logged in at this PC. '
                                                     'Board serial consoles (/dev/ttyUSB, /dev/ttyACM) need the uucp group once.')
        self.dh_usb = label('', wrap=True)
        cv.addWidget(self.dh_usb)
        self.dh_vfio_access = check('Also let me open devices given to VFIO without sudo',
                                    'adds the rustos-vfio group and a bigger locked-memory limit for DMA buffers')
        cv.addWidget(self.dh_vfio_access)
        cv.addLayout(hrow(button('Set up board access for me', self.devhw_access, 'primary')))
        v.addWidget(c)

        c, cv = card('FPGA tools', 'Open-source tools from the Arch repositories. nextpnr is not in the Arch repositories: '
                                   'use the OSS CAD Suite or the AUR (the guide explains it). Vendor tools (Vivado, Quartus, '
                                   'Radiant, Gowin EDA) are separate downloads from the vendor.')
        self.dh_tools = {}
        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        for i, (tid, cmd, what, note) in enumerate(core.FPGA_TOOLS):
            cb = check('%s  -  %s' % (cmd, what))
            cb.setToolTip(note)
            self.dh_tools[tid] = (cb, cmd)
            grid.addWidget(cb, i // 2, i % 2)
        cv.addLayout(grid)
        cv.addLayout(hrow(button('Install the ticked tools', self.devhw_install_tools, 'primary')))
        v.addWidget(c)

        c, cv = card('Developer kernel (LTS)', 'Linux LTS with its headers and DKMS. Vendor DMA drivers and your own kernel modules '
                                               'are usually tested against LTS kernels. The normal kernel stays in the boot menu.')
        self.dh_kernel = label('', wrap=True)
        cv.addWidget(self.dh_kernel)
        self.dh_lts_btn = button('Use the LTS developer kernel', self.devhw_lts, 'primary')
        cv.addLayout(hrow(self.dh_lts_btn, button('Back to the normal kernel', self.devhw_kernel_default),
                          button('Rebuild DKMS modules', self.devhw_dkms_build)))
        v.addWidget(c)
        v.addStretch(1)
        return sa

    def load_devhw(self):
        self.dh_sum.setText('Checking…')
        self.bg([core.tool('rustos-devhw'), 'check', '--machine'], self.got_devhw)
        self.load_devhw_static()

    def load_devhw_static(self):
        self.pkgs = self.pkgs or core.installed_packages()
        for tid, (cb, cmd) in self.dh_tools.items():
            inst = core.have(cmd) or tid in self.pkgs
            cb.setChecked(inst)
            cb.setEnabled(not inst)
            cb.setProperty('was', inst)
        k = core.kernel_info()
        txt = 'Running: <b>%s</b> (%s) · headers: %s · DKMS: %s' % (
            esc(k['running']), esc(k['pkgbase']), 'yes' if k['headers'] else '<span style="color:#ff7a6b">no</span>',
            'installed' if k['dkms'] else 'not installed')
        if k['lts_running']:
            txt += '<br><span style="color:#5fd38d">The LTS developer kernel is running.</span>'
        elif k['lts_installed']:
            txt += '<br>The LTS developer kernel is installed. Restart to use it.'
        self.dh_kernel.setText(txt)
        self.dh_lts_btn.setEnabled(core.IS_PC and not k['lts_installed'])

    def got_devhw(self, code, text):
        d = core.parse_devhw(text)
        self.devhw = d
        self.dh_tree.clear()
        colors = {'supported': '#5fd38d', 'unavailable': '#ff7a6b', 'untested': '#ffcc66', 'info': '#a9b8b1'}
        marks = {'supported': '✓', 'unavailable': '✗', 'untested': '?', 'info': '·'}
        for ch in d['checks']:
            it = QTreeWidgetItem([marks[ch['status']], ch['item'], ch['text'], ch['fix']])
            it.setForeground(0, QColor(colors[ch['status']]))
            it.setToolTip(2, ch['text'])
            it.setToolTip(3, ch['fix'])
            self.dh_tree.addTopLevelItem(it)
        for col in (0, 1):
            self.dh_tree.resizeColumnToContents(col)
        if d['summary']:
            self.dh_sum.setText('%d supported · %d unavailable · %d untested' % d['summary'])
        elif not d['checks']:
            self.dh_sum.setText('The check did not run (is rustos-devhw installed?)')
        iommu = core.devhw_check(d, 'IOMMU')
        self.dh_iommu_btn.setVisible(iommu == 'unavailable' and core.cpu_vendor() == 'intel' and core.IS_PC)
        self.dh_pci.clear()
        for p in d['pci']:
            vf = {'yes': 'can be given', 'bound': 'given to VFIO', 'no': 'no'}.get(p['vfio'], p['vfio'])
            if p['kept']:
                vf += ' (at every start)'
            it = QTreeWidgetItem([p['slot'], '%s [%s]' % (p['name'], p['ids']), p['driver'] or '(none)', p['group'] or '-', vf])
            it.setData(0, ROLE, p)
            if p['why']:
                it.setToolTip(4, p['why'])
            self.dh_pci.addTopLevelItem(it)
        for col in range(5):
            self.dh_pci.resizeColumnToContents(col)
        if not d['pci']:
            self.dh_why.setText('No PCIe devices are visible (a virtual machine, or lspci is missing: see the status list).')
        self.devhw_pick()
        if d['usb']:
            self.dh_usb.setText('<br>'.join('%s <b>%s</b> [%s]' % ('✓' if u['access'] == 'yes' else '✗' if u['access'] == 'no' else '?',
                                                                  esc(u['name']), esc(u['ids'])) for u in d['usb']))
        else:
            self.dh_usb.setText('No known FPGA cable or debug probe is plugged in right now.')

    def devhw_selected(self):
        it = self.dh_pci.currentItem()
        return it.data(0, ROLE) if it else None

    def devhw_pick(self):
        p = self.devhw_selected()
        ok = bool(p)
        self.dh_bind.setEnabled(ok and p['vfio'] == 'yes')
        self.dh_keep.setEnabled(ok and p['vfio'] in ('yes', 'bound') and not p['kept'])
        self.dh_release.setEnabled(ok and p['vfio'] == 'bound')
        self.dh_forget.setEnabled(ok and p['kept'])
        if p:
            self.dh_why.setText(('VFIO: not possible: ' + p['why']) if p['vfio'] == 'no' else
                                'Driver modules: %s' % (p['modules'] or 'none listed'))

    def devhw_vfio(self, action):
        p = self.devhw_selected()
        if not p:
            return
        if action in ('bind', 'keep') and not self.ask(
                'Give <b>%s</b> (%s) to VFIO?<br><br>Its normal driver lets go of it, so the system stops using it '
                'until you give it back or restart. Programs and VMs you allow can then drive it, protected by the IOMMU.'
                % (esc(p['slot']), esc(p['name'])), 'Give to VFIO'):
            return
        self.run('VFIO %s %s' % (action, p['slot']), [core.tool('rustos-devhw'), 'vfio', action, p['slot']], True,
                 lambda *_: self.load_devhw(), show=lambda _l: True)

    def devhw_access(self):
        argv = [core.tool('rustos-devhw'), 'access'] + (['--vfio'] if self.dh_vfio_access.isChecked() else []) + [USER]

        def done(code, out):
            if code == 0:
                self.info('Board access is set up. <b>Log out and in once</b> so it applies.')
            self.load_devhw()
        self.run('Setting up board access', argv, True, done, show=lambda _l: True)

    def devhw_install_tools(self):
        ids = [tid for tid, (cb, _c) in self.dh_tools.items() if cb.isChecked() and not cb.property('was')]
        if not ids:
            self.info('Tick the tools you want first.')
            return

        def done(code, out):
            self.pkgs = core.installed_packages()
            self.load_devhw_static()
            if code == 0:
                self.busy_label.setText('FPGA tools installed.')
        self.run('Installing FPGA tools', [B + '/rustos-apps', '--install'] + ids, True, done)

    def devhw_lts(self):
        if not self.ask('<b>Install the LTS developer kernel?</b><br><br>It installs linux-lts, its headers and DKMS '
                        '(about 200 MB), builds your DKMS modules for it and makes it the default in the boot menu. '
                        'The normal kernel stays in the menu as a backup.', 'Install'):
            return
        self.run('Installing the LTS developer kernel', [B + '/rustos-performance', 'kernel', 'lts'], True,
                 lambda *_: self.load_devhw_static())

    def devhw_kernel_default(self):
        if not self.ask('Go back to the normal kernel? The extra kernels (LTS, zen) that are not running are removed.', 'Back to normal'):
            return
        self.run('Going back to the normal kernel', [B + '/rustos-performance', 'kernel', 'default'], True,
                 lambda *_: self.load_devhw_static())

    def devhw_dkms_build(self):
        self.run('Building DKMS modules', [core.tool('rustos-devhw'), 'dkms', 'build'], True, lambda *_: self.load_devhw())

    def devhw_iommu_on(self):
        if not self.ask('Add <tt>intel_iommu=on</tt> to the kernel options?<br><br>Turn on <b>VT-d</b> in the firmware settings too, '
                        'then restart. RustOS keeps full DMA translation (it does not add iommu=pt).', 'Turn on'):
            return
        self.run('Turning on the IOMMU', [core.tool('rustos-devhw'), 'iommu-on'], True, lambda *_: self.load_devhw(),
                 show=lambda _l: True)

    def devhw_copy(self):
        rc, out = core.sh([core.tool('rustos-devhw'), 'check'], 60)
        QGuiApplication.clipboard().setText(out)
        self.busy_label.setText('The hardware report is copied. Paste it when you ask for help.')

    def devhw_guide(self):
        self.text_dialog('Hardware development guide', core.read(core.SHARE + '/hardware-dev.txt', 'The guide is missing. Run a RustOS update.'))

    # ---------------------------------------------------------------- System
    def page_system(self):
        sa, v = self.scroll_page()
        c, cv = card('Self-test', 'Checks updates, the boot loader, graphics, sound, network, the antivirus and more in a few seconds.')
        self.s_result = label('', 'h2')
        cv.addLayout(hrow(button('Run the self-test', self.selftest, 'primary'), self.s_result))
        v.addWidget(c)

        c, cv = card('Quick fixes', 'One click for the most common problems. Fixes marked 🔒 ask for your password.')
        grid = QGridLayout()
        grid.setSpacing(10)
        for i, (fid, text, what, root) in enumerate(core.FIXES):
            b = button(('🔒 ' if root else '') + text, lambda _c=False, f=fid, r=root, t=text: self.fix(f, r, t), tip=what)
            b.setMinimumHeight(44)
            grid.addWidget(b, i // 4, i % 4)
        cv.addLayout(grid)
        v.addWidget(c)

        c, cv = card('About this PC')
        self.s_info = QPlainTextEdit()
        self.s_info.setReadOnly(True)
        self.s_info.setMinimumHeight(240)
        cv.addWidget(self.s_info)
        cv.addLayout(hrow(button('Make a report for help', self.report),
                          button('Open the debug menu (terminal)', lambda: self.terminal(B + '/rustos-debug mainmod')),
                          button('Open the classic menus', lambda: self.detach([B + '/rustos-update-center']))))
        v.addWidget(c)
        v.addStretch(1)
        return sa

    def load_system(self):
        self.s_info.setPlainText('Loading…')
        self.bg([B + '/rustos-debug', 'info'], lambda c, t: self.s_info.setPlainText(t.strip() or 'No information.'))

    def selftest(self):
        def done(code, out):
            s = core.selftest_summary(out)
            if s:
                p, w, f = s
                self.s_result.setText('%d passed · %d warnings · %d failed' % s)
                set_kind(self.s_result, 'bad' if f else 'warn' if w else 'ok')
                val, sub = self.stats['safety']
                val.setText('%d / %d OK' % (p, p + w + f))
                sub.setText('%d warnings, %d failed' % (w, f))
            else:
                self.s_result.setText('The self-test did not finish (see the log).')
        self.run('Self-test', [B + '/rustos-debug', 'selftest'], False, done)

    def fix(self, fid, root, text):
        self.run('Fix: ' + text, [B + '/rustos-debug', 'fix', fid], root, show=lambda _l: True)

    def report(self):
        def done(code, out):
            for ln in out.splitlines():
                if 'Saved:' in ln:
                    path = ln.split('Saved:', 1)[1].strip()
                    self.info('The report is saved in<br><tt>%s</tt><br><br>Send that file when you ask for help (Discord). '
                              'It has no passwords in it.' % esc(path))
                    QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(path)))
                    return
        self.run('Making a report', [B + '/rustos-debug', 'report'], False, done)

    # ---------------------------------------------------------------- closing
    def closeEvent(self, e):
        if self.job and self.job['root']:
            if not self.ask('"%s" is still running. It keeps running in the background if you close this window.<br>Close anyway?'
                            % self.job['title'], 'Close'):
                e.ignore()
                return
        elif self.job:
            self.job['proc'].kill()
        e.accept()


def main():
    args = sys.argv[1:]
    page, scan = 'home', None
    if '--page' in args:
        i = args.index('--page')
        page = args[i + 1] if i + 1 < len(args) else 'home'
    if '--scan' in args:
        i = args.index('--scan')
        scan = [a for a in args[i + 1:] if not a.startswith('--')]
        page = 'antivirus'
    app = QApplication(sys.argv)
    app.setApplicationName(TITLE)
    app.setDesktopFileName('rustos-center')
    app.setStyleSheet(STYLE)

    # only one window: a second start just shows the page in the open window
    sock_name = 'rustos-center-%d' % os.getuid()
    s = QLocalSocket()
    s.connectToServer(sock_name)
    if s.waitForConnected(300):
        s.write(('%s\n%s' % (page, '\t'.join(scan or []))).encode())
        s.flush()
        s.waitForBytesWritten(500)
        s.disconnectFromServer()
        return 0
    QLocalServer.removeServer(sock_name)
    server = QLocalServer()
    server.listen(sock_name)

    w = Main(page, scan)

    def incoming():
        c = server.nextPendingConnection()
        if not c:
            return

        def got():
            data = bytes(c.readAll()).decode('utf-8', 'replace').split('\n')
            w.go(data[0] or 'home')
            if len(data) > 1 and data[1]:
                w.start_scan(data[1].split('\t'), False)
            w.showNormal()
            w.raise_()
            w.activateWindow()
        c.readyRead.connect(got)
    server.newConnection.connect(incoming)
    w.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
