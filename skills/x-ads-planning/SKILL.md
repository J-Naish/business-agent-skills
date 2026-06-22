---
name: x-ads-planning
description: "Plan and design X Ads programs end-to-end: choose campaign objectives, X ad formats, campaign structure, targeting, bidding, creative requirements, measurement, policy constraints, and operating cadence. Use this skill whenever the user mentions X Ads, Twitter Ads, paid campaigns on X, Promoted Ads, Vertical Video Ads, X Amplify, X Takeovers, Dynamic Product Ads, Collection Ads, Branded Notifications, Branded Hashtags, Keyword Ads, Housing/Lending/Credit ads, Cause-Based Advertising, regulated X Ads, or X campaign planning."
---

# X Ads Planning

Plan X Ads programs from strategy through launch handoff: objective choice, campaign architecture, targeting, bidding, creative, measurement, and operating practice.

## Practice-first stance

X Ads planning should prioritize the practices that make campaigns work, not just the settings that make campaigns valid. Objective, format, placement, and bid settings matter, but they are secondary to measurement quality, creative quality, destination quality, audience signal design, budget sufficiency, and disciplined operating cadence.

Before proposing campaign settings, check these first:

| Area | What to verify | Why it matters |
|---|---|---|
| Business outcome | Revenue, qualified leads, app events, awareness, or conversation participation | X objective menus do not replace unit economics |
| Measurement | X Pixel, Conversion API / Conversions API, Events Manager, MMP, catalog events, UTMs | Weak signals make optimization and reporting misleading |
| Creative system | Distinct concepts, mobile fit, first-frame strength, aesthetic quality, refresh plan | X is fast-moving; weak creative dies quickly |
| Audience signals | Keywords, conversations, follower look-alikes, Custom Audiences, exclusions, Optimized Targeting | Targeting inputs increasingly act as signals, not rigid guarantees |
| Budget and volume | Budget-to-CPA/CPI ratio, expected conversion volume, test size | Small budgets cannot support fragmented structures |
| Destination | Landing page, app store, checkout, form, catalog, page speed, message match | X can create attention; the destination converts it |
| Controls | Geography, language, age, device, sensitive category rules, brand safety, managed-product eligibility | Automation and premium placements need guardrails |
| Operating cadence | Daily sanity checks, weekly optimization, creative refresh, measurement reconciliation | Most failures come from neglect or over-editing |

### Core operating rules

- Start from business outcome and unit economics, not from X Ads Manager menus.
- Treat the optimization signal as the strategy. Prefer the deepest reliable event with enough volume and acceptable delay.
- Separate platform performance from incrementality. Retargeting, post-view credit, branded demand, and cross-channel overlap can overstate X's business impact.
- Keep structures simple. Split campaigns or ad groups only for real control needs: objective, budget, economics, market, compliance, audience, creative test, buying path, or measurement.
- Use Optimized Targeting deliberately. It can expand beyond flexible targeting inputs, while respecting location, language, age, gender, OS, device, and exclusions.
- Treat creative as a primary lever. Test distinct concepts and hooks before cosmetic variants.
- Do not chase cheap CPM, CPC, CPE, CPV, or CPI unless downstream quality, brand safety, and incrementality remain acceptable.
- For ordinary paid ad copy, avoid hashtags, raw URLs, emoji clutter, and low-quality visuals. Use managed branded features or Conversation Buttons only when the selected product explicitly requires them.
- Avoid constant intervention. Batch meaningful changes and let delivery, conversion delay, and statistical noise settle before judging.

### Cadence

Use this as the default operating cadence unless the account context suggests otherwise:

| Cadence | Focus | Avoid |
|---|---|---|
| Daily | Spend anomalies, delivery drops, disapprovals, tracking/catalog/feed breaks | Daily target and budget thrashing |
| Weekly | Creative fatigue, audience quality, keyword/search intent, KPI pacing, destination quality | Restructuring from a few days of noise |
| Biweekly | New creative concepts, keyword/audience tests, budget shifts, landing-page checks | Launching many near-identical variants |
| Monthly | Measurement health, Custom Audiences, catalog health, incrementality assumptions, structure review | Letting launch-era assumptions persist |
| Quarterly | Business-model fit, objective strategy, source-of-truth reconciliation, managed-placement role | Reporting only X Ads Manager metrics |

