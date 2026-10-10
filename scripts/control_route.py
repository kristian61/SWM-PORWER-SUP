#!/usr/bin/python3
"""Place and route the experimental analog CV/CC card, without fabrication export.

Run AFTER control_gen.py. Geometry is regenerated from the actual native pads;
their references, values, UUIDs, schematic paths and nets are never reassigned.
The final KiCad DRC, not this router's mask, is the acceptance criterion.
"""
from pathlib import Path
import os, json, math, subprocess, ctypes, collections, datetime
ROOT=Path(__file__).resolve().parents[1]
for key,rel in [('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache'),('XDG_DATA_HOME','data')]:
    os.environ.setdefault(key,str(ROOT/'.runtime/kicad'/rel))
import pcbnew
import numpy as np
D=ROOT/'design/control'; E=ROOT/'exports/control'; PCB=D/'control.kicad_pcb'
STEP=.1; W=1801; H=1501; WIDTH=.25; CLEAR=.25; VIA=.8
HV={'VOUT_SENSE','HV1','HV2'}
def pt(xy):return pcbnew.VECTOR2I(*(pcbnew.FromMM(float(v)) for v in xy))
def mm(pos):return (pcbnew.ToMM(pos.x),pcbnew.ToMM(pos.y))
def cli(*args):subprocess.run([str(ROOT/'bin/kicad-env'),'kicad-cli',*map(str,args)],cwd=ROOT,check=True)

# Each group follows the function being served, rather than BOM order.
PLACEMENT={
 'J1':(15,15,0),'J2':(45,15,0),'J3':(70,15,0),'J4':(26,25,90),
 'J5':(155,15,0),'JP1':(110,15,0),
 'U1':(55,55,0),'U2':(30,40,0),'U3':(95,38,0),
 'U4':(105,68,0),'U5':(126,68,0),'U6':(55,95,0),'U7':(108,105,0),
 'D1':(40,47,0),'D2':(40,65,0),
 'R1':(43,52,0),'R2':(43,56,0),'R3':(43,60,0),'R4':(47,62,0),
 'R5':(45,35,0),'R6':(45,40,0),'R7':(60,30,0),
 'R8':(47,66,0),'R9':(43,70,0),'R10':(40,30,0),
 'R11':(72,61,0),'R12':(72,65,0),'R13':(95,32,0),
 'R14':(88,45,0),'R15':(88,49,0),
 'R16':(68,47,0),'R17':(74,47,0),'R18':(80,47,0),
 'R19':(68,51,0),'R20':(74,51,0),'R21':(80,51,0),
 'R22':(39,38,0),'R23':(21,38,0),
 'R24':(108,24,0),'R25':(110,29,0),
 'R26':(43,88,0),'R27':(43,92,0),'R28':(68,93,0),'R29':(68,97,0),
 'R30':(68,101,0),'R31':(68,105,0),
 'R32':(94,96,0),'R33':(94,100,0),
 'R34':(94,104,0),'R35':(94,108,0),'R36':(121,104,0),'R37':(121,108,0),
 'R38':(118,77,0),'R39':(118,81,0),'R40':(133,77,0),'R41':(133,81,0),
 'R42':(155,35,-90),'R43':(155,55,-90),'R44':(155,75,-90),
 'R45':(155,89,-90),
 'C1':(55,55,0),'C2':(36,42,90),'C3':(108.5,71,0),
 'C4':(130,65,90),'C5':(55,94.35,0),'C6':(108,104.35,0),
 'C7':(95,44,0),'C8':(47,70,0),'C9':(112,74,0),'C10':(148,95,0),
 'TP1':(15,27,0),'TP2':(15,34,0),'TP3':(95,53,0),'TP4':(35,56,0),
 'TP5':(35,48,0),'TP6':(70,28,0),'TP7':(36,60,0),'TP8':(76,70,0),
 'TP9':(40,43,0),'TP10':(35,71,0),'TP11':(40,24,0),'TP12':(115,25,0),
 'TP13':(88,56,0),'TP14':(143,110,0),'TP15':(118,87,0),'TP16':(133,87,0),
}

