---
name: meta-ads-planning
description: "Plan and design Meta ads programs for Facebook, Instagram, Messenger, Threads, Audience Network, and WhatsApp end-to-end: choose objectives, conversion locations, performance goals, Advantage+ automation, campaign structure, creative requirements, placements, Pixel/CAPI/app/CRM measurement, diagnostics, and operating instructions. Use this skill whenever the user mentions Meta ads, Facebook ads, Instagram ads, paid social on Meta, Advantage+ Sales/Leads/App, Lead Ads, Reels ads, app promotion, catalog ads, or Meta campaign planning. Skip for unrelated paid-media platforms."
---

# Meta Ads Planning

Plan a Meta ads program end-to-end: objective selection, campaign architecture, Advantage+ posture, creative system, measurement design, budget viability, diagnostics, and launch/operating decisions. This skill covers both new launches and improvements to existing accounts.

## Practice-first stance

Meta ads planning should prioritize the practices that make campaigns work, not just the settings that make campaigns valid. Objective, placements, and bid strategy matter, but they are secondary to measurement quality, conversion signal design, creative quality, account structure, budget sufficiency, customer controls, and disciplined operating cadence.

Before proposing campaign settings, check these first:

| Area | What to verify | Why it matters |
|---|---|---|
| Conversion design | Pixel/CAPI, app SDK/MMP, offline/CRM feedback, deduplication, event depth, value | Bad signals make delivery learn the wrong outcome |
| Incrementality | New vs existing customers, retargeting bias, VTC/engage-through share, finance source of truth | Platform ROAS is a steering signal, not business truth |
| Creative system | Distinct concepts, hooks, proof, offer, format fit, refresh cadence | Creative is a major audience-shaping and persuasion lever |
| Budget and volume | Target CPA/ROAS realism, expected event volume, budget-to-CPA ratio | Underfunded ad sets and campaigns produce noisy learning |
| Structure | Consolidation, split logic, audience overlap, budget control needs | Fragmentation splits signal and increases volatility |
| Destination | Landing page, Instant Form, checkout, app store, catalog, messaging flow, offer match | Ads amplify the destination |
| Controls | Customer exclusions/caps, geo/language/age, Special Ad Categories, brand safety | Automation needs real business guardrails |
| Operating cadence | Learning windows, change log, creative testing rhythm, measurement reviews | Most failures come from neglect or over-editing |

### Core operating rules

- Start from business outcome and unit economics, not from Ads Manager menus.
- Treat **objective + conversion location + performance goal + optimization event** as the strategy. The objective is not a reporting label; it instructs delivery.
- Prefer the deepest reliable event with enough volume and acceptable latency. Keep weak micro-events temporary or secondary unless they predict downstream quality.
- Separate platform performance from incrementality. Retargeting, view-through attribution, modeled conversions, engage-through attribution, and existing-customer delivery can overstate business impact.
- Consolidate for learning; split only for real control needs: objective, budget, economics, geo/language, compliance, customer type, funnel role, creative test, or measurement.
- Use broad/Advantage+ delivery as the default posture when signal and creative quality support it, but keep real business constraints as controls.
- Treat creative as a primary lever. Test distinct concepts, not cosmetic variants; use Advantage+ creative as a multiplier on human strategy, not a substitute for positioning.
- Do not chase cheap CPM, clicks, engagement, installs, or raw leads unless downstream quality and incrementality remain acceptable.
- Avoid constant intervention. Batch meaningful changes and allow learning periods, conversion delay, and statistical noise to settle before judging.

### Cadence

Use this as the default operating cadence unless the account context suggests otherwise:

| Cadence | Focus | Avoid |
|---|---|---|
| Daily | Spend anomalies, tracking drops, disapprovals, catalog/feed errors, lead/app event outages | Daily bid/target rewrites |
| Weekly | Creative fatigue, lead/product/app quality, budget pacing, customer/audience breakdowns | Restructuring from a few days of noise |
| Biweekly | Creative testing readout, new concept launches, form/LP/store diagnostics | Cosmetic variants with no strategic question |
| Monthly | Structure review, suppression lists, CAPI/EMQ health, attribution/reporting checks | Letting launch-era assumptions persist |
| Quarterly | Incrementality review, event design, Advantage+ vs manual role, business-model strategy | Reporting only platform ROAS |

### Measurement notes

- Use Meta metrics for tactical optimization, not as final financial truth.
- Keep click-through, engage-through, view-through, modeled, new-customer, and existing-customer assumptions visible where possible.
- Reconcile against orders, CRM, POS, app revenue, pipeline, LTV, contribution margin, or another finance source of truth.
- Monitor new vs existing customer contribution, especially in Advantage+ Sales and retargeting-heavy setups.
- Use Meta Experiments, A/B tests, conversion lift, geo holdouts, CRM/customer holdouts, MMM, or pre/post analysis when budget and volume allow.
- Treat reporting-tool/API changes as dated implementation details; verify current Ads Manager/API behavior before hard-coding attribution-window claims.

### Common Meta Ads glossary

Use these shared terms instead of repeating basic definitions in each playbook.

| Term | Meaning |
|---|---|
| Objective | Awareness, Traffic, Engagement, Leads, App promotion, or Sales |
| Conversion location | Website, app, Instant Form, calls, Messenger, Instagram, WhatsApp, website+app, or physical store/offline path depending on objective |
| Performance goal | The outcome Meta optimizes for inside the objective, such as purchases, leads, conversations, reach, landing page views, installs, or value |
| Optimization event | Specific event used for delivery learning: Purchase, Lead, CompleteRegistration, app event, qualified lead, etc. |
| Pixel | Browser-side event source |
| CAPI | Conversions API server-side event source |
| Deduplication | Matching Pixel and CAPI events with shared event name and `event_id` |
| EMQ | Event Match Quality diagnostic for matching parameters |
| AEM | Aggregated Event Measurement; web/app behavior changes over time and must be verified |
| MMP | Mobile Measurement Partner such as AppsFlyer, Adjust, Singular, Branch, or Kochava |
| SKAN / AAK | SKAdNetwork / Apple AdAttributionKit |
| ASC | Advantage+ Sales campaign, formerly Advantage+ Shopping in many workflows |
| Advantage+ Audience | Audience automation using suggestions plus expansion unless controls restrict it |
| Advantage+ Placements | Placement automation across eligible inventory |
| Advantage+ Creative | Creative enhancements and variations at ad level |
| CRM feedback | Qualified lead, opportunity, closed-won, offline purchase, LTV, or other business outcome sent back to Meta |
| VTC | View-through conversion: impression-only credit followed by conversion |
| Engage-through | Social engagement or qualified video engagement followed by conversion in the available window |
| Special Ad Category | Meta policy category such as credit / financial products and services, employment, housing, or social issues/elections/politics |

## Output flexibility

Adapt the output to what the user actually asked for. There is no requirement to produce a written spec document.

| Situation | Output |
|---|---|
| User asks a focused question | Direct answer with reasoning. No document. |
| User wants planning guidance across the full picture | Structured inline response covering relevant sections. |
| User explicitly asks for a written plan / spec / brief | Produce a written deliverable inline or as a Markdown file, depending on requested handoff format. |
| User is launching a multi-campaign account from scratch and the deliverable will be handed off | A written spec often fits, but confirm before writing unless clearly requested. |

---

## Workflow

```
Step 0: Mode detection           -> New launch or improvement of existing account
    ↓
Step 1: Information gathering    -> Phase A basics -> business-model read -> Phase B details
    ↓
Step 2: Viability + objective selection -> Budget/signal viability -> campaign mix that fits
    ↓
Step 3: Strategy formation       -> Structure, bidding, measurement, creative, Advantage+ posture
    ↓
Step 4: Detailed design + delivery -> Per-objective playbooks; deliver as fits the situation
```

