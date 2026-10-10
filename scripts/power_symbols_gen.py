from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import kicad_helpers as h
D=ROOT/'design/power';D.mkdir(parents=True,exist_ok=True)
FP=D/'PowerPhase.pretty';FP.mkdir(exist_ok=True)
base=Path('/usr/share/kicad/footprints/Package_SO.pretty/HTSSOP-38-1EP_4.4x9.7mm_P0.5mm_EP2.74x4.75mm.kicad_mod')
o=h.parse(base.read_text());o[1]='LTC3779_FE38_31_EP';removed={'23','25','27','29','31','33','35'}
o[:]=[a for a in o if not (isinstance(a,list) and a[0]=='pad' and a[1] in removed)]
for a in h.children(o,'property'):
 if a[1]=='Value':a[2]='LTC3779_FE38_31_EP'
 if a[1]=='Description':a[2]='LTC3779 Rev A p36 landpattern: 1.05 x 0.300 mm lead pads, centres +/-2.775 mm; paste/assembly review pending.'
# Manufacturer landpattern, LTC3779 Rev A p36: lead-pad length 1.05 +/-0.10,
# width 0.315 +/-0.05, outer span 6.60 +/-0.10 mm. Width 0.300 mm is within
# that published interval and preserves the existing 0.200 mm adjacent gap.
# The larger inherited courtyard is retained as conservative assembly space.
for a in h.children(o,'pad'):
 if a[1] and a[1]!='39':
  at=h.children(a,'at')[0];at[1]=h.Atom('-2.775' if float(at[1])<0 else '2.775')
  size=h.children(a,'size')[0];size[1:]=[h.Atom('1.05'),h.Atom('0.3')]
h.children(o,'descr')[0][1]='LTC3779 FE38(31), manufacturer Rev A p36 landpattern 1.05 x 0.300 mm / 6.60 mm outer span; removed positions 23,25,27,29,31,33,35; EP2.74x4.75; paste and assembly review pending'
(FP/'LTC3779_FE38_31_EP.kicad_mod').write_text(h.emit(o)+'\n')

def symbol(name,pinlist):
 s=[f'(symbol "{name}" (pin_names (offset 1.27)) (in_bom yes) (on_board yes)',f'(property "Reference" "U" (at 0 37 0) (effects (font (size 1.27 1.27))))',f'(property "Value" "{name}" (at 0 -37 0) (effects (font (size 1.27 1.27))))',f'(symbol "{name}_0_1" (rectangle (start -10.16 35.56) (end 10.16 -35.56) (stroke (width 0.254) (type default)) (fill (type background))))',f'(symbol "{name}_1_1"']
 for no,nm,tp,side,y in pinlist:
  x=-15.24 if side=='L' else 15.24;a=0 if side=='L' else 180
  s.append(f'(pin {tp} line (at {x} {y} {a}) (length 5.08) (name "{nm}" (effects (font (size 1.0 1.0)))) (number "{no}" (effects (font (size 1.0 1.0)))))')
 return '\n'.join(s)+'))'
left=[('34','VIN','power_in'),('32','VINSNS','input'),('2','VINOV','input'),('5','EXTVCC','power_in'),('6','NDRV','output'),('7','DRVCC','power_out'),('8','V5','power_out'),('3','DRVSET','input'),('24','RUN','input'),('15','MODE','input'),('16','PLLIN','input'),('17','FREQ','input'),('9','SS','input'),('4','SGND','power_in'),('14','SGND','power_in'),('39','PGND_EP','power_in')]
right=[('37','TG1','output'),('1','BG1','output'),('36','BOOST1','passive'),('38','SW1','passive'),('21','TG2','output'),('19','BG2','output'),('22','BOOST2','passive'),('20','SW2','passive'),('11','SENSEP','input'),('12','SENSEN','input'),('26','IAVGSNSP','input'),('28','IAVGSNSN','input'),('30','VOUTSNS','input'),('10','VFB','input'),('13','ITH','passive'),('18','PGOOD','open_collector')]
pins=[(n,nm,t,'L',27.94-i*3.81) for i,(n,nm,t) in enumerate(left)]+[(n,nm,t,'R',27.94-i*3.81) for i,(n,nm,t) in enumerate(right)]
# FET visual uses a standardGDS symbol, with physicalsourcepads1,2,3 andgate4/drain5.
fet=h.resolved('Transistor_FET:Q_NMOS_GDS')
from copy import deepcopy
fet=deepcopy(fet);old=fet[1];fet[1]='BSC110N15NS5_REFERENCE'
for su in h.children(fet,'symbol'):
 su[1]='BSC110N15NS5_REFERENCE'+su[1][len(old):]
 for p in list(h.children(su,'pin')):
  num=h.sub(p,'number');name=h.sub(p,'name')[1]
  if name=='G':num[1]='4'
  elif name=='D':num[1]='5'
  elif name=='S':
   num[1]='1'
   for n in ['2','3']:
    p2=deepcopy(p);h.sub(p2,'number')[1]=n
    p2.insert(3,h.Atom('hide'));su.append(p2)
for prop in h.children(fet,'property'):
 if prop[1]=='Value':prop[2]='BSC110N15NS5'
(D/'PowerPhase.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "power-phase-draft")\n'+symbol('LTC3779EFE',pins)+'\n'+h.emit(fet)+'\n)\n')
print('Prepared sourcebased controller symbol andfootprint;32connectedpins,7positionsremoved.')
