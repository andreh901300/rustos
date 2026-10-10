#!/usr/bin/env python3
"""Smoke test for the RustOS Center window code without Qt: runs every page loader and the Hardware dev actions
against a stand-in PyQt6 and records which RustOS tools would run (and whether as root).
   python3 tests/center/test_center_window.py"""
import os
import sys
from unittest.mock import MagicMock

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(HERE, 'pyqt6_stub'))
sys.path.insert(0, os.path.join(TOP, 'overlay/airootfs/usr/share/rustos/center'))
import center_core as core  # noqa: E402
core.CATALOG = os.path.join(TOP, 'overlay/airootfs/usr/share/rustos/apps.catalog')
import rustos_center as rc  # noqa: E402


class W:
    def __getattr__(self, n):
        if n.startswith('__'):
            raise AttributeError(n)
        m = MagicMock()
        object.__setattr__(self, n, m)
        return m


class FCombo(W):
    def __init__(self, *a):
        self.items, self.i, self.en = [], 0, True
    def addItem(self, t, d=None): self.items.append((t, d))
    def count(self): return len(self.items)
    def itemData(self, i): return self.items[i][1]
    def findData(self, d): return next((i for i, (_t, x) in enumerate(self.items) if x == d), -1)
    def setCurrentIndex(self, i): self.i = i
    def currentData(self): return self.items[self.i][1] if self.items else None
    def setEnabled(self, e): self.en = e
    def isEnabled(self): return self.en


class FLine(W):
    def __init__(self, t='', *a): self.t = t if isinstance(t, str) else ''
    def text(self): return self.t
    def setText(self, t): self.t = t


class FCheck(W):
    def __init__(self, *a): self.c, self.props = False, {}
    def isChecked(self): return self.c
    def setChecked(self, c): self.c = bool(c)
    def setProperty(self, k, v): self.props[k] = v
    def property(self, k): return self.props.get(k)


class FTree(W):
    def __init__(self, *a): self.cur = None
    def currentItem(self): return self.cur


rc.QComboBox, rc.QLineEdit, rc.QCheckBox, rc.QRadioButton, rc.QTreeWidget = FCombo, FLine, FCheck, FCheck, FTree
calls = []


def fake_run(self, title, argv, root=False, done=None, line=None, show=None, cancellable=None):
    calls.append((title, root, list(argv)))
    if done:
        done(0, '')
    return True


rc.Main.run = fake_run
w = rc.Main('home')
w.ask = lambda *a, **k: True
w.info = lambda *a, **k: None
for key, *_ in rc.PAGES:
    w.show_page(w.keys.index(key))
    if getattr(w, 'load_' + key, None):
        getattr(w, 'load_' + key)()

machine = ('CHECK\tIOMMU\tunavailable\tnot active\tTurn on VT-d\n'
           'CHECK\tVFIO assignment\tunavailable\tneeds an active IOMMU\t\n'
           'PCI\t0000:03:00.0\t10ee:7024\t0580\t-\t-\t14\tyes\t\tXilinx Device\tno\n'
           'PCI\t0000:00:02.0\t8086:a780\t0300\ti915\ti915\t0\tno\tit is the graphics card showing this screen\tIntel GPU\tno\n'
           'USB\t0403:6010\tFTDI FT2232\tyes\nSUMMARY\t10\t2\t1\n')
w.got_devhw(0, machine)
assert w.devhw['summary'] == (10, 2, 1)

# pick the FPGA card and run the VFIO actions
item = MagicMock()
item.data.return_value = w.devhw['pci'][0]
w.dh_pci.cur = item
w.devhw_pick()
for a in ('bind', 'keep', 'release', 'forget'):
    w.devhw_vfio(a)
w.dh_vfio_access.setChecked(True)
w.devhw_access()
w.dh_tools['yosys'][0].setChecked(True)
w.dh_tools['yosys'][0].setProperty('was', False)
w.devhw_install_tools()
w.devhw_lts()
w.devhw_kernel_default()
w.devhw_dkms_build()
w.devhw_iommu_on()

want = [
    (True, ['rustos-devhw', 'vfio', 'bind', '0000:03:00.0']),
    (True, ['rustos-devhw', 'vfio', 'keep', '0000:03:00.0']),
    (True, ['rustos-devhw', 'vfio', 'release', '0000:03:00.0']),
    (True, ['rustos-devhw', 'vfio', 'forget', '0000:03:00.0']),
    (True, ['rustos-devhw', 'access', '--vfio']),
    (True, ['rustos-apps', '--install', 'yosys']),
    (True, ['rustos-performance', 'kernel', 'lts']),
    (True, ['rustos-performance', 'kernel', 'default']),
    (True, ['rustos-devhw', 'dkms', 'build']),
    (True, ['rustos-devhw', 'iommu-on']),
]
got = [(root, [os.path.basename(argv[0])] + argv[1:]) for _t, root, argv in calls]
for root, argv in want:
    assert any(r == root and g[:len(argv)] == argv for r, g in got), ('missing', argv, got)
# never a no-IOMMU or IOMMU-off option in anything the window runs
flat = ' '.join(' '.join(a) for _t, _r, a in calls)
for bad in ('noiommu', 'iommu=off', 'iommu=pt', '/dev/mem'):
    assert bad not in flat, bad
print('RustOS Center window smoke test: %d tool calls checked, all pages loaded' % len(want))
