# Små strømme, udgangsenergi og betydningen af 0 V / 0 A

Dette er en dimensioneringsundersøgelse til et ekstra udgangstrin. Kredsløbet er **ikke tegnet, routet eller integreret** i det eksisterende styrekort. Det aktuelle INA240/1 mΩ-kredsløb kan ikke dokumentere beskyttelse af en TL072-opstilling ved få milliampere.

## Hvorfor én 40 A-shunt ikke løser hele området

INA240's maksimale 25 µV inputoffset svarer med 1 mΩ til 25 mA. En 10 mA-belastning giver kun 10 µV over shunten. Desuden stopper det aktuelle styrekorts hardwarevindue ved en nominel strømkommando omkring 212 mA. En ny DAC-indstilling alene løser derfor ikke problemet.

En brugbar undersøgelsesretning er særskilte 20 mA-, 200 mA- og 40 A-områder. De små områder kræver større Kelvin-shunter og et aktivt strømbegrænsende element **efter** konverterens bulk-kondensatorer. Et reguleringssignal til ITH kan begrænse tilført energi, men kan ikke standse den energi, som allerede ligger på en kondensator direkte over DUT.

## Producentverificeret sensorkandidat

TI INA190A3 har gain 100 V/V, anbefalet common-mode −0,2 til 40 V og forsyning 1,7–5,5 V. Den kan bruges i belastningens retur på den flydende sekundærside. Den må ikke sættes direkte på en 100 V high-side. Databladet er `references/INA190.pdf`, SBOS863D, revideret november 2019, hentet fra TI.

Den konkrete ordrevariant INA190A3IDDFR står i databladets ordreappendiks og er en **kandidat**, ikke en monteret BOM-komponent. DDF har pin 1 VS, 2 ENABLE, 3 REF, 4 GND, 5 OUT, 6 NC, 7 IN+ og 8 IN−. NC kan efter databladet være åben eller forbindes inden for GND–VS. Kandidaten bruger REF = 0,2 V med plads til nulpunktfejl og margin over RVRR-testvinduets 0,1 V nedre grænse. Dette ændrer ikke det aktuelle INA240-styrekorts 0,1 V-reference.

| Undersøgt område | Ekstern shunt | Gain | Sensorudgang ved fuld skala | Shuntspænding | Shunttab |
|---|---:|---:|---:|---:|---:|
| 0–20 mA | 1 Ω | 100 | 2,2 V | 20 mV | 0,4 mW |
| 0–200 mA | 0,1 Ω | 100 | 2,2 V | 20 mV | 4 mW |

Shuntværdierne er dimensioneringskrav uden valgt fabrikant. De skal være fireterminaltyper med dokumenteret tolerance og temperaturkoefficient. Alle returveje, inklusive eksterne instrumenter, skal indgå i shuntmålingen.

INA190's ±15 µV offset gælder de angivne testbetingelser og må ikke ukritisk overføres til 5 V forsyning og lav common-mode. Scriptet lægger konservativt PSRR, ændret common-mode, REF-afvisning og 50 °C temperaturændring til. Resultatet er cirka **47,2 µV** samlet inputoffsetbudget før ekstern kalibrering og dynamiske forhold.

Med en antaget 0,1 % shunt, 25 ppm/°C, gain-tolerance/drift samt 1 mV samlet kommando-/referenceusikkerhed bliver det beregnede budget ved 1 mA cirka 0,063 mA på 1 Ω-området og cirka 0,580 mA på 0,1 Ω-området. Disse er konservative regnescenarier, ikke målt nøjagtighed eller godkendte strømgrænser. Kredsløbets comparator-, opamp-, filter-, støj- og transientegenskaber skal fortsat vurderes; scriptets 25 µV opampoffset er et særskilt 25 °C-scenarie, ikke en fuld temperatur- eller common-mode-specifikation.

Ved fejlagtig 40 A gennem de små shunter bliver tabet henholdsvis 1600 W og 160 W. Områderne kræver fysisk interlock, så udgangen er afbrudt og afladt før omskiftning; et softwareflag eller en uverificeret signalrelækontakt er utilstrækkeligt. Bypass, sikring og kontaktor skal vælges efter faktiske DC-ratings og fejlstrømme.

