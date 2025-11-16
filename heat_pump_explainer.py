"""
Heat Pump Explanation Engine - Track 2
Addresses all 4 criteria:
1. Detect unusual patterns
2. Explain in plain language
3. Provide actionable guidance
4. Build trust through transparency
"""

import json
from anthropic import Anthropic
from typing import Dict, Any, Tuple


class HeatPumpExplainer:
    def __init__(self, api_key: str = None):
        """Initialize the explainer with Claude API"""
        if api_key:
            self.client = Anthropic(api_key=api_key)
        else:
            # Will use ANTHROPIC_API_KEY env var
            self.client = Anthropic()

    # CRITERIA 1: DETECT UNUSUAL PATTERNS


    def detect_pattern(self, scenario_data: Dict) -> Dict[str, Any]:
        """
        Detect what pattern/anomaly is occurring
        Returns: pattern type, severity, and confidence
        """
        data = scenario_data['data']

        # Extract key metrics
        indoor_temp = data['indoor_temp']
        target_temp = data.get('target_temp', 20.0)
        outdoor_temp = data['outdoor_temp']
        cop = data['cop']
        power_kw = data['power_consumption_kw']

        # Pattern detection logic

        # ANOMALY: Low efficiency / potential fault
        if cop < 1.8 and outdoor_temp > 0:
            return {
                'pattern_type': 'efficiency_anomaly',
                'severity': 'high',
                'confidence': 'high',
                'trigger': f'COP of {cop:.1f} is unusually low for {outdoor_temp}°C',
                'is_anomaly': True,
                'category': 'potential_fault'
            }

        # ANOMALY: Not reaching target temperature
        if indoor_temp < target_temp - 2.0 and data.get('heat_pump_status') == 'heating':
            return {
                'pattern_type': 'temperature_deficit',
                'severity': 'medium',
                'confidence': 'high',
                'trigger': f'Indoor temp {indoor_temp}°C is {target_temp - indoor_temp:.1f}°C below target',
                'is_anomaly': True,
                'category': 'performance_issue'
            }

        # ANOMALY: Excessive power consumption
        expected_power = 3.0  # Typical for residential
        if power_kw > expected_power * 1.5:
            return {
                'pattern_type': 'high_power_consumption',
                'severity': 'medium',
                'confidence': 'medium',
                'trigger': f'Power usage {power_kw:.1f}kW exceeds typical range',
                'is_anomaly': True,
                'category': 'efficiency_concern'
            }

        # NORMAL: Tariff optimisation
        hour = int(scenario_data.get('timestamp', '2024-01-01T12:00:00')[11:13])
        if hour >= 0 and hour <= 5 and data.get('electricity_price_current', 0.15) < 0.12:
            return {
                'pattern_type': 'tariff_optimization',
                'severity': 'none',
                'confidence': 'high',
                'trigger': 'Operating during cheap-rate hours',
                'is_anomaly': False,
                'category': 'smart_behavior'
            }

        # NORMAL: VPP curtailment
        if data.get('vpp_signal') and indoor_temp < target_temp:
            return {
                'pattern_type': 'vpp_curtailment',
                'severity': 'none',
                'confidence': 'high',
                'trigger': 'Grid demand response active',
                'is_anomaly': False,
                'category': 'smart_behavior'
            }

        # NORMAL: Predictive pre-heating
        if data.get('weather_forecast_temp') and data['weather_forecast_temp'] < outdoor_temp - 5:
            return {
                'pattern_type': 'predictive_heating',
                'severity': 'none',
                'confidence': 'high',
                'trigger': 'Pre-heating before forecast cold snap',
                'is_anomaly': False,
                'category': 'smart_behavior'
            }

        # NORMAL: Cold weather operation
        if outdoor_temp < 0 and cop >= 2.0 and cop < 2.8:
            return {
                'pattern_type': 'cold_weather_operation',
                'severity': 'none',
                'confidence': 'high',
                'trigger': f'Normal efficiency for {outdoor_temp}°C weather',
                'is_anomaly': False,
                'category': 'normal_operation'
            }

        # Default: Normal operation
        return {
            'pattern_type': 'normal_operation',
            'severity': 'none',
            'confidence': 'medium',
            'trigger': 'Standard heating operation',
            'is_anomaly': False,
            'category': 'normal_operation'
        }

    # CRITERIA 2: EXPLAIN IN PLAIN LANGUAGE


    def generate_plain_language_explanation(
            self,
            scenario_data: Dict,
            pattern: Dict,
            benefits: Dict
    ) -> str:
        """
        Generate <50 word explanation in plain language using Claude
        """

        data = scenario_data['data']

        # Build context for Claude
        prompt = f"""You're explaining a heat pump's behaviour to a homeowner with no technical knowledge.

SITUATION:
- What happened: {pattern['pattern_type'].replace('_', ' ')}
- Indoor temperature: {data['indoor_temp']}°C (target: {data.get('target_temp', 20)}°C)
- Outdoor temperature: {data['outdoor_temp']}°C
- System efficiency: {data['cop']:.1f} (3+ is good, 2-3 is okay, <2 is concerning)
- Time: {scenario_data.get('timestamp', 'today')}

CONTEXT:
- Is this normal? {not pattern['is_anomaly']}
- Trigger: {pattern['trigger']}

BENEFITS (if applicable):
- Money saved: £{benefits.get('cost_savings', 0):.2f}
- Carbon avoided: {benefits.get('carbon_kg', 0):.1f}kg CO2

YOUR TASK:
Write ONE explanation in UNDER 50 WORDS that:
1. Explains WHY this happened in everyday language
2. Mentions the benefit if there is one (savings/carbon)
3. Is reassuring if normal, or flags if needs attention

RULES:
- NO technical jargon (don't say: COP, VPP, kWh, thermal mass, SPF, refrigerant)
- DO use everyday words (say: efficiency, heating schedule, electricity price, weather)
- Keep it conversational and friendly
- Be specific with numbers (e.g., "saved £1.20" not "saved money")

EXPLANATION (under 50 words):"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=120,
                messages=[{"role": "user", "content": prompt}]
            )

            explanation = response.content[0].text.strip()

            # Ensure it's under 50 words
            word_count = len(explanation.split())
            if word_count > 50:
                # Truncate and re-prompt if needed
                print(f"Warning: Explanation was {word_count} words, truncating...")
                explanation = ' '.join(explanation.split()[:50]) + '...'

            return explanation

        except Exception as e:
            # Fallback to template-based explanation
            print(f"Error calling Claude API: {e}")
            return self._fallback_explanation(pattern, data, benefits)

    def _fallback_explanation(self, pattern: Dict, data: Dict, benefits: Dict) -> str:
        """Fallback template-based explanations if API fails"""

        templates = {
            'tariff_optimization': f"Your smart tariff shifted heating to cheap-rate hours, saving you £{benefits.get('cost_savings', 1.2):.2f} today. The system ran efficiently despite {data['outdoor_temp']}°C outside.",

            'vpp_curtailment': f"The grid asked your heat pump to reduce during peak demand. Your house will reach {data.get('target_temp', 20)}°C by morning as usual. This helps prevent blackouts.",

            'predictive_heating': f"Your system is pre-heating before tonight's cold snap ({data.get('weather_forecast_temp', -8)}°C forecast). This uses less energy than playing catch-up later.",

            'cold_weather_operation': f"Your heat pump is using more electricity because outdoor temperature dropped to {data['outdoor_temp']}°C. This is normal winter behaviour - still cheaper than gas.",

            'efficiency_anomaly': f"Your system's efficiency ({data['cop']:.1f}) is lower than expected for {data['outdoor_temp']}°C weather. Consider checking your insulation or booking a service check."
        }

        return templates.get(pattern['pattern_type'], "Your heat pump is operating normally.")

    # ============================================
    # CRITERIA 3: PROVIDE ACTIONABLE GUIDANCE
    # ============================================

    def get_actionable_guidance(self, pattern: Dict, scenario_data: Dict) -> Dict[str, str]:
        """
        Provide clear actionable guidance based on pattern
        Three tiers: Normal / Check / Fault
        """

        data = scenario_data['data']

        guidance_map = {
            # NORMAL behaviours
            'tariff_optimization': {
                'status': ' This is normal winter behaviour',
                'action': 'No action needed',
                'detail': 'Your smart tariff is working as designed to minimize costs.',
                'confidence': 'Definitely normal',
                'tier': 'normal'
            },

            'vpp_curtailment': {
                'status': ' This is normal winter behaviour',
                'action': 'No action needed',
                'detail': 'Your system is helping balance the grid during peak demand. Temperature will recover automatically.',
                'confidence': 'Definitely normal',
                'tier': 'normal'
            },

            'predictive_heating': {
                'status': ' This is normal winter behaviour',
                'action': 'No action needed',
                'detail': 'Your system is optimizing for upcoming weather. This is more efficient than reactive heating.',
                'confidence': 'Definitely normal',
                'tier': 'normal'
            },

            'cold_weather_operation': {
                'status': ' This is normal winter behaviour',
                'action': 'No action needed',
                'detail': f'Heat pumps use more electricity in very cold weather ({data["outdoor_temp"]}°C), but remain cost-effective.',
                'confidence': 'Definitely normal',
                'tier': 'normal'
            },

            # CHECK INSULATION
            'temperature_deficit': {
                'status': ' Consider checking your insulation',
                'action': 'Check for drafts or poor insulation',
                'detail': f'Your home is struggling to maintain temperature. Improving insulation could help your heat pump work more efficiently.',
                'confidence': 'This might need attention',
                'tier': 'check'
            },

            'high_power_consumption': {
                'status': ' Consider checking your insulation',
                'action': 'Review insulation and radiator sizing',
                'detail': f'Power usage ({data["power_consumption_kw"]:.1f}kW) is higher than typical. Better insulation could reduce this.',
                'confidence': 'This might need attention',
                'tier': 'check'
            },

            # POTENTIAL FAULT
            'efficiency_anomaly': {
                'status': ' This might indicate a fault',
                'action': 'Book a service check with your installer',
                'detail': f'Efficiency ({data["cop"]:.1f}) is lower than expected for {data["outdoor_temp"]}°C. Could indicate refrigerant levels, sensor issues, or airflow problems.',
                'confidence': 'This might indicate a fault',
                'tier': 'fault'
            }
        }

        return guidance_map.get(
            pattern['pattern_type'],
            {
                'status': ' This is normal winter behaviour',
                'action': 'No action needed',
                'detail': 'Your heat pump is operating within expected parameters.',
                'confidence': 'Probably normal',
                'tier': 'normal'
            }
        )

    # ============================================
    # CRITERIA 4: BUILD TRUST THROUGH TRANSPARENCY
    # ============================================

    def build_transparency_data(
            self,
            scenario_data: Dict,
            pattern: Dict,
            benefits: Dict
    ) -> Dict[str, Any]:
        """
        Show all the data that led to the conclusion
        """

        data = scenario_data['data']
        profile = scenario_data.get('property_profile', {})

        return {
            'detection_details': {
                'Pattern Detected': pattern['pattern_type'].replace('_', ' ').title(),
                'Detection Confidence': pattern['confidence'].title(),
                'Is Anomaly?': 'Yes' if pattern['is_anomaly'] else 'No',
                'Trigger': pattern['trigger']
            },

            'measurements': {
                'Indoor Temperature': f"{data['indoor_temp']}°C",
                'Target Temperature': f"{data.get('target_temp', 20.0)}°C",
                'Temperature Gap': f"{data.get('target_temp', 20.0) - data['indoor_temp']:.1f}°C",
                'Outdoor Temperature': f"{data['outdoor_temp']}°C",
                'System Efficiency (COP)': f"{data['cop']:.1f}",
                'COP Interpretation': self._interpret_cop(data['cop']),
                'Power Consumption': f"{data['power_consumption_kw']:.1f} kW",
                'Flow Temperature': f"{data.get('flow_temp', 40)}°C",
            },

            'context': {
                'Timestamp': scenario_data.get('timestamp', 'Unknown'),
                'Electricity Price': f"£{data.get('electricity_price_current', 0.15):.2f}/kWh",
                'Peak Price': f"£{data.get('electricity_price_peak', 0.28):.2f}/kWh" if data.get(
                    'electricity_price_peak') else 'N/A',
                'Grid Signal': data.get('vpp_signal', 'None'),
                'Weather Forecast': f"{data.get('weather_forecast_temp')}°C" if data.get(
                    'weather_forecast_temp') else 'N/A'
            },

            'property_details': {
                'Property Type': profile.get('property_details', {}).get('house_type', 'Unknown'),
                'Heat Pump': f"{profile.get('heat_pump_specs', {}).get('brand', 'Unknown')} {profile.get('heat_pump_specs', {}).get('model', '')}",
                'Heat Pump Size': f"{profile.get('heat_pump_specs', {}).get('size_kw', 7.0)} kW",
                'Typical Annual Efficiency': f"{profile.get('performance_data', {}).get('annual_spf', 2.8):.2f}"
            },

            'calculated_benefits': {
                'Cost Savings Today': f"£{benefits.get('cost_savings', 0):.2f}",
                'Carbon Avoided': f"{benefits.get('carbon_kg', 0):.1f} kg CO2",
                'Equivalent to': f"{benefits.get('carbon_kg', 0) / 25:.1f} trees planted" if benefits.get('carbon_kg',
                                                                                                          0) > 0 else 'N/A'
            },

            'why_this_conclusion': self._explain_conclusion_logic(pattern, data)
        }

    def _interpret_cop(self, cop: float) -> str:
        """Human-readable COP interpretation"""
        if cop >= 3.5:
            return "Excellent efficiency"
        elif cop >= 3.0:
            return "Good efficiency"
        elif cop >= 2.5:
            return "Moderate efficiency"
        elif cop >= 2.0:
            return "Acceptable for cold weather"
        else:
            return "Lower than expected - may need attention"

    def _explain_conclusion_logic(self, pattern: Dict, data: Dict) -> str:
        """Explain how we reached this conclusion"""

        logic_map = {
            'tariff_optimization': f"Detected heating during off-peak hours (cheap electricity at £{data.get('electricity_price_current', 0.08):.2f}/kWh vs peak £{data.get('electricity_price_peak', 0.28):.2f}/kWh)",

            'vpp_curtailment': f"Grid signal '{data.get('vpp_signal')}' active with temperature {data['indoor_temp']}°C below target",

            'predictive_heating': f"Forecast shows temperature drop to {data.get('weather_forecast_temp')}°C, system pre-heating while current outdoor temp is {data['outdoor_temp']}°C",

            'cold_weather_operation': f"Outdoor temperature {data['outdoor_temp']}°C with COP {data['cop']:.1f} is within normal range for winter",

            'efficiency_anomaly': f"COP {data['cop']:.1f} is below expected range (2.5-3.5) for outdoor temperature {data['outdoor_temp']}°C"
        }

        return logic_map.get(pattern['pattern_type'], "Analysis of operational parameters suggests normal behaviour")

    # BENEFITS CALCULATION


    def calculate_benefits(self, scenario_data: Dict, pattern: Dict) -> Dict[str, float]:
        """Calculate quantified benefits"""

        data = scenario_data['data']

        # Tariff optimisation savings
        if pattern['pattern_type'] == 'tariff_optimization':
            peak_price = data.get('electricity_price_peak', 0.28)
            actual_price = data.get('electricity_price_current', 0.08)
            power_kw = data.get('power_consumption_kw', 2.0)
            hours = 3  # Typical cheap period duration

            cost_savings = (peak_price - actual_price) * power_kw * hours
            carbon_kg = 0.8  # Avoided carbon by using off-peak (lower grid carbon)

        # VPP curtailment savings (grid-level)
        elif pattern['pattern_type'] == 'vpp_curtailment':
            carbon_kg = 1.2  # Higher carbon intensity during peak
            cost_savings = 0.15  # Small compensation

        # Predictive heating savings
        elif pattern['pattern_type'] == 'predictive_heating':
            cost_savings = 0.85
            carbon_kg = 0.5

        else:
            cost_savings = 0.0
            carbon_kg = 0.0

        return {
            'cost_savings': round(cost_savings, 2),
            'carbon_kg': round(carbon_kg, 1)
        }

    # MAIN ANALYSIS FUNCTION


    def analyze_scenario(self, scenario_data: Dict) -> Dict[str, Any]:
        """
        Complete analysis addressing all 4 criteria
        """

        # 1. Detect pattern
        pattern = self.detect_pattern(scenario_data)

        # Calculate benefits
        benefits = self.calculate_benefits(scenario_data, pattern)

        # 2. Generate plain language explanation
        explanation = self.generate_plain_language_explanation(
            scenario_data, pattern, benefits
        )

        # 3. Get actionable guidance
        guidance = self.get_actionable_guidance(pattern, scenario_data)

        # 4. Build transparency data
        transparency = self.build_transparency_data(
            scenario_data, pattern, benefits
        )

        return {
            'scenario_name': scenario_data.get('name', 'Unknown Scenario'),
            'pattern_detection': pattern,
            'explanation': explanation,
            'word_count': len(explanation.split()),
            'actionable_guidance': guidance,
            'benefits': benefits,
            'transparency_data': transparency
        }


# Example usage
if __name__ == "__main__":
    # Load scenarios
    with open('/home/claude/scenarios_from_real_data.json', 'r') as f:
        data = json.load(f)

    # Test with first scenario (without API key for now)
    explainer = HeatPumpExplainer()

    scenario = data['scenarios'][0]

    print("\n=== TESTING HEAT PUMP EXPLAINER ===\n")
    print(f"Scenario: {scenario['name']}")
    print(f"Property: {scenario['property_profile']['property_id']}\n")

    # analyse without API (will use fallback explanations)
    result = explainer.analyze_scenario(scenario)

    print("1  PATTERN DETECTED:")
    print(f"   {result['pattern_detection']}\n")

    print("2  EXPLANATION ({result['word_count']} words):")
    print(f"   {result['explanation']}\n")

    print("3  ACTIONABLE GUIDANCE:")
    print(f"   Status: {result['actionable_guidance']['status']}")
    print(f"   Action: {result['actionable_guidance']['action']}\n")

    print("4  TRANSPARENCY DATA:")
    print(f"   {json.dumps(result['transparency_data']['detection_details'], indent=2)}\n")

    print(
        f" BENEFITS: £{result['benefits']['cost_savings']:.2f} saved, {result['benefits']['carbon_kg']:.1f}kg CO2 avoided")
