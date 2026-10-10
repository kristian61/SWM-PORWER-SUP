# Busbeskyttelse for den valgte 110 V front-end

Status 9. oktober 2026: **fabrikantunderbygget forundersøgelse og reproducerbart parameterstudie; beskyttelsen er ikke færdigtegnet eller kvalificeret.** Den eksisterende LTC3779-fase med 150 V MOSFETs og proceduregrænse 120 V må endnu ikke forbindes til de to RSP-3000-48-moduler. Ingen beregning nedenfor dokumenterer, at denne fase sikkert holdes under 120 V. Der er hverken foretaget fysisk test eller frigivet fabrikationsfiler til beskyttelsestrinnet.

Det eksisterende valg beholdes: to isolerede RSP-3000-48 i serie, 55,0 V per modul og 110 V nominelt. Undersøgelsen konkretiserer, hvilke separate funktioner der skal beskytte denne bus, og hvilke fabrikantdata der allerede findes. Den ændrer ikke systemdiagrammet, enkeltfasens PCB eller den endnu uafklarede firefasearkitektur.

## Problemet og de nødvendige strømveje

RSP-databladets OVP er 57,6–67,2 V per modul. Et enkelt højt modul kan give 67,2 + 55 = **122,2 V**; summen af begge øvre tærskler er **134,4 V**. Sidstnævnte er et tærskelbudget, **ikke** en dokumenteret maksimal fejl-/transientspænding. Modulet kan have lagret udgangsenergi og dynamisk oversving før og under shutdown. Dokumenteret maksimal bølgeform, samlet outputkapacitet og frakoblingstid mangler.

En brugbar integrationsarkitektur skal derfor have disse konkrete funktioner:

1. `BUS_SRC`: den ubeskyttede serieudgang med egen spændingsmåling.
2. En hurtig overspændingsfunktion, som begrænser spændingen til `BUS_PROTECTED` under det første fejlforløb, med pass-MOSFETs kvalificeret i lineær SOA og egen kortslutnings-/strømbegrænsning.
3. En separat, låsende hardwareafbrydelse på DC-siden. En common-source back-to-back MOSFET-funktion kan blokere begge strømretninger i OFF; enkelt-MOSFETens bodydiode kan ikke antages at gøre det.
4. Et defineret sted til kabelinduktans og reverse energy på begge sider af afbryderen. Frakobling flytter ikke automatisk energien væk fra den beskyttede bus.
5. Hardwarestop af alle effektfaser, separate isolerede OFF-signaler til begge RSP-moduler og derefter AC-energien fjernet med de dimensionerede netkontakter. Fault låses indtil bevidst reset og ny kontrol af begge busser.

Dette er en funktionsarkitektur, ikke et implementeret kredsløb. Den præcise rækkefølge og nødvendige uafhængighed under fejl skal kvalificeres; STOP/RUN alene er ikke en clamp. En kontaktor kan fjerne fortsat energitilførsel, men dens kontakttid klemmer ikke første transient, og en åben AC-kontakt tømmer ikke modulernes kondensatorer.

## Fabrikantverificerede kandidater

Originaldokumenterne er gemt i `references/`; URL, revision, downloadstatus, byteantal og SHA-256 findes i `references/bus-protection-sources.json`. RSP-specifikationen og dens provenance findes allerede i `references/frontend-sources.json`. Sidehenvisninger er dokumenternes trykte sidenumre, hvis de findes.