### Measurement notes

- Use X metrics for tactical optimization, not as final financial truth.
- Reconcile against orders, CRM, app revenue, qualified pipeline, LTV, contribution margin, or another business source of truth.
- Keep post-engagement and post-view attribution assumptions visible.
- For app campaigns, configure an approved Mobile Measurement Partner before planning app-install bidding.
- For e-commerce/DPA, verify X Shopping Manager, product feed health, catalog event matching, and purchase value.
- X measurement infrastructure is less mature than Meta's in some areas: do not assume Meta-style CAPI Gateway, AEM, or EMQ exists on X.

## Output flexibility

Adapt the output to what the user actually asked for. There is no requirement to produce a written spec document.

| Situation | Output |
|---|---|
| User asks a focused question | Direct answer with reasoning. No document. |
| User wants planning guidance across the full picture | Structured inline response covering relevant sections. |
| User explicitly asks for a written plan / spec / brief | Produce a written deliverable inline or as a Markdown file, depending on requested format. |
| User is launching a multi-campaign account from scratch and the deliverable will be handed off | A written spec often fits, but confirm before writing unless clearly requested. |

## Workflow

```text
Step 0: Mode detection             -> New launch or improvement of existing account
    ↓
Step 1: Information gathering      -> Phase A basics -> business-model read -> Phase B details
    ↓
Step 2: Viability + strategy       -> Budget viability -> objective, format, targeting, structure
    ↓
Step 3: Creative + measurement     -> Define creative system, signal design, and operating cadence
    ↓
Step 4: Delivery                   -> Produce the answer, operating plan, spec, or creative brief
```

---

## Step 0: Mode Detection

Determine which situation applies. If unclear, ask.

| Mode | Trigger | Path |
|---|---|---|
| **New launch** | X Ads are not running yet, or new campaigns are being designed from scratch | Step 1 -> 2 -> 3 -> 4 |
| **Improvement of existing account** | Account is already running with performance issues or improvement goals | Step 1 -> diagnostic -> improvement proposals -> Step 2-4 as needed |

### Improvement workflow

For existing accounts, run a diagnostic after Step 1. Use [references/diagnostic-decision-trees.md](references/diagnostic-decision-trees.md) to rank likely root causes before proposing changes.

1. **Inventory** - Running campaigns, objectives, ad groups, budgets, bid strategies, targeting, placements, creative volume, and current KPIs.
2. **Issue identification** - Audit measurement, conversion quality, audience/targeting fit, creative fatigue, destination quality, budget sufficiency, and product eligibility.
3. **Improvement proposals** - Ranked actions with evidence, expected stabilization window, and changes to avoid.
4. **Execution / handoff** - Document agreed changes in the form that fits the task.

---

## Step 1: Information Gathering

Use available project context first. Ask only for missing information that affects the recommendation.

### Phase A: Basics

| Category | What to confirm |
|---|---|
| **Business model** | E-commerce / lead generation / app / SaaS / local / media / brand awareness |
| **Offer** | Product, service, app, event, content, free trial, lead magnet, product drop, etc. |
| **Goal** | Primary KPI: CPA, ROAS, CPL, CPI, CPV, CPE, reach, qualified lead rate, etc. |
| **Budget** | Monthly or daily media budget |
| **Destination** | Website, landing page, app store, deep link, product catalog, live event, or profile |
| **Audience** | Geography, language, age/gender if relevant, customer type, interests, keywords, conversation spaces |

After Phase A, use [references/business-model-playbooks.md](references/business-model-playbooks.md) to check the default strategy for the business model before choosing objectives or formats.

### Useful Context

