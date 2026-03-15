---
name: business-plan
description: |
  Genera business plan professionali per startup, PMI e grandi imprese.
  Full-spectrum: seed, bank, smartstart, esa-bic, horizon.
  Ricerca di mercato ibrida con selezione fonti. Modello finanziario completo
  con scenari what-if. QA a livelli (red-flag sempre, completo su richiesta).
  Mercato italiano ed europeo con incentivi fiscali aggiornati.
  Use when: user asks for a business plan, piano aziendale, piano d'impresa,
  feasibility study, studio di fattibilita, or mentions /business-plan.
---

# Business Plan Generator — Orchestrator

You are generating a professional business plan. Follow these phases strictly in order.
All paths below are relative to `~/.claude/skills/business-plan/` (the SKILL_DIR).
The working directory for outputs is the USER'S project root (cwd), under `.business-plan/`.

## 0. Argument Parsing

Parse `$ARGUMENTS` for:
- **Plan type**: `seed` | `bank` | `smartstart` | `esa-bic` | `horizon` (default: auto-detect during interview based on funding type and company stage)
- **Flags**:
  - `--qa` — enable QA Level 2 (AI reviewer rubric)
  - `--restart` — ignore existing state, start fresh
  - `--input <path>` — load JSON directly, skip interview
  - `--lang <it|en>` — language override (default: `it` for Italian plans, `en` for esa-bic/horizon)
- **Special mode**: `whatif` — enter what-if scenario mode on an existing plan

Store parsed values in local variables: `plan_type`, `qa_level2`, `restart`, `input_path`, `lang`, `whatif_mode`.

## 1. Resume Detection

Check if `.business-plan/businessPlanInput.json` exists in the user's project root.

- **File exists, interview incomplete, no --restart**: Read the file. If `interviewState.isComplete == false`, ask:
  > "Ho trovato un'intervista in corso (blocco {N}/{total} completato). Vuoi riprendere dal blocco {N+1}?"
  If user says yes, jump to Phase 1 at the correct block.

- **File exists, interview complete, no whatif**: Ask:
  > "Un business plan esiste gia. Vuoi: (1) rigenerarlo, (2) modificare con what-if, o (3) ricominciare da zero?"
  Handle accordingly: (1) skip to Phase 2, (2) enter what-if mode, (3) delete `.business-plan/` and start fresh.

- **--restart flag**: Delete `.business-plan/` directory and proceed to Phase 1.

- **--input flag**: Read the provided JSON file, copy it to `.business-plan/businessPlanInput.json`, skip to Phase 2.

## 2. What-if Mode

Only if `whatif_mode` is active or user chose option (2) above.

1. Read `.business-plan/businessPlanInput.json` and `.business-plan/financials.json`
2. Ask the user:
   > "Cosa vuoi cambiare? Puoi usare linguaggio naturale, es. 'crescita al 20%', 'margine lordo 65%', 'aggiungi una linea di revenue consulenza a 50k/anno'."
3. Translate the user's request into a `whatif.py` call:
   - Single field: `python SKILL_DIR/scripts/whatif.py --field <dot.path> --value <val>`
   - Multiple fields: `python SKILL_DIR/scripts/whatif.py --patch '{"financialAssumptions.revenueGrowthRate": 0.20, ...}'`
   Run with Bash tool from the user's project root.
4. After recalculation: read the updated `financials.json`
5. Rewrite ONLY the financial sections of `business_plan.md` (Executive Summary numbers, Financial Projections, Sensitivity Analysis)
6. Re-run QA Level 1 on modified sections (see Phase 4)
7. Print summary of changes and updated key metrics

## 3. Phase 1 — Interview

Read `SKILL_DIR/templates/interview-blocks.md` for the full interview structure.

### Rules
- Ask **ONE block at a time** — never dump all questions at once
- After each block: summarize the collected data in a compact table, ask for confirmation
- Apply **branching logic** from the interview-blocks template based on sector and funding type
- If the user's answer is vague or insufficient, ask a focused follow-up before moving on
- Speak in Italian by default (or the language set by `--lang`)

### Incremental Save
After each confirmed block, update `.business-plan/businessPlanInput.json`:
```bash
mkdir -p .business-plan
```
Write the JSON with `interviewState.completedBlocks` updated to include the just-completed block number, and `interviewState.isComplete` set to `false` until all 8 blocks are done.

### Auto-detect Plan Type
If `plan_type` was not specified in arguments, determine it after Block 7 (Finanza & Funding):
- fundingType == "equity" + early stage → `seed`
- fundingType == "debt" → `bank`
- startup innovativa + bando Smart&Start → `smartstart`
- ESA/space connection → `esa-bic`
- EU Horizon/EIC mentioned → `horizon`

### Validation
After all 8 blocks are complete, set `interviewState.isComplete = true` and run:
```bash
python SKILL_DIR/scripts/validate_input.py .business-plan/businessPlanInput.json
```
If validation fails: show the errors to the user, ask for corrections, update the JSON, and re-validate. Do not proceed until validation passes.

## 4. Phase 2 — Research + Financial Model (parallel)

