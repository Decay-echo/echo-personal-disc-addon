"""Personal Disc Everywhere v3.4 goal+tunnel A-button, no popup - Windows PC patcher, Python 3.8+.

No packages, downloads, credentials or research files are required.
"""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import os
from pathlib import Path
import sys

DLL_NAME = '351c49438bd38225.dll'
STOCK_SHA = 'a8a8e156223ba10246f867e4513d272f5d89f0c3b5bd1a3167682176a429c4c1'
PATCHED_SHA = '391cfcb0accf30885ad87909c7da0735086af7d0a76e5dc20a1f0d2e903d743f'
EDITS = [(20866, '488b5c2450', 'e9991d0000'), (28448, '000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000', '488bcbba7ec1b557e8f3deffff488b5368488b4a384889485048c74058ffffffffff42084883c20848895070488b5c2450e931e2ffff'), (19108, 'b881c40ed3', 'b8423c3f43'), (18312, 'b833ce7e25', 'b800000000'), (18521, 'b88427d2ba', 'b800000000'), (13629, '0f8417030000', '0f84ea020000'), (13715, '0f84c1020000', '0f8494020000'), (13725, '0f84b7020000', '0f848a020000'), (34272, '00000000000000000000000000000000', '21000000905b00008d5d0000f8920000'), (35848, '000000000000000000000000', '207b0000567b0000e0950000'), (456, '0d6b0000', '566b0000'), (496, 'd6150000', 'f0150000'), (576, '08040000', '14040000'), (348, '08040000', '14040000')]

def digest(data):
    return hashlib.sha256(data).hexdigest()

def transform(data, restore=False):
    expected, wanted = (PATCHED_SHA, STOCK_SHA) if restore else (STOCK_SHA, PATCHED_SHA)
    if digest(data) != expected:
        raise ValueError('Unsupported or modified DLL. No changes made. SHA256: '+digest(data))
    result = bytearray(data)
    for at, original, patched in EDITS:
        old, new = (patched, original) if restore else (original, patched)
        old, new = bytes.fromhex(old), bytes.fromhex(new)
        if len(old) != len(new) or result[at:at+len(old)] != old:
            raise ValueError('Unexpected bytes at file offset '+hex(at))
        result[at:at+len(old)] = new
    if digest(result) != wanted:
        raise ValueError('Patch verification failed. No changes made.')
    return bytes(result)

def game_running():
    class Entry(ctypes.Structure):
        _fields_ = [('dwSize',wintypes.DWORD),('cntUsage',wintypes.DWORD),
                    ('th32ProcessID',wintypes.DWORD),('th32DefaultHeapID',ctypes.c_size_t),
                    ('th32ModuleID',wintypes.DWORD),('cntThreads',wintypes.DWORD),
                    ('th32ParentProcessID',wintypes.DWORD),('pcPriClassBase',wintypes.LONG),
                    ('dwFlags',wintypes.DWORD),('szExeFile',wintypes.WCHAR*260)]
    k = ctypes.WinDLL('kernel32',use_last_error=True)
    k.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD,wintypes.DWORD]
    k.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    k.Process32FirstW.argtypes = k.Process32NextW.argtypes = [wintypes.HANDLE,ctypes.POINTER(Entry)]
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = k.CreateToolhelp32Snapshot(2,0)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    entry = Entry()
    entry.dwSize = ctypes.sizeof(entry)
    try:
        if not k.Process32FirstW(handle,ctypes.byref(entry)):
            raise ctypes.WinError(ctypes.get_last_error())
        while True:
            if entry.szExeFile.lower() == 'echovr.exe':
                return True
            if not k.Process32NextW(handle,ctypes.byref(entry)):
                if ctypes.get_last_error() != 18:
                    raise ctypes.WinError(ctypes.get_last_error())
                return False
    finally:
        k.CloseHandle(handle)

def resolve_target(value):
    path = Path(os.path.expandvars(str(value).strip().strip('"'))).expanduser()
    possibilities = [path] if path.is_file() else [
        path/'bin'/'win10'/'scripts'/DLL_NAME,
        path/'scripts'/DLL_NAME,
        path/DLL_NAME,
    ]
    if path.name.lower() == 'echovr.exe':
        possibilities = [path.parent/'scripts'/DLL_NAME]
    for candidate in possibilities:
        if candidate.name.lower() == DLL_NAME and candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError('Cannot find '+DLL_NAME+' under '+str(path))

