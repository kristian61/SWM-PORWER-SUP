"""Minimal KiCad 9 schematic authoring helpers. Tested with kicad-cli 9.0.2.
All x/y coordinates are mm. Place on 1.27mm grid. Symbol-local y is inverted
on sheets. Use global labels for identical net names on schematic and board.
Standard library aliases are flattened before embedding. No design is implied.
"""
from pathlib import Path
from functools import lru_cache
from copy import deepcopy
import re, json, uuid, math

class Atom(str): pass

def uid(): return str(uuid.uuid4())
def quote(value): return json.dumps(str(value),ensure_ascii=False)
def parse(s):
    tokens=iter(re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+',s))
    def read(t):
        if t=='(':
            out=[]
            for n in tokens:
                if n==')':return out
                out.append(read(n))
            raise ValueError('Unclosed s-expression')
        return json.loads(t) if t.startswith('"') else Atom(t)
    return read(next(tokens))
def emit(o):
    if isinstance(o,list):return '('+' '.join(emit(x) for x in o)+')'
    return str(o) if isinstance(o,Atom) else quote(o)
def sub(o,name):return next((x for x in o[1:] if isinstance(x,list) and x[0]==name),None)
def children(o,name):return [x for x in o[1:] if isinstance(x,list) and x[0]==name]
@lru_cache(None)
def library(lib):return parse(Path('/usr/share/kicad/symbols',lib+'.kicad_sym').read_text())
@lru_cache(None)
def resolved(libid):
    lib,name=libid.split(':',1)
    source=deepcopy(next(x for x in children(library(lib),'symbol') if x[1]==name))
    ext=sub(source,'extends')
    if ext:
        base=deepcopy(resolved(lib+':'+ext[1]));oldname=base[1]
        base[1]=name
        for su in children(base,'symbol'):
            su[1]=name+su[1][len(oldname):]
        for prop in children(source,'property'):
            prior=next((p for p in children(base,'property') if p[1]==prop[1]),None)
            if prior:base.remove(prior)
            base.append(prop)
        # Derived symbols normally only override properties; preserve other flags.
        for item in source[2:]:
            if not isinstance(item,list) or item[0] in ('extends','property','symbol'):continue
            prior=sub(base,item[0])
            if prior:base.remove(prior)
            base.append(item)
        source=base
    return source

def embedded(libid):
    o=deepcopy(resolved(libid));o[1]=libid;return emit(o)
def pins(libid,unit=1):
    out=[]
    for su in children(resolved(libid),'symbol'):
        nu,style=map(int,su[1].rsplit('_',2)[-2:])
        if nu not in (0,unit) or style not in (0,1):continue
        for p in children(su,'pin'):
            at=sub(p,'at')
            out.append(dict(number=sub(p,'number')[1],name=sub(p,'name')[1],x=float(at[1]),y=float(at[2]),angle=float(at[3]),type=p[1]))
    return out

def units(libid):
    return sorted({int(s[1].rsplit('_',2)[-2]) for s in children(resolved(libid),'symbol') if int(s[1].rsplit('_',2)[-2])>0})

def symbol_tables(directory,libids):
    """Write project-local lookup table for system libraries; no global changes."""
    directory=Path(directory)
    libs=sorted({s.split(':',1)[0] for s in libids})
    entries=[f'(lib (name {quote(lib)}) (type "KiCad") (uri {quote("${KICAD9_SYMBOL_DIR}/"+lib+".kicad_sym")}) (options "") (descr "KiCad 9 standard library"))' for lib in libs]
    (directory/'sym-lib-table').write_text('(sym_lib_table (version 7)\n'+'\n'.join(entries)+'\n)\n')

def write_schematic(path,components,project=None,root_uuid=None,instance_path=None,title='',comments=(),sheets=(),texts=()):
    """components entries: ref,val,lib,footprint,xy,nets; optional unit,uuid,
    angle, datasheet,description,on_board,in_bom,dnp,label_length.
    nets maps pin numbers to net names, or None for explicit no-connect.
    Multi-unit ICs need one entry per required unit with same ref/value/footprint.
    Return sheet UUID plus components (each receives its unique symbol UUID).
    Sheets entries: name,file,xy,size,uuid. Pass child instance_path '/root/sheet'.
    """
    path=Path(path);project=project or path.stem;root_uuid=root_uuid or uid()
    instance_path=instance_path or '/'+root_uuid
    s=[f'(kicad_sch (version 20250114) (generator "kicad_helpers") (uuid {root_uuid}) (paper "A3")']
    if title or comments:
        s.append('(title_block '+(f'(title {quote(title)}) ' if title else '')+' '.join(f'(comment {i+1} {quote(c)})' for i,c in enumerate(comments))+')')
    s.append('(lib_symbols '+''.join(embedded(l) for l in sorted({c['lib'] for c in components}))+')')
    for c in components:
        x,y=c['xy'];angle=c.get('angle',0);unit=c.get('unit',1);c.setdefault('uuid',uid())
        yes=lambda k: 'yes' if c.get(k,True) else 'no'
        s.append(f'(symbol (lib_id {quote(c["lib"])}) (at {x} {y} {angle}) (unit {unit}) (in_bom {yes("in_bom")}) (on_board {yes("on_board")}) (dnp {"yes" if c.get("dnp",False) else "no"}) (uuid {c["uuid"]})')
        props=[('Reference',c['ref'],y-3.81,False),('Value',c['val'],y+3.81,c.get('hide_value',False)),('Footprint',c.get('footprint',''),y,True),('Datasheet',c.get('datasheet',''),y,True),('Description',c.get('description',''),y,True)]
        for key,value,py,hide in props:
            prop_x=x; prop_angle=angle; prop_justify=''
            if key in ('Reference','Value') and c['lib'] in ('Device:R','Device:C') and angle==0:
                prop_x=x+5.08;py=y+(-1.27 if key=='Reference' else 1.27)
                prop_justify=' (justify left)'
            if key=='Value' and c['lib'].startswith('Connector_Generic:'):
                py=y+max(-p['y'] for p in pins(c['lib'],unit))+5.08
            if key=='Reference' and c['lib'].startswith('Connector_Generic:'):
                py=y+min(-p['y'] for p in pins(c['lib'],unit))-5.08
            if key in c.get('field_positions', {}):
                prop_x, py = c['field_positions'][key]
            s.append(f'(property {quote(key)} {quote(value)} (at {prop_x} {py} {prop_angle}) (effects (font (size 1.27 1.27)){prop_justify}{" (hide yes)" if hide else ""}))')
        pp=pins(c['lib'],unit)
        for p in pp:s.append(f'(pin {quote(p["number"])} (uuid {uid()}))')
        s.append(f'(instances (project {quote(project)} (path {quote(instance_path)} (reference {quote(c["ref"])}) (unit {unit})))) )')
        for p in pp:
            # Positive symbol angle is anticlockwise; sheet y increases downwards.
            r=math.radians(angle);px=round(x+p['x']*math.cos(r)-p['y']*math.sin(r),6);py=round(y-p['x']*math.sin(r)-p['y']*math.cos(r),6)
            if p['number'] not in c['nets']:continue
            net=c['nets'][p['number']]
            if net is None:
                s.append(f'(no_connect (at {px} {py}) (uuid {uid()}))');continue
            r=math.radians(p['angle']+angle);length=c.get('label_length',5.08)
            ex=round(px-length*math.cos(r),6);ey=round(py+length*math.sin(r),6)
            if length:s.append(f'(wire (pts (xy {px} {py}) (xy {ex} {ey})) (stroke (width 0) (type default)) (uuid {uid()}))')
            # Global labels connect sheets and keep PCB net names without '/'.
            # Angle 0 has anchor at its left tip; angle 180 at its right tip.
            la=180 if abs(math.cos(r))>.5 and math.cos(r)>0 else 0
            s.append(f'(global_label {quote(net)} (shape input) (at {ex} {ey} {la}) (effects (font (size 1.0 1.0)) (justify {"right" if la==180 else "left"})) (uuid {uid()}))')
    for page,sh in enumerate(sheets,2):
        sh.setdefault('uuid',uid());x,y=sh['xy'];w,h=sh.get('size',(50.8,25.4))
        s.append(f'(sheet (at {x} {y}) (size {w} {h}) (stroke (width 0) (type default)) (fill (color 0 0 0 0)) (uuid {sh["uuid"]}) (property "Sheetname" {quote(sh["name"])} (at {x} {y-1.27} 0) (effects (font (size 1.27 1.27)) (justify left bottom))) (property "Sheetfile" {quote(sh["file"])} (at {x} {y+h+1.27} 0) (effects (font (size 1.27 1.27)) (justify left top))) (instances (project {quote(project)} (path {quote(instance_path)} (page {quote(page)})))))')
    for t in texts:
        x,y=t['xy'];s.append(f'(text {quote(t["text"])} (at {x} {y} 0) (effects (font (size {t.get("size",1.27)} {t.get("size",1.27)})) (justify left)) (uuid {uid()}))')
    s.append('(sheet_instances (path "/" (page "1")))')
    s.append('(embedded_fonts no))')
    path.write_text('\n'.join(s)+'\n')
    return root_uuid,components