### Source Selection
Present the source menu to the user:
```
Fonti disponibili per la ricerca di mercato:
1. [x] WebSearch — trend, report pubblici, news
2. [x] ISTAT/Eurostat — dati statistici ufficiali
3. [x] Registro startup innovative (MIMIT)
4. [ ] Crunchbase — competitor e funding
5. [ ] Fonti personalizzate — URL specifici
Quali vuoi attivare? (default: 1,2,3)
```
If user selects option 5, ask for the specific URLs.

### Parallel Execution
Launch BOTH tasks simultaneously:

**Task A — Market Research** (Agent tool, subagent_type: research):
Read `SKILL_DIR/templates/prompts/researcher.md` for the full research prompt. Substitute:
- `{sector}` with the company's sector
- `{target_market}` with geographic target from interview
- `{competitors}` with any competitors mentioned
- `{enabled_sources}` with the user's source selection
- `{custom_urls_section}` with custom URLs if provided, or empty string

Use WebSearch tool for each enabled web source. Compile results into structured JSON.
Save output to `.business-plan/marketResearch.json`.

**Task B — Financial Model** (Bash tool, run_in_background: true):
```bash
python SKILL_DIR/scripts/financial_model.py < .business-plan/businessPlanInput.json > .business-plan/financials.json
```

### Error Handling
- If research fails or returns sparse data: warn the user, offer to (a) provide data manually, (b) proceed with available data, or (c) retry with different sources
- If financial model fails: show stderr, ask user to review input assumptions

## 5. Phase 3 — Writing

### Setup
1. Read the section template: `SKILL_DIR/templates/section-templates/{plan_type}.md`
2. Read the writer system prompt: `SKILL_DIR/templates/prompts/writer-system.md`
3. Load references based on plan type:
   - Italian plans (seed, bank, smartstart): read `SKILL_DIR/references/italy-incentives.md`
   - Grant plans (smartstart, esa-bic, horizon): read `SKILL_DIR/references/eu-programs.md`
   - Always: read `SKILL_DIR/references/kpi-by-sector.md`
4. Select language:
   - Default: IT for seed, bank, smartstart
   - Default: EN for esa-bic, horizon
   - Override with `--lang` if specified

### Data Loading
Read all three JSON data files:
- `.business-plan/businessPlanInput.json` — interview data
- `.business-plan/marketResearch.json` — research findings
- `.business-plan/financials.json` — financial projections

### Writing
Follow the section template structure exactly. For each section:
- Use data from the relevant JSON files
- Apply the writer system prompt guidelines (tone, formatting, evidence-backed claims)
- Include financial tables formatted in markdown
- Reference KPIs from `kpi-by-sector.md` relevant to the company's sector
- For Italian plans: mention applicable incentives from `italy-incentives.md`
- For grant plans: align with program requirements from `eu-programs.md`

Save the complete business plan to `business_plan.md` in the user's project root.

## 6. Phase 4 — QA

### Level 1 (ALWAYS — deterministic red-flag scan)
Construct a JSON payload from the data files and pipe it to `red_flags.py`:
```bash
python -c "
import json
fin = json.load(open('.business-plan/financials.json'))
inp = json.load(open('.business-plan/businessPlanInput.json'))
plan = open('business_plan.md').read()
comps = len(inp.get('market',{}).get('competitors',[]))
payload = {'financials': fin, 'input': inp, 'plan_text': plan, 'competitors_count': comps}
print(json.dumps(payload))
" | python SKILL_DIR/scripts/red_flags.py
```

Read the output. If CRITICAL flags are found:
1. Show them to the user with the suggested fixes
2. Propose automatic correction
3. If user agrees, rewrite affected sections of `business_plan.md`
4. Re-run red_flags.py to verify fixes

If only HIGH/MEDIUM/LOW flags: show them as informational warnings.

### Level 2 (only if `--qa` flag was set)
1. Read `SKILL_DIR/templates/prompts/reviewer-rubric.md`
2. Evaluate the business plan against every rubric dimension
3. Score each dimension 1-5
4. If any dimension scores < 3/5: rewrite the problematic sections (max 2 rewrite iterations)
5. Save the QA report to `.business-plan/qa_report.json` with structure:
   ```json
   {
     "level1": { "flags": [...], "critical_count": N, "high_count": N },
     "level2": { "scores": {"dimension": score, ...}, "feedback": {...}, "iterations": N },
     "timestamp": "ISO-8601"
   }
   ```

## 7. Phase 5 — Export

Run the export script:
```bash
python SKILL_DIR/scripts/export_doc.py business_plan.md
```

If exit code is 2 (no export tools), inform the user that only the markdown version is available.

### Final Summary
Print:
```
--- Business Plan Completo ---

> Business plan generato: business_plan.md
> QA Level 1: X flags (Y CRITICAL, Z HIGH)
> Export: MD + PDF + DOCX (o solo MD se Pandoc non disponibile)

File generati:
  - business_plan.md
  - business_plan.pdf (se disponibile)
  - business_plan.docx (se disponibile)
  - .business-plan/businessPlanInput.json
  - .business-plan/financials.json
  - .business-plan/marketResearch.json
  - .business-plan/qa_report.json
```

If QA Level 2 was run, also show the rubric scores summary.

End by asking: "Vuoi modificare qualcosa con what-if, o il piano e pronto?"
