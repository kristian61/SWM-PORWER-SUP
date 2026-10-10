#!/usr/bin/python3
"""Rebuild a passive secondary-side measurement draft in KiCad 9.
Run with /usr/bin/python3; never emits fabrication Gerbers or drill files.
"""
from pathlib import Path
import csv, json, os, subprocess, xml.etree.ElementTree as ET
import pcbnew
from kicad_helpers import write_schematic, symbol_tables, uid

ROOT=Path(__file__).resolve().parents[1]
DESIGN=ROOT/'design/measurement'; EXPORT=ROOT/'exports/measurement'
NAME='measurement'; SCH=DESIGN/(NAME+'.kicad_sch'); PCB=DESIGN/(NAME+'.kicad_pcb')
for directory in (DESIGN,EXPORT):directory.mkdir(parents=True,exist_ok=True)
for key,rel in [('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache'),('XDG_DATA_HOME','data')]:
    os.environ.setdefault(key,str(ROOT/'.runtime/kicad'/rel));Path(os.environ[key]).mkdir(parents=True,exist_ok=True)

def cli(*args):
    print('kicad-cli '+' '.join(str(a) for a in args),flush=True)
    subprocess.run(['kicad-cli',*(str(a) for a in args)],check=True)

RHV='Resistor_SMD:R_1206_3216Metric';RLOW='Resistor_SMD:R_0603_1608Metric'
CAP='Capacitor_SMD:C_0603_1608Metric';TPFP='TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm'
J1FP='TerminalBlock_RND:TerminalBlock_RND_205-00241_1x02_P10.16mm_Horizontal'
J2FP='TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3-5.08_1x03_P5.08mm_Horizontal'
J3FP='Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical'
components=[]
def add(ref,value,lib,fp,schxy,boardxy,nets,schangle=0,boardangle=0,description=''):
    c=dict(ref=ref,val=value,lib=lib,footprint=fp,xy=schxy,nets=nets,angle=schangle,uuid=uid(),description=description,board_xy=boardxy,board_angle=boardangle)
    
    if ref.startswith('TP'):c['hide_value']=True
    components.append(c);return c
add('J1','VOLTAGE SENSE 0..120V','Connector_Generic:Conn_01x02',J1FP,(50.8,40.64),(12,15),{'1':'POS_SENSE','2':'NEG_SENSE'},boardangle=-90,description='RND 205-00241 footprint candidate; mechanical and voltage rating require manufacturer verification. Pin1 positive sense; pin2 negative sense. No load current.')
for index,prefix,row,schrow in [(1,'VP',30,60.96),(5,'VN',50,101.6)]:
    hi='POS_SENSE' if index==1 else 'NEG_SENSE';lo='VS_PLUS' if index==1 else 'VS_MINUS'
    netpairs=[(hi,prefix+'1'),(prefix+'1',prefix+'2'),(prefix+'2',lo)]
    for k,(a,b) in enumerate(netpairs):
        add('R'+str(index+k),'130k 0.1%','Device:R',RHV,(60.96+30.48*k,schrow),(25+15*k,row),{'1':a,'2':b},schangle=90,description='130 kohm ±0.1%; >=0.25W; >=100V working voltage; 1206. Maximum ~39V drop and12mW at120V input. Final MPN pending datasheet verification.')
    add('R'+str(index+3),'10k 0.1%','Device:R',RHV,(152.4,schrow),(70,row+3),{'1':lo,'2':'AGND'},boardangle=-90,description='10 kohm ±0.1%; >=0.125W; 1206. Divider lower leg; total nominal ratio1/40.')
