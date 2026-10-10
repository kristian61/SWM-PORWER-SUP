# Isoleret AC/DC-front-end — dokumenteret konstruktionsvalg

Status pr. 9. oktober 2026: **2 × MEAN WELL RSP-3000-48 i serie, hver trimmet til 55,0 V, er valgt som arbejdsgrundlag for systemdiagram og prototypeintegration.** Den nominelle bus er 110 V. Fabrikantens officielle specifikation og generelle serieforbindelsesvejledning er nu hentet og læst. Modelspecifik afklaring af serie-/flydende anvendelse, konkrete beskyttelseskomponenter, installation og fysisk kvalifikation resterer; kombinationen er ikke frigivet som en færdig laboratorieforsyning eller fabrikationsklar konstruktion.

Dette er projektets arkitekturvalg inden for brugerens bekræftede 230 V AC / dedikerede 32 A kreds og isolerede/flydende 0–100 V / op til 40 A. Netmodulerne leverer en fast bus. De efterfølgende CC/CV-, lavstrøms-, udgangsafbryder- og beskyttelseskredsløb skal stadig udvikles. RSP-modulernes strømbegrænsning alene kan ikke beskytte et lille opamp-print eller indstille laboratorieudgangen til 0 V.

## KiCad-diagram og alle viste chassisdele

Åbn `design/frontend/frontend.kicad_pro`; hoveddiagrammet er `frontend.kicad_sch`, og de uafhængige kontrolforbindelser er på `control.kicad_sch`. Det to-siders PDF-diagram findes i `exports/frontend/frontend.pdf`, og alle 14 komponentreferencer står i `bom/frontend.csv`. Projektet tegner kabelforbindelser mellem købte moduler; det indeholder ingen 230 V-PCB. `A1A/A1B` er to symbolenheder af samme fysiske modul A1, tilsvarende for A2; modulet skal kun tælles én gang.

| Reference | Værdi eller faktisk valg | Hvad delen gør |
|---|---|---|
| A1, A2 | RSP-3000-48, 55,0 V SVR-setpunkt hver | Nederste/øverste seriemodul; AC-indgangene er parallelle på nettet, DC-udgangene i serie |
| J1 | L, N, PE; kontakt og kabel endnu ikke valgt | Netindgang til kabinet; kredsens 32 A er et installationskrav |
| SW1 | To-polet AC-afbryder, rating/varenummer mangler | Afbryder L og N; PE føres ubrudt til FG og chassis |
| F1, F2 | Separat AC-grensikring; størrelse/karakteristik/brydeevne mangler | Beskytter hver moduls netgren; hverken en 32 A gruppesikring eller et tilfældigt 16 A tal er indsat som færdigt valg |
| D1, D2 | Reverse-diodekrav ≥200 V VRRM og IFSM >62,5 A; varenummer mangler | Beskytter mod negativ spænding over et seriemodul; dette er ikke de små bootstrap-dioder på effektkortet |
| J2 | BUS_POS / BUS_NEG, 110 V nominelt; terminalvalg mangler | Bus til sekundærregulatoren; ingen direkte DUT-tilslutning |
| R1, R2 | 1 kΩ, ±1 %, mindst 0,25 W som foreløbigt krav | Egen AUX12 til RC på hvert modul. Nominelt 144 mW ved 12 V og 1 kΩ; tolerance/temperatur skal indgå i endelig rating |
| K1, K2 | Separate potentialfrie normalt åbne kontaktfunktioner; relæ og driver mangler | Lukket kontakt aktiverer eget modul; åben slukker. Diagrammet viser ikke endnu en komplet relæspole-/fault-driver |
| J3 | To separate P_OK-kontaktpar | Statusforbindelser til fremtidig supervision; kontakterne må ikke erstatte præcis modul-/busmåling |

