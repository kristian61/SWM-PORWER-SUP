# Beskyttelse, små belastninger og fysisk testplan

Dette dokument fastlægger testkrav til den kommende komplette strømforsyning. Det eksisterende passive måleprint kan ikke regulere eller begrænse strøm. Ingen af de fysiske prøver nedenfor er udført, og dokumentet er ikke en erklæring om beståede tests.

## Bekræftet anvendelse og foreløbige acceptmål

Brugeren har angivet 230 V AC på en dedikeret 32 A kreds, galvanisk isoleret og flydende udgang, justerbar 0–100 V udgang og op til 40 A kontinuerligt. Strømgrænsen skal også kunne indstilles til små prøveprint. 100 V og 40 A samtidigt svarer til 4 kW. AC/DC-arbejdsvalget er nu 2 × RSP-3000-48 ved 55 V hver; dets systemintegration er uverificeret. Enkeltfaseudkastet bruger LTC3779, men den komplette effektregulator og beskyttelser er endnu ikke realiseret eller afprøvet.

En strømgrænse angiver den største strøm, forsyningen forsøger at levere. Den tvinger ikke en rask belastning til at optage denne strøm. Belastningens tilladte forsyningsspænding skal stadig overholdes. Når strømgrænsen nås, skal udgangsspændingen falde, og forsyningen skal vise CC; i normal spændingsregulering vises CV. At indstille 100 V og en lille strømgrænse er ikke en brugbar måde at forsyne en operationsforstærker, som kræver en langt lavere spænding. En negativ forsyningsskinne kræver desuden en faktisk bipolar konfiguration eller en separat isoleret forsyning; en flydende enkeltudgang skaber ikke automatisk ±-forsyning.

Følgende værdier er **foreløbige design- og testmål**, som skal gennemgås med den valgte regulator, målekæde og brugerens behov. De er ikke garanterede specifikationer:

| Funktion | Foreløbigt mål | Betydning for test |
|---|---|---|
| Højstrømsområde | 0–40 A, indstillingstrin højst 10 mA | Måle- og reguleringsfejl højst ±(0,5 % af aflæsning + 20 mA) efter kalibrering |
| Lavstrømsområde | 0–0,5 A, indstillingstrin højst 1 mA | Måle- og reguleringsfejl højst ±(1 % af aflæsning + 0,5 mA), verificeret fra 1 mA til 500 mA |
| Spænding | 0–100 V, indstillingstrin højst 10 mV | Foreløbig DC-fejl højst ±(0,1 % af aflæsning + 10 mV) efter kalibrering |
| Strømindstilling 0 A | Udgang deaktiveret | Skal ikke fortolkes som en garanteret mikroampereforsyning |
| Spændingsindstilling 0 V | Udgang deaktiveret og afladet | Aktiv CV-regulering præcist ved 0 V er endnu ikke løst; minimum reguleret spænding skal måles og oplyses |
| Udgang slået fra | Under 1 V inden 5 s fra 100 V | Gælder eget specificerede udgangskredsløb; ekstern energikilde og ekstern kapacitans behandles særskilt |
| Opstart/reset | Udgang deaktiveret | Skal også gælde MCU-reset, brownout og tab af styreforsyning |
| Områdeskift | Udgang deaktiveres før skift | Ny strømgrænse verificeres, før udgangen igen kan aktiveres |

En enkelt fejl i software må ikke omstille lavstrømsudgangen til 40 A. Lavstrømsområdet kræver en selvstændig fysisk grænse eller anden verificeret hardwarebegrænsning. Beskyttelseskredsløbets valgte fejltilstand skal være dokumenteret. De foreløbige nøjagtighedsmål omfatter ikke en garanti for, at enhver halvleder overlever en fejl.

Det nyere studie i `low-current-output.md` undersøger i stedet særskilte 20 mA- og 200 mA-områder. De er uimplementerede kandidater og opfylder ikke i sig selv tabellens oprindelige 500 mA-mål. Områdevalg og præcision kræver et samlet design og fysisk validering.

Rippel, CC-transienter, laveste regulerede spænding, tilladt udgang-til-jord-spænding og kølestøj mangler endelige mål. Testene skal registrere disse værdier; de må ikke betegnes bestået uden et fastlagt acceptkriterium. Regulatoren antages foreløbigt at levere strøm, ikke at kunne optage regenerativ energi fra batterier eller motorer.

