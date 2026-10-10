# Afsluttende afleveringsstatus

Revision: 10. oktober 2026. Arbejdet er fortsat direkte i det eksisterende SWM-PORWER-SUP. Målet er stadig 230 V AC på 32 A-kreds til galvanisk isoleret, flydende 0–100 V / 0–40 A laboratorieudgang. **Den samlede 4 kW-forsyning er endnu ikke et færdigt eller frigivet hardwaredesign.**

## 1. Færdigt CAD-arbejde

Målekortet, det eksperimentelle CV/CC-styrekort og den eksisterende LTC3779-effektfase har native diagrammer og forbundne PCB'er. Effektkortet er firelaget 135 × 90 mm; de tidligere åbne forbindelser og geometriske fund er rettet. Bootstrap C14 sidder på bagsiden. TG1 er kortet fra 43,46 til 28,38 mm; driver–R11–Q1 har cirka 32,0 mm routet kobber, og gate/source-sløjfen kræver fortsat fysisk review. Controllerens landpattern er korrigeret efter originalt ADI-datablad. Styrekortets INA240REF1/REF2-navne og OPA4192/TLV1704-databladsmetadata er rettet uden ændring af elektriske net.

Netdelen har et native chassisdiagram for to RSP-3000-48, AC-parallelindgang, PE, lokale sense-/enableledninger og beskyttelseskrav. Der er ingen net-PCB.

Det nye fasestrømstudie er tegnet i `design/control/studies/phase_sensor_study.kicad_sch`. Én kanal viser AMC3302, ekstern 2 mΩ-Kelvin-shunt, differentialforstærker, PI-gren og separat NMOS-sink til én lokal ITH. Det er **ikke integreret i de routede kort**; der er intet fasestrømstudie-PCB eller færdigt firefaset effektkort.

Hoved-BOM har 206 poster. Den supplerende kritiske matrix har 85 poster, inklusive alle 14 valgte IC-, MOSFET- og modulreferencer. Studieskemaet har 47 separate BOM-poster med både énkanals- og firefasesystemantal. Ubestemte spoler, kondensatorer, shunter, terminaler og beskyttelsesdele er krav, ingen godkendte indkøbsdele.

## 2. Godkendte automatiske kontroller

Alle tre hoved-PCB'er består ERC/DRC med alle alvorligheder, nul utilsigtede åbne forbindelser og nul schematic-parity-fund. Chassisdiagrammet består ERC. Inventarkontrollen matcher reference, værdi og footprint mellem diagramnetliste, BOM og PCB. Alle fysiske nummererede pads kontrolleres før grupperingen af gentagne pinnumre: 52 på målekortet, 191 på effektkortet svarende til 175 logiske pins og 211 på styrekortet.

De negative HV-regelkontroller bruger midlertidige kopier. Måle-/styrekortets 100 mm-kontrol og effektkortets 5 mm-kontrol producerer faktiske clearancefund; originale filer forbliver uændrede. Effektlayoutets generator genafspiller den gemte slutgeometri, og en isoleret regeneration er kontrolleret. Det dokumenterer reproducerbar CAD og aktive regler, ikke isolation eller switchingfunktion.

Studieskemaets egen ERC og 113 forventede pin/net-noder kontrolleres særskilt. Masterstatus ligger i `exports/verification/project_status.json`; de faktiske delrapporter, originale kilder og scripts medfølger. Historiske pre-route-rapporter er bevaret med særskilte navne og må ikke læses som aktuelle resultater.

Manual og ZIP genereres fra de aktuelle filer. PDF'en omfatter dansk forklaring, indhold, testpunkter, PCB-visninger, beregninger, BOM, kildeoversigt og native diagramappendikser. ZIP-integritet og afleveringsindhold kontrolleres efter pakning.

## 3. Teoretiske beregninger

Det oprindelige aktuelle budget på **601,67 W varme** bruger 4 kW udgang, antaget 95 % DC-regulator, 91,5 % typisk AC/DC og typisk PF 0,95. Det giver 4601,67 W AC og 21,06 A ved 230 V. DC-regulatortabet på 210,53 W er allerede med i tallet; MOSFET-/spole-/shunttab skal ikke lægges oveni samme 95 %-budget uden at ændre systemgrænsen. Budgettet er ingen målt virkningsgrad eller garanti ved modulers faktiske belastning.

Den nye betingede busafbrydelse tilføjer faste serie-/switchtab uden for denne regulatorgrænse. Med 50 mΩ modstand og antaget 11 mΩ varm switchbank giver en konsistent effektberegning 39,13 A fra 110 V, 107,61 V ved regulatoren og 93,38 W ekstra busvarme. Inklusive ekstra AC/DC-tab stiger scenariets varme til **703,73 W**; modstandens øvre budget giver **708,11 W**. Faktiske komponenter, køling og tab mangler kvalifikation. Ved 100 V ud bliver ideal duty 92,93 %, over LTC3779's buck-only-grænse; reel buck/boost-effektivitet og stabilitet skal verificeres.

