# Stand-in for PyQt6 so the RustOS Center code paths can be run without a screen or Qt (tests only).
import sys, types
from unittest.mock import MagicMock
class _Meta(type):
    def __getattr__(cls, name):
        if name.startswith('__'): raise AttributeError(name)
        return MagicMock(name=f'{cls.__name__}.{name}')
    def __or__(cls, o): return MagicMock()
class _Base(metaclass=_Meta):
    def __init__(self, *a, **k): pass
    def __getattr__(self, name):
        if name.startswith('__'): raise AttributeError(name)
        m = MagicMock(name=name); object.__setattr__(self, name, m); return m
class _Mod(types.ModuleType):
    def __getattr__(self, name):
        if name.startswith('__'): raise AttributeError(name)
        c = _Meta(name, (_Base,), {}); setattr(self, name, c); return c
for sub in ('QtCore', 'QtGui', 'QtWidgets', 'QtNetwork'):
    m = _Mod('PyQt6.' + sub); sys.modules['PyQt6.' + sub] = m; globals()[sub] = m
