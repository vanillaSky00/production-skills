#!/usr/bin/env python3
"""Wrap a Mermaid-engine-rendered SVG in a fixed-size illustrated card.

Supports Mermaid diagram types not handled by the bundled flowchart parser.
Native Mermaid labels should be SVG text, not foreignObject/HTML, for
CairoSVG-compatible PNG conversion. The original SVG remains authoritative.
"""
from __future__ import annotations
import argparse
import html
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from render_card import PALETTES, BLACK, fit_text

SVGNS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', SVGNS)

ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--svg',required=True,type=Path)
ap.add_argument('--out',required=True,type=Path)
ap.add_argument('--title',default='System Diagram')
ap.add_argument('--theme',choices=PALETTES.keys(),default='mint-editorial')
ap.add_argument('--size',choices=[1024,1536,2048],type=int,default=1024)
a=ap.parse_args()

native=ET.parse(a.svg).getroot()
if native.tag not in ('svg',f'{{{SVGNS}}}svg'):
    sys.exit('Input file is not an SVG document')
if any(tag.tag.endswith('foreignObject') for tag in native.iter()):
    print('WARNING: Native Mermaid SVG includes foreignObject labels; PNG converter may omit them. Use browser export instead.',file=sys.stderr)
viewbox=native.get('viewBox') or native.get('viewbox')
if not viewbox:
    def number(raw,default):
        found=re.search(r'[0-9.]+',raw or '')
        return float(found.group()) if found else default
    w=number(native.get('width'),1000);h=number(native.get('height'),800)
    viewbox=f'0 0 {w} {h}'
box=[float(x) for x in re.split(r'[\s,]+',viewbox.strip())]
if len(box)!=4 or box[2]<=0 or box[3]<=0: sys.exit('Invalid native SVG viewBox')
colors=PALETTES[a.theme]
editorial=bool(colors.get('editorial'))
if editorial:
    font, title_lines=fit_text(a.title,866,150,62,44,2)
    banner_y=44
    banner_h=145 if len(title_lines)==1 else 180
    by=banner_y+banner_h+28
    board=(50,by,924,975-by)
    content=(85,by+30,854,950-by-30)
    total_h=len(title_lines)*font*1.12
    title_base=banner_y+(banner_h-total_h)/2+font*.91
else:
    font,title_lines=fit_text(a.title,900,147,68,48,2)
    header_h=58+len(title_lines)*font*1.14
    by=max(205,min(247,header_h+27))
    board=(57,by,910,976-by)
    content=(86,by+54,852,908-by-28)
    title_base=46+font*.95
ratio=min(content[2]/box[2],content[3]/box[3])
render_w=box[2]*ratio;render_h=box[3]*ratio
x=content[0]+(content[2]-render_w)/2
y=content[1]+(content[3]-render_h)/2
native.attrib.update({'x':f'{x:.3f}', 'y':f'{y:.3f}', 'width':f'{render_w:.3f}', 'height':f'{render_h:.3f}', 'viewBox':viewbox, 'preserveAspectRatio':'xMidYMid meet'})
inner=ET.tostring(native,encoding='unicode')
head='\\n'.join(f'<text x="512" y="{title_base+i*font*1.12:.2f}" font-family="Inter, Noto Sans, Arial, sans-serif" font-weight="800" font-size="{font}" text-anchor="middle" fill="{BLACK}">{html.escape(line)}</text>' for i,line in enumerate(title_lines))
if editorial:
    deco=f'<rect x="51" y="{banner_y}" width="922" height="{banner_h}" rx="46" fill="{colors["title_bg"]}"/>'
    boardstyle=f'fill="{colors["panel"]}"'
    border=colors['border'];border_width=3
else:
    deco=f'<circle cx="911" cy="86" r="66" fill="{colors["accent"]}" opacity="0.09"/>'
    boardstyle=f'fill="{colors["panel"]}" stroke="{colors["accent"]}" stroke-width="3"'
    border=BLACK;border_width=5
svg=f'''<svg xmlns="{SVGNS}" width="{a.size}" height="{a.size}" viewBox="0 0 1024 1024">
<defs><clipPath id="cardclip"><rect x="7" y="7" width="1010" height="1010" rx="65"/></clipPath></defs>
<g clip-path="url(#cardclip)">
<rect width="1024" height="1024" fill="{colors['bg']}"/>
{deco}
<rect x="{board[0]}" y="{board[1]}" width="{board[2]}" height="{board[3]}" rx="{16 if editorial else 36}" {boardstyle}/>
{head}
{inner}
</g>
<rect x="7" y="7" width="1010" height="1010" rx="65" fill="none" stroke="{border}" stroke-width="{border_width}"/>
</svg>'''
a.out.parent.mkdir(parents=True,exist_ok=True)
if a.out.suffix.lower()=='.svg':
    a.out.write_text(svg,encoding='utf8')
elif a.out.suffix.lower()=='.png':
    try: import cairosvg
    except ImportError: sys.exit('PNG output requires cairosvg; use .svg or pip install cairosvg')
    cairosvg.svg2png(bytestring=svg.encode(),write_to=str(a.out),output_width=a.size,output_height=a.size)
    a.out.with_suffix('.svg').write_text(svg,encoding='utf8')
else:
    sys.exit('Use --out .svg or .png')
print(f'Created {a.out} ({a.size}x{a.size}) from native Mermaid SVG')
