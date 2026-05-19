---
name: tiktok-ads-planning
description: "Plan and design TikTok Ads programs end-to-end: choose TikTok Ads Manager objectives, ad formats, campaign structure, targeting, bidding, creative requirements, TikTok Shop/GMV Max options, Smart+, Symphony, lead generation, messaging, search, Spark Ads, premium reservation formats, and measurement. Use this skill whenever the user mentions TikTok Ads, TikTok for Business, TikTok Ads Manager, Spark Ads, Smart+, GMV Max, Video Shopping Ads, Search Ads, Lead Generation, Brand Consideration, Symphony, Branded Mission, Branded Effects, Branded Hashtag Challenge, TopView, Brand Takeover, Top Feed, TopReach, Logo Takeover, Prime Time, Pulse Mentions, Pulse Tastemakers, or TikTok campaign planning."
---

# TikTok Ads Planning

Plan TikTok Ads programs from strategy through launch handoff: campaign objective choice, format mix, account structure, targeting, bidding, creative, measurement, and operating practice.

## Practice-First Stance

TikTok Ads planning should prioritize what makes campaigns work, not just what makes them valid in TikTok Ads Manager. Objective, format, placement, and bid settings matter, but they are secondary to creative quality, signal quality, destination quality, budget sufficiency, account eligibility, commerce setup, and disciplined operating cadence.

Before proposing campaign settings, check these first:

| Area | What to verify | Why it matters |
|---|---|---|
| Business outcome | Sales, leads, app installs/events, reach, video views, engagement, conversations, GMV | TikTok objective menus do not replace unit economics |
| Measurement | TikTok Pixel, Events API, app MMP, TikTok Shop, catalog/product links, UTMs | Bad signals make optimization and reporting misleading |
| Creative system | Volume of distinct concepts, creator/UGC access, hook quality, refresh cadence | TikTok performance is heavily creative-driven |
| Commerce readiness | TikTok Shop, Showcase, Seller Center, catalog/product permissions, GMV Max eligibility | Shop Ads and GMV Max depend on commerce setup |
| Budget and volume | Target CPA/CPI/ROAS realism, conversion volume, creative test budget | Fragmented campaigns starve learning |
| Destination | Landing page, TikTok Shop PDP, app store, instant form, messaging destination | TikTok creates attention; the destination converts it |
| Policy/account eligibility | Restricted categories, branded products, music rights, creator authorization | Creative and account eligibility can block launch |
| Operating cadence | Daily sanity checks, weekly creative readouts, monthly signal/structure reviews | Most failures come from stale creative or over-editing |

### Core Operating Rules

- Start from business outcome and unit economics, not from ad format menus.
- Treat creative as a primary performance lever. Test different concepts, hooks, creators, offers, and proof points before cosmetic variants.
- Use TikTok-native creative: fast hook, human context, sound-aware design, captions/text overlays, and platform-native pacing.
- Prefer the deepest reliable optimization event with enough volume and acceptable delay.
- Keep structures simple. Split campaigns or ad groups only for real control needs: objective, budget, economics, market, compliance, audience, creative test, placement, or commerce setup.
- Use Smart+ and GMV Max deliberately. Automation still needs good creative, conversion signals, catalog/shop setup, and business-side validation.
- Plan identity early. TikTok is phasing out Custom Identity in favor of linked TikTok accounts for new campaigns, with exceptions depending on campaign type and account rollout.
- Separate platform-reported performance from incrementality. TikTok Shop, retargeting, view-through credit, and creator/organic effects can overstate business impact.
- Avoid chasing cheap CPM, CPC, CPV, CPL, or CPI unless downstream quality remains acceptable.
- Verify product names and eligibility in the current account because TikTok Ads Manager labels and Shop Ads availability change frequently.

## Workflow

```text
Step 0: Mode detection             -> New launch or improvement of existing account
    ↓
Step 1: Information gathering      -> Business model, goal, budget, audience, assets, measurement
    ↓
Step 2: Viability + format choice  -> Objective, buying path, format mix, signal readiness
    ↓
Step 3: Strategy + creative design -> Structure, targeting, bidding, measurement, creative system
    ↓
Step 4: Delivery                   -> Recommendation, plan, operating spec, or creative brief
```

## Step 0: Mode Detection

