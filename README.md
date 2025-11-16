# My Heat Pump Explained

**AI-powered transparency for smart heating systems**

Built by the **Queen Mary University of London Computer Science Team** at Diverse AI Hackathon 2025

---

## The Problem

Heat pumps are crucial for UK decarbonisation, but **42% of users disable automation** due to opaque decision-making. When systems run at 2am or reduce power during peaks, homeowners lose trust and revert to manual control—undermining efficiency and grid flexibility.

## The Solution

An AI transparency tool that makes automated heat pump decisions understandable. Using real data from **742 UK installations**, we:

- **Detect** patterns (tariff optimisation, grid response, faults)
- **Explain** in plain language (<50 words, zero jargon)
- **Guide** with actionable next steps (normal/check/urgent)
- **Prove** reasoning with full transparency

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set API key
export ANTHROPIC_API_KEY='your-key-here'

# Run
streamlit run app.py
```

---

## Technical Approach

**Pattern Detection**: Rule-based classification of 5 scenarios (tariff optimisation, VPP curtailment, predictive heating, cold weather, faults)

**NLG**: Claude Sonnet 4 generates context-aware explanations with specific benefits (£ saved, kg CO₂ avoided)

**Data**: Electrification of Heat dataset—real performance from ASHP, HT-ASHP, Hybrid, GSHP installations

**Stack**: Python, Streamlit, Anthropic API, Plotly

---

## Features

### Pattern Detection
Analyses temperature deltas, COP efficiency, electricity pricing, grid signals, and weather forecasts

### Plain Language Explanations
*"Your smart tariff shifted heating to cheap-rate hours, saving £1.80 today."*

### Three-Tier Guidance
- Normal: "Everything working as designed"
- Check: "Monitor this, contact installer if continues"
- Urgent: "Potential fault—schedule service"

### Full Transparency
Every conclusion shows raw measurements, detection logic, property baseline, and calculated benefits

---

## Climate Impact

**UK target**: 19M heat pumps by 2050  
**Our contribution**: Building trust in automation to unlock:
- £200-400/year cost savings per household
- ~500 kg CO₂/year reduction per household
- Reliable grid flexibility for renewables

**At scale** (1M households): **500,000 tonnes CO₂/year avoided**

---

## Project Structure

```
├── app.py                          # Streamlit dashboard
├── heat_pump_explainer.py          # Analysis engine
├── property_profiles.py            # EoH data extraction
├── scenarios_from_real_data.json   # Pre-generated scenarios
└── requirements.txt
```

---

## Hackathon

**Event**: Diverse AI Hackathon 2025  
**Track**: "Flex for All" – equitable energy flexibility  
**Team**: Queen Mary University of London Computer Science  

---

## Acknowledgements

- **EoH Project Team** for the real UK heat pump dataset
- **Diverse AI Hackathon Organisers** for the opportunity
---

**Built by Queen Mary University of London Computer Science Team**
