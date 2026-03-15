# Template: Seed / YC-style Business Plan

**Lingua:** Italiano (default) | Override: --lang en
**Lunghezza:** 15-20 pagine
**Tono:** Conciso, data-driven, narrativo

---

## Sezioni

### 1. Executive Summary (max 1 pagina)
Una pagina che cattura: problema, soluzione, mercato, trazione, team, ask.
**Dati da:** tutti i JSON

### 2. Problema & Opportunità
Descrivi il problema con evidenze concrete. Quantifica il dolore del cliente.
**Dati da:** businessPlanInput.businessModel.keyValueProposition, interview Block 1

### 3. Soluzione & Proposta di Valore
Come risolvete il problema. Differenziazione rispetto alle alternative.
**Dati da:** businessPlanInput.businessModel

### 4. Prodotto
Stato attuale, roadmap, screenshot/demo se disponibili.
**Dati da:** interview Block 3, traction.milestones

### 5. Mercato (TAM/SAM/SOM)
OBBLIGATORIO: stima bottom-up. Tabella TAM/SAM/SOM con metodologia.
**Dati da:** marketResearch.json, businessPlanInput.market

### 6. Business Model & Pricing
Modello di revenue, pricing, unit economics.
**Dati da:** businessPlanInput.businessModel.revenueLines, financials.unit_economics

### 7. Trazione & Metriche Chiave
KPI principali, grafico crescita, milestone raggiunte.
**Dati da:** businessPlanInput.traction, kpi-by-sector.md

### 8. Competizione
Matrice di posizionamento competitivo (tabella con almeno 3 competitor).
**Dati da:** marketResearch.competitors

### 9. Team & Advisory
Founder con background, team size, advisory board.
**Dati da:** businessPlanInput.team

### 10. Go-to-Market
Strategia di acquisizione, canali, partnership.
**Dati da:** interview Block 6

### 11. Proiezioni Finanziarie
P&L 3 anni (3 scenari), unit economics, funding ask.
**Tabelle da:** financials.scenarios.base.pl, financials.unit_economics, financials.breakeven

### 12. Startup Innovativa & Incentivi (se Italia)
Requisiti DL 179/2012 soddisfatti, benefici fiscali applicati.
**Dati da:** businessPlanInput.company.isInnovativeStartup, financials.incentives, italy-incentives.md