Ripple, varme, tab, shunttolerance, lagret kondensatorenergi, spændingsdividere og referencebelastning er reproducerbare i Python. R13 er bevaret på 2,49 kΩ: den korrigerede REF25-belastning er 694,211 µA, og det konservative statiske scenarie giver 104,30 µA shuntstrøm mod 65 µA minimum. Det er ikke opstarts-/rail-off-validering.

INA190A3 med 1 Ω / 20 mA eller 0,1 Ω / 200 mA giver en bedre dimensioneringsretning for små strømme. Et konservativt scenarie ved 1 mA giver cirka 0,063 mA fejl på 1 Ω-området, mod 0,580 mA på 0,1 Ω. Ingen af disse strømområder er implementeret eller kalibreret. Et pass-element efter bulk og en lille DUT-kapacitans er nødvendige for at begrænse upstream-energi; energien efter elementet kan stadig aflade direkte i DUT.

## 4. Simulerede resultater

Fire separate fasestrømservoer konvergerer i den antagne model til cirka 9,946 / 10,055 / 9,968 / 10,032 A. Den resterende forskel følger sensor-/gainfejl. Modellen demonstrerer CV omkring 100 V og CC omkring 40 V ved 1 Ω-last samt samlet låst OFF ved uventet fasefejl. Kontrolleret tre-fasedrift har højst 30 A; en defekt fase må ikke automatisk medføre 13,33 A i de tre andre.

De ni antagne faseservo-plants giver mindst 56,6° model-fasemargin. Det separate lavstrømsstudie giver mindst 55,69° og op til 294 ms indsvingning. Sidstnævnte er alt for langsomt som eneste hurtige DUT-beskyttelse. Ingen af modellerne bruger en verificeret LTC3779-/MOSFET-SPICE-model eller dokumenterer fysisk CV/CC-overgang. Modellens anti-windup, fault-latch og OFF-tracking er antagne funktioner, som ikke er komplet tegnet i native studiet.

Busmodellen undersøger en fysisk switch efter mindst 47,5 mΩ og mindst 1760 µF effektiv beskyttet kapacitans. Med ekstra krav om ≤160 V kildefejl, ≤1 mΩ ESR, ≤5 µs samlet forsinkelse, 114,88 V seneste trip-start og ≤1 V ekstra ringing bliver beregnet peak 119,324 V. **Alle disse fysiske grænser er ubekræftede.** Reportens modelresultat passerer betinget, mens dens kvalifikationsgate fejler. 200 V-kildefejl, højere ESR og manglende grænser kan afvise modellen.

## 5. Uafklarede designproblemer

1. RSP-3000-48-modellens tilladte seriedrift og flydende working-voltage er ikke modelkvalificeret. Summen 134,4 V er øvre OVP-tærskelbudget, ingen dokumenteret transientgrænse.
2. En konkret kvalificeret busafbrydelse, præladning, selvstændig OV/UV, rail-off, energi-/flywheelvej og hot-switch-SOA mangler. LTC4366/enkelt-MOS lineær 40 A-clamp er ikke godkendt af de eksisterende analyser.
3. Fasestrømstudiet mangler integreret RUN-guard, DIAG-/kommandofejllås, anti-windup, OFF-reset, clockgating og dokumenteret ITH-autoritet. Sensorens offsetækvivalent gør det uegnet som mA-område.
4. Den aktuelle enkeltfase-CV/CC er ikke systemintegreret. Kommandokortslutning til GND kan efterlade høj udgangskommando; uafhængig DUT-OVP, udgangsafbrydelse, backfeed/rail-off og CV/CC-stabilitet mangler.
5. Præcise lavstrømsområder mangler pass-kredsløb, varm DC-SOA, fysisk range-interlock, reverse-blocking og afladning. 0 A skal give OFF; 0 V kræver verificeret restspænding/afladning, ingen nuværende aktiv 0 V-garanti.
6. PCB-gate/source-loops, Kelvin-ruter, strømretur, termik, valgte fabrikant-footprints og assembly skal gennemgås uafhængigt. Geometrisk routingpass er ingen elektrisk eller termisk godkendelse.
7. Spole, bulk, shunter, dioder, terminaler, netbeskyttelse, hjælpeforsyninger og køling mangler endelige fabrikantvalg og anvendelseskvalifikation.

## 6. Nødvendig fysisk og sikkerhedsmæssig validering

Der er **ikke bygget eller spændingssat hardware**. Der er ingen målt regulatorfunktion, 40 A-drift, milliamperebeskyttelse, kortslutningsreaktion, temperatur, isolation eller EMC.

Før nettilslutning eller fysisk effekttest kræves kvalificeret, uafhængigt hardware-/sikkerhedsreview og løsning af bus-/ratings-/beskyttelsesblokeringerne. Først derefter kan testplanen i protection-and-test-plan.md følges fra spændingsløse kontroller og begrænset energi til enkeltfase, fasefejl, lavstrøm og fuld effekt. Manualens testpunkter er forventninger til fremtidige forsøg, ikke måleresultater.

Ingen GitHub-publicering, fremstillingsfrigivelse eller cloudpublicering er udført. Cloudkladden indeholder genbrugelige opstartsinstruktioner; en gemt kladde aktiverer ikke miljøet, og en ny cloudtask er ikke verificeret.
