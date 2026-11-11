#!/usr/bin/env python3
"""Render a Mermaid flowchart / JSON diagram spec as a fixed-size illustrated SVG card.

Requirements: Graphviz `dot` in PATH; Python standard library. PNG additionally
requires `cairosvg` (pip install cairosvg). For Mermaid constructs outside the
supported flowchart subset, transcribe the exact graph to --spec JSON instead.
"""
from __future__ import annotations

import argparse
import html
import json
import math
import re
import shlex
import shutil
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path

PALETTES = {
    # The primary user-approved visual family: white editorial cards with a mint title pill.
    "mint-editorial": {
        "bg": "#FFFFFF", "panel": "#FFFFFF", "accent": "#2BD7A9",
        "title_bg": "#2ED9AA", "border": "#B8BFBE", "editorial": True,
        "node_fills": ["#2DD9A9", "#BFFFF0", "#E6FFF7", "#88EACA", "#D3FAEF", "#FFFFFF"],
    },
    "mint": {"bg": "#34EDBE", "panel": "#1FE2B5", "accent": "#0EA889"},
    "sky": {"bg": "#4DCDED", "panel": "#43BFE8", "accent": "#178EAE"},
    "peach": {"bg": "#FFA678", "panel": "#FD9361", "accent": "#D9754B"},
    "lavender": {"bg": "#A2B0FA", "panel": "#93A4F2", "accent": "#5F76DD"},
    "lime": {"bg": "#58DF3D", "panel": "#44D333", "accent": "#28A72F"},
    "pink": {"bg": "#E58CD3", "panel": "#D979C6", "accent": "#B85CA9"},
}
NODE_COLORS = ["#FFF19A", "#BFE7FF", "#FFD2DF", "#D2FBB8", "#FFCAAA", "#D7CCFF"]
BLACK = "#172222"

# Tiny, original outline pictograms rendered as vector paths (viewBox 0 0 24 24).
ICONS = {
    "user": ['<circle cx="12" cy="7" r="3.6"/>', '<path d="M4.5 21v-2a7.5 7.5 0 0 1 15 0v2"/>'],
    "brain": ['<path d="M11.8 5.3C9.5 2 5.5 4 5.5 7a4.1 4.1 0 0 0-1.7 6.9A4 4 0 0 0 7 20a4 4 0 0 0 4.8-3.3M12.2 5.3c2.3-3.3 6.3-1.3 6.3 1.7a4.1 4.1 0 0 1 1.7 6.9A4 4 0 0 1 17 20a4 4 0 0 1-4.8-3.3M12 4v15"/>', '<path d="M8 10l2 2M16 10l-2 2"/>'],
    "database": ['<ellipse cx="12" cy="5" rx="8" ry="3"/>', '<path d="M4 5v14c0 4 16 4 16 0V5M4 12c0 4 16 4 16 0"/>'],
    "server": ['<rect x="3" y="3" width="18" height="8" rx="2"/>','<rect x="3" y="13" width="18" height="8" rx="2"/>','<path d="M7 7h.01M7 17h.01M11 7h7M11 17h7"/>'],
    "cloud": ['<path d="M7 19h11a4 4 0 0 0 .5-8 6.6 6.6 0 0 0-12.8-.9A4.5 4.5 0 0 0 7 19Z"/>'],
    "code": ['<path d="m8 7-5 5 5 5M16 7l5 5-5 5M14 4l-4 16"/>'],
    "check": ['<circle cx="12" cy="12" r="9"/>', '<path d="m7.5 12 3.1 3.1 6-6.2"/>'],
    "gear": ['<path d="M10 2h4l.8 2.5 2.4.9 2.4-1.2 2.5 3.2-1.7 2.1.2 2.6 1.9 2-2.4 3.3-2.5-.8-2.2 1.2L14 22h-4l-.8-2.5-2.4-.9-2.4 1.2L2 16.6l1.7-2.1-.2-2.6-1.9-2L4 6.6l2.5.8 2.2-1.2Z"/>','<circle cx="12" cy="12" r="3"/>'],
    "search": ['<circle cx="10" cy="10" r="6.5"/>','<path d="m15 15 6 6"/>'],
    "file": ['<path d="M6 2h8l5 5v15H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2ZM14 2v6h5M8 13h8M8 17h8"/>'],
    "chart": ['<path d="M3 3v18h18M7 17v-6M12 17V7M17 17V4"/>'],
    "send": ['<path d="m22 2-8.2 20-3.4-8.4L2 10.2 22 2ZM10.4 13.6 22 2"/>'],
    "shield": ['<path d="M12 2 20 5v6c0 5-3 9-8 11C7 20 4 16 4 11V5Z"/>','<path d="m8.5 12 2.5 2.5 4.5-5"/>'],
    "clock": ['<circle cx="12" cy="12" r="9"/>','<path d="M12 6v6l4.5 2.5"/>'],
    "layers": ['<path d="M12 2 2 7l10 5 10-5-10-5ZM2 12l10 5 10-5M2 17l10 5 10-5"/>'],
    "box": ['<rect x="3" y="3" width="18" height="18" rx="2"/>','<path d="M8 8h8M8 12h8M8 16h5"/>'],
}

