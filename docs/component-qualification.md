# Komponentdata, pinout og åbne indkøbsvalg

Revision: 10. oktober 2026. Denne gennemgang tager udgangspunkt i den aktuelle komponentliste med **206 poster**. Den supplerende [kritiske komponentmatrix](../bom/critical-components.csv) indeholder **85 poster**, herunder alle **14 valgte IC-, MOSFET- og netmodulreferencer**. Værdier, antal og footprintnavne er kopieret fra den samlede BOM; kredsløbene og den samlede BOM ændres ikke af matrixen.

Matrixen angiver producent, præcist varenummer, pinout/package, normale driftsgrænser, absolutte grænser, strøm-/effekt-/temperaturbetingelser, funktion, original kilde, revision, trykte sider og kildehash. Kritiske ubestemte dele står som **KRAV / IKKE VALGT**, med de dimensioneringskrav der faktisk findes i projektet. Et komponentnavn i en KiCad-footprint eller et 1206-/2512-mål dokumenterer ingen fabrikant-rating.

**Der er ikke udført hardwaretest eller frigivet indkøb/fremstilling.** Et verificeret datablad og korrekt pinmap dokumenterer komponentens angivne egenskaber; det dokumenterer ikke sløjfestabilitet, fejlrespons, termik, isolation eller hele forsyningens funktion.

## Hvad matrixen dækker

| Gruppe | Referencer og funktion | Kvalifikationsstatus |
|---|---|---|
| Effektcontroller | Effektfase U1, LTC3779EFE#PBF | Originalt ADI-datablad og native pinmap kontrolleret; landpattern rettet til fabrikantens mål; anvendelse og assembly er uafklaret |
| Effekt-MOSFETs | Effektfase Q1–Q4, BSC110N15NS5 | Originalt Infineon-datablad, packagefamilie og funktionel padmap kontrolleret; SOA, transienter, køling og assembly mangler |
| Analog regulering og måling | Styrekort U1 OPA4192IPW, U2 INA240A2D | TI-originaler og pinmaps kontrolleret; lavstrømsnøjagtighed, headroom, clampautoritet og regulering er uafklaret |
| Reference og supervisors | Styrekort U3 LM4040AIM3-2.5/NOPB, U4 TPS3808G50DBVR, U5 TPS3700DDCR | TI-originaler og pinmaps kontrolleret; referencebudget beregnet med synlige antagelser, rail-off og tidsforløb er utestede |
| Fault-comparatorer | Styrekort U6/U7 TLV1704IPW | TI-original og pinmap kontrolleret; fault-low og forsinkelse ved den faktiske 5 V-forsyning kræver validering |
| Isolerede netmoduler | Netdel A1/A2 RSP-3000-48 | Modelspecifikation og terminalmap kontrolleret; seriedrift, flydende offset, 55 V-belastning og systemintegration er ikke frigivet |
| ADI-referencekandidater | DFLS1200-7 på effekt- og styrekort; Murata GRM55DR72E105KW01L til effektkortets lokale 1 µF kondensatorer | Præcist navn og referenceværdi findes i ADI-demoens BOM; egne komponentdatablade og anvendelsen er ikke kvalificeret |
| Kritiske krav uden varenummer | Spole, shunter, bulk, HV-dividere, afkobling, kompensation, terminaler, sikringer, afbryder, enablekontakter og reverse-dioder | Krav og beregninger registreret; fabrikant-, mekanik-, puls-, temperatur- og systemreview mangler |

De mulige INA190-lavstrømsområder og LTC4366/TPSI3050-busbeskyttelse er undersøgelser uden implementerede BOM-dele. Deres fabrikantdata og begrænsninger står i [low-current-output.md](low-current-output.md) og [bus-protection.md](bus-protection.md). De er ikke præsenteret som monterede komponenter i denne matrix.

## Driftsgrænser og absolutte grænser

Absolutte grænser er skadesgrænser; de er ikke anbefalede kontinuerlige driftspunkter eller et bevis for korrekt funktion. Testbetingelser skal læses sammen med tallene. Et typisk tal er heller ikke en garanteret maksimumsgrænse.