| Funktion / kandidat | Verificerede data | Projektstatus |
|---|---|---|
| Analog HV-clamp: **LTC4366-1** | Rev. F side 1: flydende surge stopper, 9 V til over 500 V med eksterne komponenter; ekstern N-MOS regulerer lastspændingen. `-1` låser efter timer-fault; `-2` gentager efter cooldown | Relevant controllerkandidat. Eksterne FETs, bias-/gate-/timer-net og strømbegrænsning mangler; ingen 110 V / 40 A-kvalifikation |
| Hurtig DC-driver: **TPSI3050**, 3-wire mode | SLVSGO9C side 1, 10, 17–19 og 24: isoleret gateforsyning/driver, cirka 10 V gate, 1,5 A peak source / 3 A peak sink; common-source back-to-back MOSFET-topologi; 3 kV RMS **basic** isolation | Kandidat til låsende DC-frakobling. Driveren har ingen indbygget busmåling, strøm-/energibegrænsning eller 40 A effektvej |
| Hurtig tærskel: **TLV3501** | SBOS321E side 5–6: supply 2,7–5,5 V; offset ±6,5 mV maksimum ved 25 °C; propagation højst 12 ns ved 5 mV overdrive og 100 mV inputstep under angivne betingelser | Comparator-kandidat. Reference, divider, inputbegrænsning, hysterese, forsyningssekvens og faultlatch er endnu ikke dimensioneret |
| DC-switch-MOS: **IPP110N20N3 G** | Rev. 2.3 side 1–4: VDS minimum 200 V, RDS(on) maksimum 11 mΩ ved 10 V gate / 25 °C, Qg maksimum 87 nC ved 100 V / 44 A; TO-220; SOA i side 4 diagram 3 | Verificeret modeldata til switchstudie; ikke valgt eller termisk/layoutmæssigt kvalificeret. Én MOS er afvist som 40 A / 20 ms lineær pass-clamp ved cirka 20 V VDS |
| AC-startstrømsbegrænser: **MEAN WELL ICL-28R / ICL-28L** | Installationsmanual 2026.01.12 side 1 og 3–4: 180–264 V AC, 50/60 Hz, 28 A kontinuerligt, højst 60 °C; både kontinuerlig strøm og maksimal tilsluttet bulk-C skal overholdes | Fabrikantverificeret familie; præcist modeldatablad, restart-/bypass-/current-limit-data og samlet input-C mangler. Ingen af varianterne er frigivet som konkret løsning |

TLV3501's 12 ns er ikke en garanteret tid fra en langsom bus netop krydser tærsklen. 5 mV overdrive ved comparatorindgangen skal først være opnået; divider/filter og latch bidrager også. Offsetmaksimum er specificeret ved 25 °C; temperaturdrift er typisk, så en komplet worst-case-tærskel over systemtemperatur er endnu ikke bevist.

TPSI3050's max 3 µs fra EN-fald til VDRV = 10 % gælder med 100 pF load, de specificerede forsyningskondensatorer og RPXFR. To effekt-MOSFETs, gate-R og layout kræver særskilt bølgeforms-/delaykontrol. Slukning ved tab af primærforsyning har 100 µs **typisk** timeout uden angivet maksimum; den kan ikke bruges som hurtig BUS_OVP-strategi. EN skal hardwarestyres til OFF ved fault, og opstart følger fabrikantens forsyningssekvens.

## LTC4366: lovende clamp, men ikke færdig busbeskyttelse

Databladets side 4–5 angiver:

- FB-regulation 1,193 / 1,230 / 1,267 V (min/typ/max) og FB-leakage op til ±1 µA over det angivne temperaturinterval.
- Fast FB→gate-path højst 300 ns ved det angivne inputstep. Dette er ikke hele effektvejens regulerings-/frakoblingstid.
- Gate fast-discharge mindst 122 mA ved GATE = 10 V og OUT = 4,9 V. Tallet må ikke antages konstant gennem enhver ekstern gatebølgeform.
- SD→gate-filter op til **1,2 ms**. SD er en supervision-/stopfunktion, ikke den hurtige første clamp.
- Timer-threshold 2,5–3,1 V og C/I/H timercharge 5,1–13 µA. En timer må dimensioneres ud fra de ugunstige kombinationer og ekstern MOS-SOA, ikke alene den typiske formel i teksten. MP-versionens minimumstrøm er lavere.

Side 13 og 15 kræver analyse af opstart, gatebeskyttelse, ekstern MOSFETs spændingsrating og **SOA ved alle relevante faultforløb**. Side 15 angiver mindst 2 nF gatekompensation; denne kondensator påvirker slew/inrush og skal tåle den pågældende busspænding. OUT/VSS-bypass, RIN/RSS og ekstern gatebeskyttelse skal dimensioneres for flydende IC-noder. SD eller andre kontrolben må ikke forbindes som et almindeligt jordrefereret logic-input uden korrekt levelshift.

