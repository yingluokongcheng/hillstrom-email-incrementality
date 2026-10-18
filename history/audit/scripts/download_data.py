"""Explicit network step; never invoked by the offline audit."""
from pathlib import Path
import csv, gzip, hashlib, io, json, urllib.request
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = 'https://www.minethatdata.com/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv'
MIRROR = 'https://hillstorm1.s3.us-east-2.amazonaws.com/hillstorm_no_indices.csv.gz'
MIRROR_MD5 = 'a68a81291f53a14f4e29002629803ba3'

def sha(b):
    return hashlib.sha256(b).hexdigest()

def main():
    folder = ROOT / 'data/raw'
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / 'hillstrom.csv'
    manifest = folder / 'source_manifest.json'
    if dest.exists() or manifest.exists():
        meta = json.loads(manifest.read_text(encoding='utf-8'))
        assert sha(dest.read_bytes()) == meta['csv_sha256'], 'Cached data changed'
        print('Verified existing cache; no network request.')
        return
    frozen = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in [ROOT/'docs/PLAN_v1.md', ROOT/'config/plan.json']}
    attempts = []
    for url in [PRIMARY, MIRROR]:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'HillstromLocalAudit/1.0'})
            with urllib.request.urlopen(req, timeout=20) as response:
                payload = response.read()
                final_url = response.url
            if url == MIRROR:
                assert hashlib.md5(payload).hexdigest() == MIRROR_MD5, 'Mirror checksum differs from documented copy'
                data = gzip.decompress(payload)
            else:
                data = payload
            reader = csv.DictReader(io.StringIO(data.decode('utf-8-sig')))
            assert {'segment','conversion','zip_code','spend'}.issubset(reader.fieldnames or []), 'Not the expected CSV'
            attempts.append({'url': url, 'status': 'downloaded', 'bytes': len(payload)})
            # Retain source bytes and decoded CSV, without rewriting rows.
            if url == MIRROR:
                (folder / 'hillstrom.source.csv.gz').write_bytes(payload)
            dest.write_bytes(data)
            meta = {
                'downloaded_at_utc': datetime.now(timezone.utc).isoformat(),
                'source_url': url, 'final_url': final_url,
                'original_description': 'https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html',
                'mirror_documentation': 'https://www.uplift-modeling.com/en/latest/_modules/sklift/datasets/datasets.html',
                'used_mirror': url == MIRROR, 'original_bytes_verified': url == PRIMARY,
                'attempts': attempts, 'download_sha256': sha(payload), 'csv_sha256': sha(data),
                'csv_bytes': len(data), 'frozen_plan_sha256_before_download': frozen,
                'redistribution_license': 'Not established; public availability does not establish a license.'
            }
            manifest.write_text(json.dumps(meta, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
            print(json.dumps(meta, ensure_ascii=False, indent=2))
            return
        except Exception as exc:
            attempts.append({'url': url, 'status': 'failed', 'error': f'{type(exc).__name__}: {exc}'})
    raise RuntimeError(json.dumps(attempts))

if __name__ == '__main__':
    main()
