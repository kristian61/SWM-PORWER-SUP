# Analogt CV/CC-styrekort: funktion og fejlfinding

Dette dokument beskriver et **eksperimentelt styrekort til én LTC3779-effektfase**. Native KiCad-diagram, komponentliste og PCB findes i design/control, bom/control.csv og exports/control. Den aktuelle routingstatus står i control-layout.md og routing_summary.json. Kortets PCB er routet og CAD-kontrolleret; det dokumenterer ikke en færdig 230 V AC → 0–100 V / 40 A laboratorieforsyning eller verificeret hardware. Den eksisterende effektfase beskrives i [power-phase.md](power-phase.md).

Alle signaler og hjælpeforsyninger her tilhører samme flydende sekundærside. Kortet indeholder ingen netspændingsisolation. Et isoleret AC/DC-trin, sikkerhedsafstande, chassis/PE, køling og en fysisk udgangsafbryder er separate nødvendige dele af den samlede forsyning.

## Reguleringens signaler

| Signal | Nominelt område eller værdi | Funktion |
|---|---|---|
| AUX5 | 5 V | Ekstern reguleret hjælpeforsyning til opamps, comparatorer og reference; må ikke komme fra LTC3779 V5, som forsvinder i shutdown |
| PGND | Sekundærsidejord | Fasejord og reference for styrekortet; ikke beskyttelsesjord |
| VFB | 1,2 V under normal CV-drift | LTC3779-feedback; måles på fasens eksisterende divider |
| VCMD | 0–1,2 V fra en ekstern lavimpedant kilde | Omvendt spændingskommando: højere VCMD giver lavere udgangsspænding |
| INJ_NODE | Cirka VFB + VCMD | Faktisk injektionsspænding ved modstanden til VFB |
| VDIFF | Cirka 1,25 V ved korrekt CV-servo | Kontrol af forskellen INJ_NODE − VFB − VCMD |
| ISET | 0,1–0,6 V | Strømkommando; matematisk 0–10 A, men det lave område er ikke anvendeligt som præcis laboratoriebegrænsning |
| IMON | 0,1 V + 0,05 V/A × IOUT | Målt udgangsstrøm fra INA240A2 og ekstern 1 mΩ shunt |
| CC_OUT | Opamp-udgang | Kan gennem en diode trække ITH ned og reducere strømmen |
| ENABLE | Cirka 2,38 V med ARM og alle kontrolsignaler gyldige | Enable til fasens eksisterende RUN-interface; comparatorer kan trække signalet lavt |
| REF25 | 2,5 V | LM4040-reference for lokale dividergrænser; overvåges separat af TPS3700 |

VCMD og ISET skal komme fra en lavimpedant, dokumenteret ekstern indstilling. Et DAC-interface, brugerknapper, display og firmware er endnu ikke en del af denne reguleringsstudie. En manglende VCMD trækker en lokal 100 kΩ modstand mod REF25 og skal give fejl; en manglende ISET trækkes mod jord og skal give shutdown.

## CV: positiv injektion med lokal servo

OPA4192 kanal A sammenligner to dividerknudepunkter. Den ikke-inverterende indgang forbindes gennem to lige 1 MΩ modstande til henholdsvis VFB og VCMD. Den inverterende indgang måler INJ_NODE gennem en 1 MΩ / 1 MΩ divider mod PGND. Opamp-udgangen driver INJ_NODE gennem en **DFLS1200-7** med **anode ved opamp-udgangen og katode ved INJ_NODE**. INJ_NODE forbindes til VFB gennem 10 kΩ. Dioden er samme referencekandidat og PowerDI-123-footprint som i ADI-effektfasens stykliste; dens producentdata for denne anvendelse er endnu ikke verificeret.

Når dioden leder, og sløjfen regulerer, giver de lige modstande:

```text
(VFB + VCMD)/2 = INJ_NODE/2
INJ_NODE = VFB + VCMD
```

Dermed løber en positiv strøm fra INJ_NODE til VFB, som reducerer den spænding, effektfasen behøver at levere. Dioden skal blokere, hvis opamp-udgangen går lavt. En lav eller strømløs opamp-udgang kan derfor ikke gennem denne diode aktivt trække VFB ned og kræve cirka 198 V, som en direkte, tovejs spændingsinjektion med 10 kΩ kunne gøre. **En kortsluttet diode ophæver denne egenskab.**

