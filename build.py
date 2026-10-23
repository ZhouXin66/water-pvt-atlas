"""Usage: python build.py [--download]. Open dist/index.html after completion."""
from pathlib import Path
import argparse,subprocess,sys

ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--download',action='store_true')
parser.add_argument('--direct',action='store_true')
parser.add_argument('--curl',action='store_true')
args=parser.parse_args()
if args.download:
    subprocess.run([sys.executable,str(ROOT/'scripts/download_data.py')]+(['--direct'] if args.direct else [])+(['--curl'] if args.curl else []),check=True,cwd=ROOT)
for script in ['scripts/extract_tables.py','scripts/build_model.py','tests/validate_data.py','scripts/build_html.py']:
    subprocess.run([sys.executable,str(ROOT/script)],check=True,cwd=ROOT)
