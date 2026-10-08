"""Windows console setup and timed keyboard input."""
import os
import sys
import time


class Terminal:
    def __enter__(self):
        if not sys.stdin.isatty():
            raise RuntimeError('请在 Windows Terminal 或其他 Windows 终端中运行。')
        self.old_stdout = sys.stdout
        import ctypes
        from ctypes import wintypes
        import msvcrt
        self.ctypes = ctypes
        self.msvcrt = msvcrt
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.kernel.GetStdHandle.argtypes = [wintypes.DWORD]
        self.kernel.GetStdHandle.restype = wintypes.HANDLE
        self.kernel.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        self.kernel.GetConsoleMode.restype = wintypes.BOOL
        self.kernel.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.kernel.SetConsoleMode.restype = wintypes.BOOL
        self.input = self.kernel.GetStdHandle(-10 & 0xffffffff)
        self.output = msvcrt.get_osfhandle(sys.stdout.fileno())
        self.input_mode = wintypes.DWORD()
        self.output_mode = wintypes.DWORD()
        for handle, mode in ((self.input, self.input_mode), (self.output, self.output_mode)):
            if not self.kernel.GetConsoleMode(handle, ctypes.byref(mode)):
                raise RuntimeError('请直接在终端中播放，不要重定向输入或输出。')
        # Disable echo, line input, Quick Edit and VT input. msvcrt reads
        # native key events; retain processed Ctrl+C for clean shutdown.
        if not self.kernel.SetConsoleMode(self.input, (self.input_mode.value | 0x80) & ~0x246):
            raise ctypes.WinError(ctypes.get_last_error())
        if not self.kernel.SetConsoleMode(self.output, self.output_mode.value | 0x4):
            self.kernel.SetConsoleMode(self.input, self.input_mode.value)
            raise ctypes.WinError(ctypes.get_last_error())
        # A separate UTF-8 stream leaves the caller's stream settings intact.
        sys.stdout = os.fdopen(os.dup(sys.stdout.fileno()), 'w', encoding='utf-8',
                               buffering=1, newline='')
        return self

    def read(self, timeout):
        deadline = time.monotonic() + timeout
        while not self.msvcrt.kbhit():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return ''
            time.sleep(min(.005, remaining))
        keys = []
        while self.msvcrt.kbhit():
            key = self.msvcrt.getwch()
            if key in ('\x00', '\xe0'):
                key = {'K': '\x1b[D', 'M': '\x1b[C'}.get(self.msvcrt.getwch(), '')
            keys.append(key)
        return ''.join(keys)

    def size(self):
        try:
            return os.get_terminal_size(sys.stdout.fileno())
        except OSError:
            return os.terminal_size((100, 36))

    def __exit__(self, *_):
        try:
            sys.stdout.flush()
        finally:
            sys.stdout.close()
            sys.stdout = self.old_stdout
            self.kernel.SetConsoleMode(self.input, self.input_mode.value)
            self.kernel.SetConsoleMode(self.output, self.output_mode.value)