| Category | What to confirm |
|---|---|
| Existing X Ads activity | Historical CTR, CVR, CPA, ROAS, CPI, CPE, CPV, creative learnings |
| Cross-channel results | Google, Meta, TikTok, LinkedIn, email, organic social, SEO, CRM performance |
| X account status | Verified Organizations, Premium, follower base, organic engagement, managed-service access |
| Measurement | X Pixel, Conversion API / Conversions API, Events Manager, app MMP, product catalog, UTMs |
| Creative | Existing posts, images, videos, product shots, creator assets, production capacity |
| Policy/compliance | Housing/lending/credit, health, finance, alcohol, employment, political/social issues, disclosures |

After the details are known, use [references/budget-planning.md](references/budget-planning.md) to check whether the budget can support the proposed objective, campaign mix, and learning volume. If not, narrow the structure before moving to Step 2.

---

## Step 2: Viability + Strategy Formation

Before choosing the final mix, combine:

1. Business-model fit from [references/business-model-playbooks.md](references/business-model-playbooks.md).
2. Budget and signal viability from [references/budget-planning.md](references/budget-planning.md).
3. Measurement readiness from [references/measurement-and-signal-quality.md](references/measurement-and-signal-quality.md).
4. Policy/account eligibility from [references/policy-and-account-requirements.md](references/policy-and-account-requirements.md).
5. Objective, format, and buying-path fit from the sections below.

Do not recommend a campaign type just because it exists. If budget, event quality, creative supply, account eligibility, catalog health, or measurement cannot support it, state what must be fixed first.

### 2-1. Campaign Objective Selection

X objective naming is in transition in some account flows. Official public pages still list **Website conversions**, while other current X surfaces refer to **Sales** and **Conversions**. Use "Website conversions / Sales" in planning and verify the current label in X Ads Manager before launch.

| Funnel | Objective / flow | Use when | Primary watch-out |
|---|---|---|---|
| Awareness | Reach | Maximize efficient exposure | Cheap reach can hide weak message recall |
| Consideration | Video views | Drive video consumption | Views are not conversion intent |
| Consideration | Website traffic | Drive landing-page visits | Use only when conversion tracking is not ready or traffic itself matters |
| Consideration | Pre-roll views | Run against premium publisher video | Context and brand safety matter more than last-click CPA |
| Consideration | Engagement | Drive post interaction | Engagement quality can be shallow |
| Consideration | App installs | Acquire app users | Approved MMP setup is required for app-install bidding |
| Conversion | App re-engagements | Drive existing app users to act | Requires app event measurement |
| Conversion | Website conversions / Sales | Drive tracked web conversions | Pixel/CAPI event quality determines performance |
| Advanced / contextual | Keywords campaign / Search Ads | Reach users around active search intent | Search Results placement is mandatory/default; availability can vary |

X does **not** have a current native lead-form objective equivalent to Meta Lead Ads or LinkedIn Lead Gen Forms. For lead generation, use Website traffic or Website conversions / Sales with a tracked form, CRM feedback, and landing-page quality controls.

For objective details, targeting, bidding, and measurement, use [references/campaign-strategy.md](references/campaign-strategy.md).

### 2-2. Recommended Structure by Business Type

| Business type | Objective / flow | Structure | Core formats | Measurement priority |
|---|---|---|---|---|
| **E-commerce / retail** | Website conversions / Sales; DPA where catalog-ready | Prospecting + retargeting/catalog campaigns | Dynamic Product Ads, Collection, Image/Video, Carousel | Purchase value, ROAS, margin, new vs returning |
| **Lead generation** | Website conversions / Sales or Website traffic | Prospecting + retargeting + proof/education | Image, Video, Carousel, Keyword Ads | Qualified lead, CRM stage, CPL to pipeline |
| **SaaS / B2B** | Website conversions / Sales; Website traffic for education | Intent/keyword + follower look-alike + retargeting | Text, Image, Video, Carousel, Keyword Ads | Qualified signup, demo, pipeline |
| **App** | App installs or App re-engagements | Install + re-engagement; separate OS/geo only when needed | Video, Vertical Video, Carousel with App Card | CPI, app event, retention, LTV |
| **Brand / launch** | Reach, Video views, Engagement | Broad reach + vertical video + optional premium placement | Vertical Video, Video, Image, Takeovers, Amplify | Reach, frequency, view quality, lift |
| **Live/event** | Reach, Video views, Engagement | Pre-event + live + post-event retargeting | X Live, Video, Branded Notifications, Takeovers | Registrations, viewers, watch time, clips |