| Komponent | Verificeret driftsområde | Separat absolut grænse eller anden begrænsning |
|---|---|---|
| LTC3779EFE#PBF | VIN 4,5–150 V; VOUT 1,2–150 V; valgt E-grade junction −40…125 °C | Flere HV-pins har også 150 V absmax: der er ingen spændingsreserve ved 150 V. DRVCC og BOOST−SW højst 11 V; ITH/SS/PLLIN følger den lokale V5-grænse. Projektets 120 V-proceduregrænse er fortsat gældende |
| BSC110N15NS5 | Projektet bruger nominelt 10 V gate og 110 V DC-bus. Databladet angiver 150 V VDS-rating og mindst 150 V breakdown ved VGS = 0 V, ID = 1 mA | VGS højst ±20 V, Tj højst 150 °C. Der er ingen særskilt recommended-operating-tabel, som kvalificerer projektets ringing eller lineære drift |
| OPA4192IPW | VS 4,5–36 V, temperatur −40…125 °C | VS absmax 40 V; inputbeskyttelsesstrøm højst ±10 mA. Udgangsniveau og strøm skal vurderes ved faktisk last/common-mode |
| INA240A2D | VS 2,7–5,5 V, common-mode −4…80 V, temperatur −40…125 °C | VS absmax 6 V, common-mode −6…90 V. Den er ikke egnet direkte på en 100 V high-side |
| LM4040AIM3-2.5/NOPB | 2,5 V shuntreference; eksakt I-grade −40…85 °C. A/I-varianten kræver op til 65 µA minimum over temperatur | Reverse-current absmax 20 mA; forward 10 mA; Tj højst 125 °C. Familien har andre temperaturvarianter, som ikke er det valgte varenummer |
| TLV1704IPW | VS 2,2–36 V, common-mode mellem rails, temperatur −40…125 °C | VS absmax 40 V, input mellem rails ±0,5 V med højst ±10 mA clampstrøm. En tilladt injektionsstrøm dokumenterer ikke korrekt rail-off |
| TPS3808G50DBVR | VDD 1,7–6,5 V; SENSE/MR/RESET 0–6,5 V; CT højst VDD | VDD/SENSE/MR/RESET absmax 7 V; CT højst VDD+0,3 V. Reset er ikke funktionelt garanteret helt ned til 0 V under alle laster |
| TPS3700DDCR | VDD 1,8–18 V; sense 0–6,5 V; outputs 0–18 V; junction −40…125 °C | VDD/output absmax 20 V; input 7 V; junction absmax 125 °C. Den aktuelle AUX5 ligger i driftsområdet |
| RSP-3000-48 | 180–264 V AC, 47–63 Hz; 48 V / 62,5 A / 3000 W nominelt; SVR 43–56 V | 55 V × 62,5 A er over 3000 W og er ikke en frigivet rating. OVP 57,6–67,2 V er et shutdown-tærskelinterval, ikke en transientclamp eller maksimal faultspænding |

De originale sider og de øvrige pin-grænser står i CSV-matrixen. Systemets mulige temperatur og effekt kan ikke fastlægges ud fra én IC's temperaturinterval: LM4040-variant, netmodul, øvrige dele og lokal opvarmning kan sætte lavere grænser.

## Strøm, tab og regulatorens råderum

**MOSFETens databladstal er ikke kortets strøm-rating.** BSC110N15NS5 har ID max 76 A ved TC = 25 °C og 48 A ved TC = 100 °C. Ptot 125 W forudsætter TC = 25 °C; junction og den virkelige kølevej sætter grænsen. De 38 A i RDS(on)-testen er en testbetingelse. RDS(on) højst 11 mΩ gælder VGS = 10 V og Tj = 25 °C. Databladets puls-/avalanchetal skal vurderes med deres angivne strøm, temperatur, SOA og gentagelse; de frigiver ikke et 40 A-print eller et lineært pass-trin.

LTC3779 har ingen selvstændig 10 A/40 A-effektstrømrating. Eksterne MOSFETs, shunter, spole, kondensatorer og forbindelser bestemmer effektvejen. Dets 70–110 mV buck-valley-threshold er den maksimale threshold under databladstesten, ikke et matching-tal til fire 10 A-faser. Det native middelstrømsloft omkring 12,5 A er heller ikke præcis, justerbar laboratorie-CC.

OPA4192's ±65 mA short-circuitstrøm er **typisk**. Den beviser ikke, at den aktuelle diode/470 Ω-vej kan trække ITH til det nødvendige niveau under alle forhold. Lavspændingstabellen angiver højst 110 mV outputheadroom med 10 kΩ last til midt-rail ved 25 °C; det er ikke en direkte garanti for den faktiske **100 mV IREF-buffer**. Referenceindgangenes belastning, opampens common-mode, offset, udgangsheadroom og temperatur skal med i det konkrete budget og afprøves.

INA240A2's gain er 50 V/V. Offset højst ±25 µV gælder blandt andet 25 °C, VS = 5 V, VCM = 12 V og REF1 = REF2 = VS/2. Det svarer til 25 mA ved en 1 mΩ shunt **under disse betingelser**, før andre fejl og temperaturdrift. Det aktuelle low-side-setup har common-mode nær 0 V og reference 0,1 V; et samlet fejlbudget og målinger mangler. Offsetdrift, shuntdrift og det cirka 212 mA nominelle kommandovindue gør dette kort utilstrækkeligt til dokumenteret beskyttelse ved få milliampere.

