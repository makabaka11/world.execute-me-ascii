"""Verify the actual onefile EXE without Python/FFmpeg discovery on PATH."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import player

EXE = ROOT/'dist/world-execute-mv.exe'


@unittest.skipUnless(sys.platform == 'win32' and EXE.is_file(), 'Build the Windows EXE first')
class ExeTests(unittest.TestCase):
    def test_exe_alone_in_unicode_directory_without_python_or_ffmpeg(self):
        with tempfile.TemporaryDirectory(prefix='mv exe ') as directory:
            base = Path(directory)
            work = base/'无 Python 环境'; work.mkdir()
            scratch = base/'scratch'; scratch.mkdir()
            standalone = work/'字符播放器.exe'
            shutil.copyfile(EXE, standalone)
            env = dict(os.environ, PATH=str(Path(os.environ['SystemRoot'])/'System32'),
                       TEMP=str(scratch), TMP=str(scratch), TMPDIR=str(scratch))
            for name in ('PYTHONHOME', 'PYTHONPATH', 'WEZTERM_PANE', 'WEZTERM_UNIX_SOCKET', 'WT_SESSION'):
                env.pop(name, None)
            film = player.Film()
            for t in (67.3, 124.2, 159.85, 183.2):
                result = subprocess.run([str(standalone), '--snapshot', str(t), '--plain',
                                         '--width', '125', '--height', '45'], cwd=work,
                                        env=env, capture_output=True, text=True,
                                        encoding='utf-8', check=True, timeout=30)
                self.assertEqual(result.stdout, film.render(t, 125, 45, True).plain()+'\n')
                self.assertEqual(list(work.iterdir()), [standalone])
                self.assertEqual(list(scratch.iterdir()), [])
            result = subprocess.run([str(standalone), '--help'], cwd=work, env=env,
                                    capture_output=True, text=True, encoding='utf-8',
                                    check=True, timeout=30)
            self.assertIn('--autoplay', result.stdout)
            self.assertEqual(list(scratch.iterdir()), [])

if __name__ == '__main__':
    unittest.main(verbosity=2)
