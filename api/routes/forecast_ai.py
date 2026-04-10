"""
Forecast AI Analysis — /forecast-ai/*
Groq-powered generative demand explanation endpoint.
Accepts forecast summary + historical data and returns a rich,
LLM-generated narrative about the product demand, patterns, and factors.
"""
import traceback
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.ai_service import _call_groq
from services.weather_service import get_weather_forecast

router = APIRouter(prefix="/forecast-ai", tags=["Forecast AI"])


class ForecastAIRequest(BaseModel):
    """Payload from the frontend after a forecast is generated."""
    demandType: str = "Unknown"
    trend: str = "stable"
    confidence: str = "Medium"
    forecastTotal: float = 0
    avgDailyDemand: float = 0
    minForecast: float = 0
    maxForecast: float = 0
    dataPointsUsed: int = 0
    appliedFestivalDays: int = 0
    modelName: str = "Prophet (Adaptive)"
    # Optional historical summary stats
    historicalMean: float = 0
    historicalStdDev: float = 0
    historicalMin: float = 0
    historicalMax: float = 0
    forecastDurationDays: int = 15
    # Raw series (optional, last 60 values max for context)
    recentHistory: list[float] = []
    # Selected location context
    location: str = "India"
    # External signals from Twitter/Weather/etc.
    externalContext: str = ""


@router.post("/explain")
async def explain_forecast(req: ForecastAIRequest):
    """
    Generate a rich, generative AI explanation of the demand forecast.
    Uses Groq (Llama 3.3 70B) to provide:
    - Product demand narrative
    - Pattern analysis (trend, seasonality, volatility)
    - Factors affecting demand
    - Actionable recommendations
    """
    try:
        # Build a rich context prompt for the LLM
        cv = (req.historicalStdDev / req.historicalMean * 100) if req.historicalMean > 0 else 0

        recent_str = ""
        if req.recentHistory:
            # Show last 30 values as a compact series
            last_30 = req.recentHistory[-30:]
            recent_str = f"\nRecent daily values (last {len(last_30)} days): {', '.join([str(round(v, 1)) for v in last_30])}"
        
        forecast_daily_avg = req.forecastTotal / max(1, req.forecastDurationDays)
        pct_change = ((forecast_daily_avg / req.historicalMean) - 1) * 100 if req.historicalMean > 0 else 0
        direction = "increase" if pct_change >= 0 else "decrease"
        
        prompt = f"""You are a senior demand planning analyst. Analyze the following demand forecast results.

=== FORECAST DATA ===
Model: {req.modelName}
Classification: {req.demandType}
Trend: {req.trend}
Confidence: {req.confidence}
Forecast Total: {req.forecastTotal:,.0f} units
Average Daily Forecast: {req.avgDailyDemand:,.1f} units
Historical Mean: {req.historicalMean:,.1f} units
Percentage Change vs History: {pct_change:+.1f}% ({direction})
Volatility (CV): {cv:.1f}%
Weather: {get_weather_forecast(req.location)}
External Signals: {req.externalContext}

=== YOUR ANALYSIS MUST FOLLOW THIS EXACT FORMAT WITH EMOJIS ===

🔍 Demand Summary  
Forecasted demand is **{req.forecastTotal:,.0f} units**, showing a **{pct_change:+.1f}% {direction}** vs historical average. [Add 1 sentence on health/volume].

📈 Key Trend  
Demand is on a **{req.trend} trajectory**, characterized as **{req.demandType}** demand. [Explain what this means for planning].

⚠️ Risk Factors  
• [Risk 1 based on {req.confidence} confidence and {cv:.1f}% volatility]
• [Risk 2 based on logistics or data quality]

🌐 External Signals  
• [Signal 1: Extract insights from: {req.externalContext}]
• [Signal 2: Analyze weather impact: {get_weather_forecast(req.location)}]

🎯 Actionable Recommendation  
Increase/Adjust inventory to **~{req.forecastTotal * 1.3:,.0f} units (+30% safety buffer)** to avoid stockouts. [Add 1 specific logistics tip].

IMPORTANT:
- Use the emojis shown above exactly.
- Keep total response under 300 words.
- Use bold text for key metrics.
"""

        system_msg = """You are an expert supply chain and demand planning analyst. 
        IMPORTANT: Only mention weather impact if the product is weather-sensitive (e.g., ACs, heaters, umbrellas, beverages, apparel). 
        Do NOT mention weather for consumer electronics like smartphones, headphones, or laptops unless there is a logically strong link (like major storms causing shipping delays).
        Always reference specific numbers from the data and use the required emoji-based format.
        """

        response = _call_groq([
            {
                "role": "system",
                "content": system_msg
            },
            {"role": "user", "content": prompt}
        ])

        if response and response.choices:
            analysis = response.choices[0].message.content
            return {
                "status": "success",
                "analysis": analysis,
                "model": "Groq (Llama 3.3 70B)",
            }
        else:
            return {
                "status": "fallback",
                "analysis": _generate_fallback_analysis(req, cv),
                "model": "Deterministic Fallback",
            }

    except Exception as e:
        traceback.print_exc()
        # Return fallback instead of erroring out
        cv = (req.historicalStdDev / req.historicalMean * 100) if req.historicalMean > 0 else 0
        return {
            "status": "fallback",
            "analysis": _generate_fallback_analysis(req, cv),
            "model": "Deterministic Fallback",
            "error": str(e),
        }


def _generate_fallback_analysis(req: ForecastAIRequest, cv: float) -> str:
    """Deterministic fallback when Groq is unavailable."""

    forecast_daily_avg = req.forecastTotal / max(1, req.forecastDurationDays)
    pct_change = ((forecast_daily_avg / req.historicalMean) - 1) * 100 if req.historicalMean > 0 else 0
    direction = "increase" if pct_change >= 0 else "decrease"
    
    analysis = f"""🔍 Demand Summary  
Forecasted demand is **{req.forecastTotal:,.0f} units**, showing a **{pct_change:+.1f}% {direction}** vs historical average of {req.historicalMean:,.1f}.

📈 Key Trend  
Demand is on a **{req.trend} trajectory**, characterized as **{req.demandType}** demand. [Historical volatility: {cv:.1f}%].

⚠️ Risk Factors  
• Forecast confidence is **{req.confidence}** based on {req.dataPointsUsed} days of history.
• {"High volatility detected (CV > 50%) warrants safety stock." if cv > 50 else "Moderate variability in demand signals detected."}

🌐 External Signals  
• Twitter and market interest signals indicate **{req.trend} momentum**.
• Weather impact: {get_weather_forecast(req.location)}.

🎯 Actionable Recommendation  
Increase inventory to **~{req.forecastTotal * 1.3:,.0f} units (+30% buffer)** to ensure availability during the {req.forecastDurationDays}-day horizon.
"""
    return analysis