def discover():
    roots = [Path(__file__).resolve().parent,Path.cwd()]
    for variable in ('ProgramW6432','ProgramFiles','ProgramFiles(x86)'):
        root = os.environ.get(variable)
        if root:
            for launcher in ('Meta Horizon','Oculus'):
                roots.append(Path(root)/launcher/'Software'/'Software'/'ready-at-dawn-echo-arena')
    found = []
    for root in roots:
        try:
            target = resolve_target(root)
            if target not in found:
                found.append(target)
        except FileNotFoundError:
            pass
    return found

def replace_checked(target, expected, replacement):
    if game_running():
        raise RuntimeError('Close Echo VR completely before patching or restoring.')
    if target.read_bytes() != expected:
        raise RuntimeError('The DLL changed during this operation. Stopped.')
    temporary = target.with_name(target.name+'.personal-disc.tmp')
    created = False
    try:
        with temporary.open('xb') as stream:
            created = True
            stream.write(replacement)
            stream.flush()
            os.fsync(stream.fileno())
        if game_running() or target.read_bytes() != expected:
            raise RuntimeError('Game started or DLL changed. Stopped.')
        os.replace(temporary,target)
    finally:
        if created and temporary.exists():
            temporary.unlink()
    if target.read_bytes() != replacement:
        raise RuntimeError('Installed file failed verification.')