add('R9','1k 1%','Device:R',RLOW,(190.5,60.96),(82,30),{'1':'VS_PLUS','2':'VMON_PLUS'},schangle=90,description='Voltage monitor series filter resistor; 1 kohm ±1%,0603.')
add('R10','1k 1%','Device:R',RLOW,(190.5,101.6),(82,50),{'1':'VS_MINUS','2':'VMON_MINUS'},schangle=90,description='Voltage monitor series filter resistor;1 kohm ±1%,0603.')
add('C1','10nF C0G 50V','Device:C',CAP,(228.6,60.96),(90,33),{'1':'VMON_PLUS','2':'AGND'},boardangle=-90,description='10nF ±5%,C0G/NP0,50V,0603. Combined with divider Thevenin9.75k and1k filter gives nominal~1.48kHz pole.')
add('C2','10nF C0G 50V','Device:C',CAP,(228.6,101.6),(90,53),{'1':'VMON_MINUS','2':'AGND'},boardangle=-90,description='10nF ±5%,C0G/NP0,50V,0603. Same filtering asC1.')
add('J2','EXTERNAL SHUNT KELVIN','Connector_Generic:Conn_01x03',J2FP,(50.8,152.4),(15,75),{'1':'KELVIN_PLUS','2':'KELVIN_MINUS','3':'AGND'},description='Phoenix MKDS1.5 3pos5.08mm footprint candidate; pin1 externalshunt high Kelvin,pin2lowKelvin,pin3analogground. Shunt1mohm >=10W outsidePCB; no40A current throughPCB.')
add('R11','1k 1%','Device:R',RLOW,(91.44,152.4),(55,70),{'1':'KELVIN_PLUS','2':'IMON_PLUS'},schangle=90,description='Kelvin shunt monitor series resistor;1 kohm ±1%,0603.')
add('R12','1k 1%','Device:R',RLOW,(91.44,182.88),(55,80),{'1':'KELVIN_MINUS','2':'IMON_MINUS'},schangle=90,description='Kelvin shunt monitor series resistor;1 kohm ±1%,0603.')
add('C3','10nF C0G 50V','Device:C',CAP,(152.4,167.64),(80,75),{'1':'IMON_PLUS','2':'IMON_MINUS'},description='10nF ±5%,C0G/NP0,50V,0603. Differential shunt filter;2k total seriesresistance gives nominal7.96kHzpole.',boardangle=-90)
add('J3','MONITOR OUTPUT - NO ADC','Connector_Generic:Conn_01x06',J3FP,(281.94,152.4),(103,50),{'1':'AGND','2':'VMON_PLUS','3':'VMON_MINUS','4':'IMON_PLUS','5':'IMON_MINUS','6':'AGND'},description='Low current analog output. High input impedance >=10Mohm required for voltage monitors. No clamps,isolation,ADC,orcurrentgainprovided; external frontend must be powered and rated beforeconnection.')
TP_NETS=['POS_SENSE','NEG_SENSE','AGND','VS_PLUS','VS_MINUS','VMON_PLUS','VMON_MINUS','KELVIN_PLUS','KELVIN_MINUS','IMON_PLUS','IMON_MINUS']
TP_XY=[(20,23),(12,40),(78,85),(73,26),(73,46),(87,25),(87,45),(30,66),(30,84),(68,66),(68,84)]
for i,(net,xy) in enumerate(zip(TP_NETS,TP_XY),1):
    add('TP'+str(i),net,'Connector:TestPoint',TPFP,(30.48+30.48*((i-1)%6),228.6+22.86*((i-1)//6)),xy,{'1':net},description=('HV optional test location; guarded fixture only, no hand probing energized.' if i in (1,2) else 'Analog measurement/test point; reference to floating secondaryAGND.'))

project={'meta':{'filename':NAME+'.kicad_pro','version':1},'board':{'design_settings':{'rules':{'min_clearance':0.25,'min_track_width':0.25,'min_copper_edge_clearance':0.5}}},'net_settings':{'classes':[{'name':'Default','clearance':0.25,'track_width':0.4,'via_diameter':0.8,'via_drill':0.4},{'name':'HV','clearance':3.0,'track_width':0.4,'via_diameter':1.0,'via_drill':0.5}], 'netclass_patterns':[{'netclass':'HV','pattern':n} for n in ['POS_SENSE','NEG_SENSE','VP1','VP2','VN1','VN2']],'meta':{'version':4}},'text_variables':{}}
(DESIGN/(NAME+'.kicad_pro')).write_text(json.dumps(project,indent=2)+'\n')
symbol_tables(DESIGN,[c['lib'] for c in components])
footlibs=sorted({c['footprint'].split(':')[0] for c in components})
(DESIGN/'fp-lib-table').write_text('(fp_lib_table (version 7)\n'+'\n'.join(f'(lib (name "{l}") (type "KiCad") (uri "${{KICAD9_FOOTPRINT_DIR}}/{l}.pretty") (options "") (descr "KiCad 9 standard library"))' for l in footlibs)+'\n)\n')
rootid,_=write_schematic(SCH,components,title='MÅLEKORT UDKAST - IKKE 4 kW EFFEKTTRIN',comments=['Floating DC secondary; NONISOLATED to secondary AGND','0..120 V relative AGND; divider 1/40; 100 V gives 2.5 V','External four-terminal 1 mohm shunt; 40 A gives 40 mV','No ADC or clamps; input >=10 Mohm; powered frontend only'],texts=[dict(xy=(15.24,20.32),text='PASSIVT MÅLEKORT UDKAST - IKKE 4 kW EFFEKTTRIN\nIngen forbindelse til 230 V AC eller PE. Flydende DC-sekundaer AGND.'),dict(xy=(15.24,125.73),text='Vout = 40*(VMON_PLUS - VMON_MINUS), ideal unloaded ratio.\nBoth sense inputs: 0..120 V relative AGND; no negative common mode.\n130 k resistors rated >=100 V; max 39 V drop at 120 V total input.'),dict(xy=(15.24,203.2),text='External 1 mohm four-terminal shunt >=10 W, rated >=50 A DC; outside PCB.\n40 A -> 40 mV; I = (IMON_PLUS - IMON_MINUS) / 0.001 ohm.\nTP1/TP2 energized HV: no hand probing; guarded fixture only.'),dict(xy=(228.6,228.6),text='No active protection, no ADC, no CC/CV control.\nMonitor loads affect gain; input impedance >=10 Mohm.\nDo not connect unpowered ADC. Prototype only.')])
cli('sch','export','netlist','--format','kicadxml','-o',EXPORT/(NAME+'.xml'),SCH)
xml=ET.parse(EXPORT/(NAME+'.xml')).getroot()
expected={c['ref']:c for c in components}
netpins={}
for net in xml.find('nets'):
    netpins[net.attrib['name']]={(node.attrib['ref'],node.attrib['pin']) for node in net.findall('node')}
want={}
for c in components:
    for pin,net in c['nets'].items():want.setdefault(net,set()).add((c['ref'],pin))
assert netpins==want,'Schematic export does not match intended component pin map'
board=pcbnew.BOARD();nets={};fps={}
for name in netpins:
    n=pcbnew.NETINFO_ITEM(board,name);board.Add(n);nets[name]=n
for c in components:
    lib,part=c['footprint'].split(':',1)
    fp=pcbnew.FootprintLoad('/usr/share/kicad/footprints/'+lib+'.pretty',part)
    if fp is None:raise RuntimeError('Missing footprint '+c['footprint'])
    fp.SetAttributes(fp.GetAttributes() & ~pcbnew.FP_EXCLUDE_FROM_BOM);fp.SetFPID(pcbnew.LIB_ID(lib,part));fp.SetReference(c['ref']);fp.SetValue(c['val'])
    fp.SetPosition(pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in c['board_xy'])));fp.SetOrientationDegrees(c['board_angle'])
    path=pcbnew.KIID_PATH();path.push_back(pcbnew.KIID(rootid));path.push_back(pcbnew.KIID(c['uuid']));fp.SetPath(path)
    for pad in fp.Pads():pad.SetNet(nets[c['nets'][pad.GetNumber()]])
    fp.Reference().SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1),pcbnew.FromMM(1)));fp.Reference().SetTextThickness(pcbnew.FromMM(.15))
    fp.Reference().SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(c['board_xy'][0]),pcbnew.FromMM(c['board_xy'][1]-3.4)))
    fp.Value().SetVisible(False);
    if c['ref']=='J1':fp.Reference().SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(5),pcbnew.FromMM(20)))
    board.Add(fp);fps[c['ref']]=fp

