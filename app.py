"""
My Heat Pump Explained - Streamlit Dashboard
Track 2: Diverse AI Hackathon 2025
"""

import streamlit as st
import json
import plotly.graph_objects as go
from heat_pump_explainer import HeatPumpExplainer

# Page config
st.set_page_config(
    page_title="My Heat Pump Explained",
    page_icon="",
    layout="wide"
)


# Load data
@st.cache_data
def load_scenarios():
    with open('scenarios_from_real_data.json', 'r') as f:
        return json.load(f)


data = load_scenarios()


# Initialize explainer with API key
@st.cache_resource
def get_explainer():
    return HeatPumpExplainer(
        api_key='')


explainer = get_explainer()

# Header
st.title(" My Heat Pump Explained")
st.markdown("**AI-powered transparency for smart heating systems**")
st.markdown("---")

# Sidebar
st.sidebar.header(" Scenario Explorer")
st.sidebar.markdown("*Based on real UK heat pump installations*")

# Group scenarios by property
scenarios_by_property = {}
for scenario in data['scenarios']:
    prop_id = scenario['property_profile']['property_id']
    if prop_id not in scenarios_by_property:
        scenarios_by_property[prop_id] = []
    scenarios_by_property[prop_id].append(scenario)

# Property selector
property_options = list(scenarios_by_property.keys())
selected_property = st.sidebar.selectbox(
    "Select Property:",
    property_options,
    format_func=lambda x: f"{x} - {scenarios_by_property[x][0]['property_profile']['property_details']['house_type']}"
)

# Scenario selector for chosen property
property_scenarios = scenarios_by_property[selected_property]
scenario_names = [s['name'] for s in property_scenarios]
selected_scenario_name = st.sidebar.selectbox(
    "Select Scenario:",
    scenario_names
)

# Get selected scenario
selected_scenario = next(s for s in property_scenarios if s['name'] == selected_scenario_name)

# Property info sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("###  Property Details")
profile = selected_scenario['property_profile']
st.sidebar.text(f"Type: {profile['property_details']['house_type']}")
st.sidebar.text(f"Age: {profile['property_details']['house_age']}")
st.sidebar.text(f"Heat Pump: {profile['heat_pump_specs']['brand']}")
st.sidebar.text(f"Size: {profile['heat_pump_specs']['size_kw']}kW")
st.sidebar.text(f"Annual SPF: {profile['performance_data']['annual_spf']:.2f}")

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    # Scenario header
    st.header(selected_scenario['name'])
    st.caption(f" {selected_scenario['timestamp']}")

    # analyse scenario
    with st.spinner("Analyzing heat pump behaviour..."):
        result = explainer.analyze_scenario(selected_scenario)

    # CRITERIA 1: Pattern Detection
    st.markdown("###  What We Detected")
    pattern_col1, pattern_col2 = st.columns([1, 1])
    with pattern_col1:
        st.metric("Pattern Type", result['pattern_detection']['pattern_type'].replace('_', ' ').title())
    with pattern_col2:
        anomaly_text = " Anomaly" if result['pattern_detection']['is_anomaly'] else " Normal"
        st.metric("Status", anomaly_text)

    st.info(f"**Trigger:** {result['pattern_detection']['trigger']}")

    # CRITERIA 2: Plain Language Explanation
    st.markdown("---")
    st.markdown("###  What's Happening")
    st.success(f"**{result['explanation']}**")
    st.caption(f"*{result['word_count']} words*")

    # CRITERIA 3: Actionable Guidance
    st.markdown("---")
    st.markdown("###  What You Should Do")

    guidance = result['actionable_guidance']
    if guidance['tier'] == 'normal':
        st.success(f"**{guidance['status']}**")
    elif guidance['tier'] == 'check':
        st.warning(f"**{guidance['status']}**")
    else:
        st.error(f"**{guidance['status']}**")

    st.markdown(f"**Action:** {guidance['action']}")
    st.caption(guidance['detail'])

    # Benefits
    st.markdown("---")
    st.markdown("###  Your Benefits")
    benefit_col1, benefit_col2, benefit_col3 = st.columns(3)
    with benefit_col1:
        st.metric(" Cost Savings", f"Â£{result['benefits']['cost_savings']:.2f}")
    with benefit_col2:
        st.metric(" Carbon Avoided", f"{result['benefits']['carbon_kg']:.1f} kg")
    with benefit_col3:
        equivalent_trees = result['benefits']['carbon_kg'] / 25 if result['benefits']['carbon_kg'] > 0 else 0
        st.metric(" Equivalent", f"{equivalent_trees:.1f} trees")