## Strømbegrænsning efter bulk-kondensatorerne

Den foreslåede rækkefølge er: reguleret konverter → bulk-kondensator → aktivt serieelement og fysisk afbrydelse → lille lokal DUT-kondensator → DUT. Returens Kelvin-shunt måler strømmen i hele DUT-vejen. Konverterens CV sættes lidt over DUT-spændingen, så det efterfølgende trin har reguleringsmargin; den tilladte margin skal dimensioneres.

Serieelementet skal have verificeret DC- og puls-SOA ved den aktuelle temperatur. De valgte BSC110N15NS5-switching-MOSFET'er er **ikke kvalificeret til denne lineære funktion**. Ved en kortslutning og 100 V over elementet er tabet 2 W ved 20 mA og 20 W ved 200 mA, før spændingsreguleringen når at reducere indgangen. SOA, energiforløb, reaktionstid, termik og kortsluttet pass-element skal dækkes af et selvstændigt design.

Der mangler en faktisk valgt pass-komponent, kompensation, uafhængig udgangs-OVP, range-interlock, afbrydelse og feedback fra den faktiske DUT-terminal. En fejl i en fælles setpunktkilde må ikke antages opdaget, blot fordi sensor og regulator bruger den samme fejlagtige kommando. Et fysisk valgt lavspændingsområde kan give en uafhængig maksimumgrænse til eksempelvis en opamp-opstilling, men det er endnu ikke implementeret.

## Lagret energi og udladning

| Kapacitans direkte ved DUT | Energi ved 5 V | Energi ved 100 V |
|---|---:|---:|
| 1 µF, eksempel | 12,5 µJ | 5 mJ |
| 96 µF, enkeltfasens nominelle bulk | 1,2 mJ | 0,48 J |
| 384 µF, fire gange bulk som eksempel | 4,8 mJ | 1,92 J |

Tabellen viser `E = C × V² / 2`. En lille kondensator er ikke automatisk ufarlig for enhver DUT. DC-bias, tolerance, kabling og DUT's egen kapacitans skal med i det endelige budget. Seriebegrænseren hjælper kun på upstream-energi; energi efter den kan stadig løbe direkte ind i DUT.

En 10 kΩ udladningsmodstand over en afbrudt udgang giver ideelt `V(t) = V0 × exp(−t/RC)`. Fra 100 V til 0,1 V tager det cirka 69 ms med 1 µF og 6,63 s med 96 µF. Initialt tab er 1 W; en fysisk modstand eller aktiveret udladningsgren skal have passende spændings-, effekt- og pulsrating. Tallene er scenarier uden monteret udladningskredsløb.

## Hvad 0 V og 0 A kan betyde

LTC3779 dokumenterer positiv regulering fra cirka 1,2 V; det aktuelle CV-forsøg dokumenterer ikke aktiv 0 V-regulering. Ved 0 V-kommando skal en praktisk løsning afbryde energitilførslen og aflade DUT-terminalen til en defineret restspænding inden for en defineret tid. Et instrument, som viser 0,00 V, er ikke et bevis for matematisk præcis nul eller for galvanisk afbrydelse.

0 A skal være en **slukkommando med afbrudt udgang**, ikke et løfte om en stabil CC-sløjfe ved præcis nul. Kontaktlækstrøm, sensornulpunkt, bleederstrøm og spænding fra en ekstern DUT skal beskrives. En belastning, som selv driver udgangen, kræver reverse-blocking og eventuelt en dimensioneret sink-funktion.

En aktiv forsyning, som holder 0 V mod en ekstern energikilde, skal kunne absorbere strøm. Den aktuelle ensrettede 4 kW-forsyning og de valgte AC/DC-moduler er ikke dokumenteret som energisink. Kravet om 40 A til rådighed tæt på 0 V adskilles derfor fra kravet om at absorbere 40 A: det sidste er ikke et eksisterende brugerkrav og er ikke implementeret.

## Genkør beregningerne

```sh
/usr/bin/python3 scripts/low_current_calcs.py
```

Resultater og alle numeriske antagelser gemmes i `exports/analysis/low_current.json`. Der er ingen hardwaretest eller implementeret lavstrømsbeskyttelse i dette appendiks.