| Mode | Trigger | Path |
|---|---|---|
| **New launch** | TikTok Ads are not running yet, or new campaigns are being designed from scratch | Step 1 -> 2 -> 3 -> 4 |
| **Improvement** | Account is already running with performance issues or improvement goals | Step 1 -> diagnostic using references -> improvement proposals -> Step 2-4 as needed |

## Step 1: Information Gathering

Use available project context first. Ask only for missing information that affects the recommendation.

| Category | What to confirm |
|---|---|
| Business model | E-commerce / TikTok Shop / lead generation / app / SaaS / local / brand / media / live commerce |
| Offer | Product, service, app, lead magnet, event, TikTok Shop product, LIVE event, creator offer |
| Goal | Reach, Traffic, Video Views, Brand Consideration, Community Interaction, Lead Generation, App Promotion, Sales, GMV |
| Budget | Monthly or daily media budget; separate production/creator budget if relevant |
| Audience | Geography, language, age/gender if relevant, interests/behaviors, creators/communities, search intent |
| KPI | CPM, CPV, CPC, CTR, CPA, ROAS, GMV, ROI target, CPL, lead quality, CPI, in-app event, view-through assumptions |
| Creative | Existing videos, Spark Ads candidates, creators, UGC, product footage, still images, production capacity |
| Measurement | TikTok Pixel, Events API, app MMP, TikTok Shop/Seller Center, catalog, CRM/offline data, UTMs |
| Policy | Regulated category, music rights, creator disclosure, branded content, market-specific legal requirements |

## Step 2: Viability + Format Choice

TikTok Ads uses both **Auction** buying through TikTok Ads Manager and **Reservation / managed** buying for premium reach and branded experiences.

Before recommending the final mix, combine:

1. Business-model fit from [business-model-playbooks.md](references/business-model-playbooks.md).
2. Budget and learning viability from [budget-planning.md](references/budget-planning.md).
3. Creative-system readiness from [creative-strategy.md](references/creative-strategy.md) and [creative-testing.md](references/creative-testing.md).
4. Format fit from the cheat sheet below.

Do not recommend a campaign type just because it is available. If creative supply, conversion signal, destination quality, budget, commerce setup, or measurement cannot support it, state what must be fixed first.

| Buying path | Use when | Examples |
|---|---|---|
| Auction | Performance campaigns, testing, flexible budgets, always-on programs | In-Feed Ads, Spark Ads, Carousel Ads, Lead Generation, Search Ads, App Promotion, Smart+ modes |
| Automated commerce | TikTok Shop sales with automation and fewer manual controls | Product GMV Max, LIVE GMV Max |
| Reservation / managed | Guaranteed reach, premium placement, branded participation, creator crowdsourcing | TopView, Top Feed, TopReach, Logo Takeover, Prime Time, Pulse Mentions, Pulse Tastemakers, Brand Takeover, Reach & Frequency, Branded Hashtag Challenge, Branded Effects, Branded Mission |

### Official Terminology Notes

- **Sales** is TikTok's current integrated objective in newer account flows, merging Website Conversions and Product Sales for eligible advertisers. Older or phased interfaces may still show legacy labels.
- **Brand Consideration** is a gated mid-funnel objective for select customers onboarded to TikTok Market Scope. Treat it as managed-access unless the account shows it.
- **GMV Max** is the default and only supported campaign type for TikTok Shop Ads from July 2025 in current TikTok Help Center guidance. Use **Product GMV Max** and **LIVE GMV Max** when planning TikTok Shop campaigns.
- **Video Shopping Ads** may still appear for Showcase, catalog, or legacy/eligible contexts. Do not plan new TikTok Shop Sales campaigns around legacy Video Shopping Ads unless the current account flow explicitly supports it.
- **Smart+** is an auction automation mode, not a separate buying path. Current Smart+ products include Web, App, Lead Generation, Traffic, and Catalog Ads flows where available.
- **Symphony** is TikTok's AI creative suite. Use it as production support, not as a substitute for human creative strategy or rights review.
- **Custom Identity** is being phased out. For new campaigns, plan around linked TikTok accounts / authorized accounts unless an official exception applies.

### Format Cheat Sheet