class Router:
 def __init__(self,board):
  self.b=board; self.fps={f.GetReference():f for f in sorted(board.GetFootprints(),key=lambda f:(len(f.GetReference()),f.GetReference()))}
  self.net={n.GetNetname():n for n in board.GetNetsByNetcode().values()}
  self.pads=[];self.geometry=[];self.added=[]
  for f in self.fps.values():
   for p in sorted(f.Pads(),key=lambda p:p.GetNumber()):
    if p.GetNumber():self.pads.append(p)
  self.by_net=collections.defaultdict(list)
  for p in self.pads:self.by_net[p.GetNetname()].append(p)
  so=ROOT/'.runtime/control_router_grid.so';so.parent.mkdir(parents=True,exist_ok=True)
  src=ROOT/'scripts/control_route_grid.cpp'
  if not so.exists() or src.stat().st_mtime>so.stat().st_mtime:
   subprocess.run(['g++','-O3','-std=c++17','-shared','-fPIC',str(src),'-o',str(so)],check=True)
  self.lib=ctypes.CDLL(str(so));self.lib.route_grid.argtypes=[ctypes.c_void_p,ctypes.c_void_p]+[ctypes.c_int]*8+[ctypes.c_void_p,ctypes.c_int]
  self.lib.route_grid.restype=ctypes.c_int

 def pad(self,ref,no):return next(p for p in self.fps[ref].Pads() if p.GetNumber()==str(no))
 def track(self,net,a,b,l=0):
  if np.linalg.norm(np.array(a)-np.array(b))<1e-7:return
  t=pcbnew.PCB_TRACK(self.b);t.SetStart(pt(a));t.SetEnd(pt(b));t.SetWidth(pcbnew.FromMM(WIDTH));t.SetLayer(pcbnew.F_Cu if l==0 else pcbnew.B_Cu);t.SetNet(self.net[net]);self.b.Add(t)
  self.geometry.append((net,'line',a,b,WIDTH/2,[l]));self.added.append(t)
 def via(self,net,a):
  if any(n==net and shape=='circle' and math.dist(a,b)<1e-6 for n,shape,b,_,_,_ in self.geometry):return
  v=pcbnew.PCB_VIA(self.b);v.SetPosition(pt(a));v.SetWidth(pcbnew.F_Cu,pcbnew.FromMM(VIA));v.SetWidth(pcbnew.B_Cu,pcbnew.FromMM(VIA));v.SetDrill(pcbnew.FromMM(.4));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetNet(self.net[net]);self.b.Add(v)
  self.geometry.append((net,'circle',a,a,VIA/2,[0,1]));self.added.append(v)

 def draw(self,mask,a,b,r,layers,shape='line'):
  xa,ya=a;xb,yb=b
  x0=max(0,int(math.floor((min(xa,xb)-r-.1)/STEP)));x1=min(W-1,int(math.ceil((max(xa,xb)+r+.1)/STEP)))
  y0=max(0,int(math.floor((min(ya,yb)-r-.1)/STEP)));y1=min(H-1,int(math.ceil((max(ya,yb)+r+.1)/STEP)))
  xx=np.arange(x0,x1+1)[None,:]*STEP;yy=np.arange(y0,y1+1)[:,None]*STEP
  vx=xb-xa;vy=yb-ya;v2=vx*vx+vy*vy
  u=np.clip(((xx-xa)*vx+(yy-ya)*vy)/v2,0,1) if v2 else 0
  near=(xx-xa-u*vx)**2+(yy-ya-u*vy)**2 <= r*r+1e-10
  for l in layers:mask[l,y0:y1+1,x0:x1+1]|=near

 def padmask(self,mask,p,margin):
  x,y=mm(p.GetPosition());sx,sy=mm(p.GetSize());a=math.radians(p.GetOrientationDegrees())
  # Actual rotated pad rectangle; rounded corners conservatively treated square.
  r=max(sx,sy)/2+margin+.1
  x0=max(0,int((x-r)/STEP));x1=min(W-1,int(math.ceil((x+r)/STEP)))
  y0=max(0,int((y-r)/STEP));y1=min(H-1,int(math.ceil((y+r)/STEP)))
  xx=np.arange(x0,x1+1)[None,:]*STEP-x;yy=np.arange(y0,y1+1)[:,None]*STEP-y
  xr=xx*math.cos(a)+yy*math.sin(a);yr=-xx*math.sin(a)+yy*math.cos(a)
  d=np.maximum(abs(xr)-sx/2,0)**2+np.maximum(abs(yr)-sy/2,0)**2
  near=d<=margin*margin
  if p.GetShape()==pcbnew.PAD_SHAPE_CIRCLE:near=(xx*xx+yy*yy)<=(sx/2+margin)**2
  ls=([0] if p.IsOnLayer(pcbnew.F_Cu) else [])+([1] if p.IsOnLayer(pcbnew.B_Cu) else [])
  for l in ls:mask[l,y0:y1+1,x0:x1+1]|=near

 def mask(self,net,via=False):
  m=np.zeros((2,H,W),dtype=np.uint8);rad=VIA/2 if via else WIDTH/2
  for p in self.pads:
   if p.GetNetname()==net:continue
   clear=3.08 if net in HV or p.GetNetname() in HV else CLEAR+.02
   self.padmask(m,p,clear+rad)
  for n,shape,a,b,r,ls in self.geometry:
   if n==net:continue
   clear=3.08 if net in HV or n in HV else CLEAR+.02
   self.draw(m,a,b,r+rad+clear,ls,shape)
  # No copper pours, vias or routes may use the HV divider's clearance area.
  # Local terminal-gap exceptions are used only by the explicit hand-routes.
  m[:,:8,:]=1;m[:,-8:,:]=1;m[:,:,:8]=1;m[:,:,-8:]=1
  return m

 def route(self,net,p,q):
  sx,sy=(int(round(v/STEP)) for v in mm(p.GetPosition()));tx,ty=(int(round(v/STEP)) for v in mm(q.GetPosition()))
  sl=(1 if p.IsOnLayer(pcbnew.F_Cu) else 0)+(2 if p.IsOnLayer(pcbnew.B_Cu) else 0)
  tl=(1 if q.IsOnLayer(pcbnew.F_Cu) else 0)+(2 if q.IsOnLayer(pcbnew.B_Cu) else 0)
  m=self.mask(net);vm=self.mask(net,True)
  # Hole spacing still applies between vias/pads belonging to the same net.
  for n,shape,a,b,r,ls in self.geometry:
   if shape=='circle':self.draw(vm,a,b,.70,[0,1])
  for pad in self.pads:
   drill=mm(pad.GetDrillSize())
   if max(drill)>0:self.draw(vm,mm(pad.GetPosition()),mm(pad.GetPosition()),max(drill)/2+.2+.27,[0,1])
  via_ok=np.ascontiguousarray(~np.any(vm,axis=0),dtype=np.uint8)
  # SMD endpoints can be approached from their actual copper layer only.
  out=np.empty(20000,dtype=np.int32)
  n=self.lib.route_grid(m.ctypes.data,via_ok.ctypes.data,W,H,sx,sy,sl,tx,ty,tl,out.ctypes.data,len(out))
  if n<0:return False
  points=[(int(v)//(W*H),((int(v)%(W*H))%W)*STEP,((int(v)%(W*H))//W)*STEP) for v in out[:n]]
  self.track(net,mm(p.GetPosition()),points[0][1:],points[0][0])
  # Merge collinear grid steps into ordinary editable native copper segments.
  start=points[0];previous=points[0];direction=None
  for node in points[1:]:
   if node[0]!=previous[0]:
    self.track(net,start[1:],previous[1:],previous[0]);self.via(net,node[1:]);start=node;direction=None
   else:
    nd=(round(node[1]-previous[1],4),round(node[2]-previous[2],4))
    if direction is not None and nd!=direction:self.track(net,start[1:],previous[1:],previous[0]);start=previous
    direction=nd
   previous=node
  self.track(net,start[1:],previous[1:],previous[0]);self.track(net,previous[1:],mm(q.GetPosition()),previous[0]);return True

 def run(self):
  # Reserve dense TSSOP fanouts before routing unrelated nets. The seven pins
  # on each side spread to 1.43 mm via pitch; no via is placed inside an SMD pad.
  replacements={}
  for ref in ['U1','U6','U7']:
   f=self.fps[ref];cx,cy=mm(f.GetPosition())
   for p in f.Pads():
    px,py=mm(p.GetPosition());side=-1 if px<cx else 1
    mid=(cx+side*5,py);end=(cx+side*7.5,round(cy+(py-cy)*2.2,1))
    self.track(p.GetNetname(),(px,py),mid);self.track(p.GetNetname(),mid,end);self.via(p.GetNetname(),end)
    endpoint=pcbnew.PAD(f);endpoint.SetPosition(pt(end));endpoint.SetNumber(p.GetNumber());layers=pcbnew.LSET();layers.AddLayer(pcbnew.F_Cu);layers.AddLayer(pcbnew.B_Cu);endpoint.SetLayerSet(layers);endpoint.SetNet(self.net[p.GetNetname()]);replacements[(ref,p.GetNumber())]=endpoint
  for n,pads in self.by_net.items():
   self.by_net[n]=[replacements.get((p.GetParentFootprint().GetReference(),p.GetNumber()),p) for p in pads]
  # Quad IC supply pins sit on opposite edges. Three back-side capacitors lie
  # directly beneath their IC, with dedicated inner vias and short supply loops.
  backside={'C1':('U1','4','11'),'C5':('U6','3','12'),'C6':('U7','3','12')}
  for cap,(ic,vpin,gpin) in backside.items():
   for cp,ip,net in [('1',vpin,'AUX5'),('2',gpin,'PGND')]:
    cpad=self.pad(cap,cp);ipad=self.pad(ic,ip);xy=mm(cpad.GetPosition())
    self.track(net,mm(ipad.GetPosition()),xy,0);self.via(net,xy)
    target=replacements[(ic,ip)]
    self.by_net[net]=[target if p.GetParentFootprint().GetReference()==cap and p.GetNumber()==cp else p for p in self.by_net[net]]
  # Route local supply loops first. Their actual copper is protected against
  # later signals; duplicated endpoints below reflect these real connections.
  decoupling=[('C1','U1','4','11'),('C2','U2','6','4'),('C3','U4','5','2'),('C4','U5','5','2'),('C5','U6','3','12'),('C6','U7','3','12')]
  for cap,ic,vpin,gpin in decoupling:
   if cap in backside:continue
   for cp,ip,net in [('1',vpin,'AUX5'),('2',gpin,'PGND')]:
    source=self.pad(cap,cp);target=replacements.get((ic,ip),self.pad(ic,ip))
    assert self.route(net,source,target),f'Local decoupling escape failed: {cap}:{cp}'
    self.by_net[net]=[target if p.GetParentFootprint().GetReference()==cap and p.GetNumber()==cp else p for p in self.by_net[net]]
  # Hand-route the serial HV divider: each resistor is vertical, copper stays
  # on the outer edge. This respects the exact body-local terminal allowances.
  for net,a,b in [('VOUT_SENSE',('J5',1),('R42',1)),('HV1',('R42',2),('R43',1)),('HV2',('R43',2),('R44',1))]:self.track(net,mm(self.pad(*a).GetPosition()),mm(self.pad(*b).GetPosition()))
  # Leave the final HV resistor through its low-voltage terminal before any
  # lateral route; its own opposite pad is covered by the explicit allowance.
  vmon=mm(self.pad('R44',2).GetPosition());exitpoint=(vmon[0],83)
  self.track('VMON',vmon,exitpoint)
  # Treat R44 VMON as an ordinary endpoint at this already connected escape.
  dummy=pcbnew.PAD(self.fps['R44']);dummy.SetPosition(pt(exitpoint));layers=pcbnew.LSET();layers.AddLayer(pcbnew.F_Cu);dummy.SetLayerSet(layers);dummy.SetNet(self.net['VMON'])
  self.by_net['VMON']=[dummy if p.GetParentFootprint().GetReference()=='R44' else p for p in self.by_net['VMON']]
  priorities={'INM':0,'INP':0,'KS_LOW':0,'KS_HIGH':0,'CC_NEG':1,'CC_COMP':1,'CC_OUT':2,'CV_POS':2,'CV_NEG':2,'DIFF_POS':2,'DIFF_NEG':2,'DELAY':2,'IREF_RAW':2,'IREF':3,'REF25':4,'AUX5':8,'PGND':9,'ENABLE':7}
  failed=[];count=0
  for net,pads in sorted(self.by_net.items(),key=lambda a:(priorities.get(a[0],5),len(a[1]),a[0])):
   if net in HV:continue
   # A Euclidean spanning tree limits length while connecting every pad.
   connected=[pads[0]];remaining=pads[1:]
   while remaining:
    _,i,j=min((math.dist(mm(a.GetPosition()),mm(b.GetPosition())),i,j) for i,a in enumerate(connected) for j,b in enumerate(remaining))
    a=connected[i];b=remaining.pop(j)
    if not self.route(net,a,b):failed.append([net,a.GetParentFootprint().GetReference(),a.GetNumber(),b.GetParentFootprint().GetReference(),b.GetNumber()])
    connected.append(b);count+=1
    if count%10==0:print(f'Routed {count} links, failed {len(failed)}',flush=True)
  return failed

def remove_unused_layer_transitions(board):
 # Fanouts reserve a via site before path finding. When every resulting track
 # at a site uses one layer and meets at the identical endpoint, the drilled
 # transition is unnecessary; remove the via while keeping the actual junction.
 tracks=[t for t in board.GetTracks() if not isinstance(t,pcbnew.PCB_VIA)]
 removed=0
 for via in [v for v in board.GetTracks() if isinstance(v,pcbnew.PCB_VIA)]:
  pos=mm(via.GetPosition());near=[]
  for t in tracks:
   if t.GetNetname()!=via.GetNetname():continue
   a=np.array(mm(t.GetStart()));b=np.array(mm(t.GetEnd()));p=np.array(pos);ab=b-a;d=np.dot(ab,ab)
   u=np.clip(np.dot(p-a,ab)/d,0,1) if d else 0
   if np.linalg.norm(p-a-u*ab)<=VIA/2+pcbnew.ToMM(t.GetWidth())/2+1e-6:near.append(t)
  if len({t.GetLayer() for t in near})==1:
   exact=[t for t in near if math.dist(pos,mm(t.GetStart()))<1e-6 or math.dist(pos,mm(t.GetEnd()))<1e-6]
   if len(exact)>=2:board.Delete(via);removed+=1
 return removed

def main():
 board=pcbnew.LoadBoard(str(PCB));fps={f.GetReference():f for f in board.GetFootprints()}
 assert set(fps)==set(PLACEMENT),'PCB inventory changed; placement requires review'
 for t in list(board.GetTracks()):board.Delete(t)
 for f in fps.values():
  x,y,a=PLACEMENT[f.GetReference()];f.SetPosition(pt((x,y)))
  want_back=f.GetReference() in ['C1','C5','C6']
  if (f.GetLayer()==pcbnew.B_Cu)!=want_back:f.Flip(f.GetPosition(),False)
  f.SetOrientationDegrees(a)
  f.Reference().SetTextSize(pt((.8,.8)));f.Reference().SetTextThickness(pcbnew.FromMM(.12));f.Reference().SetPosition(pt((x,y-3.3 if f.GetReference().startswith('U') else y-2)))
  f.Reference().SetTextAngle(pcbnew.EDA_ANGLE(0,pcbnew.DEGREES_T));f.Value().SetVisible(False)
  if f.GetReference() in ['R42','R43','R44','R45']:f.Reference().SetPosition(pt((150,y)))
  if f.GetReference()=='J5':f.Reference().SetPosition(pt((155,10)))
 for item in board.GetDrawings():
  if isinstance(item,pcbnew.PCB_TEXT) and item.GetText().startswith('UNROUTED'):item.SetText('EXPERIMENTAL ANALOG CV/CC - NOT FOR FABRICATION')
 router=Router(board);failed=router.run();removed=remove_unused_layer_transitions(board);pcbnew.SaveBoard(str(PCB),board)
 cli('pcb','drc','--severity-all','--schematic-parity','--format','json','-o',E/'drc_routed.json',PCB)
 cli('pcb','export','svg','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','--layers','F.Cu,F.SilkS,Edge.Cuts','-o',E/'pcb_front_routed.svg',PCB)
 cli('pcb','export','svg','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','--mirror','--layers','B.Cu,B.SilkS,Edge.Cuts','-o',E/'pcb_back_routed.svg',PCB)
 for side in ['front','back']:
  subprocess.run([str(ROOT/'bin/kicad-env'),'inkscape',str(E/f'pcb_{side}_routed.svg'),'--export-type=png',f'--export-filename={E}/pcb_{side}_routed.png','--export-width=1800'],cwd=ROOT,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 dr=json.loads((E/'drc_routed.json').read_text());objects=list(board.GetTracks());vias=[t for t in objects if isinstance(t,pcbnew.PCB_VIA)]
 summary={'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Experimental single-phase analog control, not the complete laboratory power supply','native_PCB':'design/control/control.kicad_pcb','components':len(fps),'connected_pins':len(router.pads),'nets':len(router.by_net),'board_mm':[180,150],'copper_layers':2,'backside_components':['C1','C5','C6'],'copper_objects':len(objects),'track_segments':len(objects)-len(vias),'vias':len(vias),'unused_layer_transition_vias_removed':removed,'router_failed_links':failed,'drc_violations':len(dr['violations']),'drc_types':dict(collections.Counter(v['type'] for v in dr['violations'])),'unconnected':len(dr['unconnected_items']),'schematic_parity':len(dr['schematic_parity']),'DRC_all_severities_pass':not(failed or dr['violations'] or dr['unconnected_items'] or dr['schematic_parity']),'hardware_tests':'NOT PERFORMED','fabrication_release':False}
 (E/'routing_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
 if not summary['DRC_all_severities_pass']:raise SystemExit(2)
if __name__=='__main__':main()
