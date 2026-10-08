"""PCM playback driven by the Windows waveOut device's sample counter.

FFmpeg is needed once to decode MP3 into a cached WAV. A distributed Windows
bundle embeds that WAV and needs only Python and the Windows audio APIs.
"""
import ctypes
from ctypes import wintypes
import hashlib
from pathlib import Path
import shutil
import subprocess
import wave


class WaveFormat(ctypes.Structure):
    _fields_ = [('tag', wintypes.WORD), ('channels', wintypes.WORD),
                ('rate', wintypes.DWORD), ('bytes_per_second', wintypes.DWORD),
                ('block_align', wintypes.WORD), ('bits', wintypes.WORD),
                ('extra', wintypes.WORD)]


class WaveHeader(ctypes.Structure):
    _fields_ = [('data', ctypes.c_void_p), ('length', wintypes.DWORD),
                ('recorded', wintypes.DWORD), ('user', ctypes.c_size_t),
                ('flags', wintypes.DWORD), ('loops', wintypes.DWORD),
                ('next', ctypes.c_void_p), ('reserved', ctypes.c_size_t)]


class MMTimeValue(ctypes.Union):
    _fields_ = [('samples', wintypes.DWORD), ('bytes', wintypes.DWORD),
                ('padding', ctypes.c_byte * 8)]


class MMTime(ctypes.Structure):
    _fields_ = [('type', wintypes.UINT), ('value', MMTimeValue)]


