"""Fetch the pinned June 2026 GFS source vintage without overwriting an archive.

Use --output-dir with a new directory to check for a revised source vintage.
Existing files are retained. The builder uses all quarters from this one vintage.
"""
from argparse import ArgumentParser
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
import hashlib
import json
import os
import tempfile

ROOT=Path(__file__).resolve().parents[2]
URLS={
 'quarterly.xlsx':'https://www.abs.gov.au/statistics/economy/government/government-finance-statistics-australia/jun-2026/Jun%20Quarter%202026.xlsx',
 'insights.html':'https://www.abs.gov.au/articles/insights-government-finance-statistics-june-2026',
}

def main():
    p=ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',type=Path,default=ROOT/'data/abs_gfs/raw/quarterly/jun-2026')
    args=p.parse_args(); args.output_dir.mkdir(parents=True,exist_ok=True)
    manifest_path=args.output_dir/'manifest.json'
    previous=json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
    manifest={}
    for name,url in URLS.items():
        path=args.output_dir/name
        if path.exists():
            content=path.read_bytes()
            entry=previous.get(name,{})
            if entry.get('sha256') and entry['sha256']!=hashlib.sha256(content).hexdigest():
                raise ValueError(f'Archive hash mismatch: {name}')
            timestamp=entry.get('retrieved_utc')
        else:
            with urlopen(Request(url,headers={'User-Agent':'APET/1.0 public data downloader'}),timeout=90) as response:
                content=response.read()
            if name.endswith('.xlsx') and not content.startswith(b'PK'): raise ValueError('Expected XLSX')
            if name.endswith('.html') and b'Insights into Government Finance Statistics' not in content: raise ValueError('Unexpected article')
            with tempfile.NamedTemporaryFile(dir=args.output_dir,delete=False) as tmp:
                tmp.write(content); temporary=tmp.name
            os.replace(temporary,path)
            timestamp=datetime.now(timezone.utc).isoformat()
        manifest[name]=dict(url=url,sha256=hashlib.sha256(content).hexdigest(),bytes=len(content),retrieved_utc=timestamp)
        print(f'Archived {path}')
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__': main()
