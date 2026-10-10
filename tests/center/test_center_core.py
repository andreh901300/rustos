#!/usr/bin/env python3
"""Tests for center_core (no Qt needed): its own checks, and rustos-devhw --machine output parsed the way RustOS
Center reads it, made on a fake system with no IOMMU and one FPGA card without a driver.
   python3 tests/center/test_center_core.py"""
import gzip
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(TOP, 'overlay/airootfs/usr/share/rustos/center'))
import center_core as core  # noqa: E402

TOOL = os.path.join(TOP, 'overlay/airootfs/usr/local/bin/rustos-devhw')
K = '7.2.9-arch1-1'


def w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(text)


def fake_root(d, iommu):
    w(d + '/proc/cmdline', 'root=UUID=1 rw quiet\n')
    w(d + '/proc/cpuinfo', 'vendor_id\t: GenuineIntel\n')
    w(d + '/proc/meminfo', 'MemTotal: 8000000 kB\n')
    w(d + '/proc/mounts', '')
    w(d + '/usr/lib/modules/%s/modules.dep' % K, 'kernel/drivers/vfio/vfio.ko.zst:\nkernel/drivers/vfio/pci/vfio-pci.ko.zst:\n')
    w(d + '/usr/lib/modules/%s/modules.builtin' % K, '')
    w(d + '/usr/lib/modules/%s/pkgbase' % K, 'linux\n')
    with gzip.open(d + '/proc/config.gz', 'wt') as f:
        f.write('CONFIG_IOMMU_SUPPORT=y\nCONFIG_VFIO=m\nCONFIG_VFIO_PCI=m\n')
    dev = d + '/sys/devices/pci0000:00/0000:03:00.0'
    for k, v in (('class', '0x058000'), ('vendor', '0x10ee'), ('device', '0x7024'), ('driver_override', '')):
        w(dev + '/' + k, v + '\n')
    os.makedirs(d + '/sys/bus/pci/devices', exist_ok=True)
    os.symlink('../../../devices/pci0000:00/0000:03:00.0', d + '/sys/bus/pci/devices/0000:03:00.0')
    if iommu:
        os.makedirs(d + '/sys/class/iommu/dmar0')
        os.makedirs(d + '/sys/kernel/iommu_groups/14/devices')
        os.symlink('../../../kernel/iommu_groups/14', dev + '/iommu_group')
        os.symlink('../../../../devices/pci0000:00/0000:03:00.0', d + '/sys/kernel/iommu_groups/14/devices/0000:03:00.0')
    shims = d + '.bin'
    os.makedirs(shims)
    w(shims + '/lspci', '#!/bin/sh\necho "0000:03:00.0 Memory controller [0580]: Xilinx Corporation Device [10ee:7024]"\n')
    w(shims + '/systemd-detect-virt', '#!/bin/sh\necho none\n')
    for f in os.listdir(shims):
        os.chmod(os.path.join(shims, f), 0o755)
    return shims


def machine(d, shims):
    env = dict(os.environ, RUSTOS_DEVHW_ROOT=d, RUSTOS_DEVHW_KREL=K, RUSTOS_DEVHW_ARCH='x86_64',
               PATH=shims + ':' + os.environ['PATH'], NO_COLOR='1')
    return subprocess.run(['bash', TOOL, 'check', '--machine'], env=env, stdout=subprocess.PIPE, text=True).stdout


def main():
    core.selftest()
    n = 0
    with tempfile.TemporaryDirectory() as t:
        # no IOMMU: VFIO is unavailable, the card cannot be given away, the fix names VT-d
        d = os.path.join(t, 'noiommu')
        out = core.parse_devhw(machine(d, fake_root(d, False)))
        assert core.devhw_check(out, 'IOMMU') == 'unavailable', out['checks'][:8]
        assert core.devhw_check(out, 'VFIO assignment') == 'unavailable'
        fix = [c['fix'] for c in out['checks'] if c['item'] == 'IOMMU'][0]
        assert 'VT-d' in fix, fix
        assert len(out['pci']) == 1 and out['pci'][0]['vfio'] == 'no' and out['pci'][0]['driver'] == ''
        assert 'IOMMU is not active' in out['pci'][0]['why']
        assert out['summary'] and out['summary'][1] >= 2
        n += 6
        # IOMMU on: the card can be given to VFIO, group 14
        d = os.path.join(t, 'iommu')
        out = core.parse_devhw(machine(d, fake_root(d, True)))
        assert core.devhw_check(out, 'IOMMU') == 'supported'
        assert core.devhw_check(out, 'VFIO assignment') == 'supported'
        p = out['pci'][0]
        assert p['vfio'] == 'yes' and p['group'] == '14' and p['ids'] == '10ee:7024' and not p['kept'], p
        assert all(c['status'] in core.DEVHW_STATUSES for c in out['checks'])
        n += 4
    # catalog: the FPGA group is there and every tool in FPGA_TOOLS is in it
    cat = core.catalog(os.path.join(TOP, 'overlay/airootfs/usr/share/rustos/apps.catalog'))
    ids = {a['id'] for a in cat if a['cat'] == 'FPGA and hardware'}
    assert {t[0] for t in core.FPGA_TOOLS} <= ids and 'fpgaaccess' in ids, ids
    n += 1
    print('center_core + rustos-devhw --machine: %d checks passed' % n)


if __name__ == '__main__':
    main()