---

## Step 0: Mode detection

Determine which situation applies. If unclear, ask.

| Mode | Trigger | Path |
|---|---|---|
| **New launch** | Meta ads are not running yet, or new campaigns are being designed from scratch | Step 1 -> 2 -> 3 -> 4 |
| **Improvement of existing account** | Account is already running with performance issues or improvement goals | Step 1 -> diagnostic -> improvement proposals -> Step 3-4 as needed |

### Improvement workflow

For existing accounts, run a diagnostic after Step 1 before proposing changes.

- If the user provides account data in any form - CSV/XLSX exports, copied tables, screenshots, dashboards, CRM reports, Events Manager diagnostics, catalog reports, MMP exports, API extracts, or metric summaries - first use [references/account-data-diagnostics.md](references/account-data-diagnostics.md).
- If the user only describes symptoms, use [references/symptom-diagnostics.md](references/symptom-diagnostics.md) to rank likely root causes.
- Always separate supported findings from limitations, rank actions by business impact and evidence, and include expected stabilization windows plus changes to avoid.

---

## Step 1: Information gathering

### Phase A: Basics

| Category | What to confirm |
|---|---|
| **Business model** | E-commerce / lead generation / app / local business / SaaS / brand awareness |
| **Offer** | Product, service, free trial, lead magnet, app, catalog, event, or store visit |
| **Goal** | Primary KPI: CPA, ROAS, CPL, CPI, retained value, lift, reach, pipeline, etc. |
| **Budget** | Monthly or daily ad budget |
| **Destination** | URL, app store, Instant Form, Messenger/Instagram/WhatsApp flow, catalog, store/POS |
| **Audience constraints** | Geography, language, age, compliance, customer type, exclusions, Special Ad Category |

After Phase A, use [references/business-model-playbooks.md](references/business-model-playbooks.md) to check the default strategy for the business model before choosing objectives or structure.

### Phase B: Detailed inputs for design

| Category | What to confirm |
|---|---|
| **Existing account state** | Running campaigns, current objective mix, budgets, issues, change history |
| **Conversion data** | Last 30/60/90 days by event: purchases, leads, qualified leads, app events, value, latency |
| **Measurement** | Pixel, CAPI, deduplication, EMQ, domain, app SDK/MMP, offline/CRM feedback |
| **Catalog** | Product catalog, feed health, content IDs, product sets, margin/inventory labels |
| **Creative** | Existing videos/images, concept diversity, production capacity, UGC/social proof |
| **Customer data** | Purchaser lists, lead stages, high-LTV cohorts, exclusions, new/existing customer definitions |
| **Policy** | Special Ad Category, regulated vertical, teen targeting, financial/health/sensitive constraints |

After the details are known:

- Use [references/budget-planning.md](references/budget-planning.md) to check whether the budget can support the proposed conversion event, campaign mix, and learning volume.
- Use [references/measurement-and-attribution.md](references/measurement-and-attribution.md) when conversion tracking is not yet live, CAPI/app measurement is involved, lead quality is a problem, or reporting reconciliation matters.
- Use [references/policy-and-special-categories.md](references/policy-and-special-categories.md) before recommending targeting for credit, employment, housing, social issues/elections/politics, financial services, health, teens, or other constrained categories.

---

## Step 2: Viability + objective selection

Before choosing the final mix, combine:

1. Business-model fit from [references/business-model-playbooks.md](references/business-model-playbooks.md).
2. Budget and signal viability from [references/budget-planning.md](references/budget-planning.md).
3. Measurement readiness from [references/measurement-and-attribution.md](references/measurement-and-attribution.md).
4. Objective and automation fit from the cheat sheet and playbooks below.

