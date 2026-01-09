
### Why this template fixes your bullet concatenation issue
Your original template used `{%- if ... %}` which tells Jinja2 to **strip the preceding newline**, so multiple bullet lines can “stick together”. The revised version removes those dash modifiers and forces newlines in every bullet section.

---

## Confirming your “Measured Market Reactions” section

### Is it valid for Layer-1?
Yes—**conceptually it is valid** for Layer-1 *if and only if*:

1. **Each reaction row is a measured outcome** (computed from your market data service)  
2. It is **time-windowed**, deterministic, and linked to:
   - an `event_id` (timeline)
   - a window definition (`t0_to_t+60m`, `pre_to_close`, etc.)
3. You are **not interpreting causality** (e.g., “SPX fell because of the auction”).

Your sample rows satisfy the structure: *instrument → event_id → window → move_pct*. That’s exactly what you want for L1.

### What I would tighten (important)
Your current output is valid but not yet “institutional-grade” unless you also do these:

1) **Define t0 precisely per event type**  
- For news: `t0 = published_ts`  
- For macro releases: `t0 = scheduled release ts` (not when Reuters posts)  
- For auctions: `t0 = auction results timestamp`  
If you don’t define this, “measured reaction” becomes fuzzy.

2) **Use a canonical window set**
Pick a standard set and stick to it:
- `t0_to_t+5m`, `t0_to_t+30m`, `t0_to_t+60m`, `t0_to_close`, `pre_to_close`  
Then lint: only these are allowed.

3) **Reduce the volume for readability / chunk quality**
Dumping 80–200 lines into one chunk can harm retrieval.
Two options:
- **Group by event_id** (best), or
- Keep list form but cap to “indices + top affected tickers” (e.g., 5–10 instruments per event).

If you want, I’ll provide a grouped-by-event rendering block (still L1) that produces far better chunk semantics.

4) **Add “basis” metadata in JSON (not necessarily in markdown)**
For institutional auditability, your reaction window entries should include:
- `t0_ts` (the actual timestamp used)
- `t0_price`, `t1_price` (or at least `start_px`, `end_px`)
- `vendor` + `bar_resolution` (1m, 5m, etc.)

You can keep the markdown concise while preserving audit fields in the JSON.

---

## Recommendation: one small template tweak for reactions (optional but strongly advised)

If you want to keep your markdown readable and improve chunking, switch Section 3 to **group by event** (this is a big win). Tell me and I’ll provide the exact Jinja snippet; it requires only that `reaction_windows` be sortable/groupable (or you pre-group them in JSON).

---

If you paste one of the rendered markdown files that previously failed formatting (the concatenated bullets one), I can confirm the exact line that will now be fixed by this template.
::contentReference[oaicite:0]{index=0}


### What this achieves for your sample doc
- The concatenated “Index / Rates / Vol” lines in `day_2026-04-21.md` will render as clean bullets. :contentReference[oaicite:5]{index=5}  
- Reaction windows won’t be an unreadable flat dump; they’ll be **event-scoped**, and each event becomes its own semantic unit for retrieval.

---

## C. Confirming “Measured Market Reactions” validity (and what you should enforce)
Your section is valid Layer-1, but you should enforce these as **hard requirements**:

1) **Canonical window set** (lint): only allow a fixed set (like the template’s `allowed_windows`).  
2) **Deterministic t0 definition per event type**:
   - macro release → scheduled timestamp
   - filings → published timestamp
   - auction → results timestamp
3) **Audit basis stored in JSON** (recommended, not strictly required in MD):
   - `t0_ts, t1_ts, start_px, end_px, bar_resolution, calc_method`

Right now your markdown only shows `move_pct`, so it’s “valid but not audit-grade.” :contentReference[oaicite:6]{index=6}

---

## D. Two additional lint rules you should add now (based on the sample)
These are non-negotiable if you want stability:

### 1) Rate unit correctness (HARD)
If symbol matches `UST` / `SOFR` / `Fed Funds` and field represents a yield/rate level, require `unit == "pct"`.  
Your sample violates this (`UST 2Y: 4.15 bps`). :contentReference[oaicite:7]{index=7}  

### 2) Market session derived from timestamp (HARD)
Enforce:
- `pre` if ts < `13:30Z`
- `regular` if `13:30Z <= ts < 20:00Z`
- `post` if ts >= `20:00Z`

Your sample has an event at `14:14Z` labeled `post`. :contentReference[oaicite:8]{index=8}  

---

## E. One generator tweak you should make (so template improvements aren’t “papering over” data problems)
Even with the improved template, you should fix the generator so you don’t keep emitting invalid units/sessions:

- For `rates_fx_commodities`, yields should be `unit="pct"`, and yield change should be separate, e.g.:
  - `change_bps: +4.0` (or `change_pct_pt: +0.04`)
- For event sessions, compute from published_ts.

If you paste your current generator’s `generate_market_outcomes()` and event timestamp logic (or point me to the exact functions), I’ll give you the exact code diffs consistent with your existing style.

---

If your next step is “make this pass the new render lint,” apply this template and re-render `day_2026-04-21.md`. It should immediately eliminate the bullet concatenation that’s visible in the sample. :contentReference[oaicite:9]{index=9}
::contentReference[oaicite:10]{index=10}

---

## Why your current output is collapsing into one line

You can see in your rendered `.md` that the index bullets are concatenated like:

`- **SPX**: ... Range ...- **NDX**: ... Range ...- **RUT** ...` 

That is exactly what `trim_blocks/lstrip_blocks` does in Jinja when templates rely on natural newlines around `{% for %}` blocks. So: **fix the renderer**, not just the template.

---

## Two key generator corrections (non-negotiable)

1) **UST yields**
- `value` should be the yield in `%` (e.g., 4.19)
- `unit` should be `"pct"`
- the *change* should be in **bps**, stored as `change_bps` (e.g., -2.5)

Your older JSON is already closer to correct (`unit:"pct"`, `change:-2.5`)   
Your newer generator snippet sets `unit:"bps"` for yield **values** (wrong).

2) **Headline neutrality**
Your JSON includes “technology leads” / “sectors diverge” in `headline_neutral`. That violates your own L1 boundaries because “leads/diverge” implies interpretation.   
Your linter should hard-fail these phrases in L1 headlines.

---

## Next step (so we don’t regress)

If you want, I’ll apply the same standard to:
- your `generate_market_outcomes()` output schema (so units are consistent),
- your linter rules (hard-fail on causality/leadership language),
- your `render_l1.py` environment config (stop whitespace bugs permanently),
- and your `validate_l1.py` referential integrity for reaction windows.

But the above template + renderer change will already eliminate the most visible quality issue and make your L1 docs materially more “production-shaped.”
::contentReference[oaicite:6]{index=6}