## Hvorfor en 1 mΩ shunt ikke er tilstrækkelig alene

En samlet 1 mΩ fireterminal-shunt giver 40 mV ved 40 A og afgiver 1,6 W. Ved 10 mA bliver signalet kun 10 µV; ved 1 mA er det 1 µV. Et samlet inputrefereret offset på eksempelvis 25 µV svarer derfor til 25 mA fejl. Dette er et regneeksempel og ikke en angivelse af et bestemt sensor-datablad.

Med forstærkning 50 og en ideal 16-bit ADC med 3,3 V fuldskala bliver én kode cirka 50,4 µV på ADC-input, svarende til 1,01 mA gennem 1 mΩ shunten. Reelle offset-, støj-, reference- og temperaturfejl kommer oveni. Et stort antal ADC-bit alene gør ikke målekæden præcis ved små strømme.

Et muligt lavstrømsmåleområde kan benytte en separat 0,1 Ω Kelvin-shunt: 500 mA giver 50 mV og 25 mW; 1 mA giver 100 µV. Shunten må **ikke** kunne udsættes for 40 A i lavområdet: det ville afsætte 160 W. Områdekontakt, bypass, hardwarebegrænsning, fejlregistrering og shuntens pulseffekt skal derfor indgå i det faktiske kredsløb. 0,1 Ω er her en beregningsværdi, ikke et valgt komponentvarenummer eller et færdigt kredsløb.

Gain-ændring på den samme shunt kan forbedre ADC-opløsningen, men ændrer hverken shuntens inputrefererede offset eller den energi, belastningen modtager ved en fejl. En højopløselig, langsom måle-ADC må heller ikke være den eneste kilde til hurtig overstrømsbeskyttelse. Det passive måleprints cirka 8 kHz differentialfilter erstatter ikke cyklus-for-cyklus strømbegrænsning i effekttrinnet.

## Lagret energi og en begrænsnings faktiske virkning

For det **ældre, hypotetiske systemberegningspunkt** 4 × 470 µF = 1.880 µF gælder `E = ½ × C × V²`. Denne bank findes ikke i den aktuelle BOM. Den faktiske enkeltfase har nominelt 96 µF; fire sådanne faser ville have 384 µF og lagre 1,92 J ved 100 V. De aktuelle scenarier findes i `exports/analysis/design_budget.json` og `low-current-output.md`. Tabellen og 470 Ω-afladningseksemplet nedenfor beholder det større oprindelige beregningspunkt:

| Kondensatorspænding | Lagret energi |
|---:|---:|
| 5 V | 23,5 mJ |
| 15 V | 211,5 mJ |
| 100 V | 9,4 J |
| 120 V | 13,54 J |

Hvis bulk-kondensatoren er direkte forbundet med DUT-terminalen, kan den afgive denne energi, selv om buck-regulatoren allerede har stoppet sine gates. Et kortslutningsforløb afhænger af ESR, ESL, kabler og fejlimpedans. En DC-strømgrænse på eksempelvis 10 mA siger derfor ikke, at den første strømspids er 10 mA.

En beregning med konstant 100 V, 40 A og 100 µs giver yderligere 0,4 J fra et aktivt effekttrin. Den faktiske fejlenergi skal måles som `integral(v_DUT(t) × i_DUT(t) dt)`, inklusive udgangskondensatorer og reaktionstid. Der findes ikke ét universelt energital, som beskytter alle små print.

Lavstrømsarkitekturen bør placere hurtig analog strømbegrænsning **mellem bulk-energilager og lavstrømsterminal**, med så lidt kapacitans som muligt efter begrænseren. Et selvstændigt lavstrømsudtag er en mulighed; det er endnu ikke en leveret funktion. Begrænserens effekttransistor skal vælges ud fra DC- og pulse-SOA ved den reelle spænding og temperatur. 100 V spændingsfald ved 0,5 A er 50 W; en almindelig lille MOSFET kan ikke vælges alene efter dens ampere-rating.

Som størrelsesorden lagrer 10 µF ved terminalen 1,125 mJ ved 15 V, men 50 mJ ved 100 V. Selv denne begrænsede kapacitans kræver vurdering for det tilsluttede print. Den samlede terminalkapacitans, inklusive kabler og ekstern DUT-kapacitans, skal oplyses for begge områder. Bulk-kapacitans, ekstra filterkondensatorer og flyback-veje må ikke kunne omgå lavstrømsbegrænseren.