with col2:
    # CRITERIA 4: Transparency
    st.markdown("###  Supporting Data")
    st.caption("*Building trust through transparency*")

    # COP Gauge
    cop = selected_scenario['data']['cop']
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=cop,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "System Efficiency"},
        gauge={
            'axis': {'range': [None, 5]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 2], 'color': "lightcoral"},
                {'range': [2, 2.5], 'color': "lightyellow"},
                {'range': [2.5, 3], 'color': "lightgreen"},
                {'range': [3, 5], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 1.8
            }
        }
    ))
    fig.update_layout(height=250, margin=dict(t=30, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)

    # Key measurements
    st.markdown("**Temperature:**")
    st.text(f"Indoor: {result['transparency_data']['measurements']['Indoor Temperature']}")
    st.text(f"Outdoor: {result['transparency_data']['measurements']['Outdoor Temperature']}")
    st.text(f"Target: {result['transparency_data']['measurements']['Target Temperature']}")

    st.markdown("**Performance:**")
    st.text(f"COP: {result['transparency_data']['measurements']['System Efficiency (COP)']}")
    st.text(result['transparency_data']['measurements']['COP Interpretation'])
    st.text(f"Power: {result['transparency_data']['measurements']['Power Consumption']}")

# Full transparency section (expandable)
st.markdown("---")
with st.expander(" Show Complete Transparency Data"):
    transparency = result['transparency_data']

    tab1, tab2, tab3, tab4 = st.tabs([
        "Detection", "Measurements", "Context", "Logic"
    ])

    with tab1:
        st.json(transparency['detection_details'])

    with tab2:
        st.json(transparency['measurements'])

    with tab3:
        st.json(transparency['context'])

    with tab4:
        st.markdown(f"**Why this conclusion:**")
        st.write(transparency['why_this_conclusion'])
        st.markdown("**Property baseline:**")
        st.json(transparency['property_details'])

# Q&A Section - AI Chatbot
st.markdown("---")
st.markdown("###  Ask About Your Heat Pump")

query = st.text_input(
    "Type your question:",
    placeholder="e.g., Why did my heat pump turn on at 2am? Why were there anomalies? How do heat pumps work?"
)

if query:
    st.markdown("####  Answer:")

    with st.spinner("Thinking..."):
        # Build comprehensive context for Claude
        current_scenario_data = selected_scenario['data']
        property_info = selected_scenario['property_profile']

        # Create context about the current scenario and dataset
        context = f"""You are an AI assistant helping homeowners understand their heat pump system. You have access to:

CURRENT SCENARIO CONTEXT:
- Scenario: {selected_scenario['name']}
- Indoor temp: {current_scenario_data['indoor_temp']}Â°C (target: {current_scenario_data.get('target_temp', 20)}Â°C)
- Outdoor temp: {current_scenario_data['outdoor_temp']}Â°C
- System efficiency (COP): {current_scenario_data['cop']}
- Power usage: {current_scenario_data['power_consumption_kw']} kW
- Electricity price: Â£{current_scenario_data.get('electricity_price_current', 0.15)}/kWh

PROPERTY INFORMATION:
- Type: {property_info['property_details']['house_type']}
- Heat pump: {property_info['heat_pump_specs']['brand']} {property_info['heat_pump_specs']['model']} ({property_info['heat_pump_specs']['size_kw']}kW)
- Typical efficiency: {property_info['performance_data']['annual_spf']:.2f} annual SPF

DATASET CONTEXT:
- Our demo uses real data from the Electrification of Heat (EoH) study
- 742 real UK heat pump installations monitored over 2+ years
- Scenarios are based on actual performance characteristics from these properties

AVAILABLE SCENARIOS IN DEMO:
1. Tariff optimisation - heating during cheap nighttime hours
2. VPP curtailment - grid demand response during peak times
3. Cold weather operation - normal winter efficiency drops
4. Predictive pre-heating - preparing for forecast cold weather
5. Potential faults - efficiency anomalies that need attention

USER QUESTION: {query}

Provide a helpful, accurate answer in plain language (no jargon). Keep it conversational and under 100 words. If the question is about:
- Dataset/anomalies: Explain what the EoH study is and why anomalies occur
- Specific heat pump behaviour: Reference the relevant scenario and explain clearly
- General heat pump questions: Provide educational information
- The demo itself: Explain what our tool does and how it works

Be warm, reassuring, and helpful. Avoid technical terms like "COP", "VPP", "SPF" unless asked specifically."""

        try:
            # Call Claude API for intelligent response
            from anthropic import Anthropic

            client = Anthropic(
                api_key='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')

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                messages=[{"role": "user", "content": context}]
            )

            answer = response.content[0].text.strip()
            st.info(answer)

            # Show if it relates to a specific scenario
            query_lower = query.lower()
            if any(word in query_lower for word in ['night', '2am', 'early', 'cheap', 'tariff']):
                st.caption(" Related scenario: Early Morning Heating on Cheap Tariff")
            elif any(word in query_lower for word in ['grid', 'peak', 'demand', 'vpp']):
                st.caption(" Related scenario: Grid Demand Response")
            elif any(word in query_lower for word in ['cold', 'weather', 'winter']):
                st.caption(" Related scenario: Cold Weather Performance")
            elif any(word in query_lower for word in ['predict', 'forecast', 'preheat']):
                st.caption(" Related scenario: Pre-heating Before Cold Snap")
            elif any(word in query_lower for word in ['fault', 'problem', 'inefficient']):
                st.caption(" Related scenario: Lower Than Expected Efficiency")

        except Exception as e:
            # Fallback if API fails
            st.error(f"AI response unavailable. Error: {str(e)}")
            st.info("Please try rephrasing your question or select a scenario above to see detailed explanations.")

# Footer
st.markdown("---")
st.caption("Built for Diverse AI Hackathon 2024 - Track 2: My Heat Pump Explained")
st.caption("Data source: Electrification of Heat (EoH) Study - 742 real UK installations")
