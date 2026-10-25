"""Opt-in single-process Windows startup and local dashboard launcher."""
import os
import sys
import threading
from pathlib import Path
from .dashboard import serve
from .runner import watch

class SingleInstance:
    def __init__(self, path):
        self.path=Path(path)
        self.fp=None
    def __enter__(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.fp=open(self.path,'a+b')
        self.fp.seek(0)
        self.fp.write(b'1')
        self.fp.flush()
        try:
            if os.name == 'nt':
                import msvcrt
                self.fp.seek(0)
                msvcrt.locking(self.fp.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(self.fp.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except (OSError,BlockingIOError) as exc:
            self.fp.close();self.fp=None
            raise RuntimeError('Autopilot already running; close the first copy instead of starting another.') from exc
        return self
    def __exit__(self,*args):
        try:
            if os.name == 'nt':
                import msvcrt
                self.fp.seek(0);msvcrt.locking(self.fp.fileno(),msvcrt.LK_UNLCK,1)
            else:
                import fcntl
                fcntl.flock(self.fp.fileno(),fcntl.LOCK_UN)
        finally:
            self.fp.close()


def run_autopilot(home:Path,interval=900,live=True,max_cases=8,port=8765):
    if interval < 300: raise ValueError('Minimum cycle interval: 300 seconds')
    with SingleInstance(home/'data'/'autopilot.lock'):
        def dashboard():
            try: serve(home,port)
            except OSError as exc: print(f'Dashboard server unavailable (maybe already open): {exc}',flush=True)
        threading.Thread(target=dashboard,daemon=True,name='FarmDashboard').start()
        print(f'Visit http://127.0.0.1:{port} — local drafts and continuous research on.',flush=True)
        watch(home,interval=interval,live=live,max_cases=max_cases)


def startup_file():
    if os.name != 'nt': raise ValueError('Windows autostart only. Start the autopilot manually on other OSes.')
    appdata=os.getenv('APPDATA')
    if not appdata: raise ValueError('APPDATA is not set. Cannot locate the Startup folder.')
    return Path(appdata)/'Microsoft'/'Windows'/'Start Menu'/'Programs'/'Startup'/'Operation Billion Autopilot.cmd'


def install_autostart(home: Path):
    p=startup_file()
    p.parent.mkdir(parents=True,exist_ok=True)
    # Windows start command requires a dummy title before quoted executable.
    # Escape % to avoid accidental environment expansion.
    project=str(home.resolve()).replace('%','%%')
    python=str(Path(sys.executable).resolve()).replace('%','%%')
    text='@echo off\r\ncd /d "'+project+'"\r\nstart "Operation Billion Autopilot" /min "'+python+'" -m botfarm autopilot --live\r\n'
    p.write_text(text,encoding='utf-8')
    return p


def uninstall_autostart():
    p=startup_file()
    p.unlink(missing_ok=True)
    return p
