# Effektfase: LTC3779, fast 99,6 V og 10 A som udviklingsmål

Denne del er et konkret **forskningsudkast til én effektfase**. Diagrammet er i `design/power/power_phase.kicad_sch`, controllerdelen i `control.kicad_sch`, og den komplette stykliste i `bom/power-phase.csv`. PDF-diagrammet er `exports/power/power_phase.pdf`. Printfilen indeholder komponentplacering og netnavne, men **ingen kobberforbindelser**. Den kan ikke fungere eller fremstilles som et færdigt effektprint.

Brugerens slutmål er stadig en galvanisk isoleret/flydende 230 V AC → **0–100 V / 0–40 A** laboratorieforsyning. Dette udkast regulerer nominelt **fast 99,6 V**, har et uverificeret udviklingsmål på **10 A**, og har en intern, fast middelstrømsgrænse på cirka **12,5 A**. Det har endnu ingen justerbar CV/CC, aktiv 0 V-regulering, milliampereområde til små opamp-print, isoleret AC/DC-indgang, udgangsafbryder eller verificeret strømfordeling mellem faser. Fire kopier af printet dokumenterer ikke en 40 A forsyning.

## Dokumenteret controller og reference

LTC3779 understøtter 4,5–150 V indgang og 1,2–150 V udgang, fire N-kanal MOSFETs og både buck- og boost-drift. Den officielle DC2456A-reference leverer **48 V / 10 A**, og dens dokumenterede egenskaber må ikke overføres direkte til dette ændrede 99,6 V-kredsløb.

| Egenskab | Verificeret i LTC3779-databladet | Betydning for udkastet |
|---|---|---|
| VIN og VOUT | 150 V spændingsområde; se absolutte grænser og elektriske specifikationer, s. 2–3 | En 100 V udgang er inden for controllerens område |
| VFB-reference | 1,2 V nominelt, 1,188–1,212 V; s. 3 | Referencen alene bidrager ±1 % til udgangsspændingen |
| Gateforsyning | DRVSET vælger 6–10 V; s. 11 | DRVSET = V5 giver nominelt 10 V DRVCC |
| Middelstrømsgrænse | IAVGSNSP–IAVGSNSN = 47,5–52,5 mV, typisk 50 mV; s. 3, 17, 21 | 4 mΩ giver cirka 12,5 A; der findes ingen justerbar CC-pin |
| Buck-strømgrænse | Valley-strømgrænse 70–110 mV, typisk 90 mV; s. 3 og 18–21 | 6 mΩ kræver spole- og MOSFET-dimensionering efter værste grænse |
| Frekvens | 50–600 kHz; PLLIN kan synkronisere til ekstern clock; s. 12, 22 | 37,4 kΩ giver omtrent 101,8 kHz efter databladets approksimation |
| Parallelle faser | Ekstern clock er dokumenteret; en strømfordelingsbus er ikke dokumenteret | Firefasekobling er en separat reguleringsopgave |
| Soft start | SS lades med nominelt 5 µA og påvirker referencen under opstart; s. 11, 15, 17 | 100 nF giver cirka 24 ms til 1,2 V; SS er ikke dokumentation for permanent 0 V-regulering |

**LTC3895 er fravalgt til direkte 100 V udgang**: dens officielle datablad angiver 0,8–60 V udgang og en 65 V absolut grænse på strøm-sense-benene. En høj indgangsspændingsrating er ikke en høj udgangsspændingsrating.

Controllerens lokale footprint er afledt af KiCads HTSSOP-38, 4,4 × 9,7 mm, 0,5 mm pitch og 2,74 × 4,75 mm exposed pad. **Positionerne 23, 25, 27, 29, 31, 33 og 35 er fysisk fjernet**, som databladets FE38(31)-tegning på s. 36 angiver. Exposed pad er **ben 39, PGND**. Der er 31 fysiske ledere plus exposed pad, i alt 32 elektriske ben. Den lokale pinmap bruger de korrigerede switch-/gate-ben i Rev A, s. 12. Landpattern, loddepasta, varmevias og fabtolerancer kræver stadig review.

## Tilslutninger

Alle nedenstående GND-forbindelser tilhører den **flydende DC-sekundærside**. Et jordet instrument, USB-interface eller en PE-forbindelse kan ophæve den flydende udgang.

