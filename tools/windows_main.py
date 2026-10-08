"""Console executable entry point; Windows selects the user's default terminal."""
from pathlib import Path
import sys

if not getattr(sys, 'frozen', False):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import player


if __name__ == '__main__':
    player.main()