def point(xy):return pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in xy))
def pad(ref,pin):
    p=next(p for p in fps[ref].Pads() if p.GetNumber()==str(pin)).GetPosition()
    return (pcbnew.ToMM(p.x),pcbnew.ToMM(p.y))
def wire(net,coords,layer=pcbnew.F_Cu,width=.4):
    for a,b in zip(coords,coords[1:]):
        if a==b:continue
        t=pcbnew.PCB_TRACK(board);t.SetStart(point(a));t.SetEnd(point(b));t.SetWidth(pcbnew.FromMM(width));t.SetLayer(layer);t.SetNet(nets[net]);board.Add(t)
def via(net,xy):
    v=pcbnew.PCB_VIA(board);v.SetPosition(point(xy));v.SetWidth(pcbnew.F_Cu,pcbnew.FromMM(1));v.SetWidth(pcbnew.B_Cu,pcbnew.FromMM(1));v.SetDrill(pcbnew.FromMM(.5));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetNet(nets[net]);board.Add(v)
# Two physically separated voltage divider chains; small currents only.
wire('POS_SENSE',[pad('J1',1),(20,15),(20,30),pad('R1',1)])
wire('POS_SENSE',[(20,23),pad('TP1',1)])
wire('NEG_SENSE',[pad('J1',2),(12,50),pad('R5',1)])
wire('NEG_SENSE',[(12,40),pad('TP2',1)])
for a,b,net in [('R1','R2','VP1'),('R2','R3','VP2'),('R5','R6','VN1'),('R6','R7','VN2')]:wire(net,[pad(a,2),pad(b,1)])
for start,lower,flt,cap,tpv,tpo,row,vx,endy,output in [('R3','R4','R9','C1','TP4','TP6',30,99,52.54,2),('R7','R8','R10','C2','TP5','TP7',50,96,55.08,3)]:
    raw='VS_PLUS' if row==30 else 'VS_MINUS';monitor='VMON_PLUS' if row==30 else 'VMON_MINUS'
    wire(raw,[pad(start,2),pad(flt,1)]);wire(raw,[(70,row),pad(lower,1)]);wire(raw,[(73,row),pad(tpv,1)])
    wire(monitor,[pad(flt,2),(vx,row),(vx,endy),pad('J3',output)]);wire(monitor,[(90,row),pad(cap,1)]);wire(monitor,[(87,row),pad(tpo,1)])
