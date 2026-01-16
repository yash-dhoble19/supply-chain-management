# backend/ai_insight_service.py - ENHANCED EXECUTIVE VERSION
# ---------------------------------------------------------------

import google.generativeai as genai
from config import (
    settings, 
    get_festivals_for_month,
    get_safety_stock_percentage,
    estimate_promotion_impact_range
)
from typing import Optional
import pandas as pd

genai.configure(api_key=settings.gemini_api_key)


def _build_executive_context(
    category: str,
    forecasted_units: int,
    mom_change: float,
    trend: str,
    month: str,
    lower_bound: int,
    upper_bound: int,
    historical_avg: float,
    yoy_change: float,
    confidence: str,
    coefficient_of_variation: float,
    region: str
) -> str:
    """Build concise, executive-ready context."""
    
    # Calculate meaningful metrics
    range_width_pct = ((upper_bound - lower_bound) / forecasted_units * 100) if forecasted_units > 0 else 0
    vs_historical = ((forecasted_units - historical_avg) / historical_avg * 100) if historical_avg else None
    
    context = f"""FORECAST SNAPSHOT
Product Category: {category}
Target Month: {month}
Point Forecast: {forecasted_units:,} units
Confidence Range: {lower_bound:,} - {upper_bound:,} units (±{range_width_pct:.0f}%)
Confidence Level: {confidence}
Trend Direction: {trend} ({mom_change:+.1f}% MoM)"""

    if yoy_change is not None:
        context += f"\nYear-over-Year: {yoy_change:+.1f}%"
    
    if vs_historical is not None:
        context += f"\nvs. Historical Avg: {vs_historical:+.1f}% ({historical_avg:,.0f} units)"
    
    context += f"\nDemand Volatility (CV): {coefficient_of_variation:.1f}%"
    context += f"\nMarket: {region}"
    
    return context


def _structure_demand_drivers(external_factors: dict, seasonality: dict, festivals: list) -> dict:
    """Organize demand drivers with clear causal reasoning."""
    
    drivers = {
        "promotional": [],
        "seasonal": [],
        "market": [],
        "risks": []
    }
    
    if not external_factors:
        external_factors = {}
    
    # Promotional drivers
    if external_factors.get("upcoming_promotion"):
        uplift_range = estimate_promotion_impact_range()
        drivers["promotional"].append({
            "factor": "Planned promotional campaign",
            "impact": f"{uplift_range['min']}-{uplift_range['max']}% demand uplift",
            "mechanism": "Price promotions historically convert price-sensitive shoppers and accelerate purchase timing"
        })
    
    if external_factors.get("marketing_campaign"):
        drivers["promotional"].append({
            "factor": "Active marketing initiatives",
            "impact": "10-20% awareness expansion",
            "mechanism": "Marketing increases consideration set entry among target demographics"
        })
    
    # Price elasticity
    if external_factors.get("price_change") == "Increase":
        drivers["risks"].append({
            "factor": "Planned price increase",
            "impact": f"~{int(settings.price_elasticity_moderate*100)}% volume reduction per 10% price rise",
            "mechanism": "Category shows moderate price sensitivity - premium alternatives may gain share"
        })
    elif external_factors.get("price_change") == "Decrease":
        drivers["market"].append({
            "factor": "Competitive price repositioning",
            "impact": f"~{int(settings.price_elasticity_moderate*100)}% volume gain per 10% price reduction",
            "mechanism": "Lower prices improve value perception and attract switchers from competitors"
        })
    
    # Product launch dynamics
    if external_factors.get("new_product_launch"):
        drivers["market"].append({
            "factor": "New SKU introduction",
            "impact": "15-30% portfolio interaction effect",
            "mechanism": "New products can cannibalize existing SKUs or expand total category wallet share"
        })
    
    # Seasonal/festival factors
    if festivals and len(festivals) > 0:
        festival_names = [f.split('(')[0].strip() for f in festivals[:2]]
        holiday_strength = seasonality.get("holiday_impact_strength", 0) if seasonality else 0
        
        if len(festival_names) == 1:
            festival_desc = festival_names[0]
        else:
            festival_desc = f"{festival_names[0]} and {festival_names[1]}"
        
        drivers["seasonal"].append({
            "factor": f"{festival_desc} alignment",
            "impact": f"~{holiday_strength:.0f}% festival premium" if holiday_strength > 5 else "Moderate consumption spike",
            "mechanism": f"Cultural celebrations in {external_factors.get('region', 'the region')} drive gift purchasing and household restocking"
        })
    
    # Broader seasonality
    if seasonality:
        yearly_strength = seasonality.get("yearly_seasonality_strength", 0)
        if yearly_strength > settings.strong_seasonality_threshold:
            drivers["seasonal"].append({
                "factor": "Strong seasonal pattern",
                "impact": f"{yearly_strength:.0f}% of demand variance explained by season",
                "mechanism": "Category exhibits pronounced calendar-driven consumption cycles"
            })
    
    # Supply chain risks
    if external_factors.get("supply_chain_disruption"):
        drivers["risks"].append({
            "factor": "Supply chain constraints",
            "impact": "Fulfillment ceiling below demand potential",
            "mechanism": "Logistics bottlenecks may cap actual sales regardless of consumer demand"
        })
    
    if external_factors.get("availability_issues"):
        drivers["risks"].append({
            "factor": "Inventory availability gaps",
            "impact": "10-15% lost sales exposure",
            "mechanism": "Stockouts lead to immediate substitution toward available alternatives"
        })
    
    # Economic headwinds
    if external_factors.get("economic_uncertainty") and external_factors["economic_uncertainty"] != "None":
        severity = external_factors["economic_uncertainty"]
        drivers["risks"].append({
            "factor": f"{severity} economic uncertainty",
            "impact": "5-15% demand volatility increase",
            "mechanism": "Consumer spending becomes more conservative and less predictable under economic stress"
        })
    
    if external_factors.get("regulatory_changes"):
        drivers["risks"].append({
            "factor": "Pending regulatory shifts",
            "impact": "Compliance-driven demand redirection",
            "mechanism": "Regulatory changes can restrict product categories or shift demand to compliant alternatives"
        })
    
    return drivers