Hvis injektionen bortfalder, vender fasen mod dens høje, faste grundindstilling. Derfor er positiv injektion alene ikke tilstrækkelig beskyttelse af en belastning indstillet til eksempelvis 5 V. RUN-shutdown og måling af den faktiske udgang er nødvendige.

OPA4192 kanal D overvåger servoen. Den ikke-inverterende indgang forbindes gennem tre lige 1 MΩ modstande til INJ_NODE, VMID = 1,25 V og PGND. Den inverterende indgang forbindes gennem tre lige 1 MΩ modstande til VFB, VCMD og kanalens egen udgang VDIFF. Ideelt giver det:

```text
VDIFF = INJ_NODE − VFB − VCMD + VMID
```

VDIFF skal derfor ligge omkring 1,25 V, når den lokale CV-servo fungerer. Denne overvågning er nyttig ved en fastlåst injektionsudgang eller en afbrudt injektionsvej. Den overvåger ikke alle fejl i en fælles opamp, reference, jord eller connector og må ikke betegnes som verificeret enkeltfejlsbeskyttelse.

### Feedback-belastning og kalibrering

1 MΩ-netværkene belaster den eksisterende feedback-divider. Med ideelle opamp-indgange og VMID = 1,25 V er den ekstra strøm ud af VFB:

```text
Iextra = (7 × VFB − 5 × VCMD − 2,5 V)/(6 MΩ)
VOUT = 83,9566667 × VFB − 82,6833333 × VCMD − 0,3416667 V
```

Med LTC3779's nominelle VFB = 1,2 V:

```text
VOUT = 100,406333 V − 82,6833333 × VCMD
```

| VCMD | Beregnet VOUT | Praktisk betydning |
|---:|---:|---|
| 0 V | 100,406 V | Over 100 V allerede i den ideelle beregning; kræver kalibrering og separat vurdering af maksimum |
| Cirka 0,004914 V | 100 V | Ideelt kalibreringspunkt; ingen garanti for 100 V med komponenttolerancer |
| Cirka 1,153876 V | 5 V | Lav spænding kræver stadig måling af stabilitet, ripple og lasttransienter |
| 1,2 V | 1,186 V | Under controllerens dokumenterede minimum på 1,2 V; ikke et verificeret driftspunkt |
| Cirka 1,21435 V | 0 V matematisk | Ingen dokumentation for fysisk 0 V-regulering; må ikke bruges som en specifikation |

Beregningen udelader opamp-offset, inputbias, modstandsratiofejl, VCMD-kildens impedans, VMID-belastning og lækstrømme. En passiv VMID-divider belastes også af kanal D og skal indgå i den endelige model. LTC3779's referenceinterval 1,188–1,212 V alene ændrer den beregnede udgang cirka ±1,007 V. Ved VCMD = 0 og den højeste reference er den beregnede udgang cirka 101,414 V.

CV-reguleringen skal derfor kalibreres mod en målt udgang; en DAC-kode eller beregning er ikke en selvstændig spændingsmåling. Permanent regulering helt ned til 0 V samt en defineret afladning eller aktiv sink-funktion mangler.

## CC: udgangsshunt og sink-only ITH-kontrol

En ekstern **1 mΩ Kelvin-shunt** placeres i belastningens retur. INA240A2 måler med IN+ på belastningens retur og IN− på fasens PGND, så normal udgangsstrøm giver et positivt signal. Alle strømførende returveje skal gå gennem shunten. Et instrumentjord-, USB- eller chassisforbindelse, som omgår shunten, gør strømmålingen forkert.

Begge INA240-referenceben tilføres en bufferet 0,1 V reference. Den dannes nominelt af REF25 gennem 240 kΩ over 10 kΩ. Med gain 50 V/V bliver:

```text
IMON = 0,1 V + 50 × 0,001 Ω × IOUT
IOUT = (IMON − 0,1 V)/0,05 V/A
```

OPA4192's CC-kanal har ISET på den ikke-inverterende indgang og IMON gennem 20 kΩ på den inverterende indgang. En seriekobling på **10 kΩ og 1 nF** fra CC_OUT til den inverterende indgang er en foreløbig PI-kompensation. ITH forbindes gennem **470 Ω** til en **DFLS1200-7**-diodes anode; katoden forbindes til CC_OUT. Når IMON overskrider ISET, falder CC_OUT, og dioden trækker ITH ned. Ved strøm under indstillingen går CC_OUT højt, og dioden blokerer, så den ikke forsøger at hæve ITH. Forward drop, lækstrøm og opampens strømkapacitet skal verificeres; tilstrækkelig ITH-kontrol kan ikke garanteres ud fra et generisk Schottky-symbol.

