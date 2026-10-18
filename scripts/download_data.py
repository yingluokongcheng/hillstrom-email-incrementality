"""Restore the exact audited data cache; explicitly separate from offline analysis."""
from pathlib import Path
import gzip,hashlib,json,urllib.request
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]

def sha(b): return hashlib.sha256(b).hexdigest()
def main():
    folder=ROOT/'data/raw';folder.mkdir(parents=True,exist_ok=True)
    source=json.loads((folder/'source_manifest.json').read_text(encoding='utf-8'))
    raw=folder/'hillstrom.csv';packed=folder/'hillstrom.source.csv.gz'
    if packed.exists():
        payload=packed.read_bytes()
    else:
        request=urllib.request.Request(source['source_url'],headers={'User-Agent':'HillstromReproduction/1.0'})
        with urllib.request.urlopen(request,timeout=30) as response:
            payload=response.read()
    assert sha(payload)==source['download_sha256'],'Compressed source differs from audited hash; stop'
    data=gzip.decompress(payload)
    assert sha(data)==source['csv_sha256'],'CSV differs from audited hash; stop'
    # Never overwrite a changed local cache. Historical metadata remains unchanged.
    for path,content in [(raw,data),(packed,payload),
                         (ROOT/'history/audit/data/raw/hillstrom.csv',data),
                         (ROOT/'history/audit/data/raw/hillstrom.source.csv.gz',payload)]:
        if path.exists(): assert path.read_bytes()==content,f'Changed cache: {path}'
        else: path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(content)
    # This row-level audit extract is generated locally, not included in the repository bundle.
    df=pd.read_csv(raw);mask=df.duplicated(keep=False);duplicates=df.loc[mask].copy()
    duplicates.insert(0,'csv_line',df.index[mask]+2)
    record_path=ROOT/'history/audit/reports/identical_rows.csv'
    content=duplicates.to_csv(index=False,lineterminator='\n',float_format='%.12g').encode('utf-8')
    preservation=json.loads((ROOT/'docs/audit_preservation.json').read_text(encoding='utf-8'))
    assert sha(content)==preservation['reports/identical_rows.csv'],'Generated duplicate extract differs'
    if record_path.exists(): assert record_path.read_bytes()==content
    else: record_path.write_bytes(content)
    print('Exact data cache and row-level audit extract ready; source metadata unchanged.')

if __name__=='__main__':main()
