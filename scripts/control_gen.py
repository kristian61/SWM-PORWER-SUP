#!/usr/bin/python3
"""Experimental analogCV/CC card, positive-only VFB injection, sink-only ITH.
Keeps design/power unchanged. Creates unrouted researchplacement; noGerbers.
Run fromrepository with /usr/bin/python3.
"""
from pathlib import Path
from copy import deepcopy
import os,json,csv,subprocess,xml.etree.ElementTree as ET,collections,datetime
ROOT=Path(__file__).resolve().parents[1]
for k,rel in [('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache'),('XDG_DATA_HOME','data')]:os.environ.setdefault(k,'/workspace/scratch/kicad-psu-runtime/'+rel)
import pcbnew
import kicad_helpers as h
D=ROOT/'design/control';E=ROOT/'exports/control';D.mkdir(parents=True,exist_ok=True);E.mkdir(parents=True,exist_ok=True)
NAME='control';LIB='PSUControl';components=[];analog=[];fault=[]
urls={p:'https://www.ti.com/lit/ds/symlink/'+f+'.pdf' for p,f in [('OPA4192','opa192'),('INA240A2D','ina240'),('TLV1704','tlv1704'),('TPS3808G50','tps3808'),('TPS3700','tps3700'),('LM4040','lm4040-n')]}
DS='https://www.analog.com/media/en/technical-documentation/data-sheets/ltc3779.pdf';DEMO='https://www.analog.com/media/en/technical-documentation/user-guides/DC2456AF.PDF'
# Derive same-pin graphicalsymbols, retainingmanufacturer-verifiedphysicalpinmaps.
libitems=[]
def derivative(name,base,pinfix=None):
 o=deepcopy(h.resolved(base));old=o[1];o[1]=name
 for su in h.children(o,'symbol'):
  su[1]=name+su[1][len(old):]
  for p in h.children(su,'pin'):
   if pinfix and h.sub(p,'number')[1] in pinfix:p[1]=h.Atom(pinfix[h.sub(p,'number')[1]])
 for p in h.children(o,'property'):
  if p[1]=='Value':p[2]=name
  if name=='OPA4192':
   if p[1]=='Datasheet':p[2]=urls['OPA4192']
   if p[1]=='Description':p[2]='OPA4192 precision quad operational amplifier; TI OPA192 family datasheet'
   if p[1]=='ki_fp_filters':p[2]='TSSOP*4.4x5mm*P0.65mm*'
  if name=='TLV1704':
   if p[1]=='Datasheet':p[2]=urls['TLV1704']
   if p[1]=='Description':p[2]='TLV1704 quad open-collector comparator; see TI datasheet'
   if p[1]=='ki_fp_filters':p[2]='TSSOP*4.4x5mm*P0.65mm*'
 libitems.append(h.emit(o))
derivative('OPA4192','Amplifier_Operational:LM324')
derivative('TLV1704','Comparator:LM339')
derivative('TPS3808G50','Power_Supervisor:TPS3808DBV',{'1':'open_collector'})
def box_symbol(name, pinspec, halfheight):
 s=[f'(symbol "{name}" (pin_names (offset 1.27)) (in_bom yes) (on_board yes)',
    '(property "Reference" "U" (at 0 12.7 0) (effects (font (size 1.27 1.27))))',
    f'(property "Value" "{name}" (at 0 -12.7 0) (effects (font (size 1.27 1.27))))',
    f'(symbol "{name}_0_1" (rectangle (start -6.35 {halfheight}) (end 6.35 {-halfheight}) (stroke (width 0.254) (type default)) (fill (type background))))',
    f'(symbol "{name}_1_1"']
 for no,nm,tp,x,y,a in pinspec:
  s.append(f'(pin {tp} line (at {x} {y} {a}) (length 3.81) (name "{nm}" (effects (font (size 1 1)))) (number "{no}" (effects (font (size 1 1)))))')
 libitems.append('\n'.join(s)+'))')
# Spacious graphics; physical SOIC pin numbering stays manufacturer verified.
box_symbol('INA240A2_SOIC', [('8','IN+','input',-10.16,7.62,0),('1','IN-','input',-10.16,2.54,0),
 ('3','REF2','input',-10.16,-2.54,0),('7','REF1','input',-10.16,-7.62,0),
 ('6','VS','power_in',10.16,7.62,180),('5','OUT','output',10.16,2.54,180),
 ('4','NC','passive',10.16,-2.54,180),('2','GND','power_in',10.16,-7.62,180)],10.16)
box_symbol('LM4040A25', [('1','K','passive',10.16,0,180),
 ('2','A','passive',-10.16,2.54,0),('3','NC / A','passive',-10.16,-2.54,0)],6.35)
# TPS3700 SOT-6 exactDDC pinmap; source datasheetp4.
s=['(symbol "TPS3700DDC" (pin_names(offset1.27))(in_bom yes)(on_board yes)','(property "Reference" "U" (at0 8 0)(effects(font(size1.27 1.27))))','(property "Value" "TPS3700DDC" (at0 -8 0)(effects(font(size1.27 1.27))))','(symbol "TPS3700DDC_0_1"(rectangle(start -5.08 6.35)(end5.08 -6.35)(stroke(width0.254)(type default))(fill(type background))))','(symbol "TPS3700DDC_1_1"']
for no,nm,tp,x,y,a in [('3','INA+','input',-8.89,3.81,0),('4','INB-','input',-8.89,0,0),('5','VDD','power_in',-8.89,-3.81,0),('1','OUTA','open_collector',8.89,3.81,180),('6','OUTB','open_collector',8.89,0,180),('2','GND','power_in',8.89,-3.81,180)]:
 s.append(f'(pin {tp} line(at {x} {y} {a})(length3.81)(name "{nm}"(effects(font(size1 1))))(number "{no}"(effects(font(size1 1)))))')
