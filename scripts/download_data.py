"""Download published numerical tables only; never evaluate a property model."""
from pathlib import Path
import hashlib, json, datetime, urllib.request, argparse, subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'nist_index.html': 'https://www.nist.gov/system/files/documents/srd/NISTIR5078.htm',
    'nist_table1.pdf': 'https://www.nist.gov/system/files/documents/srd/NISTIR5078-Tab1.pdf',
    'nist_table2.pdf': 'https://www.nist.gov/system/files/documents/srd/NISTIR5078-Tab2.pdf',
    'nist_table3.pdf': 'https://www.nist.gov/system/files/documents/srd/NISTIR5078-Tab3.pdf',
    'nist_notes.pdf': 'https://www.nist.gov/system/files/documents/srd/NISTIR5078-Text.pdf',
    'feistel_wagner_2006.pdf': 'https://www.teos-10.org/pubs/Feistel_and_Wagner_2006.pdf',
    'nist_rights.html': 'https://www.nist.gov/open/copyright-fair-use-and-licensing-statements-srd-data-software-and-technical-series-publications',
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--direct', action='store_true', help='Bypass local proxy')
    parser.add_argument('--curl', action='store_true', help='Use Windows curl with offline revocation checks disabled (TLS certificates still verified)')
    args = parser.parse_args()
    raw = ROOT / 'raw_data'
    raw.mkdir(exist_ok=True)
    records = []
    for name, url in SOURCES.items():
        path = raw / name
        if not path.exists():
            if args.curl:
                command = ['curl.exe', '--ssl-no-revoke', '-L', '--fail', '--max-time', '120']
                if args.direct:
                    command += ['--noproxy', '*']
                temporary = path.with_suffix(path.suffix+'.part')
                subprocess.run(command + [url, '-o', str(temporary)], check=True)
                payload = temporary.read_bytes()
            else:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({})) if args.direct else urllib.request.build_opener()
                with opener.open(req, timeout=120) as response:
                    payload = response.read()
            if name.endswith('.pdf') and not payload.startswith(b'%PDF'):
                raise ValueError(f'Not a PDF: {url}')
            path.write_bytes(payload)
            if args.curl:
                temporary.unlink(missing_ok=True)
        records.append(dict(file=name, url=url, bytes=path.stat().st_size,
                            sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        print(name, path.stat().st_size)
    (raw/'manifest.json').write_text(json.dumps({'retrieved_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                                'sources': records}, indent=2), encoding='utf-8')

if __name__ == '__main__':
    main()
