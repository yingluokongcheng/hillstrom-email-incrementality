"""Run deterministic audit and report with Python network calls disabled."""
from pathlib import Path
import runpy, socket, sys

def blocked(*args,**kwargs):
    raise RuntimeError('Network disabled in the offline audit runner')

socket.socket.connect=blocked
socket.socket.connect_ex=blocked
socket.create_connection=blocked
socket.getaddrinfo=blocked
root=Path(__file__).resolve().parents[1]
sys.argv=[str(root/'scripts/audit.py')]
runpy.run_path(sys.argv[0],run_name='__main__')
sys.argv=[str(root/'scripts/build_report.py')]
runpy.run_path(sys.argv[0],run_name='__main__')