libitems.append('\n'.join(s)+'))')
# Only insertspacesbetween keyword/numericparameters; compactsyntaxstillKiCad-safe.
libtext='(kicad_symbol_lib(version20241209)(generator "control_gen")\n'+'\n'.join(libitems)+'\n)\n'
import re
libtext=re.sub(r'\((offset|at|size|width|start|end|length|version)(?=[0-9-])',r'(\1 ',libtext)
(D/(LIB+'.kicad_sym')).write_text(libtext)
orig=h.library
h.library=lambda name:h.parse((D/(LIB+'.kicad_sym')).read_text()) if name==LIB else orig(name)
R='Resistor_SMD:R_0603_1608Metric';RH='Resistor_SMD:R_1206_3216Metric';C='Capacitor_SMD:C_0603_1608Metric';TP='TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm';FP14='Package_SO:TSSOP-14_4.4x5mm_P0.65mm';SOT6='Package_TO_SOT_SMD:SOT-23-6';SO8='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm'
rows={'analog':0,'fault':0};idx=0

def add(ref,val,lib,fp,nets,desc,source='',sheet='analog',xy=None,unit=1,bxy=None,in_bom=True,on_board=True):
 global idx
 if xy is None:
  i=rows[sheet];rows[sheet]+=1;xy=(25.4+55.88*(i%6),157.48+24.13*(i//6))
 if bxy is None:
  bxy=(10+10*(idx%12),70+6*(idx//12));idx+=1
 c=dict(ref=ref,val=val,lib=lib,footprint=fp,nets=nets,description=desc,datasheet=source,xy=xy,board_xy=bxy,unit=unit,uuid=h.uid(),in_bom=in_bom,on_board=on_board,hide_value=ref.startswith('TP'))
 components.append(c);(analog if sheet=='analog' else fault).append(c);return c

def resistor(ref,val,a,b,desc,sheet='analog',fp=R,xy=None,bxy=None):return add(ref,val,'Device:R',fp,{'1':a,'2':b},desc,DS,sheet,xy=xy,bxy=bxy)
def capacitor(ref,val,a,b,desc,sheet='analog',xy=None,bxy=None):return add(ref,val,'Device:C',C,{'1':a,'2':b},desc,'',sheet,xy=xy,bxy=bxy)
add('J1','FLOATING +5V AUX / PGND','Connector_Generic:Conn_01x02','Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',{'1':'AUX5','2':'PGND'},'External regulatedisolated5V,samefloatingsecondaryasphase;4.75..5.25Vrequirement. Noonboardregulator.',xy=(25.4,27.94),bxy=(10,15))
add('J2','VCMD / ISET / PGND','Connector_Generic:Conn_01x03','Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical',{'1':'VCMD','2':'ISET','3':'PGND'},'External lowimpedanceanalogsetpoints: VCMD0..1.2V(highVoutto lowVout);ISET0.1..0.6Vnominal0..10A;lowISETcausesshutdownbelow~0.212A. Notfirmware.',xy=(111.76,27.94),bxy=(30,15))
add('J3','VFB / ITH / ENABLE / PGND','Connector_Generic:Conn_01x04','Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical',{'1':'VFB','2':'ITH','3':'ENABLE','4':'PGND'},'Connectonlytofutureprogrammablephasevariant. Originalpowerphaseunchanged. VFBviaR7,currentceilingnativepreserved;ENABLEonlythiscard,nootherdriver.',xy=(218.44,27.94),bxy=(60,15))
add('J4','SHUNT KELVIN + / - / PGND','Connector_Generic:Conn_01x03','Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical',{'1':'KS_HIGH','2':'KS_LOW','3':'PGND'},'External1mohmoutputreturnshunt;IN+highKelvinloadreturn,IN-lowKelvinatphasePGND. No10Aflowsinthisconnector.',xy=(325.12,27.94),bxy=(90,15))
add('J5','VOUT SENSE / PGND - HV','Connector_Generic:Conn_01x02','TerminalBlock_RND:TerminalBlock_RND_205-00241_1x02_P10.16mm_Horizontal',{'1':'VOUT_SENSE','2':'PGND'},'0..120Vpositiveoutputmonitoronly;notloadcurrent. ActualconnectorvoltageMPNreviewpending. HVareaseparatefromlogic.',sheet='fault',xy=(350.52,25.4),bxy=(155,15))
add('JP1','ARM - DEFAULT OPEN','Connector_Generic:Conn_01x02','Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',{'1':'AUX5','2':'ARM_FEED'},'Physicaljumper/manualswitch:opencircuitdefaultshutdown. ClosedprovidesonlyENABLEpullupthrough10k. Notalatchingfaultreset.',sheet='fault',xy=(25.4,25.4),bxy=(110,15))
# OPA4192 quadpinmap independentlyverifiedagainstTI datasheetp4.
ampunits=[(1,{'1':'CV_DRIVE','2':'CV_NEG','3':'CV_POS'},(45.72,76.2),'Positive-onlyCVservo:INJ_NODE=VFB+VCMDwhenenabledanddiodeforward.'),(2,{'7':'CC_OUT','6':'CC_NEG','5':'ISET'},(132.08,76.2),'External CCerroramp;onlysinksITHthroughdiode/R470,PIstartingvaluesunverified.'),(3,{'8':'IREF','9':'IREF','10':'IREF_RAW'},(218.44,76.2),'Buffers0.1Vsensorreference;offsetpermitspositive/negativezerocurrenterrorwithoutoutputgroundclipping.'),(4,{'14':'VDIFF','13':'DIFF_NEG','12':'DIFF_POS'},(311.15,76.2),'TracksINJ_NODE−VFB−VCMD+1.25V;detectsinjectionbranchmismatchafter~±0.1V.'),(5,{'4':'AUX5','11':'PGND'},(365.76,76.2),'Supply4.5Vminimum;supervisorrequired.')]
for unit,pins,xy,desc in ampunits:add('U1','OPA4192IPW',LIB+':OPA4192',FP14,pins,desc,urls['OPA4192'],xy=xy,unit=unit,bxy=(25,40))
add('U2','INA240A2D',LIB+':INA240A2_SOIC',SO8,{'1':'INM','2':'PGND','3':'IREF','4':'PGND','5':'IMON','6':'AUX5','7':'IREF','8':'INP'},'SOICpinmap! Gain50,external1mohm:I_MON=0.1+0.05*I;max±25uVoffset=>±25mA beforeothererrors. Commonmode−4..80V;not100Vhighside.',urls['INA240A2D'],xy=(60.96,116.84),bxy=(50,40))
add('U3','LM4040AIM3-2.5/NOPB',LIB+':LM4040A25','Package_TO_SOT_SMD:SOT-23',{'1':'REF25','2':'PGND','3':'PGND'},'2.5Vshuntreference,Agrade0.1%at25C;minimum up to65uA over temperature. Rbias2.49kfrom5V;divider load about0.694mA, remaining about0.310mA at5V. Pin3 grounded to anode as allowed by TI datasheet p3.',urls['LM4040'],xy=(156.21,116.84),bxy=(75,40))
add('U4','TPS3808G50DBVR',LIB+':TPS3808G50',SOT6,{'1':'ENABLE','2':'PGND','3':'AUX5','4':'DELAY','5':'AUX5','6':'AUX5'},'5Vrailsupervisor,nominal4.65Vthreshold,ODRESETwiredtoENABLE. 10nFdelay~57.6ms. RESETtypecorrectedtoODfromgenericKiCadlibrary.',urls['TPS3808G50'],sheet='fault',xy=(111.76,71.12),bxy=(85,40))
add('U5','TPS3700DDCR',LIB+':TPS3700DDC',SOT6,{'1':'ENABLE','2':'PGND','3':'REF_UV','4':'REF_OV','5':'AUX5','6':'ENABLE'},'Independent400mVfactoryreferencewatchdogforREF25;UVnominal2.396Vrelease/~2.363Vassert,OV2.64Vassert/~2.6037Vrelease.',urls['TPS3700'],sheet='fault',xy=(218.44,71.12),bxy=(110,40))
# TLV1704 physicalpinmap matchesLM339; units3/4oflibrary mapphysicalchannels4/3.
for ref,functions,bxy in [('U6',[('VCMD_HI','REF_CMD_HI','VCMD'),('INJ_HI','REF25','INJ_NODE'),('ISET_LO','ISET','REF_I_LO'),('ISET_HI','REF_I_HI','ISET')],(25,55)),('U7',[('IMON_LO','IMON','REF_IMON_LO'),('DIFF_LO','VDIFF','REF_DIFF_LO'),('DIFF_HI','REF_DIFF_HI','VDIFF'),('VOUT_OVP','REF25','VMON')],(55,55))]:
 pinseq=[('5','4','2'),('7','6','1'),('11','10','13'),('9','8','14')]
 for i,((role,p,m),(pp,pm,po)) in enumerate(zip(functions,pinseq),1):
  add(ref,'TLV1704IPW',LIB+':TLV1704',FP14,{pp:p,pm:m,po:'ENABLE'},role+':lowcollectoronfault;wiredalloutputs onlybecauseOD. Noindependentlatchingfault.',urls['TLV1704'],sheet='fault',xy=(40.64+83.82*(i-1),111.76 if ref=='U6' else 137.16),unit=i,bxy=bxy)
 add(ref,'TLV1704IPW',LIB+':TLV1704',FP14,{'3':'AUX5','12':'PGND'},'Supplyforquadcomparator.',urls['TLV1704'],sheet='fault',xy=(370.84,73.66 if ref=='U6' else 101.6),unit=5,bxy=bxy)
# Diodes fromactualADI demo BOM;ownVF/leakagemanufacturerdatasheetstillpending.
for ref,cat,an,xy,bxy in [('D1','INJ_NODE','CV_DRIVE',(228.6,116.84),(30,60)),('D2','CC_OUT','ITH_LIM',(311.15,116.84),(50,60))]:
 add(ref,'DFLS1200-7 - VF REVIEW PENDING','Device:D_Schottky','Diode_SMD:D_PowerDI-123',{'1':cat,'2':an},'1K2A PowerDI123;200V1AADI-referencepart. D1blockssinkingCVbranch;D2onlyallowsITHsink. ManufacturerVF/leakageandrecoveryrequiredbeforeenergizedtests.',DEMO,xy=xy,bxy=bxy)
ra=[('R1','1M 0.1%','VFB','CV_POS','CV+averaginginput1.'),('R2','1M 0.1%','VCMD','CV_POS','CV+averaginginput2.'),('R3','1M 0.1%','INJ_NODE','CV_NEG','CV-dividerfeedbackhigh.'),('R4','1M 0.1%','CV_NEG','PGND','CV-dividerfeedbacklow. 1Mlimitsrailoffloadingbutdoesnoteliminateit.'),('R5','100k','REF25','VCMD','MissingVCMDpullsup2.5V=>high-commandfault. Externalcommandsourcelowimpedance.'),('R6','100k','ISET','PGND','Missingcurrentsetpointpulldown0=>hardwareoff.'),('R7','10k 0.1%','INJ_NODE','VFB','Positive-currentinjectionbranch;currentonlysourcewhileD1intact. Keeporiginal820k/10kphasefeedback.'),('R8','20k','IMON','CC_NEG','Currenterrorinput;PIstartingnetworknotvalidated.'),('R9','10k','CC_OUT','CC_COMP','PIserieszeroresistor,startingvalueonly.'),('R10','470','ITH','ITH_LIM','LimitsITHclampcurrent;clampauthoritydependsunpublishedITHsourcecurrentanddiodeVF.'),('R11','240k 0.1%','REF25','IREF_RAW','Sensorreferenceupperleg2.5V/25.'),('R12','10k 0.1%','IREF_RAW','PGND','Sensorreferencebottomleg=>0.1Vnominal.'),('R13','2.49k 1%','AUX5','REF25','Shuntreferencebias;approx1mAtotalat5V.'),('R14','10k 0.1%','REF25','VMID','1.25Vmidpointupperdivider;high-Zdiffnetworkloadcausesadditionalerror.'),('R15','10k 0.1%','VMID','PGND','Midpointbottomdivider.'),('R16','1M 0.1%','INJ_NODE','DIFF_POS','Mismatch+weightedinput1.'),('R17','1M 0.1%','VMID','DIFF_POS','Mismatch+weightedinput2.'),('R18','1M 0.1%','PGND','DIFF_POS','Mismatch+weightedinput3.'),('R19','1M 0.1%','VFB','DIFF_NEG','Mismatch−suminput1.'),('R20','1M 0.1%','VCMD','DIFF_NEG','Mismatch−suminput2.'),('R21','1M 0.1%','VDIFF','DIFF_NEG','Mismatchfeedback;VDIFF=INJ−VFB−VCMD+VMID.'),('R22','0','KS_HIGH','INP','DirectKelvinsensorinput;noinputfilterbydefaultperINA240datasheetrecommendation.'),('R23','0','KS_LOW','INM','DirectKelvinsensornegativeinput;no10Ainthisboard.')]
for ref,val,a,b,desc in ra:resistor(ref,val,a,b,desc)
rf=[('R24','10k','ARM_FEED','ENABLE','Onlysourceofenable;manualARMclosedandallfaultsreleasedrequired.'),('R25','10k','ENABLE','PGND','Strongdefaultshutdown;inparallelwithphase100k gives~25mVat2.5uAwhenunpowered.'),('R26','10.3k 0.1%','REF25','REF_CMD_HI','VCMDupperwindowleg.'),('R27','10k 0.1%','REF_CMD_HI','PGND','Uppercommandlimit1.2315Vnominal.'),('R28','216k 0.1%','REF25','REF_I_LO','ISETlowthresholdupperleg.'),('R29','10k 0.1%','REF_I_LO','PGND','ISETlowthreshold0.110619V=>~0.2124Aactivefloor;0commandshutdown.'),('R30','30k 0.1%','REF25','REF_I_HI','ISETupperthresholdleg.'),('R31','10k 0.1%','REF_I_HI','PGND','UpperISET0.625V=>10.5Anominal,setpointvalidityonly.'),('R32','324k 0.1%','REF25','REF_IMON_LO','IMON low plausibility threshold upper leg.'),('R33','10k 0.1%','REF_IMON_LO','PGND','IMON lower limit0.07485 V; normal zero-current bias0.1 V passes. Not full sense-open detection.'),('R34','11.8k 0.1%','REF25','REF_DIFF_LO','VDIFFlowthresholdupperleg.'),('R35','10k 0.1%','REF_DIFF_LO','PGND','VDIFFlowerlimit1.14679Vnominal.'),('R36','8.45k 0.1%','REF25','REF_DIFF_HI','VDIFFhighthresholdupperleg.'),('R37','10k 0.1%','REF_DIFF_HI','PGND','VDIFFupperlimit1.35501Vnominal.'),('R38','49.9k 0.1%','REF25','REF_UV','IndependentTPS3700referencemonitorUVtop.'),('R39','10k 0.1%','REF_UV','PGND','UVdivider400mVthreshold,release2.396Vtypical.'),('R40','56k 0.1%','REF25','REF_OV','IndependentreferencemonitorOVtop.'),('R41','10k 0.1%','REF_OV','PGND','OVassert2.64Vtypical.'),('R42','130k 0.1%','VOUT_SENSE','HV1','OVPdividerstage1,>=100VworkingratingMPNpending.'),('R43','130k 0.1%','HV1','HV2','OVPdividerstage2,>=100VworkingratingMPNpending.'),('R44','137k 0.1%','HV2','VMON','OVPdividerstage3,>=100VworkingratingMPNpending.'),('R45','10k 0.1%','VMON','PGND','Vout/40.7;2.5Vthreshold=>101.75Vnominal,not100Vhardceiling.')]
for i,(ref,val,a,b,desc) in enumerate(rf):
 bxy={'R42':(155,40),'R43':(155,60),'R44':(155,80),'R45':(155,100)}.get(ref)
 resistor(ref,val,a,b,desc,'fault',RH if ref in ('R42','R43','R44') else R,bxy=bxy)
for i,ref in enumerate(['U1','U2','U4','U5','U6','U7'],1):capacitor('C'+str(i),'100nF 50V X7R','AUX5','PGND','LocalICdecoupling;realroutingmustlocateat'+ref,sheet='analog' if i<=2 else 'fault')
capacitor('C7','100nF 50V X7R','REF25','PGND','Referencebypass,LM4040stablewithcapacitiveloaddatareview.')
capacitor('C8','1nF 50V C0G','CC_COMP','CC_NEG','PIstartingcapacitor;1/(2pi*10k*1n)=15.9kHzzero,notproofloopbandwidth/stability.')
capacitor('C9','10nF 50V X7R','DELAY','PGND','TPS3808resetrelease~57.6msnominal.',sheet='fault')
capacitor('C10','100pF 50V C0G','VMON','PGND','OVPinputnoisebypass;dividerRth~9.75k gives~1usRC;delaymustbeincludedinOVPbudget.',sheet='fault',bxy=(142,105))
for i,n in enumerate(['AUX5','PGND','REF25','VCMD','INJ_NODE','VFB','ISET','IREF','IMON','CC_OUT','ITH','ENABLE','VDIFF','VMON','REF_UV','REF_OV'],1):
 add('TP'+str(i),n,'Connector:TestPoint',TP,{'1':n},'Floatingsecondarytestpoint;INJ/VFB/ITHprobedhighimpedance;VMONmonitorsHVdivider.',xy=(20.32+22.86*((i-1)%8),254+15.24*((i-1)//8)),bxy=(10+8*(i-1),130))
for i,n in enumerate(['AUX5','PGND'],1):add('#FLG'+str(i),'PWR_FLAG','power:PWR_FLAG','',{'1':n},'Externalfixtureenergysource.',xy=(279.4+22.86*(i-1),25.4),in_bom=False,on_board=False)
descriptions={
 'J1':'Ekstern reguleret 5 V hjælpeforsyning på samme flydende sekundærside; krav 4,75–5,25 V. Ingen regulator på kortet.',
 'J2':'Eksterne lavimpedante setpunkter: VCMD 0–1,2 V giver høj til lav udgangsspænding; ISET 0,1–0,6 V svarer nominelt til 0–10 A. Under cirka 0,212 A gives shutdown.',
 'J3':'VFB, ITH og ENABLE til en senere programmerbar enkeltfasevariant. Den eksisterende faste effektfase er ikke ændret eller integreret.',
 'J4':'Direkte Kelvin-ledninger til ekstern 1 mΩ returshunt. IN+ på DUT-retur, IN− på fase-PGND; ingen belastningsstrøm gennem stikket.',
 'J5':'Separat 0–120 V udgangssense. Stikfabrikat og spændingsrating mangler. Ingen belastningsstrøm.',
 'JP1':'ARM-jumper, normalt åben. Aktiverer kun ENABLE-pullup gennem 10 kΩ; ingen fejllås eller fysisk udgangsafbrydelse.',
 'U1':'OPA4192: fire kanaler til positiv CV-injektion, ITH-strømclamp, bufferet 0,1 V strømreference og dynamisk injektionskontrol. Stabilitet og fejlrespons er uverificeret.',
 'U2':'INA240A2 SOIC-8, gain 50. IMON = 0,1 V + 0,05 V/A. Maksimalt 25 µV inputoffset svarer til 25 mA på 1 mΩ. Common-mode −4–80 V; ikke til 100 V high-side.',
 'U3':'LM4040A 2,5 V shuntreference, 0,1 % ved 25 °C; bias fra 2,49 kΩ. Pin 3 forbindes til anoden efter TI-databladets tilladelse.',
 'U4':'TPS3808G50, open-drain RESET på ENABLE; nominelt 4,65 V hjælpeforsyningsgrænse og cirka 57,6 ms resetforsinkelse med 10 nF.',
 'U5':'TPS3700 med uafhængig intern 400 mV reference overvåger 2,5 V-referencen. Hysterese og tærskeltolerance indgår i review.',
 'U6':'TLV1704 med open-collector udgange: VCMD høj, INJ_NODE høj samt ISET lav og høj trækker ENABLE lavt.',
 'U7':'TLV1704: IMON lav, VDIFF lav/høj og separat udgangs-OVP. IMON-low erstatter den startblokerende absolutte INJ-low kontrol.',
 'D1':'DFLS1200-7, katode ved INJ_NODE. Tillader positiv CV-injektion og blokerer aktiv sinking. Fabrikantdata for lækstrøm/VF mangler; kortsluttet diode ophæver beskyttelsen.',
 'D2':'DFLS1200-7, anode mod ITH gennem 470 Ω. Tillader kun at CC-kanalen trækker ITH ned; clampautoritet og diode-VF er ikke kvalificeret.',
 'R1':'CV-servo: VFB til ikke-inverterende gennemsnitsknude.', 'R2':'CV-servo: VCMD til samme gennemsnitsknude.',
 'R3':'CV-servoens INJ_NODE-feedback, øverste halvdel.', 'R4':'CV-servoens feedback til PGND, nederste halvdel; passiv feedbackbelastning består også ved strømtab.',
 'R5':'Trækker manglende VCMD mod 2,5 V, hvilket skal give kommandofejl.', 'R6':'Trækker manglende ISET mod PGND, hvilket skal give shutdown.',
 'R7':'Positiv injektionsvej fra INJ_NODE til VFB; oprindelig 820 kΩ/10 kΩ fasefeedback bevares.',
 'R8':'CC-fejlforstærkerens måleindgang fra IMON; startværdi til kompensation.', 'R9':'Seriemodstand i foreløbig CC-kompensation.',
 'R10':'Begrænser strømmen fra ITH til CC-clamp; faktisk clampautoritet kræver måling.',
 'R11':'Strømreferencens øvre dividerben, 2,5 V/25.', 'R12':'Strømreferencens nedre dividerben, nominelt 0,1 V.',
 'R13':'Bias til 2,5 V shuntreference; cirka 1,004 mA samlet ved 5 V før dividerbelastninger.',
 'R14':'Øvre ben til VMID, nominelt 1,25 V; belastning skal medregnes.', 'R15':'Nedre ben til VMID.',
 'R16':'Dynamisk injektionskontrol, INJ_NODE til positiv sumindgang.', 'R17':'Dynamisk injektionskontrol, VMID til positiv sumindgang.',
 'R18':'Dynamisk injektionskontrol, PGND til positiv sumindgang.', 'R19':'Dynamisk injektionskontrol, VFB til negativ sumindgang.',
 'R20':'Dynamisk injektionskontrol, VCMD til negativ sumindgang.', 'R21':'Feedback til VDIFF = INJ_NODE − VFB − VCMD + VMID.',
 'R22':'0 Ω direkte Kelvin+ forbindelse til INA240; intet inputfilter i denne revision.', 'R23':'0 Ω direkte Kelvin− forbindelse til INA240.',
 'R24':'ENABLE-pullup efter fysisk ARM. Eneste tilsigtede enable-kilde.', 'R25':'ENABLE-pulldown for normalt shutdown; parallelt med fasens 100 kΩ.',
 'R26':'Øvre ben til VCMD-høj grænse.', 'R27':'Nedre ben, giver nominelt 1,2315 V VCMD-grænse.',
 'R28':'Øvre ben til ISET-lav grænse.', 'R29':'Nedre ben, giver 0,11062 V, cirka 0,2124 A nominel slukgrænse.',
 'R30':'Øvre ben til ISET-høj grænse.', 'R31':'Nedre ben, giver 0,625 V eller 10,5 A nominelt som kommandovindue.',
 'R32':'Øvre ben til IMON-lav plausibilitetsgrænse.', 'R33':'Nedre ben, giver 74,85 mV. Normal nulstrøm ved 100 mV passerer; åben sense er ikke dækket fuldstændigt.',
 'R34':'Øvre ben til VDIFF-lav grænse.', 'R35':'Nedre ben, giver 1,14679 V nominelt.',
 'R36':'Øvre ben til VDIFF-høj grænse.', 'R37':'Nedre ben, giver 1,35501 V nominelt.',
 'R38':'Øvre ben til TPS3700 reference-undervolt.', 'R39':'Nedre ben; 2,396 V nominel positiv tærskel.',
 'R40':'Øvre ben til TPS3700 reference-overvolt.', 'R41':'Nedre ben; 2,64 V nominel triptærskel.',
 'R42':'Separat udgangs-OVP-divider, højspændingstrin 1. Krav mindst 100 V arbejdsrating; fabrikant mangler.',
 'R43':'Separat udgangs-OVP-divider, højspændingstrin 2. Krav mindst 100 V arbejdsrating; fabrikant mangler.',
 'R44':'Separat udgangs-OVP-divider, højspændingstrin 3. Krav mindst 100 V arbejdsrating; fabrikant mangler.',
 'R45':'OVP-dividerens bundben: VMON = VOUT/40,7; nominelt 101,75 V trip, ingen hård 100 V-grænse.',
 'C7':'Afkobling af LM4040-referencen.', 'C8':'Foreløbig CC-seriekompensation; nulpunkt cirka 15,9 kHz. Ingen dokumenteret stabilitet.',
 'C9':'TPS3808-resetforsinkelse, cirka 57,6 ms nominelt.', 'C10':'100 pF støjfilter på OVP-divider; cirka 1 µs RC skal indgå i fejlrespons.',
}
for i, ic in enumerate(['U1','U2','U4','U5','U6','U7'],1):descriptions['C'+str(i)]='Lokal forsyningsafkobling ved '+ic+'.'
for c in components:
 if c['ref'].startswith('TP'):c['description']='Testpunkt '+c['val']+' på flydende sekundærside; se manualens forventede værdier.'
 elif c['ref'] in descriptions:c['description']=descriptions[c['ref']]
 if c['ref']=='J1':c['xy']=(33.02,27.94)
 if c['ref'] in ('U2','U3'):
  x,y=c['xy'];c['field_positions']={'Reference':(x,y-13.97),'Value':(x,y+13.97)}
 if c['ref']=='U1' and c['unit']==5:
  x,y=c['xy'];c['field_positions']={'Reference':(x+10.16,y-2.54),'Value':(x+10.16,y+2.54)}
 if c['ref'] in ('C2','C7','C8'):c['xy']={'C2':(340.36,215.9),'C7':(340.36,240.03),'C8':(228.6,266.7)}[c['ref']]
 if c['ref'].startswith('TP'):
  i=int(c['ref'][2:])-1;c['xy']=(25.4+22.86*(i%8),259.08+15.24*(i//8))
root=h.uid();child=h.uid();h.write_schematic(D/(NAME+'.kicad_sch'),analog,project=NAME,root_uuid=root,title='EXPERIMENTAL CV/CC - SINGLE PHASE ONLY - NOT4kW',comments=['Source-only VFB injection; sink-only ITH clamp','1.2..~100 V / 0..10 A commands; ~0.21 A active floor','PCB status: routing report; no hardware tests; not for fabrication'],sheets=[dict(name='Fault guard and output monitor',file='faults.kicad_sch',xy=(350.52,157.48),size=(55.88,35.56),uuid=child)],texts=[dict(xy=(12.7,12.7),text='EXPERIMENTAL ANALOG CONTROL - one LTC3779 research phase\nNo active0V, no milliampere protection, no4-phase sharing. Native power design unchanged.'),dict(xy=(12.7,140.97),text='VCMD 0..1.2 V -> high-to-low Vout. CV diode prevents intentional feedback sinking.\nISET=0.1+0.05*I; lower than~0.1106 V causes hardware shutdown; PI values unvalidated.')])
h.write_schematic(D/'faults.kicad_sch',fault,project=NAME,root_uuid=child,instance_path='/'+root+'/'+child,title='EXPERIMENTAL FAULT GUARDS',comments=['Open-collector fault outputs; no latch/output switch','ENABLE default low; manual ARM is the pull-up source','OVP ~101.75 V nominal; no hard 100 V limit'],texts=[dict(xy=(12.7,12.7),text='Hardware guards:5V/ref validity, VCMD andISET range, actualINJ andmismatch, VOUT OVP.\nFaults may automatically restart when cleared. RUN-off does not discharge/disconnect Cout.')])
project={'meta':{'filename':NAME+'.kicad_pro','version':1},'board':{'design_settings':{'rules':{'min_clearance':0.25,'min_track_width':0.25,'min_copper_edge_clearance':0.5}}},'net_settings':{'classes':[{'name':'Default','clearance':0.25,'track_width':0.3,'via_diameter':0.8,'via_drill':0.4},{'name':'HV','clearance':3.0,'track_width':0.3,'via_diameter':0.8,'via_drill':0.4}],'netclass_patterns':[{'netclass':'HV','pattern':n} for n in ['VOUT_SENSE','HV1','HV2']],'meta':{'version':4}}}
(D/(NAME+'.kicad_pro')).write_text(json.dumps(project,indent=2)+'\n')
libs=sorted({c['lib'].split(':')[0] for c in components});(D/'sym-lib-table').write_text('(sym_lib_table(version 7)\n'+'\n'.join(f'(lib(name "{lib}")(type "KiCad")(uri "'+('${KIPRJMOD}/'+LIB+'.kicad_sym' if lib==LIB else '${KICAD9_SYMBOL_DIR}/'+lib+'.kicad_sym')+'")(options "")(descr "Verifiedpinmapresearchlibrary"))' for lib in libs)+'\n)\n'.replace('${KIPRJMOD}','${KIPRJMOD}'))
# StandardKiCad variableisKIPRJMOD.
fplibs=sorted({c['footprint'].split(':')[0] for c in components if c['footprint']});(D/'fp-lib-table').write_text('(fp_lib_table(version 7)\n'+'\n'.join(f'(lib(name "{l}")(type "KiCad")(uri "${{KICAD9_FOOTPRINT_DIR}}/{l}.pretty")(options "")(descr "InstalledKiCadfootprint"))' for l in fplibs)+'\n)\n')
def cli(*args):subprocess.run([str(ROOT/'bin/kicad-env'),'kicad-cli',*map(str,args)],cwd=ROOT,check=True)
cli('sch','export','netlist','--format','kicadxml','-o',E/'control.xml',D/(NAME+'.kicad_sch'))
xml=ET.parse(E/'control.xml').getroot();wanted={};perref={}
for c in components:
 if not c['on_board']:continue
 perref.setdefault(c['ref'],c)
 for p,n in c['nets'].items():
  if n is not None:wanted.setdefault(n,set()).add((c['ref'],p))
actual={n.attrib['name']:{(p.attrib['ref'],p.attrib['pin']) for p in n.findall('node') if not p.attrib['ref'].startswith('#')} for n in xml.find('nets') if not n.attrib['name'].startswith('unconnected-')};assert actual==wanted,[(n,sorted(actual.get(n,set())-wanted.get(n,set())),sorted(wanted.get(n,set())-actual.get(n,set()))) for n in set(actual)|set(wanted) if actual.get(n,set())!=wanted.get(n,set())]
board=pcbnew.BOARD();nets={}
for n in wanted:
 ni=pcbnew.NETINFO_ITEM(board,n);board.Add(ni);nets[n]=ni
for ref,c in perref.items():
 lib,part=c['footprint'].split(':');fp=pcbnew.FootprintLoad('/usr/share/kicad/footprints/'+lib+'.pretty',part);assert fp,c['footprint'];fp.SetAttributes(fp.GetAttributes() & ~pcbnew.FP_EXCLUDE_FROM_BOM);fp.SetReference(ref);fp.SetValue(c['val']);fp.SetFPID(pcbnew.LIB_ID(lib,part));fp.SetPosition(pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in c['board_xy'])));path=pcbnew.KIID_PATH();path.push_back(pcbnew.KIID(root));
 if c in fault:path.push_back(pcbnew.KIID(child))
 path.push_back(pcbnew.KIID(c['uuid']));fp.SetPath(path)
 cpins={p:n for a in components if a['ref']==ref for p,n in a['nets'].items()}
 for pad in fp.Pads():
  p=pad.GetNumber()
  if p and cpins[p] is not None:pad.SetNet(nets[cpins[p]])
 fp.Value().SetVisible(False);fp.Reference().SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(.8),pcbnew.FromMM(.8)));fp.Reference().SetTextThickness(pcbnew.FromMM(.12));fp.Reference().SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(c['board_xy'][0]),pcbnew.FromMM(c['board_xy'][1]-2.5)));
 if ref in ['U1','U2','U6','U7']:fp.Reference().SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(c['board_xy'][0]),pcbnew.FromMM(c['board_xy'][1]-5)))
 if ref=='J5':fp.Reference().SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(145),pcbnew.FromMM(20)))
 board.Add(fp)
