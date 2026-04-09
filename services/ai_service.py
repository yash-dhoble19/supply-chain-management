"""
Groq AI service — wraps all LLM calls behind a clean interface.
All AI calls in the system should go through this module.
"""
import json
import os
import re
from openai import OpenAI
import openai
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

_client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
) if GROQ_API_KEY else None


def _call_groq(messages, response_format=None, model="llama-3.3-70b-versatile"):
    """Internal helper — single point for all Groq LLM calls."""
    if not _client:
        return None
    kwargs = {"model": model, "messages": messages}
    if response_format:
        kwargs["response_format"] = response_format
    return _client.chat.completions.create(**kwargs)


# ── Public AI Functions ──────────────────────────────────────────────


def analyze_order_risk(address: str) -> str:
    try:
        response = _call_groq([
            {"role": "system", "content": "Risk Manager. Mark HIGH/LOW RISK."},
            {"role": "user", "content": address},
        ])
        return response.choices[0].message.content if response else "AI unavailable"
    except openai.RateLimitError:
        return "AI Rate Limit Reached. Please try again later."
    except Exception:
        return "AI Error"




def analyze_pricing(product_name: str, current_price: float, stock_ratio: float):
    """AI pricing analysis — could be replaced with deterministic logic."""
    prompt = f"""
    You are a Strategic Pricing Algorithm.
    DATA:
    - Product: {product_name}
    - Current Price: ${current_price}
    - Stock Ratio: {stock_ratio:.2f}
    RULES:
    1. IF Ratio > 1.5: LOWER price
    2. IF Ratio < 0.3: RAISE price
    3. ELSE: HOLD price
    OUTPUT JSON:
    {{"new_price": float, "action": "RAISE/LOWER/HOLD", "reason": "string", "confidence": 95}}
    """
    try:
        response = _call_groq(
            [{"role": "system", "content": "Output strict JSON."}, {"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content) if response else _pricing_fallback(current_price)
    except openai.RateLimitError:
        return _pricing_fallback(current_price)
    except Exception as e:
        raise RuntimeError(f"AI Pricing Failed: {e}")


def _pricing_fallback(current_price: float):
    return {"new_price": current_price, "action": "HOLD", "reason": "AI currently unavailable.", "confidence": 0}


def audit_inventory(products_summary: list[dict]) -> str:
    data = "\n".join([f"- {p['product']}: Stock {p['on_hand']}/{p['optimal_stock']}" for p in products_summary])
    prompt = f"Supply Chain CFO Audit. Inventory: {data}\nWrite Strategic Report (Markdown): Executive Summary, Risks, Recommendations."
    try:
        response = _call_groq([{"role": "user", "content": prompt}])
        return response.choices[0].message.content if response else "AI unavailable."
    except openai.RateLimitError:
        return "AI Rate Limit Reached. Strategic audit is temporarily unavailable."
    except Exception as e:
        raise RuntimeError(f"Audit Failed: {e}")


def simulate_scenario(scenario: str, products_context: str):
    prompt = f'Risk Analyst. Inventory: {products_context}. Scenario: "{scenario}"\nOutput JSON: impact_score, impact_summary, affected_products, recommendation.'
    try:
        response = _call_groq(
            [{"role": "system", "content": "JSON only."}, {"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content) if response else _simulation_fallback()
    except openai.RateLimitError:
        return _simulation_fallback()
    except Exception as e:
        raise RuntimeError(str(e))


def _simulation_fallback():
    return {
        "impact_score": 50,
        "impact_summary": "AI unavailable. Simulation could not be completed.",
        "affected_products": [],
        "recommendation": "Monitor inventory levels manually.",
    }


def draft_negotiation_email(product_name: str, supplier_name: str, current_stock: int, optimal_stock: int, unit_price: float):
    needed = max(0, optimal_stock - current_stock)
    cost = round(needed * unit_price, 2)
    prompt = f"""
    Write a professional procurement email to {supplier_name}.
    Product: {product_name}. Need: {needed} units at ${unit_price}/unit.
    Total: ${cost}. Tone: professional but urgent.
    Request: best pricing, delivery timeline, and volume discount.
    """
    try:
        response = _call_groq([
            {"role": "system", "content": "Professional Procurement Manager writing a supplier email."},
            {"role": "user", "content": prompt},
        ])
        email_body = response.choices[0].message.content if response else "AI unavailable."
        return {"email": email_body, "recommended_qty": needed, "estimated_cost": cost}
    except openai.RateLimitError:
        return {"email": "AI Rate Limit. Please draft manually.", "recommended_qty": needed, "estimated_cost": cost}
    except Exception as e:
        raise RuntimeError(f"AI Email Failed: {e}")


def generate_supplier_email(supplier, recent_pos_count: int, total_volume: float):
    prompt = f"""
    Write a professional procurement negotiation email.
    Supplier: {supplier.name} ({supplier.contact_email}), Category: {supplier.category}
    Reliability: {supplier.reliability_score}/100, Delivery: {supplier.delivery_speed_days} days
    Price: ${supplier.price_per_unit}/unit
    Our record: {recent_pos_count} POs, ${total_volume:,.2f} total volume.
    Goals: volume discounts, faster delivery, quarterly business review.
    Tone: Professional, collaborative.
    """
    try:
        response = _call_groq([
            {"role": "system", "content": "Professional procurement manager writing strategic supplier emails."},
            {"role": "user", "content": prompt},
        ])
        return response.choices[0].message.content if response else "AI unavailable."
    except openai.RateLimitError:
        return "AI Rate Limit. Please draft manually."
    except Exception as e:
        raise RuntimeError(f"AI Email Generation Failed: {e}")


def analyze_route_risk(route_description: str, distance_km: float, duration_min: float) -> str:
    prompt = f"""
    Route: {route_description}. Distance: {distance_km} km. Duration: {duration_min} mins.
    Analyze logistics risks (traffic, road conditions, weather, safety). Keep concise.
    """
    try:
        response = _call_groq([
            {"role": "system", "content": "Risk Manager. Mark HIGH/LOW RISK."},
            {"role": "user", "content": prompt},
        ])
        return response.choices[0].message.content if response else "AI unavailable"
    except Exception:
        return "AI Error"


def parse_product_info(description: str) -> dict:
    """AI-powered product info extraction, with local regex fallback."""
    prompt = f"""
    Extract product details from: "{description}"
    Output JSON:
    {{"name": "...", "category": "...", "stage": "...", "current_stock": 0, "unit_price": 0.0, "optimal_stock_level": 0, "safety_stock_level": 0}}
    """
    try:
        if not GROQ_API_KEY:
            return parse_product_info_local(description)
        response = _call_groq(
            [{"role": "system", "content": "Output JSON only."}, {"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content) if response else parse_product_info_local(description)
    except Exception:
        return parse_product_info_local(description)


def parse_product_info_local(description: str) -> dict:
    """Deterministic regex fallback for product info extraction."""
    text = description.lower()

    name = description.strip()
    name = re.sub(r"^(?i)(add|create|insert|new|please|make)\s+", "", name)
    name = re.sub(r"\s+per\s+unit.*$", "", name, flags=re.IGNORECASE)

    category = "Raw Material"
    if any(k in text for k in ["finished", "final", "complete"]):
        category = "Finished Good"
    elif "packaging" in text:
        category = "Packaging"
    elif any(k in text for k in ["component", "part", "assembly"]):
        category = "Component"

    stock = 0
    stock_match = re.search(r"(\d+)\s*(?:stock|qty|quantity|units|pcs|sheets|items|pieces|boxes)", text)
    if stock_match:
        stock = int(stock_match.group(1))
    else:
        numbers = re.findall(r"\b\d+\b", text)
        if numbers:
            stock = int(numbers[0])

    price = 0.1
    for pattern in [
        r"(?:rs\.?|inr|\$)\s*([0-9]+(?:\.[0-9]+)?)",
        r"([0-9]+(?:\.[0-9]+)?)\s*(?:dollars?|bucks?|usd)",
        r"([0-9]+(?:\.[0-9]+)?)\s*per\s*unit",
        r"(?:price|cost)[:\s]*([0-9]+(?:\.[0-9]+)?)",
    ]:
        m = re.search(pattern, text)
        if m:
            price = float(m.group(1))
            break

    optimal = int(max(stock if stock > 0 else 100, round((stock if stock > 0 else 100) * 1.2)))
    safety = int(round(optimal * 0.2))

    return {
        "name": name,
        "category": category,
        "stage": category,
        "current_stock": stock,
        "unit_price": price,
        "optimal_stock_level": optimal,
        "safety_stock_level": safety,
    }

# anything
