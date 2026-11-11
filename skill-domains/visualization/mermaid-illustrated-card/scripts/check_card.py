#!/usr/bin/env python3
"""Validate basic deliverable properties of illustrated square card PNGs."""
import argparse
import sys
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('image',type=Path)
p.add_argument('--size',type=int,default=1024)
args=p.parse_args()
try:
    from PIL import Image, ImageStat
except ImportError:
    sys.exit('Install pillow: pip install pillow')
if not args.image.is_file(): sys.exit(f'Missing file: {args.image}')
with Image.open(args.image) as im:
    if im.size != (args.size,args.size): sys.exit(f'FAIL: dimensions {im.size}; expected {(args.size,args.size)}')
    if im.mode not in ('RGB','RGBA'): sys.exit(f'FAIL: mode {im.mode}')
    rgb=im.convert('RGB')
    variance=ImageStat.Stat(rgb).var
    if max(variance)<200: sys.exit('FAIL: suspiciously blank or flat image')
    bbox=rgb.getbbox()
    if bbox is None: sys.exit('FAIL: blank image')
    print(f'PASS: {im.size[0]}x{im.size[1]}, {im.mode}, nonblank; visual+semantic QA still required.')
