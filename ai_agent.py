from typing import Dict, Any

class SupplyChainAgent:
    @staticmethod
    def route(intent: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if intent == "inventory_advisor":
            on_hand = int(payload.get("on_hand", 0))
            safety = int(payload.get("safety_stock", max(int(payload.get("optimal_stock", 100) * 0.2), 20)))
            optimal = int(payload.get("optimal_stock", max(on_hand, 100)))
            status = "OK"
            rec = "Optimal"
            if on_hand < safety:
                status = "CRITICAL"
                rec = "Replenish immediately"
            elif on_hand < int(safety * 1.2):
                status = "LOW"
                rec = "Plan reorder soon"
            return {
                "status": status,
                "recommendation": rec,
                "target_optimal": optimal,
                "target_safety": safety
            }
        if intent == "procurement_negotiator":
            supplier = payload.get("supplier_name", "Supplier")
            product = payload.get("product_name", "Material")
            price = float(payload.get("unit_price", 0.0))
            qty = int(payload.get("quantity", 0))
            return {
                "email_subject": f"Partnership terms for {product}",
                "email_body": f"Hello {supplier}, we propose {qty} units at {price:.2f} per unit with improved terms based on reliability and volume."
            }
        if intent == "logistics_planner":
            start = payload.get("start_address")
            end = payload.get("end_address")
            if not start or not end:
                return {"error": "Missing addresses"}
            return {
                "plan": f"Route from {start} to {end}",
                "risk": "LOW"
            }
        return {"error": "Unknown intent"}