### Beregning af kontrolleret afladning

For en modstand `R` og kapacitans `C` er spændingen efter tiden `t`: `V(t) = V0 × exp(−t/(R×C))`. En foreløbig, koblet 470 Ω afladningsmodstand med 1.880 µF giver cirka 4,07 s fra 100 V til 1 V; med +20 % kapacitans bliver tiden cirka 4,88 s. Begge tal er beregnede og forudsætter ingen tilbageført energi.

Ved 100 V er initial effekt 21,3 W. Ved 120 V er den 30,6 W, og den nominelle lagrede energi er 13,54 J. Modstand, omskifter og køling skal derfor have verificeret pulseffekt, maksimal kontinuerlig effekt ved fejl, spændingsrating og temperaturderating. En chassis-modstand i 50 W-klassen kan undersøges som kandidat, men en effektangivelse uden korrekt montage er ikke en færdig dimensionering.

En permanent 470 Ω modstand ville selv trække 213 mA ved 100 V og forstyrre lavstrømsmålingen. Afladning skal derfor være en defineret tilstand, adskilt fra normal udgangsregulering. Placering og shuntforbindelse skal sikre, at intern afladningsstrøm ikke fejlagtigt vises som strøm leveret til DUT. Afladningskredsløbet skal også håndtere udgangsafbryderens placering: en afbrudt terminal må ikke efterlade en anden kondensatorbank uden afladningsvej.

## Beskyttelsesfunktioner og fejlrespons

| Funktion | Påkrævet adfærd | Fysisk verifikation |
|---|---|---|
| Fasestrømgrænse | Stop eller begræns hver fase inden mætning og transistorernes pulsegrænse | Mål fasestrøm, gate og switch-node samtidigt; konkret peakgrænse og tid fastlægges ud fra valgte komponenter |
| Samlet CC | Hold den indstillede strøm i både belastningsspring og ved kortslutning | Mål terminalstrøm over tid, inklusive første strømspids og overgang mellem CV og CC |
| Lavstrømsfejlgrænse | Hardware begrænser også ved stoppet MCU | Injicér styrefejl ved reduceret busspænding, og mål faktisk DUT-strøm og energi |
| OVP | Uafhængig comparator stopper energitilførsel; udgangen fejllåses | Injicér målesignal under energi-begrænsede forhold, og mål threshold, forsinkelse, gateslukning og terminalspænding |
| Brugervalgt OVP | Grænsen skal kunne passe til belastningens maksimale spænding | En ren 100/105 V hardwaregrænse beskytter ikke en 5 V belastning; kontroller brugergrænse før aktivering |
| High-side kortsluttet | Stop bulk-energien gennem en særskilt afbryder/beskyttelsesvej | Analysér fejlstrøm og verificér DC-brydeevne; almindelig gate-shutdown er ikke nok |
| Gate-interlock | Ingen samtidige high-side/low-side gates | Mål ved opstart, reset, brownout og signalfejl; deadtime skal passe til den valgte driver og MOSFET |
| For varm effektkomponent | Reducér eller stop før komponentens tilladte temperatur overskrides | Sammenhold sensor og uafhængig temperaturmåling på varmeste komponent |
| Sensor-/blæserfejl | Defineret fejltilstand med udgang deaktiveret | Afbryd/kortslut termistorer, blokér fan og fjern tacho under kontrolleret belastning |
| Åben remote-sense | Udgang må ikke drive mod maksimal spænding | Afbryd begge senseledninger enkeltvis; hold spænding under den indstillede OVP-grænse |
| Tilbageføring | Specifik blokering eller energiabsorbering, også når forsyningen er slukket | Test først med isoleret, strømbegrænset kilde; tilslut ikke batteri som første forsøg |
| Reset eller mistet hjælpespænding | Gates slukket, udgang afbrudt, ingen automatisk genaktivering | Kontroller fysisk terminaltilstand, ikke alene displayets tekst |

OVP- og CC-sløjfer må ikke dele en enkelt fejl, som kan hæve både reguleringssetpoint og beskyttelsesgrænse uden registrering. De konkrete uafhængige referencer, comparatorer, latch og afbryder er endnu ikke designet. Temperaturgrænser, comparator-forsinkelser og peakstrømme skal føjes til denne tabel efter komponentvalget; de må ikke erstattes af gættede IC-grænser.

## Trinvis fysisk validering