PV–PS og OLP–OL-SD på kontrolarket repræsenterer beholdte fabriksbroer, ikke ekstra modstande. De ubrugte CS og den dublerede −S er markeret som no-connect. ERC og uafhængig netlistekontrol er bestået for 63 terminalforbindelser; modulernes interne pins er passive funktionssymboler, så kontrollen viser ikke elektrisk kvalifikation af modulets indre eller isolation. Det er ikke et byggeklart netdiagram, mens de eksplicit manglende komponentvalg og busbeskyttelser står åbne.

## Verificerede fabrikantdata

Kilde: `references/MEANWELL_RSP-3000_SPEC.pdf`, revision **2026-07-20**, især side 2–5 og 9–10. Værdier gælder under databladets betingelser; typiske værdier er ikke worst-case-grænser.

| Egenskab | RSP-3000-48, per modul |
|---|---|
| Nominel DC-udgang / mærkestrøm / mærkeeffekt | 48 V / 62,5 A / 3.000 W |
| Indbygget potentiometer, tilladt trimområde | 43–56 V |
| Indgang | 180–264 V AC, 47–63 Hz; AC/L og AC/N til samme enfasede net |
| Virkningsgrad | 91,5 % typisk |
| Power factor | 0,95 typisk ved 230 V AC og fuld last |
| AC-strøm / startstrøm | 16 A typisk ved 230 V AC / 60 A typisk ved 230 V AC |
| Lækagestrøm | < 2,0 mA ved 240 V AC |
| Udgangstolerance | ±1,0 %, inklusive setup-, line- og load-regulation ifølge note 3 |
| Ripple/noise | Højst 200 mV p-p under databladets 20 MHz-målemetode |
| OVP-grænse | **57,6–67,2 V**, shutdown; AC-genindkobling kræves |
| Overlast | 100–112 % rated output power; kontinuerlig CC eller CC med shutdown efter 5 s |
| Temperatur | −20 til +70 °C, med derating; 100 % load til 50 °C, faldende til 50 % ved 70 °C ved vandret installation |
| Temperaturskoefficient | ±0,05 %/°C, angivet for 0–50 °C |
| Remote sense | Kompenserer op til 0,25 V ledningsfald per modul |
| AUX | 12 V / 0,1 A, kun til remote ON/OFF-styring |
| Dielektrisk prøvespænding | I/P–O/P 3 kV AC, I/P–FG 2 kV AC, O/P–FG 0,5 kV AC |
| Mekanik | 278 × 177,8 × 63,5 mm; 4 kg; indbygget ventilator |

Dielektrisk prøvespænding er en testværdi. Den fastlægger ikke den tilladte kontinuerlige DC-offset mellem et moduls udgang og chassis/PE. Denne arbejds-/transientspænding skal afklares for den konkrete serieforbindelse og den ønskede flydende laboratorieudgang.

## Valgt bus og effektmargin

Begge moduler trimmes med deres indbyggede SVR til **55,0 V**; dette ligger under databladets 56 V maksimum. PV-funktionen aktiveres ikke i denne iteration. Fabriksbroen PV–PS beholdes på hvert modul. Outputtrim og spænding kontrolleres først enkeltvis uden effektregulator tilsluttet; ingen justering udføres på eksponerede net-/effektdele under last.

| Beregning ved 100 V / 40 A | Resultat |
|---|---:|
| Laboratorieudgang | 4.000 W |
| Busbehov med antaget 95 % DC-regulatorvirkningsgrad | 4.211 W |
| Nominel bus | 55 V + 55 V = 110 V |
| Busstrøm | 38,28 A |
| Effekt per seriemodul | 2.105 W |
| Effektandel af 3 kW per modul | 70,18 % |
| Ideal buck-duty ved 100 V ud | 90,91 % |
| Nominel margin over 100 V | 10 V |

Ved en antaget DC-regulatorvirkningsgrad på 90 % bliver busbehovet 4.444 W, busstrømmen 40,40 A og effekten 2.222 W per modul. Disse tal er beregninger, ikke målte virkningsgrader.