Den passive ensretning mellem CC-sløjfen og ITH er et reguleringsprincip; den dokumenterer ikke stabilitet. Kompensationsværdierne er startværdier. Opampens mætning, genindkobling, oversving ved CV/CC-overgang, diodekapacitans, ITH-strøm og samspillet med fasens eksisterende kompensation skal måles. Der er endnu ingen særskilt anti-windup eller dokumenteret mætningstilbagekobling.

### Begrænsning ved små strømme

INA240's maksimale inputoffset på ±25 µV svarer med 1 mΩ til **±25 mA** før shuntfejl, referencedrift, temperatur og andre kredsløbsfejl. Offsetdrift kan bidrage yderligere. En 10 mA belastning giver kun 10 µV over shunten, mindre end den maksimale offset. Dette område kan derfor ikke bruges til at love beskyttelse af en lille TL072-opstilling.

Den foreslåede hardwaregrænse ved **ISET ≈ 0,11062 V** slukker RUN. Det svarer matematisk til cirka **0,2124 A**. Indstillinger derunder er et slukområde, ikke et dokumenteret 0–212 mA CC-område. Et separat lavstrømsområde med egnet shunt, gain, udgangskapacitans og beskyttelse kræves for brugerens ønske om milliamperebegrænsning.

Shunten skal have verificeret Kelvin-opbygning, temperaturkoefficient, effektrating og terminaler. Ved 10 A er dens tab nominelt 0,1 W; ved 40 A 1,6 W. Disse beregninger dokumenterer ikke termisk egnethed eller en 40 A effektfase.

## Hardware-shutdown og referenceovervågning

To **TLV1704** giver otte comparatorer med open-collector udgange. De forbindes til en fælles ENABLE-knude sammen med **TPS3808G50's aktive-lave RESET** og **TPS3700's to open-drain udgange**. Der er ingen LVC-logikgate i dette kredsløb. Der må ikke kobles push-pull udgange på denne fælles knude. TPS3808's RESET skal være modelleret som open-drain i KiCad; et generisk bibliotekssymbol med almindelig output-type beskriver ikke den faktiske elektriske funktion.

En manuel ARM-jumper forbinder AUX5 til ENABLE gennem **10 kΩ**. Styrekortets egen **10 kΩ pulldown** og fasens eksisterende **100 kΩ RUN-pulldown** giver uden fejl nominelt cirka 2,38 V, før intern pull-up og øvrige lækstrømme medregnes. Den interne RUN-pull-up ændrer denne værdi lidt. Uden ARM er den kombinerede pulldown cirka 9,09 kΩ, og LTC3779's interne 2,5 µA pull-up giver cirka 23 mV. ARM er en manuel aktivering, ikke et verificeret udgangsrelæ.

LTC3779 skal have RUN under 1,1 V for shutdown; dens turn-on tærskel er specificeret til 1,1–1,3 V. Comparatorernes lave udgangsspænding og strøm under alle fejltilstande skal derfor verificeres mod den fælles knudes belastning. ENABLE må ikke samtidig drives fra en separat spændingskilde, som omgår eller overbelaster fault-gaten.

| Overvågning | Foreløbig grænse | Hvad den kan opdage |
|---|---|---|
| INJ_NODE høj | 2,5 V | For høj faktisk injektionsspænding |
| IMON lav | Cirka 0,07485 V | Sensorudgang under normal nulstrømsbias; ikke fuld åben-sense-diagnose |
| VCMD høj | Cirka 1,2315 V | Manglende indstilling, som trækkes mod REF25, eller for høj kommando |
| VDIFF lav/høj | 1,15–1,35 V | Afvigelse fra INJ_NODE = VFB + VCMD |
| ISET lav | Cirka 0,11062 V | Manglende strømkommando og indstilling i slukområdet |
| ISET høj | Omkring 0,625 V som foreløbigt loft | For høj eller forkert strømkommando; endelig divider skal fremgå af stykliste/diagram |
| Uafhængig VOUT-divider | Cirka 101,75 V nominelt | Overspænding målt på den faktiske udgang, separat fra fasens VFB-net |
| AUX5 supervisor | 4,65 V nominelt | Hjælpeforsyning under det fastlagte driftsområde |
| REF25 monitor | Cirka 2,396 / 2,64 V positive tærskler | Referencefejl med separat intern 400 mV reference |