LM4040's current-budget bruger den konkrete 65 µA minimumsgrænse. Den genkontrollerede nominelle REF25-belastning er 694,211 µA; R13 = 2,49 kΩ giver cirka 309,8 µA resterende shuntstrøm ved AUX5 = 5 V. Et konservativt scenarie giver 104,30 µA, cirka 39,30 µA over minimum. Beregningens reference-, resistor-, supervisor- og ekstra-load-antagelser er synlige i `control_limits.json`; resultatet er statisk og beviser ikke referenceopstart eller rail-off.

## Fault-output og forsinkelser

TPS3808G50's 4,65 V tærskel har ±2 % tolerance over −40…125 °C, så den kan ligge mellem 4,557 og 4,743 V. 10 nF CT giver cirka 57,64 ms nominel resetforsinkelse. Den typiske 20 µs SENSE-assertion har ingen angivet maksimumsgrænse, og der er ikke en direkte min/max-tabelpost ved 10 nF. Den angivne lave POR-forsyning gælder en bestemt resetlast og ramp; den dokumenterer ikke alle tilfælde med signal-backfeed.

TPS3700 har en separat intern 400 mV reference og hjælper med at opdage REF25-fejl. Positive thresholdgrænser er 396/400/404 mV; negative 387/394,5/400 mV. Hysterese, dividerfejl og outputtilstand under UVLO skal med i systemet. Startup har højst 450 µs efter VDD passerer 1,8 V, men de viste 18/29 µs comparatorforsinkelser er typiske ved 5 V, 10 mV overdrive og 10 kΩ pull-up.

TLV1704's VOL ≤0,9 V er specificeret ved IO ≤4 mA, 100 mV overdrive og VS = 36 V. Short-circuitsink 20 mA, leakage 70 nA og 460/560 ns propagation er typiske værdier under deres testbetingelser. Styrekortet bruger 5 V og kan have langt mindre overdrive: faktisk ENABLE-low, alle parallelle outputlækstrømme og faulttid skal kontrolleres. Ingen af disse databladstal skaber den manglende fejllås eller fysiske udgangsafbryder.

## Native package- og pinoutkontrol

| Del | Sammenholdt med fabrikant | Aktuel begrænsning |
|---|---|---|
| Effektfase U1 | FE38(31): body 4,4 × 9,7 mm, pitch 0,5 mm, fjernede positionsnumre 23/25/27/29/31/33/35, EP39 til PGND | Native/library leadpads er korrigeret til 1,050 × 0,300 mm, centre ±2,775 mm, samlet yderbredde 6,600 mm. Det ligger i s.36's anbefalede 1,05±0,10 × 0,315±0,05 mm og 6,60±0,10 mm. EP/pastamønster, lodning, finepitch-clearance og termik kræver assemblyreview |
| Effektfase Q1–Q4 | Infineon s.1/9: source1–3, gate4, drain5–8; pitch 1,27 mm; U08 package E 5,70–6,10 / D 4,80–5,35 mm | Native footprint har sourcepads1–3/gate4 og flere drainpads med fælles nummer5/net. CAD F.Fab er cirka 6,15 × 5,15 mm; package-/landpattern- og pastamønsterreview er ikke frigivet alene af dette familienavn |
| Styrekort U1 | PW TSSOP-14; A OUT/−/+ = 1/2/3; B = 7/6/5; C = 8/9/10; D = 14/13/12; V+4/V−11 | Pinmap og packagefamilie matcher; opampens fire kanaler kan ikke betragtes som uafhængig enkeltfejlsbeskyttelse |
| Styrekort U2 | D SOIC-8; IN−1/GND2/REF2-3/NC4/OUT5/VS6/REF1-7/IN+8 | Begge REF til IREF; NC4 til PGND er tilladt. REF1/REF2-navnene er nu rettet både i lokalt bibliotek og embedded schematic. TSSOP-varianten har en anden map |
| Styrekort U3 | DBZ SOT-23; katode1/anode2/auxiliary3 | Pin3 til anoden/PGND er udtrykkeligt tilladt af TI; der er ingen ukendt NC-funktion på dette ben |
| Styrekort U4 | DBV SOT-23-6; RESET1/GND2/MR3/CT4/SENSE5/VDD6 | RESET er open-drain; pinmap matcher. Intet bevis for ubetinget korrekt fejlrespons ved strømløs AUX5 |
| Styrekort U5 | DDC SOT-6/SOT-23-THIN; OUTA1/GND2/INA+3/INB−4/VDD5/OUTB6; pitch 0,95 mm | Funktionsmap/package-ID matcher. Den arkiverede PDF har ikke den detaljerede DDC mekanik/landpattern; fabrikant-landpatternreview er derfor åbent |
| Styrekort U6/U7 | PW TSSOP-14; ch1 OUT/−/+ = 2/4/5; ch2 = 1/6/7; ch3 = 14/8/9; ch4 = 13/10/11; V+3/V−12 | Biblioteksunits C/D svarer til fabrikantens kanal4/3; de fysiske pinmaps matcher. Alle outputs er knyttet til ENABLE |
| Netdel A1/A2 | TB1 L/N/FG, CN2/CN3 terminalmap og separate lokale control-/senseforbindelser | Chassisdiagrammet bruger passive terminalsymboler, ingen net-PCB. Pinmap er ikke working-voltage- eller modelserie-kvalifikation |

