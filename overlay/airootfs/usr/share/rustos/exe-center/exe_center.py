#!/usr/bin/env python3
"""RustOS EXE Center: the window. Run Windows programs and games on RustOS (through Wine).
Start it from the menu ("RustOS EXE Center") or run  rustos-exe-center . The old menu is  rustos-exe-center --classic ."""
import os
import shlex
import shutil
import sys
import time
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exe_core as core  # noqa: E402

from PyQt6.QtCore import QProcess, QProcessEnvironment, QSize, Qt, QTimer, QUrl, QFileSystemWatcher  # noqa: E402
from PyQt6.QtGui import QDesktopServices, QFont, QIcon, QPixmap, QTextCursor  # noqa: E402
from PyQt6.QtWidgets import (  # noqa: E402
    QAbstractItemView, QApplication, QCheckBox, QFileDialog, QFrame, QGridLayout, QGroupBox, QHBoxLayout,
    QInputDialog, QLabel, QLineEdit, QListView, QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
    QPlainTextEdit, QPushButton, QSizePolicy, QSplitter, QStackedWidget, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget,
)

TITLE = 'RustOS EXE Center'
ROLE = Qt.ItemDataRole.UserRole

STYLE = """
QWidget { background: #121d1a; color: #e9ede8; font-size: 14px; }
QMainWindow::separator { background: #26382f; width: 1px; height: 1px; }
QLabel#h1 { font-size: 22px; font-weight: 800; }
QLabel#h2 { font-size: 18px; font-weight: 800; color: #ff9a3c; }
QLabel#muted { color: #a9b8b1; }
QLabel#pill { background: #1b2a26; border: 1px solid #33463f; border-radius: 12px; padding: 4px 12px; color: #a9b8b1; }
QListWidget#side { background: #0d1513; border: none; padding-top: 8px; outline: 0; }
QListWidget#side::item { padding: 11px 12px; margin: 2px 8px; border-radius: 9px; }
QListWidget#side::item:selected { background: #26382f; color: #ffffff; }
QListWidget#side::item:hover { background: #1b2a26; }
QPushButton { background: #26382f; border: 1px solid #33463f; padding: 8px 14px; border-radius: 9px; }
QPushButton:hover { background: #30463c; }
QPushButton:pressed { background: #1b2a26; }
QPushButton:disabled { color: #6b7873; }
QPushButton#primary { background: #ff9a3c; color: #121d1a; font-weight: 800; border: none; }
QPushButton#primary:hover { background: #ffb066; }
QPushButton#danger { background: #4a1f1b; border-color: #7a2e27; }
QPushButton#tool { text-align: left; padding: 14px 16px; }
QLineEdit { background: #1b2a26; border: 1px solid #33463f; border-radius: 9px; padding: 8px 10px; }
QLineEdit:focus { border-color: #ff9a3c; }
QListWidget#grid { background: #121d1a; border: none; outline: 0; }
QListWidget#grid::item { border-radius: 12px; padding: 6px; color: #e9ede8; }
QListWidget#grid::item:selected { background: #26382f; border: 1px solid #ff9a3c; }
QListWidget#grid::item:hover { background: #1b2a26; }
QListWidget, QTreeWidget { background: #1b2a26; border: 1px solid #26382f; border-radius: 10px; outline: 0; }
QListWidget::item, QTreeWidget::item { padding: 6px; }
QListWidget::item:selected, QTreeWidget::item:selected { background: #30463c; color: #ffffff; }
QHeaderView::section { background: #1b2a26; color: #a9b8b1; border: none; padding: 6px; }
QPlainTextEdit#log { background: #0a100e; color: #cfd9d4; font-family: monospace; font-size: 12px; border: none; border-top: 1px solid #26382f; }
QFrame#banner { background: #3a2412; border: 1px solid #ff9a3c; border-radius: 12px; }
QFrame#card { background: #1b2a26; border: 1px solid #26382f; border-radius: 14px; }
QGroupBox { border: 1px solid #26382f; border-radius: 12px; margin-top: 16px; padding: 14px 12px 10px; }
QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 4px; color: #ff9a3c; font-weight: 700; }
QCheckBox { spacing: 8px; }
QStatusBar { background: #0d1513; color: #a9b8b1; }
QScrollBar:vertical { background: transparent; width: 10px; }
QScrollBar::handle:vertical { background: #33463f; border-radius: 5px; min-height: 30px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
QToolTip { background: #1b2a26; color: #e9ede8; border: 1px solid #33463f; }
"""


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
    return lab


