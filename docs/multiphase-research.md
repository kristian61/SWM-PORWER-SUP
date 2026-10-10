# Fire LTC3779-faser med fælles ITH — afgrænset forundersøgelse

Status pr. 9. oktober 2026: **elektrisk begrundet forskningshypotese, ikke en dokumenteret eller valideret firefaset løsning**. Undersøgelsen gælder fire LTC3779-effektfaser på fælles VIN/VOUT, matched shunts og eksterne PLLIN-clocks med 0°, 90°, 180° og 270° faseforskydning. Der er ikke tegnet eller frigivet et native firefasekredsløb ud fra denne hypotese. Forsyningssekvensen og håndtering af en slukket/fejlramt fase skal løses før en sådan konstruktion konkretiseres.

Dette dokument er næste designinput og manualappendiks. Det ændrer ikke enkeltfasens aktuelle status og dokumenterer ikke 100 V / 40 A-drift, justerbar laboratorie-CC/CV eller præcis lavstrømsbeskyttelse.

## Dokumentgrundlag og fabrikantstøtte

Den primære kilde er det faktisk hentede officielle **LTC3779-datablad, Rev. A**, lokalt `references/LTC3779.pdf` og `references/LTC3779.txt`, fra:

<https://www.analog.com/media/en/technical-documentation/data-sheets/ltc3779.pdf>

Dokumentets identitet og SHA-256 fremgår af `references/sources.json`. Sidehenvisninger nedenfor er databladets trykte sidenumre.

LTC3779-databladet, DC2456A-manualen/-diagrammet, produktets officielle dokumentoversigt og den tilknyttede demoartikel blev gennemgået. Der blev **ikke fundet et konkret ADI-referencekredsløb med parallelle LTC3779 og fælles ITH**, og der blev heller ikke fundet et udtrykkeligt forbud mod denne forbindelse. Fravær af en fundet reference beviser hverken producentens godkendelse eller, at arkitekturen er umulig.

Den officielle dokumentoversigt på <https://www.analog.com/en/products/ltc3779.html> viser den enkelte DC2456A-fase. Den tilknyttede designnote om pass-thru handler om LT8210 og etablerer ikke en LTC3779-multifasereference. ADI's EngineerZone-søgning på `ez.analog.com` og sitesøgningens script på `assets2.analog.com` gav HTTP 403 gennem den normale proxy; den statiske søgeside havde ingen brugbare resultater. Disse begrænsninger er ikke forsøgt omgået.

## Hvad databladet faktisk understøtter

| Databladside | Verificeret egenskab | Betydning for hypotesen |
|---|---|---|
| 3 | Fejlforstærkerens gm er typisk 1,5 mS | ITH er en strømstyrende gm-udgang; flere udgange kan analyseres som summerede strømme, men databladet kvalificerer ikke fælles ITH mellem flere IC'er |
| 11 | ITH er fejlforstærkerens udgang og styrer current-comparator-tærsklen | Fælles ITH kan principielt give en fælles strømkommando |
| 14–16 | Induktorstrømmen styres via ITH; buck bruger valley current, boost bruger peak current | Middelstrømmen afhænger også af ripple og driftsområde |
| 17 | IAVG-sløjfen trækker ITH ned, når den målte strøm overskrider grænsen | En lokal IAVG-sløjfe kan påvirke alle faser på fælles ITH |
| 12 og 17–18 | PLLIN synkroniserer oscillator til ekstern clock, 50–600 kHz; lokal FREQ-modstand skal beholdes | Clockforskydning er understøttet som inputfunktion; den er ikke et strømfordelingssignal |
| 31–32 | ITH-netværket kompenserer sløjfen; outputkapacitet og lasttransienter indgår i stabilitetsvurderingen | En enkeltfasereferences kompensation kan ikke uden analyse overføres til fire faser |

Ud fra disse egenskaber er fælles ITH en begrundet analog forskningsarkitektur. Den er ikke producentdokumentation for stabil, fejltolerant eller nøjagtig firefaset drift.

## Summeret gm og kompensation

Hvis alle fire interne spændingsfejlforstærkere er aktive og ser samme feedbacksignal og reference, summeres deres småsignalstrømme ideelt på fælles ITH:

`gm_total = gm1 + gm2 + gm3 + gm4 ≈ 4 × 1,5 mS = 6 mS`