| Stik | Ben | Signal | Funktion |
|---|---:|---|---|
| J1 | 1 | VIN | Ekstern galvanisk isoleret DC-indgang; udviklingspunkt 110–115 V, højst 120 V |
| J1 | 2 | PGND | DC-indgangens retur og fasejord; ikke PE |
| J2 | 1 | VOUT | Fast nominelt 99,6 V efter middelstrømsshunten |
| J2 | 2 | PGND | Udgangsretur i dette enkeltfaseudkast |
| J3 | 1 | AUX12 | Ekstern isoleret 12 V hjælpeforsyning på samme flydende side |
| J3 | 2 | PGND | Hjælpeforsyningens retur |
| J4 | 1 | ENABLE | 3,3 V enable fra en ekstern fixture; lav betyder shutdown |
| J4 | 2 | SYNC | Valgfri ekstern clock til PLLIN, inden for V5-pinens grænser |
| J4 | 3 | PGOOD | Open-drain status, trukket op til **V5 ≈ 5,5 V**; ikke direkte 3,3 V-kompatibel |
| J4 | 4 | PGND | Interface-reference |
| L1's terminaler | 1 / 2 | SWA / SWB | Tilslutning til en ekstern 150 µH spole; footprint er en foreløbig terminalplacering |

J1, J2 og L1 bruger foreløbige terminal-footprints. Der er endnu ikke valgt og verificeret et konkret stik til spænding, strøm, kontaktmodstand og temperatur. L1-symboler og terminaler repræsenterer **én ekstern spole**, ikke en printvikling.

12 V hjælpen skal være til stede før høj spænding/enable og fortsætte, indtil effektbussen er fjernet. En automatisk hardware-interlock ved tab af AUX12 er **ikke implementeret**. Det interne VIN-forsynede LDO må ikke antages at kunne levere gateeffekten fra 120 V uden en termisk beregning.

## Hvad delene gør

| Referencer | Faktiske værdier i diagrammet | Funktion og begrænsning |
|---|---|---|
| U1 | LTC3779EFE#PBF | Fire-switch controller med spændings- og middelstrømsregulering. Ingen integreret isolation |
| Q1–Q4 | BSC110N15NS5, referencekandidater | Q1/Q2 danner indgangens halvbro; Q3/Q4 udgangens halvbro. Infineons eget datablad er nu hentet: 150 V, RDS(on) højst 11 mΩ ved VGS = 10 V og Tj = 25 °C; gate ben 4, source ben 1–3, drain ben 5–8. Anvendelse på begge broer ved 99,6 V er fortsat ikke termisk verificeret |
| L1 | 150 µH, ekstern; Irms ≥15 A, varm Isat ≥25 A som krav | Lagrer energi mellem SWA og SWB. Fabrikant, kernetab, DCR, varm mætningsgrænse og fysisk opbygning mangler |
| R1, R2 | 12 mΩ hver, ±1 %, ≥2 W; parallelkoblet til 6 mΩ | Lavside-shunt til hurtig cycle-strømmåling. Kelvin-traces kræves. Begge nederste MOSFETs returnerer via denne shunt |
| R3, R4 | 8 mΩ hver, ±1 %, ≥2 W; parallelkoblet til 4 mΩ | Udgangsshunt til den interne middelstrømsgrænse, nominelt 12,5 A. Dette er en overlastgrænse, ikke brugerens justerbare strømindstilling |
| C1, C2 | 47 µF / 200 V hver; ≥105 °C som krav | Indgangens bulk-kondensatorer. Samlet ripple-rating ≥5 A ved relevant temperatur/frekvens kræves; serie/ESR/MPN mangler |
| C3, C4 | 47 µF / 200 V hver; ≥105 °C som krav | Udgangens bulk-kondensatorer. ESR, ripple, levetid og dynamik mangler |
| C5–C8 | 1 µF / 250 V X7R, Murata GRM55DR72E105KW01L fra ADI-BOM | Lokal højspændingsafkobling. Den effektive kapacitet falder med DC-bias |
| R5 | 0 Ω | Binder NDRV til DRVCC for at deaktivere den eksterne NDRV-pass-regulator som beskrevet i databladet |
| R6, R7 | 100 kΩ RUN-pulldown; 100 Ω enable-serie | Default shutdown; 2,5 µA intern pull-up giver cirka 0,25 V over 100 kΩ, under shutdown-grænsen |
| R8 | 100 kΩ | Holder PLLIN lav, når ingen ekstern clock er tilsluttet |
| R9 | 37,4 kΩ / 1 % | Programmerer omtrent 101,8 kHz; frekvens skal måles |
| R10 | 10 kΩ | PGOOD pull-up til 5,5 V V5 |
| R11–R14 | 0 Ω gate-jumpere | Forbinder TG1/BG1/BG2/TG2 til Q1/Q2/Q3/Q4. Endelige gate-modstande kræver ringing-, switchingtab- og deadtime-målinger |
| R15, R16, C15 | 100 Ω i hver sensevej; 220 pF / 100 V C0G differentialt | Filter for den hurtige cycle-strømmåling, direkte Kelvin fra shunten |
| R17, R18, C16 | 100 Ω / 150 Ω; 1 µF / 250 V X7R differentialt | Filter for middelstrømsmåling. De forskellige modstande kompenserer førsteordens biasstrømme på 15/10 µA ved common mode over cirka 4 V; s. 21 |
| R19 | 1 kΩ | Fører VOUTSNS til Q4's drain PREOUT, som databladets pinfunktion kræver |
| R20, R21, R22 | 410 kΩ + 410 kΩ / 0,1 %; 10 kΩ / 0,1 % bundmodstand | Fast feedback: 1,2 × (1 + 820 kΩ/10 kΩ) = **99,6 V nominelt**. Referencetolerance, ratiofejl og kalibrering er separate bidrag |
| R23, R24, R25 | 499 kΩ + 499 kΩ / 0,1 %; 10 kΩ / 0,1 % bundmodstand | VINOV-divider: nominelt 129,0 V. Comparatorens tolerance giver cirka 118,94–139,10 V før dividerfejl. Dette er ingen præcis uafhængig overspændingsbeskyttelse |
| R26, C17, C18 | 10 kΩ; 10 nF / 50 V; 100 pF / 50 V | Startværdier for ITH-kompensation fra ADI-demo. Det ændrede L/C/VOUT kræver ny sløjfeanalyse; værdierne dokumenterer ikke stabilitet |
| C9, C10, C11 | 4,7 µF / 16 V; 4,7 µF / 10 V; 1 µF / 50 V | Afkobler henholdsvis DRVCC, V5 og AUX12 |
| C12 | 100 nF / 50 V | Soft start, nominelt 24 ms til 1,2 V |
| C13, C14 | 220 nF / 16 V X7R | Bootstrap-kondensatorer BST1–SWA og BST2–SWB |
| D1, D2 | DFLS1200-7, 1 A / 200 V, PowerDI-123 | Lader bootstrap-kondensatorerne fra DRVCC. ADI-demo angiver delen og rating; eget fabrikant-/footprint-review mangler |
| TP1–TP19 | Testpunkt-pad Ø2 mm, 1 mm hul | Planlagt adgang til spændinger og kontrolsignaler; de åbne TP-forbindelser er med i den delvise routingrapport |

