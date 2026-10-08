"""Platform adaptation and optional real Windows device integration tests."""
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import player
from terminal_io import Terminal
from windows_audio import WindowsAudio


class KeyboardTests(unittest.TestCase):
    def test_windows_arrow_prefixes_and_unknown_keys(self):
        keys = iter(['\xe0', 'K', '\x00', 'M', '\xe0', 'H', 'q'])
        pending = [7]
        class CRT:
            def kbhit(self): return pending[0] > 0
            def getwch(self):
                pending[0] -= 1
                return next(keys)
        terminal = Terminal()
        terminal.win = True
        terminal.msvcrt = CRT()
        self.assertEqual(terminal.read(0), '\x1b[D\x1b[Cq')

    def test_windows_poll_does_not_block_without_input(self):
        terminal = Terminal()
        terminal.win = True
        class CRT:
            def kbhit(self): return False
        terminal.msvcrt = CRT()
        start = time.monotonic()
        self.assertEqual(terminal.read(.02), '')
        self.assertLess(time.monotonic()-start, .2)


class PlayerTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform == 'win32', 'Windows backend selection')
    def test_ready_pause_arrows_chapters_volume_and_cleanup(self):
        class Audio:
            def __init__(self):
                self.state = {'time': 0., 'duration': 211.906667, 'playing': False}
                self.commands = []
                self.closed = False
            def snapshot(self): return self.state.copy()
            def command(self, value):
                self.commands.append(value)
                if value == 'play': self.state['playing'] = True
                if value == 'pause': self.state['playing'] = False
                if value.startswith('seek '): self.state['time'] = float(value.split()[1])
            def close(self): self.closed = True
        class FakeTerminal:
            def __init__(self): self.keys = iter([' ', ' ', '\x1b[C', '4', 'h', '+', '-', 'r', 'q'])
            def read(self, timeout): return next(self.keys)
            def size(self): return (128, 44)
        audio = Audio()
        args = player.argparse.Namespace(audio=str(ROOT/'media/song.mp3'), offset=None,
            autoplay=False, paused=False, start=0., fps=24, stop_after=None, report=None)
        with patch('windows_audio.WindowsAudio', return_value=audio), tempfile.TemporaryFile(mode='w+', encoding='utf-8') as output, patch('sys.stdout', output):
            player.run_terminal(args, player.Film(), FakeTerminal())
            output.seek(0)
            frames = output.read()
        self.assertTrue(audio.closed)
        self.assertIn('seek 5.0', audio.commands)
        self.assertIn('seek 125.708', audio.commands)
        self.assertIn('pause', audio.commands)
        self.assertIn('volume 0.8', audio.commands)
        self.assertTrue(frames.endswith('\x1b[0m\x1b[?7h\x1b[?25h\x1b[?1049l'))


@unittest.skipUnless(sys.platform == 'win32' and os.environ.get('MV_TEST_AUDIO') == '1',
                     'Set MV_TEST_AUDIO=1 to test the actual Windows audio device')
class DeviceTests(unittest.TestCase):
    def test_sample_clock_pause_play_seek_eof_and_reopen(self):
        with tempfile.TemporaryDirectory(prefix='mv 音频 ') as directory:
            path = Path(directory)/'测试 PCM.wav'
            with wave.open(str(path), 'wb') as source:
                source.setparams((2, 2, 44100, 0, 'NONE', 'not compressed'))
                source.writeframes(b'\0' * (44100 * 4))
            audio = WindowsAudio(path)
            try:
                self.assertAlmostEqual(audio.duration, 1.)
                audio.command('seek 0.25')
                self.assertAlmostEqual(audio.snapshot()['time'], .25, places=4)
                audio.command('play')
                time.sleep(.12)
                self.assertGreater(audio.snapshot()['time'], .3)
                audio.command('pause')
                position = audio.snapshot()['time']
                time.sleep(.1)
                self.assertEqual(audio.snapshot()['time'], position)
                audio.command('seek 0.5')
                self.assertFalse(audio.snapshot()['playing'])
                self.assertAlmostEqual(audio.snapshot()['time'], .5)
                audio.command('play')
                audio.command('seek 0.85')
                self.assertTrue(audio.snapshot()['playing'])
                time.sleep(.4)
                self.assertFalse(audio.snapshot()['playing'])
                self.assertAlmostEqual(audio.snapshot()['time'], 1.)
                audio.command('play')
                self.assertTrue(audio.snapshot()['playing'])
                self.assertLess(audio.snapshot()['time'], .1)
                audio.command('volume 0.5')
            finally:
                audio.close()
                audio.close()
            reopened = WindowsAudio(path)
            reopened.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