def semantic_icon(label: str) -> str:
    t = label.lower()
    words = [
        ("database", ["database", "postgres", "mysql", "sql", "storage", "db", "資料庫", "儲存"]),
        ("brain", ["llm", "model", "agent", "ai", "推理", "模型", "生成", "research"]),
        ("user", ["user", "human", "client", "customer", "使用者", "客戶"]),
        ("cloud", ["cloud", "aws", "s3", "雲端"]),
        ("server", ["api", "backend", "server", "service", "worker", "服務", "伺服器"]),
        ("shield", ["auth", "security", "verify", "驗證", "權限"]),
        ("chart", ["metrics", "report", "chart", "monitor", "kpi", "報表", "監控"]),
        ("search", ["search", "retrieve", "query", "rag", "檢索", "搜尋"]),
        ("check", ["done", "success", "pass", "approved", "check", "完成", "成功"]),
        ("file", ["document", "doc", "file", "text", "文件", "資料"]),
        ("code", ["code", "build", "git", "deploy", "程式", "部署"]),
        ("gear", ["process", "pipeline", "transform", "compute", "執行", "處理"]),
        ("clock", ["schedule", "wait", "delay", "time", "排程", "等待"]),
        ("send", ["output", "response", "send", "reply", "結果", "回覆"]),
    ]
    for icon, keys in words:
        if any(k in t for k in keys):
            return icon
    return "box"

NODE_DECL = re.compile(r'(?<![\w-])([A-Za-z_][\w-]*)(\[\[.*?\]\]|\[\(.*?\)\]|\(\(.*?\)\)|\{.*?\}|\[.*?\]|\(.*?\))')
ARROW_SPLIT = re.compile(r'(<-->|-.->|==>|-->|---)')
ID_RE = re.compile(r'[A-Za-z_][\w-]*')

def clean_label(raw: str) -> str:
    raw = raw.strip()
    for a,b in (("[[","]]") ,("[(",")]"),("((","))"),("[","]"),("{","}"),("(",")")):
        if raw.startswith(a) and raw.endswith(b):
            raw = raw[len(a):-len(b)]
            break
    return raw.strip().strip('"\'').replace('<br/>',' ').replace('<br>',' ').replace('\\n',' ')

