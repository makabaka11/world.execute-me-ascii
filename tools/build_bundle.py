"""Build the Windows-only Python zipapp with its decoded audio."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import zipapp

ROOT = Path(__file__).resolve().parents[1]
FILES = ('player.py', 'scenes.py', 'terminal_io.py', 'windows_audio.py',
         'config.json', 'lyrics.json', 'spectrum.json', 'media/song.wav')


def main():
    if sys.platform != 'win32':
        raise SystemExit('请在 Windows 上构建。')
    if not (ROOT/'media/song.mp3').is_file():
        raise SystemExit('缺少 media/song.mp3，无法构建内嵌音乐的播放器。')
    sys.path.insert(0, str(ROOT))
    from windows_audio import prepare_audio
    pcm = prepare_audio(ROOT/'media/song.mp3')
    output = ROOT/'dist'
    output.mkdir(exist_ok=True)
    (ROOT/'.build').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='bundle-', dir=ROOT/'.build') as folder:
        stage = Path(folder)
        manifest = {'format': 1, 'platform': 'Windows', 'architectures': ['native-python'], 'files': {}}
        for name in FILES:
            data = pcm.read_bytes() if name == 'media/song.wav' else (ROOT/name).read_bytes()
            if name == 'config.json':
                config = json.loads(data)
                config['audio'] = 'media/song.wav'
                data = (json.dumps(config, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
            target = stage/name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            manifest['files'][name] = hashlib.sha256(data).hexdigest()
        (stage/'__main__.py').write_bytes((ROOT/'tools/bundle_main.py').read_bytes())
        (stage/'bundle-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n',encoding='utf-8')
        package = output/'world-execute-mv.pyz'
        zipapp.create_archive(stage, package, compressed=True)
    print(json.dumps({'artifact': str(package), 'embedded_audio': True}, ensure_ascii=False))


if __name__ == '__main__':
    main()