import base64
import json
import struct
import zlib
VERSION = 'v3.5 goal+launcher+tunnel A-button, no popup'
DISC_NAME = "38965d90a823f03f.dll"
DISC_SHA = '777653b7547925b2c86bf5f343848564b3c07c6efd8df421acbb629604ed67ed'
RECORDS = {'351c49438bd38225.dll': {'stock': 'a8a8e156223ba10246f867e4513d272f5d89f0c3b5bd1a3167682176a429c4c1', 'patched': '6924f10fda85dfec36028ce1153b7de0fd72e154ab7bf57ffe710101b9a1d53f', 'length': 36864, 'inverse': [[190, '05'], [213, '6c'], [217, '22'], [265, 'd000'], [345, 'b000'], [348, '08'], [456, '0d'], [496, 'd6'], [576, '08'], [648, '00000000'], [656, '0000'], [661, '00'], [665, '00'], [669, '00'], [684, '00'], [687, '0000000000'], [696, '0000'], [701, '00'], [705, '00'], [709, '00'], [724, '00'], [727, '0000000000'], [736, '00'], [741, '00'], [745, '00'], [749, '00'], [764, '00'], [767, '0000000000'], [776, '0000'], [782, '00'], [785, '00'], [789, '00'], [804, '00'], [807, '00'], [9710, '7e06'], [9956, '8805'], [10540, '4003'], [10959, '9d01'], [13631, '1703'], [13717, 'c1'], [13727, 'b7'], [18313, '33ce7e25'], [19109, '81c40ed3'], [19460, '68e0ffff'], [19764, '38dfffff'], [20866, '488b5c2450'], [28448, '000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'], [34272, '00'], [34276, '0000'], [34280, '0000'], [34284, '0000'], [35848, '0000'], [35852, '0000'], [35856, '0000']]}, '38965d90a823f03f.dll': {'stock': '777653b7547925b2c86bf5f343848564b3c07c6efd8df421acbb629604ed67ed', 'patched': 'e8bb4fbcfae83f35fbc3ab76fa3f5b6c4f6a09fb7b19cf5ca777b7aaa032f12e', 'length': 118784, 'inverse': [[190, '05'], [213, '88'], [217, '52'], [265, '00'], [345, 'e001'], [348, 'cc0f'], [648, '00000000'], [656, '0000'], [662, '00'], [665, '00'], [669, '0000'], [684, '00'], [687, '0000000000'], [696, '0000'], [701, '0000'], [705, '00'], [709, '0000'], [724, '00'], [727, '0000000000'], [736, '00'], [741, '0000'], [745, '00'], [749, '0000'], [764, '00'], [767, '0000000000'], [776, '0000'], [781, '0000'], [785, '00'], [789, '0000'], [804, '00'], [807, '00'], [32942, '9e0800'], [33188, 'a80700'], [33708, 'a00500'], [34127, 'fd0300'], [60848, '4883ec5833d2'], [81012, 'd84cffff'], [91968, '4883ec5833d2']]}}
V34_RECORDS = {'351c49438bd38225.dll': {'stock': 'a8a8e156223ba10246f867e4513d272f5d89f0c3b5bd1a3167682176a429c4c1', 'patched': 'd60f87d44903084d17b22136f085f8961ea46e0046487622553dac8ac1e3c271', 'length': 36864, 'inverse': [[190, '05'], [213, '6c'], [217, '22'], [265, 'd000'], [345, 'b000'], [348, '08'], [456, '0d'], [496, 'd6'], [576, '08'], [648, '00000000'], [656, '0000'], [661, '00'], [665, '00'], [669, '00'], [684, '00'], [687, '0000000000'], [696, '0000'], [701, '00'], [705, '00'], [709, '00'], [724, '00'], [727, '0000000000'], [736, '00'], [741, '00'], [745, '00'], [749, '00'], [764, '00'], [767, '0000000000'], [776, '0000'], [782, '00'], [785, '00'], [789, '00'], [804, '00'], [807, '00'], [9710, '7e06'], [9956, '8805'], [10540, '4003'], [10959, '9d01'], [13631, '1703'], [13717, 'c1'], [13727, 'b7'], [18313, '33ce7e25'], [19109, '81c40ed3'], [19460, '68e0ffff'], [19764, '38dfffff'], [20866, '488b5c2450'], [28448, '000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'], [34272, '00'], [34276, '0000'], [34280, '0000'], [34284, '0000'], [35848, '0000'], [35852, '0000'], [35856, '0000']]}, '38965d90a823f03f.dll': {'stock': '777653b7547925b2c86bf5f343848564b3c07c6efd8df421acbb629604ed67ed', 'patched': 'c9aedb29feaec0ba3dccde191db2fe73f49369abba3ce0af36c63e04fe0f3b2d', 'length': 118784, 'inverse': [[190, '05'], [213, '88'], [217, '52'], [265, '00'], [345, 'e001'], [348, 'cc0f'], [648, '00000000'], [656, '0000'], [662, '00'], [665, '00'], [669, '0000'], [684, '00'], [687, '0000000000'], [696, '0000'], [701, '0000'], [705, '00'], [709, '0000'], [724, '00'], [727, '0000000000'], [736, '00'], [741, '0000'], [745, '00'], [749, '0000'], [764, '00'], [767, '0000000000'], [776, '0000'], [781, '0000'], [785, '00'], [789, '0000'], [804, '00'], [807, '00'], [32942, '9e0800'], [33188, 'a80700'], [33708, 'a00500'], [34127, 'fd0300'], [60848, '4883ec5833d2'], [81012, 'd84cffff'], [91968, '4883ec5833d2']]}}
V33_RECORDS = {'351c49438bd38225.dll': {'stock': 'a8a8e156223ba10246f867e4513d272f5d89f0c3b5bd1a3167682176a429c4c1', 'patched': 'be5c1d14bed118d289060444157f9c1e526678e025d92f60122bd9e01ba63297', 'length': 36864, 'inverse': [[190, '05'], [213, '6c'], [217, '22'], [265, 'd000'], [345, 'b000'], [348, '08'], [456, '0d'], [496, 'd6'], [576, '08'], [648, '00000000'], [656, '0000'], [661, '00'], [665, '00'], [669, '00'], [684, '00'], [687, '0000000000'], [696, '0000'], [701, '00'], [705, '00'], [709, '00'], [724, '00'], [727, '0000000000'], [736, '00'], [741, '00'], [745, '00'], [749, '00'], [764, '00'], [767, '0000000000'], [776, '0000'], [782, '00'], [785, '00'], [789, '00'], [804, '00'], [807, '00'], [9710, '7e06'], [9956, '8805'], [10540, '4003'], [10959, '9d01'], [13631, '1703'], [13717, 'c1'], [13727, 'b7'], [18313, '33ce7e25'], [19109, '81c40ed3'], [19460, '68e0ffff'], [19764, '38dfffff'], [20866, '488b5c2450'], [28448, '000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'], [34272, '00'], [34276, '0000'], [34280, '0000'], [34284, '0000'], [35848, '0000'], [35852, '0000'], [35856, '0000']]}, '38965d90a823f03f.dll': {'stock': '777653b7547925b2c86bf5f343848564b3c07c6efd8df421acbb629604ed67ed', 'patched': 'd5670fe2f1b31cd21c90a11593409950211dcbeb83ce653d5e12db4daee4f936', 'length': 118784, 'inverse': [[190, '05'], [213, '88'], [217, '52'], [265, '00'], [345, 'e001'], [348, 'cc0f'], [648, '00000000'], [656, '0000'], [662, '00'], [665, '00'], [669, '0000'], [684, '00'], [687, '0000000000'], [696, '0000'], [701, '0000'], [705, '00'], [709, '0000'], [724, '00'], [727, '0000000000'], [736, '00'], [741, '0000'], [745, '00'], [749, '0000'], [764, '00'], [767, '0000000000'], [776, '0000'], [781, '0000'], [785, '00'], [789, '0000'], [804, '00'], [807, '00'], [32942, '9e0800'], [33188, 'a80700'], [33708, 'a00500'], [34127, 'fd0300'], [60848, '4883ec5833d2'], [81012, 'd84cffff'], [91968, '4883ec5833d2']]}}
V31_RECORDS = {'351c49438bd38225.dll': {'stock': 'a8a8e156223ba10246f867e4513d272f5d89f0c3b5bd1a3167682176a429c4c1', 'patched': '2a497ecf57e1d99a28857cf2e22a8ab211333014bd7f61414a4c8c8eaa7bd0b5', 'length': 36864, 'inverse': [[190, '05'], [213, '6c'], [217, '22'], [265, 'd000'], [345, 'b000'], [348, '08'], [456, '0d'], [496, 'd6'], [576, '08'], [648, '00000000'], [656, '0000'], [661, '00'], [665, '00'], [669, '00'], [684, '00'], [687, '0000000000'], [696, '0000'], [701, '00'], [705, '00'], [709, '00'], [724, '00'], [727, '0000000000'], [736, '00'], [741, '00'], [745, '00'], [749, '00'], [764, '00'], [767, '0000000000'], [776, '0000'], [782, '00'], [785, '00'], [789, '00'], [804, '00'], [807, '00'], [9710, '7e06'], [9956, '8805'], [10540, '4003'], [10959, '9d01'], [13631, '1703'], [13717, 'c1'], [13727, 'b7'], [18313, '33ce7e25'], [19109, '81c40ed3'], [19460, '68e0ffff'], [19764, '38dfffff'], [20866, '488b5c2450'], [28448, '000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'], [34272, '00'], [34276, '0000'], [34280, '0000'], [34284, '0000'], [35848, '0000'], [35852, '0000'], [35856, '0000']]}, '38965d90a823f03f.dll': {'stock': '777653b7547925b2c86bf5f343848564b3c07c6efd8df421acbb629604ed67ed', 'patched': 'eff1a406f76b39238f4c2835bd31c1be28f2b34fa7c817a66575d0902df77ca1', 'length': 118784, 'inverse': [[190, '05'], [213, '88'], [217, '52'], [265, '00'], [345, 'e001'], [348, 'cc0f'], [648, '00000000'], [656, '0000'], [662, '00'], [665, '00'], [669, '0000'], [684, '00'], [687, '0000000000'], [696, '0000'], [701, '0000'], [705, '00'], [709, '0000'], [724, '00'], [727, '0000000000'], [736, '00'], [741, '0000'], [745, '00'], [749, '0000'], [764, '00'], [767, '0000000000'], [776, '0000'], [781, '0000'], [785, '00'], [789, '0000'], [804, '00'], [807, '00'], [32942, '9e0800'], [33188, 'a80700'], [33708, 'a00500'], [34127, 'fd0300'], [60848, '4883ec5833d2'], [81012, 'd84cffff'], [91968, '4883ec5833d2']]}}
V301_RECORDS = {'351c49438bd38225.dll': {'stock': 'a8a8e156223ba10246f867e4513d272f5d89f0c3b5bd1a3167682176a429c4c1', 'patched': '5421de8a34703d9872df0fa3841443eee8a28577fb50461cc5c01e2911bcd911', 'length': 36864, 'inverse': [[190, '05'], [213, '6c'], [217, '22'], [265, 'd000'], [345, 'b000'], [348, '08'], [456, '0d'], [496, 'd6'], [576, '08'], [648, '00000000'], [656, '0000'], [661, '00'], [665, '00'], [669, '00'], [684, '00'], [687, '0000000000'], [696, '0000'], [701, '00'], [705, '00'], [709, '00'], [724, '00'], [727, '0000000000'], [736, '00'], [741, '00'], [745, '00'], [749, '00'], [764, '00'], [767, '0000000000'], [776, '0000'], [782, '00'], [785, '00'], [789, '00'], [804, '00'], [807, '00'], [9710, '7e06'], [9956, '8805'], [10540, '4003'], [10959, '9d01'], [13631, '1703'], [13717, 'c1'], [13727, 'b7'], [18313, '33ce7e25'], [19109, '81c40ed3'], [19460, '68e0ffff'], [19764, '38dfffff'], [20866, '488b5c2450'], [28448, '000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'], [34272, '00'], [34276, '0000'], [34280, '0000'], [34284, '0000'], [35848, '0000'], [35852, '0000'], [35856, '0000']]}, '38965d90a823f03f.dll': {'stock': '777653b7547925b2c86bf5f343848564b3c07c6efd8df421acbb629604ed67ed', 'patched': 'deca1e86cd437116a1afab07bcf228274d9d51274b385a92ab7568d346759c75', 'length': 118784, 'inverse': [[190, '05'], [213, '88'], [217, '52'], [265, '00'], [345, 'e001'], [348, 'cc0f'], [648, '00000000'], [656, '0000'], [662, '00'], [665, '00'], [669, '0000'], [684, '00'], [687, '0000000000'], [696, '0000'], [701, '0000'], [705, '00'], [709, '0000'], [724, '00'], [727, '0000000000'], [736, '00'], [741, '0000'], [745, '00'], [749, '0000'], [764, '00'], [767, '0000000000'], [776, '0000'], [781, '0000'], [785, '00'], [789, '0000'], [804, '00'], [807, '00'], [32942, '9e0800'], [33188, 'a80700'], [33708, 'a00500'], [34127, 'fd0300'], [60848, '4883ec5833d2'], [81012, 'd84cffff'], [91968, '4883ec5833d2']]}}
LEGACY_RECORDS = {'351c49438bd38225.dll': {'stock': 'a8a8e156223ba10246f867e4513d272f5d89f0c3b5bd1a3167682176a429c4c1', 'patched': '36a5554bf0c1e8c65df9ece0343ea2d9ab9516e0fd8216fbda455b614956f7a4', 'length': 36864, 'inverse': [[190, '05'], [213, '6c'], [217, '22'], [265, 'd000'], [345, 'b000'], [348, '08'], [456, '0d'], [496, 'd6'], [576, '08'], [648, '00000000'], [656, '0000'], [661, '00'], [665, '00'], [669, '00'], [684, '00'], [687, '0000000000'], [696, '0000'], [701, '00'], [705, '00'], [709, '00'], [724, '00'], [727, '0000000000'], [736, '00'], [742, '00'], [745, '00'], [749, '00'], [764, '00'], [767, '0000000000'], [776, '0000'], [781, '0000'], [785, '00'], [789, '00'], [804, '00'], [807, '00'], [9710, '7e06'], [9956, '8805'], [10540, '4003'], [10959, '9d01'], [13631, '1703'], [13717, 'c1'], [13727, 'b7'], [18313, '33ce7e25'], [19109, '81c40ed3'], [19460, '68e0ffff'], [19764, '38dfffff'], [20866, '488b5c2450'], [28448, '000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'], [34272, '00'], [34276, '0000'], [34280, '0000'], [34284, '0000'], [35848, '0000'], [35852, '0000'], [35856, '0000']]}, '38965d90a823f03f.dll': {'stock': '777653b7547925b2c86bf5f343848564b3c07c6efd8df421acbb629604ed67ed', 'patched': '584a74c0e80a379b4da7eb4df5376609ad4f907c292f600b578ad134dd7e30b0', 'length': 118784, 'inverse': [[190, '05'], [213, '88'], [217, '52'], [265, '00'], [345, 'e001'], [348, 'cc0f'], [648, '00000000'], [656, '0000'], [661, '0000'], [665, '00'], [669, '0000'], [684, '00'], [687, '0000000000'], [696, '0000'], [701, '0000'], [705, '00'], [709, '0000'], [724, '00'], [727, '0000000000'], [736, '00'], [741, '0000'], [745, '00'], [749, '0000'], [764, '00'], [767, '0000000000'], [776, '0000'], [781, '0000'], [785, '00'], [789, '0000'], [804, '00'], [807, '00'], [32942, '9e0800'], [33188, 'a80700'], [33708, 'a00500'], [34127, 'fd0300'], [60848, '4883ec5833d2'], [81012, 'd84cffff'], [91968, '4883ec5833d2']]}}
PAYLOAD = zlib.decompress(base64.b64decode('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'))