for a,b in [((0,0),(180,0)),((180,0),(180,150)),((180,150),(0,150)),((0,150),(0,0))]:
 t=pcbnew.PCB_SHAPE(board);t.SetShape(pcbnew.SHAPE_T_SEGMENT);t.SetStart(pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in a)));t.SetEnd(pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in b)));t.SetLayer(pcbnew.Edge_Cuts);t.SetWidth(pcbnew.FromMM(.05));board.Add(t)
for txt,xy,size in [('UNROUTED EXPERIMENTAL CV/CC - DO NOT FABRICATE',(90,5),1.3),('ONE PHASE;NO ACTIVE0V;NOmA PROTECTION;NO40A',(90,145),1.0),('HV SENSE',(157,28),1.0)]:
 t=pcbnew.PCB_TEXT(board);t.SetText(txt);t.SetPosition(pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in xy)));t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(size),pcbnew.FromMM(size)));t.SetTextThickness(pcbnew.FromMM(.15));t.SetLayer(pcbnew.F_SilkS);board.Add(t)
board.GetDesignSettings().SetCopperLayerCount(2);pcbnew.SaveBoard(str(D/(NAME+'.kicad_pcb')),board)
native=json.loads((D/(NAME+'.kicad_pro')).read_text());native.setdefault('board',{}).setdefault('design_settings',{}).setdefault('rules',{}).update(project['board']['design_settings']['rules']);native['net_settings']=project['net_settings'];(D/(NAME+'.kicad_pro')).write_text(json.dumps(native,indent=2)+'\n')
rules=['(version 1)', '(rule "HV copper separation" (condition "A.NetClass == \'HV\' || B.NetClass == \'HV\'") (constraint clearance (min 3.0mm)))']
for ref in ['R42','R43','R44']:
 c=perref[ref];a,b=c['nets']['1'],c['nets']['2']
 condition=f"A.intersectsCourtyard('{ref}') && B.intersectsCourtyard('{ref}') && ((A.NetName == '{a}' && B.NetName == '{b}') || (A.NetName == '{b}' && B.NetName == '{a}'))"
 rules.append(f'(rule "{ref} intended 1206 terminal gap" (condition "{condition}") (constraint clearance (min 1.5mm)))')
