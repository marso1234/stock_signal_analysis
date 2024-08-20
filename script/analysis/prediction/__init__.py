import os.path
from pathlib import Path
import sys

current_path = Path(os.path.dirname(__file__))
dir_name = current_path.name
count = 0
while dir_name != 'script' and count < 100:
    count += 1
    current_path = current_path.parents[0]
    dir_name = current_path.name
    sys.path.append(str(current_path))