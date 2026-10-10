# Ændringer og tekniske beslutninger

Revision: 10. oktober 2026. Arbejdet fortsætter i den eksisterende projektmappe. Det fungerende målekorts kredsløb og routing er bevaret.

| Ændring | Begrundelse og evidens | Status |
|---|---|---|
| Styrekortets off-grid placeringer rettet | KiCad ERC pegede på konkrete lednings- og pinender; flyttet til elektrisk grid | Aktuel ERC uden advarsler eller fejl |
| LM4040 pin 3 til PGND | TI tillader forbindelse til anoden; lokalt symbol viser faktisk tilladt pinfunktion | XML og PCB stemmer, ingen NC-paritetsfejl |
| INJ-low erstattet af IMON-low | Den absolutte 1,1 V INJ-grænse låste start fra afladt udgang ved høj spændingskommando | Statiske KCL-startpunkter passerer; tidsforløb er ikke testet |
| R13 beholdt på 2,49 kΩ | En indledende summeringsfejl gav 796 µA referencebelastning. KCL fra aktuelle BOM-/XML-grene og uafhængig genkontrol giver 694,21 µA | Kortvarig ændring til 2,00 kΩ er tilbageført; konservativt static-scenarie har 39,3 µA reserve over 65 µA |
| Styrekortet routet | Funktionel placering, direkte Kelvin, lokal afkobling og eksplicit HV-dividerområde | 211 terminaler, ERC/DRC/paritet bestået; hardwarefunktion ikke målt |
| Effektfasens layout afsluttet | Hovedstrøm, gate, bootstrap og Kelvin-ruter er forbundet; C14 er på bagsiden | 1551 segmenter / 111 vias, ERC/DRC/paritet bestået, nul åbne forbindelser; ingen fysisk kvalifikation |
| U1-landpattern korrigeret | LTC3779 Rev. A s.36 anbefaler 1,05±0,10 × 0,315±0,05 mm og 6,60±0,10 mm yderbredde | Aktuelle pads 1,05 × 0,300 mm, centre ±2,775 mm; ingen regellempelse eller ændring af pinpitch |
| Effektlayout kan genskabes | Generatoren genafspiller slutgeometrien fra power_routing_plan.json efter kontrol af fysiske pad/net-par | Isoleret regeneration giver ERC/DRC PASS og identisk routing-plan SHA-256 |
| INA240REF-navne og IC-metadata rettet | TI SOIC-8 bruger REF2 på pin3 og REF1 på pin7; begge er allerede forbundet til IREF. OPA4192/TLV1704 fik egne databladslinks | Ingen elektriske netændringer; styrekortet genkontrolleret med alle211 forbindelser og ERC/DRC PASS |
| Fire faser behandlet som hypotese | Fælles ITH har uløste V5-/fasefejl-grænser og dokumenterer ikke middelstrømsdeling | Sensitivitetsmodeller viser ubalance; ingen færdig 40 A-fasekonstruktion |
| Fire uafhængige strømservoer udviklet som studie | AMC3302 isoleret måling af hver2 mΩ-gren, separat PI og NMOS-sink til lokal ITH | Native énkanalsstudie og firefasemodel; anti-windup, fault-latch, fysisk integration og plantidentifikation mangler |
| CC-kompensation ikke frigivet | Antagne plant-modeller giver lav eller negativ margin med 1 nF; den faktiske strømsløjfe mangler identifikation | Ingen påstået valideret komponentændring eller hardwarestabilitet |
| INA190 lavstrømskandidat bruger 0,2 V reference | 0,1 V ligger på RVRR-testvinduets nedre kant; 0,2 V giver margin ved referenceusikkerhed | Undersøgelse uden native kredsløb; det eksisterende INA240-korts 0,1 V er bevaret |
| Lavstrøms-loop undersøgt særskilt | 24 antagne gm/gatepol-tilfælde giver mindst55,69° margin og op til294 ms indsvingning | Ingen kompensationsfrigivelse; hurtig fejlbeskyttelse og post-bulk pass-kredsløb mangler |
| Busbeskyttelse ikke erklæret løst | Step-/delaymodel, clamp-tolerance og fabrikant-SOA viser konkrete manglende marginer | RSP-seriebus må ikke kobles til prototypefasen før kvalifikation |
| Komponentkrav holdt særskilt fra verificerede varenumre | Spole, flere passive effektdele, terminaler og beskyttelsesdele er endnu ikke valgt | BOM-status angiver uafklarede valg, ingen komplet indkøbsfrigivelse |
| 85 kritiske komponentposter gennemgået | Originale fabrikantdata, betingelser, pinmaps, drifts-/absmax-grænser og kildehashes | Separat kvalifikationsmatrix;206-posthovedlisten bevares, åbne passive valg er markeret |

Aktuelle tal ligger i JSON-rapporterne. Negative HV-kontroller ændrer kun midlertidige kopier og kontrollerer originale filhashes. De viser aktive CAD-regler, ikke isolation, temperatursikkerhed eller fejltolerant drift.

Ingen hardwaretest, 4 kW-prøve, GitHub-publicering eller fabrikationsfrigivelse er foretaget. Miljøindstillingerne er en gemt kladde; publicering og verifikation fra en ny cloudtask er separate trin.