wire('KELVIN_PLUS',[pad('J2',1),(15,70),pad('R11',1)]);wire('KELVIN_PLUS',[(30,70),pad('TP8',1)])
wire('KELVIN_MINUS',[pad('J2',2),(20.08,80),pad('R12',1)]);wire('KELVIN_MINUS',[(30,80),pad('TP9',1)])
wire('IMON_PLUS',[pad('R11',2),(93,70),(93,57.62),pad('J3',4)]);wire('IMON_PLUS',[(68,70),pad('TP10',1)]);wire('IMON_PLUS',[(80,70),pad('C3',1)])
wire('IMON_MINUS',[pad('R12',2),(99,80),(99,60.16),pad('J3',5)]);wire('IMON_MINUS',[(68,80),pad('TP11',1)]);wire('IMON_MINUS',[(80,80),pad('C3',2)])
# AGND is routed only on the low voltage side; no ground pour underHV traces.
for ref,row in [('R4',36),('R8',56)]:wire('AGND',[pad(ref,2),(72,pad(ref,2)[1]),(72,row)]);via('AGND',(72,row))
for ref,row in [('C1',36),('C2',56)]:wire('AGND',[pad(ref,2),(90,row)]);via('AGND',(90,row))
wire('AGND',[(72,36),(90,36)],pcbnew.B_Cu);wire('AGND',[(72,56),(90,56)],pcbnew.B_Cu)
wire('AGND',[(76,36),(76,87)],pcbnew.B_Cu)
wire('AGND',[pad('J2',3),(25.16,87),(106,87)],pcbnew.B_Cu)
wire('AGND',[pad('J3',1),(106,50),(106,87)],pcbnew.B_Cu);wire('AGND',[pad('J3',6),(106,62.7)],pcbnew.B_Cu)
wire('AGND',[pad('TP3',1),(78,87)],pcbnew.B_Cu)
for a,b in [((0,0),(110,0)),((110,0),(110,90)),((110,90),(0,90)),((0,90),(0,0))]:
    e=pcbnew.PCB_SHAPE(board);e.SetShape(pcbnew.SHAPE_T_SEGMENT);e.SetStart(point(a));e.SetEnd(point(b));e.SetLayer(pcbnew.Edge_Cuts);e.SetWidth(pcbnew.FromMM(.05));board.Add(e)
def text(label,xy,size=1.2,layer=pcbnew.F_SilkS):
    t=pcbnew.PCB_TEXT(board);t.SetText(label);t.SetPosition(point(xy));t.SetTextSize(point((size,size)));t.SetTextThickness(pcbnew.FromMM(.15));t.SetLayer(layer);board.Add(t)
text('MÅLEKORT UDKAST - IKKE 4 kW EFFEKTTRIN',(56,5),1.5)
text('FLOATING SECONDARY / NONISOLATED TO AGND',(56,9),1.0)
text('HV 0..120 V',(37,18),1.1);text('NO LOAD CURRENT',(45,22),1.0)
text('HV FIXTURE ONLY',(34,39),1.0);text('NO HAND PROBING TP1/TP2',(42,43),.85)
text('SHUNT KELVIN ONLY',(47,60),1.0);text('1 mOhm EXTERNAL / 40 A = 40 mV',(46,63),.85)
text('NO ADC / NO CLAMPS / NO CC-CV',(64,88),.85)
text('NO MAINS / NO PE',(46,54),.85)
board.GetDesignSettings().SetCopperLayerCount(2)
pcbnew.SaveBoard(str(PCB),board)
# Preserve native defaults, especially rule_severities. Omitting that dictionary
# suppresses geometric DRC providers even when a custom .kicad_dru exists.
native_project=json.loads((DESIGN/(NAME+'.kicad_pro')).read_text())
native_project['board']['design_settings']['rules'].update(project['board']['design_settings']['rules'])
native_class=native_project['net_settings']['classes'][0].copy()
native_project['net_settings']['classes']=[]
for desired in project['net_settings']['classes']:
    merged=native_class.copy();merged.update(desired)
    merged['priority']=2147483647 if desired['name']=='Default' else 0
    native_project['net_settings']['classes'].append(merged)