def generate_ai_insight(
    category: str,
    forecasted_units: int,
    mom_change: float,
    trend: str,
    month: str,
    lower_bound: int = None,
    upper_bound: int = None,
    historical_avg: float = None,
    yoy_change: float = None,
    data_months: int = None,
    confidence: str = None,
    region: str = "India",
    festivals: list[str] | None = None,
    seasonality: dict = None,
    warnings: list[str] = None,
    coefficient_of_variation: float = None,
    external_factors: dict = None,
    country: str = None
) -> str:
    """
    Generate executive-grade business insight with causal reasoning.
    
    DESIGN PRINCIPLES:
    - Credible confidence ranges (realistic uncertainty)
    - Clear cause-and-effect explanations  
    - Reconcile contradictions (e.g., festivals + declining demand)
    - Justified inventory recommendations
    - Consulting-grade writing quality
    """
    
    if country is None:
        country = settings.default_country

    # Get festivals if not provided
    if festivals is None:
        month_name = month.split()[0] if " " in month else month
        festivals = get_festivals_for_month(month_name, country)
    
    # Build comprehensive data context for Gemini to interpret
    prompt = f"""You are a senior supply chain strategist. Analyze the following forecast data and provide an executive business insight.

=== FORECAST DATA ===
Product Category: {category}
Forecast Period: {month}
Forecasted Units: {forecasted_units:,}
Month-over-Month Change: {mom_change:+.1f}%
Trend: {trend}
Confidence Level: {confidence}
Confidence Range: {lower_bound:,} to {upper_bound:,} units
Historical Average: {historical_avg:,.0f} units (based on {data_months} months)
Demand Volatility (CV): {coefficient_of_variation:.1f}%"""

    if yoy_change is not None:
        prompt += f"\nYear-over-Year Change: {yoy_change:+.1f}%"
    
    prompt += f"\nRegion: {region}"
    
    # Add seasonality information if available
    if seasonality:
        prompt += f"""

=== SEASONAL PATTERNS ===
Yearly Seasonality Strength: {seasonality.get('yearly_seasonality_strength', 0):.1f}%
Holiday Impact Strength: {seasonality.get('holiday_impact_strength', 0):.1f}%
Pattern Detected: {seasonality.get('interpretation', 'No significant patterns')}"""

    # Add festivals if present
    if festivals and len(festivals) > 0:
        prompt += f"""

=== UPCOMING FESTIVALS/EVENTS ==="""
        for festival in festivals[:4]:
            prompt += f"\n- {festival}"
    
    # Add external factors context
    if external_factors and any(external_factors.values()):
        prompt += """

=== EXTERNAL FACTORS (User-Provided Context) ==="""
        
        factor_count = 0
        if external_factors.get("upcoming_promotion"):
            prompt += "\n- Upcoming Promotion: YES (promotional campaign planned)"
            factor_count += 1
        
        if external_factors.get("marketing_campaign"):
            prompt += "\n- Marketing Campaign: YES (active marketing initiatives)"
            factor_count += 1
        
        if external_factors.get("new_product_launch"):
            prompt += "\n- New Product Launch: YES (new SKU introduction expected)"
            factor_count += 1
        
        if external_factors.get("price_change") and external_factors.get("price_change") != "Same":
            prompt += f"\n- Price Change: {external_factors.get('price_change')} (pricing adjustment planned)"
            factor_count += 1
        
        if external_factors.get("availability_issues"):
            prompt += "\n- Availability Issues: YES (inventory/stock constraints expected)"
            factor_count += 1
        
        if external_factors.get("supply_chain_disruption"):
            prompt += "\n- Supply Chain Disruption: YES (sourcing/logistics risks)"
            factor_count += 1
        
        if external_factors.get("regulatory_changes"):
            prompt += "\n- Regulatory Changes: YES (compliance changes expected)"
            factor_count += 1
        
        if external_factors.get("logistics_constraints"):
            prompt += "\n- Logistics Constraints: YES (transportation/delivery constraints)"
            factor_count += 1
        
        if external_factors.get("economic_uncertainty") and external_factors.get("economic_uncertainty") != "None":
            prompt += f"\n- Economic Uncertainty: {external_factors.get('economic_uncertainty')} (market volatility level)"
            factor_count += 1
    
    # Add data quality warnings if any
    if warnings and len(warnings) > 0:
        prompt += """

=== DATA QUALITY NOTES ==="""
        for warning in warnings:
            clean_warning = warning.replace("⚠️ ", "").replace("❌ ", "")
            prompt += f"\n- {clean_warning}"
    
    # Calculate inventory buffer and justification
    has_risks = external_factors and (
        external_factors.get("supply_chain_disruption") or 
        external_factors.get("availability_issues") or
        external_factors.get("logistics_constraints")
    )
    safety_pct = get_safety_stock_percentage(coefficient_of_variation, has_risks)
    base_buffer = settings.base_safety_buffer_pct
    total_buffer = base_buffer + safety_pct
    target_inventory = int(forecasted_units * (1 + total_buffer))
    
    # Build justification for buffer
    buffer_justification = []
    if coefficient_of_variation > settings.high_cv_threshold:
        buffer_justification.append(f"high demand variability (CV {coefficient_of_variation:.1f}%)")
    if has_risks:
        buffer_justification.append("identified supply/market risks")
    if festivals:
        buffer_justification.append("festival-driven demand surges")
    if not buffer_justification:
        buffer_justification.append("standard forecast uncertainty")
    
    justification_text = " and ".join(buffer_justification)
    
    prompt += f"""

=== INVENTORY PLANNING ===
Recommended Target: {target_inventory:,} units
Buffer Percentage: {int(total_buffer * 100)}% above forecast
Festival Lead Time: {settings.festival_preparation_weeks} weeks before peak events

=====================================

Based on ALL the data above, write a professional executive insight with these sections:

**PARAGRAPH 1 - Current Situation & Forecast Interpretation (3-4 sentences)**
Start by clearly stating what the forecast shows. Explain the trend direction and what the numbers mean. If there are festivals but demand is declining (or vice versa), explain this apparent contradiction naturally. When discussing confidence: if the range is very narrow (like {lower_bound:,} to {upper_bound:,}), explain this indicates high model certainty based on stable historical patterns. If the range is wide, discuss the uncertainty factors.

**PARAGRAPH 2 - Key Drivers & Influencing Factors (4-5 sentences)**
Analyze which factors are influencing this forecast and HOW they work. Connect the external factors, seasonal patterns, and festivals to the forecast outcome. Explain cause-and-effect relationships. If multiple factors are present, explain how they interact or which ones dominate. IMPORTANT: If "New Product Launch" is mentioned in external factors, discuss both potential positive (category expansion) AND negative (cannibalization) effects.

**PARAGRAPH 3 - Risks & Considerations (2-4 sentences)**
Discuss ANY significant considerations that could impact outcomes. This includes:
- External risks (supply chain, availability, economic uncertainty)
- Product launch risks (cannibalization vs. category growth)
- Demand variability concerns (if CV is high)
- Data limitations (if historical data is limited)
Skip this paragraph ONLY if there are truly no risks or considerations to discuss.

**PARAGRAPH 4 - Inventory & Action Recommendations (3-4 sentences)**
Recommend the {target_inventory:,} unit target and explain why this buffer is appropriate given the specific factors present. If festivals exist, mention timing (e.g., "{settings.festival_preparation_weeks} weeks before [festival name]"). End with a monitoring recommendation that's specific to the risks identified.

WRITING GUIDELINES:
- Write in natural, professional business language
- Be conversational but authoritative
- Each sentence should add new insight
- Total length: 200-300 words
- Use actual data from above - don't make up facts
- Be honest about uncertainty where it exists
- Focus on actionable insights
- Ensure all 4 paragraphs are present unless risks truly don't exist

Write the insight now:"""

    try:
        model = genai.GenerativeModel(settings.gemini_model)
        
        # Generate content with increased timeout via generation config
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.6,  # Higher for more natural, interpretive language
                max_output_tokens=800,  # More room for natural expression
            )
        )
        
        insight = response.text.strip()
        
        # Add context footer only if significant factors exist
        context_items = []
        if festivals:
            context_items.append(f"Festivals: {', '.join([f.split('(')[0].strip() for f in festivals[:2]])}")
        if external_factors:
            active_factors = []
            if external_factors.get("upcoming_promotion"):
                active_factors.append("Promotion")
            if external_factors.get("supply_chain_disruption") or external_factors.get("availability_issues"):
                active_factors.append("Supply Risk")
            if external_factors.get("new_product_launch"):
                active_factors.append("New Launch")
            if external_factors.get("economic_uncertainty") and external_factors.get("economic_uncertainty") != "None":
                active_factors.append(f"{external_factors.get('economic_uncertainty')} Economic Uncertainty")
            if active_factors:
                context_items.append(f"Factors: {', '.join(active_factors[:3])}")
        
        if context_items:
            insight += f"\n\n**Context:** {' | '.join(context_items)}"
        
        return insight
    
    except Exception as e:
        # Log the error for debugging
        import traceback
        print(f"⚠️ Gemini API Error: {str(e)}")
        print(traceback.format_exc())
        print("📝 Using fallback insight generation (high-quality alternative)...")
        
        return _generate_fallback_insight(
            category, forecasted_units, mom_change, trend, month,
            lower_bound, upper_bound, historical_avg, yoy_change,
            data_months, confidence, region, festivals, seasonality,
            warnings, coefficient_of_variation, external_factors,
            target_inventory, total_buffer, justification_text
        )