class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        core.make_folders()
        self.cfg = core.load_config()
        self.procs = []
        self.programs = []
        self.icon_queue = []
        self.file_trees = {}
        self.setWindowTitle(TITLE)
        self.setWindowIcon(theme_icon('rustos', 'wine'))
        self.resize(1180, 760)
        self.setAcceptDrops(True)

        root = QWidget()
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ---- sidebar
        self.side = QListWidget()
        self.side.setObjectName('side')
        self.side.setFixedWidth(220)
        self.side.setIconSize(QSize(22, 22))
        pages = [('Library', ('applications-games', 'wine')), ('Setups', ('system-software-install',)),
                 ('Runtimes', ('package-x-generic', 'application-x-archive')), ('DLLs', ('application-x-sharedlib', 'text-x-script')),
                 ('Tools', ('preferences-system', 'configure')), ('Help', ('help-about', 'help-contents'))]
        for name, icons in pages:
            self.side.addItem(QListWidgetItem(theme_icon(*icons), name))
        self.side.currentRowChanged.connect(self.show_page)
        outer.addWidget(self.side)

        # ---- right side
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(18, 14, 18, 0)
        rv.setSpacing(10)
        outer.addWidget(right, 1)

        top = QHBoxLayout()
        self.title = label('Library', 'h1')
        top.addWidget(self.title)
        top.addStretch(1)
        self.search = QLineEdit()
        self.search.setPlaceholderText('Search your programs…')
        self.search.setClearButtonEnabled(True)
        self.search.setFixedWidth(280)
        self.search.textChanged.connect(self.filter_grid)
        top.addWidget(self.search)
        top.addWidget(button('Add files', self.add_files, 'primary', 'Setups, runtimes, DLLs and programs are sorted for you'))
        top.addWidget(button('Add a folder', self.add_folder, tip='A whole game or program folder'))
        top.addWidget(button('Run any .exe', self.run_any))
        self.stop_btn = button('Stop all', self.stop_all, 'danger', 'Close every running Windows program')
        top.addWidget(self.stop_btn)
        rv.addLayout(top)

        # banner when Wine is missing
        self.banner = QFrame()
        self.banner.setObjectName('banner')
        bl = QHBoxLayout(self.banner)
        bl.addWidget(label('<b>Windows support is not installed yet.</b> RustOS runs .exe files with Wine. '
                           'Install it once (a few hundred MB) and every program here works with one click.', wrap=True), 1)
        bl.addWidget(button('Install Windows support', self.install_wine, 'primary'))
        rv.addWidget(self.banner)

        self.stack = QStackedWidget()
        rv.addWidget(self.stack, 1)
        self.stack.addWidget(self.page_library())
        self.stack.addWidget(self.page_files('Setups', core.SETUPS, ('.exe', '.msi', '.bat'),
                                             'Installers, like "cs1.6 setup.exe". Pick one and press Install.', 'Install'))
        self.stack.addWidget(self.page_runtimes())
        self.stack.addWidget(self.page_dlls())
        self.stack.addWidget(self.page_tools())
        self.stack.addWidget(self.page_help())

        # log
        self.log = QPlainTextEdit()
        self.log.setObjectName('log')
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(4000)
        self.log.setFixedHeight(170)
        self.log.setVisible(bool(self.cfg.get('show_log')))
        rv.addWidget(self.log)

        self.setCentralWidget(root)
        self.status = self.statusBar()
        self.log_btn = button('Show log', self.toggle_log)
        self.log_btn.setFlat(True)
        self.status.addPermanentWidget(self.log_btn)
        self.wine_label = label('', 'muted')
        self.status.addPermanentWidget(self.wine_label)

        # keep the library fresh when a setup adds a menu entry
        self.watch = QFileSystemWatcher(self)
        for d in (core.WINEMENU, core.PROGS):
            os.makedirs(d, exist_ok=True)
            self.watch.addPath(d)
        self.watch.directoryChanged.connect(lambda _p: self.refresh_soon())
        self.refresh_timer = QTimer(self, singleShot=True, interval=800)
        self.refresh_timer.timeout.connect(self.refresh_all)
        self.tick = QTimer(self, interval=3000)
        self.tick.timeout.connect(self.update_running)
        self.tick.start()
        self.icon_timer = QTimer(self, interval=30)
        self.icon_timer.timeout.connect(self.load_next_icon)

        self.side.setCurrentRow(0)
        self.refresh_all()

    # ------------------------------------------------------------ pages
    def page_library(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        split = QSplitter(Qt.Orientation.Horizontal)
        lay.addWidget(split)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        self.grid = QListWidget()
        self.grid.setObjectName('grid')
        self.grid.setViewMode(QListView.ViewMode.IconMode)
        self.grid.setIconSize(QSize(64, 64))
        self.grid.setGridSize(QSize(150, 132))
        self.grid.setResizeMode(QListView.ResizeMode.Adjust)
        self.grid.setMovement(QListView.Movement.Static)
        self.grid.setWordWrap(True)
        self.grid.setSpacing(6)
        self.grid.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.grid.itemDoubleClicked.connect(lambda it: self.run_selected())
        self.grid.currentItemChanged.connect(lambda cur, _prev: self.show_details())
        ll.addWidget(self.grid, 1)
        self.empty = label('<div style="font-size:18px"><b>Your library is empty</b></div><br>'
                           'Drag .exe files or a whole game folder onto this window,<br>'
                           'or open <b>Setups</b> to install a program like <i>cs1.6 setup.exe</i>.', 'muted')
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ll.addWidget(self.empty, 1)
        split.addWidget(left)

        # details
        self.details = QFrame()
        self.details.setObjectName('card')
        self.details.setMinimumWidth(330)
        dv = QVBoxLayout(self.details)
        dv.setContentsMargins(18, 18, 18, 18)
        self.d_icon = QLabel()
        self.d_icon.setFixedSize(96, 96)
        self.d_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dv.addWidget(self.d_icon)
        self.d_name = label('', 'h2', wrap=True)
        dv.addWidget(self.d_name)
        self.d_meta = label('', 'muted', wrap=True)
        self.d_meta.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        dv.addWidget(self.d_meta)
        row = QHBoxLayout()
        row.addWidget(button('▶  Run', self.run_selected, 'primary'))
        row.addWidget(button('🎮  Run as game', lambda: self.run_selected(game=True), tip='GameMode + FPS overlay'))
        dv.addLayout(row)
        row2 = QGridLayout()
        self.fav_btn = button('☆ Favourite', self.toggle_fav)
        row2.addWidget(self.fav_btn, 0, 0)
        row2.addWidget(button('Rename', self.rename), 0, 1)
        row2.addWidget(button('Open folder', self.open_folder), 1, 0)
        self.menu_btn = button('Add to app menu', self.add_to_menu)
        row2.addWidget(self.menu_btn, 1, 1)
        row2.addWidget(button('Open log', self.open_prog_log), 2, 0)
        row2.addWidget(button('Hide', self.hide_prog, tip='Remove it from the library (the files stay)'), 2, 1)
        dv.addLayout(row2)

        box = QGroupBox('Settings for this program')
        bv = QVBoxLayout(box)
        self.s_game = QCheckBox('Always run as a game (GameMode + MangoHud)')
        self.s_hud = QCheckBox('Show FPS (DXVK games)')
        self.s_log = QCheckBox('Save Wine errors to a log (for fixing problems)')
        self.s_nowarn = QCheckBox("Don't warn me about anti-cheat")
        for c in (self.s_game, self.s_hud, self.s_log, self.s_nowarn):
            c.toggled.connect(self.save_settings)
            bv.addWidget(c)
        bv.addWidget(label('Extra start options (for example  -game cstrike  or  -windowed)', 'muted', wrap=True))
        self.s_args = QLineEdit()
        self.s_args.setPlaceholderText('none')
        self.s_args.editingFinished.connect(self.save_settings)
        bv.addWidget(self.s_args)
        dv.addWidget(box)
        dv.addStretch(1)
        split.addWidget(self.details)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 1)
        return w

    def page_files(self, name, folder, exts, hint, action):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(label(hint, 'muted', wrap=True))
        tree = QTreeWidget()
        tree.setHeaderLabels(['File', 'Size', 'Type'])
        tree.setRootIsDecorated(False)
        tree.setColumnWidth(0, 520)
        tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        tree.itemDoubleClicked.connect(lambda it, _c: self.install_files([it.data(0, ROLE)]))
        v.addWidget(tree, 1)
        row = QHBoxLayout()
        row.addWidget(button(f'{action} selected', lambda: self.install_files(
            [i.data(0, ROLE) for i in tree.selectedItems()]), 'primary'))
        row.addWidget(button('Add files…', self.add_files))
        row.addWidget(button('Open the folder', lambda: self.open_path(folder)))
        row.addStretch(1)
        v.addLayout(row)
        self.file_trees[name] = (tree, folder, exts)
        return w

    def page_runtimes(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        top = QHBoxLayout()
        mine = QGroupBox('From your files (Runtimes folder)')
        mv = QVBoxLayout(mine)
        self.rt_tree = QTreeWidget()
        self.rt_tree.setHeaderLabels(['File', 'Size', 'Bits'])
        self.rt_tree.setRootIsDecorated(False)
        self.rt_tree.setColumnWidth(0, 300)
        self.rt_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        mv.addWidget(self.rt_tree, 1)
        r = QHBoxLayout()
        r.addWidget(button('Install selected', lambda: self.install_files(
            [i.data(0, ROLE) for i in self.rt_tree.selectedItems()]), 'primary'))
        r.addWidget(button('Open the folder', lambda: self.open_path(core.RUNTIMES)))
        r.addStretch(1)
        mv.addLayout(r)
        top.addWidget(mine, 1)

        dl = QGroupBox('Download for me (official sources, via winetricks)')
        dv = QVBoxLayout(dl)
        self.extra_boxes = []
        for verb, title, desc, default in core.EXTRAS:
            c = QCheckBox(f'{title}  —  {desc}')
            c.setChecked(default)
            c.setProperty('verb', verb)
            dv.addWidget(c)
            self.extra_boxes.append(c)
        dv.addStretch(1)
        dv.addWidget(button('Download and install ticked', self.install_extras, 'primary'))
        top.addWidget(dl, 1)
        v.addLayout(top, 1)
        v.addWidget(label('Most programs need none of these. Add them when a program asks for one, '
                          'for example "VCRUNTIME140.dll is missing" means Visual C++.', 'muted', wrap=True))
        return w

    def page_dlls(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(label('Extra .dll files a program asks for. "For all programs" puts it into Windows and tells Wine to use it; '
                          '"Next to a program" copies it into that program\'s folder.', 'muted', wrap=True))
        self.dll_tree = QTreeWidget()
        self.dll_tree.setHeaderLabels(['File', 'Bits', 'Size'])
        self.dll_tree.setRootIsDecorated(False)
        self.dll_tree.setColumnWidth(0, 420)
        self.dll_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        v.addWidget(self.dll_tree, 1)
        row = QHBoxLayout()
        row.addWidget(button('Install for all programs', lambda: self.install_dlls('windows'), 'primary'))
        row.addWidget(button('Install next to a program…', lambda: self.install_dlls('folder')))
        row.addWidget(button('Add DLL…', self.add_files))
        row.addWidget(button('Open the folder', lambda: self.open_path(core.DLLS)))
        row.addStretch(1)
        v.addLayout(row)
        return w

    def page_tools(self):
        w = QWidget()
        g = QGridLayout(w)
        g.setContentsMargins(0, 0, 0, 0)
        g.setSpacing(12)
        tools = [
            ('Windows C: drive', 'Open the files of the Windows environment', lambda: self.open_path(os.path.join(core.PREFIX, 'drive_c'))),
            ('EXE Center folder', 'Your Setups, Runtimes, DLLs and Programs', lambda: self.open_path(core.ROOT)),
            ('Windows settings', 'Windows version, graphics, audio (winecfg)', lambda: self.wine_tool(['winecfg'])),
            ('Uninstall a Windows program', 'The Windows "Add or remove programs"', lambda: self.wine_tool(['wine', 'uninstaller'])),
            ('Will my program work?', 'Look it up on WineHQ and ProtonDB', self.compat),
            ('Stop all Windows programs', 'When something hangs', self.stop_all),
            ('Task manager', 'Windows programs running inside Wine', lambda: self.wine_tool(['wine', 'taskmgr'])),
            ('Windows registry', 'For experts (regedit)', lambda: self.wine_tool(['wine', 'regedit'])),
            ('Reset the Windows environment', 'Start fresh. Your old one is kept as a backup', self.reset_env),
            ('Remove Windows support', 'Uninstall Wine (about 1 GB). Your files stay', self.remove_wine),
            ('Classic menu', 'The old EXE Center menu', lambda: QProcess.startDetached('/usr/local/bin/rustos-exe-center', ['--classic'])),
            ('Environment info', 'Wine version, size, folders', self.env_info),
        ]
        for i, (title, desc, fn) in enumerate(tools):
            b = QPushButton(f'{title}\n{desc}')
            b.setObjectName('tool')
            b.setMinimumHeight(70)
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            b.clicked.connect(fn)
            g.addWidget(b, i // 2, i % 2)
        g.setRowStretch(len(tools) // 2 + 1, 1)
        return w

    def page_help(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        t = label(
            '<p><b>How it works.</b> Linux cannot run Windows programs by itself. RustOS runs them with <b>Wine</b> '
            '(and Steam games with <b>Proton</b>). The EXE Center keeps your setups, runtimes, DLLs and programs in one place: '
            '<tt>' + core.ROOT + '</tt></p>'
            '<p><b>Quick start.</b> Drag a setup or a game folder onto this window. Setups appear under <b>Setups</b>: press Install. '
            'Installed and portable programs appear in the <b>Library</b>: double-click to play.</p>'
            '<p><b>Usually works:</b> many everyday programs and older games (Counter-Strike 1.6, old strategy games), '
            'and many Steam games (check protondb.com).</p>'
            '<p><b>Often does not work:</b> games with kernel anti-cheat (Valorant, many online shooters), Microsoft Office, '
            'Adobe apps, programs that need special Windows drivers.</p>'
            '<p><b>Something broke?</b> Tick "Save Wine errors to a log" for that program, run it, then press Open log. '
            'In a terminal, <tt>.debug wine</tt> shows the Windows environment status.</p>', wrap=True)
        t.setTextFormat(Qt.TextFormat.RichText)
        t.setAlignment(Qt.AlignmentFlag.AlignTop)
        v.addWidget(t)
        v.addStretch(1)
        return w

    # ------------------------------------------------------------ refresh
    def show_page(self, i):
        self.stack.setCurrentIndex(i)
        self.title.setText(self.side.item(i).text())
        self.search.setVisible(i == 0)

    def refresh_soon(self):
        self.refresh_timer.start()

    def refresh_all(self):
        self.cfg = core.load_config()
        ver = core.wine_version()
        self.banner.setVisible(ver is None)
        self.refresh_library()
        self.refresh_files()
        self.update_running()

    def refresh_library(self):
        keep = self.current_key()
        self.programs = core.scan_library(self.cfg)
        self.grid.clear()
        self.icon_queue = []
        generic = theme_icon('wine', 'application-x-ms-dos-executable', 'application-x-executable')
        for p in self.programs:
            it = QListWidgetItem(generic, p.name)
            it.setData(ROLE, p.key)
            it.setToolTip(p.path or p.name)
            it.setSizeHint(QSize(146, 128))
            if self.cfg['programs'].get(p.key, {}).get('fav'):
                it.setText('★ ' + p.name)
            self.grid.addItem(it)
            self.icon_queue.append((it, p))
            if p.key == keep:
                self.grid.setCurrentItem(it)
        if self.icon_queue:
            self.icon_timer.start()
        has = bool(self.programs)
        self.grid.setVisible(has)
        self.empty.setVisible(not has)
        self.details.setVisible(has)
        if has and not self.grid.currentItem():
            self.grid.setCurrentRow(0)
        self.filter_grid(self.search.text())

    def load_next_icon(self):
        if not self.icon_queue:
            self.icon_timer.stop()
            return
        it, p = self.icon_queue.pop(0)
        png = p.icon if p.kind == 'installed' else core.exe_icon(p.path)
        if png and os.path.exists(png):
            pm = QPixmap(png)
            if not pm.isNull():
                it.setIcon(QIcon(pm))
                if self.current_key() == p.key:
                    self.show_details()

    def refresh_files(self):
        tree, folder, exts = self.file_trees['Setups']
        self.fill_tree(tree, core.files_in(folder, exts), lambda f: [core.human_size(os.path.getsize(f)), os.path.splitext(f)[1][1:].upper()], folder)
        self.fill_tree(self.rt_tree, core.files_in(core.RUNTIMES, ('.exe', '.msi')),
                       lambda f: [core.human_size(os.path.getsize(f)), f'{core.pe_bits(f) or "?"}-bit'], core.RUNTIMES)
        self.fill_tree(self.dll_tree, core.files_in(core.DLLS, ('.dll', '.ocx')),
                       lambda f: [f'{core.pe_bits(f) or "?"}-bit', core.human_size(os.path.getsize(f))], core.DLLS)

    @staticmethod
    def fill_tree(tree, files, cols, base):
        tree.clear()
        for f in files:
            try:
                extra = cols(f)
            except OSError:
                continue
            it = QTreeWidgetItem([os.path.relpath(f, base)] + extra)
            it.setData(0, ROLE, f)
            tree.addTopLevelItem(it)
        if not files:
            it = QTreeWidgetItem(['Nothing here yet. Use "Add files", or drag files onto this window.', '', ''])
            it.setFlags(Qt.ItemFlag.NoItemFlags)
            tree.addTopLevelItem(it)

    def filter_grid(self, text):
        t = (text or '').lower()
        for i in range(self.grid.count()):
            it = self.grid.item(i)
            it.setHidden(bool(t) and t not in it.text().lower())

    def update_running(self):
        run = core.running_programs()
        self.stop_btn.setText(f'Stop all ({len(run)})' if run else 'Stop all')
        self.stop_btn.setEnabled(bool(run))
        ver = core.wine_version()
        self.wine_label.setText(f'{len(self.programs)} programs  ·  {ver or "Wine not installed"}  ·  {len(run)} running')

    # ------------------------------------------------------------ the selected program
    def current_key(self):
        it = self.grid.currentItem() if hasattr(self, 'grid') else None
        return it.data(ROLE) if it else None

    def current(self):
        k = self.current_key()
        for p in self.programs:
            if p.key == k:
                return p
        return None

    def show_details(self):
        p = self.current()
        if not p:
            return
        it = self.grid.currentItem()
        self.d_icon.setPixmap(it.icon().pixmap(96, 96))
        self.d_name.setText(p.name)
        if p.kind == 'installed':
            meta = 'Installed with a setup<br><span style="font-size:12px">' + (p.folder or 'in the Windows C: drive') + '</span>'
        else:
            bits = core.pe_bits(p.path) if p.path and p.path.lower().endswith('.exe') else 0
            try:
                size = core.human_size(os.path.getsize(p.path))
            except OSError:
                size = '?'
            meta = (('Portable program' if p.kind == 'portable' else 'Added from another folder') +
                    f'  ·  {bits or "?"}-bit  ·  {size}<br><span style="font-size:12px">{p.path}</span>')
        self.d_meta.setText(meta)
        s = self.cfg['programs'].get(p.key, {})
        for c, k in ((self.s_game, 'game'), (self.s_hud, 'dxvk_hud'), (self.s_log, 'log'), (self.s_nowarn, 'no_warn')):
            c.blockSignals(True)
            c.setChecked(bool(s.get(k)))
            c.blockSignals(False)
        self.s_args.setText(s.get('args', ''))
        installed = p.kind == 'installed'
        self.s_args.setEnabled(not installed)
        self.menu_btn.setEnabled(not installed)
        self.fav_btn.setText('★ Favourite' if s.get('fav') else '☆ Favourite')

    def settings_for(self, p):
        return self.cfg['programs'].setdefault(p.key, {})

    def save_settings(self, *_):
        p = self.current()
        if not p:
            return
        s = self.settings_for(p)
        s['game'] = self.s_game.isChecked()
        s['dxvk_hud'] = self.s_hud.isChecked()
        s['log'] = self.s_log.isChecked()
        s['no_warn'] = self.s_nowarn.isChecked()
        s['args'] = self.s_args.text().strip()
        core.save_config(self.cfg)

    def toggle_fav(self):
        p = self.current()
        if p:
            s = self.settings_for(p)
            s['fav'] = not s.get('fav')
            core.save_config(self.cfg)
            self.refresh_library()

    def rename(self):
        p = self.current()
        if not p:
            return
        name, ok = QInputDialog.getText(self, TITLE, 'New name:', QLineEdit.EchoMode.Normal, p.name)
        if ok and name.strip():
            self.settings_for(p)['name'] = name.strip()
            core.save_config(self.cfg)
            self.refresh_library()

    def hide_prog(self):
        p = self.current()
        if p and self.ask(f'Hide <b>{p.name}</b> from the library?<br>The files are not deleted.'):
            self.cfg.setdefault('hidden', []).append(p.key)
            if p.key in self.cfg.get('extra', []):
                self.cfg['extra'].remove(p.key)
            core.save_config(self.cfg)
            self.refresh_library()

    def open_folder(self):
        p = self.current()
        if p:
            self.open_path(p.folder or os.path.join(core.PREFIX, 'drive_c'))

    def add_to_menu(self):
        p = self.current()
        if p and p.path:
            f = core.make_menu_entry(p)
            self.toast(f'{p.name} is now in the app menu')
            self.log_line(f'Menu entry: {f}')

    def log_file(self, p):
        safe = ''.join(ch if ch.isalnum() else '-' for ch in p.name).strip('-') or 'program'
        return os.path.join(core.CACHE, 'logs', safe + '.log')

    def open_prog_log(self):
        p = self.current()
        if not p:
            return
        f = self.log_file(p)
        if os.path.exists(f):
            self.open_path(f)
        else:
            self.info('There is no log yet. Tick <b>Save Wine errors to a log</b>, run the program, then press Open log.')

    # ------------------------------------------------------------ running things
    def env_for(self, extra):
        env = QProcessEnvironment.systemEnvironment()
        for k, v in extra.items():
            env.insert(k, v)
        return env

    def need_wine(self):
        if core.wine_version():
            return True
        self.install_wine()
        return False

    def run_selected(self, game=None):
        p = self.current()
        if not p or not self.need_wine():
            return
        cmd, env = core.run_command(p, self.cfg, game)
        q = QProcess(self)
        if self.cfg['programs'].get(p.key, {}).get('log'):
            logf = self.log_file(p)
            os.makedirs(os.path.dirname(logf), exist_ok=True)
            env['RUSTOS_LOGFILE'] = logf
            with open(logf, 'a') as fh:
                fh.write(f'\n==== {time.strftime("%Y-%m-%d %H:%M:%S")}  {shlex.join(cmd)}\n')
            cmd = ['bash', '-c', 'exec "$@" >>"$RUSTOS_LOGFILE" 2>&1', '_'] + cmd
        q.setProgram(cmd[0])
        q.setArguments(cmd[1:])
        q.setProcessEnvironment(self.env_for(env))
        q.setWorkingDirectory(p.folder if p.folder and os.path.isdir(p.folder) else core.HOME)
        q.startDetached()
        self.toast(f'Starting {p.name}…' + ('  (game mode)' if (game or self.cfg['programs'].get(p.key, {}).get('game')) else ''))
        self.log_line('Run: ' + shlex.join(cmd))
        QTimer.singleShot(4000, self.update_running)

    def run_attached(self, cmd, what, env=None, done=None):
        """Run something and show its output in the log (setups, winetricks)."""
        q = QProcess(self)
        q.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        q.setProcessEnvironment(self.env_for(env or {}))
        q.readyReadStandardOutput.connect(lambda: self.log_text(bytes(q.readAllStandardOutput()).decode(errors='replace')))

        def finished(code, _status):
            self.log_line(f'{what}: finished ({"ok" if code == 0 else "exit code " + str(code)})')
            self.procs.remove(q)
            self.refresh_all()
            if done:
                done(code)
        q.finished.connect(finished)
        self.procs.append(q)
        self.log.setVisible(True)
        self.log_line(f'{what}: ' + shlex.join(cmd))
        q.start(cmd[0], cmd[1:])

    def install_files(self, files):
        files = [f for f in files if f]
        if not files or not self.need_wine():
            return
        queue = list(files)

        def next_one(_code=0):
            if not queue:
                self.toast('Done. New programs show up in the Library.')
                return
            f = queue.pop(0)
            self.run_attached([core.RUN, f], 'Install ' + os.path.basename(f), {'RUSTOS_WINEDEBUG': 'err+all,fixme-all'}, next_one)
        next_one()

    def install_extras(self):
        verbs = [c.property('verb') for c in self.extra_boxes if c.isChecked()]
        if not verbs or not self.need_wine():
            return
        if not shutil.which('winetricks'):
            self.info('winetricks is missing. It comes with Windows support: press <b>Install Windows support</b> again.')
            return
        self.run_attached(['winetricks', '-q'] + verbs, 'Download ' + ', '.join(verbs), {'WINEDEBUG': '-all'},
                          lambda code: self.toast('Installed: ' + ', '.join(verbs)) if code == 0 else
                          self.info('Something did not install. Look at the log for the first error. Windows downloads are '
                                    'sometimes unreliable; try again later.'))

    def install_dlls(self, where):
        files = [i.data(0, ROLE) for i in self.dll_tree.selectedItems() if i.data(0, ROLE)]
        if not files:
            self.info('Pick a DLL in the list first.')
            return
        if not self.need_wine():
            return
        target = 'windows'
        if where == 'folder':
            target = QFileDialog.getExistingDirectory(self, 'Which program folder?', core.PROGS)
            if not target:
                return
        msgs = []
        for f in files:
            if core.is_core_dll(f) and not self.ask(
                    f'<b>{os.path.basename(f)} is a core Windows file.</b><br>Wine has its own, and replacing it usually breaks '
                    'every Windows program. Install it anyway?'):
                continue
            try:
                msgs.append(core.dll_install(f, target))
            except Exception as e:  # noqa: BLE001 - show any failure to the person
                msgs.append(f'{os.path.basename(f)}: {e}')
        if msgs:
            self.info('<br>'.join(msgs) + '<br><br>Close and start your program again.')

    def install_wine(self):
        q = QProcess(self)
        q.finished.connect(lambda *_: self.refresh_all())
        self.procs.append(q)
        q.finished.connect(lambda *_: self.procs.remove(q) if q in self.procs else None)
        q.start(core.RUN, ['--ensure'])

    def wine_tool(self, cmd):
        if self.need_wine():
            QProcess.startDetached(cmd[0], cmd[1:])

    def stop_all(self):
        if core.running_programs() and not self.ask('Close every running Windows program now? Unsaved work in them is lost.'):
            return
        QProcess.startDetached('wineserver', ['-k'])
        self.toast('Stopped all Windows programs')
        QTimer.singleShot(1500, self.update_running)

    # ------------------------------------------------------------ adding
    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, 'Add Windows files', os.path.join(core.HOME, 'Downloads'),
                                                'Windows files (*.exe *.EXE *.msi *.MSI *.dll *.DLL *.ocx *.bat *.lnk *.zip);;All files (*)')
        if files:
            self.do_add(files)

    def add_folder(self):
        d = QFileDialog.getExistingDirectory(self, 'Add a game or program folder', core.HOME)
        if d:
            self.do_add([d])

    def run_any(self):
        f, _ = QFileDialog.getOpenFileName(self, 'Run a Windows program', os.path.join(core.HOME, 'Downloads'),
                                           'Windows programs (*.exe *.EXE *.msi *.MSI *.bat *.lnk)')
        if not f or not self.need_wine():
            return
        if self.ask('Keep it in your Library too?', default_yes=True):
            self.cfg.setdefault('extra', [])
            if f not in self.cfg['extra']:
                self.cfg['extra'].append(f)
                core.save_config(self.cfg)
            self.refresh_library()
        QProcess.startDetached(core.RUN, [f], os.path.dirname(f))
        self.toast('Starting ' + os.path.basename(f) + '…')

    def do_add(self, paths):
        try:
            done = core.add_paths(paths)
        except OSError as e:
            self.info(f'Could not copy: {e}')
            return
        if not done:
            self.info('Nothing was added.')
            return
        self.refresh_all()
        lines = '<br>'.join(f'• {n}  →  {k}' for n, k in done)
        self.info(f'<b>Added {len(done)}:</b><br>{lines}')
        kinds = {k for _, k in done}
        page = 1 if kinds == {'Setups'} else 2 if kinds == {'Runtimes'} else 3 if kinds == {'DLLs'} else 0
        self.side.setCurrentRow(page)

    def dragEnterEvent(self, e):  # noqa: N802 (Qt name)
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):  # noqa: N802
        paths = [u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]
        if paths:
            self.do_add(paths)

    # ------------------------------------------------------------ tools
    def compat(self):
        name, ok = QInputDialog.getText(self, TITLE, 'Name of the program or game:')
        if ok and name.strip():
            q = quote(name.strip())
            QDesktopServices.openUrl(QUrl(f'https://appdb.winehq.org/objectManager.php?sClass=application&sTitle={q}'))
            QDesktopServices.openUrl(QUrl(f'https://www.protondb.com/search?q={q}'))
            self.toast('Look for Platinum, Gold or Silver ratings')

    def reset_env(self):
        if not os.path.isdir(core.PREFIX):
            self.info('There is nothing to reset yet.')
            return
        if not self.ask('<b>Reset the Windows environment?</b><br><br>Programs installed with setups must be installed again. '
                        'The old environment is kept as <tt>.wine.old-DATE</tt> in your home folder, so saved games are not lost. '
                        'Your EXE Center folder is not touched.'):
            return
        QProcess.execute('wineserver', ['-k'])
        os.rename(core.PREFIX, core.PREFIX + '.old-' + time.strftime('%Y-%m-%d-%H%M'))
        shutil.rmtree(core.WINEMENU, ignore_errors=True)
        os.makedirs(core.WINEMENU, exist_ok=True)
        self.refresh_all()
        self.info('Done. A fresh Windows environment is made the next time you run a program.')

    def remove_wine(self):
        if not core.wine_version():
            self.info('Windows support is not installed.')
            return
        if not self.ask('<b>Remove Windows support?</b><br>This uninstalls Wine (about 1 GB). .exe files stop working until you '
                        'install it again. Your EXE Center folder and files stay.'):
            return
        QProcess.startDetached('konsole', ['--hold', '-e', 'sudo', 'pacman', '-Rns', 'wine', 'wine-mono', 'wine-gecko', 'winetricks'])

    def env_info(self):
        size = core.human_size(core.prefix_size()) if os.path.isdir(core.PREFIX) else 'not made yet'
        self.info(f'<b>Wine:</b> {core.wine_version() or "not installed"}<br><b>Windows environment:</b> {core.PREFIX} ({size})<br>'
                  f'<b>EXE Center folder:</b> {core.ROOT}<br><b>Programs in the library:</b> {len(self.programs)}<br>'
                  f'<b>Running now:</b> {len(core.running_programs())}')

    # ------------------------------------------------------------ small helpers
    def open_path(self, p):
        if not os.path.exists(p):
            if p.startswith(core.PREFIX) and not self.need_wine():
                return
            os.makedirs(p, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(p))

    def toggle_log(self):
        vis = not self.log.isVisible()
        self.log.setVisible(vis)
        self.log_btn.setText('Hide log' if vis else 'Show log')
        self.cfg['show_log'] = vis
        core.save_config(self.cfg)

    def log_text(self, text):
        self.log.moveCursor(QTextCursor.MoveOperation.End)
        self.log.insertPlainText(text)
        self.log.ensureCursorVisible()

    def log_line(self, text):
        self.log.appendPlainText(time.strftime('%H:%M:%S  ') + text)

    def toast(self, text):
        self.status.showMessage(text, 6000)

    def info(self, html):
        QMessageBox.information(self, TITLE, html)

    def ask(self, html, default_yes=False):
        yes, no = QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No
        return QMessageBox.question(self, TITLE, html, yes | no, yes if default_yes else no) == yes

    def closeEvent(self, e):  # noqa: N802
        busy = [q for q in self.procs if q.state() != QProcess.ProcessState.NotRunning]
        if busy and not self.ask('Something is still installing. Close anyway (it stops)?'):
            e.ignore()
            return
        e.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(TITLE)
    app.setDesktopFileName('rustos-exe-center')
    app.setStyle('Fusion')
    app.setStyleSheet(STYLE)
    f = QFont(app.font())
    f.setPointSize(max(f.pointSize(), 10))
    app.setFont(f)
    w = Main()
    w.show()
    if len(sys.argv) > 1 and sys.argv[1] == '--add':
        w.do_add(sys.argv[2:])
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