LTC4366 alene giver ikke en komplet garanteret effektstrømgrænse ved kortslutning. ADI's **DC2150A** (side 1–2) kombinerer den med LT4363 for blandt andet strømbegrænsning, men demoen er en 28 V / 4 A-løsning. **DC1850A** er en cirka 28 V / 1,5 A-demo med 41–45,3 V clamp (side 1). Deres 100–250 V surge-eksempler må ikke overføres som et kvalifikationsbevis for 110 V / 40 A.

### Statisk clamp-margin med det aktuelle 55 V-setpunkt

Et illustrativt, **ikke valgt**, divider-eksempel er `BUS_PROTECTED/OUT — 1,21 kΩ — FB — 2 × 55,6 kΩ — BUS_NEG`, alle ±0,1 %. Beregningen omfatter controllerens FB-grænser, værste dividerkombination og ±1 µA leakage:

| Resultat | Spænding |
|---|---:|
| Nominel clamp | 114,268 V |
| Laveste statiske clamp | 110,501 V |
| Højeste statiske clamp | 118,050 V |
| Margin fra højeste clamp til 120 V | 1,950 V |
| Normal 110 V-bus med ±1 % og +25 °C ved ±0,05 %/°C, før ripple | Op til 112,475 V |

Dermed kan denne divider allerede gå i clamp og senere timer-fault på en ellers normal høj bus: minimum-clampen ligger 1,974 V under dette normalbudget. En hævet clamp flytter samtidig dens øvre tolerance tæt på 120 V. Dette divider-eksempel løser altså ikke integrationsproblemet. Dividerens nederste modstande afsætter samlet cirka 115 mW nominelt; spændings-/effekt-/temperaturrating kræver stadig faktiske modstandsvalg.

Et undersøgeligt **designalternativ**, uden ændring af den aktuelle CAD, er trim til 53 V per modul / 106 V samlet. Det samme normalbudget bliver 108,385 V, så divider-eksemplet har 2,116 V nedre margin. Det løser ikke dynamisk oversving eller MOS-SOA. Ved 100 V ud overstiger ideal duty 91,67 % buck-only-grænsen, og LTC3779 skal arbejde i overgangs-/buck-boost-området; strømfordeling, tab og den belastede minimumsbus skal analyseres før et sådant setpunkt vælges.

## Reaktionstid og beskyttet kapacitet

Alle beregninger reproduceres med:

```sh
python3 scripts/bus_protection_calcs.py
```

Resultater og eksplicitte antagelser gemmes i `exports/analysis/bus_protection.json`. Scriptet er et SI-baseret analytisk parameterstudie, ikke SPICE, controller-loopmodel eller hardwaretest.

Den eksisterende enkeltfase har 2 × 47 µF bulk. Med **antaget ±20 %** bliver minimum 75,2 µF, når keramiske bidrag ignoreres. Fire sådanne forbundne faser giver 300,8 µF; den firefasekonstruktion findes endnu ikke. To yderligere cases, 470 µF og 2.200 µF hver med samme toleranceniveau, er hypotetiske beskyttelsesbulkvalg og findes ikke på det nuværende PCB. ESR/ESL, temperatur og levetidsdrift er ikke modelleret.

Et eksempel på et ufuldstændigt hardwaretrip-budget bruger 116,0 V nominalt, ±0,65 V antaget tærskelusikkerhed og en 2,5 V/116 V divider. De krævede 5 mV comparatoroverdrive svarer til yderligere 0,232 V på bussen. Delay-analysen begynder derfor ved **116,882 V**. Budgettet er 12 ns comparator + 0,5 µs antaget sensefilter + 0,5 µs antaget latch/buffer + 3 µs TPSI3050 + 1 µs antaget yderligere loaded-gate-turnoff = **5,012 µs**. Referencen/divideren og disse antagelser er ikke en færdig komponentdimensionering.

For en idealiseret konstant ladningsstrøm ved nul last er tidsrummet til 120 V `t = C × (120 − 116,882) / I`. Ved eksisterende 75,2 µF og 500 A bliver det kun **0,469 µs**. 500 A er et eksempel, ikke en dokumenteret RSP-pulsstrøm; et moduls 62,5 A-mærkestrøm begrænser ikke automatisk fejlstrøm fra dets kondensatorer.