### 2-3. Ad Format Selection Matrix

| Goal | First choice | Second choice | Third choice |
|---|---|---|---|
| Awareness | Vertical Video Ads | Video Ads | Image Ads / Takeover |
| Website traffic | Image or Video with Website Card | Carousel | Keyword Ads |
| E-commerce sales | Dynamic Product Ads | Collection Ads | Carousel / Video |
| Lead generation | Image/Video to landing page | Keyword Ads | Carousel proof sequence |
| App installs | Video / Vertical Video with App Card | Carousel with App Card | Image with App Card |
| Engagement | Text/Image/Video | Polls / Conversation Buttons where available | Branded features |
| Premium context | Amplify Pre-roll | Amplify Sponsorship | X Live / Takeover |

### 2-4. Buying Path and Eligibility

| Buying path | Use when | Examples |
|---|---|---|
| Self-serve via X Ads Manager | Performance campaigns, testing, standard Promoted Ads, app/website objectives | Image, Video, Carousel, DPA, Collection, Keywords campaign |
| Eligible / account-dependent | Feature access varies by account, market, or workflow | Vertical Video, Amplify Pre-roll, Polls, Conversation Buttons |
| Managed service / high-touch | Premium reservation, sponsorship, large events, branded features | Timeline Takeover, Spotlight Takeover, Amplify Sponsorship, Branded Notifications, Branded Hashtags, X Live |

### 2-5. After Selection

Present the direction before going deep:

1. Recommended objective and why.
2. Campaign-mix overview: number of campaigns/ad groups and role of each.
3. Recommended formats and buying path.
4. Targeting posture, including whether Optimized Targeting should be used.
5. Bid strategy, budget allocation, and measurement prerequisites.

---

## Step 3: Creative + Measurement Design

This step links creative, targeting, and measurement. On X, fast-feed creative, keyword/conversation context, and optimization signals must reinforce one another.

### Creative Design Principles

- Lead with one message and one audience problem.
- Show the product, proof, outcome, or conversation hook early.
- Design for mobile-first feeds and vertical environments.
- Use 4:5 and 2:3 assets when reusing Meta/TikTok/Instagram creative; X expanded these ratios in 2026 for creative portability.
- Use captions or text overlays for video, but keep them readable and uncluttered.
- Keep ordinary paid ad copy free of hashtags unless using a managed branded feature or Conversation Button.
- Avoid raw URLs in copy when Website Cards or App Cards are available.
- Treat Aesthetic Score guidance as operationally important, but do not report it as a guaranteed visible metric unless the current account exposes it.

For creative principles, Aesthetic Score guidance, hook design, CTA selection, and testing cadence, use [references/creative-fundamentals.md](references/creative-fundamentals.md).

### Measurement Design

Use [references/measurement-and-signal-quality.md](references/measurement-and-signal-quality.md) before finalizing launch recommendations.

| Business type | Preferred signal | Watch-outs |
|---|---|---|
| E-commerce / retail | Purchase with value; product-level events | Revenue ROAS can hide margin, returns, discounts, and existing-customer bias |
| Lead generation | Qualified lead / CRM stage when volume allows | Raw leads can train cheap low-quality volume |
| SaaS / subscription | Qualified signup, demo, activation, retained value | Trial/signup volume can mislead if activation is weak |
| App | Install -> in-app event -> retained value/LTV | Do not optimize forever to installs |
| Brand / awareness | Reach, frequency, view quality, lift/proxy demand | Last-click CPA will understate upper-funnel value |
| Live/event | Registration, reminder opt-in, viewers, watch time, post-event actions | Event value depends on timing and follow-up |

### Format-Specific References