def relative(op, at, to):
    return bytes.fromhex(op)+struct.pack("<i",to-at-5)

def align(n,a=0x1000): return (n+a-1)//a*a
def u32(b,at): return struct.unpack_from('<I',b,at)[0]
def put32(b,at,v): struct.pack_into('<I',b,at,v)

class PE:
    def __init__(self,data):
        self.data=data
        self.pe=u32(data,60)
        assert data[self.pe:self.pe+4]==b'PE\0\0'
        assert struct.unpack_from('<H',data,self.pe+4)[0]==0x8664
        self.opt=self.pe+24
        assert struct.unpack_from('<H',data,self.opt)[0]==0x20b
        self.header=self.opt+struct.unpack_from('<H',data,self.pe+20)[0]
        self.count=struct.unpack_from('<H',data,self.pe+6)[0]
        self.image_size=u32(data,self.opt+56)
        self.sections=[]
        for i in range(self.count):
            at=self.header+40*i
            vs,va,size,raw=struct.unpack_from('<4I',data,at+8)
            self.sections.append(dict(name=bytes(data[at:at+8]).rstrip(b'\0').decode(),
                                      vs=vs,va=va,size=size,raw=raw,flags=u32(data,at+36)))
    def offset(self,rva):
        for s in self.sections:
            if s['va']<=rva<s['va']+s['size']: return s['raw']+rva-s['va']
        raise ValueError('Unmapped RVA '+hex(rva))
    def directory(self,n): return struct.unpack_from('<II',self.data,self.opt+112+8*n)
    def runtime(self):
        va,size=self.directory(3)
        at=self.offset(va)
        return list(struct.iter_unpack('<III',self.data[at:at+size]))
    def exports(self):
        va,size=self.directory(0)
        at=self.offset(va)
        count=u32(self.data,at+24)
        functions,names,ordinals=struct.unpack_from('<III',self.data,at+28)
        result={}
        for i in range(count):
            n=self.offset(u32(self.data,self.offset(names)+4*i))
            end=self.data.index(0,n)
            ordinal=struct.unpack_from('<H',self.data,self.offset(ordinals)+2*i)[0]
            result[bytes(self.data[n:end]).decode()]=u32(self.data,self.offset(functions)+4*ordinal)
        return result