Do not recommend an objective just because it is available. If budget, event quality, creative supply, catalog health, app measurement, CRM feedback, or policy cannot support it, state what must be fixed first.

### Campaign-objective cheat sheet

Meta's "campaign type" is usually **objective + conversion location + performance goal + automation layer**, not a channel type like Search or Shopping.

| Objective | Primary role | Best for | Main playbook |
|---|---|---|---|
| **Awareness** | Reach, frequency, ad recall, brand lift, upper-funnel video | Brand launches, category creation, events, full-funnel support | [references/awareness-traffic-engagement.md](references/awareness-traffic-engagement.md) |
| **Traffic** | Landing page visits, link clicks, profile/WhatsApp/phone/website traffic | Content distribution, consideration pages, low-signal bridge campaigns | [references/awareness-traffic-engagement.md](references/awareness-traffic-engagement.md) |
| **Engagement** | Video views, post engagement, messages, event responses, social proof | Video pools, communities, events, message volume, mid-funnel warming | [references/awareness-traffic-engagement.md](references/awareness-traffic-engagement.md) |
| **Leads** | Raw leads, higher-intent leads, calls, click-to-message leads, Conversion Leads | B2B, services, education, real estate, local, high-ticket inquiry flows | [references/leads-campaigns.md](references/leads-campaigns.md) |
| **App promotion** | Installs, app events, value, re-engagement | Apps, mobile games, subscription apps, retained user growth | [references/app-campaigns.md](references/app-campaigns.md) |
| **Sales** | Purchases, website/app conversions, catalog sales, value, purchases through messaging | E-commerce, D2C, subscriptions, catalog retail, conversion-led revenue | [references/sales-campaigns.md](references/sales-campaigns.md) |

### Selection references

Use the cheat sheet only for first-pass direction. Before finalizing the mix, read:

| Decision | Reference |
|---|---|
| Default mix by business model and funnel role | [references/business-model-playbooks.md](references/business-model-playbooks.md) |
| Budget sufficiency, expected event volume, and what not to launch yet | [references/budget-planning.md](references/budget-planning.md) |
| Awareness / Traffic / Engagement details | [references/awareness-traffic-engagement.md](references/awareness-traffic-engagement.md) |
| Leads, Instant Forms, click-to-message leads, calls, Conversion Leads | [references/leads-campaigns.md](references/leads-campaigns.md) |
| App promotion, app events, iOS/SKAN/AAK, MMP, re-engagement, playable ads | [references/app-campaigns.md](references/app-campaigns.md) |
| Sales, Advantage+ Sales, catalog ads, collection, purchases through messaging | [references/sales-campaigns.md](references/sales-campaigns.md) |
| Advantage+ automation and controls | [references/advantage-plus.md](references/advantage-plus.md) |
| Measurement, CAPI, attribution, offline/CRM, and app signal quality | [references/measurement-and-attribution.md](references/measurement-and-attribution.md) |
| Format specs and placement overview | [references/ad-formats-and-placements.md](references/ad-formats-and-placements.md) |

Verify current Meta documentation or current Ads Manager UI before implementing volatile features such as Advantage+ Sales controls, existing-customer budget cap behavior, Advantage+ Leads eligibility, attribution columns, Detailed Targeting exclusions, AEM behavior, Threads placement availability, and teen/Special Ad Category targeting.

### After selection, confirm direction with the user

Present:

1. Recommended objective(s), conversion location(s), and performance goal(s).
2. Campaign-mix overview: how many campaigns/ad sets and the role of each.
3. Advantage+ vs manual posture and which controls remain human-owned.
4. Bidding strategy and budget split.
5. Measurement prerequisites or blockers.

Get confirmation before going deep into Step 3 unless the user asked for a full plan directly.

---

## Step 3: Strategy formation

This step decides cross-campaign strategy. Per-objective detailed design happens in Step 4 using the playbooks.

Use this order:

1. Confirm business-model strategy and campaign roles.
2. Confirm budget viability and expected event volume.
3. Define conversion signals and incrementality stance.
4. Decide structure, bidding, Advantage+ posture, and budget split.
5. Define creative strategy using [references/creative-strategy.md](references/creative-strategy.md).

### Account structure

Meta Ads is a 3-layer structure: Ad account -> Campaign -> Ad set -> Ad.

| Level | Design principle |
|---|---|
| Campaign | Split by objective, budget owner, economics, geography/language, compliance, lifecycle/customer type, or materially different measurement goal. |
| Ad set | Split only when the optimization event, conversion location, audience control, placement, budget, or test question truly needs separation. |
| Ad | Hold distinct creative concepts, format variations, copy variants, catalog assets, or flexible creative units. |

### Naming conventions

Establish a single naming convention before launch. Naming directly impacts filtering, reporting, and diagnosis.

#### Campaign name

**Format:** `{Obj}_{Goal}_{Audience}_{Geo}_{Note}`

| Element | Values | Notes |
|---|---|---|
| Obj | `Sales` `Lead` `App` `Awareness` `Traffic` `Engagement` | Objective abbreviation |
| Goal | `Purchase` `Value` `QLead` `Install` `AppEvent` `Reach` `LPV` `Msg` | Performance goal or optimization event |
| Audience | `Prospecting` `Retargeting` `NewCustomer` `Existing` `Broad` `SAC` | Audience/customer role |
| Geo | `US` `EU` `LATAM` `SEA` `Global` etc. | Geographic targeting; omit only if obvious |
| Note | Product/category/test/compliance note | As needed |

**Examples:** `Sales_Purchase_NewCustomer_US`, `Lead_QLead_Prospecting_EMEA`, `App_AppEvent_iOS_LATAM`, `Awareness_Reach_Broad_Global`, `Engagement_Msg_Prospecting_SEA`.

#### Ad set name

**Format:** `{LocationOrEvent}_{AudienceControl}_{PlacementOrTest}`

Examples: `Website_Purchase_Broad`, `InstantForm_HigherIntent_Broad`, `AppEvent_PurchaserValue_iOS`, `Messenger_Conversation_Manual`, `Catalog_ProductSet_HighMargin`.

#### Naming rules

- Use underscores `_` consistently.
- Use English-based names for better compatibility with Ads Manager filters and exports.
- Use PascalCase tokens (`NewCustomer`, `HigherIntent`, `HighMargin`).
- Do not include start dates unless it is a time-bound test; append `_Test_YYMM` only when useful.
- Maintain a shared abbreviation list for objectives, events, regions, and customer segments.

### Bidding strategy

Use [references/budget-planning.md](references/budget-planning.md) and the selected objective playbook before selecting, changing, or rolling back bid strategies. At minimum, check:

1. Primary optimization-event volume in the last 30 days.
2. Event latency vs attribution and decision window.
3. CPA / ROAS / value stability.
4. Signal depth: purchase, qualified lead, app value, retained user, or micro-event.
5. Budget-to-bid ratio.

Default path: start with **Highest volume** in current Ads Manager UI (often represented as lowest-cost/automatic bidding in older docs or API language) for unstable launches, introduce **Cost per result goal** only after the account has stable volume and defensible economics, and use **Bid cap** / **ROAS goal** only when value data and delivery volume can support stricter control.

### Conversion design

Use [references/measurement-and-attribution.md](references/measurement-and-attribution.md) for Pixel/CAPI, deduplication, EMQ, offline events, Conversion Leads CRM integration, app measurement, attribution, and incrementality. Use [references/advantage-plus.md](references/advantage-plus.md) for Advantage+ automation controls and manual fallback decisions.

Keep the high-level rule in the active plan: choose the deepest reliable event with workable volume and latency, keep weak proxies secondary or temporary unless validated, and separate click-through, engage-through, view-through, modeled, and business-source-of-truth results when the decision is material.