| Format | Buying path | Primary job | Reference |
|---|---|---|---|
| In-Feed Ads | Auction / R&F eligible | Flexible performance and reach | [in-feed-ads.md](references/in-feed-ads.md) |
| Spark Ads | Auction | Boost organic TikTok posts or creator-authorized posts | [spark-ads.md](references/spark-ads.md) |
| Carousel Ads | Auction | Image-led story, product set, app/service explanation | [carousel-ads.md](references/carousel-ads.md) |
| Search Ads | Auction | Capture TikTok search intent | [search-ads.md](references/search-ads.md) |
| Lead Generation | Auction | Collect leads with TikTok Instant Forms or website forms | [lead-generation-ads.md](references/lead-generation-ads.md) |
| Messaging Ads | Auction / market-dependent | Start conversations in supported messaging destinations | [messaging-ads.md](references/messaging-ads.md) |
| Playable Ads | Auction / Pangle-oriented | Interactive app/game trial before install | [playable-ads.md](references/playable-ads.md) |
| Video Shopping Ads | Auction / eligibility-dependent | Shoppable videos for eligible commerce setups | [video-shopping-ads.md](references/video-shopping-ads.md) |
| Smart+ Catalog Ads | Auction / catalog | Catalog-driven product ads for website/app destinations where available | [smart-plus-catalog-ads.md](references/smart-plus-catalog-ads.md) |
| GMV Max | Automated commerce | Maximize TikTok Shop GMV/ROI | [gmv-max.md](references/gmv-max.md) |
| Reach & Frequency | Reservation | Forecasted reach and frequency control | [reach-and-frequency.md](references/reach-and-frequency.md) |
| Top Feed | Reservation / R&F | Premium first in-feed ad placement | [top-feed.md](references/top-feed.md) |
| TopView | Managed / premium | High-impact first exposure after app open | [topview.md](references/topview.md) |
| NewFronts 2026 premium formats | Managed | Logo Takeover, Prime Time, TopReach, Pulse Mentions, Pulse Tastemakers | [newfronts-2026-premium-formats.md](references/newfronts-2026-premium-formats.md) |
| Brand Takeover | Reservation / managed | Short full-screen takeover where available | [brand-takeover.md](references/brand-takeover.md) |
| Branded Hashtag Challenge | Managed | UGC participation around a branded hashtag | [branded-hashtag-challenge.md](references/branded-hashtag-challenge.md) |
| Branded Effects | Managed | AR/effect-led participation | [branded-effects.md](references/branded-effects.md) |
| Branded Mission | Managed | Crowdsource creator videos for brand campaigns | [branded-mission.md](references/branded-mission.md) |
| Symphony | Creative tooling | AI-assisted ideation, video generation, avatars, dubbing, creative refresh | [symphony-and-ai-tools.md](references/symphony-and-ai-tools.md) |

### Recommended Mix by Business Goal

| Goal | First choice | Second choice | Watch-out |
|---|---|---|---|
| Website sales | In-Feed/Spark with Sales or legacy Web Conversion flow | Search Ads, Carousel | Pixel/Events API quality and landing-page speed matter |
| TikTok Shop sales | Product GMV Max | Spark Ads in eligible Shop contexts | Automation can reduce manual control; validate against seller economics |
| LIVE commerce | LIVE GMV Max | In-Feed/Spark promotion | Requires LIVE operations and inventory readiness |
| Lead generation | Lead Generation + Spark/In-Feed | Search Ads | Lead quality and CRM feedback matter more than CPL |
| App installs | App Promotion + In-Feed/Spark | Playable Ads, Pangle where suitable | Optimize beyond installs when event volume supports it |
| Brand awareness | Reach & Frequency, TopView, Top Feed | Spark Ads, Branded Effects | Premium buys need managed availability and measurement plan |
| Mid-funnel consideration | Brand Consideration where available | Video Views, Traffic, Spark Ads | Requires TikTok Market Scope access and careful KPI definition |
| Engagement/community | Spark Ads, Community Interaction | Branded Hashtag Challenge, Branded Mission | Participation requires creator/community seeding |
| Search intent | Search Ads | In-Feed retargeting | Keyword-to-creative relevance is critical |

After selecting formats, present:

1. Recommended objective and format mix.
2. Why each format fits the business goal.
3. Budget role for each format.
4. Measurement prerequisites and primary KPI.