def append_payload(original,payload,kind):
    target=PE(original)
    obj=PE(payload)
    assert obj.directory(1)==(0,0), 'Payload must have no imports'
    assert obj.directory(5)==(0,0), 'Payload must be position-independent'
    assert u32(payload,obj.opt+16)==0, 'No DLL entry point'
    # Windows requires adjacent section RVAs: the payload starts at RVA 0x1000,
    # so using SizeOfImage directly leaves a page-sized hole and causes error 193.
    shift=align(target.image_size)-obj.sections[0]['va']
    exports=obj.exports()
    config=(shift,kind,0x3870,0x4d30,0xa260,0xa2c8,0xa1b4,0xa090,0xa0b8,0xa110) if kind==1 else (
        shift,kind,0x9550,0x11700,0x1dac0,0x1dca8,0x1d734,0x1d210,0x1d2b0,0x1d48c)
    payload=bytearray(payload)
    struct.pack_into('<10Q',payload,obj.offset(exports['configuration']),*config)
    runtime=target.runtime()+[(a+shift,z+shift,u+shift) for a,z,u in obj.runtime()]
    runtime.sort()
    assert all(a<z and z<=runtime[i+1][0] for i,(a,z,u) in enumerate(runtime[:-1]))
    table=b''.join(struct.pack('<III',*entry) for entry in runtime)
    combined=bytearray(original)
    total=target.count+len(obj.sections)
    header_end=target.header+total*40
    assert header_end<=u32(original,target.opt+60), 'No room for section headers'
    assert not any(original[target.header+target.count*40:header_end])
    pdata_rva=obj.directory(3)[0]
    code_size=u32(original,target.opt+4)
    init_size=u32(original,target.opt+8)
    image_size=target.image_size
    for i,s in enumerate(obj.sections):
        body=bytes(payload[s['raw']:s['raw']+s['size']])
        virtual=s['vs']
        if s['va']==pdata_rva:
            assert i==len(obj.sections)-1, 'Exception section must be last'
            body=table
            virtual=len(body)
        raw=align(len(combined),0x200)
        rawsize=align(len(body),0x200)
        combined.extend(b'\0'*(raw-len(combined)))
        combined.extend(body+b'\0'*(rawsize-len(body)))
        at=target.header+40*(target.count+i)
        name=('.pd'+str(i)).encode().ljust(8,b'\0')
        struct.pack_into('<8sIIIIIIHHI',combined,at,name,virtual,s['va']+shift,rawsize,raw,0,0,0,0,s['flags'])
        image_size=max(image_size,align(s['va']+shift+virtual))
        if s['flags'] & 0x20: code_size+=rawsize
        elif s['flags'] & 0x40: init_size+=rawsize
    struct.pack_into('<H',combined,target.pe+6,total)
    put32(combined,target.opt+56,image_size)
    put32(combined,target.opt+4,code_size)
    put32(combined,target.opt+8,init_size)
    put32(combined,target.opt+64,0) # Optional checksum unused for these user-mode DLLs.
    struct.pack_into('<II',combined,target.opt+112+24,shift+pdata_rva,len(table))
    return combined,{k:v+shift for k,v in exports.items()}