En separat illustrativ RC-stepcase bruger 134,4 V idealkilde, **antaget 20 mΩ** samlet kilde-/kabel-/switchmodstand og nul last, uden kabelinduktans. Switchen antages fuldt ON indtil den åbner. Startpunktet er den nævnte 116,882 V tærskel/overdrive:

| Beskyttet C minimum | Spænding efter kun 3 µs driver-delay | Spænding efter hele eksempelbudgettet 5,012 µs |
|---|---:|---:|
| 75,2 µF, eksisterende én fase | 132,02 V | 133,77 V |
| 300,8 µF, hypotetisk fire faser | 123,76 V | 126,79 V |
| 376 µF, hypotetisk 470 µF bulk | 122,64 V | 125,40 V |
| 1.760 µF, hypotetisk 2.200 µF bulk | 118,31 V | 119,21 V |

Det sidste eksempel holder sig under 120 V **i denne afgrænsede matematiske case**, men beviser ikke konstruktionen: hverken 134,4 V, 20 mΩ eller 5,012 µs er en kvalificeret worst-case-grænse. Større sourceoversving, lavere impedans, længere gate-delay eller inductive ringing ændrer resultatet. Tabellen viser hvorfor en DC-afbryder alene med den eksisterende kapacitet ikke kan accepteres ud fra dens databladstid.

Et LTC4366-gateestimat med antaget 200 nC eksternt gate-charge og 2 nF gatekondensator ved 12 V giver cirka 1,836 µs discharge plus 300 ns fast-path = 2,136 µs. Det bruger min sink-current fra ét testpunkt som en forenkling og er **ikke** en garanteret responstid. Den analoge clamp reducerer strømmen løbende; ovenstående ideal-ON/ideal-OFF RC-model beskriver ikke dens loop. Der skal bruges et kvalificeret faktisk kredsløb og bølgeformsanalyse for at fastlægge peak på `BUS_PROTECTED`.

## Pass-MOSFET, opstart og varme

Ved eksempel-kilden 134,4 V, clamp 114,268 V og 40 A bliver pass-effekten **805 W**. Energi er cirka 4,03 J ved 5 ms og 16,11 J ved 20 ms; 1 s kræver 805 J. Længere/korte faultforløb skal derfor testes mod SOA, ikke kun watt-rating eller avalanche energy.

IPP110N20N3 G's originale SOA-diagram, side 4 diagram 3, gælder Tc = 25 °C og enkeltpuls. Omkring 20–21 V / 40 A ligger punktet under 1 ms-kurven, men tydeligt over 10 ms-kurven. **Én af disse MOSFETs er dermed afvist til 20 ms-pass-clamp allerede ved 25 °C.** Der er ingen 5 ms-kurve; 1 ms-kurven kan ikke kvalificere 5 ms. Parallelle MOSFETs kan ikke blot tælles som ideel SOA-multiplikation uden strømfordeling, gate-/source-net, termisk matching og fabrikantunderbygget analyse.

Infineons originale AP99007, V1.1 maj 2017, især side 7–12, beskriver termisk instabilitet/hotspots og temperatur-/repetitionsderating i lineær drift. En switch-optimeret lav-RDS MOSFET er derfor ikke automatisk en robust lineær surge-stopper. Et SOA-egnet passvalg mangler fortsat. Normal HTTPS-adgang til `www.littelfuse.com` gav proxyafvisning under undersøgelsen; der er ikke kvalificeret en IXYS linear-MOS via et distributørnavn eller en gættet model.

Som **ON-tabseksempel** giver to IPP110N20N3 G i back-to-back med en antaget 2× varm RDS(on) i alt 44 mΩ. Ved 40 A er det 70,4 W og 1,76 V fald for parret. Temperaturfaktoren er en antagelse, ikke en fabrikantmaksimumgrænse. FET-antal, køling og forbindelser må vælges ud fra faktiske hot-RDS-/SOA-grænser; 200 V-rating alene frigiver ikke afbryderen.

