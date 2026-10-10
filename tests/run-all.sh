#!/usr/bin/env bash
# Runs every RustOS test that needs no hardware, no Qt and no network.   bash tests/run-all.sh
set -u
cd "$(dirname "$0")/.." || exit 1
rc=0
bash tests/devhw/run-tests.sh || rc=1
python3 tests/center/test_center_core.py || rc=1
python3 tests/center/test_center_window.py || rc=1
python3 overlay/airootfs/usr/share/rustos/exe-center/exe_core.py selftest >/dev/null 2>&1 && echo "exe_core: selftest passed" || { echo "exe_core: selftest FAILED"; rc=1; }
[ "$rc" = 0 ] && echo "ALL TESTS PASSED" || echo "SOME TESTS FAILED"
exit $rc