def build_pair(controller_stock,disc_stock,payload):
    if digest(controller_stock)!=STOCK_SHA or digest(disc_stock)!=DISC_SHA:
        raise ValueError('Unsupported original DLL pair')
    controller=transform(controller_stock)
    controller=bytearray(controller)
    def edit(b,at,old,new):
        p=PE(b).offset(at)
        if b[p:p+len(old)]!=old or len(old)!=len(new): raise ValueError('Patch-site mismatch '+hex(at))
        b[p:p+len(old)]=new
    # Restore disable routing. The new policy distinguishes it from region exits.
    edit(controller,0x5459,bytes.fromhex('b800000000'),bytes.fromhex('b88427d2ba'))
    edit(controller,0x7b20+4,struct.pack('<I',0x57b5c17e),struct.pack('<I',0x70644733))
    controller,ce=append_payload(controller,payload,1)
    for at in (0x31ed,0x32e3,0x352b,0x36ce,0x5803,0x5933):
        edit(controller,at,relative('e8',at,0x3870),relative('e8',at,ce['controller_execute']))
    disc,de=append_payload(disc_stock,payload,2)
    for at in (0x8cad,0x8da3,0x8fab,0x914e,0x14873):
        edit(disc,at,relative('e8',at,0x9550),relative('e8',at,de['disc_execute']))
    for at,name in ((0xf9b0,'disc_condition'),(0x17340,'disc_requested')):
        edit(disc,at,bytes.fromhex('4883ec5833d2'),relative('e9',at,de[name])+b'\x90')
    return bytes(controller),bytes(disc),dict(controller_exports=ce,disc_exports=de)

