"""Build an x64 Windows onefile executable with Python and decoded PCM inside."""
import json
from pathlib import Path
import shutil
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    if sys.platform != 'win32' or struct.calcsize('P') != 8:
        raise SystemExit('请在 64 位 Windows Python 中构建。')
    try:
        import PyInstaller.__main__
    except ImportError:
        raise SystemExit('请先安装构建依赖：python -m pip install -r tools/requirements-exe.txt')
    from windows_audio import prepare_audio
    pcm = prepare_audio(ROOT/'media/song.mp3')
    stage = ROOT/'.build/exe-resources'
    (stage/'media').mkdir(parents=True, exist_ok=True)
    shutil.copyfile(pcm, stage/'media/song.wav')
    config = json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
    config['audio'] = 'media/song.wav'
    (stage/'config.json').write_text(json.dumps(config, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    arguments = ['--noconfirm', '--onefile', '--console',
                 '--noupx', '--icon', 'NONE', '--name', 'world-execute-mv',
                 '--paths', str(ROOT), '--distpath', str(ROOT/'dist'),
                 '--workpath', str(ROOT/'.build/pyinstaller'), '--specpath', str(ROOT/'.build'),
                 '--add-data', str(stage/'config.json')+':.',
                 '--add-data', str(stage/'media/song.wav')+':media']
    for name in ('lyrics.json', 'spectrum.json'):
        arguments += ['--add-data', str(ROOT/name)+':.']
    arguments.append(str(ROOT/'tools/windows_main.py'))
    PyInstaller.__main__.run(arguments)
    executable = ROOT/'dist/world-execute-mv.exe'
    print(json.dumps({'artifact': str(executable),
                      'python_required': False, 'ffmpeg_required': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