Dette er en typisk, lineariseret beregning. Reference-, gm-, clamp- og temperaturvariationer er ikke fjernet ved forbindelsen.

Fire identiske lokale ITH-kompensationsnetværk i parallel giver ideelt:

`Zcomp_total(s) = Zcomp_enkelt(s) / 4`

For et netværk med en serie-RC-gren til signalground og en lille kondensator direkte fra ITH til signalground er den præcise ækvivalens for fire identiske grene:

| Komponent | Per fase, eksempel | Fire grene i parallel, ækvivalent |
|---|---:|---:|
| Serie-R | 10 kΩ | 2,5 kΩ |
| Serie-C | 10 nF | 40 nF |
| Direkte shunt-C | 100 pF | 400 pF |

Seriegrenens tidskonstant forbliver `10 kΩ × 10 nF = 2,5 kΩ × 40 nF = 100 µs`; nulpunktet forbliver cirka 1,59 kHz. Samtidig bliver det idealiserede produkt `gm_total × Zcomp_total` det samme som for én fejlforstærker med én af disse grene. Værdierne er **et regneeksempel**, ikke valgt kompensation til den færdige laboratorieforsyning.

Den samlede power-stage-transferfunktion skal stadig med i analysen. Hvis fire identiske strømstyrede faser, samlet udgangskapacitet og last skaleres tilsvarende, kan den idealiserede normaliserede outputdynamik ligne enkeltfasens. Hvis udgangskapaciteten holdes uændret, eller effektfaser, shunter, belastning og sensenets ikke følger denne skalering, gælder den forenklede lighed ikke. ESR-/ESL-nulpunkter, fasedelay, kabling og buck/boost-overgangen indgår også.

**Én uændret kompensationsgren sammen med fire aktive fejlforstærkere er ikke den samme sløjfe som enkeltfasen.** Den ændrer `gm × Zcomp` og kan øge sløjfeforstærkningen. En central gren skal beregnes ud fra det samlede system; den må ikke vælges ved at kopiere ét referenceprint. En “master/slave”-betegnelse deaktiverer heller ikke automatisk de øvrige interne fejlforstærkere. LTC3779 har ikke i de gennemgåede kilder en dokumenteret slavefunktion, som blot kan antages aktiveret ved ændring af VFB.

Databladets side 31–32 beskriver vurdering med den konkrete kapacitet/layout og lastspring samt observation af ITH-respons. Simulation og fysisk sløjfemåling skal omfatte både spændingsregulering og strømbegrænsning; et analytisk RC-ækvivalent eller KiCad ERC er ikke et stabilitetsbevis.

## Fælles strømkommando er ikke garanteret middelstrømsdeling

I buck bestemmer ITH en valley-current-tærskel. Ideelt er en fases middelstrøm:

`Iavg,fase ≈ Ivalley,fase + ΔIL,fase / 2`

Samme ITH og samme shuntværdi giver derfor ikke automatisk samme middelstrøm, hvis induktans eller ripple varierer. Controllerens current-comparator-offsets, gain, temperatur, slope compensation og interne begrænsninger indgår også. Side 3 angiver 70–110 mV for den **maksimale** buck-sensetærskel under de angivne testbetingelser. Dette er ikke en matching-specifikation ved vilkårlig ITH eller præcis 10 A; det kan ikke omsættes til et løfte om fire lige strømme.

90° PLLIN-forskydning giver forskudte oscillatorclocks. Den må ikke beskrives som verificeret strømfordeling eller præcis 90° forskydning mellem alle faktiske MOSFET-pulser under alle driftstilstande. I valley control påvirker comparator-timing den faktiske high-side-tændtid, og pulse skipping kan udelade pulser helt.

Alle fire faktiske fasestrømme skal kunne måles separat. Fejl-/temperaturgrænser og komponentkapacitet skal baseres på en dokumenteret maksimal faseubalance; 40 A total betyder ikke i sig selv præcis 10 A i hvert effekttrin.

## Driftsområder og MODE

Side 15 angiver maksimal buck-only duty til **91,67 %**. Ved 100 V ud og 110 V ind er ideal duty **90,91 %**, tæt på denne grænse. Busfald, tolerance og kraftdelens spændingsfald kan flytte en fase ind i buck-boost. Små lokale forskelle mellem faser kan give forskellig transitionstilstand. Her er den simple fælles valley-current-model utilstrækkelig; side 16 beskriver skift mellem buck- og boostoperation inden for en clockcyklus.