Topologien anvender samme PGND-net til signal- og effektretur, men den endelige routing skal give adskilte strømbaner og en kontrolleret Kelvin-reference. Ét fælles netnavn betyder ikke, at en vilkårlig ground-pour er korrekt.

## Beregninger, der styrer næste komponentvalg

Ved 120 V ind og 99,6 V ud er ideel buck-duty 0,83. Med 150 µH og 101,8 kHz er spoleripple cirka **1,11 A p-p**. Det maksimale idealiserede ripple over buckområdet ved 120 V er cirka **1,96 A p-p**, omkring 60 V ud. Det sidstnævnte er et dimensioneringscheck; denne revision har fast 99,6 V, ikke en dokumenteret indstilling til 60 V.

| Størrelse | Beregning / resultat | Begrænsning |
|---|---|---|
| Cycle-shunt ved 10 A | Spændingsmagnituden er 6 mΩ × 10 A = 60 mV; samlet 0,60 W; 0,30 W pr. modstand | Layout, tolerance og varm rating kræves |
| Typisk valley-strømloft | 90 mV / 6 mΩ = 15 A | Ikke samme som middel- eller peakstrøm |
| Højeste specified valley-loft | 110 mV / 6 mΩ = 18,33 A; med 1 % lav shunt og 1,96 A ripple cirka **20,5 A peak** | Beregning efter databladets strømgrænse; ikke en transientgaranti eller SOA-test |
| Udgangsshunt ved 10 A | 4 mΩ × 10 A = 40 mV; samlet 0,40 W; 0,20 W pr. modstand | Den interne CC-grænse nås først over 10 A |
| Nominelt middelstrømsloft | 50 mV / 4 mΩ = 12,5 A | Controlleren har ingen direkte justerbar CC-pin |
| CC-grænse med specificeret threshold og 1 % shunt | 47,5 mV / 4,04 mΩ = 11,76 A; 52,5 mV / 3,96 mΩ = 13,26 A | Bias-/filterfejl og drift kommer oveni |
| Input-capacitor RMS ved 99,6 V / 10 A | 10 × √(0,83 × 0,17) ≈ 3,76 A | Værste ideelle buckpunkt giver 5 A; cap-bank skal dimensioneres efter dette |
| Nominel udgangskapacitet | 2 × 47 µF + 2 × 1 µF = 96 µF før tolerance/bias | Ikke 98 µF; kun to af de fire 1 µF-kondensatorer sidder på udgangen |
| Energi ved 99,6 V | ½ × 96 µF × 99,6² ≈ **0,476 J** | Kan afgives til et lille print før buckens CC reagerer |
| 10 A lastspring i 100 µs, kun kondensatoren | 10 A × 100 µs / 96 µF ≈ 10,4 V | Illustrerer behov for sløjfevalidering og ændret C; ikke en målt performance |
| Spoleenergi ved 20,5 A | ½ × 150 µH × 20,5² ≈ 31,5 mJ | Varm mætning og fejlstrøm skal testes |

