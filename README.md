# Business Plan Generator — Claude Code Skill

Skill per Claude Code che genera business plan professionali per startup, PMI e grandi imprese — ricerca multi-dominio, architettura tecnica, modello finanziario completo e guide per mercato italiano ed europeo.

## Prerequisiti

- [Claude Code](https://claude.com/claude-code) installato
- Python 3.9+
- **Opzionale:** [Pandoc](https://pandoc.org/) per export PDF/DOCX (`apt install pandoc` o `brew install pandoc`)

## Installazione

```bash
# Clona il repository
git clone https://github.com/lucadidomenicodopehubs/business-plan-skill-v2
cd business-plan-skill-v2

# Copia nella directory skill di Claude Code
mkdir -p ~/.claude/skills
cp -r . ~/.claude/skills/business-plan/

# Installa dipendenze Python (opzionale, per validazione avanzata)
pip install -r requirements.txt
```

## Uso

```bash
# Avvia Claude Code nel tuo progetto
claude

# Avvia la skill (intervista guidata)
/business-plan

# Con tipo di piano pre-selezionato
/business-plan seed          # Startup seed/pre-seed (YC-style)
/business-plan bank          # Finanziamento bancario (SBA/Harvard)
/business-plan smartstart    # Smart&Start Italia (Invitalia)
/business-plan esa-bic       # ESA Business Incubation Centre
/business-plan horizon       # Horizon Europe Part B

# Flag combinabili
/business-plan seed --qa     # Con QA completo (Level 2)
/business-plan bank --lang en  # In inglese
/business-plan --input data.json  # Salta intervista, usa JSON
/business-plan --restart     # Ignora stato precedente

# Modalità what-if (dopo generazione)
/business-plan whatif        # Modifica scenari finanziari
```

## Tipi di piano supportati

| Tipo | Framework | Lingua | Pagine | Target |
|------|-----------|--------|--------|--------|
| seed | YC-style / Lean Canvas | IT | 15-20 | VC, acceleratori, CDP VC |
| bank | SBA / Harvard | IT | 30-40 | Banche, istituti di credito |
| smartstart | Smart&Start Italia | IT | 25-30 | Invitalia (startup innovative) |
| esa-bic | ESA BIC | EN | max 25 | ESA Business Incubation |
| horizon | Part B | EN | variabile | Horizon Europe / EIC |

## Output generati

```
business_plan.md              # Documento principale
business_plan.pdf             # Se Pandoc disponibile
business_plan.docx            # Se Pandoc disponibile
.business-plan/
├── businessPlanInput.json    # Dati intervista strutturati
├── marketResearch.json       # Ricerca di mercato
├── financials.json           # Modello finanziario completo
├── qa_report.json            # Report QA
└── history/                  # Versioni what-if
```

## Modello finanziario

Il modello genera automaticamente:
- **Conto Economico (P&L)** — 3-5 anni × 3 scenari (pessimistico/base/ottimistico)
- **Cash Flow Statement** — con variazioni capitale circolante
- **Stato Patrimoniale** pro-forma
- **Break-even Analysis** + Unit Economics (LTV, CAC, LTV/CAC)
- **Sensitivity Analysis** — matrice 5×5 (crescita ricavi × margine lordo)
- **Incentivi fiscali IT** — Patent Box, Credito R&S, Innovazione 4.0, Nuova Sabatini

## Quality Assurance

### Livello 1 (sempre attivo)
Controllo deterministico con 11 red flag:
- TAM solo top-down, competitor assenti, hockey-stick growth
- P&L/CF non riconciliati, cassa negativa senza finanziamento
- Unit economics impossibili, sezione rischi mancante
- Controlli bando-specifici (Smart&Start, ESA BIC, Horizon)

### Livello 2 (con --qa)
Valutazione LLM su 5 dimensioni con pesi dinamici per audience:
- Completezza strutturale, Qualità mercato, Robustezza financials
- Team/execution/traction, Aderenza normativa IT/UE

## Incentivi fiscali supportati

- **Startup Innovativa** (DL 179/2012) — requisiti e benefici
- **Patent Box** — super-deduzione 110% spese R&S
- **Credito R&S** — 20% spese ammissibili (tetto EUR 4M/anno)
- **Credito Innovazione 4.0** — 15% per transizione digitale/green
- **Nuova Sabatini** — contributo interessi su beni strumentali

## Sviluppo

```bash
# Esegui test
cd ~/.claude/skills/business-plan
python -m pytest tests/ -v

# Verifica sintassi Python
python -m py_compile scripts/financial_model.py
python -m py_compile scripts/validate_input.py
python -m py_compile scripts/red_flags.py
python -m py_compile scripts/export_doc.py
python -m py_compile scripts/whatif.py
```

## Licenza

MIT
