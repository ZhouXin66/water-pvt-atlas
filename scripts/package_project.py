"""Distributable code/numerical teaching model; exclude third-party paper full text."""
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[1]
FILES=['README.md','DATA_SOURCES.md','THIRD_PARTY_NOTICES.md','LICENSE','requirements.txt','build.py','launch.py','Start-Water-PVT.cmd','.gitignore']
DIRS=['scripts','src','web','processed_data','dist']
def main():
    target=ROOT/'water-pvt-project.zip'
    paths=[ROOT/p for p in FILES]
    for directory in DIRS:
        paths += [p for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'downloads' not in p.parts and 'legacy_exports' not in p.parts]
    paths += [p for p in (ROOT/'tests').iterdir() if p.suffix in ('.py','.cjs')]
    paths += [ROOT/'raw_data/manifest.json']
    # Source numerical facts are included; fetch original PDFs via download_data.py.
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(set(paths)):z.write(p,p.relative_to(ROOT))
    with zipfile.ZipFile(target) as z:
        assert not any(n.endswith('.pdf') or n.startswith('raw_data/ice_') for n in z.namelist())
        assert z.testzip() is None
    print(target.name,target.stat().st_size,'bytes')
if __name__=='__main__':main()