def _generate_fallback_insight(
    category: str,
    forecasted_units: int,
    mom_change: float,
    trend: str,
    month: str,
    lower_bound: int,
    upper_bound: int,
    historical_avg: float,
    yoy_change: float,
    data_months: int,
    confidence: str,
    region: str,
    festivals: list,
    seasonality: dict,
    warnings: list,
    coefficient_of_variation: float,
    external_factors: dict,
    target_inventory: int,
    total_buffer: float,
    justification_text: str
) -> str:
    """Generate comprehensive fallback insight when Gemini API fails."""
    
    # === PARAGRAPH 1: Current Situation & Forecast ===
    change_text = f"up {abs(mom_change):.1f}%" if mom_change > 0 else f"down {abs(mom_change):.1f}%"
    insight = f"The forecast for {category} in {month} shows demand at {forecasted_units:,} units, {change_text} from the previous month. "
    
    # Explain the trend with context
    if festivals and mom_change < -3:
        festival_name = festivals[0].split('(')[0].strip()
        insight += f"While {festival_name} typically drives short-term demand increases in {region}, the overall market trend indicates {trend.lower()} momentum, suggesting broader market factors are outweighing seasonal effects. "
    elif festivals and mom_change > 5:
        festival_name = festivals[0].split('(')[0].strip()
        insight += f"The upward trend aligns with {festival_name}, which historically boosts {category} sales in {region} through increased gifting and household purchases. "
    elif mom_change > 5:
        insight += f"This {trend.lower()} trajectory suggests strengthening market demand for {category}. "
    elif mom_change < -5:
        insight += f"This {trend.lower()} movement indicates softening demand conditions in the {category} category. "
    else:
        insight += f"Demand remains relatively stable with {trend.lower()} momentum. "
    
    # Confidence statement
    range_pct = ((upper_bound - lower_bound) / forecasted_units * 100) if forecasted_units > 0 else 0
    if range_pct < 1:
        insight += f"With {data_months} months of historical data, the forecast carries {confidence.lower()} confidence. The narrow range ({lower_bound:,} to {upper_bound:,} units, ±{range_pct:.0f}%) indicates high model certainty based on stable historical patterns.\n\n"
    else:
        insight += f"With {data_months} months of historical data, the forecast carries {confidence.lower()} confidence with a range of {lower_bound:,} to {upper_bound:,} units (±{range_pct:.0f}%), reflecting inherent demand variability.\n\n"
    
    # === PARAGRAPH 2: Key Drivers & Influencing Factors ===
    key_factors = []
    
    # Festivals
    if festivals and len(festivals) > 0:
        festival_list = ', '.join([f.split('(')[0].strip() for f in festivals[:2]])
        key_factors.append(f"upcoming festivals ({festival_list}) drive cultural purchasing behavior")
    
    # Seasonal patterns
    if seasonality and seasonality.get("yearly_seasonality_strength", 0) > 20:
        key_factors.append(f"strong seasonal patterns contribute {seasonality['yearly_seasonality_strength']:.0f}% of demand variance")
    
    # External factors - positive drivers
    if external_factors:
        if external_factors.get("upcoming_promotion"):
            key_factors.append("planned promotional activities expected to boost demand through price incentives")
        
        if external_factors.get("marketing_campaign"):
            key_factors.append("active marketing initiatives expanding brand awareness")
        
        if external_factors.get("price_change") == "Decrease":
            key_factors.append("price reduction strategy may attract price-sensitive customers")
    
    if key_factors:
        insight += "Several factors influence this forecast: " + "; ".join(key_factors[:4]) + ". "
    else:
        insight += "This forecast is based on historical demand patterns and current market trends. "
    
    # New product launch specific analysis
    if external_factors and external_factors.get("new_product_launch"):
        insight += "The planned new product launch adds complexity—new SKUs typically attract fresh customer segments and can expand the overall category, but they may also cannibalize sales from existing products depending on positioning and price points. "
    
    insight += "\n\n"
    
    # === PARAGRAPH 3: Risks & Considerations ===
    risk_factors = []
    
    if external_factors:
        if external_factors.get("new_product_launch"):
            risk_factors.append("**The key risk is product portfolio management.** If the new launch targets the same customer segment as existing SKUs, it could shift sales rather than grow total demand. Launching during a festival period requires careful inventory planning for both new and existing products.")
        
        if external_factors.get("supply_chain_disruption"):
            risk_factors.append("Supply chain constraints may cap actual sales below forecasted demand even if customer interest remains strong.")
        
        if external_factors.get("availability_issues"):
            risk_factors.append("Inventory availability gaps could lead to stockouts during peak demand, driving customers to competitors.")
        
        if external_factors.get("logistics_constraints"):
            risk_factors.append("Logistics constraints may delay product availability, particularly critical during time-sensitive festival periods.")
        
        if external_factors.get("price_change") == "Increase":
            risk_factors.append("The planned price increase may reduce volume as price-sensitive customers seek alternatives.")
        
        if external_factors.get("economic_uncertainty") and external_factors.get("economic_uncertainty") != "None":
            severity = external_factors.get("economic_uncertainty")
            risk_factors.append(f"{severity} economic uncertainty increases demand volatility and makes consumer spending less predictable.")
    
    # Demand variability risk
    if coefficient_of_variation > 40:
        risk_factors.append(f"High demand volatility (CV: {coefficient_of_variation:.1f}%) creates additional forecast uncertainty.")
    
    # Data limitation risk
    if data_months < 12:
        risk_factors.append(f"Limited historical data ({data_months} months) constrains the model's ability to capture seasonal patterns reliably.")
    
    if risk_factors:
        insight += " ".join(risk_factors[:3]) + "\n\n"
    
    # === PARAGRAPH 4: Inventory & Action Recommendations ===
    insight += f"Recommended inventory target is {target_inventory:,} units, which includes a {int(total_buffer * 100)}% buffer above the base forecast to account for {justification_text}. "
    
    if festivals:
        festival_name = festivals[0].split('(')[0].strip()
        insight += f"Position this inventory at least {settings.festival_preparation_weeks} weeks before {festival_name} to ensure availability during peak demand. "
    
    # Specific monitoring based on risks
    if external_factors and external_factors.get("new_product_launch"):
        insight += "Implement weekly sales monitoring by SKU to track whether the new launch is expanding or cannibalizing the category, and adjust future procurement accordingly."
    elif risk_factors:
        insight += "Implement weekly sales monitoring to track actual performance against forecast and enable rapid inventory adjustments in response to demand signals."
    else:
        insight += "Monitor weekly sell-through to validate forecast accuracy and adjust replenishment as needed."
    
    # === Context Footer ===
    context_items = []
    if festivals:
        context_items.append(f"Festivals: {festivals[0].split('(')[0].strip()}")
    
    if external_factors:
        active_factors = []
        if external_factors.get("upcoming_promotion"):
            active_factors.append("Promotion")
        if external_factors.get("new_product_launch"):
            active_factors.append("New Launch")
        if external_factors.get("supply_chain_disruption") or external_factors.get("availability_issues"):
            active_factors.append("Supply Risk")
        if external_factors.get("economic_uncertainty") and external_factors.get("economic_uncertainty") != "None":
            active_factors.append(f"{external_factors.get('economic_uncertainty')} Econ Uncertainty")
        if active_factors:
            context_items.append(f"Factors: {', '.join(active_factors[:3])}")
    
    if context_items:
        insight += f"\n\n**Context:** {' | '.join(context_items)}"
    
    return insight