(D/(NAME+'.kicad_dru')).write_text('\n'.join(rules)+'\n')
bpads={}
for fp in board.GetFootprints():
 for p in fp.Pads():
  if p.GetNumber() and p.GetNetname():bpads.setdefault(p.GetNetname(),set()).add((fp.GetReference(),p.GetNumber()))
assert bpads==wanted,'WrongPCBpinmapping'
with (ROOT/'bom/control.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['Reference','Value','Footprint','Quantity','Description','Source','Release_status'])
 for c in perref.values():w.writerow([c['ref'],c['val'],c['footprint'],1,c['description'],c['datasheet'],'EXPERIMENTAL - SEE ROUTING REPORT / HARDWARE AND STABILITY PENDING'])
 w.writerow(['SHUNT_EXTERNAL','1mohm four-terminal >=10W >=50A','OFFBOARD',1,'Ekstern returshunt, samme systemkrav som målekortets SHUNT_EXT; ikke en ekstra fysisk shunt ved fælles måling. Fabrikat mangler. 10 A giver 10 mV og 0,1 W; 40 A giver 40 mV og 1,6 W.','','UNSELECTED OFFBOARD REQUIREMENT'])
cli('sch','export','pdf','-o',E/'control.pdf',D/(NAME+'.kicad_sch'));cli('sch','export','svg','-o',E/'schematic_svg',D/(NAME+'.kicad_sch'));cli('sch','erc','--severity-all','--format','json','-o',E/'erc.json',D/(NAME+'.kicad_sch'));cli('pcb','drc','--severity-all','--schematic-parity','--format','json','-o',E/'drc_unrouted.json',D/(NAME+'.kicad_pcb'));cli('pcb','export','svg','--mode-single','--layers','F.Cu,F.SilkS,Edge.Cuts','-o',E/'pcb_placement.svg',D/(NAME+'.kicad_pcb'))
er=json.loads((E/'erc.json').read_text());dr=json.loads((E/'drc_unrouted.json').read_text());summary={'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Experimental single-phase control;notfull0..100V40Asupply','erc_violations':sum(len(s['violations']) for s in er['sheets']),'drc_violations':len(dr['violations']),'drc_types':dict(collections.Counter(v['type'] for v in dr['violations'])),'drc_unconnected':len(dr['unconnected_items']),'drc_parity':len(dr['schematic_parity']),'logical_pin_agreement':'PASS','components':len(perref),'connected_pins':sum(map(len,wanted.values())),'nets':len(wanted),'tracks':0,'hardware_tests':'NOT PERFORMED','fabrication_release':False};(E/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
