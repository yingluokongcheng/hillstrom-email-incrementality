"""Rebuild in a new directory, preserve it, compare bytes, and save validation evidence."""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess, sys
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--destination',type=Path,required=True)
    args=parser.parse_args()
    dest=args.destination.resolve()
    if dest.exists():
        raise FileExistsError('Use a new verification directory; existing evidence is never deleted.')
    dest.mkdir(parents=True)
    for folder in ['scripts','config','docs','data']:
        shutil.copytree(ROOT/folder,dest/folder,ignore=shutil.ignore_patterns('__pycache__'))
    env={**os.environ,'PYTHONIOENCODING':'utf-8'}
    test=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(ROOT/'tests'),'-v'],
                        capture_output=True,text=True,encoding='utf-8',env=env)
    (ROOT/'reports/test_results.txt').write_text(test.stdout+test.stderr,encoding='utf-8')
    assert test.returncode==0, 'Semantic tests failed'
    rerun=subprocess.run([sys.executable,str(dest/'scripts/run_offline.py')],cwd=dest,
                         capture_output=True,text=True,encoding='utf-8',env=env)
    (dest/'rerun.log').write_text(rerun.stdout+rerun.stderr,encoding='utf-8')
    assert rerun.returncode==0, 'Offline rebuild failed'
    records=[]
    for p in sorted((dest/'reports').iterdir()):
        original=ROOT/'reports'/p.name
        records.append({'file':p.name,'sha256':digest(p),'byte_identical':p.read_bytes()==original.read_bytes()})
    assert all(r['byte_identical'] for r in records)
    # Validate local HTML links without a browser/network request.
    from html.parser import HTMLParser
    class Links(HTMLParser):
        def __init__(self): super().__init__(); self.paths=[]
        def handle_starttag(self,tag,attrs):
            if tag=='a':
                self.paths.extend(v for k,v in attrs if k=='href' and not v.startswith(('http:','https:','#')))
    links=Links(); links.feed((ROOT/'reports/Hillstrom数据审计.html').read_text(encoding='utf-8'))
    missing=[v for v in links.paths if v!='verification.json' and not (ROOT/'reports'/v).exists()]
    assert not missing, missing
    result={'verified_at_utc':datetime.now(timezone.utc).isoformat(),
            'tests_passed':True,'test_methods':6,'test_log':'test_results.txt',
            'independent_directory':str(dest),'network_block':'Python socket connect/connect_ex/create_connection/getaddrinfo blocked; not OS firewall',
            'reproduced_files':records,'all_byte_identical':True,'local_html_links_checked':len(links.paths),
            'raw_sha256':digest(ROOT/'data/raw/hillstrom.csv'),'effect_analysis_run':False,
            'note':'Binomial simulations in tests validate planning formulas on hypothetical scenarios only.'}
    (ROOT/'reports/verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'tests_passed':True,'reproduced_files':len(records),'all_byte_identical':True,'local_links':len(links.paths)}))

if __name__=='__main__':
    main()
