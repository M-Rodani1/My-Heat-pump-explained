"""
Extract representative property profiles from EoH dataset to ground synthetic scenarios in reality
"""

import pandas as pd
import json
from datetime import datetime

def extract_property_profiles(csv_path, num_properties=5):
    """
    Extract diverse property profiles from the EoH dataset
    """
    df = pd.read_csv(csv_path)
    
    # Filter to properties with complete data
    complete_df = df[df['Included_SPF_analysis'] == True].copy()
    
    profiles = []
    
    # 1. Standard ASHP - Good performer
    ashp_good = complete_df[
        (complete_df['HP_Installed'] == 'ASHP') & 
        (complete_df['SPFH2_selected_window'] > 3.0)
    ].iloc[0] if len(complete_df[complete_df['HP_Installed'] == 'ASHP']) > 0 else None
    
    if ashp_good is not None:
        profiles.append(create_profile(ashp_good, "High Efficiency ASHP"))
    
    # 2. Standard ASHP - Average performer
    ashp_avg = complete_df[
        (complete_df['HP_Installed'] == 'ASHP') & 
        (complete_df['SPFH2_selected_window'] >= 2.5) &
        (complete_df['SPFH2_selected_window'] <= 3.0)
    ].iloc[0] if len(complete_df[complete_df['HP_Installed'] == 'ASHP']) > 0 else None
    
    if ashp_avg is not None:
        profiles.append(create_profile(ashp_avg, "Average ASHP"))
    
    # 3. High Temperature ASHP
    ht_ashp = complete_df[
        complete_df['HP_Installed'] == 'HT_ASHP'
    ].iloc[0] if len(complete_df[complete_df['HP_Installed'] == 'HT_ASHP']) > 0 else None
    
    if ht_ashp is not None:
        profiles.append(create_profile(ht_ashp, "High Temperature ASHP"))
    
    # 4. Hybrid system
    hybrid = complete_df[
        complete_df['HP_Installed'] == 'Hybrid'
    ].iloc[0] if len(complete_df[complete_df['HP_Installed'] == 'Hybrid']) > 0 else None
    
    if hybrid is not None:
        profiles.append(create_profile(hybrid, "Hybrid Heat Pump"))
    
    # 5. Ground Source (if available)
    gshp = complete_df[
        complete_df['HP_Installed'] == 'GSHP'
    ].iloc[0] if len(complete_df[complete_df['HP_Installed'] == 'GSHP']) > 0 else None
    
    if gshp is not None:
        profiles.append(create_profile(gshp, "Ground Source Heat Pump"))
    
    return profiles

def create_profile(row, description):
    """
    Create a detailed property profile from a dataframe row
    """
    return {
        "profile_name": description,
        "property_id": row['Property_ID'],
        "property_details": {
            "house_type": row['House_Form'],
            "house_age": row['House_Age'],
            "postcode_area": row['Postcode'][:4] if pd.notna(row['Postcode']) else "UK",
        },
        "heat_pump_specs": {
            "type": row['HP_Installed'],
            "brand": row['HP_Brand'],
            "model": row['HP_Model'],
            "size_kw": float(row['HP_Size_kW']) if pd.notna(row['HP_Size_kW']) else 7.0,
            "refrigerant": row['HP_Refrigerant'] if pd.notna(row['HP_Refrigerant']) else "Unknown"
        },
        "performance_data": {
            "annual_spf": float(row['SPFH2_selected_window']) if pd.notna(row['SPFH2_selected_window']) else 2.8,
            "typical_cop_range": [
                float(row['SPFH2_selected_window']) - 0.5 if pd.notna(row['SPFH2_selected_window']) else 2.3,
                float(row['SPFH2_selected_window']) + 0.5 if pd.notna(row['SPFH2_selected_window']) else 3.3
            ],
            "mean_flow_temp": float(row['Mean_annual_SH_flow_temp_selected_window']) if pd.notna(row['Mean_annual_SH_flow_temp_selected_window']) else 40.0,
            "winter_flow_temp": float(row['Winter_mean_SH_flow_temp_selected_window']) if pd.notna(row['Winter_mean_SH_flow_temp_selected_window']) else 42.0,
            "coldest_day_cop": float(row['Coldest_day_COPH4']) if pd.notna(row['Coldest_day_COPH4']) else 2.0,
            "coldest_day_outdoor_temp": float(row['Coldest_day_External_Air_Temp_mean']) if pd.notna(row['Coldest_day_External_Air_Temp_mean']) else -5.0
        },
        "energy_consumption": {
            "annual_system_kwh": float(row['Whole_System_Energy_Consumed_selected_window']) if pd.notna(row['Whole_System_Energy_Consumed_selected_window']) else 3000.0,
            "annual_heat_output_kwh": float(row['HP_Energy_Output_selected_window']) if pd.notna(row['HP_Energy_Output_selected_window']) else 8000.0
        }
    }