Hvert trin kræver et dateret måleark med hardwareversion, komponentversioner, forbindelsesdiagram, instrumenttype, måleusikkerhed og resultat. En fejl føres tilbage til design og retestes, før der tilføres større energi. De næste trin er en plan, ikke udførte prøver.

1. **Dokument- og CAD-kontrol uden forsyning.** Sammenhold alle IC-ben med officielle datablade, polaritet og BOM med diagram, footprint og mekaniske mål. Kør ERC/DRC og kontrollér netliste, strømveje, komponentrating, clearance, krybeafstand og adskillelse mellem net, isoleret sekundær og betjeningsinterface. Isolation og afstande kræver kendt standard, højde, forureningsgrad, overspændingskategori og tilladt udgang-til-jord-spænding. En vilkårlig KiCad-clearance kan ikke attestere disse forhold.
2. **Passivt måleprint.** Inspicér lodninger og mål modstande, kortslutninger og isolation mellem signalgrupper uden effektforsyning. Brug derefter en strømbegrænset DC-kilde og mål delere ved 0, 5, 15, 50, 100 og 120 V, først når modstandsseriens spændingsrating og printets afstande er verificeret. For den nominelle 40:1 deler er idealværdier 0; 0,125; 0,375; 1,250; 2,500 og 3,000 V. Registrér gain/offset og støj; ingen DUT forsynes gennem måleprintet.
3. **Hjælpeforsyninger og kontrol.** Effektbus er frakoblet. Verificér analog/reference/driver-forsyninger, reset, setpoints, hardware-OFF, OVP-latch, sensorfejl og rækkefølgen for enable. Ingen fejl skal kunne generere et gate-signal. Den konkrete forsyningssekvens kontrolleres mod datablade.
4. **Gate-driver med reduceret energi.** Start med isoleret, strømbegrænset DC-bus og dummy-load ved lav spænding, hvis controllerens verificerede driftsspænding tillader det. Mål hver gate i forhold til dens egen source, ikke kraftjord. Kontrollér amplitude, deadtime, Miller-turn-on og opstartssekvens for hver fase, før alle faser aktiveres. Hvert scope-signal kræver probe med korrekt spændings-, transient- og common-mode-rating; jordklemmen på et jordet oscilloskop må ikke gøre den flydende udgang jordbundet.
5. **Én fase og derefter flerfase.** Verificér spolestrøm, peakgrænse, ringing, strømfordeling og switching-tab ved trinvist øget bus og last. Fire faser skal have dokumenteret faseforskydning og stabil strømfordeling. Snubbervalg foretages efter målt ringing; nye snubbertab og varme registreres.
6. **CV/CC og lavstrømsområde.** Kalibrér strøm ved mindst 0, 1, 5, 10, 50, 100 og 500 mA i lavområdet og 0, 0,1, 1, 5, 10, 20 og 40 A i højområdet. Brug en uafhængig kalibreret shunt eller strømstandard. Prøv CV og CC ved mindst 1, 5, 15, 50 og 100 V, hvor kombinationen er inden for alle ratings. Mål CC med resistiv belastning såvel som elektronisk belastning, hvis regulatorer i den elektroniske belastning påvirker stabiliteten. Værdier tæt på 0 V må ikke betegnes regulerede, før de er verificeret.
7. **Dynamik og små-printbeskyttelse.** Mål opstart til tilsluttet last, lastspring, korte/lange kabler og kortslutning via defineret testfixture. Prøv lavområdet ved 5, 15 og 100 V uden at bruge et rigtigt prøveprint som offer. Registrér strømspids, varighed, minimum/maksimum spænding, CC-indsvingning og integreret fejlenergi. Test et lastspring mellem 10 % og 90 % af den indstillede strøm, begge veje. Fastlæg tilladt terminalenergi for den konkrete DUT-type, før en beskyttelsespåstand fremsættes.
8. **Fejlinjektion.** Prøv MCU-stop, forkert setpoint, tab af reference, åbne/kortsluttede sense- og temperatursignaler, fan-fejl og fejl under områdeskift. Start ved reduceret bus og energi. Dokumentér hver fejl med målt gate- og terminalrespons. En destruktiv transistorfejl kræver en separat testfixture og analyseret brydeevne; den må ikke fremkaldes ved en almindelig kortslutningstråd.
9. **Termisk drift og fuld effekt.** Brug 4 kW-klassificeret belastning og registrér AC-inputeffekt/PF, outputeffekt, virkningsgrad, hver fase, MOSFET/spole/shunt/stiktemperatur og blæserdrift. Kræv mindst to timers sammenhængende drift ved 100 V/40 A og derudover termisk ligevægt, defineret som mindre end 1 °C ændring over 30 min for alle overvågede hotspots. Gentag relevante varmeprøver ved lavere spænding og 40 A, fordi lednings- og transistorstrømmen fortsat er høj. Det aktuelle systembudget med 91,5 % typisk AC/DC-virkningsgrad og antaget 95 % DC-regulator giver cirka 602 W varme; det ældre 95 %/95 %-eksempel gav 432 W. Begge er budgetter, ikke målinger. Køling må ikke kvalificeres ud fra den ældre værdi alene.
10. **Isolation, net og EMC.** Kun det komplette mekanisk samlede system kan testes for PE-kontinuitet, elektrisk styrke, læk-/berøringsstrøm, inrush og ledningsført/udstrålet støj. Prøvespænding og testmetode vælges fra den relevante standard og isolationstype; der er ikke fastsat et vilkårligt hipot-tal her. Prøven skal inkludere alle forbindelser til kabinet, USB, display og måleudstyr, som ellers kan ødelægge udgangens flydende egenskab.

