---
title: Decon AI — Market Intelligence Engine
emoji: 🧬
colorFrom: green
colorTo: gray
sdk: docker
app_port: 8501
pinned: false
---

# 🧬 Decon AI — Market Intelligence Engine

An AI decision platform for Deconstruct. Two tools:

- **🧠 Product Intelligence** — live Amazon India competitor & category analysis: ratings, reviews,
  claims and rankings, with an AI launch/R&D brief, exported as a fully-documented multi-tab Excel.
- **🗣️ Review Intelligence** — deep-dive descriptive read of a single product's Amazon reviews: voice
  of customer, themes with real quotes, friction points, verdict — plus a chart-driven Excel export.

Built on a provider-agnostic AI core (Groq), live Amazon data (SerpAPI, with optional Apify for a
deeper review sample), and grounded, auditable analytics — every number traces to a source.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Configuration (environment variables / host secrets)

| Variable | Purpose | Required? |
|---|---|---|
| `LLM_PROVIDER=groq` | selects the AI provider | yes |
| `GROQ_API_KEY` | AI text analysis (both tools) | yes |
| `SERPAPI_KEY` | Amazon India search/product/review data | yes |
| `APIFY_KEY` | deeper review sample (~100+ instead of ~10-30) | optional |

Locally these live in a `.env`; on a host, set them as secrets/environment variables.
