# Complaint Sentiment & Urgency Triage System

*NLP pipeline built on Microsoft Azure AI Language (Free Tier) — MSBA 695-50 Cloud Computing, University of Louisville, July 2026*

**Author:** Miranda Pachini (development) | Co-presented with German Collado

## Business Problem

Companies that handle high volumes of written customer complaints struggle to spot urgent issues quickly. A single fraud complaint can sit unread behind hundreds of routine ones, and manual review doesn't scale without a large data science budget. I built a meaningful triage pipeline using only free, prebuilt Azure tools — so smaller teams can act on urgent complaints faster without paid infrastructure or labeled training data.

## What It Does

A lightweight NLP pipeline that turns raw complaint text into an actionable, prioritized worklist:

- **Sentiment Analysis** — flags each complaint as positive, negative, neutral, or mixed, with a confidence score
- **Key Phrase Extraction** — pulls the core topics from each complaint (e.g., "unauthorized charge," "late payment," "credit report error") as visible evidence behind every flag
- **Urgency Routing** — a transparent, rule-based classifier (keyword matching, not a black-box model) that assigns each complaint a category (Fraud, Credit Reporting, Customer Service, Billing) and an urgent flag when sentiment is negative **and** 2+ severity keywords are present

The output feeds a Streamlit dashboard that a fraud, support, or compliance team can filter and act on directly.

## Results From My Test Sample

Running my pipeline on 100 sampled CFPB complaints:
- **34%** carried negative sentiment
- **11%** met the stricter urgency bar (negative sentiment + 2+ severity keywords) — the real "act now" signal

## Dataset

[CFPB Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/search/) — a free, public U.S. government dataset of 6.8M+ consumer complaints about financial products, updated daily, accessed via a public REST API requiring no key. For the live Streamlit demo, a local 1.4 GB bulk CFPB CSV (via Kaggle) was used in place of the live API for instant, reliable loading during the presentation.

## Tools & Architecture

| Category | Tool / Service |
|---|---|
| Data source | CFPB Consumer Complaint Database API (free, public, no key) |
| NLP engine | Azure AI Language — Free (F0) tier, under Azure AI Foundry's Natural Language category |
| NLP features | Sentiment Analysis and Key Phrase Extraction (prebuilt, no custom training) |
| Code | Python (`requests` for API calls, `pandas` for data handling) |
| Routing logic | Plain Python if/else keyword matching — deterministic and fully auditable |
| Demo | Streamlit dashboard |

Azure AI Language is used as PaaS (Platform as a Service): Microsoft manages the underlying models and infrastructure, and the project only manages its own application logic and data. No Azure Machine Learning compute, GPU, or paid model deployment is used — every component runs on free tiers.

**Optional upgrade path (documented, not required):** swapping the rule-based router for a low-cost LLM (Azure OpenAI GPT-5-nano or GPT-4o-mini) was cost-modeled at under $5/month even at 100,000 complaints/month, but was intentionally left out of the free baseline.

## Azure Setup

Standard Azure resource hierarchy: **Subscription → Resource Group → Resource**

1. Sign in to the Azure Portal with an Azure for Students subscription (free credit, no card required)
2. Create a Resource Group to hold all project resources
3. Create an Azure AI Language resource on the Free (F0) tier inside that group
4. Run `complaint_triage.py`, which fetches sample complaints from the CFPB API and calls Azure AI Language for sentiment and key phrases at no cost

## Responsible AI

I explicitly designed the project around Azure's six Responsible AI pillars — Fair, Reliable & Safe, Private & Secure, Inclusive, Transparent, and Accountable — most notably:
- **Transparent:** every flag is shown next to the exact keyword that triggered it — no hidden confidence score
- **Accountable:** the system only recommends; it never auto-closes a complaint or takes an irreversible action, so a human reviewer stays responsible for every real decision
- **Private & Secure:** built entirely on CFPB's already-scrubbed public data — no additional personal data is collected or stored

## Business Impact

| Impact Area | Effect |
|---|---|
| Faster response to urgent issues | Fraud/safety complaints surface same-day instead of waiting behind routine ones |
| Lower triage labor cost | Reduces manual reading and tagging of every incoming complaint |
| Early problem detection | Spikes in specific key phrases are visible before they become widespread issues |
| Better resource allocation | Teams can staff toward the categories generating the most negative sentiment |

## Recommendations for a Live Version

1. Run it on live, incoming complaints — the value is catching new fraud early, not analyzing history
2. Add automated alerting (email/Slack/Teams) when a complaint is flagged urgent
3. Periodically review false negatives and expand the keyword list — this is meant to be a living system
4. Track real outcomes against flags to build an accuracy record and evaluate whether an LLM upgrade is worth the cost

## Sources

- CFPB Consumer Complaint Database — [consumerfinance.gov](https://www.consumerfinance.gov/data-research/consumer-complaints/search/)
- CFPB API documentation — [cfpb.github.io/api/ccdb](https://cfpb.github.io/api/ccdb/)
- Microsoft Azure AI Language documentation — [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/ai-services/language-service/)
- Microsoft Azure AI Foundry documentation — [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/ai-foundry/)
- Microsoft Azure OpenAI Service pricing — [azure.microsoft.com/pricing](https://azure.microsoft.com/en-us/pricing/details/azure-openai/)
- Course materials: Mohsen Asghari, PhD — Azure AI Engineer course, MSBA 695-50, 2026

*AI assistance: Claude (Anthropic) was used to help draft and structure the project proposal, run the cost-benefit analysis, and write/debug the accompanying Python code, under my direction and review.*