Precharge udføres med effektfaser OFF. Ved ideel opladning fra nul til 110 V har 376 µF energi 2,275 J og 1.760 µF energi 10,648 J; en resistiv eller lineær præladningsvej afsætter samme energi ved ideal 110 V-kilde og nul load. Ved eksempelvis 1 A tager opladningen henholdsvis 41,36 ms og 193,6 ms. Det er kun de hypotetiske sekundærbulk-kondensatorer; moduler og eksisterende faser har yderligere ukendt/afhængig lagret energi. Precharge-modstand/pass-FET skal have pulse-rating/SOA, bypass må først ske efter verificeret spændingsforskel, og et kortsluttet load må ikke udløse gentagen automatisk precharge.

## Reverse energy og induktiv afbrydelse

LTC3779 kan tilbageføre energi fra output til input, og forced CCM tillader negativ strøm; se `docs/multiphase-research.md` og LTC3779 side 17. RSP-modulerne er ikke dokumenteret som regenerative energisænker. Antiparalleldioden over hvert RSP-modul beskytter mod **negativ modulspænding**; den absorberer ikke en stigende positiv samlet bus.

Når DC-afbryderen er OFF, kan den beskytte `BUS_SRC` mod reverse current, mens energien stadig bliver fanget i `BUS_PROTECTED`. Den beskyttede kapacitet kan kun modtage `ΔE = ½ C (120² − 110²)` inden 120 V:

| C minimum | Energi fra 110 til 120 V | Tidsrum ved 4 kW netto tilbageført energi |
|---|---:|---:|
| 75,2 µF | 0,0865 J | 21,62 µs |
| 376 µF | 0,4324 J | 108,1 µs |
| 1.760 µF | 2,024 J | 506,0 µs |

4 kW regeneration er en eksplicit eksempelbelastning, ikke dokumenteret controllerdrift. Et aktivt dump ved 116 V skulle til 4 kW bruge omkring **3,364 Ω**, 34,48 A og 4 kW varme; 50 ms er 200 J og 1 s 4 kJ. Dump-MOSFET, modstand, puls-/termisk rating og fault-latch er uafklaret. En almindelig bleedermodstand er ikke sådan et dump. Ingen TVS er valgt: stand-off, breakdown-tolerance og faktisk clamp ved den mulige pulsstrøm/temperatur skal alle passe under den beskyttede komponentgrænse. Et tal i et TVS-modelnavn dokumenterer ikke en clamp under 120 V.

Kabel-/sløjfeinduktans kræver en lokal afslutning af strømmen, når DC-switchen åbner. `E = ½ L I²`; 10 µH giver 8 mJ ved 40 A, men 1,25 J ved 500 A. Et fald på 40 A i 1 µs giver idealiseret 400 V induktivt bidrag ved 10 µH, før snubber/clamp og parasitter. Derfor skal strømveje, snubber/diode/clamp og begge FETs' VDS-spidser analyseres fysisk i layoutet. MOSFETens single-pulse avalanche energy ved én databladstest er ikke en generel absorptionsrating for dette forløb.

RSP's samlede udgangskapacitet er ukendt. For **kun et eksempel** på 1 mF ville energien ved 134,4 V være 9,032 J, hvoraf 2,982 J er stigningen over 110 V. Eksemplet er ikke en måling af modulerne og må ikke bruges til sikrings-/clampdimensionering som et maksimum.

## AC-inrush, kontaktorer, sikringer og nødstop

De to RSP-moduler har hver 60 A **typisk** kold inrush ved 230 V. Deres nominelle AC-strøm er hver 16 A typisk ved fuld moduleffekt; projektet bruger ikke begge modulers fulde 6 kW. Med 95 % antaget DC-effektivitet og modulernes 91,5 % / PF 0,95 typiske data er 4 kW-systembudgettet cirka 21,06 A ved 230 V og 26,91 A ved 180 V. Disse værdier er ikke et maksimum til kontaktor-/sikringsvalg.

ICL-28-familiens 28 A kontinuerlige rating giver nominelt margin ved 230 V, men meget lidt ved det lave 180 V-budget. Den kan ikke blot forsynes med to moduler, som hver frit må trække deres fulde typiske 16 A. Installationsmanualens kapacitansgrænser 2.500/6.000 µF er familiereferencer; det præcise variantdatablad og den samlede tilsluttede AC-inputbulk skal kontrolleres. Den historiske RSP-3000-48-RPT side 7 nævner C5 = 470 µF / 420 V, men opgiver ikke en fuld kondensatorbankoptælling og dokumenterer ikke samlet input-C. Denne gamle sample-rapport kvalificerer heller ikke den aktuelle 2026-revision.