Pin/pad-overensstemmelse i `inventory.json` og fabrikant-pinout er forskellige kontroller: den første sikrer, at diagram og PCB stemmer; den anden kontrollerer, om modellen beskriver den faktiske komponent. Geometrisk DRC og en pinmap-kontrol frigiver ikke assembly eller elektrisk funktion.

## Ubestemte valg er fortsat krav

Spolen er 150 µH med Irms ≥15 A og varm Isat ≥25 A som projektniveau. Det er ikke data fra en valgt fabrikant. DCR, kernetab, AC-viklingstab, varm mætning, terminaler, spændingsstress og køling er åbne.

De fire 47 µF/200 V bulk-kondensatorer har ingen valgt serie. Det generiske D12,5 mm/P5 mm-footprint dokumenterer ikke faktisk størrelse, ripple eller levetid. Inputbankens idealiserede 5,013 A RMS kræver reel margin og temperatur-/frekvensderating. De 1 µF/250 V Murata-kandidater følger ADI-reference-BOM'en; egne bias-/ripple-/landpattern-data mangler. Nominal kapacitans er ikke effektiv kapacitans ved høj DC-bias.

HV-dividere kræver faktisk resistorserie med tolerance, voltage coefficient, working-voltage, puls- og temperaturdata. Den passive måledel kræver 130 kΩ/0,1 %/mindst 100 V og 0,25 W i de øvre grene; 1206-målene alene beviser ikke disse ratings. En åben bundgren kan sende en meget højere spænding mod monitor og 50 V-filterkondensatorer; kortet har ingen aktiv clamp.

`SHUNT_EXT` og `SHUNT_EXTERNAL` er **to krydsreferencer til samme krævede fysiske 1 mΩ fireterminalshunt** ved fælles måling. De er ikke to shunter, som skal indkøbes automatisk. Mindst10 W/50 A DC er endnu et krav uden valgt fabrikat. Dets Kelvin-ledninger bærer ingen 40 A-laststrøm.

Der er ingen frigivne sikringer, netafbryder, kontaktor, nødstop, reverse-dioder eller højspændingsterminaler. Gruppens 32 A og et generisk kontakt-/stiksymbol er ikke komponentratings. Reverse-dioderne over modulerne skal dimensioneres for faktiske strøm-/energibetingelser og faultbus; de beskytter mod negativ modulspænding, ikke mod stigende positiv serie-bus.

## Kilder og næste kvalifikation

Originaler findes i `references/`. `references/sources.json` og de enkelte fabrikantmanifestfiler angiver officielle URL'er og SHA-256; matrixen viser hash for den konkrete lokale kilde. De seks TI-manifestoriginaler er sammenholdt med bytes/hash, og `OPA192.pdf` og `OPA2192.pdf` indeholder samme SBOS620E-snapshot. Her bruges de trykte sidenumre i PDF'erne. Generiske krav kan godt henvise til et controllerdatablad for dimensioneringsmetoden; sådan en reference er **ikke** et datablad for den endnu ukendte passive del.

DFLS1200-7 er ikke fabrikantkvalificeret ved hjælp af en distributørside eller en lignende diode. Normal HTTPS-adgang til `www.diodes.com` gav HTTP403; den eksisterende ADI-reference er det nuværende evidensniveau. De konkrete Vf/leakage/Cj/puls-/packagegrænser skal verificeres før brug i bootstrap, CV-servo eller CC-clamp.

Næste review skal vælge de manglende præcise varenumre, afslutte komponenternes mekanik/assembly og kontrollere deres faktiske drifts-/fejlforløb. De to RSP-modulers 134,4 V OVP-thresholdbudget mod effektfasens 120 V-proceduregrænse skal løses med en konkret kvalificeret beskyttelse, før effektprøve. Fasedeling/railfejl, udgangsafbrydelse, lavstrømsområder, 0 V-udladning, termik, loops, isolation og fysisk test resterer som angivet i [validation.md](validation.md).