MOSFET-kandidaternes 150 V klasse og controllerens 150 V grænser giver højst 30 V mellem 120 V DC og mærkegrænsen. Denne margin inkluderer endnu ingen målte oversving. En snubber, clamp eller lavere busspænding må vælges efter faktisk switch-node-måling og fabrikantdata; ingen komponentrating eller tidsbudget gør udkastet verificeret.

Ved den valgte 110 V front-end er 100/110 = 90,91 % ideal duty tæt på LTC3779's 91,67 % buck-only-grænse på s. 15. Busfald, tolerancer og tab kan derfor føre driften ind i buck/boost-området, hvor begge halvbroer skifter. Ideelle buckripple- og tabstal er referenceberegninger, ikke en beskrivelse af alle switchforløb ved den højeste laboratorieindstilling. Dette skal indgå i MOSFET-tab, kompensation og den endnu uløste firefasestrømfordeling.

Infineons **BSC110N15NS5 Rev. 2.6, 7. november 2022** er nu kontrolleret direkte. Databladets s. 1 angiver PG-TDSON-8 og pinout: source 1–3, gate 4, drain 5–8. Det fælles drain er repræsenteret som pad 5 i KiCad-footprintet. S. 3 angiver RDS(on) typisk 9 mΩ, højst 11 mΩ ved VGS = 10 V, ID = 38 A og Tj = 25 °C; maksimum bliver 12,7 mΩ ved 8 V under den angivne test. VGS-grænsen er ±20 V og maksimal Tj er 150 °C. En ideelt konstant 10 A gennem én fuldt tændt transistor giver allerede 1,1 W med 25 °C-maksimumsværdien, før temperaturstigning og switchingtab.

RθJC er højst 1 K/W. RθJA = 50 K/W gælder kun databladets 40 × 40 × 1,5 mm FR4-testkort med 6 cm², 70 µm kobber på drain, lodret i stille luft. De 76 A gælder TC = 25 °C; ved TC = 100 °C angives 48 A. SOA-kurven på s. 5 gælder TC = 25 °C og enkeltpuls, D = 0, og skelner mellem DC og pulslængder. Disse tal frigiver ikke det uafsluttede PCB til 10 A eller fejldrift. Det opdaterede package-outline på s. 9, PG-TDSON-8-U08, skal stadig sammenholdes med landpattern og fabrikantens montagekrav.

Ved IAVGSNS-common-mode under cirka 4 V ændrer biasstrømmene sig og kan nå cirka −300 µA ved 0 V; se databladets s. 21–22. Derfor må denne fast-CC-løsning ikke omtales som verificeret strømbegrænsning ved kortslutning eller som en præcis lavstrømsforsyning. Til små opamp-print mangler både et passende måleområde og en begrænser/afbryder efter den energilagrende bulk-kapacitans.

## Testpunkter og forventede signaler

Tabellen beskriver **teoretiske udviklingsmålinger efter en fuldt routet og gennemgået prototype**. Det eksisterende print er ikke forbundet og skal ikke spændingssættes. Brug måleudstyr, hvis spændings- og common-mode-rating passer til den flydende del. High-side gate måles i forhold til sin egen source; almindelig scope-ground på PGND kan forbinde udgangen til PE.