**62,5 A må ikke kombineres med 55 V og behandles som den kontinuerlige rating:** 55 V × 62,5 A = 3.438 W, over modulets 3.000 W. Effektloftet alene giver højst 54,55 A ved 55 V, før yderligere derating. Databladets PV-diagram kræver også reduceret strøm ved hævet spænding; det er ikke et løfte om konstant 62,5 A over hele trimområdet. Den planlagte belastning på 38,28–40,40 A ligger betydeligt lavere. Endelig strømgrænse ved SVR = 55 V skal verificeres i modelafklaringen og belastningstesten; tabellen gør ikke 54,55 A til en ny fabrikantgaranteret rating.

Kabinettets luftindløb til modulerne skal holdes **højst 50 °C ved fuld systemlast** som konstruktionsmål, og begge fabriksventilatorer/luftveje beholdes. Ved 60 °C viser den lineære deratingkurve omkring 75 % effekt = 2.250 W per modul; marginen til 2.222 W per modul er da for lille til at ignorere hjælpelast, tolerancer og tab. Modulernes automatiske termiske genstart må ikke automatisk genindkoble laboratorieudgangen efter en termisk fejl; systemets fault skal låses.

±1 % modultolerance giver en nominelt beregnet busvariation på ±1,10 V før temperaturdrift, ripple og DC-kabeltab. Ved 25 °C temperaturændring er ±0,05 %/°C en yderligere beregnet mulighed for op til cirka ±1,375 V på den trimmede 110 V-bus, hvis begge modulers drift falder i samme retning. Dette er et konservativt budget ud fra koefficienten, ikke en målt worst-case-kombination. Remote-sense-/ledningstab og de efterfølgende kraftkomponenters spændingsfald skal indgå i den belastede busminimumgrænse. LTC3779-forskningsfasen kan både bucke og booste, men det dokumenterer ikke 100 V / 40 A-regulering, strømfordeling eller stabilitet.

Det ældre regneeksempel med 95 % AC/DC-virkningsgrad og PF 0,98 er **ikke den valgte front-ends databladsværdier**. Bruger man i stedet modulets 91,5 % typiske effektivitet som budgetantagelse og 95 % DC-regulator, fås cirka 4.602 W fra AC, 21,06 A ved 230 V / PF 0,95 og cirka 602 W samlet varme. Disse typiske full-load-data er ikke verificeret ved hvert moduls faktiske 70 % loadpunkt. Samlet 32 A mærkestrøm for to fuldt belastede moduler giver ingen margin på brugerens 32 A gruppe; systemet dimensioneres og begrænses til den faktiske 4 kW-udgang plus tab, ikke fri adgang til to modulers fulde 6 kW.

## Serieforbindelse og flydende signaler

MEAN WELLs officielle FAQ, **Q39: “What are the applications with serial connection?”**, viser to isolerede udgange i serie for øget spænding. Fabrikanten kræver en diode antiparallelt over hver udgang for at undgå skade ved opstart. Diodens spændingsrating skal være større end V1 + V2, og peak forward surge current-rating større end rated current. FAQ'en anbefaler isolerede kontrolsignaler, fordi dele af signalground er forbundet til outputground.

RSP-3000-databladet har en modelanvisning for parallelkobling, men **ingen særskilt modelbeskrivelse af seriedrift**. Den generelle FAQ er derfor dokumenteret serieevidens; den erstatter ikke afklaring af RSP-3000-48's tilladte output-til-FG-offset, opstartssekvens og arbejde ved 55 V i dette system. Modelafklaring/integrationstest er et åbent frigivelsespunkt, ikke en brugerpræference, der skal besvares igen.

Forbindelserne i systemdiagrammet er:

- Nederste modul: −V → `BUS_NEG`, +V → `BUS_MID`.
- Øverste modul: −V → `BUS_MID`, +V → `BUS_POS`.
- Begge AC/L og AC/N forsynes fra samme 230 V net gennem den dimensionerede netbeskyttelse; begge FG og kapslingen går til PE.
- `BUS_NEG` og `BUS_MID` forbindes ikke permanent til PE. Chassisjord er fortsat påkrævet for net-/kapslingsdelene.
- Hver beskyttelsesdiode har **anode på modulets −V og katode på dets +V**. Dioden er normalt spærret, men klemmer en negativ moduludgang ved asymmetrisk opstart/stop.
- Ingen CS-, AUXG-, RCG-, TTL-status- eller sense-ledning forbindes direkte mellem de to moduler. Kontrol og overvågning udføres med dokumenteret isolering eller separate korrekt ratede potentialfrie kontakter.
- Senseforbindelser beholdes lokalt: hvert +S til eget +V og hvert −S til eget −V. Et moduls sense må ikke lægges over den samlede 110 V bus. Laboratoriets eventuelle remote sense ligger i sekundærregulatorens eget kredsløb.

Diodekrav til et senere konkret komponentvalg: VRRM mindst 200 V som foreløbigt projektniveau, IFSM > 62,5 A efter FAQ-kravet og tilstrækkelig gentagen/steady-state-strøm og termisk kapacitet til den faktisk mulige start-/fejlstrøm. En “1 A / 200 V” bootstrapdiode fra ADI's converterreference er ikke en dokumenteret 40 A reverse-beskyttelsesdiode. Der er endnu ikke valgt diodevarenummer, sikring eller kontaktor.

## OVP: 110 V nominelt er ikke maksimal busspænding

Hvert modul har et OVP-interval på **57,6–67,2 V**. To moduler kan derfor i et worst-case-grænsebudget nærme sig **2 × 67,2 V = 134,4 V**, før deres indbyggede OVP nødvendigvis udløser. Hvis kun ét modul er højt, kan summen eksempelvis være 67,2 + 55 = 122,2 V. Databladet dokumenterer ikke den dynamiske oversvingstop under disse fejl; 134,4 V er heller ikke et sikkert transientloft.

55 V-setpunktet ligger under den laveste angivne 57,6 V OVP-grænse, men setupdrift, remote sense og temperaturvariation skal verificeres. Trim må ikke hæves helt til 56 V for at hente marginal ekstra headroom uden denne analyse.

**Dette front-endvalg overholder ikke automatisk forskningsfasens proceduregrænse på 120 V input.** Systemdiagrammet skal vise en endnu uimplementeret uafhængig `BUS_OVP`/fejllåsning med shutdown af begge moduler, regulatorshutdown og en passende DC-/AC-afbrydelse. RUN = OFF slukker regulatoren; det klemmer ikke i sig selv front-endens bus. En langsom netkontaktor kan heller ikke alene bevise, at inputkondensatorer og MOSFETs aldrig overskrider deres spændingsgrænse.

LTC3779's 150 V driftområde og et 150 V MOSFET-varenummer giver ikke dokumenteret margin til 134,4 V plus kabelføring/switch-node-ringing. Endelig oversvings-/clampanalyse, busafbryderens responstid og højere spændingsratede MOSFETs/kapacitorer, hvor nødvendigt, skal afklares før dette system forbindes til effektfasen. Beskyttelsesdiode-rating beregnes mod fejlbus/transienter, ikke blot 110 V-setpunktet.

## Verificerede terminaler og kontrolben

RSP-3000-specifikationens side 9–10 indeholder følgende:

| Fysisk forbindelse | Ben | Funktion |
|---|---:|---|
| TB1 | 1 | AC/L |
| TB1 | 2 | AC/N |
| TB1 | 3 | FG, beskyttelsesjord |
| DC-effektterminaler | mærket +V og −V | Moduludgang; ingen numerisk pin-identitet angivet |
| CN1 / CN2 | 1 | RCG, remote ON/OFF ground |
| CN1 / CN2 | 2 | RC, remote ON/OFF |
| CN1 / CN2 | 3 | PV, output voltage programming |
| CN1 / CN2 | 4 | PS, reference voltage terminal |
| CN1 / CN2 | 5 og 7 | −S, lokal negativ remote sense |
| CN1 / CN2 | 6 | CS, current sharing, ikke anvendt i serie |
| CN1 / CN2 | 8 | +S, lokal positiv remote sense |
| CN3 | 1 | P OK GND |
| CN3 | 2 | P OK, relay contact |
| CN3 | 3 | P OK GND2 |
| CN3 | 4 | P OK2, TTL/open-collector status |
| CN3 | 5 | RCG |
| CN3 | 6 | RC |
| CN3 | 7 | AUXG |
| CN3 | 8 | AUX, 12 V / 0,1 A til remote-control |
| CN3 | 9 | OLP |
| CN3 | 10 | OL-SD |

