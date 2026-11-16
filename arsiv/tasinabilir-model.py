#!/usr/bin/env python3
"""Create relocated MuJoCo XMLs for archived machines without touching originals."""
import argparse
import os
from pathlib import Path
import xml.etree.ElementTree as ET

def relocate(root):
    duet=root/'work/duet'
    for name in ('duet','hex'):
        source=duet/(name+'.xml')
        model=ET.parse(source)
        for node in model.iter():
            if 'file' not in node.attrib:continue
            recorded=Path(node.attrib['file'])
            if not recorded.is_absolute():continue
            if 'outputs' not in recorded.parts:
                raise ValueError(f'Beklenmeyen kaynak konumu {recorded}')
            new=root.joinpath(*recorded.parts[recorded.parts.index('outputs'):])
            if not new.is_file():
                raise FileNotFoundError(new)
            node.set('file',os.path.relpath(new,duet))
        dest=duet/(name+'.portable.xml')
        model.write(dest,encoding='utf-8',xml_declaration=True)
        print(dest)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('deney_klasoru',type=Path)
    relocate(p.parse_args().deney_klasoru.resolve())
