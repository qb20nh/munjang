#!/usr/bin/env python3
"""Build reproducible ZIP containers from a clean local package (stdlib only)."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
IGNORED={'.git','__pycache__','.pytest_cache','.mypy_cache','dist','.venv'}


def archive(source:Path,destination:Path,prefix:str)->dict:
    files=[]
    for p in sorted(source.rglob('*')):
        rel=p.relative_to(source)
        if any(part in IGNORED or part.startswith('.munjang-') for part in rel.parts):continue
        if p.is_symlink():raise ValueError(f'Refusing archive symlink: {p}')
        if not p.is_file() or p.suffix in ('.pyc','.pyo') or p.name=='.DS_Store':continue
        files.append((p,rel))
    destination.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p,rel in files:
            info=zipfile.ZipInfo((Path(prefix)/rel).as_posix(),date_time=(2026,9,15,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.create_system=3
            info.external_attr=(0o100644<<16)
            z.writestr(info,p.read_bytes())
    with zipfile.ZipFile(destination) as z:
        if z.testzip() is not None:raise ValueError('ZIP CRC verification failed')
        if any(n.startswith('/') or '..' in Path(n).parts for n in z.namelist()):raise ValueError('Unsafe archive path')
    return {'name':destination.name,'files':len(files),'bytes':destination.stat().st_size,
            'sha256':hashlib.sha256(destination.read_bytes()).hexdigest()}


def main():
    import json
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT.parent);a=p.parse_args()
    out=a.output.resolve()
    if ROOT==out or ROOT in out.parents:raise ValueError('Write release archives outside the source package')
    rows=[archive(ROOT,out/'munjang-1.0.0.zip','munjang'),
          archive(ROOT/'skills/korean-writing',out/'korean-writing-skill-1.0.0.zip','korean-writing')]
    (out/'munjang-SHA256SUMS.txt').write_text(''.join(f"{x['sha256']}  {x['name']}\n" for x in rows),encoding='ascii')
    print(json.dumps(rows,indent=2))


if __name__=='__main__':main()