Der er derfor **ingen frigivet AC-kontaktor, AC-inrush-variant, branch-sikring, DC-sikring eller nødstop-varenummer**. Et endeligt kontaktvalg skal have dokumenteret making-/breaking-evne for det faktiske PFC-/kapacitive load og faultkoordination. En AC1/AC3-mærkning alene dokumenterer ikke denne inrush, og en AC-kontaktors rating må ikke genbruges som DC-bryderating. Sikringen skal koordineres med tilgængelig fejlstrøm, afbrydeevne, kabel-/terminalgrænser, inrush og power-semiconductorens energi; softwarestrømbegrænsning eller gruppens 32 A tal gør ikke dette valg.

Den konkrete stopfunktion skal droppe de valgte netkontaktorer og begge modul-enablekontakter, fastholde fault og holde DC-/output-enable OFF ved manglende styringsforsyning. Stop af output/faser, DC-energi og AC-indgang har forskellige opgaver. PE føres ubrudt til chassis og begge FG og må ikke indgå i stopkontakterne. Kontaktorsvejsning/status og resetsekvens skal vurderes i den færdige hardware; dette dokument påstår ingen sikkerheds- eller nødstopcertifikation.

MEAN WELL-dokumenterne giver ikke en garanteret tid fra RC/AC-off til tom DC-bus. Historisk sample hold-up er ikke samme som maksimal sikker udladningstid. Kontaktorer, reverse-diodestrømme og deres isolation ved øverste modul skal fortsat kvalificeres mod den valgte serieforbindelse.

## Målepunkter til næste konstruktion og fejlfinding

Disse er foreslåede funktioner, **ikke allerede placerede PCB-testpunkter**:

| Fremtidigt målepunkt | Reference / måling | Hvad det afgør |
|---|---|---|
| `TPB_SRC` | Ubeskyttet bus til BUS_NEG | RSP-sum, sourceoversving og shutdownforløb |
| `TPB_LOAD` | Beskyttet bus til BUS_NEG | Om clamp/afbrydelse faktisk holder alle peaks under den kvalificerede grænse |
| `TPB_OVP_SENSE` | Divider-node til dens lokale senseground | Tærskel, offset, filterdelay og overdrive |
| `TPB_FAULT` | Latchet fault til lokal logicground | Udløsning, reset og afbrudt hjælpeforsyning |
| `TPB_GATE_S` | Gate **til hver MOSFETs egen source**, ikke BUS_NEG | Gateforsinkelse, UVLO og VGS-oversving |
| `TPB_DUMP_I` | Dokumenteret strømtransducer/shunt | Regen-/induktiv energi til dumpvej |
| Modulstatus / separate enable | Hvert moduls egen isolerede reference | Om begge moduler stopper; P_OK er ikke præcis 55 V-good |

Før integration kræves uafhængig review af det faktiske beskyttelseskredsløb og derefter afgrænsede målinger med eksternt strøm-/energibegrænset kilde. Det konkrete kvalifikationsresultat skal indeholde worst-case tærskel og protected-peak, fuld gate-/VDS-bølgeform, temperatur/SOA og energi ved startup, OV, afbrudt hjælpespænding og reverse current. Dokumentationen må ikke mærkes testet alene fordi en JSON-beregning eller KiCad ERC passerer.

## Præcis reststatus

Kandidat-controller, driver, comparator og et 200 V switch-MOS-datablad er verificeret og arkiveret. Reaktionstid, bulkenergi, linear-SOA og regen er nu konkret beregnet med synlige antagelser. Den eksisterende 120 V / 150 V-fase er **stadig ikke kvalificeret til RSP-bussen**. Den aktuelle showstopper er mangel på et faktisk dimensioneret og kvalificeret hurtigt clamp-/afbrydelsestrin med bounded sourceforløb, varmt MOS-SOA og energiabsorptionsvej. Højere komponentratings eller lavere setpunkt er relevante designmuligheder, men de erstatter ikke analysen af controllergrænser, switch-node-ringing, fælles fasekontrol og reverse energy.

