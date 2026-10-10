#!/usr/bin/python3
"""Generate a source-backed LTC3779 single-phase research schematic/layout.
This is fixed99.6V/10A target, NOT the requested complete0..100V/40A supply.
Layout remains an engineering prototype, not fabrication release.
No Gerbers or drill files. /usr/bin/python3 required for pcbnew.
"""
from pathlib import Path
import sys,json,csv,subprocess,os,xml.etree.ElementTree as ET
for key,rel in [('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache'),('XDG_DATA_HOME','data')]:
 os.environ.setdefault(key,str(Path('/workspace/scratch/kicad-psu-runtime')/rel))
import pcbnew
import kicad_helpers as h
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'design/power';E=ROOT/'exports/power';E.mkdir(parents=True,exist_ok=True)
NAME='power_phase';WRAP=ROOT/'bin/kicad-env'
# Project-local custom library; keep helper and systemlibraries unchanged.
original_library=h.library
def project_library(name):
 return h.parse((D/'PowerPhase.kicad_sym').read_text()) if name=='PowerPhase' else original_library(name)
h.library=project_library
DS='https://www.analog.com/media/en/technical-documentation/data-sheets/ltc3779.pdf'
DEMO='https://www.analog.com/media/en/technical-documentation/user-guides/DC2456AF.PDF'
FET_DS='https://www.infineon.com/assets/row/public/documents/24/49/infineon-bsc110n15ns5-datasheet-en.pdf'
R='Resistor_SMD:R_0603_1608Metric';RH='Resistor_SMD:R_1206_3216Metric';SH='Resistor_SMD:R_2512_6332Metric';C='Capacitor_SMD:C_0603_1608Metric';CH='Capacitor_SMD:C_2220_5750Metric';CB='Capacitor_THT:CP_Radial_D12.5mm_P5.00mm';TP='TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm';J='TerminalBlock_RND:TerminalBlock_RND_205-00241_1x02_P10.16mm_Horizontal'
components=[];power=[];control=[]

def add(ref,val,lib,fp,xy,bxy,nets,desc,source='',status='DESIGN VALUE - FINAL MPN/DATASHEET PENDING',sheet='power',angle=0):
 c=dict(ref=ref,val=val,lib=lib,footprint=fp,xy=xy,board_xy=bxy,nets=nets,description=desc,datasheet=source,release=status,uuid=h.uid(),angle=angle,label_length=3.81)
 components.append(c);(power if sheet=='power' else control).append(c)
 return c

add('J1','ISOLATED DC INPUT <=120V','Connector_Generic:Conn_01x02',J,(30.48,30.48),(10,15),{'1':'VIN','2':'PGND'},'External isolated source; researchfixture110..115Vnominal,120Vmaximum. No230VACorPE. Connectorvoltage/currentMPNunverified.')
add('J2','99.6V FIXED OUTPUT / 10A TARGET','Connector_Generic:Conn_01x02',J,(350.52,30.48),(165,15),{'1':'VOUT','2':'PGND'},'10Aengineeringtarget only; currentthermalperformanceunvalidated. NativeCCceiling~12.5A,notadjustable. ConnectorMPNpending.')
fpfet='Package_SON:Infineon_PG-TDSON-8_6.15x5.15mm'
for ref,gate,drain,source,xy,bxy in [('Q1','GA','VIN','SWA',(99.06,60.96),(35,40)),('Q2','GB','SWA','CS',(99.06,116.84),(35,55)),('Q3','GC','SWB','CS',(279.4,116.84),(125,55)),('Q4','GD','PREOUT','SWB',(279.4,60.96),(125,40))]:
 add(ref,'BSC110N15NS5','PowerPhase:BSC110N15NS5_REFERENCE',fpfet,xy,bxy,{'1':source,'2':source,'3':source,'4':gate,'5':drain},'Infineon Rev2.6 verified:150V,VGS+/-20V,Rdsmax11mohm at10V/25C/38A,Tjmax150C. Source1/2/3,gate4,common drain5..8 represented by footprintpad5. SOA,ringing,layout and thermal review still pending.',FET_DS,'MANUFACTURER DATASHEET/PINOUT VERIFIED - LAYOUT/THERMAL VALIDATION PENDING')
add('L1','150uH EXTERNAL','Device:L',J,(190.5,88.9),(80,40),{'1':'SWA','2':'SWB'},'Calculated150uHdesignrequirement at~102kHz;Irms>=15A;hotIsat>=25A. Externalinductor; terminalfootprintisplaceholder,notawindinglayout. Vendor,coreloss,DCR,warmIsatandconnectorpending.',DS,angle=90)
for ref,xy,bxy in [('R1',(137.16,162.56),(60,55)),('R2',(238.76,162.56),(100,55))]:
 add(ref,'12m 1% >=2W','Device:R',SH,xy,bxy,{'1':'CS','2':'PGND'},'Two12mohmparallel create6mohmlow-sidesharedcurrentshunt. 10Arms->0.30Wperresistor; cyclelimitmayreach~20.5Apeak,so25Ahotinductorrequirement. MPNpending.',DS)
for ref,xy,bxy in [('R3',(335.28,175.26),(145,42)),('R4',(375.92,175.26),(145,50))]:
 add(ref,'8m 1% >=2W','Device:R',SH,xy,bxy,{'1':'PREOUT','2':'VOUT'},'Two8mohmparallel create4mohmoutputaverageshunt. Native50mVCC->12.5Anominal;47.5..52.5mVand1%shunttolerance->11.76..13.26A. Notuser-adjustable.',DS)
for ref,net,xy,bxy in [('C1','VIN',(20.32,66.04),(15,35)),('C2','VIN',(50.8,116.84),(15,57)),('C3','VOUT',(345.44,66.04),(165,35)),('C4','VOUT',(383.54,116.84),(165,57))]:
 add(ref,'47uF 200V','Device:C_Polarized',CB,xy,bxy,{'1':net,'2':'PGND'},'Bulkcapacitorrequirement;>=105C. Inputcombinedratedripple>=5Aatoperatingtemperature/frequency;outputESRandripplepending. GenericD12.5P5footprintisprovisional. Exactmanufacturerpartnotselected.',DS)
for i,(net,xy,bxy) in enumerate([('VIN',(60.96,66.04),(25,25)),('VIN',(60.96,91.44),(25,68)),('VOUT',(304.8,66.04),(155,35)),('VOUT',(304.8,91.44),(155,57))],5):
 add('C'+str(i),'1uF 250V X7R','Device:C',CH,xy,bxy,{'1':net,'2':'PGND'},'MurataGRM55DR72E105KW01L fromADI-demolist. DCbiasdecreasescapacitance;layout/RMSreviewpending.',DEMO,'ADI DEMO PART - DC BIAS / RMS REVIEW PENDING')
