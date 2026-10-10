# SWM-PORWER-SUP – laboratorieforsyning 100 V / 40 A

**Status: uafsluttet konstruktionsudkast. Den komplette 4 kW strømforsyning er ikke leveret eller frigivet til fremstilling.**

## Download

Afleveringsfilerne findes i [GitHub-prerelease v0.1-design-draft](https://github.com/kristian61/SWM-PORWER-SUP/releases/tag/v0.1-design-draft):

- [Dansk PDF-manual, 134 sider](https://github.com/kristian61/SWM-PORWER-SUP/releases/download/v0.1-design-draft/SWM-POWER-SUP-manual-dansk.pdf)
- [Komplet projekt-ZIP med fabrikantdatablade, cirka 61 MB](https://github.com/kristian61/SWM-PORWER-SUP/releases/download/v0.1-design-draft/SWM-POWER-SUP-komplet-projekt.zip)
- [Mindre projekt-ZIP uden fabrikantdatablade, cirka 15 MB](https://github.com/kristian61/SWM-PORWER-SUP/releases/download/v0.1-design-draft/SWM-POWER-SUP-projekt-uden-datablade.zip)

PDF, ZIP og kontrolrapporter er den kontrollerede CAD-aflevering fra 10. oktober 2026, før GitHub-upload. Deres bemærkninger om endnu ikke udført GitHub-publicering beskriver dette tidligere tidspunkt. Kildefilerne på main indeholder samme CAD og beregningsarbejde samt disse downloadhenvisninger. Prerelease betyder ingen frigivelse til fremstilling eller net-/effekttest. Nogle scripts i den mindre ZIP kræver originalerne fra den komplette pakke.

Krav: 230 V AC på en dedikeret 32 A kreds, isoleret og flydende 0–100 V udgang, op til 40 A og justerbar strømbegrænsning til små prøveprint.

## Konkrete delprojekter

| Delprojekt | Leveret | Kontrolstatus |
|---|---|---|
| Passivt måle-/testkort | Native KiCad-diagram og fuldt routet 110 × 90 mm, 2-lags PCB, 11 testpunkter | ERC/DRC uden fejl, ingen åbne forbindelser, alle 52 pin/pad-forbindelser sammenholdt; HV-reglernes aktivering afprøvet |
| LTC3779-effektfase | To-siders diagram, lokal controller-symbol/footprint, BOM, 19 testpunkter og fuldt routet 135 × 90 mm PCB i fire lag | ERC/DRC/paritet uden fejl, ingen åbne forbindelser; 175 logiske pins og alle 191 fysiske pads kontrolleret |
| Isoleret netdel | Native chassisdiagram for 2 × RSP-3000-48 ved 55 V hver, separate enable-kredse, lokale senseledninger og diodekrav | Officielle producentdata og terminalforbindelser kontrolleret, ERC bestået; ingen net-PCB eller kvalificeret systemintegration |
| Analogt CV/CC-styrekort | Separat forsøgsdiagram, fuldt routet 180 × 150 mm PCB, komponentliste og 16 testpunkter til én effektfase | ERC/DRC/paritet bestået, alle 211 forbindelser stemmer; regulering og fejlrespons utestet, omfatter ikke 0 V, milliamperebeskyttelse eller 40 A |

Effektfaseudkastet har fast 99,6 V, 10 A som uverificeret udviklingsmål og en intern fast strømgrænse omkring 12,5 A. Det er ikke en 0–100 V / 40 A laboratorieforsyning og har ingen justerbar laboratorie-CC. Der er endnu ingen hardwaretest af nogen af kortene.

Det separate styrekort undersøger en positiv VFB-injektion til CV og en ITH-clamp til CC. Det er ikke integreret i den oprindelige faste effektfase. Nominelle kommandoer dækker cirka 1,2–100 V og 0–10 A, men de aktuelle hardwarevinduer slukker ved strømkommandoer under cirka 0,21 A. Det kan derfor ikke bruges som dokumenteret beskyttelse af et lille opamp-print.

## Filer

- `design/measurement/measurement.kicad_pro`: målekortets native KiCad-projekt.
- `design/power/power_phase.kicad_pro`: det uafsluttede enkeltfase-projekt.
- `design/frontend/frontend.kicad_pro`: netmodulernes chassisforbindelser; `exports/frontend/frontend.pdf` er det to-siders PDF-diagram.
- `design/control/control.kicad_pro`: separat eksperimentelt analogt styrekort med routet PCB.
- `bom/measurement.csv` og `bom/power-phase.csv`: alle komponentreferencer, værdier, mængder, footprints, funktioner og indkøbs-/reviewstatus for hvert kort. Referencer som R1 og J1 starter forfra på hvert delprojekt.
- `bom/current-draft.csv`: samlet komponentoversigt med eksplicit kortnavn; den er ikke en komplet 4 kW-stykliste.
- `bom/critical-components.csv` og `docs/component-qualification.md`: 85 kritiske komponentposter med fabrikantdata, pinout, betingelser og åbne valg.
- `design/control/studies/`, `bom/phase-balancing-study.csv` og `docs/phase-balancing.md`: nyt énkanals fasestrømstudie og model af fire uafhængige strømservoer; ikke integreret i de routede kort.
- `docs/bus-disconnect-design.md`: betinget dimensionering af fysisk busafbrydelse; komponent- og transientkvalifikation mangler.
- `docs/final-status.md`: afsluttende status opdelt i CAD, kontroller, beregninger, simulering og fysisk validering.
- `bom/frontend.csv`: netmoduler og alle viste chassisdele; manglende varenumre/rating står som krav, ikke indkøbsfrigivne komponenter.
- `bom/control.csv` og `docs/control.md`: styrekortets komponenter, funktion, stik, testpunkter og aktuelle begrænsninger.
- `docs/control-layout.md`, `docs/power-analysis.md`, `docs/bus-protection.md` og `docs/low-current-output.md`: layout, tab/ripple/loop-modeller, busfejl og mA-/0 V-undersøgelse.
- `docs/low-current-loop.md`: separat antaget post-bulk-strømservo og varm-SOA-begrænsning; ingen frigivet lavstrøms-PCB.
- `docs/power-layout.md` og `exports/power/remaining_connections.json`: effektkortets strømbaner, kobberbudget, regler og konkrete routingrester.
- `docs/manual.md` og `docs/power-phase.md`: funktion, stik, testpunkter og fejlfinding.
- `docs/krav.md`, `docs/architecture-research.md`, `docs/frontend-selection.md` og `docs/protection-and-test-plan.md`: krav, effektbudget, isolation/netdel og fysisk valideringsplan.
- `exports/manual_da.pdf`: samlet dansk projektmanual.
- `exports/measurement/` og `exports/power/`: PDF-diagrammer og PCB-visninger.
- `exports/verification/`: kontroller og samlet status. Ingen Gerber-frigivelse.
- `exports/verification/project_status.json`: samlet CAD-status, beregningsrapporter, kildehashes og manglende hardwarevalidering.
- `references/`: hentede officielle producentdatablade og referencekredsløb.

## KiCad i cloudmiljøet

KiCad 9.0.2 er allerede installeret. Brug wrapperen, fordi hjemmemappen er skrivebeskyttet:

```sh
cd /workspace/SWM-PORWER-SUP
bin/kicad-env kicad-cli version
bin/kicad-env /usr/bin/python3 scripts/validate_kicad.py
bin/kicad-env /usr/bin/python3 scripts/check_inventory.py
bin/kicad-env /usr/bin/python3 scripts/validate_control_layout.py
```

Python PCB-API'en findes i `/usr/bin/python3`, ikke standard-Python. Brug den eksisterende checkout; cloudopgaven er allerede isoleret, så opret ikke en Git worktree som opstartstrin.

Kun ved bevidst regeneration af genererede filer:

```sh
bin/kicad-env /usr/bin/python3 scripts/measurement_gen.py
bin/kicad-env /usr/bin/python3 scripts/power_phase_gen.py
bin/kicad-env /usr/bin/python3 scripts/frontend_gen.py
bin/kicad-env /usr/bin/python3 scripts/control_gen.py
bin/kicad-env /usr/bin/python3 scripts/control_route.py
/usr/bin/python3 scripts/package_draft.py --metadata-only
/usr/bin/python3 scripts/project_status.py
/usr/bin/python3 scripts/render_manual.py
/usr/bin/python3 scripts/package_draft.py
```

Beregningsmodeller kan køres særskilt med `/usr/bin/python3`: design_calcs.py, power_analysis.py, control_limits.py, low_current_calcs.py, low_current_loop.py, phase_balance_analysis.py, bus_protection_calcs.py og bus_disconnect_envelope.py. Kør design_calcs.py efter bus_disconnect_envelope.py for det konsistente tillægsbudget. De aktuelle resultater og modelantagelser ligger i exports/analysis/.

Generatorerne overskriver deres genererede KiCad-filer. Bevar brugerændringer først. Efter control_gen.py skal control_route.py genoprette routingen. Den afsluttende validate_control_layout.py opdaterer aktuel status; summary_pre_route.json viser generatorstadiet. power_phase_gen.py genafspiller den gemte slutrouting fra power_routing_plan.json; en isoleret regeneration er kontrolleret.

## Hvad der blokerer den komplette konstruktion

Front-endens arbejdsvalg er nu dokumenteret: 2 × RSP-3000-48 ved 55 V giver nominelt 110 V. Der mangler modelkvalifikation af seriedrift/flydende offset, endelige chassis-/effektkomponenter, busbeskyttelse, færdig og integreret CV/CC samt 0 V-regulering, lavstrømsbeskyttelse, firefaset systemintegration og fysisk validering. Modulernes OVP kan tillade samlet 134,4 V threshold og ukendt oversving; det overholder ikke automatisk effektfasens 120 V-proceduregrænse. Færdig CAD-routing ændrer ikke disse funktionelle og sikkerhedsmæssige blokeringer.

Analog Devices, TI, `meanwell.com` og aktuelle Infineon-produkt-/assetadresser kan nås, og de læste originaler er gemt i `references/`. `www.diodes.com` gav fortsat HTTP 403 ved de seneste normale forsøg. Netværksdomæner og genbrugelige KiCad-opstartsinstruktioner er gemt i miljøkladden. Gennemgå og gem ændringerne i miljøindstillingerne for genbrug; en kladdesave publicerer ikke miljøet. Publicering og afprøvning i en ny task er ikke udført.
