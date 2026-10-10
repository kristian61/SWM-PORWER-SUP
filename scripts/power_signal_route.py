#!/usr/bin/python3
"""Complete signal/test-point routes after power_phase_gen.py.

Retains all original power and Kelvin routes. No pad/net/values are reassigned,
no DRC exclusions are made, and no fabrication files are emitted. Every batch
is checked with native all-severity DRC and schematic parity. The router's
conservative geometry mask is only a search aid, never a DRC substitute.
"""
from pathlib import Path
import os,json,math,subprocess,ctypes,collections,sys
ROOT=Path(__file__).resolve().parents[1]
for key,rel in [('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache'),('XDG_DATA_HOME','data')]:os.environ.setdefault(key,str(ROOT/'.runtime/kicad'/rel))
import pcbnew
import numpy as np
from control_route import Router as BaseRouter
import control_route as base
D=ROOT/'design/power'; E=ROOT/'exports/power'; PCB=D/'power_phase.kicad_pcb'
STEP=.1;W=1351;H=901;WIDTH=.18;VIA=.5;LAYERS=[pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu]
base.STEP=STEP;base.W=W;base.H=H
HV=set('VIN VOUT PREOUT SWA SWB GA GD BST1 BST2 TG1 TG2 FBMID OVMID OUTSNS IAVGP IAVGN'.split())
LOW=set('BG1 BG2 VINOV V5 PGND AUX12 NDRV_TIE DRVCC SS VFB SENSEP SENSEN ITH SYNC FREQ PGOOD RUN'.split())
FLOAT=[('SWA','GA'),('SWA','TG1'),('SWA','BST1'),('GA','TG1'),('TG1','BST1'),('SWB','GD'),('SWB','TG2'),('SWB','BST2'),('GD','TG2'),('TG2','BST2'),('PREOUT','VOUT'),('IAVGP','IAVGN')]
LOCAL=[('SWB','TG2'),('TG2','BST2'),('SWA','TG1'),('TG1','BST1')]
def pair(n,m,pairs):return (n,m) in pairs or (m,n) in pairs
def mm(p):return (pcbnew.ToMM(p.x),pcbnew.ToMM(p.y))
def pt(xy):return pcbnew.VECTOR2I(*(pcbnew.FromMM(float(v)) for v in xy))
def inside(a):return 63.15<=a[0]<=70.85 and 25.9<=a[1]<=36.1
def clearance(n,m):return .5 if pair(n,m,FLOAT) else (1.5 if n in HV or m in HV else .25)
class Router(BaseRouter):
 def __init__(self,b):
  self.b=b;self.fps={f.GetReference():f for f in b.GetFootprints()};self.net={n.GetNetname():n for n in b.GetNetsByNetcode().values()};self.pads=[p for f in self.fps.values() for p in f.Pads() if p.GetNumber()];self.geometry=[];self.added=[]
  b.BuildConnectivity();self.conn=b.GetConnectivity();self.vias=[t for t in b.GetTracks() if type(t)==pcbnew.PCB_VIA];self.uuid={p.m_Uuid.AsString():p for p in self.pads}
  for t in b.GetTracks():
   self.uuid[t.m_Uuid.AsString()]=t
   if type(t)==pcbnew.PCB_VIA:self.geometry.append((t.GetNetname(),'circle',mm(t.GetPosition()),mm(t.GetPosition()),pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu))/2,list(range(4))))
   else:self.geometry.append((t.GetNetname(),'line',mm(t.GetStart()),mm(t.GetEnd()),pcbnew.ToMM(t.GetWidth())/2,[LAYERS.index(t.GetLayer())]))
  so=ROOT/'.runtime/power_router_grid.so';src=ROOT/'scripts/power_route_grid.cpp'
  if not so.exists() or src.stat().st_mtime>so.stat().st_mtime:subprocess.run(['g++','-O3','-std=c++17','-shared','-fPIC',str(src),'-o',str(so)],check=True)
  self.lib=ctypes.CDLL(str(so));self.lib.route_grid.argtypes=[ctypes.c_void_p,ctypes.c_void_p]+[ctypes.c_int]*8+[ctypes.c_void_p,ctypes.c_int];self.lib.route_grid.restype=ctypes.c_int
 def track(self,n,a,b,l=0):
  if math.dist(a,b)<1e-7:return
  t=pcbnew.PCB_TRACK(self.b);t.SetStart(pt(a));t.SetEnd(pt(b));t.SetWidth(pcbnew.FromMM(WIDTH));t.SetLayer(LAYERS[l]);t.SetNet(self.net[n]);self.b.Add(t);self.geometry.append((n,'line',a,b,WIDTH/2,[l]));self.added.append(t)
 def via(self,n,a):
  if any(k==n and s=='circle' and math.dist(a,p)<1e-6 for k,s,p,q,r,ls in self.geometry):return
  v=pcbnew.PCB_VIA(self.b);v.SetPosition(pt(a));v.SetWidth(pcbnew.F_Cu,pcbnew.FromMM(VIA));v.SetWidth(pcbnew.B_Cu,pcbnew.FromMM(VIA));v.SetDrill(pcbnew.FromMM(.3));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetNet(self.net[n]);self.b.Add(v);self.geometry.append((n,'circle',a,a,VIA/2,list(range(4))));self.added.append(v)
 def padmask(self,mask,p,margin):
  # Reuse native oriented-pad rasterisation, with all four actual copper layers.
  x,y=mm(p.GetPosition());sx,sy=mm(p.GetSize());a=math.radians(p.GetOrientationDegrees());r=max(sx,sy)/2+margin+.1
  x0=max(0,int((x-r)/STEP));x1=min(W-1,int(math.ceil((x+r)/STEP)));y0=max(0,int((y-r)/STEP));y1=min(H-1,int(math.ceil((y+r)/STEP)))
  xx=np.arange(x0,x1+1)[None,:]*STEP-x;yy=np.arange(y0,y1+1)[:,None]*STEP-y;xr=xx*math.cos(a)+yy*math.sin(a);yr=-xx*math.sin(a)+yy*math.cos(a)
  near=np.maximum(abs(xr)-sx/2,0)**2+np.maximum(abs(yr)-sy/2,0)**2<=margin*margin
  if p.GetShape()==pcbnew.PAD_SHAPE_CIRCLE:near=xx*xx+yy*yy<=(sx/2+margin)**2
  for l,layer in enumerate(LAYERS):
   if p.IsOnLayer(layer):mask[l,y0:y1+1,x0:x1+1]|=near
 def mask(self,n,via=False):
  m=np.zeros((4,H,W),dtype=np.uint8);rad=VIA/2 if via else WIDTH/2
  # Restore normal spacing outside the U1 courtyard. Package geometry is used
  # only within its actual documented 7.7 x 10.2 mm courtyard.
  for p in self.pads:
   k=p.GetNetname()
   if k==n:continue
   c=clearance(n,k)
   if p.GetParentFootprint().GetReference()=='U1':
    local=.2 if ((n in LOW and k in LOW) or pair(n,k,LOCAL)) else .7
    temp=np.zeros_like(m);self.padmask(temp,p,local+rad+.005)
    outside=np.zeros_like(m);self.padmask(outside,p,c+rad+.015)
    outside[:,259:362,632:709]=temp[:,259:362,632:709];m|=outside
   elif p.GetParentFootprint().GetReference() in ['Q1','Q2','Q3','Q4','C13','C14','D1','D2','C16','R17','R18','R19','R11','R14']:
    f=p.GetParentFootprint();corners=[xy for g in f.GraphicalItems() if g.GetLayer() in [pcbnew.F_CrtYd,pcbnew.B_CrtYd] for xy in [mm(g.GetStart()),mm(g.GetEnd())]]
    xs=[v[0] for v in corners];ys=[v[1] for v in corners];x0,x1=int(min(xs)/STEP),int(max(xs)/STEP)+1;y0,y1=int(min(ys)/STEP),int(max(ys)/STEP)+1
    temp=np.zeros_like(m);self.padmask(temp,p,.5+rad+.015);outside=np.zeros_like(m);self.padmask(outside,p,c+rad+.015);outside[:,y0:y1,x0:x1]=temp[:,y0:y1,x0:x1];m|=outside
   else:self.padmask(m,p,max(c,.5 if p.GetParentFootprint().GetReference() in ['D1','D2'] else c)+rad+.015)
  for k,s,a,b,r,ls in self.geometry:
   if k==n:continue
   c=clearance(n,k)
   if (inside(a) or inside(b)):
    local=.2 if ((n in LOW and k in LOW) or pair(n,k,LOCAL)) else .7
    temp=np.zeros_like(m);self.draw(temp,a,b,r+rad+local+.005,ls,s)
    outside=np.zeros_like(m);self.draw(outside,a,b,r+rad+c+.015,ls,s)
    outside[:,259:362,632:709]=temp[:,259:362,632:709];m|=outside
   else:self.draw(m,a,b,r+rad+c+.015,ls,s)
  m[:,:12,:]=1;m[:,-12:,:]=1;m[:,:,:12]=1;m[:,:,-12:]=1
  return m
 def endpoint(self,node):
  obj=self.uuid.get(node['uuid']);xy=(node['pos']['x'],node['pos']['y'])
  if obj is None:raise ValueError(node)
  # Airwire endpoints can name an SMD pad although its already routed local
  # escape reaches a through via. Start at that actual connected via, allowing
  # inner-layer routing without inserting an overlapping duplicate via.
  queue=[obj];seen=set();vias=[]
  while queue:
   item=queue.pop()
   if item.Type()==pcbnew.PCB_VIA_T:item=pcbnew.Cast_to_PCB_VIA(item)
   key=item.m_Uuid.AsString()
   if key in seen:continue
   seen.add(key)
   if type(item)==pcbnew.PCB_VIA:vias.append(item)
   queue.extend(t for t in self.conn.GetConnectedTracks(item) if t.m_Uuid.AsString() not in seen)
   if type(item)==pcbnew.PCB_TRACK:
    a=np.array(mm(item.GetStart()));b=np.array(mm(item.GetEnd()));ab=b-a;d=float(ab@ab)
    for v in self.vias:
     if v.GetNetname()!=item.GetNetname() or v.m_Uuid.AsString() in seen:continue
     pos=np.array(mm(v.GetPosition()));near=a+max(0,min(1,float((pos-a)@ab/d)))*ab if d else a
     if float(np.linalg.norm(pos-near))<pcbnew.ToMM(item.GetWidth())/2+pcbnew.ToMM(v.GetWidth(pcbnew.F_Cu))/2:queue.append(v)
  if vias:
   obj=min(vias,key=lambda v:math.dist(xy,mm(v.GetPosition())));xy=mm(obj.GetPosition())
  if type(obj)==pcbnew.PCB_TRACK:ls=1<<LAYERS.index(obj.GetLayer())
  else:ls=sum(1<<l for l,layer in enumerate(LAYERS) if obj.IsOnLayer(layer))
  return xy,ls,obj.GetNetname()
 def connection(self,a,b):
  ap,sl,n=self.endpoint(a);bp,tl,n2=self.endpoint(b);assert n==n2
  sx,sy=(int(round(v/STEP)) for v in ap);tx,ty=(int(round(v/STEP)) for v in bp)
  m=self.mask(n);vm=self.mask(n,True)
  for k,s,p,q,r,ls in self.geometry:
   if s=='circle':self.draw(vm,p,q,r+.35,list(range(4)))
  for p in self.pads:
   drill=mm(p.GetDrillSize())
   if max(drill)>0:self.draw(vm,mm(p.GetPosition()),mm(p.GetPosition()),max(drill)/2+.36,list(range(4)))
  via_ok=np.ascontiguousarray(~np.any(vm,axis=0),dtype=np.uint8);out=np.empty(25000,dtype=np.int32)
  z=self.lib.route_grid(m.ctypes.data,via_ok.ctypes.data,W,H,sx,sy,sl,tx,ty,tl,out.ctypes.data,len(out))
  if z<0:return False
  points=[(int(v)//(W*H),((int(v)%(W*H))%W)*STEP,((int(v)%(W*H))//W)*STEP) for v in out[:z]]
  self.track(n,ap,points[0][1:],points[0][0]);start=prev=points[0];direction=None
  for node in points[1:]:
   if node[0]!=prev[0]:self.track(n,start[1:],prev[1:],prev[0]);self.via(n,node[1:]);start=node;direction=None
   else:
    nd=(round(node[1]-prev[1],4),round(node[2]-prev[2],4))
    if direction is not None and nd!=direction:self.track(n,start[1:],prev[1:],prev[0]);start=prev
    direction=nd
   prev=node
  self.track(n,start[1:],prev[1:],prev[0]);self.track(n,prev[1:],bp,prev[0]);return True
def drc():
 r=subprocess.run([str(ROOT/'bin/kicad-env'),'kicad-cli','pcb','drc','--severity-all','--schematic-parity','--exit-code-violations','--format','json','-o',str(E/'drc.json'),str(PCB)],cwd=ROOT,stdout=subprocess.DEVNULL)
 assert r.returncode in (0,5);return json.loads((E/'drc.json').read_text())
PLAN=ROOT/'scripts/power_routing_plan.json'
def capture():
 b=pcbnew.LoadBoard(str(PCB));objects=[]
 for t in b.GetTracks():
  if type(t)==pcbnew.PCB_VIA:objects.append({'kind':'via','net':t.GetNetname(),'at':mm(t.GetPosition()),'diameter_mm':[pcbnew.ToMM(t.GetWidth(l)) for l in LAYERS],'drill_mm':pcbnew.ToMM(t.GetDrill())})
  else:objects.append({'kind':'track','net':t.GetNetname(),'start':mm(t.GetStart()),'end':mm(t.GetEnd()),'width_mm':pcbnew.ToMM(t.GetWidth()),'layer':b.GetLayerName(t.GetLayer())})
 objects.sort(key=lambda o:(o['net'],o['kind'],json.dumps(o,sort_keys=True)))
 pads=sorted((f.GetReference(),p.GetNumber(),p.GetNetname()) for f in b.GetFootprints() for p in f.Pads() if p.GetNumber())
 plan={'format':1,'scope':'Deterministic copper geometry for fixed 99.6 V / 10 A research PCB; no hardware/fabrication qualification','board_size_mm':[135,90],'copper_layers':['F.Cu','In1.Cu','In2.Cu','B.Cu'],'pad_net_pairs':pads,'objects':objects}
 PLAN.write_text(json.dumps(plan,indent=2)+'\n');print('Captured',len(objects),'native copper objects')
def replay():
 plan=json.loads(PLAN.read_text());b=pcbnew.LoadBoard(str(PCB));nets={n.GetNetname():n for n in b.GetNetsByNetcode().values()};layers={b.GetLayerName(l):l for l in LAYERS}
 pads=sorted((f.GetReference(),p.GetNumber(),p.GetNetname()) for f in b.GetFootprints() for p in f.Pads() if p.GetNumber())
 assert pads==[tuple(p) for p in plan['pad_net_pairs']],'Routing plan does not match logical PCB pins'
 # Keep native project settings byte-for-byte, including all rule severities.
 project_path=D/'power_phase.kicad_pro';native_project=project_path.read_bytes()
 for t in list(b.GetTracks()):b.Delete(t)
 for o in plan['objects']:
  if o['kind']=='via':
   t=pcbnew.PCB_VIA(b);t.SetPosition(pt(o['at']));t.SetViaType(pcbnew.VIATYPE_THROUGH);t.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);t.SetDrill(pcbnew.FromMM(o['drill_mm']))
   for layer,diameter in zip(LAYERS,o['diameter_mm']):t.SetWidth(layer,pcbnew.FromMM(diameter))
  else:
   t=pcbnew.PCB_TRACK(b);t.SetStart(pt(o['start']));t.SetEnd(pt(o['end']));t.SetLayer(layers[o['layer']]);t.SetWidth(pcbnew.FromMM(o['width_mm']))
  t.SetNet(nets[o['net']]);b.Add(t)
 pcbnew.SaveBoard(str(PCB),b);project_path.write_bytes(native_project)
 print('Replayed',len(plan['objects']),'native copper objects; unchanged logical pins and project rules')
def run():
 for iteration in range(4):
  report=drc();b=pcbnew.LoadBoard(str(PCB));r=Router(b);success=0
  items=report['unconnected_items']
  # Local IC escapes first, then near-to-far signal and test-point links.
  items.sort(key=lambda e:(0 if any('of U1' in n['description'] for n in e['items']) else 1,math.dist(tuple(e['items'][0]['pos'].values()),tuple(e['items'][1]['pos'].values()))))
  for e in items:
   ok=r.connection(*e['items']);success+=ok
   print(iteration,'OK' if ok else 'BLOCKED',e['items'][0]['description'],'->',e['items'][1]['description'],flush=True)
  pcbnew.SaveBoard(str(PCB),b);new=drc();print('BATCH',iteration,'added',len(r.added),'unconnected',len(new['unconnected_items']),'violations',len(new['violations']),flush=True)
  if not success or not new['unconnected_items']:break
if __name__=='__main__':
 if '--capture' in sys.argv:capture()
 elif '--replay' in sys.argv:replay()
 else:run()