def parse_mermaid(text: str, title: str | None, theme: str) -> dict:
    """Strict subset: flowchart/graph, basic nodes, multi-edge chains and edge labels.

    Unknown structural syntax raises, never silently omits flow topology.
    """
    lines = text.splitlines()
    header = next((ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("%%")), "")
    m = re.fullmatch(r'(?:flowchart|graph)\s+(TD|TB|BT|LR|RL)\s*;?', header, re.I)
    if not m:
        raise ValueError('The built-in renderer supports Mermaid flowchart/graph syntax. For other Mermaid types use the skill\'s native Mermaid/image workflow or a faithful JSON spec.')
    direction = m.group(1).upper().replace('TD','TB')
    nodes: OrderedDict[str,dict] = OrderedDict()
    edges = []
    groups = []
    current_group = None
    mermaid_title = None
    for raw in lines:
        line = raw.strip().rstrip(';')
        if line.startswith('%%'):
            tm = re.match(r'%%\s*title\s*:\s*(.+)', line, re.I)
            if tm: mermaid_title = tm.group(1).strip()
            continue
        if not line or line == header or line.startswith('flowchart ') or line.startswith('graph '):
            continue
        if re.match(r'^subgraph\s+',line,re.I):
            if current_group is not None:
                raise ValueError('Nested subgraphs require native Mermaid rendering or JSON spec with flattened groups')
            name = line.split(None,1)[1].strip()
            gm = re.match(r'^([\w-]+)\s*\[(.+)\]$',name)
            group_id = gm.group(1) if gm else f'group{len(groups)+1}'
            group_label = gm.group(2).strip('\"') if gm else name.strip('\"')
            current_group={'id':group_id,'label':group_label,'nodes':[]}
            groups.append(current_group)
            continue
        if line == 'end':
            if current_group is None: raise ValueError('Unexpected Mermaid end')
            current_group = None
            continue
        if re.match(r'^(classDef|class\s|style\s|linkStyle)',line,re.I):
            continue  # style-only directives do not affect topology
        if re.match(r'^(click\s|direction\s)',line,re.I):
            raise ValueError(f'Unsupported Mermaid directive; use native rendering: {line}')
        # Reject constructs this strict parser cannot fully enumerate.
        if '&' in line or ';' in line:
            raise ValueError(f'Multiple inline endpoints/statements need a faithful JSON spec or native Mermaid rendering: {raw.strip()}')
        # Support Mermaid edge labels written as '-- yes -->' (simple case).
        line = re.sub(r'--\s+([^<>\-]+?)\s+-->', lambda m: '-->|'+m.group(1).strip()+'|', line)
        def replace_decl(m):
            node_id, raw_label = m.group(1),m.group(2)
            label = clean_label(raw_label)
            shape = 'diamond' if raw_label.startswith('{') else 'database' if raw_label.startswith('[(') else 'circle' if raw_label.startswith('((') else 'rounded'
            if current_group and node_id not in current_group['nodes']: current_group['nodes'].append(node_id)
            if node_id not in nodes: nodes[node_id] = {'id':node_id,'label':label,'shape':shape}
            else: nodes[node_id].update({'label':label,'shape':shape})
            return node_id
        simplified = NODE_DECL.sub(replace_decl,line)
        parts = ARROW_SPLIT.split(simplified)
        if len(parts) == 1:
            remainder = parts[0].strip()
            if not ID_RE.fullmatch(remainder):
                raise ValueError(f'Unsupported Mermaid line (not silently ignored): {raw.strip()}')
            nodes.setdefault(remainder, {'id':remainder,'label':remainder})
            if current_group and remainder not in current_group['nodes']: current_group['nodes'].append(remainder)
            continue
        if len(parts) % 2 != 1:
            raise ValueError(f'Cannot parse Mermaid edge: {raw.strip()}')
        for i in range(1,len(parts),2):
            left = parts[i-1].strip()
            right = parts[i+1].strip()
            label_match = re.match(r'^\|([^|]+)\|\s*(.*)$',right)
            edge_label = ''
            if label_match:
                edge_label, right = label_match.group(1),label_match.group(2)
            left_ids = ID_RE.findall(re.sub(r'\|[^|]*\|','',left))
            right_ids = ID_RE.findall(re.sub(r'\|[^|]*\|','',right))
            if not left_ids or not right_ids:
                raise ValueError(f'Cannot identify edge endpoints: {raw.strip()}')
            src, dst = left_ids[-1],right_ids[0]
            for nd in [src,dst]:
                nodes.setdefault(nd, {'id':nd,'label':nd})
                if current_group and nd not in current_group['nodes']: current_group['nodes'].append(nd)
            arrow = parts[i]
            if arrow == '<-->':
                edges.append({'from':src,'to':dst,'label':edge_label,'style':'solid','bidirectional':True})
            else:
                edges.append({'from':src,'to':dst,'label':edge_label,'style':'dotted' if arrow=='-.->' else 'thick' if arrow=='==>' else 'solid','undirected':arrow=='---'})
    if current_group is not None: raise ValueError('Unclosed Mermaid subgraph')
    if not nodes: raise ValueError('No Mermaid nodes were found.')
    return {'title':title or mermaid_title or 'System Flow', 'theme':theme, 'direction':direction, 'nodes':list(nodes.values()),'edges':edges,'groups':groups}

def esc(s) -> str:
    return html.escape(str(s),quote=True)

def q(s) -> str:
    return '"'+str(s).replace('\\','\\\\').replace('"','\\"')+'"'