Forced CCM giver den klareste første analyse af kontinuerlig strømfordeling, men **tillader negative induktorstrømme og tilbageført energi**. Side 17 beskriver også regulatorens mulighed for at sende strøm fra output til input. Den valgte AC/DC-front-end må ikke antages at kunne absorbere denne energi. Bus-OVP og energihåndtering er derfor en del af systemanalysen.

Pulse skipping begrænser reverse current i buck-/boost-regionerne og er relevant til lav last, men side 16–17 beskriver tilladt reverse current og smalle CCM-bånd tæt på buck-boost-overgangen. Faserne kan desuden skippe uafhængigt. MODE-valget skal således vurderes mod strømfordeling, ripple, cirkulerende strøm, busenergi og beskyttelse af små prøveprint. Ingen af tilstandene dokumenterer præcis lavstrøms-CC eller active CV ned til 0 V.

## IAVG, reference og soft start

Hver lokal IAVG-sløjfe kan trække fælles ITH ned, så den først aktive clamp kan begrænse alle fire faser. Fire lokale grænser bliver ikke automatisk en præcis samlet 40 A-grænse. Threshold-, shunt- og filtertolerancer samt overgangen mellem aktive/inaktive clamps skal indgå i strømreguleringsanalysen. Databladets side 21 angiver filter-/sløjfekrav for IAVG; disse er ikke en dokumenteret firefasekompensationsopskrift.

Hvis SS forbindes fælles, summeres de fire typiske 5 µA soft-start-strømme til cirka 20 µA. Der kræves derfor fire gange enkeltfasens fælles SS-kapacitans for samme ideelle rampetid. Fire lokale identiske SS-kondensatorer på den samme net giver allerede denne samlede kapacitans. RUN-, UVLO-, OTP- og VINOV-fejl kan trække en lokal SS lav; virkningen af sådanne hændelser på en delt SS-/ITH-net skal analyseres sammen med alle gate-stop og systemets fejllåsning. Et delt analogt signal erstatter ikke hardware-shutdown af alle faser.

## Konkret begrænsning ved slukket eller fejlramt fase

Databladets **side 2** angiver absolute maximum for **ITH, SS og PLLIN i forhold til den lokale V5**. Side 14 beskriver, at RUN-shutdown slukker hovedkontrol og de lokale DRVCC-/V5-regulatorer. Dermed kan en fase med lav/slukket V5 få fælles ITH eller clock drevet fra de øvrige aktive faser uden, at dens egne pin-grænser er overholdt.

Forsyningssekvens og fasefejl er derfor et konkret uløst konstruktionspunkt. **Native firefasekonstruktion tegnes ikke**, før der er en dokumenteret løsning, som holder alle fælles signaler inden for hver fases pin-grænser under opstart, stop, tab af hjælpespænding, RUN-shutdown og en enkeltfasefejl. Separat RUN-slukning af én fase kan ikke alene antages at være en sikker metode til fasefrakobling på fælles ITH.

Løsningen skal fastlægge faktiske spændinger, signalveje, strømbegrænsning/afbrydelse og tidsforløb ud fra producentdata. Der er ikke indsat en vilkårlig diode, seriemodstand eller analog switch som en påstået løsning. Når begrænsningen er løst, kan et forskningsdiagram konkretiseres og kontrolleres; producentstøtte, simulation og fysisk fase-/loop-/fejltest resterer stadig før frigivelse.

## Aktuelt beslutningsgrundlag

Fælles ITH er begrundet nok til beregning og forskningsarbejde. **Det er endnu ikke en dokumenteret strømfordelingsløsning til fire gange 10 A.** De vigtigste næste designinput er en sikker forsynings-/fasefejlarkitektur for de fælles pins, samlet kompensation med den faktiske power-stage/outputkapacitet, målbar faseubalance og native/ekstern CC-interaktion gennem buck-, buck-boost- og lavlastdrift.

Ingen firefaset hardware, simulation eller stabilitets-/4 kW-test er udført som del af denne undersøgelse. Ingen effektimplementering er ændret ud fra hypotesen.