CN1 og CN2 er internt forbundet. Headerne er HRS DF11-8DP-2DS og DF11-10DP-2DS eller tilsvarende; mating housings er DF11-8DS og DF11-10DS med passende DF11-kontakter. Den præcise kontaktvariant og ledningsdimension skal vælges ved kabelfremstilling. Fakta om headernavn/pinout giver ikke en færdig kabelstykliste.

**Valgt enable-princip er side 5, eksempel 3.2(C), default OFF:** på hvert modul går dets egen AUX (CN3-8) gennem en ekstern 1 kΩ til RC (CN2-2); dets RCG (CN2-1) forbindes til egen AUXG (CN3-7). En separat potentialfri kontakt mellem RC og RCG giver ON, når den lukker; åben kontakt giver OFF. Begge modulers kontakter skal slippe ved controllerreset, fault eller manglende hjælpeforsyning. Kontakternes coil-/kontrolside og indbyrdes isolation skal ratedes til de faktiske potentialer. 1 kΩ er angivet af fabrikanten; modstandens effekt-/spændingsrating er ikke fastlagt i fabrikantfiguren og skal vælges i styklistearbejdet.

Fabriksbroen CN2-3/PV til CN2-4/PS beholdes, når PV ikke bruges. CN3-9/OLP til CN3-10/OL-SD er fabriksbroen for CC med shutdown efter fem sekunder ifølge funktionsteksten. Side 6 har modstridende figurtekst om “Insert/Remove”; fabriksfunktion og fysisk variant skal verificeres før en bro ændres. Ingen broer ændres i systemdiagrammets standardopsætning.

**P OK relay-signalet** er low ved modulets udgang over 80 % af rated voltage og high/open ved power fail. Fabrikanten angiver højst 20 V / 500 mA, samlet 10 W, for den eksterne kreds. P OK2 er en anden, ikke tilsvarende isoleret TTL/open-collector-vej med højst 30 V / 10 mA. Brug af relay-signalet foretrækkes til isoleret status i systemdiagrammet. Kontrollér kontaktisolation for den konkrete variant; den viste interne isolering er ikke en fuld working-voltage-specifikation. “P OK” ved 80 % af 48 V er cirka 38,4 V per modul og er derfor **ikke** bevis for, at en 55 V-enhed eller den samlede bus er inden for regulatorens inputvindue. Begge modulspændinger og samlet bus skal måles særskilt.

## Installation og systemtest, der endnu mangler

- Dimensionér og vælg netfilter, sikringer, AC-kontaktor, kabling og kapsling efter den faktiske installation. To gange 60 A typisk inrush er et samlet startstrømsproblem; simpel addition er et budget, ikke en målt bølgeform eller garanteret maksimum.
- Hold alle FG/kapslingsforbindelser på PE og dokumentér continuity, leakage/touch current, primær/sekundær-isolation og tilladt flydende offset. Begge modulers <2 mA-databladsgrænser skal vurderes sammen med resten af systemet.
- Verificér 55 V under kold/varm drift, begge modules current-limit ved trim, load steps, ujævn opstart, enkeltmodulshutdown, AC-brownout og genindkobling. Test de antiparallelle dioders temperatur og energi uden at bruge den færdige belastning som prøvegenstand.
- Verificér den uafhængige bus-OVP og de faktiske maksimale DC-/switch-node-spændinger før 100 V drift. Modulerne må ikke kobles på det uafsluttede effektprint alene på grund af dette dokument.
- Verificér faultlåsning og udgangsafbryder, så automatisk front-end-recovery ikke genforsyner et prøveprint.
- Udfør temperaturtest ved 4 kW med kabinet, blæsere, luftvej og endelig omgivelsetemperatur. Fabrikantens ventilatorkøling/EMC-certificering af netmoduler er ikke systemets 4 kW-validering.

