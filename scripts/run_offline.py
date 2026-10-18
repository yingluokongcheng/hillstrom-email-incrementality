"""Deterministic local analysis, with Python networking blocked."""
from pathlib import Path
import socket,runpy,sys
def blocked(*args,**kwargs):
    raise RuntimeError('Network disabled during local analysis')
socket.socket.connect=blocked
socket.socket.connect_ex=blocked
socket.create_connection=blocked
socket.getaddrinfo=blocked
root=Path(__file__).resolve().parents[1]
for name in ['analyze.py','build_report.py']:
    if (root/'scripts'/name).exists():
        sys.argv=[str(root/'scripts'/name)]
        runpy.run_path(sys.argv[0],run_name='__main__')