| Testpunkt | Net | Forventning / fejlfinding |
|---|---|---|
| TP1 | VIN | 110–115 V udviklingspunkt, aldrig over 120 V; se busfald og oversving |
| TP2 | VOUT | Cirka 99,6 V i CV efter soft start, med reference-/dividerfejl; 10 A-funktion ikke bevist |
| TP3 | PGND | Reference på den flydende DC-side, ikke PE |
| TP4 | SWA | Buck-switch-node, pulser mellem cirka CS-retur og VIN; ringing skal måles differentialt |
| TP5 | SWB | Tæt ved udgangsspændingen i ren buckdrift; skifter i buck/boost-overgang og boostdrift |
| TP6 | DRVCC | Nominelt 10 V i forhold til PGND; start og droop er vigtige ved gatefejl |
| TP7 | V5 | Cirka 5,5 V; under cirka 4,35 V typisk controller-UVLO ved opadgående forsyning |
| TP8 | SS | Cirka 5 µA / 100 nF = 50 V/s ramp; 24 ms til 1,2 V, fortsætter derefter højere |
| TP9 | VFB | Cirka 1,2 V i korrekt CV; højere/lavere med OVP, CC eller fejl |
| TP10 | ITH | Dynamisk analog reguleringssignal inden for pinens V5-grænser; ingen fast forventet spænding. Intern CC trækker ITH ned |
| TP11 | CS | Buck-freewheel gennem Q2: CS er cirka **−60 mV** mod PGND ved 10 A, med ripple; begge lowside-switches slukkede: nær 0 V. Under boost/lowside-retur er polariteten positiv. Mål mod shuntens egen PGND-Kelvin-retur; sense-benene må ikke byttes |
| TP12 / TP13 | IAVGP / IAVGN | Høj common mode nær 99,6 V; differentialt omtrent 40 mV ved 10 A og 50 mV ved nominelt CC-loft, med filter-/biasfejl |
| TP14 | RUN | Default cirka 0,25 V; lavere end 1,1 V shutdown, højere end 1,2 V typisk enable; ekstern fixture bruger 3,3 V |
| TP15 | PGOOD | Cirka 5,5 V når open-drain ikke trækker lav; lav uden for VFB-vinduet ±10 %. Ikke en uafhængig OVP |
| TP16 | GA, Q1 gate | Omtrent 10 V over Q1's egen SWA-source, med switching; aldrig vurder kun i forhold til PGND |
| TP17 | GB, Q2 gate | Gate-source måles mod Q2's CS-source; lavside switching/deadtime |
| TP18 | GC, Q3 gate | Gate-source måles mod Q3's CS-source; normalt lav i ren buck, aktivitet ved buck/boost |
| TP19 | GD, Q4 gate | Omtrent 10 V over Q4's egen SWB-source i buck; måles differentialt |

## Fejlsøgning og udviklingsrækkefølge

1. **Før en hardwareprototype:** fremskaf manglende databladssæt; vælg spole, bulk-kondensatorer, shunter, stik, køling og beskyttelser. Rout alle strøm-, sense-, bootstrap- og gateforbindelser og gennemfør review. Den medfølgende placering kan ikke bruges direkte.
2. Verificér med effektbussen fjernet, at ENABLE holdes lav, at AUX12 er korrekt isoleret, og at controlleren ikke utilsigtet starter. Auxiliary-interlock skal konkret implementeres.
3. Kontroller DRVCC/V5, gate-reference, korrekt fysisk pinout, polaritet, Kelvin-ledninger og fravær af gate-overlap på en gennemgået fixture. Første funktionstest skal bruge begrænset energikilde og lasten passende til designet.
4. Efter gradvis energiøgning kontrolleres CV, middel- og cycle-strømloft, input-OVLO, soft start, både CV/CC-sløjfestabilitet, lastspring og fejlgenstart. R26/C17/C18 er kun startværdier; loop-måling skal bestemme de endelige værdier.
5. Fuld spænding, 10 A, kontinuerlig drift, varm spole, MOSFET-tab, blæserfejl og kortslutning kræver fysisk test. Denne cloudopgave har ikke gennemført disse test.
6. Før 4 kW-udvidelse skal 0–100 V, præcis justerbar 0–40 A CC, lavstrømsbeskyttelse, udgangsafbryder, discharge, uafhængig OVP/OCP/OTP, AC/DC-isolation og dokumenteret fasestrømfordeling designes og testes særskilt.

## Kontrolleret filstatus