def prepare_audio(path):
    """Decode once, keyed by file contents; never put generated audio in Git."""
    path = Path(path).resolve()
    if path.suffix.lower() == '.wav':
        return path
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    cache = Path(__file__).resolve().parent / '.build' / 'pcm'
    target = cache / (digest + '.wav')
    if not target.is_file():
        ffmpeg = shutil.which('ffmpeg')
        if not ffmpeg:
            raise RuntimeError('首次播放需要 FFmpeg 解码 MP3。请安装 FFmpeg，或用 --audio 指定 PCM WAV。')
        cache.mkdir(parents=True, exist_ok=True)
        temporary = cache / (digest + '.tmp.wav')
        result = subprocess.run([ffmpeg, '-nostdin', '-v', 'error', '-y', '-i', str(path),
                                 '-map', '0:a:0', '-vn', '-ac', '2', '-ar', '44100',
                                 '-c:a', 'pcm_s16le', str(temporary)],
                                capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode:
            temporary.unlink(missing_ok=True)
            raise RuntimeError('音频解码失败：' + result.stderr.decode('utf-8', errors='replace'))
        temporary.replace(target)
    return target


class WindowsAudio:
    def __init__(self, path):
        with wave.open(str(prepare_audio(path)), 'rb') as source:
            if source.getcomptype() != 'NONE' or source.getsampwidth() != 2:
                raise RuntimeError('Windows 音频后端需要 16 位 PCM WAV。')
            self.rate = source.getframerate()
            self.align = source.getnchannels() * source.getsampwidth()
            self.frames = source.getnframes()
            payload = source.readframes(self.frames)
            format = WaveFormat(1, source.getnchannels(), self.rate,
                                self.rate * self.align, self.align, 16, 0)
        self.duration = self.frames / self.rate
        if not self.frames:
            raise RuntimeError('音频文件为空。')
        self.buffer = ctypes.create_string_buffer(payload)
        self.handle = wintypes.HANDLE()
        self.dll = ctypes.WinDLL('winmm')
        self.dll.waveOutOpen.argtypes = [ctypes.POINTER(wintypes.HANDLE), wintypes.UINT,
                                         ctypes.POINTER(WaveFormat), ctypes.c_size_t,
                                         ctypes.c_size_t, wintypes.DWORD]
        self.dll.waveOutOpen.restype = wintypes.UINT
        for name in ('waveOutPrepareHeader', 'waveOutUnprepareHeader', 'waveOutWrite'):
            function = getattr(self.dll, name)
            function.argtypes = [wintypes.HANDLE, ctypes.POINTER(WaveHeader), wintypes.UINT]
            function.restype = wintypes.UINT
        for name in ('waveOutPause', 'waveOutRestart', 'waveOutReset', 'waveOutClose'):
            function = getattr(self.dll, name)
            function.argtypes = [wintypes.HANDLE]
            function.restype = wintypes.UINT
        self.dll.waveOutGetPosition.argtypes = [wintypes.HANDLE, ctypes.POINTER(MMTime), wintypes.UINT]
        self.dll.waveOutGetPosition.restype = wintypes.UINT
        self.dll.waveOutSetVolume.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.dll.waveOutSetVolume.restype = wintypes.UINT
        self.dll.waveOutGetErrorTextW.argtypes = [wintypes.UINT, wintypes.LPWSTR, wintypes.UINT]
        self.closed = True
        self.header = None
        self.offset = 0
        self.playing = False
        self._check(self.dll.waveOutOpen(ctypes.byref(self.handle), 0xffffffff,
                                         ctypes.byref(format), 0, 0, 0))
        self.closed = False
        try:
            self.command('volume 0.75')
        except Exception:
            self.close()
            raise

    def _check(self, code):
        if code:
            text = ctypes.create_unicode_buffer(512)
            self.dll.waveOutGetErrorTextW(code, text, len(text))
            raise RuntimeError(f'Windows 音频错误 ({code}): {text.value}')

    def snapshot(self):
        samples = 0
        if self.header is not None:
            position = MMTime(2)  # TIME_SAMPLES: consumed sample frames, not elapsed wall time.
            self._check(self.dll.waveOutGetPosition(self.handle, ctypes.byref(position), ctypes.sizeof(position)))
            if position.type == 2:
                samples = position.value.samples
            elif position.type == 4:  # A driver may return TIME_BYTES instead.
                samples = position.value.bytes // self.align
            elif position.type == 1:  # TIME_MS.
                samples = round(position.value.samples * self.rate / 1000)
            else:
                raise RuntimeError('音频设备没有提供支持的播放时钟。')
            if self.header.flags & 1:  # WHDR_DONE.
                samples = self.frames - self.offset
        frame = min(self.frames, self.offset + samples)
        if frame >= self.frames:
            self.playing = False
        return {'time': frame / self.rate, 'duration': self.duration, 'playing': self.playing}

    def _release_header(self):
        self._check(self.dll.waveOutReset(self.handle))
        if self.header is not None:
            self._check(self.dll.waveOutUnprepareHeader(self.handle, ctypes.byref(self.header), ctypes.sizeof(self.header)))
            self.header = None

    def _seek(self, seconds):
        self._release_header()
        self.offset = round(min(max(0, seconds), self.duration) * self.rate)
        self.offset = min(self.frames, self.offset)
        if self.offset == self.frames:
            self.playing = False
            return
        self._check(self.dll.waveOutPause(self.handle))
        self.header = WaveHeader(ctypes.addressof(self.buffer) + self.offset * self.align,
                                 (self.frames - self.offset) * self.align)
        self._check(self.dll.waveOutPrepareHeader(self.handle, ctypes.byref(self.header), ctypes.sizeof(self.header)))
        self._check(self.dll.waveOutWrite(self.handle, ctypes.byref(self.header), ctypes.sizeof(self.header)))
        if self.playing:
            self._check(self.dll.waveOutRestart(self.handle))

    def command(self, command):
        fields = command.split()
        name = fields[0]
        if name == 'play':
            if self.header is None or self.snapshot()['time'] >= self.duration:
                self._seek(0)
            self._check(self.dll.waveOutRestart(self.handle))
            self.playing = True
        elif name == 'pause':
            self._check(self.dll.waveOutPause(self.handle))
            self.playing = False
        elif name == 'seek':
            self.snapshot()
            self._seek(float(fields[1]))
        elif name == 'volume':
            volume = round(min(1, max(0, float(fields[1]))) * 65535)
            self._check(self.dll.waveOutSetVolume(self.handle, volume | (volume << 16)))
        elif name == 'quit':
            self.close()
        else:
            raise ValueError('Unknown audio command: ' + command)

    def close(self):
        if not self.closed:
            self._release_header()
            self._check(self.dll.waveOutClose(self.handle))
            self.closed = True