Fabrikantens generelle installationmanual er også hentet. Den skal bruges sammen med den modelspecifikke specifikation; hvor terminaltorque/tabeller er forskellige, skal modelafklaring afgøre den endelige værdi. Der er ikke indsat en vilkårlig torque i kabelmanualen.

## Andre dokumenter og fravalg

De allerede hentede ADI/TI-kilder indeholder ingen dokumenteret enfaset isoleret 4,5 kW AC/DC-front-end:

- LTC3895 er afvist som direkte 100 V-regulator: angivet output 0,8–60 V og SENSE-ben med 65 V absolute maximum.
- LTC3779 og DC2456A er DC/DC-kilder. DC2456A-manualen dokumenterer 16–120 V input og 48 V / højst 10 A ud, med fuld strøm angivet fra 21 V input. Den er en 480 W reference, ikke en isoleret 4 kW netdel. Dens ADI-stykliste indeholder verificerede reference-komponentnavne, men output-kondensatorer på 63 V og 60 V MOSFETs i 48 V-området må ikke kopieres til 100 V udgang.
- UCC21520's galvaniske signal-/gatedriver-isolation er ikke 4 kW energi-isolation eller en AC/DC-front-end.
- RSP-2400-48 undersøges ikke videre nu; RSP-3000-48 har den ønskede nominelle effektmargin. Der fremsættes ingen nye verificerede RSP-2400-specifikationer.
- Et enkelt 110–130 V / mindst 4,5 kW AC/DC-modul er ikke udvalgt; to dokumenterede 3 kW-moduler er den konkrete arbejdsarkitektur.

## Kilder og bevis for adgang

Normal HTTPS med miljøets eksisterende proxy og bevaret TLS-verifikation lykkedes den 9. oktober 2026 til producentens **meanwell.com** uden `www`. Tidligere forsøg mod `www.meanwell.com` gav HTTP 403; de blev ikke gentaget uændret. Den fungerende bare-host-rute er en almindelig officiel fabrikant-URL og ændrer ikke proxy eller netværkskontrol. Det gættede `RSP-3000-MANUAL.PDF` gav HTTP 404; funktionmanualen findes i stedet inde i specifikations-PDF'en, og dens klikbare installationslink blev fulgt på samme officielle host.

Verificerede filer og SHA-256 ligger i `references/frontend-sources.json`:

| Officiel kilde, HTTP 200 | Lokal fil | SHA-256 |
|---|---|---|
| <https://meanwell.com/Upload/PDF/RSP-3000/RSP-3000-SPEC.PDF> | `MEANWELL_RSP-3000_SPEC.pdf` | `1dd3a8d722ecb0de772aac083baca471db785b7f5e90079450b290bc0e7fc7a9` |
| <https://meanwell.com/Upload/PDF/Enclosed_Type_EN.pdf> | `MEANWELL_Enclosed_Type_EN.pdf` | `3e40e59123e5c23d498a468e851f89e5a9d89d99fdbdc82fe8c19348294e4940` |
| <https://meanwell.com/qa.aspx>, Q39 | `MEANWELL_FAQ.html` | `d51fe7c94abcf1bc5e79f84d2a4b2a3dfe12851cdfd7c388ddb58ce1ae916c8a` |

Tekstudtræk er gemt sammen med originalerne. SHA-256 identificerer den faktisk læste fil; det er ikke en fabrikant-signatur eller en separat certificering. Offentlige datablade kræver ingen brugerhemmeligheder. Producentadgang er nu løst for dette valg; fysisk kvalifikation og de uimplementerede systemkredsløb er de resterende begrænsninger.