def validate_spec(spec: dict):
    if not spec.get('nodes'):
        raise ValueError('No nodes in diagram spec')
    ids = [n['id'] for n in spec['nodes']]
    if len(set(ids)) != len(ids): raise ValueError('Duplicate node IDs')
    for edge in spec.get('edges',[]):
        if edge['from'] not in ids or edge['to'] not in ids:
            raise ValueError('Edge endpoint missing from nodes: '+str(edge))
    if spec.get('direction','TB') not in ['TB','TD','BT','LR','RL']:
        raise ValueError('Invalid direction; use TB, BT, LR, or RL')
    if spec.get('theme','mint') not in PALETTES:
        raise ValueError('Unknown theme: '+str(spec.get('theme')))
    for group in spec.get('groups',[]):
        missing=set(group.get('nodes',[]))-set(ids)
        if missing: raise ValueError(f'Group {group.get("id","?")} contains missing nodes: {missing}')

def layout_dot(spec: dict):
    if not shutil.which('dot'):
        raise RuntimeError('Graphviz `dot` not found. Install Graphviz (brew install graphviz / apt install graphviz).')
    direction = spec.get('direction','TB').replace('TD','TB')
    dot = ['digraph G {', f'graph [rankdir={direction}, bgcolor="transparent", pad="0.08", ranksep="0.72", nodesep="0.40", splines=true];',
           'node [shape=box, fixedsize=true, width=3.20, height=1.12, margin=0];','edge [arrowsize=0.65];']
    for node in spec['nodes']:
        dot.append(f'{q(node["id"])} [label={q(node["id"])}];')
    for idx,group in enumerate(spec.get('groups',[])):
        dot.append(f'subgraph cluster_{idx} {{ style=invis; label=""; margin=0.22;')
        for nd in group.get('nodes',[]): dot.append(q(nd)+';')
        dot.append('}')
    # Cycle/back edges should not impose another rank constraint; otherwise
    # feedback arrows may overlay the forward path and become unreadable.
    adjacency={node['id']:set() for node in spec['nodes']}
    def path_exists(start, target):
        seen=set();stack=[start]
        while stack:
            cur=stack.pop()
            if cur==target: return True
            if cur in seen:continue
            seen.add(cur);stack.extend(adjacency[cur]-seen)
        return False
    for ed in spec.get('edges',[]):
        arrow = 'none' if ed.get('undirected') else 'normal'
        direction_attr = 'both' if ed.get('bidirectional') else 'forward'
        backedge = path_exists(ed['to'],ed['from'])
        extra = ', constraint=false, minlen=2, weight=0.2' if backedge else ''
        dot.append(f'{q(ed["from"])} -> {q(ed["to"])} [arrowhead={arrow}, dir={direction_attr}{extra}];')
        adjacency[ed['from']].add(ed['to'])
    dot.append('}')
    proc = subprocess.run(['dot','-Tplain'],input='\n'.join(dot),text=True,capture_output=True)
    if proc.returncode:
        raise RuntimeError('Graphviz failed: '+proc.stderr)
    layout = {'nodes': {}, 'edges': []}
    for line in proc.stdout.splitlines():
        chunks = shlex.split(line)
        if not chunks: continue
        if chunks[0]=='graph':
            layout['w'] = float(chunks[2]); layout['h'] = float(chunks[3])
        elif chunks[0]=='node':
            layout['nodes'][chunks[1]] = {'x':float(chunks[2]), 'y':float(chunks[3]), 'w':float(chunks[4]), 'h':float(chunks[5])}
        elif chunks[0]=='edge':
            n=int(chunks[3]); pts=[(float(chunks[i]),float(chunks[i+1])) for i in range(4,4+2*n,2)]
            layout['edges'].append({'from':chunks[1],'to':chunks[2],'points':pts})
    if len(layout['edges']) != len(spec.get('edges',[])):
        raise RuntimeError('Graphviz edge count mismatch')
    return layout

def str_width(s: str, font_px: float) -> float:
    # Approximate Inter/Noto Sans width, using full width for CJK.
    width=0.0
    for c in s:
        if c.isspace(): width+=.30
        elif ord(c)>0x2e80: width+=1.04
        elif c in 'ilI.,:;!|\'': width+=.29
        elif c in 'mwMW@%': width+=.82
        else: width+=.57
    return width*font_px

def wrap_label(text: str, max_width: float, size: float):
    lines=[]
    for paragraph in str(text).replace('\\n','\n').split('\n'):
        if not paragraph.strip(): continue
        words=paragraph.split(' ') if ' ' in paragraph else list(paragraph)
        current=''
        for word in words:
            test=(current+' '+word if current and ' ' in paragraph else current+word)
            if current and str_width(test,size)>max_width:
                lines.append(current.strip());current=word
            else: current=test
        if current: lines.append(current.strip())
    return lines or ['']

