# Kravgrundlag – laboratorieforsyning 100 V / 40 A

## Bekræftet af brugeren

- Indgang: 230 V AC, dedikeret 32 A kreds.
- Udgang: 0–100 V, op til 40 A gennem spændingsområdet.
- Justerbar strømbegrænsning, så små prøveprint kan forsynes i CC/CV.
- Galvanisk isoleret og flydende udgang.
- KiCad-diagram og PCB, komponentliste med værdier og dansk funktions-/fejlfindingsmanual med testpunkter.

Det dimensionerende punkt er samtidig 100 V og 40 A = 4.000 W. Der dimensioneres foreløbigt til kontinuerlig drift; dette er ikke en målt kapabilitet.

## Arbejdsvalg og åbne konstruktionsbeslutninger

- Nettopologi: 2 × MEAN WELL RSP-3000-48, hver trimmet til 55 V, er nu det dokumenterede arbejdsvalg. Den nominelle bus er 110 V; serieintegration, flydende offset og busbeskyttelse er endnu ikke kvalificeret.
- Beregningsreference for DC-regulator: 120 V bus som dimensioneringspunkt, fire interleavede faser, 10 A per fase, 100 kHz, 150 µH. Det konkrete enkeltfaseudkast bruger LTC3779; firefasestyring og strømfordeling er endnu ikke realiseret.
- 0 V og 0 A skal undersøges praktisk. Slukket/afladt udgang adskilles fra aktiv 0 V-regulering og fra strømabsorption; det aktuelle kredsløb dokumenterer kun positiv regulering fra omkring 1,2 V.
- Lavstrømsundersøgelsen omfatter særskilte 20 mA- og 200 mA-områder med større shunter samt et 40 A-område. Dette er dimensioneringsforslag, ikke implementerede eller ekstra brugerbekræftede specifikationer.
- Nøjagtighed, ripple, lasttransienter, mekanik og kølingsstøj er ikke specificeret. Foreløbige testmål mærkes særskilt.
- Batteriopladning, tilbageført energi og aktivt strømsink er ikke bekræftede funktioner og er ikke tilladt i den første prototype.
- Der skal fastlægges en konkret udgang-til-PE arbejds- og transientspænding; 'flydende' betyder ikke ubegrænset isolation mod jord.

## Effektbudget

P_out = 100 V × 40 A = 4.000 W.
Ved 95 % effektivitet i DC-regulatoren bliver dens input 4.211 W og dens tab 211 W.
Det oprindelige regneeksempel med 95 % AC/DC og PF = 0,98 gav 4.432 W, 432 W varme og 19,7 A. For det aktuelle Mean Well-valg giver databladets 91,5 % typiske effektivitet og PF = 0,95 i stedet cirka 4.602 W, 602 W samlet varme og 21,06 A ved 230 V. Dette er et budget med typiske data, ikke en målt eller garanteret performance ved modulers faktiske belastning.
Den valgte 32 A kreds giver effektmargin; startstrøm, netfilter, stik, kabler, kredsbeskyttelse og front-end-derating skal stadig dimensioneres særskilt.

## Aktuel leverance og frigivelsesstatus

Det passive måle-/testkort er CAD-kontrolleret. Måleprintet kan måle via 40:1 delere og Kelvin-filter; det regulerer ikke spænding eller strøm, har ingen egen galvanisk isolation og fører ikke 40 A. Det placeres på den isolerede sekundærside.
Det separate LTC3779-effektfaseudkast har fast 99,6 V nominelt og 10 A som udviklingsmål. Det er fuldt routet i fire lag med bestået ERC/DRC og nul åbne forbindelser; det opfylder ikke 40 A eller justerbar laboratorie-CV/CC. Det separate analoge styrekort er CAD-routet og kontrolleret, men regulering og fysisk integration er utestet. Netmodulernes chassisdiagram er tegnet i `design/frontend/`, men busbeskyttelse og integration er uafsluttet.
Datablade fra Analog Devices, TI, Mean Well og Infineon er hentet og gemt. DFLS1200-fabrikantdata, endelige magnetiske/passive effektdele, programmerbar styring og systembeskyttelser mangler fortsat helt eller delvist; se de enkelte delprojekters aktuelle status.
Ingen hardware er fremstillet eller testet ved 4 kW.
