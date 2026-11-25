---
title: Energy-Efficient Power Design for Buildings & Homes
subtitle: Cut the load first, then power what's left with solar, storage and smart controls
author: deckgen example deck
theme: evergreen
style: business
---

## Buildings are one of the biggest levers for cutting energy use
- Buildings use roughly 30% of global final energy
- Most of a home's energy goes to heating, cooling and hot water
- Design choices lock in energy use for 50+ years
- Efficiency plus on-site solar can bring homes close to net zero
Source: IEA, Buildings tracking report (2023)
Notes: Frame the opportunity. Buildings last for decades, so decisions made at design time set energy use and costs for a very long time.

## Heating and hot water drive most home energy use
```chart
type: pie
categories: [Space heating, Water heating, Air conditioning, "Appliances, lighting & other"]
series:
  - name: Share of US household energy (approx.)
    values: [42, 19, 9, 30]
highlight: 0
annotation: Space heating alone is ~40% of home energy use
```
- Fix heating demand first: insulation and airtightness
- Hot water is next: heat pump water heaters
Source: U.S. EIA, Residential Energy Consumption Survey 2020 (rounded)
Notes: This split is why envelope and heating systems come before solar panels in the design order.

## Design in order: reduce, make efficient, then generate
### 1. Reduce the load
- Orientation, shading, daylight
- Insulation, airtight envelope, high-performance windows
### 2. Serve it efficiently, then generate
- Heat pumps, heat-recovery ventilation, LED lighting
- Rooftop solar PV, battery storage, smart controls
Notes: The energy hierarchy. Every kWh you avoid is one you don't have to generate, store or pay for.

## A good envelope can cut heating demand by up to 90%
```chart
type: bar
categories: [Older uninsulated home, Typical code-built home, High-performance home, Passive House]
series:
  - name: Heating demand, kWh/m² per year (illustrative)
    values: [200, 80, 40, 15]
highlight: 3
annotation: Passive House caps heating demand at 15 kWh/m²·yr
```
- Continuous insulation, no thermal bridges
- Airtightness tested with a blower door
- Triple-glazed or low-e windows
Source: Passive House Institute criteria; other values are typical illustrative ranges
Notes: Values other than the Passive House limit are illustrative, to show the order of magnitude between building standards.

## Efficient systems do more with less energy
```metrics
- value: "300–400%"
  label: Heat pump efficiency (COP 3–4) vs ~95% for a gas furnace
- value: "~75%"
  label: Less electricity for LED vs incandescent lighting
- value: "20–23%"
  label: Typical efficiency of mainstream solar panels
- value: "70–90%"
  label: Heat recovered by an HRV/ERV ventilation unit
```
Source: U.S. DOE Energy Saver; manufacturer datasheets (typical ranges)
Notes: Heat pumps move heat instead of making it, which is why they deliver three to four units of heat per unit of electricity.

## Efficiency first shrinks the solar array by 40%
```chart
type: column
categories: [Before upgrades, After upgrades]
series:
  - name: PV size needed for net zero (kWp)
    values: [7.1, 4.3]
highlight: 1
annotation: 4.3 kWp ≈ 11 × 400 W panels ≈ 21 m² of roof
```
- Load drops from 10,000 to 6,000 kWh/yr
- Assumes a yield of 1,400 kWh per kWp per year
- Smaller array: lower cost, fits more roofs
Notes: Worked example. PV size equals annual load divided by specific yield. Check local yield with PVWatts or PVGIS.

## Solar sizing worked example
| Step | Value |
|---|---|
| Annual electricity use after upgrades | 6,000 kWh |
| Specific yield (location dependent) | 1,400 kWh/kWp |
| Required PV capacity | 4.3 kWp |
| Panel rating | 400 W |
| Number of panels | 11 |
| Roof area (≈1.9 m² per panel) | ≈21 m² |
| Inverter size (≈0.9–1.0 × array) | 4.0 kW |
Notes: Walk through the arithmetic. Adjust the yield for the site: roughly 1,000 in northern Europe to 1,800+ in sunny regions.

## Solar peaks at noon but homes peak at night, so storage bridges the gap
```chart
type: line
categories: ["6:00", "9:00", "12:00", "15:00", "18:00", "21:00"]
series:
  - name: Solar generation (kW)
    values: [0.3, 2.5, 4.0, 3.0, 0.8, 0.0]
  - name: Home demand (kW)
    values: [0.8, 0.6, 0.5, 0.7, 2.2, 1.8]
annotation: Illustrative summer day for a 4.3 kWp home
```
- Battery stores midday surplus for evening use
- Smart controls shift EV charging and hot water to solar hours
Notes: Self-consumption is the key economic lever where export tariffs are low.

## Power system design: components that work together
### Generation & conversion
- PV array with string or micro-inverters
- Rapid shutdown and DC isolation per code
- Grid-tie with net metering or export tariff
### Storage & control
- Lithium iron phosphate (LFP) battery, 5–13 kWh typical
- Smart panel / energy management system
- EV charger and heat pump on managed circuits
Notes: Always design to the local electrical code, for example NEC Articles 690 and 705 in the US, and use a licensed installer.

## Homes vs commercial buildings: same principles, different priorities
### Homes
- Heating, cooling and hot water dominate
- Rooftop PV can cover most annual use
- Simple controls, big comfort gains
### Commercial buildings
- Lighting, cooling, plug loads and ventilation dominate
- Building automation and metering are critical
- Roof area often limits PV; add façades and carports
Notes: The hierarchy is the same, but commercial buildings get more value from controls and demand management.

## A phased roadmap turns any building into a low-energy building
1. Audit: energy bills, blower-door test, thermal imaging
2. Envelope: air sealing, insulation, windows
3. Systems: heat pump, heat pump water heater, HRV, LEDs
4. Generate: right-sized rooftop solar PV
5. Store & manage: battery, smart controls, EV charging
6. Monitor: track kWh and tune settings every season
Notes: Phase the work so each step makes the next one smaller and cheaper.

## Reduce first, then generate: the path to a net-zero-ready building {conclusion}
- Efficiency is the cheapest kWh: fix the envelope and systems first
- Heat pumps and LEDs cut energy use 3–4× for heating and lighting
- A right-sized solar + battery system covers the remaining load
- Smart controls match demand to solar output and cut bills further
Notes: Leave this slide up during Q&A.