def generate_scenarios_from_profile(profile):
    """
    Generate realistic operational scenarios based on property profile
    """
    scenarios = []
    
    # Scenario 1: Tariff Optimization (Night heating)
    scenarios.append({
        "id": f"{profile['property_id']}_tariff_opt",
        "name": "Early Morning Heating on Cheap Tariff",
        "property_profile": profile,
        "timestamp": "2024-01-15T02:30:00",
        "event_type": "tariff_optimization",
        "data": {
            "indoor_temp": 19.2,
            "target_temp": 20.0,
            "outdoor_temp": -3.0,
            "heat_pump_status": "heating",
            "power_consumption_kw": profile['heat_pump_specs']['size_kw'] * 0.3,
            "cop": profile['performance_data']['annual_spf'] - 0.2,  # Slightly lower at night
            "flow_temp": profile['performance_data']['winter_flow_temp'],
            "electricity_price_current": 0.08,
            "electricity_price_peak": 0.28,
            "grid_carbon_intensity": 150,
            "vpp_signal": None,
            "mode": "heating"
        }
    })
    
    # Scenario 2: VPP Demand Response
    scenarios.append({
        "id": f"{profile['property_id']}_vpp",
        "name": "Grid Demand Response (Peak Period)",
        "property_profile": profile,
        "timestamp": "2024-01-15T18:15:00",
        "event_type": "vpp_curtailment",
        "data": {
            "indoor_temp": 19.1,
            "target_temp": 20.0,
            "outdoor_temp": 4.0,
            "heat_pump_status": "reduced",
            "power_consumption_kw": profile['heat_pump_specs']['size_kw'] * 0.15,
            "cop": profile['performance_data']['annual_spf'] + 0.3,  # Better when less stressed
            "flow_temp": profile['performance_data']['mean_flow_temp'],
            "electricity_price_current": 0.32,
            "grid_carbon_intensity": 420,
            "vpp_signal": "reduce_50%",
            "mode": "heating"
        }
    })
    
    # Scenario 3: Coldest Day Performance
    scenarios.append({
        "id": f"{profile['property_id']}_cold_day",
        "name": "Cold Weather Performance",
        "property_profile": profile,
        "timestamp": "2024-01-20T08:00:00",
        "event_type": "normal_winter_behavior",
        "data": {
            "indoor_temp": 19.8,
            "target_temp": 20.0,
            "outdoor_temp": profile['performance_data']['coldest_day_outdoor_temp'],
            "heat_pump_status": "heating",
            "power_consumption_kw": profile['heat_pump_specs']['size_kw'] * 0.5,
            "cop": profile['performance_data']['coldest_day_cop'],
            "flow_temp": profile['performance_data']['winter_flow_temp'] + 2,
            "electricity_price_current": 0.15,
            "mode": "heating"
        }
    })
    
    # Scenario 4: Predictive Pre-heating
    scenarios.append({
        "id": f"{profile['property_id']}_predictive",
        "name": "Pre-heating Before Cold Snap",
        "property_profile": profile,
        "timestamp": "2024-01-16T14:00:00",
        "event_type": "predictive_heating",
        "data": {
            "indoor_temp": 21.2,
            "target_temp": 20.0,
            "outdoor_temp": 2.0,
            "heat_pump_status": "heating",
            "power_consumption_kw": profile['heat_pump_specs']['size_kw'] * 0.3,
            "cop": profile['performance_data']['annual_spf'] + 0.5,
            "flow_temp": profile['performance_data']['mean_flow_temp'],
            "weather_forecast_temp": -8.0,
            "forecast_time": "tonight 22:00",
            "mode": "heating"
        }
    })
    
    # Scenario 5: Potential Issue (Low COP)
    scenarios.append({
        "id": f"{profile['property_id']}_low_cop",
        "name": "Lower Than Expected Efficiency",
        "property_profile": profile,
        "timestamp": "2024-01-22T10:30:00",
        "event_type": "potential_fault",
        "data": {
            "indoor_temp": 18.5,
            "target_temp": 20.0,
            "outdoor_temp": 3.0,
            "heat_pump_status": "heating",
            "power_consumption_kw": profile['heat_pump_specs']['size_kw'] * 0.45,
            "cop": max(1.4, profile['performance_data']['annual_spf'] - 1.5),  # Significantly low
            "flow_temp": profile['performance_data']['mean_flow_temp'] + 5,
            "return_temp": profile['performance_data']['mean_flow_temp'],
            "electricity_price_current": 0.15,
            "mode": "heating"
        }
    })
    
    return scenarios

if __name__ == "__main__":
    # Extract profiles
    profiles = extract_property_profiles('/mnt/user-data/uploads/EoH_Dataset_CSV.csv')
    
    print(f"\n=== EXTRACTED {len(profiles)} PROPERTY PROFILES ===\n")
    
    all_scenarios = []
    
    for profile in profiles:
        print(f"Profile: {profile['profile_name']}")
        print(f"  Property: {profile['property_id']}")
        print(f"  Type: {profile['property_details']['house_type']}, {profile['property_details']['house_age']}")
        print(f"  Heat Pump: {profile['heat_pump_specs']['brand']} {profile['heat_pump_specs']['model']} ({profile['heat_pump_specs']['size_kw']}kW)")
        print(f"  Annual SPF: {profile['performance_data']['annual_spf']:.2f}")
        print(f"  Coldest Day COP: {profile['performance_data']['coldest_day_cop']:.2f} at {profile['performance_data']['coldest_day_outdoor_temp']:.1f}Â°C")
        print()
        
        # Generate scenarios for this profile
        scenarios = generate_scenarios_from_profile(profile)
        all_scenarios.extend(scenarios)
    
    # Save to JSON
    output = {
        "profiles": profiles,
        "scenarios": all_scenarios,
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "source": "EoH Dataset CSV",
            "total_properties": len(profiles),
            "total_scenarios": len(all_scenarios)
        }
    }
    
    with open('/home/claude/scenarios_from_real_data.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n Generated {len(all_scenarios)} scenarios from {len(profiles)} real properties")
    print(f" Saved to: scenarios_from_real_data.json")