OPA4192 kræver mindst 4,5 V. TPS3808G50's 4,65 V tærskel har op til ±2 % tolerance over hele temperaturintervallet, hvilket giver cirka 4,557–4,743 V før yderligere forhold. Den laveste tærskel giver kun cirka 57 mV margin til opampens minimum. Forsyningsripple, comparatorforsinkelse, reset-timing og opstart skal indgå i valideringen; en nominel tærskel alene garanterer ikke korrekte signaler under spændingsfald.

REF25 dannes af **LM4040AIM3-2.5/NOPB** med **2,49 kΩ bias fra AUX5 og 100 nF afkobling**. Biasstrømmen er nominelt cirka 1,004 mA ved 5 V. Alle divider-, reference- og inputbelastninger skal trækkes fra, så LM4040's minimumsstrøm fortsat overholdes.

TPS3700 anvender en separat intern 400 mV reference. Med **49,9 kΩ / 10 kΩ** til undervoltindgangen og **56 kΩ / 10 kΩ** til overvoltindgangen er de positive tærskler 2,396 V og 2,64 V. Intern hysterese betyder, at undervolt ved faldende reference typisk først asserts ved cirka **2,363 V**, og overvolt efter en fejl typisk frigives omkring **2,604 V**. De nævnte 2,396–2,64 V er derfor ikke en præcis, symmetrisk fejlgrænse. Databladets tærskeltolerance, hystereseinterval, biasstrømme og modstandstolerancer skal med i grænseberegningen.

De otte TLV1704-kanaler er fordelt som følger: U6 overvåger VCMD høj, INJ_NODE høj, ISET lav og ISET høj; U7 overvåger IMON lav, VDIFF lav, VDIFF høj og VOUT overspænding. U2 er INA240-sensoren. IMON-low bruger 324 kΩ / 10 kΩ fra 2,5 V, hvilket giver cirka 74,85 mV. Normal nulstrømsbias på 100 mV passerer. Åben eller kortsluttet shunt-sense er ikke dokumenteret dækket; der er ingen ledig comparator eller skjult softwarebeskyttelse.

### Separat udgangsoverspænding

Den foreslåede VOUT-divider har **130 kΩ + 130 kΩ + 137 kΩ** i toppen og **10 kΩ** i bunden. VMON = VOUT/40,7. Sammenligning med REF25 = 2,5 V giver **101,75 V nominelt**. Divideren skal forbindes til udgangsspændingen gennem en separat målevej fra fasens almindelige VFB-divider.

Dette er **ingen hård 100 V grænse**. Comparatoroffset, referencetolerance og temperaturdrift samt modstandsratiofejl flytter tripspændingen. Den beregnede maksimale CV-spænding på cirka 101,414 V før øvrige fejl ligger kun cirka 0,336 V under den nominelle OVP. Disse områder kan overlappe med tolerancer og give utilsigtet shutdown ved høj indstilling. Kalibrering og et samlet grænsebudget er nødvendigt før en fuldskalaindstilling kan accepteres.

OVP-comparatoren bruger her samme REF25 som flere lokale grænser. TPS3700 overvåger referencefejl med sin egen reference, men en tilladt ændring inden for referencevinduet flytter stadig OVP. Kredsløbet er en separat udgangsmåling; det er ikke dokumenteret som fuldstændig uafhængig, enkeltfejlssikker beskyttelse.

Der er **ingen fejllås**. Når fejlen forsvinder og ARM stadig er monteret, kan forsyningen automatisk forsøge at starte igen. Automatisk genstart og mulige gentagne energipulser skal vurderes særskilt. Et sikkert udgangsrelæ eller en elektronisk afbryder med specificeret DC-brydeevne mangler.

### Opstart ved lav eller ingen udgangsspænding

Den tidligere absolutte INJ_NODE-lav comparator ved 1,1 V gav en opstartslåsning fra afladt udgang ved VCMD nær 0. Den er fjernet i den aktuelle native revision og erstattet med IMON-low. Når VOUT = 0 og den ideelle servo arbejder, er INJ_NODE omtrent VFB + VCMD, så den dynamiske kontrol VDIFF fortsat ligger nær 1,25 V. Sensorens 0,1 V nulstrømsbias ligger over IMON-low. Den konkrete statiske startblokering er dermed fjernet; dette er en DC-kontrol af forbindelserne, ikke en målt opstartstransient.