def fit_text(text, maxw, maxh, max_size=30, min_size=16, max_lines=3):
    for s in range(int(max_size),int(min_size)-1,-1):
        lines=wrap_label(text,maxw,s)
        if len(lines)<=max_lines and len(lines)*s*1.20<=maxh:
            return s,lines
    lines=wrap_label(text,maxw,min_size)
    if len(lines)*min_size*1.2>maxh:
        raise ValueError(f'Label too long to fit without unreadable text: {text!r}. Shorten only with explicit user approval or redesign the layout.')
    return min_size,lines

def icon_markup(icon: str, cx: float, cy: float, size: float, color=BLACK) -> str:
    paths=''.join(ICONS.get(icon,ICONS['box']))
    # icons have arbitrary paths but all are outlined and share 24x24 coordinates
    paths=paths.replace('/>',' fill="none"/>')
    return f'<g transform="translate({cx-size/2:.1f} {cy-size/2:.1f}) scale({size/24:.4f})" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{paths}</g>'

def render_svg(spec: dict, size:int=1024) -> str:
    validate_spec(spec)
    layout = layout_dot(spec)
    pal = PALETTES[spec.get('theme','mint-editorial')]
    editorial = bool(pal.get('editorial'))
    f=size/1024.0
    # work in virtual 1024px coordinates so every card shares the same layout and scale
    top_margin=46
    title_text = spec.get('title') or 'System Flow'
    if editorial:
        ts,title_lines = fit_text(title_text, 866, 150, 62, 44, 2)
        # Keep one visual grammar across ALL eight reference-card archetypes.
        banner_y = 44
        banner_h = 145 if len(title_lines)==1 else 180
        board_y = banner_y + banner_h + 28
        board_rect = (50, board_y, 924, 975-board_y)
        diagram_rect = (85, board_y+26, 854, 950-board_y-23)
    else:
        ts,title_lines = fit_text(title_text, 900, 147, 68, 48, 2)
        header_h = 58 + len(title_lines)*ts*1.14
        board_y = max(205, min(247,header_h+27))
        board_rect=(57,board_y,910,976-board_y)
        diagram_rect=(90, board_y+52, 844, 922-board_y-36)
    gw,gh=layout['w'],layout['h']
    scale=min(diagram_rect[2]/gw,diagram_rect[3]/gh)
    ox=diagram_rect[0]+(diagram_rect[2]-gw*scale)/2
    oy=diagram_rect[1]+(diagram_rect[3]-gh*scale)/2
    def xy(x,y):return (ox+x*scale,oy+(gh-y)*scale)
    # Card background and compact, unified mint editorial title treatment.
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 1024 1024">',
           '<defs><clipPath id="rounded"><rect x="7" y="7" width="1010" height="1010" rx="65"/></clipPath></defs>',
           f'<g clip-path="url(#rounded)"><rect width="1024" height="1024" fill="{pal["bg"]}"/>']
    if editorial:
        parts.append(f'<rect x="51" y="{banner_y}" width="922" height="{banner_h}" rx="46" fill="{pal["title_bg"]}"/>')
        total_h = len(title_lines)*ts*1.12
        title_base = banner_y + (banner_h-total_h)/2 + ts*.91
        title_line_h=ts*1.12
        # Most examples deliberately leave the diagram on white, with color in nodes.
        parts.append(f'<rect x="{board_rect[0]}" y="{board_rect[1]}" width="{board_rect[2]}" height="{board_rect[3]}" rx="16" fill="{pal["panel"]}"/>')
    else:
        parts.extend([
            f'<circle cx="905" cy="85" r="66" fill="{pal["accent"]}" opacity="0.10"/>',
            f'<circle cx="91" cy="142" r="37" fill="#FFFFFF" opacity="0.10"/>',
            f'<rect x="{board_rect[0]}" y="{board_rect[1]}" width="{board_rect[2]}" height="{board_rect[3]}" rx="36" fill="{pal["panel"]}" stroke="{pal["accent"]}" stroke-width="3"/>',
        ])
        title_line_h=ts*1.10
        title_base=top_margin+ts*0.95
    for idx,t in enumerate(title_lines):
        parts.append(f'<text x="512" y="{title_base+idx*title_line_h:.1f}" font-family="Inter, Noto Sans, Arial, sans-serif" font-size="{ts}" font-weight="800" text-anchor="middle" fill="#101919">{esc(t)}</text>')
    if not editorial:
        # Only the more colorful themes use confetti accents.
        for ax,ay in [(86,board_y+23),(938,board_y+23),(86,955),(938,955)]:
            parts.append(f'<circle cx="{ax}" cy="{ay}" r="3.5" fill="{pal["accent"]}" opacity="0.45"/>')
    # soft group envelopes behind the diagram, preserving Mermaid subgraphs
    for group in spec.get('groups',[]):
        contained=[layout['nodes'][nid] for nid in group['nodes'] if nid in layout['nodes']]
        if not contained: continue
        l=min(xy(node['x']-node['w']/2,node['y'])[0] for node in contained)-23
        r=max(xy(node['x']+node['w']/2,node['y'])[0] for node in contained)+23
        t=min(xy(node['x'],node['y']+node['h']/2)[1] for node in contained)-60
        b=max(xy(node['x'],node['y']-node['h']/2)[1] for node in contained)+25
        l=max(72,l);r=min(952,r);t=max(board_y+15,t);b=min(967,b)
        parts.append(f'<rect x="{l:.1f}" y="{t:.1f}" width="{r-l:.1f}" height="{b-t:.1f}" rx="24" fill="{("#E7FFF5" if editorial else "#FFFFFF")}" fill-opacity="{("0.80" if editorial else "0.18")}" stroke="{pal["accent"]}" stroke-width="2.5" stroke-dasharray="9 6"/>')
        # Keep subgraph name legible even when the first node starts near the group border.
        gname=str(group.get('label','Group'))
        first_top=min(xy(n['x'],n['y']+n['h']/2)[1] for n in contained)
        label_y=t-10 if first_top-t < 38 else t+28
        label_w=min(r-l-18,max(85,str_width(gname,18)+26))
        parts.append(f'<rect x="{l+10:.1f}" y="{label_y-20:.1f}" width="{label_w:.1f}" height="25" rx="8" fill="#FFFFFF"/>')
        parts.append(f'<text x="{l+19:.1f}" y="{label_y:.1f}" fill="{BLACK}" font-family="Inter, Noto Sans, sans-serif" font-weight="800" font-size="18">{esc(gname)}</text>')
    # graph connectors
    # Graphviz can reorder edges. Match by exact endpoint IDs instead of zip().
    edge_lookup = {}
    for ed in spec.get('edges',[]): edge_lookup.setdefault((ed['from'],ed['to']),[]).append(ed)
    for shape in layout['edges']:
        key=(shape['from'],shape['to'])
        if not edge_lookup.get(key): raise RuntimeError(f'Cannot match layout edge to source: {key}')
        ed=edge_lookup[key].pop(0)
        pts=[xy(x,y) for x,y in shape['points']]
        if len(pts)<2: continue
        src_g=layout['nodes'][ed['from']];dst_g=layout['nodes'][ed['to']]
        src_c=xy(src_g['x'],src_g['y']);dst_c=xy(dst_g['x'],dst_g['y'])
        vertical=spec.get('direction','TB') in ('TB','TD','BT')
        feedback=(vertical and src_c[1]>dst_c[1]+15) or (not vertical and src_c[0]>dst_c[0]+15)
        if feedback:
            if vertical:
                maxright=max(xy(g['x']+g['w']/2,g['y'])[0] for g in layout['nodes'].values())
                loop_x=min(board_rect[0]+board_rect[2]-32,maxright+60)
                pts=[(src_c[0]+src_g['w']*scale/2,src_c[1]),(loop_x,src_c[1]),(loop_x,dst_c[1]),(dst_c[0]+dst_g['w']*scale/2,dst_c[1])]
            else:
                maxbottom=max(xy(g['x'],g['y']-g['h']/2)[1] for g in layout['nodes'].values())
                loop_y=min(board_rect[1]+board_rect[3]-32,maxbottom+60)
                pts=[(src_c[0],src_c[1]+src_g['h']*scale/2),(src_c[0],loop_y),(dst_c[0],loop_y),(dst_c[0],dst_c[1]+dst_g['h']*scale/2)]

        path=f'M {pts[0][0]:.2f} {pts[0][1]:.2f}'
        if (len(pts)-1)%3==0:
            for i in range(1,len(pts),3):
                path+=f' C {pts[i][0]:.2f} {pts[i][1]:.2f} {pts[i+1][0]:.2f} {pts[i+1][1]:.2f} {pts[i+2][0]:.2f} {pts[i+2][1]:.2f}'
        else:
            for x,y in pts[1:]: path+=f' L {x:.2f} {y:.2f}'
        dash=' stroke-dasharray="9 7"' if ed.get('style')=='dotted' else ''
        thick=4.2 if ed.get('style')=='thick' else 3.3
        parts.append(f'<path d="{path}" fill="none" stroke="{BLACK}" stroke-width="{thick}"{dash} stroke-linecap="round"/>')
        if not ed.get('undirected'):
            def arrow(at,prior):
                dx,dy=at[0]-prior[0],at[1]-prior[1]
                dist=math.hypot(dx,dy) or 1
                ux,uy=dx/dist,dy/dist; px,py=-uy,ux
                tx,ty=at; bx,by=tx-ux*13,ty-uy*13
                return f'<path d="M{tx:.1f} {ty:.1f} L{bx+px*6.8:.1f} {by+py*6.8:.1f} L{bx-px*6.8:.1f} {by-py*6.8:.1f} Z" fill="{BLACK}"/>'
            parts.append(arrow(pts[-1],pts[-2]))
            if ed.get('bidirectional'): parts.append(arrow(pts[0],pts[1]))
        if ed.get('label'):
            mid=((pts[1][0]+pts[2][0])/2,(pts[1][1]+pts[2][1])/2) if feedback else pts[len(pts)//2]
            text=str(ed['label']); lw=min(180,str_width(text,20))
            parts.append(f'<rect x="{mid[0]-lw/2-8:.1f}" y="{mid[1]-25:.1f}" width="{lw+16:.1f}" height="31" rx="10" fill="#FFFCED" stroke="{BLACK}" stroke-width="1.5"/>')
            parts.append(f'<text x="{mid[0]:.1f}" y="{mid[1]-4:.1f}" text-anchor="middle" fill="{BLACK}" font-family="Inter, Noto Sans, sans-serif" font-size="20" font-weight="700">{esc(text)}</text>')
    # graph nodes
    for i,node in enumerate(spec['nodes']):
        g=layout['nodes'][node['id']]; cx,cy=xy(g['x'],g['y']); w,h=g['w']*scale,g['h']*scale
        left,top=cx-w/2,cy-h/2
        radius=min(23,h*.19)
        fill=node.get('color') or (pal['node_fills'][i%len(pal['node_fills'])] if editorial else NODE_COLORS[i%len(NODE_COLORS)])
        shape_name=node.get('shape','rounded')
        if shape_name=='diamond':
            points=f'{cx:.2f},{top:.2f} {left+w:.2f},{cy:.2f} {cx:.2f},{top+h:.2f} {left:.2f},{cy:.2f}'
            parts.append(f'<polygon points="{points}" fill="{esc(fill)}" stroke="{BLACK}" stroke-width="3"/>')
        elif shape_name=='circle':
            parts.append(f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{w/2:.2f}" ry="{h/2:.2f}" fill="{esc(fill)}" stroke="{BLACK}" stroke-width="3"/>')
        elif shape_name=='database':
            parts.append(f'<rect x="{left:.2f}" y="{top+10:.2f}" width="{w:.2f}" height="{h-20:.2f}" fill="{esc(fill)}" stroke="{BLACK}" stroke-width="3"/>')
            parts.append(f'<ellipse cx="{cx:.2f}" cy="{top+10:.2f}" rx="{w/2:.2f}" ry="10" fill="{esc(fill)}" stroke="{BLACK}" stroke-width="3"/>')
            parts.append(f'<path d="M {left:.2f} {top+h-10:.2f} a {w/2:.2f} 10 0 0 0 {w:.2f} 0" fill="none" stroke="{BLACK}" stroke-width="3"/>')
        else:
            if not editorial:
                parts.append(f'<rect x="{left:.2f}" y="{top+5:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{radius:.1f}" fill="#000000" opacity="0.10"/>')
            parts.append(f'<rect x="{left:.2f}" y="{top:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{radius:.1f}" fill="{esc(fill)}" stroke="{BLACK}" stroke-width="3"/>')
        label=str(node.get('label',node['id']))
        preferred_icon=node.get('icon') or semantic_icon(label)
        text_area=h-8
        if shape_name=='diamond':
            text_top=top+9; text_area=h-18; label_width=w*.54
        elif h>=115:
            icon_size=min(36,h*.28)
            icon_y=top+icon_size*.50+10
            parts.append(icon_markup(preferred_icon,cx,icon_y,icon_size))
            text_top=top+icon_size+18
            text_area=h-icon_size-24; label_width=w-28
        else:
            # A compact pictogram badge keeps the illustration language even
            # when a tall flowchart forces short node boxes.
            badge_x=left+14;badge_y=top+4
            parts.append(f'<circle cx="{badge_x:.1f}" cy="{badge_y:.1f}" r="18" fill="#FCFFF9" stroke="{BLACK}" stroke-width="2"/>')
            parts.append(icon_markup(preferred_icon,badge_x,badge_y,21))
            text_top=top+6; text_area=h-12; label_width=w-34
        if shape_name=='diamond':
            # Center a short decision on one line where the diamond is widest.
            # Labels at the top/bottom tips often overlap the outline.
            font,lines=fit_text(label,w*.82,h*.58,26,16,1)
            if len(lines)==1:
                start_y=cy+font*.34
            else:
                # Long decisions may need wrapping; remain centered on the widest area.
                font,lines=fit_text(label,w*.66,h*.70,22,15,2)
                line_height=font*1.12
                start_y=cy-(len(lines)-1)*line_height/2+font*.34
        else:
            font,lines=fit_text(label,label_width,text_area,29,17,3)
            line_height=font*1.16
            start_y=text_top+(text_area-len(lines)*line_height)/2+font*.88
        line_height=font*1.16
        for line_num,t in enumerate(lines):
            parts.append(f'<text x="{cx:.2f}" y="{start_y+line_num*line_height:.2f}" font-family="Inter, Noto Sans, Arial, sans-serif" text-anchor="middle" fill="{BLACK}" font-size="{font}" font-weight="750">{esc(t)}</text>')
    outer_color = pal['border'] if editorial else BLACK
    outer_width = 3 if editorial else 5
    parts.extend([f'</g><rect x="7" y="7" width="1010" height="1010" rx="65" fill="none" stroke="{outer_color}" stroke-width="{outer_width}"/>','</svg>'])
    return '\n'.join(parts)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    src=ap.add_mutually_exclusive_group(required=True)
    src.add_argument('--spec',type=Path,help='Faithful JSON diagram spec (recommended for advanced Mermaid)')
    src.add_argument('--mermaid',type=Path,help='Mermaid flowchart/graph input (strict supported subset)')
    ap.add_argument('--out',type=Path,required=True,help='Output PNG or SVG')
    ap.add_argument('--title',help='Override heading')
    ap.add_argument('--theme',choices=PALETTES.keys(),default=None)
    ap.add_argument('--size',type=int,default=1024,help='Output square side in px; default 1024')
    args=ap.parse_args()
    if args.size not in (1024,1536,2048):
        ap.error('Use one of 1024, 1536, or 2048 to keep consistent card size')
    if args.spec:
        spec=json.loads(args.spec.read_text(encoding='utf-8'))
        if args.title: spec['title']=args.title
        if args.theme: spec['theme']=args.theme
    else:
        spec=parse_mermaid(args.mermaid.read_text(encoding='utf-8'),args.title,args.theme or 'mint-editorial')
        if not args.title and spec['title']=='System Flow':
            spec['title']=args.mermaid.stem.replace('_',' ').replace('-',' ').title()
    spec.setdefault('theme','mint-editorial')
    svg=render_svg(spec,args.size)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    if args.out.suffix.lower()=='.svg': args.out.write_text(svg,encoding='utf-8')
    elif args.out.suffix.lower()=='.png':
        try: import cairosvg
        except ImportError as e: raise SystemExit('PNG output requires cairosvg. Use --out card.svg or pip install cairosvg.') from e
        cairosvg.svg2png(bytestring=svg.encode('utf-8'),write_to=str(args.out),output_width=args.size,output_height=args.size)
        args.out.with_suffix('.svg').write_text(svg,encoding='utf-8')
    else: ap.error('Output must end in .svg or .png')
    print(f'Created {args.out} ({args.size}x{args.size}); {len(spec["nodes"])} nodes, {len(spec.get("edges",[]))} edges; theme={spec["theme"]}')

if __name__=='__main__':
    try: main()
    except (ValueError,RuntimeError,KeyError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr)
        sys.exit(2)