## Step 3: Strategy + Creative Design

Use these references as needed:

| Theme | Reference |
|---|---|
| Campaign structure, targeting, bidding, Smart+, learning, scaling, measurement | [campaign-strategy.md](references/campaign-strategy.md) |
| Creative principles, hooks, UGC/creator direction, sound, captions, refresh cadence | [creative-fundamentals.md](references/creative-fundamentals.md) |
| Practical creative strategy, hooks, fatigue, creator briefs | [creative-strategy.md](references/creative-strategy.md) |
| Creative testing cadence and decision rules | [creative-testing.md](references/creative-testing.md) |
| Budget viability and bid strategy selection | [budget-planning.md](references/budget-planning.md) |
| Business-model default playbooks | [business-model-playbooks.md](references/business-model-playbooks.md) |
| Existing-account diagnosis | [diagnostic-decision-trees.md](references/diagnostic-decision-trees.md) |
| Symphony AI creative tools | [symphony-and-ai-tools.md](references/symphony-and-ai-tools.md) |
| Format-specific details | The format reference files linked above |

### Structure Basics

- TikTok Ads Manager uses a three-level structure: **Campaign -> Ad Group -> Ad**.
- Use campaign objectives and optimization events that match the business outcome.
- Keep early tests simple: fewer campaigns, clear ad group hypotheses, multiple distinct creatives.
- Use Campaign Budget Optimization / campaign-level budget only when ad groups share the same goal and budget can be allocated flexibly.
- Use ad-group budgets when strict allocation, audience testing, or creative testing matters.
- During learning, avoid unnecessary edits. TikTok guidance says volatility often declines after about 25 campaign results or 7 days, and significant budget, bid/ROAS, bidding strategy, targeting, pause, or unreasonable creative-volume changes can disrupt learning.

### Creative Basics

Use TikTok's principle: **Don't Make Ads. Make TikToks.**

- Hook in the first 1-3 seconds.
- Make the product, problem, creator, or story visible early.
- Use captions/text overlays even when sound is important.
- Use Commercial Music Library or properly licensed audio for ads.
- Build creator-style concepts, not only polished brand edits.
- Refresh creative frequently; prioritize concept diversity over small variants.
- Use 3-5 unique creatives per ad group as a practical official baseline. At higher spend, plan a continuing creative pipeline rather than one launch batch.

### Naming and Tracking

Use consistent, English-based names for filtering and exports.

```text
Campaign: TT_{Objective}_{Funnel}_{Format}_{Market}
Ad group: AG_{Audience}_{Optimization}_{Placement}
Ad: Ad_{Concept}_{CreatorOrAsset}_{Variant}
```

Recommended UTM pattern:

```text
utm_source=tiktok
utm_medium=paid_social
utm_campaign={campaign_name}
utm_content={ad_name}
utm_term={keyword_or_audience}
```

## Step 4: Delivery

Produce the output that fits the request: a short recommendation, structured inline plan, strategy memo, operating specification, or creative brief. Do not force a written document unless the user asked for one or the deliverable needs to be handed off.

A full plan usually includes:

1. Strategy summary: business goal, audience, and chosen objective.
2. Format mix: selected TikTok ad formats and the job of each.
3. Campaign structure: campaigns, ad groups, budgets, targeting, bidding, and schedule.
4. Creative specification: concepts, hooks, aspect ratios, copy, audio, CTA, and refresh cadence.
5. Measurement design: Pixel / Events API / MMP / TikTok Shop / CRM / UTMs.
6. Operating cadence: launch checks, learning period, optimization rhythm, and reporting view.

## Platform Notes

- TikTok product names, campaign objectives, Shop Ads availability, specs, and managed-product access change over time. Verify current account availability in TikTok Ads Manager or with a TikTok representative before launch.
- Premium products such as TopView, Brand Takeover, Top Feed, TopReach, Logo Takeover, Prime Time, Pulse, Branded Hashtag Challenge, Branded Effects, Branded Mission, and some Reach & Frequency options may require managed access.
- Benchmarks vary heavily by market, category, creative, objective, bidding, placement, and measurement quality. Treat CPM, CPC, CPV, CPI, CPA, CPL, ROAS, and GMV benchmarks as planning inputs, not promises.