Opampens mætning, referenceopstart, hjælpeforsyningssekvens, supervisorforsinkelse og soft-start skal stadig afprøves med en afladt udgang ved flere kommandoer. Der bruges ingen blanking eller manuel foropladning til at skjule en CV-fejl. Den aktuelle hardware har ingen fejllås og kan genstarte automatisk, når signalerne igen er gyldige.

## Fejlanalyse før nogen effektprøve

| Fejl | Forventet eller mulig virkning | Nødvendig afprøvning |
|---|---|---|
| VCMD-ledning åben | 100 kΩ til REF25 giver høj kommando og skal trække ENABLE lavt | Afbryd ved controllerconnectoren; bekræft faktisk lokal spænding og RUN-shutdown |
| VCMD kortsluttet til PGND | Gyldig høj-spændingskommando; efterspørger cirka 100,4 V nominelt | Denne fejl kan ikke skelnes fra brugerens fuldskalaindstilling med dette interface; ekstern kommandoovervågning eller ændret kodning kræves ved lavspændingsbelastninger |
| CV-opamp udgang lav/strømløs | Injektionsdiode skal blokere; høj grundspænding kan blive efterspurgt | Mismatch, INJ_NODE og faktisk OVP skal testes; undersøges først ved lav, strømbegrænset DC-bus |
| Injektionsdiode kortsluttet | Lav opamp-udgang kan aktivt trække VFB ned | Denne fejl ophæver sink-blokering; verificer direkte shutdown og analyser effekttrinnets transient |
| Injektionsmodstand eller forbindelse åben | Fasen kan vende tilbage mod cirka 99,6 V og/eller ændret feedbackbelastning | Afbryd hver connectorvej; mål VFB, INJ_NODE, VDIFF og ENABLE |
| VFB-måleledning åben | CV-servo og mismatch kan måle noget andet end den virkelige fasefeedback | Selvstændig VMON og default shutdown kræves; åben måleledning kan ikke antages altid at give lav udgang |
| ISET-ledning åben/til jord | Lokal pulldown giver RUN-shutdown | Bekræft slukgrænsen og at ingen anden signalvej holder ISET oppe |
| Shuntledninger ombyttet | IMON falder ved stigende strøm; CC kan miste sin begrænsning | Verificer polaritet før tilslutning af effekt; kan ikke dækkes alene af ISET-vinduet |
| Shunt-senseledninger kortsluttet sammen | IMON kan forblive omkring 0,1 V og se plausibelt ud | Denne fejl har ingen demonstreret dækning; brug anden beskyttelse og separat ledningsdiagnose |
| Jord- eller returforbindelse omgår shunten | Belastningsstrøm måles for lavt | Kontroller alle eksterne forbindelser og galvaniske broer |
| CC-opamp eller sink-diode åben | Justerbar CC kan forsvinde | Fasens faste middelstrømsloft er kun en grov overlastgrænse; afprøv særskilt beskyttelse |
| CC_OUT fast lav | Kan begrænse ITH og forhindre normal drift | Bekræft om RUN stadig kan slukke, og mål strømmen; diodefald gør ikke dette til sikker 0 A |
| AUX5 falder eller forsvinder | Supervisor skal holde ENABLE lavt; passive pulldowns skal overtage | Sweep spændingen og afprøv brat afbrydelse, med og uden levende effektbus |
| Start med uopladet udgang og VCMD nær 0 | Den gamle INJ-low startlåsning er fjernet; dynamisk mismatch og IMON-low skal passere i ideal DC | Afprøv reference/servo/reset/soft-start i tid; endnu ingen fysisk opstartstest |
| Inputdiode-backfeed ved AUX5 slukket | VOUT-divider og andre måleveje kan sende strøm til en strømløs forsyningsrail | TLV1704/OPA-indgange har beskyttelsesdioder; beregn og mål injektion, railspænding og ENABLE før nogen påstand om rail-off sikkerhed |
| Reference ændrer sig eller bryder sammen | Flere lokale grænser og OVP flytter sig samtidig | Afprøv TPS3700 med en separat varierbar referencesimulator; inkluder hysterese og opstart |
| RUN eller ENABLE kortsluttes højt | Converter kan forblive aktiv trods comparatorfejl | En separat fysisk udgangsafbryder og dokumenteret sikkerhedsanalyse mangler |