## Målepunkter og praktisk fejlsøgning

Navnene i denne tabel er funktionsnavne. TP-numre skal hentes fra det faktiske KiCad-projekt; et TP-navn her angiver ikke, at en testpad allerede findes.

| Signal | Hvad målingen afgør | Normal reference |
|---|---|---|
| Isoleret DC-bus +/− | Front-end-droop, inrush og tilbageført energi | Busretur; klassificeret differentialprobe |
| OUT+/OUT− ved terminal | Faktisk DUT-spænding, OVP, ripple og afladning | Terminal OUT−; galvanisk isolation opretholdes |
| Bulk+ og lavstrømsterminal | Om begrænseren faktisk adskiller energi fra DUT | Begge sider måles under samme fejlforløb |
| Kelvin I+/I− | Strøm og CC-grænse uden kablers spændingsfald | Differential over valgt shunt |
| Lavområdevalg og hardware-OFF | Om den rigtige fysiske strømgrænse er valgt | Kontrolreference, hvis isolationsforbindelsen tillader det |
| V-set/I-set og måleoutputs | Forkert indstilling eller fejl i gain/offset | Analog reference |
| OVP-output/latch og gate-enable | Beskyttelsens måle-til-slukket-forsinkelse | Den konkrete digitale/analoge reference |
| Gate-source for hver MOSFET | Deadtime og fysisk gateslukning | Den pågældende MOSFET-source |
| Temperatursignal og fan-tacho | Overtemperatur eller sensor-/blæserfejl | Kontrolreference; sammenhold med uafhængigt termometer |

Begynd fejlsøgning med effektbus frakoblet: verificér hjælpeskinner, hardware-OFF og målekæde. Hvis displayet viser forkert strøm, sammenlign Kelvin-shuntspændingen med den uafhængige måler, derefter sensoroutput, reference og ADC. Hvis CC-grænsen er rigtig ved DC men fejler ved kortslutning, kontrollér den terminaltilsluttede kapacitans og den hurtige hardwarevej. Hvis udgangen hopper op ved åbent sensekabel, er det en beskyttelsesfejl, ikke en kalibreringsfejl. Hvis der stadig er spænding efter OFF, mål begge sider af udgangsafbryderen og kontrollér afladningsvejen samt ekstern tilbageføring.

## Hvad en KiCad-kontrol kan og ikke kan afgøre

En bestået ERC/DRC dokumenterer kun de kontrollerede CAD-regler for den konkrete projektversion. Den dokumenterer ikke 4 kW kontinuerlig drift, transistor-SOA, spolekernetab, CV/CC-stabilitet, små-printbeskyttelse, isolation, elektromagnetisk støj eller afbrydernes DC-brydeevne. Alle disse resultater kræver beregninger med verificerede komponentdata og de relevante fysiske målinger ovenfor.

Den endelige frigivelse skal derfor indeholde en sporbar liste over **beregnede**, **simulerede**, **CAD-kontrollerede** og **fysisk målte** egenskaber, inklusive manglende tests. Der foreligger endnu ingen fysisk målerapport for en komplet 100 V/40 A laboratorieforsyning.
