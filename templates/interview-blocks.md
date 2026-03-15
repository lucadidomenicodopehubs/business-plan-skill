# Interview Blocks — Business Plan Generator

Conduci un'intervista strutturata per raccogliere i dati necessari. Procedi un blocco alla volta, riepiloga dopo ogni blocco e chiedi conferma.

---

## Block 1: Idea / Problema & Soluzione
**Maps to:** `company`, `businessModel.keyValueProposition`

### Domande
1. Quale problema concreto risolvete e per chi?
2. Come lo risolvete? Qual è la vostra proposta di valore unica?
3. Quali alternative o competitor usano oggi i vostri clienti?

### Branching
- Nessuno (sempre richiesto)

---

## Block 2: Mercato
**Maps to:** `market.*`

### Domande
1. Chi sono i segmenti di clientela target? In quali paesi/regioni?
2. Qual è la dimensione stimata del mercato (TAM/SAM/SOM) e la sua crescita?
3. Ci sono regolamentazioni di settore rilevanti (medicale, fintech, space, AI Act UE)?

### Branching
- IF sector == "SaaS_B2B" → chiedi specificamente su NRR, churn atteso, espansione revenue
- IF sector == "Manufacturing" → chiedi su regolamentazioni prodotto, certificazioni necessarie

---

## Block 3: Prodotto / Tecnologia
**Maps to:** `businessModel.sector`, `company.isInnovativeStartup`

### Domande
1. Qual è lo stato del prodotto (idea, prototipo, beta, produzione)?
2. Quali tecnologie core utilizzate (AI, IoT, space tech, biotech, manifattura 4.0)?
3. Ci sono IP protette (brevetti, software registrato) o candidabili a Patent Box?

### Branching
- IF target == "smartstart" → approfondisci: "Le spese in R&S superano il 15% del fatturato? Quante persone nel team hanno un dottorato?"
- IF target == "esa-bic" → chiedi: "Qual è la connessione con tecnologie/dati spaziali (osservazione Terra, navigazione, telecomunicazioni)?"

---

## Block 4: Team & Governance
**Maps to:** `team.*`

### Domande
1. Chi sono i founder e il core team, con quali esperienze rilevanti?
2. Come sono ripartite le quote e i ruoli decisionali?
3. Avete advisory board, partner chiave, università coinvolte?

### Branching
- IF target == "horizon" → chiedi struttura del consorzio: "Quanti partner? Università e PMI? Ruolo di ciascuno?"

---

## Block 5: Trazione & KPI
**Maps to:** `traction.*`

### Domande
1. Clienti paganti? Piloti? PoC? Revenue (ARR/MRR)?
2. Metriche chiave per il vostro settore?
3. Principali milestone raggiunte (lanci, certificazioni, grant ottenuti)?

### Branching
- IF sector == "SaaS_B2B" → approfondisci: MRR, MRR growth, churn rate, LTV/CAC, pipeline
- IF sector == "Manufacturing" → insisti su: OEE, capacità produttiva, tasso di scarto, certificazioni ISO/AS

---

## Block 6: Go-to-Market & Operatività
**Maps to:** `businessModel.revenueModel`, `businessModel.revenueLines`

### Domande
1. Canali di acquisizione clienti (direct sales, partner, online, marketplace)?
2. Modello di pricing e revenue (subscription, usage-based, licenze, fee)?
3. Struttura operativa: produzione interna/esterna, supply chain?

### Branching
- IF sector == "Marketplace" → chiedi take rate, GMV, strategia chicken-and-egg

---

## Block 7: Finanza & Funding
**Maps to:** `planProfile.*`, `financialAssumptions.*`, `unitEconomics.*`

### Domande
1. Stato finanziario attuale (capitale versato, debito, round chiusi)?
2. Importo di funding richiesto, uso dei fondi, orizzonte temporale?
3. Tipo di funding: equity VC, debito bancario, bando pubblico specifico?

### Branching
- IF fundingType == "debt" → approfondisci: garanzie disponibili, patrimonio netto, cash flow storico
- IF fundingType == "grant" AND target == "smartstart" → chiedi aderenza requisiti startup innovativa
- IF fundingType == "grant" AND target == "horizon" → chiedi budget per Work Package, costo personale, overhead

---

## Block 8: Contesto Giuridico / Italia-UE
**Maps to:** `company.legalForm`, `company.isInnovativeStartup`, `financialAssumptions.usePatentBox`, `financialAssumptions.useTaxCredits`

### Domande
1. Forma societaria (SRL, SPA, SRLS, cooperativa)?
2. Siete iscritti o intendete iscrivervi come startup innovativa (DL 179/2012)?
3. Quali agevolazioni fiscali intendete utilizzare (Patent Box, crediti R&S, Transizione 4.0, Nuova Sabatini)?

### Branching
- IF company.isInnovativeStartup == true → verifica requisiti: costituita da meno di 60 mesi, fatturato < 5M, almeno 1 criterio innovazione soddisfatto

---

## Post-Interview

Dopo aver completato tutti i blocchi:
1. Mostra un riepilogo completo dei dati raccolti
2. Chiedi conferma o correzioni
3. Valida il JSON risultante con `validate_input.py`
4. Salva in `.business-plan/businessPlanInput.json`