Denne tabel er en arbejdsliste, ikke en komplet FMEA. Connectorfejl, jordløft, alle komponentkortslutninger, ESD, temperatur, signalforsinkelser og fælles fejl skal behandles yderligere.

## Testpunkter og målerækkefølge

Kortet har 16 mærkede testpunkter; deres aktuelle net og forventede værdier fremgår af docs/control.md. VMID måles på R14/R15 og har ikke eget testpunkt i denne revision. Shunten skal have separate Kelvin-sensepunkter. Switchknudepunkter og gateknudepunkter på effektfasen kræver egnede differentialprober; et oscilloskopjordklip må ikke forbindes til en flydende switchknude.

1. **Styrekort alene, ARM fjernet:** forsyn med strømbegrænset 5 V. Mål reference og railstrømme. Brug lavspændingskilder som simulator for VFB, VMON, IMON og kommandoer. Ingen effektbus tilsluttes.
2. **CV-servo:** simulér VFB = 1,2 V og sweep VCMD. Kontrollér INJ_NODE ≈ VFB + VCMD og VDIFF ≈ 1,25 V; mål faktiske fejl fra modstandsbelastning og offset. Afbryd og kortslut de relevante lavspændingssignaler enkeltvis.
3. **CC-sløjfe:** simulér IMON omkring ISET og mål CC_OUT samt sink-retningen ved ITH. Brug en begrænset testkilde på ITH; opampens mætning og genindkobling registreres. Dette måler kontrolfunktionen, ikke en færdig belastningsregulering.
4. **Fault-gate:** med simulatorer på alle input, kontrollér hver comparatorgrænse, hysterese hvor relevant, ARM, supervisorens forsinkelse og ENABLE's lave værdi. Sweep AUX5 gennem hele opstart/nedlukning og gentag med signalerne fortsat aktive for at opdage backfeed.
5. **Lille effektprøve:** efter verificeret routet effektprint og afsluttet komponentreview bruges en isoleret, strømbegrænset lav DC-bus og en egnet testlast. Mål CV/CC-overgang, korte lastpulser, shutdown, faktisk udgangsafladning og sløjfestabilitet før højere spænding eller strøm.
6. **Udvidelse:** efter nye beregninger og målinger kan spænding, strøm og temperatur øges trinvist. 100 V / 40 A kontinuerligt kræver endnu en særskilt effekt-, isolation-, strømfordelings- og termisk validering.

RUN slukker switching, men fjerner ikke energien fra udgangskondensatorerne. De eksisterende to 47 µF kondensatorer lagrer nominelt **0,47 J ved 100 V**, før yderligere kapacitet og belastningskapacitet medregnes. Denne energi kan løbe ind i et lille print med strøm større end den indstillede CC, inden converteren når at reagere. En dokumenteret afladning, belastningstilslutning og passende udgangsbeskyttelse kræves for følsomme kredsløb.

## Datablad- og frigivelsesstatus

Primære kilder er de officielle lokale referencer: [LTC3779](../references/LTC3779.pdf), [OPA192/OPA2192/OPA4192](../references/OPA2192.pdf), [INA240](../references/INA240.pdf), [TLV1704](../references/TLV1704.pdf), [TPS3808](../references/TPS3808.pdf), [TPS3700](../references/TPS3700.pdf) og [LM4040-N](../references/LM4040.pdf). [TI SLAAE22](../references/TI_SLAAE22.pdf) dokumenterer principper for feedback-injektion med en anden DAC og en anden forsyning; det validerer ikke denne positive-injektionsservo eller dens dynamik.

INA240A2 i **SOIC-8** bruger IN− ben 1, GND ben 2, REF2 ben 3, NC ben 4, OUT ben 5, VS ben 6, REF1 ben 7 og IN+ ben 8. TSSOP-8 har en anden pinmap og må ikke udskiftes uden korrekt symbol/footprint-review. OPA4192 SOIC/TSSOP-14 har V+ ben 4 og V− ben 11; hvert kanalben skal kontrolleres mod databladet. TPS3700 SOT-6 og WSON-6 har også forskellige pinmaps.

**DFLS1200-7 producentdatablad, forward drop, lækstrøm, kapacitans og det konkrete footprint/pinmap er fortsat frigivelsesblokeringer.** PowerDI-123-repræsentationen følger den tidligere ADI-reference med pad 1 katode og pad 2 anode, men det erstatter ikke producentreview. Den tidligere overvejede BAT54 er ikke valgt i dette kredsløb. En generisk KiCad-diode eller en anden producents lignende navn dokumenterer ikke den indkøbte komponent.

