# Basic COCOMO Constants
# (Mode, a, b, c, d)
COCOMO_PARAMS = {
    "organic": (2.4, 1.05, 2.5, 0.38),
    "semi-detached": (3.0, 1.12, 2.5, 0.35),
    "embedded": (3.6, 1.20, 2.5, 0.32),
}

def calculate_cocomo(kloc, mode="semi-detached"):
    """
    Calculates effort (Person-Months) and development time (Months) using Basic COCOMO.
    
    Args:
        kloc (float): Kilo Lines of Code.
        mode (str): Project mode ('organic', 'semi-detached', 'embedded').
    
    Returns:
        tuple: (effort_pm, duration_m) or (None, None) if invalid mode.
    """
    if kloc <= 0:
        return 0, 0 
        
    if mode not in COCOMO_PARAMS:
        print(f"Invalid COCOMO mode: {mode}")
        return None, None 

    a, b, c, d = COCOMO_PARAMS[mode]

    effort_pm = a * (kloc ** b)
    duration_m = c * (effort_pm ** d)

    return round(effort_pm, 2), round(duration_m, 2)

def calculate_cost(roles_info, duration_months, contingency_percentage=10):
    """
    Calculates total project cost based on roles, their rates, and project duration.
    
    Args:
        roles_info (list of dicts): e.g., [{"role_name": "Developer", "count": 2, "rate_ph": 50}, ...]
                                     Rate is per hour. Assumes 160 hours per month per person.
        duration_months (float): Project duration in months from COCOMO.
        contingency_percentage (float): Percentage for contingency buffer.
    
    Returns:
        tuple: (total_cost_without_contingency, total_cost_with_contingency, cost_breakdown_details)
    """
    if duration_months <= 0: 
        return 0, 0, {}

    total_cost_sub = 0 
    cost_breakdown = {}
    
    hours_per_month_person = 160 

    for role_item in roles_info:
        role_name = role_item.get("role_name", "Unknown Role") 
        count = int(role_item.get("count", 0))
        rate_per_hour = float(role_item.get("rate_ph", 0.0))

        if count > 0 and rate_per_hour > 0:
            monthly_cost_per_person = rate_per_hour * hours_per_month_person
            total_role_cost_for_duration = monthly_cost_per_person * count * duration_months
            
            cost_breakdown[role_name] = {
                "count": count,
                "rate_ph": rate_per_hour,
                "monthly_cost_per_person": round(monthly_cost_per_person, 2),
                "total_role_cost": round(total_role_cost_for_duration, 2)
            }
            total_cost_sub += total_role_cost_for_duration
        elif count > 0 and role_name not in cost_breakdown : 
             cost_breakdown[role_name] = {
                "count": count,
                "rate_ph": rate_per_hour,
                "monthly_cost_per_person": 0.00,
                "total_role_cost": 0.00
            }

    contingency_amount = (total_cost_sub * contingency_percentage) / 100
    total_with_contingency = total_cost_sub + contingency_amount
    
    if contingency_percentage > 0 or contingency_amount > 0 : 
        cost_breakdown["Contingency"] = {
            "count": f"{contingency_percentage}%",
            "rate_ph": "-", 
            "monthly_cost_per_person": "-", 
            "total_role_cost": round(contingency_amount, 2)
        }
    
    return round(total_cost_sub, 2), round(total_with_contingency, 2), cost_breakdown