### Budget allocation

Use [references/budget-planning.md](references/budget-planning.md) before applying allocation rules. The 70 / 20 / 10 split is only a default operating pattern when the budget is large enough to fund learning in each bucket.

**70 / 20 / 10 rule:**

- 70% - proven campaigns and concepts.
- 20% - testing new creative, offers, conversion locations, or audiences.
- 10% - exploratory objectives, new formats, or new funnel bets.

### Operating cadence

Use the cadence table in [Practice-first stance](#cadence) as the canonical operating rhythm. Per-objective playbooks may add specific checks, but should not override the basic rule: monitor anomalies frequently, batch meaningful changes, and avoid reacting to short-term noise.

### Common pitfalls

| Failure mode | Fix |
|---|---|
| Optimizing Sales/Leads to a shallow event because it is easier to get volume | Validate proxy quality, import deeper events, and move back toward the business outcome |
| Traffic or Engagement expected to drive purchases | Use Sales when revenue is the goal, or label upper-funnel campaigns as support with separate KPIs |
| Raw leads look cheap but sales rejects them | Add form friction, qualify questions, CRM feedback, Conversion Leads, or downstream value |
| Advantage+ Sales reports high ROAS while blended revenue is flat | Segment new/existing customers, reconcile backend revenue, and test incrementality |
| Pixel-only setup at meaningful spend | Add CAPI with deduplication and EMQ hygiene |
| Catalog sales underperform while campaign settings look fine | Diagnose feed, content IDs, product availability, price, product sets, and margin labels |
| App campaigns optimize forever to installs | Move to app events/value when volume and measurement allow |
| Creative testing is only cosmetic variants | Build distinct concepts: problem, outcome, proof, offer, objection, comparison, social proof |
| Special Ad Category ignored until launch | Check policy and targeting limits before structure and audience design |

---

## Step 4: Detailed design + delivery

For each selected objective, consult the matching playbook for both practice and settings. The practice sections should drive the recommendation; settings are the implementation layer.

Before asset specs or copy drafts, use [references/creative-strategy.md](references/creative-strategy.md) to define audience, offer, proof, objections, format fit, and test angles. Produce one filled brief per concept using the [Creative Brief Template](references/creative-strategy.md#7-creative-brief-template) before commissioning production. Then use objective playbooks and [references/creative-production.md](references/creative-production.md) for format-specific production.

### Per-objective playbooks

| Objective / campaign type | Playbook | Key design topics |
|---|---|---|
| Awareness | [references/awareness-traffic-engagement.md](references/awareness-traffic-engagement.md) | Reach, ad recall, Brand Lift, Reservation buying, Threads, video-led creative, upper-funnel measurement |
| Traffic | [references/awareness-traffic-engagement.md](references/awareness-traffic-engagement.md) | Link clicks vs landing page views, traffic-as-sales antipattern, LPV quality, content/consideration roles |
| Engagement | [references/awareness-traffic-engagement.md](references/awareness-traffic-engagement.md) | Video views, messages, event responses, social proof, Reels/Stories/Threads, handoff to Sales/Leads |
| Leads | [references/leads-campaigns.md](references/leads-campaigns.md) | Instant Forms, Higher Intent, Rich Creative, website leads, click-to-message, calls, Conversion Leads, CRM quality loops |
| App promotion | [references/app-campaigns.md](references/app-campaigns.md) | Advantage+ App, app event ladder, iOS AAK/SKAN/AEM, MMPs, CAPI for App, re-engagement, playable ads |
| Sales | [references/sales-campaigns.md](references/sales-campaigns.md) | Advantage+ Sales, manual Sales, catalog ads, collection/Instant Experience, purchases through messaging, value optimization |

### Cross-cutting design references

Use these inside the workflow, not just as optional reading:

| Reference | Use when | Key design topics |
|---|---|---|
| [references/business-model-playbooks.md](references/business-model-playbooks.md) | Choosing strategy by business model | E-commerce, lead gen, SaaS, local, app, brand, combination patterns |
| [references/budget-planning.md](references/budget-planning.md) | Deciding what the budget can realistically support | CPA/ROAS economics, expected event volume, campaign mix viability |
| [references/measurement-and-attribution.md](references/measurement-and-attribution.md) | Designing events, choosing attribution, planning incrementality, diagnosing signal issues | Pixel/CAPI, deduplication, EMQ, offline/CRM, app measurement, attribution, lift |
| [references/advantage-plus.md](references/advantage-plus.md) | Deciding automation posture and manual fallback structure | Advantage+ Sales, Leads, App, Audience, Placements, Creative, CBO, volatile controls |
| [references/account-data-diagnostics.md](references/account-data-diagnostics.md) | Interpreting account exports, screenshots, dashboards, CRM/MMP/catalog data, Events Manager diagnostics | Data intake, field map, evidence ranking, if-this-then-that actions |
| [references/policy-and-special-categories.md](references/policy-and-special-categories.md) | Regulated or constrained categories | Special Ad Categories, targeting limits, teen/sensitive topics, compliance-first design |
| [references/symptom-diagnostics.md](references/symptom-diagnostics.md) | Improving an existing account from symptoms | Spend/CV issues, lead quality, fatigue, signal, structure, Advantage+ traps |
| [references/creative-strategy.md](references/creative-strategy.md) | Designing creative system, tests, and briefs | Angles, proof, objections, funnel-stage creative, refresh cadence |
| [references/creative-production.md](references/creative-production.md) | Producing assets and copy | Image, video, carousel, collection, Instant Forms, Instant Experience |
| [references/ad-formats-and-placements.md](references/ad-formats-and-placements.md) | Need a quick overview of formats or placements | Image, video, carousel, collection, Instant Experience, placements, safe zones |
| [references/setup-checklist.md](references/setup-checklist.md) | Setup-level implementation | Account setup, Pixel/CAPI basics, targeting, bidding, ad setup |
| [references/campaign-structure.md](references/campaign-structure.md) | Structural templates and naming | 2/3-campaign patterns, learning, KPIs, structure examples |

### Delivering the output

Match the output shape to [Output flexibility](#output-flexibility). Do not create a written deliverable unless the user asks for one or the plan is clearly being handed off to another team, agency, or client.

If a written plan is the right deliverable, it typically covers:

1. Strategy summary - goal, audience, and why this objective mix.
2. Campaign list - objective, conversion location, performance goal, bidding, budget split.
3. Per-objective design - driven by the playbooks.
4. Advantage+ posture - what is automated, what remains controlled, what must be verified in current UI.
5. Creative requirements - concepts, formats, specs, production owner, refresh cadence.
6. Measurement design - Pixel/CAPI/app/CRM/offline setup, conversion definitions, attribution view.
7. Operating timeline - launch, learning phase, optimization phases, diagnostics cadence.
8. KPIs and success criteria - platform metrics, business source of truth, and incrementality plan.

For Markdown-file deliverables, keep the structure practical rather than template-heavy: use clear sections, decision tables where they help handoff, explicit assumptions, and concrete launch/measurement actions. Avoid filling generic sections that do not change the campaign decision.

---

## Related workflows

| Adjacent need | Use a separate skill or workflow when |
|---|---|
| Landing page copywriting | The user needs full landing page copy, not just ad copy |
| Landing page design | The user needs the destination page structure or design |
| Analytics implementation | The user needs GA4, GTM, Meta Pixel, Conversions API, SDK, or MMP work implemented |
| Competitive research | The user needs competitor ads or market research |
| Image generation | The user needs banner or image creative generated |
| Video generation | The user needs video creative generated |
| Google Ads planning | The user is planning Google Ads instead of Meta ads |