Yderligere frigivelsesblokeringer er loopstabilitet, tolerancebudget for CV/CC/OVP, opstart i hele indstillingsområdet, manglende fejllås/udgangsafbryder, manglende lavstrømsområde, reference- og rail-off backfeed, connectorfejl, routet PCB/DRC, effektkomponenternes termiske review og hardwarevalidering. Fire parallelle faser kræver aktiv, dokumenteret strømbalancering; en fælles clock eller fire kopier af denne regulator opfylder ikke dette krav. **0 V-regulering, milliamperebeskyttelse og 40 A kontinuerlig drift er endnu ikke dokumenteret.**

## De faktiske stik og testpunkter

Alle værdier refereres til styrekortets PGND. Kortet ligger på samme flydende sekundærside som effektfasen; PGND må ikke automatisk forbindes til PE, USB-jord eller et jordet oscilloskopklip.

| Stik | Pin | Net / funktion |
|---|---:|---|
| J1 | 1 / 2 | Ekstern reguleret AUX5 / PGND |
| J2 | 1 / 2 / 3 | VCMD / ISET / PGND |
| J3 | 1 / 2 / 3 / 4 | VFB / ITH / ENABLE / PGND |
| J4 | 1 / 2 / 3 | KS_HIGH fra DUT-retur / KS_LOW fra fase-PGND / PGND |
| J5 | 1 / 2 | VOUT_SENSE / PGND; højspændingssense, ingen belastningsstrøm |
| JP1 | 1 / 2 | AUX5 / ARM_FEED; normalt åben jumper |

J3 er et integrationsinterface, ikke en godkendt færdig ledningsadapter. Den faste effektfase har VFB på TP9, ITH på TP10 og ENABLE på J4.1 gennem sin 100 Ω RUN-seriemodstand. Der må ikke samtidigt være en anden enable-driver tilsluttet. Feedback, sense- og returkabler skal gennemgås, før den uændrede effektfase kobles til et programmerbart forsøgssetup.

| Testpunkt | Net | Forventet ved gyldig normal drift |
|---|---|---|
| TP1 | AUX5 | Ekstern 5 V; nominelt driftskrav 4,75–5,25 V |
| TP2 | PGND | Lokal flydende reference |
| TP3 | REF25 | Cirka 2,5 V; referencebias og alle belastninger skal kontrolleres |
| TP4 | VCMD | 0–1,2 V, højere kommando giver lavere udgangsspænding |
| TP5 | INJ_NODE | Cirka VFB + VCMD, når servo og diode arbejder |
| TP6 | VFB | Cirka 1,2 V under CV efter soft-start; lavere under andre driftsforhold |
| TP7 | ISET | 0,1 V + 0,05 V/A × ønsket strøm; hardware slukker under cirka 0,11062 V |
| TP8 | IREF | Cirka 0,1 V bufferet til begge INA240-referencepins |
| TP9 | IMON | Cirka 0,1 V + 0,05 V/A × faktisk positiv DUT-strøm |
| TP10 | CC_OUT | Dynamisk, lavere når CC-sløjfen kræver strømreduktion; ingen fast normalværdi |
| TP11 | ITH | Dynamisk current-command; pin-grænser følger lokal LTC3779 V5 |
| TP12 | ENABLE | Cirka 2,38 V med ARM og alle grænser gyldige; under 1,1 V kræves ved fault |
| TP13 | VDIFF | Cirka 1,25 V; nominelt vindue 1,14679–1,35501 V |
| TP14 | VMON | VOUT/40,7; cirka 2,457 V ved 100 V og 2,5 V ved nominel OVP |
| TP15 | REF_UV | REF25/5,99; cirka 0,4174 V ved korrekt reference |
| TP16 | REF_OV | REF25/6,6; cirka 0,3788 V ved korrekt reference |

VMID findes på R14/R15 og har ikke eget TP i denne revision. KS_HIGH/KS_LOW findes på J4. Test først sensorpolariteten med kendt lav strøm eller en millivoltsimulator. Ved 1 A skal IMON stige cirka 50 mV over sin nulstrømsværdi; omvendt fortegn eller konstant nulpunkt betyder, at reguleringen ikke må aktiveres.

## Tab af styreforsyning er stadig et frigivelsespunkt