- KiCad 9.0.2 indlæser og eksporterer det native to-siders diagram og printplaceringen.
- ERC med alle alvorligheder: **0 fejl/advarsler** i denne revisionsrapport.
- Eksporteret netliste og samtlige fysiske padnumre stemmer: **75 komponenter, 175 logiske pin/pad-forbindelser, 38 net**. Controllerens 32 forbindelser og 7 fjernede positioner stemmer med den lokale footprintdefinition.
- PCB er nu **135 × 90 mm i fire lag** med **1551 sporsegmenter og 111 vias**. Hovedstrøm, gate-/bootstrap-forbindelser og Kelvin-grene er routet; **nul åbne forbindelser, nul geometriske overtrædelser og nul paritetsfejl**, samlet **DRC PASS**. Se `docs/power-layout.md` og `exports/power/layout_summary.json`. Controllerens landpattern er rettet efter originalt fabrikantdatablad; pinpitch og nummerering bevares. Ingen fabrikationsfrigivelse; funktion, termik og komponenternes fysiske egnethed er utestet.
- Hardwaretest, termisk test, stabilitet, isolation, 10 A og 4 kW er **ikke gennemført**.
- Der er ikke frigivet Gerber- eller borefiler.

ERC og logisk pin-overensstemmelse fortæller, at filerne er konsistente. De viser ikke, at strømforsyningen fungerer eller er klar til produktion.

## Primære kilder

1. Analog Devices, **LTC3779 Rev A**, officielt datablad, lokalt `references/LTC3779.pdf`: https://www.analog.com/media/en/technical-documentation/data-sheets/ltc3779.pdf — s. 2–4 grænser/pinout; s. 11–12 pinfunktioner; s. 15–18 drift/CV/CC; s. 19–23 dimensionering/strømfiltre/frekvens; s. 25–26 feedback/OVLO; s. 36 package; s. 38 typisk kredsløb.
2. Analog Devices, **DC2456A demo manual**, lokalt `references/LTC3779_DC2456AF.pdf`: https://www.analog.com/media/en/technical-documentation/user-guides/DC2456AF.PDF — s. 1 performance 48 V / 10 A, s. 2 termiske begrænsninger og current-loop-opsætning, s. 8–9 komponentliste, s. 10–11 kredsløb.
3. Analog Devices, **DC2456A-4 schematic**, lokalt `references/LTC3779_DC2456A4_schematic.pdf`: https://www.analog.com/media/en/technical-documentation/user-guides/DC2456A-4-SCH.PDF — MOSFET/pinforbindelser, bootstrap og kompensationsstartværdier.
4. Analog Devices, **LTC3779 produktoversigt**: https://www.analog.com/en/products/ltc3779.html — officielle dokumentlinks.
5. Analog Devices, **LTC3895**, lokalt `references/LTC3895.pdf`: https://www.analog.com/media/en/technical-documentation/data-sheets/3895fa.pdf — udgangsområde og absolut SENSE-grænse; fravalgt til 100 V udgang.
6. Infineon, **BSC110N15NS5 Rev. 2.6**, lokalt `references/BSC110N15NS5.pdf` og `.txt`: https://www.infineon.com/assets/row/public/documents/24/49/infineon-bsc110n15ns5-datasheet-en.pdf — s. 1 pinout, s. 3 spænding/modstand/termiske grænser, s. 5 SOA, s. 9 package-outline. Fundet via den officielle produktside https://www.infineon.com/part/BSC110N15NS5 og hentet med normal HTTPS den 9. oktober 2026. SHA256: `ba0b880c5ae9919b1b32bdae90ea848e70739c4be5f2247b96e3c1b86fa45576`.

Direkte fabrikantdatablade for **Diodes Incorporated DFLS1200-7** og enkelte valgte passivdele er endnu ikke hentet/verificeret. Normale HTTPS-forsøg til `https://diodes.com/part/view/DFLS1200` og `https://diodes.com/assets/Datasheets/DFLS1200.pdf` den 9. oktober 2026 omdirigerede til `www.diodes.com` og gav HTTP 403. Infineons aktuelle produkt- og assets-adresser ovenfor virker nu; ældre eller omdirigerede adresser etablerer ikke databladets tilgængelighed. Kritiske krav til **150 µH-spolen, 47 µF/200 V-kondensatorerne, shunterne og effektterminalerne** har endnu ingen endelig fabrikant/MPN. ADI-reference-BOM'en erstatter ikke de endnu manglende producentdatablade; det hentede MOSFET-datablad erstatter ikke elektrisk, termisk eller fysisk validering.
