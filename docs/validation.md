# Kontrolstatus og åbne konstruktionspunkter

Kontrollerne bruger KiCad 9.0.2. Ingen fysisk prototype er bygget eller spændingssat; elektrisk funktion, dynamik, temperatur og isolation er ikke målt. Rapporterne i `exports/` viser CAD- og konsistenskontrol, ikke bestået 4 kW-drift.

| Del | Kontrolresultat | Praktisk grænse |
|---|---|---|
| Passivt måleprint | 29 komponenter, 52 pin/pad-forbindelser, 15 net; ERC og DRC med alle alvorligheder bestået, ingen åbne forbindelser eller paritetsfejl | Ingen regulator, aktiv strømbegrænsning, ADC, clamps eller isolation på selve kortet; komponentindkøb og fysisk test mangler |
| Måleprintets HV-regler | Umulig midlertidig 100 mm-regel detekterede 499 HV-clearancefejl i en scratchkopi; originalen blev ikke ændret | Viser, at reglerne aktiveres; er ikke en isolationstest eller en fuld vurdering af anvendelsesmiljø |
| Analogt styrekort | 86 komponenter, 211 terminaler, 41 net; ERC/DRC/paritet uden fejl, ingen åbne forbindelser. 2362 sporsegmenter og 154 vias | Eksperimentel enkeltfase-CV/CC; loop-stabilitet, rail-off, fysisk start og DUT-beskyttelse er utestede |
| Styrekortets HV-regler | Negativ 100 mm-kontrol gav 499 clearancefejl; originale filhashes var uændrede | Geometrisk kontrol, ingen fysisk isolationstest |
| LTC3779-effektfase | 75 komponenter, 175 logiske pins og 191 fysiske pads, 38 net; ERC/DRC/paritet bestået. 135 × 90 mm, fire lag, 1551 sporsegmenter og 111 vias | Nul åbne forbindelser og nul geometriske overtrædelser; ingen fremstillingsfrigivelse, switching-/sense-/termisk kvalifikation mangler |
| Effektkortets HV-regler og reproduktion | Negativ 5 mm-regel gav499 clearancefund/exit5 i kopi; originale hashes uændrede. Isoleret regeneration giver ERC/DRC PASS og identisk routingplan | Viser aktive regler og reproducerbar geometri; ingen isolationstest |
| Netmodulernes chassisdiagram | 14 referencer, 63 tilsluttede terminaler og 4 bevidste no-connects; ERC og terminalkortlægning kontrolleret | Passive terminalsymboler repræsenterer købte moduler, ingen net-PCB. Beskyttelsesdele, bus-OVP og kvalifikation mangler |

Effektkortets oprindelige 22 clearancefejl er håndteret med afgrænsede komponent-/netparregler ved controllerens native finepitch-geometri. De konkrete lavspændingspar og højere spændingspar er beskrevet i power-layout.md; den almindelige HV-separation bevares uden for pakkerne. Reglerne er funktionelle layoutvalg, ingen isolationskvalifikation. Åbne forbindelser er med i DRC og er ikke skjult.

`scripts/check_inventory.py` sammenholder uafhængigt reference, værdi og footprint mellem XML-netliste, BOM og PCB samt hver logisk pin/pad-netforbindelse. **Alle fysiske nummererede pads kontrolleres før ens pinnumre samles**, så flere MOSFET-drainpads ikke kan skjule et forkert net. Den samlede rapport ligger i `exports/verification/inventory.json`. DRC dokumenterer desuden faktisk CAD-konnektivitet; det er fortsat ikke fysisk funktionstest.

## Genkør relevante kontroller

```sh
cd /workspace/SWM-PORWER-SUP
bin/kicad-env /usr/bin/python3 scripts/validate_kicad.py
bin/kicad-env /usr/bin/python3 scripts/validate_control_layout.py
bin/kicad-env /usr/bin/python3 scripts/check_inventory.py
```

Den første kommando gælder kun måleprintet; den anden gælder det routede styrekort. `exports/control/summary.json` og `layout_validation.json` viser aktuel status, mens `summary_pre_route.json` er historik fra generatorens placeringsstadium. Effektkortets aktuelle beståede DRC står i `exports/power/drc.json`. Generatorer erstatter de genererede kilder og må kun køres, når brugerændringer først er bevaret. Effektgeneratoren inkluderer slutroutingens replay; præcis reproduktion og hash er dokumenteret særskilt.

Fasestrømstudiet er et separat native koncept uden PCB, ikke en femte frigivet hardwareenhed. Dets egen ERC/netlistekontrol og tydelige mangler beskrives i phase-balancing.md. Hovedlisten bevarer206 poster; studieskemaets47 poster og komponentmatrixens85 poster er supplerende lister, ikke ekstra monterede hovedkortdele.

## Det næste arbejde til den komplette forsyning

1. Implementér uafhængig busbeskyttelse og afbrydelse, så den dokumenterede front-end ikke overskrider regulatorens ratings eller proceduregrænser. 134,4 V er et OVP-thresholdbudget, ikke en transientclamp.
2. Afslut programmerbar CV/CC, lavstrømsmåling og begrænsning efter bulk-kondensatorerne samt 0 V-enden. De aktuelle forsøgsdele dokumenterer ikke beskyttelse af et lille opamp-print.
3. Integrér og kvalificér de foreslåede fire uafhængige fasestrømservoer. Native AMC3302/PI/NMOS-studie og antaget firefasemodel er leveret; fault-latch, anti-windup, RUN-guard, plant og fysisk fasefejl er endnu ikke verificeret.
4. Vælg spole, bulk-kondensatorer, shunter, diode, terminaler, afbryder, sikringer, hjælpeforsyninger og køling med faktiske varenumre/rating. De eksplicitte krav i BOM må ikke behandles som godkendte købskomponenter.
5. Review kortenes gate/source-sløjfer, Kelvin-sense, termik og analogsignalers føring. Fysisk prototype må først afprøves efter komponent-, busbeskyttelses- og funktionsreview; CAD-pass ophæver ikke disse åbne punkter.

GitHub-publicering, miljøpublicering og afprøvning fra en ny cloudtask er ikke udført. Alle leverede filer er aktuelle arbejdsfiler i projektmappen og den samlede ZIP.