Med AUX5 reelt på 0 V og intakte jordforbindelser giver R25 parallelt med fasens 100 kΩ en nominel ENABLE-værdi omkring 23 mV fra LTC3779's 2,5 µA pull-up. Dette er en statisk beregning. Supervisorens RESET og comparatorerne er ikke funktionelt specificeret i hele området ned til 0 V.

TLV1704-databladets note til absolute maximum beskriver inputclamps til forsyningsrails og højst 10 mA injektion. Den separate VOUT-divider kan derfor ved levende 120 V udgang sende strøm ind i en slukket AUX5. Gennem dens 397 kΩ øvre kæde er strømmen under 0,303 mA ved en antaget clamp nær jord, før bundmodstanden og faktisk diode-/railspænding medregnes. Det er under den nævnte pin-strømgrænse, men kan stadig oplade en let belastet rail og ændre ENABLE. En pin-strøm under absolute maximum er ikke bevis for korrekt fejlrespons.

ITH kan også gennem 470 Ω, D2 og opampens outputbeskyttelse sende strøm mod en slukket AUX5. Diodens VF, ITH's faktiske kildeegenskaber og opampens strømløse output gør, at denne vej endnu ikke har en kvalificeret øvre strøm-/railspændingsgrænse. VFB- og kommandoindgange har yderligere passive veje. Der er ingen implementeret, uafhængig rail-off signalafbrydelse eller kvalificeret udgangsfejllås.

Afprøv derfor AUX5-sweep og brat afbrydelse med signalerne fortsat aktive på en energibegrænset simulator. Registrer railspænding, clampstrømme, ENABLE, RUN, ITH og udgang samtidigt. Live-bus prøver og tilslutning af følsomme DUT er ikke frigivet på grundlag af den statiske pulldownberegning.

## CC-kompensation og layoutstatus

R8 = 20 kΩ, R9 = 10 kΩ og C8 = 1 nF er fortsat foreløbige værdier. Den parameteriserede model i `docs/power-analysis.md` finder omkring 5,9° og −0,4° fasemargin i to antagne plant-scenarier. Modellen er ikke en identificeret LTC3779-sløjfe, men viser, at værdierne ikke kan krediteres som robuste. 10 nF og 100 nF undersøges som følsomhedsændringer, uden at der påstås en valideret erstatning.

Mål eller identificér den faktiske strømplant, diodens clampautoritet, strøm-sensorens filter og opampens mætning/anti-windup; beregn derefter kompensation og mål sløjfen både i CV, CC og overgangen. Kortets beståede CAD-DRC løser ingen af disse reguleringsspørgsmål.

## Efterprøvet reference- og grænseberegning

`scripts/control_limits.py` læser de aktuelle modstandsværdier fra BOM og kontrollerer dividerbelastning, ideelle statiske startpunkter, ENABLE og kommandovinduer. REF25's nominelle belastning ved VCMD = 0 er cirka 694,2 µA, inklusive VMID-belastning. Med den oprindelige R13 = 2,49 kΩ bliver shuntreferencens resterende strøm cirka 309,8 µA ved AUX5 = 5 V og 209,4 µA ved 4,75 V.

Et konservativt brownout-scenarie bruger AUX5 = 4,557 V, REF25 = 2,525 V som en bred antagelse, 1 % høj biasmodstand, 0,1 % lave dividerkæder, 5 % lav R5 og 0,5 µA ekstra belastning. Det giver cirka 104,3 µA tilbage mod en 65 µA minimumsstrømsgrænse over temperatur. Der er cirka 39,3 µA statisk reserve i dette scenario. R13 beholdes derfor på 2,49 kΩ; en tidligere summeringsfejl gav cirka 796 µA belastning; den blev rettet ved en uafhængig ledger over alle aktuelle REF25-grene.

De nominelle comparatorgrænser er ikke præcise strøm-/spændingsindstillinger. Med den angivne comparatoroffset, bias og dividerfejl giver det lave ISET-vindue som eksempel cirka 92–333 mA i stedet for én fast 212 mA grænse; referencedrift, sensor- og kommando-kildefejl er ikke alle med i intervallet. Det er yderligere grund til at holde små prøveprint uden for denne revisions strømområde.

De statiske cold-start-punkter passerer VDIFF og IMON-low ved VCMD = 0, 0,6 og 1,2 V i den ideelle model. Det beviser, at den konkrete gamle DC-startlåsning er fjernet; tidsforløb, backfeed og faktisk load-start er stadig utestede. Resultaterne ligger i `exports/analysis/control_limits.json`.