# Included verbatim in the standalone installer by package_round_guard.py.

def original_bytes(name, current):
    record = RECORDS[name]
    sha = digest(current)
    if sha == record['stock']:
        return current
    if name == DLL_NAME and sha == PATCHED_SHA:
        return transform(current, restore=True)
    for previous in (V34_RECORDS, V33_RECORDS, V31_RECORDS, V301_RECORDS, LEGACY_RECORDS):
        if sha == previous[name]['patched']:
            record = previous[name]
    if sha != record['patched']:
        raise ValueError('Unsupported or modified '+name+'. No changes made. SHA256: '+sha)
    result = bytearray(current[:record['length']])
    for at, original in record['inverse']:
        data = bytes.fromhex(original)
        result[at:at+len(data)] = data
    if digest(result) != record['stock']:
        raise ValueError('Original reconstruction failed for '+name)
    return bytes(result)


def run(target, restore=False, check=False):
    paths = [target, target.parent/DISC_NAME]
    # Validate both files and both backups before touching either installed DLL.
    current = [path.read_bytes() for path in paths]
    stocks = [original_bytes(path.name, data) for path, data in zip(paths, current)]
    controller, disc, _ = build_pair(stocks[0], stocks[1], PAYLOAD)
    candidates = [controller, disc]
    for path, data in zip(paths, candidates):
        if digest(data) != RECORDS[path.name]['patched']:
            raise ValueError('Candidate verification failed for '+path.name)
    backups = [path.with_name(path.name+'.personal-disc.original') for path in paths]
    for backup, stock in zip(backups, stocks):
        if backup.exists() and backup.read_bytes() != stock:
            raise ValueError('Existing backup does not match the original DLL. Stopped: '+str(backup))
    for path, data in zip(paths, current):
        version = (VERSION if digest(data) == RECORDS[path.name]['patched'] else
                   'v3.4 goal+tunnel A-button, no popup' if digest(data) == V34_RECORDS[path.name]['patched'] else
                   'v3.3 goal+tunnel A-button' if digest(data) == V33_RECORDS[path.name]['patched'] else
                   'v3.1 goal+tunnel' if digest(data) == V31_RECORDS[path.name]['patched'] else
                   'v3.0.1' if digest(data) == V301_RECORDS[path.name]['patched'] else
                   'v3.0.0 (broken DLL layout)' if digest(data) == LEGACY_RECORDS[path.name]['patched'] else
                   'v2' if path.name == DLL_NAME and digest(data) == PATCHED_SHA else 'original')
        print(str(path)+' ['+version+']')
    if check:
        print('Both DLLs compatible. Check passed; no files changed.')
        return
    if game_running():
        raise RuntimeError('Close Echo VR completely before patching or restoring.')
    for backup, stock in zip(backups, stocks):
        if not backup.exists():
            with backup.open('xb') as stream:
                stream.write(stock)
                stream.flush()
                os.fsync(stream.fileno())
        if backup.read_bytes() != stock:
            raise RuntimeError('Backup verification failed. Installed DLLs unchanged.')
    desired = stocks if restore else candidates
    changed = []
    try:
        # Recheck the entire pair after backup creation.
        if any(path.read_bytes() != before for path, before in zip(paths, current)):
            raise RuntimeError('A DLL changed during this operation. Stopped.')
        for index, path in enumerate(paths):
            if current[index] == desired[index]:
                continue
            # Record before calling: replacement may succeed but readback may fail.
            changed.append(index)
            replace_checked(path, current[index], desired[index])
        if any(path.read_bytes() != data for path, data in zip(paths, desired)):
            raise RuntimeError('Installed pair failed verification.')
    except Exception as error:
        failures = []
        for index in reversed(changed):
            try:
                present = paths[index].read_bytes()
                if present == current[index]:
                    continue
                if present != desired[index]:
                    raise RuntimeError('File changed unexpectedly; preserved for inspection')
                replace_checked(paths[index], present, current[index])
            except Exception as rollback_error:
                failures.append(paths[index].name+': '+str(rollback_error))
        if failures:
            raise RuntimeError('Install/restore failed: '+str(error)+
                               '. Rollback incomplete: '+'; '.join(failures)+
                               '. Close Echo VR and run RESTORE.cmd before launching it.') from error
        raise RuntimeError('Install/restore failed; prior DLL pair restored: '+str(error)) from error
    print('Original DLLs restored and verified.' if restore else 'Personal Disc '+VERSION+' installed and verified.')
    print('Backups: '+', '.join(str(path) for path in backups))
    if not restore:
        print('Restart Echo VR. Spawning is disabled during play, except actual timeouts and')
        print('from a goal until the tunnel opens. No arm popup: install DiscButton.dll, X summons the disc.')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target',help='Echo game folder, echovr.exe, scripts folder, or controller DLL')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--restore',action='store_true',help='Restore the exact supported original')
    group.add_argument('--check',action='store_true',help='Check compatibility without writing files')
    args = parser.parse_args()
    if os.name != 'nt':
        raise RuntimeError('This patch supports Windows PC Echo VR only.')
    if args.target:
        target = resolve_target(args.target)
    else:
        found = discover()
        if len(found) == 1:
            target = found[0]
        else:
            if found:
                print('Multiple installations found:')
                for path in found:
                    print('  '+str(path))
            target = resolve_target(input('Paste your Echo VR game folder (or echovr.exe path): ').strip())
    run(target,args.restore,args.check)

if __name__ == '__main__':
    try:
        main()
    except PermissionError:
        print('\nAccess denied. Right-click INSTALL.cmd or RESTORE.cmd and choose Run as administrator.',file=sys.stderr)
        sys.exit(1)
    except (OSError,ValueError,RuntimeError,EOFError) as error:
        print('\nERROR: '+str(error),file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print('\nCancelled.',file=sys.stderr)
        sys.exit(130)