| Format | Reference |
|---|---|
| Text Ads | [text-ads.md](references/text-ads.md) |
| Image Ads | [image-ads.md](references/image-ads.md) |
| Video Ads | [video-ads.md](references/video-ads.md) |
| Vertical Video Ads | [vertical-video-ads.md](references/vertical-video-ads.md) |
| Carousel Ads | [carousel-ads.md](references/carousel-ads.md) |
| Collection Ads | [collection-ads.md](references/collection-ads.md) |
| Dynamic Product Ads | [dpa.md](references/dpa.md) |
| Keywords campaign / Search Ads | [search-keyword-ads.md](references/search-keyword-ads.md) |
| Amplify Pre-roll | [amplify-preroll.md](references/amplify-preroll.md) |
| Amplify Sponsorship | [amplify-sponsorship.md](references/amplify-sponsorship.md) |
| Timeline Takeover | [timeline-takeover.md](references/timeline-takeover.md) |
| Spotlight Takeover | [spotlight-takeover.md](references/spotlight-takeover.md) |
| X Live | [x-live.md](references/x-live.md) |
| Branded Notifications | [branded-notifications.md](references/branded-notifications.md) |
| Branded Hashtags / branded features | [branded-hashtags.md](references/branded-hashtags.md) |
| Grok and xAI creative tools | [grok-ad-tools.md](references/grok-ad-tools.md) |

---

## Step 4: Delivery

Produce the output that fits the user's request: a short recommendation, structured inline plan, strategy memo, operating specification, or creative brief.

### References to Use

| Theme | Reference | Contents |
|---|---|---|
| Objectives, structure, targeting, bidding | [campaign-strategy.md](references/campaign-strategy.md) | Objective selection, Optimized Targeting, keyword targeting, buying path, bidding |
| Business-model playbooks | [business-model-playbooks.md](references/business-model-playbooks.md) | E-commerce, lead gen, SaaS/B2B, app, brand, event |
| Budget planning | [budget-planning.md](references/budget-planning.md) | CPA/CPI/ROAS economics, signal viability, budget split |
| Measurement and signal quality | [measurement-and-signal-quality.md](references/measurement-and-signal-quality.md) | X Pixel, Conversion API, MMP, catalog, attribution, incrementality |
| Policy and account requirements | [policy-and-account-requirements.md](references/policy-and-account-requirements.md) | Account eligibility, Verified Organizations, HLC, cause-based, healthcare, finance, restricted categories |
| Diagnostics | [diagnostic-decision-trees.md](references/diagnostic-decision-trees.md) | Existing-account failure modes and fixes |
| Creative fundamentals | [creative-fundamentals.md](references/creative-fundamentals.md) | Aesthetic Score, copy, hooks, CTA, testing |
| Creative strategy | [creative-strategy.md](references/creative-strategy.md) | X-native voice, creator/founder handles, fatigue, replies, video posture |
| Creative testing | [creative-testing.md](references/creative-testing.md) | Post count, concept tests, audience-thesis tests, refresh rules |
| Format-specific details | Format files linked above | Specs, use cases, mistakes |

### Platform Notes

- X Ads product names, eligibility, specs, and managed-service availability change quickly. Verify current availability in X Ads Manager or with an X representative before final launch.
- Official X public pages currently still use some legacy labels such as Website conversions and Conversion API while other surfaces use Sales, Conversions, or Conversions API. Preserve both when needed and verify the account UI.
- Premium products such as Timeline Takeover, Spotlight Takeover, Amplify Sponsorship, Branded Hashtags, Branded Notifications, and X Live may require managed-service access or X Next/account-team support.
- Benchmarks vary heavily by market, category, creative, objective, bidding, and measurement quality. Treat CPM, CPC, CPV, CPE, CPI, CPA, and ROAS benchmarks as planning inputs, not promises.

## Related Workflows

- Use Google Ads, Meta Ads, TikTok Ads, LinkedIn Ads, or other platform planning skills for cross-platform media mix design.
- Use creative or copywriting workflows when the user needs finished ad copy or production-ready assets.
- Use analytics/tracking workflows when the user needs implementation for X Pixel, Conversion API / Conversions API, app MMP, catalog feeds, or CRM attribution.