native_project['net_settings']['netclass_patterns']=project['net_settings']['netclass_patterns']
native_project['net_settings']['meta']={'version':4}
(DESIGN/(NAME+'.kicad_pro')).write_text(json.dumps(native_project,indent=2)+'\n')
# Hierarchical paths and exportedXML pin maps agree with allPCB pad net names.
actual={}
for fp in board.GetFootprints():
    for p in fp.Pads():actual.setdefault(p.GetNetname(),set()).add((fp.GetReference(),p.GetNumber()))
assert actual==want,'PCB pad/net mapping differs from schematic'
(EXPORT/'pin_net_agreement.json').write_text(json.dumps({'status':'PASS','components':len(components),'nets':len(want),'pins':sum(map(len,want.values())),'root_uuid':rootid,'schematic_xml':'measurement.xml','note':'Logical pin mapping agreement; electricalperformance not validated'},indent=2)+'\n')
# General HV separation rule with explicit component-local pad-gap allowances.
# These are designconstraints, not violation exclusions. 1206 geometry cannot
# provide3mm across resistor terminals; each stage drops~39V at120V input.
rules=['(version 1)','(rule "Default geometric minimums" (constraint clearance (min 0.25mm)) (constraint track_width (min 0.25mm)) (constraint edge_clearance (min 0.5mm)))','(rule "HV copper separation away from divider bodies" (condition "A.NetClass == \'HV\' || B.NetClass == \'HV\'") (constraint clearance (min 3.0mm)))']
for ref in ['R1','R2','R3','R5','R6','R7']:
    pair=expected[ref]['nets']
    net_a,net_b=pair['1'],pair['2']
    condition=(f"A.intersectsCourtyard('{ref}') && B.intersectsCourtyard('{ref}') && "
               f"((A.NetName == '{net_a}' && B.NetName == '{net_b}') || "
               f"(A.NetName == '{net_b}' && B.NetName == '{net_a}'))")
    rules.append(f'(rule "Explicit {ref} 1206 intended-net terminal-gap allowance" (condition "{condition}") (constraint clearance (min 1.5mm)))')
(DESIGN/(NAME+'.kicad_dru')).write_text('\n'.join(rules)+'\n')
# BOM is every physically populatedPCB component, withoutinvented finalMPNs.
with (EXPORT/'bom_measurement.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['Reference','Value','Footprint','Quantity','Description','Release_status'])
    for c in components:w.writerow([c['ref'],c['val'],c['footprint'],1,c['description'],'DRAFT - MPN and datasheet review pending'])

(ROOT/'bom').mkdir(exist_ok=True)
(ROOT/'bom/measurement.csv').write_bytes((EXPORT/'bom_measurement.csv').read_bytes())
with (ROOT/'bom/measurement.csv').open('a',newline='') as f:
    csv.writer(f).writerow(['SHUNT_EXT','1 mohm; four-terminal; >=10 W; >=50 A DC','OFFBOARD - no PCB footprint',1,'External power shunt; final manufacturer and datasheet required','OFFBOARD REQUIREMENT - not a populated board component'])
cli('sch','export','pdf','-o',EXPORT/(NAME+'.pdf'),SCH)
cli('sch','export','svg','-o',EXPORT/'schematic_svg/',SCH)
cli('sch','erc','--exit-code-violations','--format','json','-o',EXPORT/'erc.json',SCH)
cli('pcb','export','svg','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','--black-and-white','--layers','F.Cu,F.SilkS,Edge.Cuts','-o',EXPORT/'pcb_front.svg',PCB)
cli('pcb','export','svg','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','--black-and-white','--mirror','--layers','B.Cu,B.SilkS,Edge.Cuts','-o',EXPORT/'pcb_back.svg',PCB)
cli('pcb','drc','--schematic-parity','--exit-code-violations','--format','json','-o',EXPORT/'drc.json',PCB)
print('Generated native KiCad source, PDF/SVG review exports, BOM, ERC/DRC reports. No fabrication files generated.')