def generate_inventory_recommendation(
    category: str,
    forecasted_units: int,
    current_stock: int = None,
    lead_time_days: int = None,
    safety_stock_days: int = 7,
    seasonality_strength: float = 0,
    has_external_risks: bool = False,
    coefficient_of_variation: float = 0
) -> str:
    """Generate executive inventory recommendations."""
    
    daily_forecast = forecasted_units / 30
    safety_pct = get_safety_stock_percentage(coefficient_of_variation, has_external_risks)
    base_buffer = settings.base_safety_buffer_pct
    total_buffer = base_buffer + safety_pct
    safety_stock = daily_forecast * safety_stock_days
    
    if seasonality_strength > settings.strong_seasonality_threshold:
        safety_stock *= 1.5
        seasonality_note = f"Strong seasonality warrants {int(safety_stock)} units buffer"
    elif seasonality_strength > settings.moderate_seasonality_threshold:
        safety_stock *= 1.2
        seasonality_note = f"Moderate seasonal variance requires {int(safety_stock)} units safety stock"
    else:
        seasonality_note = f"Stable demand pattern supports {int(safety_stock)} units baseline buffer"
    
    context = f"""Category: {category}
Monthly Forecast: {forecasted_units:,} units
Daily Run Rate: {daily_forecast:.1f} units
Safety Stock: {int(safety_stock)} units ({int(safety_pct * 100)}%)
{seasonality_note}"""
    
    if current_stock is not None:
        days_coverage = current_stock / daily_forecast if daily_forecast > 0 else 0
        context += f"\nCurrent Inventory: {current_stock:,} units ({days_coverage:.1f} days coverage)"
    
    if lead_time_days is not None:
        reorder_point = daily_forecast * (lead_time_days + safety_stock_days)
        context += f"\nSupplier Lead Time: {lead_time_days} days\nReorder Trigger: {int(reorder_point)} units"

    prompt = f"""You are an inventory strategist. Based on this data:

{context}

Write 2-3 sentences that:
1. State whether immediate reorder is needed (if current stock provided)
2. Recommend specific order quantity with clear reasoning
3. Reference the seasonality consideration

Be direct and quantitative."""

    try:
        model = genai.GenerativeModel(settings.gemini_model)
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=200,
            )
        )
        return response.text.strip()
    except Exception:
        if current_stock and lead_time_days:
            days_remaining = current_stock / daily_forecast if daily_forecast > 0 else 0
            reorder_point = int(daily_forecast * (lead_time_days + safety_stock_days))
            
            if days_remaining < lead_time_days:
                order_qty = int(forecasted_units * 1.5)
                return f"⚠️ Immediate reorder required - only {days_remaining:.0f} days coverage remaining (below {lead_time_days}-day lead time threshold). Place order for {order_qty:,} units to cover forecast plus {int(total_buffer * 100)}% safety buffer. {seasonality_note}."
            else:
                return f"Current stock provides {days_remaining:.0f} days coverage. Schedule reorder when inventory drops to {reorder_point:,} units (lead time + safety stock threshold). {seasonality_note}."
        else:
            target = int(forecasted_units * (1 + safety_pct))
            return f"Target inventory: {target:,} units ({forecasted_units:,} forecast + {int(safety_pct * 100)}% buffer). {seasonality_note}. Coordinate with suppliers on lead time expectations."
