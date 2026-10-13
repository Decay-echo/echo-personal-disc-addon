"""Installs or removes DiscButton.dll: the Oculus X button summons the personal disc.

Needs the Personal Disc Everywhere patch v3.3 or newer and EchoLoader (echoloader.json).
  py -3 install_discbutton.py [--target GAME_FOLDER]
  py -3 install_discbutton.py --uninstall
"""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
ENTRY = 'DiscButton.dll'
SETTINGS = """; DiscButton: a Touch button summons the personal disc
; (only while the disc is allowed: lobby, timeouts, and from a goal until the launcher countdown ends).
[summon]
; A or B (right controller), X or Y (left controller), or OFF. Every other button works as always.
; Also on the arcade tablet's SETTINGS page; changes apply while Echo runs.
button=X
; 0 = Echo still sees the button as well
; 1 = Echo no longer sees it (it only summons the disc)
hide_from_echo=0
"""

spec = importlib.util.spec_from_file_location('patcher', HERE.parent / 'echo_game.py')
patcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patcher)


def game_bin(target):
    if target:
        scripts = patcher.resolve_target(target).parent
    else:
        found = patcher.discover()
        if len(found) != 1:
            raise RuntimeError('Pass --target with your Echo VR game folder.')
        scripts = found[0].parent
    return scripts.parent  # bin\win10


def entries(config):
    return [p for p in config.get('plugins', []) if isinstance(p, dict) and p.get('file', '').lower() == ENTRY.lower()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', help='Echo game folder, echovr.exe, scripts folder, or controller DLL')
    parser.add_argument('--uninstall', action='store_true')
    args = parser.parse_args()
    bin_ = game_bin(args.target)
    loader, plugins = bin_ / 'echoloader.json', bin_ / 'plugins'
    if not loader.is_file() or not plugins.is_dir():
        raise RuntimeError('EchoLoader not found (missing echoloader.json or plugins folder) in ' + str(bin_))
    if patcher.game_running():
        raise RuntimeError('Close Echo VR completely first.')
    config = json.loads(loader.read_text(encoding='utf-8'))
    backup = loader.with_name('echoloader.json.discbutton-backup')
    if not backup.exists():
        shutil.copy2(loader, backup)
    if args.uninstall:
        config['plugins'] = [p for p in config.get('plugins', []) if p not in entries(config)]
        loader.write_text(json.dumps(config, indent=4) + '\n', encoding='utf-8')
        (plugins / ENTRY).unlink(missing_ok=True)
        print('DiscButton removed. Settings kept in', plugins / 'DiscButton')
        return
    built = HERE / 'build' / ENTRY
    if not built.is_file():
        raise RuntimeError('Build it first: run build_discbutton.cmd')
    shutil.copy2(built, plugins / ENTRY)
    settings = plugins / 'DiscButton' / 'settings.ini'
    settings.parent.mkdir(exist_ok=True)
    if settings.exists() and '[summon]' not in settings.read_text(encoding='utf-8', errors='replace'):
        shutil.copy2(settings, settings.with_name('settings.ini.old'))  # the old A-button settings
        settings.unlink()
        print('Old A-button settings replaced (kept as settings.ini.old): the disc is on X now and A works as always')
    if not settings.exists():
        settings.write_text(SETTINGS, encoding='utf-8')
    else:
        text = settings.read_text(encoding='utf-8', errors='replace')
        fixed = '\n'.join('button=X' if line.strip().replace(' ', '').lower() == 'button=off' else line for line in text.splitlines()) + '\n'
        if fixed != text and fixed.rstrip('\n') != text.rstrip('\n'):  # installing means you want it
            settings.write_text(fixed, encoding='utf-8')
            print('The summon button was OFF (the tablet\'s ALL OFF?): it is X again')
    if not entries(config):
        config.setdefault('plugins', []).append({'file': ENTRY})
        loader.write_text(json.dumps(config, indent=4) + '\n', encoding='utf-8')
    print('DiscButton installed:', plugins / ENTRY)
    print('Settings:', settings)
    print('Log after playing: %LOCALAPPDATA%\\DiscButton\\discbutton.log')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError) as error:
        print('ERROR: ' + str(error), file=sys.stderr)
        sys.exit(1)