# Controllerpinmapandbodyfromdatasheetpp2,11,12,36.
add('U1','LTC3779EFE#PBF','PowerPhase:LTC3779EFE','PowerPhase:LTC3779_FE38_31_EP',(274.32,113.03),(80,85),{'1':'BG1','2':'VINOV','3':'V5','4':'PGND','5':'AUX12','6':'NDRV_TIE','7':'DRVCC','8':'V5','9':'SS','10':'VFB','11':'SENSEP','12':'SENSEN','13':'ITH','14':'PGND','15':'V5','16':'SYNC','17':'FREQ','18':'PGOOD','19':'BG2','20':'SWB','21':'TG2','22':'BST2','24':'RUN','26':'IAVGP','28':'IAVGN','30':'OUTSNS','32':'VIN','34':'VIN','36':'BST1','37':'TG1','38':'SWA','39':'PGND'},'150VinputANDoutput4-switchcontroller. FE38(31),0.5mmpitch,4.4x9.7body,EP2.74x4.75pad39PGND. Positions23/25/27/29/31/33/35removed. FixedCV99.6V;nativeCCceilingnotprecisionprogrammable.',DS,'DATASHEET PINOUT VERIFIED; HARDWARE UNVALIDATED',sheet='control')
add('J3','AUX12 / PGND - BEFORE HV','Connector_Generic:Conn_01x02','Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',(30.48,30.48),(15,100),{'1':'AUX12','2':'PGND'},'Externalisolated12Vaux mustbepresentbeforeHV/enableandmaintaineduntilHVremoved. Drawfromsamefloatingsecondary. Loss-of-auxhardwareinterlocknotyetdesigned.',sheet='control')
add('J4','ENABLE 3.3V / SYNC / PGOOD / PGND','Connector_Generic:Conn_01x04','Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical',(370.84,30.48),(145,105),{'1':'ENABLE','2':'SYNC','3':'PGOOD','4':'PGND'},'Floating-secondaryfixtureinterface. Defaultshutdownby100kRUNpulldown. PGOODopen-drainpulledtoV5~5.5V,not3.3Vsafe. SYNCexternalsignal<=V5. NoDAC/programmableCVCCinterface.',DS,sheet='control')
res=[('R5','0','NDRV_TIE','DRVCC','DisableexternalNDRVpassFETbytieNDRVtoDRVCCperdatasheetp11.'),('R6','100k','RUN','PGND','DefaultRUN~0.25Vwith2.5uApullup;below1.1Vshutdown. FixturemustholdENABLElowuntilAUXvalid.'),('R7','100','ENABLE','RUN','Enableinterfaceresistance;3.3Vlogicexternalfixture.'),('R8','100k','SYNC','PGND','KeepunusedPLLINlow;externalsyncsupportedbutnophasesharing.'),('R9','37.4k 1%','FREQ','PGND','Datasheetp22RFREQequationgivesapproximately101.8kHz;measureactualfrequency.'),('R10','10k','V5','PGOOD','PGOODopen-drainpullupto5.5Vrail;indicationonly,notindependentprotection.'),('R11','0','TG1','GA','Prototypegatejumper;gateedge/ringingmustdeterminefinalvalue.'),('R12','0','BG1','GB','Prototypegatejumper;gateedge/ringingmustdeterminefinalvalue.'),('R13','0','BG2','GC','Prototypegatejumper;gateedge/ringingmustdeterminefinalvalue.'),('R14','0','TG2','GD','Prototypegatejumper;gateedge/ringingmustdeterminefinalvalue.'),('R15','100','CS','SENSEP','Cyclecurrentsensepositivefilter;220pFdifferentialcapacitor.'),('R16','100','PGND','SENSEN','Cyclecurrentsensenegativefilter;separateKelvintracesmandatory.'),('R17','100','PREOUT','IAVGP','Averagecurrentpositivefilter;15uAcommon-modebiasat>=4V.'),('R18','150','VOUT','IAVGN','Averagecurrentnegativefilter;10uAbias,150ohmcompensates15uA*100ohmfirstorder.'),('R19','1k','PREOUT','OUTSNS','VOUTSNSmustconnecttodrainofoutputhighsideQ4through1kohm,p12.'),('R20','410k 0.1%','VOUT','FBMID','Feedbackupperleg1;100Vratingminimum;topology1.2*(1+820k/10k)=99.6V.'),('R21','410k 0.1%','FBMID','VFB','Feedbackupperleg2;~49.2Vdrop,~5.9mWnominal.'),('R22','10k 0.1%','VFB','PGND','Feedbacklowerleg;VFB1.2Vtypical±1%. ThisisfixedCV99.6V,not0..100V.'),('R23','499k 0.1%','VIN','OVMID','VINOVupperleg1;two499k+10kdividergives129.024Vnominaltrip.'),('R24','499k 0.1%','OVMID','VINOV','VINOVupperleg2;thresholdtolerancegives118.944..139.104Vtripbeforedividererrors;notpreciseOVP.'),('R25','10k 0.1%','VINOV','PGND','ControllerinputOVLOdividerbottom. IndependentOVPstillmissing.'),('R26','10k','ITH','COMP','Initialvoltageloopcompensation copiedfromADI demo;notvalidatedfornewL,CandCV.' )]
# Screenlayoutslots;keepgroupsonaseparatepagefrompower.
for i,(ref,val,a,b,desc) in enumerate(res):
 col=i%6;row=i//6;xy=(30.48+50.8*col,184.15+20.32*row)
 # Boardpassivesareplacementplanningonly; noRF-looplayoutclaim.
 bxy=(40+12*(i%8),66+5*(i//8))
 fp=RH if ref in ['R20','R21','R23','R24'] else R
 add(ref,val,'Device:R',fp,xy,bxy,{'1':a,'2':b},desc,DS,sheet='control')
caps=[('C9','4.7uF 16V X5R','DRVCC','PGND','Gate-driversupplydecoupling,p11.'),('C10','4.7uF 10V X5R','V5','PGND','V5minimum4.7uFdecoupling,p11.'),('C11','1uF 50V X7R','AUX12','PGND','External12Vinputdecoupling.'),('C12','100nF 50V X7R','SS','PGND','SS5uAcharge:nominal24ms to1.2V. Softstartonly;notuserprogrammable0Vclaim.'),('C13','220nF 16V X7R','BST1','SWA','InputsidebootstrapcapacitorfromADIdemo.'),('C14','220nF 16V X7R','BST2','SWB','OutputsidebootstrapcapacitorfromADIdemo.'),('C15','220pF 100V C0G','SENSEP','SENSEN','Cycle-sensedifferentialfilterfromADIdemo.'),('C16','1uF 250V X7R','IAVGP','IAVGN','Differentialaveragecurrentfilterwithin1..4.7uF recommendationp21. Highcommonmodemakesto-groundratingimportant.'),('C17','10nF 50V X7R','COMP','PGND','Initialseries10k/10nFITHcompensation;retuningrequired.'),('C18','100pF 50V C0G','ITH','PGND','Initialhighfrequencypole;retuningrequired.')]
for i,(ref,val,a,b,desc) in enumerate(caps):
 add(ref,val,'Device:C',CH if ref=='C16' else C,(30.48+50.8*(i%4),88.9+25.4*(i//4)),(40+12*(i%8),92+6*(i//8)),{'1':a,'2':b},desc,DS,sheet='control')
for ref,bst,xy,bxy in [('D1','BST1',(40.64,76.2),(55,35)),('D2','BST2',(116.84,76.2),(105,35))]:
 add(ref,'DFLS1200-7 / 1A 200V','Device:D_Schottky','Diode_SMD:D_PowerDI-123',xy,bxy,{'1':bst,'2':'DRVCC'},'BootstrapSchottkydiodefromADIdemo:1K,2A. Exactmanufacturerfootprintreviewstillrequired.',DEMO,'ADI DEMO PART - MANUFACTURER DATASHEET PENDING',sheet='control')
for i,net in enumerate(['VIN','VOUT','PGND','SWA','SWB','DRVCC','V5','SS','VFB','ITH','CS','IAVGP','IAVGN','RUN','PGOOD','GA','GB','GC','GD'],1):
 xy=(20.32+19.05*((i-1)%10),241.3+20.32*((i-1)//10));bxy=(10+8*(i-1),119)
 c=add('TP'+str(i),net,'Connector:TestPoint',TP,xy,bxy,{'1':net},'Differential/guardedtestpoint;scopegroundcanremovefloatingoutput. Gateprobealwaysgate-to-ownsource. CAD routing complete; no hardware/fabrication qualification; see layout report.',sheet='power');c['hide_value']=True
# Powerflagsrepresentexternalfixtureenergy;nosupplyvaluesinvented.
for i,net in enumerate(['VIN','PGND','AUX12'],1):
 c=add('#FLG'+str(i),'PWR_FLAG','power:PWR_FLAG','',(320.04+20.32*(i-1),157.48),(0,0),{'1':net},'ExternallysuppliednetforERC.',sheet='control');c['in_bom']=False;c['on_board']=False

project={'meta':{'filename':NAME+'.kicad_pro','version':1},'board':{'design_settings':{'rules':{'min_clearance':0.2,'min_track_width':0.18,'min_copper_edge_clearance':1.0,'min_via_diameter':0.5,'min_through_hole_diameter':0.3,'min_via_annular_width':0.1}}},'net_settings':{'classes':[{'name':'Default','clearance':0.25,'track_width':0.3,'via_diameter':0.8,'via_drill':0.4},{'name':'HV','clearance':1.5,'track_width':0.5,'via_diameter':1.0,'via_drill':0.5},{'name':'Power','clearance':1.5,'track_width':5.0,'via_diameter':1.2,'via_drill':0.6},{'name':'PowerReturn','clearance':0.25,'track_width':5.0,'via_diameter':1.0,'via_drill':0.5}],'netclass_patterns':[{'netclass':'Power','pattern':n} for n in ['VIN','VOUT','PREOUT','SWA','SWB']]+[{'netclass':'PowerReturn','pattern':n} for n in ['PGND','CS']]+[{'netclass':'HV','pattern':n} for n in ['GA','GD','BST1','BST2','TG1','TG2','FBMID','OVMID','OUTSNS','IAVGP','IAVGN']],'meta':{'version':4}},'text_variables':{}}
(D/(NAME+'.kicad_pro')).write_text(json.dumps(project,indent=2)+'\n')
libs=sorted({c['lib'].split(':')[0] for c in components});entries=[]
for lib in libs:
 path='${KIPRJMOD}/PowerPhase.kicad_sym' if lib=='PowerPhase' else '${KICAD9_SYMBOL_DIR}/'+lib+'.kicad_sym'
 entries.append(f'(lib(name "{lib}")(type "KiCad")(uri "{path}")(options "")(descr "Projectorinstalledlibrary"))')
(D/'sym-lib-table').write_text('(sym_lib_table(version 7)\n'+'\n'.join(entries)+'\n)\n')
fplibs=sorted({c['footprint'].split(':')[0] for c in components if c['footprint']})
(D/'fp-lib-table').write_text('(fp_lib_table(version 7)\n'+'\n'.join(f'(lib(name "{lib}")(type "KiCad")(uri "'+('${KIPRJMOD}/PowerPhase.pretty' if lib=='PowerPhase' else '${KICAD9_FOOTPRINT_DIR}/'+lib+'.pretty')+'")(options "")(descr "Engineering draft footprints"))' for lib in fplibs)+'\n)\n')
rootid=h.uid();child=h.uid();sh=[dict(name='Controller and sensing',file='control.kicad_sch',xy=(195.58,175.26),size=(76.2,35.56),uuid=child)]
h.write_schematic(D/(NAME+'.kicad_sch'),power,project=NAME,root_uuid=rootid,title='RESEARCH PHASE - FIXED99.6V / 10A TARGET - NOT4kW',comments=['CAD routing complete; see layout report; no hardware/fabrication qualification','External isolatedDC,<=120V;12VauxmustprecedeHV','No0Vregulation;noadjustableCC;no4-phasecurrent-sharing','Allpowercomponentsthermal/integrityreviewpending'],sheets=sh,texts=[dict(xy=(12.7,15.24),text='RESEARCH ONLY: fixed 99.6 V / 10 A target. No 230 V AC on this board.\nDoes NOT implement requested 0..100 V / 40 A laboratory PSU.'),dict(xy=(15.24,195.58),text='6 mOhm low-side cycle shunt; 4 mOhm output average shunt.\nNative CC ceiling ~12.5 A, not precision adjustable.\nExternal 150 uH inductor: warm Isat >=25 A; vendor pending.'),dict(xy=(12.7,225.425),text='Guarded/differential test points. Switch-node and high-side gate signals float.\nPCB CAD routing complete; see exports/power/layout_summary.json.\nHardware performance unvalidated; no Gerbers released.')])
h.write_schematic(D/'control.kicad_sch',control,project=NAME,root_uuid=child,instance_path='/'+rootid+'/'+child,title='LTC3779 CONTROL - FIXED SETPOINT RESEARCH ONLY',comments=['PinoutverifiedagainstLTC3779RevA pp2/11/12','ManufacturerdatasheetsforMOSFETandothercriticalpartsrequired','Loopcompensationinitialonly;notverifiedatnewL/C/VOUT'],texts=[dict(xy=(12.7,15.24),text='LTC3779: VIN/VOUT rated to150 V; native reference1.2 V.\n12V floating auxiliary and external enable interlock required. No programmable CV/CC.'),dict(xy=(12.7,157.48),text='Fixed CV: 1.2*(1+820k/10k)=99.6V nominal, reference tolerance +/-1%.\nVINOV:1.28*(1+998k/10k)=129.0V nominal, broad comparator tolerance; no precise OVP.'),dict(xy=(315,85),text='Physical pins23/25/27/29/31/33/35 absent.\nEP39 must connect PGND.\nV5=5.5V; DRVCC=10V.\nPGOOD pulled to5.5V.\nMODE=V5: pulse skipping.\nAUX failure interlock missing.',size=1.1)])

# Move large controllerreference/valueoutsideitsbody;helperdefaultsfit smallsymbols.
control_doc=h.parse((D/'control.kicad_sch').read_text())
for sym in h.children(control_doc,'symbol'):
 ref=next((p for p in h.children(sym,'property') if p[1]=='Reference'),None)
 if ref is not None and ref[2]=='U1':
  for prop in h.children(sym,'property'):
   if prop[1] in ('Reference','Value'):
    at=h.sub(prop,'at');at[1]=h.Atom('274.32');at[2]=h.Atom('71.12' if prop[1]=='Reference' else '154.94')
(D/'control.kicad_sch').write_text(h.emit(control_doc)+'\n')
# Visiblepowerwiresmakefour-switchtopologyreadable;globalnetsstilllinkcontrollersheet.
power_doc=h.parse((D/(NAME+'.kicad_sch')).read_text())
for sym in h.children(power_doc,'symbol'):
 ref=next((p for p in h.children(sym,'property') if p[1]=='Reference'),None)
 if ref is not None and ref[2] in ('Q1','Q2','Q3','Q4'):
  at=h.sub(sym,'at');x=float(at[1]);y=float(at[2])
  for prop in h.children(sym,'property'):
   if prop[1] in ('Reference','Value'):
    pa=h.sub(prop,'at');pa[1]=h.Atom(str(x));pa[2]=h.Atom(str(y+(-11.43 if prop[1]=='Reference' else 11.43)))
for a,b in [((101.6,66.04),(101.6,111.76)),((101.6,88.9),(186.69,88.9)),((194.31,88.9),(281.94,88.9)),((281.94,66.04),(281.94,111.76)),((101.6,121.92),(101.6,143.51)),((101.6,143.51),(281.94,143.51)),((281.94,143.51),(281.94,121.92)),((137.16,143.51),(137.16,158.75)),((238.76,143.51),(238.76,158.75))]:
 power_doc.append(h.parse(f'(wire(pts(xy {a[0]} {a[1]})(xy {b[0]} {b[1]}))(stroke(width 0)(type default))(uuid {h.uid()}))'))
for x,y in [(101.6,88.9),(281.94,88.9),(137.16,143.51),(238.76,143.51)]:
 power_doc.append(h.parse(f'(junction(at {x} {y})(diameter 0)(color 0 0 0 0)(uuid {h.uid()}))'))
(D/(NAME+'.kicad_sch')).write_text(h.emit(power_doc)+'\n')

def cli(*args):
 subprocess.run([str(WRAP),'kicad-cli',*map(str,args)],cwd=ROOT,check=True)
cli('sch','export','netlist','--format','kicadxml','-o',E/'power_phase.xml',D/(NAME+'.kicad_sch'))
xml=ET.parse(E/'power_phase.xml').getroot();netpins={};want={}
for net in xml.find('nets'):netpins[net.attrib['name']]={(n.attrib['ref'],n.attrib['pin']) for n in net.findall('node')}
for c in components:
 for pin,net in c['nets'].items():
  if c['on_board'] if 'on_board' in c else True:want.setdefault(net,set()).add((c['ref'],pin))
# Netlist containspowerflagpseudo-components;ignorethemforphysicalpins.
actual={n:{p for p in ps if not p[0].startswith('#')} for n,ps in netpins.items()}
assert actual==want,'Schematicdoesnotmatchintendedpinmap'
# Compact functional floorplan: switching stage above, quiet analogue below.
# Rotations refer to PCB footprint geometry, independent of schematic rotation.
placement={
 'J1':(15,18,0),'J2':(127,12,180),'J3':(18,78,0),'J4':(119,75,0),
 'Q1':(49,29,180),'Q2':(54,36,0),'Q3':(77.2,36,180),'Q4':(85,29,0),
 'L1':(60,13,0),'R1':(64,45,270),'R2':(71,45,270),'R3':(95,29,0),'R4':(95,35,0),
 'C1':(38,25,180),'C2':(30,44,180),'C3':(105,30,0),'C4':(115,47,0),
 'C5':(44,14,180),'C6':(39,48,180),'C7':(108,17,0),'C8':(105,54,0),
 'U1':(67,31,0),
 'R5':(59,28,0),'R6':(76,45,0),'R7':(79,53,0),'R8':(53,50,0),
 'R9':(56,50,0),'R10':(59,58,0),
 'R11':(51,23.5,0),'R12':(48.6,38,0),'R13':(87,37,0),'R14':(86,24,0),
 'R15':(58.5,46,0),'R16':(58.5,48,0),'R17':(92,45,0),'R18':(92,57,0),
 'R19':(88,41,0),'R20':(105,66,180),'R21':(97,66,180),'R22':(62,35.5,90),
 'R23':(28,63,0),'R24':(36,63,0),'R25':(58,61,0),'R26':(57,52,0),
 'C9':(62,29.5,270),'C10':(60,34,270),'C11':(62,24.5,270),'C12':(53,46,0),
 'C13':(74,25.5,270),'C14':(73.25,35.3,270),'C15':(61,46.5,90),'C16':(88,52,0),
 'C17':(57,55,0),'C18':(62,55,0),'D1':(68,24,180),'D2':(80,49,0),
 'TP1':(10,53,0),'TP2':(113,60,0),'TP3':(67,61,0),
 'TP4':(52,11,0),'TP5':(83,15,0),'TP6':(46,53,0),'TP7':(45,69,0),
 'TP8':(53,69,0),'TP9':(82,73,0),'TP10':(64,59,0),'TP11':(54,54,0),
 'TP12':(106,73,0),'TP13':(114,73,0),'TP14':(92,78,0),'TP15':(45,75,0),
 'TP16':(46,8,0),'TP17':(49,45,0),'TP18':(80,59,0),'TP19':(90,17,0),
}
board=pcbnew.BOARD();nets={};fps={}
for net in want:
 item=pcbnew.NETINFO_ITEM(board,net);board.Add(item);nets[net]=item
for c in components:
 if not c.get('on_board',True):continue
 lib,part=c['footprint'].split(':');libpath=D/'PowerPhase.pretty' if lib=='PowerPhase' else Path('/usr/share/kicad/footprints')/(lib+'.pretty')
 fp=pcbnew.FootprintLoad(str(libpath),part);assert fp,'Missing footprint '+c['footprint']
 fp.SetAttributes(fp.GetAttributes() & ~pcbnew.FP_EXCLUDE_FROM_BOM);fp.SetFPID(pcbnew.LIB_ID(lib,part));fp.SetReference(c['ref']);fp.SetValue(c['val'])
 x,y,angle=placement[c['ref']];c['board_xy']=(x,y)
 board.Add(fp) # Flip needs a native parent BOARD in KiCad 9.
 fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y)))
 if c['ref']=='C14':fp.Flip(fp.GetPosition(),False)
 fp.SetOrientationDegrees(angle)
 path=pcbnew.KIID_PATH();path.push_back(pcbnew.KIID(rootid))
 if c in control:path.push_back(pcbnew.KIID(child))
 path.push_back(pcbnew.KIID(c['uuid']));fp.SetPath(path)
 for pad in fp.Pads():
  pn=pad.GetNumber()
  if pn:pad.SetNet(nets[c['nets'][pn]])
 fp.Value().SetVisible(False);fp.Reference().SetVisible(False)
 fps[c['ref']]=fp

def point(xy):return pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in xy))
def pad(ref,num):
 p=next(p for p in fps[ref].Pads() if p.GetNumber()==str(num))
 return (pcbnew.ToMM(p.GetPosition().x),pcbnew.ToMM(p.GetPosition().y))
def track(net,pts,width=.3,layer=pcbnew.F_Cu):
 for a,b in zip(pts,pts[1:]):
  if a==b:continue
  t=pcbnew.PCB_TRACK(board);t.SetStart(point(a));t.SetEnd(point(b));t.SetWidth(pcbnew.FromMM(width));t.SetLayer(layer);t.SetNet(nets[net]);board.Add(t)
def via(net,xy,diam=.8,drill=.4):
 v=pcbnew.PCB_VIA(board);v.SetPosition(point(xy));v.SetWidth(pcbnew.F_Cu,pcbnew.FromMM(diam));v.SetDrill(pcbnew.FromMM(drill));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetNet(nets[net]);board.Add(v)
# Source contacts are connected with a short local copper strap. Gate pad4 is
# deliberately excluded; current ratings of solder joints remain to be tested.
for ref in ['Q1','Q2','Q3','Q4']:
 source=next(c for c in components if c['ref']==ref)['nets']['1']
 track(source,[pad(ref,1),pad(ref,2),pad(ref,3)],.65)
# Main copper trunks are 5 mm, 70 um outer-copper engineering assumption.
# Pad entries are tapered by short 1.0/2.0 mm stubs, not claimed as 40 A routes.
# Short terminal necks avoid encroaching on neighbouring drain/gate copper.
track('SWA',[pad('Q1',2),(54.5,29)],.65)
track('SWA',[(54.5,29),(54.675,29),pad('Q2',5)],3.0)
track('SWA',[(54.5,29),(54.5,19),(60,19),pad('L1',1)],3.0)
track('SWB',[pad('Q4',2),(79.5,29)],.65)
track('SWB',[pad('Q3',5),(76.325,29),(79.5,29)],3.0)
track('SWB',[(79.5,29),(79.5,19),(70.16,19),pad('L1',2)],3.0)
track('CS',[pad('Q2',2),(45.5,35.365),(45.5,42)],.65)
track('CS',[pad('Q3',2),(82.5,36.635),(82.5,42)],.65)
track('CS',[(45.5,42),(82.5,42)],3.0)
for ref in ['R1','R2']:track('CS',[(pad(ref,1)[0],42),pad(ref,1)],3.0)
track('PREOUT',[pad('Q4',5),pad('R3',1)],3.0)
track('PREOUT',[pad('R3',1),pad('R4',1)],3.0)
track('VOUT',[pad('R3',2),pad('R4',2)],3.0)
track('VOUT',[pad('R3',2),(100,29),(100,30),pad('C3',1)],3.0)
track('VOUT',[(100,30),(100,5),(127,5),pad('J2',1)],5.0)
track('VOUT',[pad('R4',2),(99,39),(99,47),(111,47)],5.0)
track('VOUT',[(111,47),pad('C4',1)],2.0)
track('VIN',[pad('J1',1),(15,8),(34,8),(34,19)],5.0)
track('VIN',[(34,19),(38,20),pad('C1',1)],2.0)
track('VIN',[pad('C1',1),(43,29),pad('Q1',5)],3.0)
track('VIN',[pad('C1',1),(38,33),(34,36),(30,40),pad('C2',1)],2.0)
# Through-hole bulk/terminal pads connect the broad B.Cu power return directly.
# Six plated vias per shunt are a provisional pad-entry pattern, not a verified
# via ampacity rating. Copper plating/barrel thickness must be specified.
for ref in ['R1','R2']:
 x,y=pad(ref,2);track('PGND',[(x,y),(x,51)],2.0)
 for layer in [pcbnew.F_Cu,pcbnew.B_Cu]:track('PGND',[(x-1,51),(x+1,51),(x+1,52.5),(x-1,52.5),(x-1,51)],1.0,layer)
 for dx in [-1,0,1]:
  for dy in [0,1.5]:via('PGND',(x+dx,51+dy),1.0,.5)
track('PGND',[(64,51),(71,51),(73,55),(73,65),(16,65),(16,46),(21,46)],5.0,pcbnew.B_Cu)
track('PGND',[(21,46),pad('C2',2)],2.0,pcbnew.B_Cu)
track('PGND',[pad('C2',2),(25,25),pad('C1',2)],3.0,pcbnew.B_Cu)
track('PGND',[pad('C1',2),(33,18),pad('J1',2)],3.0,pcbnew.B_Cu)
track('PGND',[(73,65),(128,65),(128,47),(124,47)],5.0,pcbnew.B_Cu)
track('PGND',[(124,47),pad('C4',2)],2.0,pcbnew.B_Cu)
track('PGND',[(124,47),(128,47),(128,21),(116.84,21),pad('J2',2)],3.0,pcbnew.B_Cu)
track('PGND',[pad('C3',2),(116,30),(116,39),(124,39),(124,47),(120,47)],3.0,pcbnew.B_Cu)
# Quiet controller ground returns at the shunt PGND entry; no switch current
# is intentionally carried in these 0.3 mm signal-ground branches.
track('PGND',[pad('U1',39),(67,34.5)],.5)
track('PGND',[pad('U1',4),(65.3,28),pad('U1',39)],.18)
track('PGND',[pad('U1',14),(67,33),pad('U1',39)],.18)
via('PGND',(67,34.5));track('PGND',[(67,34.5),(64,48)],.5,pcbnew.B_Cu)
via('PGND',(64,48));track('PGND',[(64,48),pad('R1',2)],.5)
# DRVCC decoupling at the driver pin. Small component-pad necks are explicit.
track('DRVCC',[pad('U1',7),(63,29.5),pad('C9',1)],.18)
track('PGND',[pad('C9',2),(60.5,30.275)],.3);via('PGND',(60.5,30.275))
track('PGND',[(60.5,30.275),(60.5,34.5),(67,34.5)],.3,pcbnew.B_Cu)
# Bootstrap components retain their own switching-source reference.
track('BST1',[pad('D1',1),(70,24),pad('C13',1)],.3)
via('SWA',(71.4,26.1),.5,.3);via('SWA',pad('C13',2),.5,.3)
track('SWA',[pad('U1',38),(71.4,26.1)],.18)
track('SWA',[(71.4,26.1),(71.4,24.7),(72.5,24.7),pad('C13',2)],.3,pcbnew.B_Cu)
via('SWA',(54.5,29),1,.5)
track('SWA',[(71.4,26.1),(70,26.25),(70,18),(54.5,18),(54.5,29)],.3,pcbnew.B_Cu)
via('BST1',(72.5,28.8));via('BST1',pad('C13',1))
track('BST1',[pad('U1',36),(70.8,27.5),(72.5,28.8)],.18)
track('BST1',[(72.5,28.8),(75.5,29.3),(75.5,24.725),pad('C13',1)],.3,pcbnew.In1_Cu)
# Top gate and bottom gate, each followed by its own source-return reference.
via('TG1',(72.5,27));track('TG1',[pad('U1',37),(72.5,27)],.18)
via('TG1',pad('R11',1))
# Short gate path around existing HV/LV through-vias, replacing the old y=16
# detour. No other gate, source or Kelvin path is reassigned.
track('TG1',[(72.5,27),(72.3,25.6),(70,23.8),(67.3,22),(61,20.1),(58.2,20.1),(57,20.2),pad('R11',1)],.3,pcbnew.In2_Cu)
track('GA',[pad('R11',2),pad('Q1',4)],.3)
via('BG1',(62,26.5));track('BG1',[pad('U1',1),(62,26.5)],.18)
via('BG1',(48.5,39.5));track('BG1',[pad('R12',1),(47.775,39.5),(48.5,39.5)],.3)
track('BG1',[(62,26.5),(49,26.5),(49,33),(48.5,33),(48.5,39.5)],.3,pcbnew.In2_Cu)
track('GB',[pad('R12',2),pad('Q2',4)],.3)
via('SWB',(72.6,36.5));via('SWB',(70.8,36.6))
track('SWB',[pad('C14',2),(72.6,36.5)],.3)
track('SWB',[pad('U1',20),(70.5,35.5),(70.8,36.6)],.18)
track('SWB',[(72.6,36.5),(70.8,36.6)],.3,pcbnew.B_Cu)
via('BST2',(71.35,35.3),.5,.3)
track('BST2',[pad('U1',22),(70.75,34.5),(71.35,35.3)],.18)
track('BST2',[(71.35,35.3),(71.35,32.8),(72.6,32.8),pad('C14',1)],.3,pcbnew.B_Cu)
via('BST2',pad('C14',1),.8,.4);via('BST2',pad('D2',1),.8,.4)
track('BST2',[pad('C14',1),(74.6,33.725),(74.6,46),pad('D2',1)],.3,pcbnew.B_Cu)
track('DRVCC',[pad('C9',1),(60.3,28.725)],.3);via('DRVCC',(60.3,28.725))
via('DRVCC',pad('D1',2));via('DRVCC',pad('D2',2))
track('DRVCC',[(60.3,28.725),(60.3,24),pad('D1',2)],.3,pcbnew.B_Cu)
via('DRVCC',(60.3,24))
track('DRVCC',[pad('D2',2),(87,49),(87,20.5),(60.3,20.5),(60.3,24)],.3,pcbnew.In1_Cu)
# Distinct positive and negative cycle-sense Kelvin paths. Negative pick-up is
# taken at R1 pad2 through a dedicated inner-layer branch, not a remote cap.
track('CS',[pad('R1',1),(61.5,42.0375),(57.675,43),pad('R15',1)],.3)
track('PGND',[pad('R16',1),(56,48)],.3);via('PGND',(56,48))
track('PGND',[(56,48),(64,48)],.3,pcbnew.In2_Cu)
track('SENSEP',[pad('R15',2),(60,46),(60,47.275),pad('C15',1)],.3)
track('SENSEN',[pad('R16',2),(59.325,49.3),(61.9,49.3),(61.9,45.725),pad('C15',2)],.3)
# Average-sense leads branch directly from the output shunt pads. High common
# mode is retained; they do not reference a low-voltage analogue ground.
track('PREOUT',[pad('R3',1),(91.175,35),pad('R17',1)],.3)
via('VOUT',(99,35.2),1,.5);via('VOUT',(89,57),1,.5)
track('VOUT',[(99,35.2),(99,60),(89,60),(89,57)],.5,pcbnew.B_Cu)
track('VOUT',[(89,57),pad('R18',1)],.3)
track('IAVGP',[pad('R17',2),(94.5,45)],.3);via('IAVGP',(94.5,45),1,.5)
via('IAVGP',(84,52),1,.5);track('IAVGP',[(94.5,45),(84,45),(84,52)],.3,pcbnew.In2_Cu)
track('IAVGP',[(84,52),pad('C16',1)],.3)
track('IAVGN',[pad('R18',2),(95,57)],.3);via('IAVGN',(95,57),1,.5)
via('IAVGN',(93,52),1,.5);track('IAVGN',[(95,57),(95,52),(93,52)],.3,pcbnew.B_Cu)
track('IAVGN',[(93,52),pad('C16',2)],.3)
# Three independent short source-pad necks per MOSFET. They sum to 2.4 mm
# nominal outer copper; equal current distribution still needs thermal review.
for ref,exitx in [('Q1',54.5),('Q2',45.5),('Q3',82.5),('Q4',79.5)]:
 net=next(c for c in components if c['ref']==ref)['nets']['1']
 for num in [1,2,3]:
  xy=pad(ref,num);track(net,[xy,(exitx,xy[1])],.8)
 ys=[pad(ref,num)[1] for num in [1,2,3]]
 track(net,[(exitx,min(ys)),(exitx,max(ys))],1.8)
# Wide continuations from the collected low-side source pads to CS trunk.
track('CS',[(45.5,36.635),(45.5,42)],3.0)
track('CS',[(82.5,37.905),(82.5,42)],3.0)
# Local high-frequency capacitors finally join the actual power/return nodes.
track('VIN',[pad('C5',1),(47.5,14),(47.5,29),pad('Q1',5)],1.0)
track('PGND',[pad('C5',2),(39,14)],.5);via('PGND',(39,14),1,.5)
track('PGND',[(39,14),(33,14),pad('C1',2)],.5,pcbnew.B_Cu)
via('VIN',pad('C6',1),1,.5)
track('VIN',[pad('C2',1),(35,44),(35,48),pad('C6',1)],.5,pcbnew.B_Cu)
track('PGND',[pad('C6',2),(35,51)],.5);via('PGND',(35,51),1,.5)
track('PGND',[(35,51),(35,65)],.5,pcbnew.B_Cu)
track('VOUT',[pad('C7',1),(103,17),(100,17)],1.0)
track('PGND',[pad('C7',2),(112.5,17)],.5);via('PGND',(112.5,17),1,.5)
track('PGND',[(112.5,17),(116.84,17),(116.84,21)],.5,pcbnew.B_Cu)
via('VOUT',pad('C8',1),1,.5);track('VOUT',[pad('C8',1),(99,54)],.5,pcbnew.B_Cu)
track('PGND',[pad('C8',2),(111,54)],.5);via('PGND',(111,54),1,.5)
track('PGND',[(111,54),(109,54),(109,65)],.5,pcbnew.B_Cu)
# Cycle-sense filter-to-controller paths on the quiet inner signal layer.
via('SENSEP',(62.65,31.5),.5,.3);via('SENSEN',(63,32.2),.5,.3)
track('SENSEP',[pad('U1',11),(62.65,31.5)],.18)
track('SENSEN',[pad('U1',12),(63,32),(63,32.2)],.18)
via('SENSEP',(59.4,45.5));track('SENSEP',[(59.4,45.5),pad('R15',2)],.3)
via('SENSEN',(61.9,45.725));track('SENSEN',[(61.9,45.725),pad('C15',2)],.3)
track('SENSEP',[(62.65,31.5),(60,32.5),(60,44.5),(59.4,45.5)],.3,pcbnew.In2_Cu)
track('SENSEN',[(63,32.2),(64.5,33),(64.5,44),(64,44),(64,45.725),(61.9,45.725)],.3,pcbnew.In2_Cu)
# Output low-side gate is a separate 10 V signal above the shared CS source.
via('BG2',(63,37.5));track('BG2',[pad('U1',19),(63.2,35.5),(63.2,37.5),(63,37.5)],.18)
via('BG2',(85.5,37));track('BG2',[(85.5,37),pad('R13',1)],.3)
track('BG2',[(63,37.5),(65,39),(85.5,39),(85.5,37)],.3,pcbnew.In1_Cu)
track('GC',[pad('R13',2),(88.8,37),(88.8,33.1),(80.025,33.1),pad('Q3',4)],.3)
# No copper is poured beneath SWA/SWB. No mains or PE is present on this PCB.
for a,b in [((0,0),(135,0)),((135,0),(135,90)),((135,90),(0,90)),((0,90),(0,0))]:
 shape=pcbnew.PCB_SHAPE(board);shape.SetShape(pcbnew.SHAPE_T_SEGMENT);shape.SetStart(point(a));shape.SetEnd(point(b));shape.SetLayer(pcbnew.Edge_Cuts);shape.SetWidth(pcbnew.FromMM(.05));board.Add(shape)
for content,xy,size in [('POWER LAYOUT PROTOTYPE - DO NOT FABRICATE',(67.5,5),1.2),('FIXED 99.6 V / 10 A TARGET; NOT 40 A',(67.5,8),.9),('NO MAINS; FLOATING SECONDARY; EXTERNAL 150 uH',(67.5,87),.9)]:
 t=pcbnew.PCB_TEXT(board);t.SetText(content);t.SetPosition(point(xy));t.SetTextSize(point((size,size)));t.SetTextThickness(pcbnew.FromMM(.15));t.SetLayer(pcbnew.F_SilkS);board.Add(t)
board.GetDesignSettings().SetCopperLayerCount(4)
pcbnew.SaveBoard(str(D/(NAME+'.kicad_pcb')),board)
# Native stackup is a preliminary request, not a fabricator-qualified recipe.
# 70/35/35/70 um copper is explicit so trace-current estimates cannot silently
# rely on KiCad's ordinary 35 um outer-layer defaults. Total nominal 1.60 mm.
stackup=h.parse('(stackup (layer "F.SilkS" (type "Top Silk Screen")) (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01)) (layer "F.Cu" (type "copper") (thickness 0.07)) (layer "dielectric 1" (type "prepreg") (thickness 0.19) (material "FR4 - vendor TBD")) (layer "In1.Cu" (type "copper") (thickness 0.035)) (layer "dielectric 2" (type "core") (thickness 0.99) (material "FR4 - vendor TBD")) (layer "In2.Cu" (type "copper") (thickness 0.035)) (layer "dielectric 3" (type "prepreg") (thickness 0.19) (material "FR4 - vendor TBD")) (layer "B.Cu" (type "copper") (thickness 0.07)) (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01)) (layer "B.SilkS" (type "Bottom Silk Screen")))')
pcb_text=(D/(NAME+'.kicad_pcb')).read_text()
assert '(setup\n' in pcb_text
(D/(NAME+'.kicad_pcb')).write_text(pcb_text.replace('(setup\n','(setup\n'+h.emit(stackup)+'\n',1))
# Retain KiCad's complete native severity map and each class default. A sparse
# design_settings dictionary can silently suppress clearance DRC providers.
native=json.loads((D/(NAME+'.kicad_pro')).read_text())
native.setdefault('board',{}).setdefault('design_settings',{}).setdefault('rules',{}).update(project['board']['design_settings']['rules'])
default_class=native['net_settings']['classes'][0].copy()
native['net_settings']['classes']=[]
for desired in project['net_settings']['classes']:
 merged=default_class.copy();merged.update(desired);merged['priority']=2147483647 if desired['name']=='Default' else (0 if desired['name']=='Power' else 1)
 native['net_settings']['classes'].append(merged)
native['net_settings']['netclass_patterns']=project['net_settings']['netclass_patterns'];native['net_settings']['meta']={'version':4}
(D/(NAME+'.kicad_pro')).write_text(json.dumps(native,indent=2)+'\n')
# Functional secondary-circuit spacing. These are NOT mains isolation ratings.
rules=['(version 1)',
 '(rule "Default geometric minima" (constraint clearance (min 0.25mm)) (constraint track_width (min 0.18mm)) (constraint edge_clearance (min 1.0mm)))',
 '(rule "HV and power functional spacing" (condition "A.NetClass == \'HV\' || B.NetClass == \'HV\' || A.NetClass == \'Power\' || B.NetClass == \'Power\'") (constraint clearance (min 1.5mm)))',
 '(rule "U1 FE38 high-voltage package-local pad gap" (condition "A.intersectsCourtyard(\'U1\') && B.intersectsCourtyard(\'U1\')") (constraint clearance (min 0.7mm)))']
# Only these neighbouring U1 nets have <=12 V differential in intended operation.
low_pairs=[('BG1','VINOV'),('VINOV','V5'),('V5','PGND'),('PGND','AUX12'),('AUX12','NDRV_TIE'),('NDRV_TIE','DRVCC'),('DRVCC','V5'),('V5','SS'),('SS','VFB'),('VFB','SENSEP'),('SENSEP','SENSEN'),('SENSEN','ITH'),('ITH','PGND'),('V5','SYNC'),('SYNC','FREQ'),('FREQ','PGOOD'),('PGOOD','BG2'),('SWB','TG2'),('TG2','BST2'),('SWA','TG1'),('TG1','BST1')]
for a,b in low_pairs:
 cond=f"A.intersectsCourtyard('U1') && B.intersectsCourtyard('U1') && ((A.NetName == '{a}' && B.NetName == '{b}') || (A.NetName == '{b}' && B.NetName == '{a}'))"
 rules.append(f'(rule "U1 low-differential pair {a}-{b}" (condition "{cond}") (constraint clearance (min 0.2mm)))')
for ref in ['Q1','Q2','Q3','Q4']:
 rules.append(f'(rule "{ref} verified TDSON local geometry" (condition "A.intersectsCourtyard(\'{ref}\') && B.intersectsCourtyard(\'{ref}\')") (constraint clearance (min 0.5mm)))')
for a,b in [('SWA','GA'),('SWA','TG1'),('SWA','BST1'),('GA','TG1'),('TG1','BST1'),('SWB','GD'),('SWB','TG2'),('SWB','BST2'),('GD','TG2'),('TG2','BST2'),('PREOUT','VOUT'),('IAVGP','IAVGN')]:
 cond=f"((A.NetName == '{a}' && B.NetName == '{b}') || (A.NetName == '{b}' && B.NetName == '{a}'))"
 rules.append(f'(rule "Low differential floating pair {a}-{b}" (condition "{cond}") (constraint clearance (min 0.5mm)))')
for ref in ['R20','R21','R23','R24']:
 rules.append(f'(rule "{ref} 1206 divider terminal geometry" (condition "A.intersectsCourtyard(\'{ref}\') && B.intersectsCourtyard(\'{ref}\')") (constraint clearance (min 1.5mm)))')
for ref in ['C13','C14','D1','D2','C16','R17','R18','R19','R11','R14']:
 rules.append(f'(rule "{ref} low differential at high common mode" (condition "A.intersectsCourtyard(\'{ref}\') && B.intersectsCourtyard(\'{ref}\')") (constraint clearance (min 0.5mm)))')
for a,b in low_pairs:
 cond=f"A.Type == 'Pad' && B.Type == 'Pad' && A.intersectsCourtyard('U1') && B.intersectsCourtyard('U1') && ((A.NetName == '{a}' && B.NetName == '{b}') || (A.NetName == '{b}' && B.NetName == '{a}'))"
 rules.append(f'(rule "U1 pad-only low differential {a}-{b}" (condition "{cond}") (constraint clearance (min 0.2mm)))')
low_nets=['BG1','BG2','VINOV','V5','PGND','AUX12','NDRV_TIE','DRVCC','SS','VFB','SENSEP','SENSEN','ITH','SYNC','FREQ','PGOOD','RUN']
low_test=lambda side:'('+ ' || '.join(f"{side}.NetName == '{n}'" for n in low_nets)+')'
cond="A.intersectsCourtyard('U1') && B.intersectsCourtyard('U1') && "+low_test('A')+' && '+low_test('B')
rules.append(f'(rule "U1 <=12 V local low-voltage fanout" (condition "{cond}") (constraint clearance (min 0.2mm)))')
# Apply the package-local low-differential rule last so neighbouring component
# courtyards cannot accidentally strengthen or weaken the U1 pin-pair rule.
for a,b in low_pairs:
 cond=f"A.intersectsCourtyard('U1') && B.intersectsCourtyard('U1') && ((A.NetName == '{a}' && B.NetName == '{b}') || (A.NetName == '{b}' && B.NetName == '{a}'))"
 rules.append(f'(rule "U1 final local pair {a}-{b}" (condition "{cond}") (constraint clearance (min 0.2mm)))')
(D/(NAME+'.kicad_dru')).write_text('\n'.join(rules)+'\n')
# Complete the original hand-planned power placement with the reviewed native
# copper snapshot. Regeneration must never silently regress to a partial PCB.
# The plan asserts every physical pad/net pair before replacing copper objects.
subprocess.run([str(WRAP),'/usr/bin/python3',str(ROOT/'scripts/power_signal_route.py'),'--replay'],cwd=ROOT,check=True)
board=pcbnew.LoadBoard(str(D/(NAME+'.kicad_pcb')))
fps={f.GetReference():f for f in board.GetFootprints()}
padmap={}
for fp in board.GetFootprints():
 for p in fp.Pads():
  if p.GetNumber():padmap.setdefault(p.GetNetname(),set()).add((fp.GetReference(),p.GetNumber()))
assert padmap==want,'PCBpinmapdiffersfromschematic'
(E/'pin_net_agreement.json').write_text(json.dumps({'status':'PASS','components':len([c for c in components if c.get('on_board',True)]),'pins':sum(map(len,want.values())),'nets':len(want),'controller_connected_pins':len(next(c for c in components if c['ref']=='U1')['nets']),'controller_removed_positions':[23,25,27,29,31,33,35],'board_tracks':len(board.GetTracks()),'scope':'Logical pin agreement only; power layout prototype is not hardware validated'},indent=2)+'\n')
with (ROOT/'bom/power-phase.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['Reference','Value','Footprint','Quantity','Description','Source','Release_status'])
 for c in components:
  if c.get('in_bom',True):w.writerow([c['ref'],c['val'],c['footprint'],1,c['description'],c['datasheet'],c['release']+'; PCB CAD ROUTING COMPLETE - no hardware/fabrication qualification'])
cli('sch','export','pdf','-o',E/'power_phase.pdf',D/(NAME+'.kicad_sch'))
cli('sch','export','svg','-o',E/'schematic_svg',D/(NAME+'.kicad_sch'))
cli('sch','erc','--severity-all','--format','json','-o',E/'erc.json',D/(NAME+'.kicad_sch'))
drc_result=subprocess.run([str(WRAP),'kicad-cli','pcb','drc','--severity-all','--schematic-parity','--exit-code-violations','--format','json','-o',str(E/'drc_unrouted.json'),str(D/(NAME+'.kicad_pcb'))],cwd=ROOT)
assert drc_result.returncode in (0,5),f'DRC tool failure: {drc_result.returncode}'
# Compatibility filename remains for older manual links; content is current.
(E/'drc.json').write_bytes((E/'drc_unrouted.json').read_bytes())
report=json.loads((E/'drc.json').read_text());erc=json.loads((E/'erc.json').read_text())
from collections import Counter
remaining=[]
for item in report['unconnected_items']:
 names=[node['description'] for node in item['items']]
 remaining.append({'description':item['description'],'items':names,'positions_mm':[node['pos'] for node in item['items']]})
(E/'remaining_connections.json').write_text(json.dumps(remaining,indent=2)+'\n')
with (E/'placement.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['Reference','X_mm','Y_mm','Rotation_deg','Side','Footprint','Layout_status'])
 for c in components:
  if c.get('on_board',True):w.writerow([c['ref'],*placement[c['ref']],'B.Cu' if c['ref']=='C14' else 'F.Cu',c['footprint'],'CAD ROUTING COMPLETE - no hardware/fabrication qualification'])
summary={'status':'CAD ROUTING COMPLETE - DRC PASS; HARDWARE UNVALIDATED' if drc_result.returncode==0 else 'CAD DRC FAIL - SEE DETAILS','hardware_validated':False,'fabrication_released':False,'board_size_mm':[135,90],'copper_layers':4,'copper_thickness_um':[70,35,35,70],'track_segments':sum(type(t)==pcbnew.PCB_TRACK for t in board.GetTracks()),'vias':sum(type(t)==pcbnew.PCB_VIA for t in board.GetTracks()),'track_objects':len(board.GetTracks()),'components':len(fps),'erc_violations':len(erc.get('violations',[])),'drc_geometry_violations':len(report['violations']),'drc_geometry_types':dict(Counter(v['type'] for v in report['violations'])),'unconnected_items':len(report['unconnected_items']),'schematic_parity_issues':len(report['schematic_parity']),'drc_exit_code':drc_result.returncode,'unconnected_detail':'remaining_connections.json','note':'CAD connectivity/geometry checks do not qualify switching, current, thermal or isolation performance.'}
(E/'layout_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
if (E/'summary.json').exists() and not (E/'summary_pre_layout.json').exists():(E/'summary_pre_layout.json').write_bytes((E/'summary.json').read_bytes())
(E/'summary.json').write_bytes((E/'layout_summary.json').read_bytes())
print(json.dumps(summary,indent=2))
cli('pcb','export','svg','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','--layers','F.Cu,F.SilkS,Edge.Cuts','-o',E/'pcb_placement.svg',D/(NAME+'.kicad_pcb'))
print('Generated fixed-CV research prototype with deterministic complete CAD routing. DRC status is explicit in layout_summary.json. No fabrication files.')

cli('pcb','export','svg','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','--layers','B.Cu,B.SilkS,Edge.Cuts','-o',E/'pcb_back.svg',D/(NAME+'.kicad_pcb'))
cli('pcb','export','pdf','--mode-separate','--layers','F.Cu,In1.Cu,In2.Cu,B.Cu','--common-layers','Edge.Cuts','-o',E/'pcb_layers',D/(NAME+'.kicad_pcb'))
subprocess.run(['pdfunite',*[str(E/'pcb_layers'/f'power_phase-{layer}.pdf') for layer in ['F_Cu','In1_Cu','In2_Cu','B_Cu']],str(E/'pcb_layers.pdf')],check=True)
cli('pcb','export','pdf','--mode-single','--layers','F.Fab,Edge.Cuts','--sketch-pads-on-fab-layers','-o',E/'pcb_assembly.pdf',D/(NAME+'.kicad_pcb'))
cli('pcb','export','pdf','--mode-single','--layers','B.Fab,Edge.Cuts','--sketch-pads-on-fab-layers','-o',E/'pcb_assembly_back.pdf',D/(NAME+'.kicad_pcb'))

cli('pcb','export','svg','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','--black-and-white','--layers','F.Cu,F.Fab,Edge.Cuts','-o',E/'pcb_assembly.svg',D/(NAME+'.kicad_pcb'))

for svg,png in [("pcb_placement.svg","pcb_front_preview.png"),("pcb_back.svg","pcb_back_preview.png")]:
 subprocess.run([str(WRAP),"inkscape",str(E/svg),"--export-type=png","--export-filename="+str(E/png),"--export-width=1600"],check=True)
if drc_result.returncode or erc.get('violations'):
 raise SystemExit(5) # Complete CAD generation must not report success on ERC/DRC findings.
