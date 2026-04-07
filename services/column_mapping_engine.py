import re
from typing import Dict, List, Optional, Tuple

import pandas as pd
from pandas import DataFrame, Series

NORMALIZE_PATTERN = re.compile(r"[^a-z0-9]+")


def normalize_name(value: str) -> str:
    return re.sub(NORMALIZE_PATTERN, "", value.lower())


def conversion_ratio(values: Series, converter) -> float:
    if values.empty:
        return 0.0
    converted = values.map(converter)
    valid = converted.notna().sum()
    return valid / len(values)


def compute_column_metrics(column: Series, total_rows: int) -> Dict[str, float]:
    non_null = column.dropna()
    non_null_ratio = len(non_null) / total_rows if total_rows else 0.0
    sample = non_null.astype(str)

    numeric_ratio = conversion_ratio(sample, pd.to_numeric)
    date_ratio = conversion_ratio(sample, pd.to_datetime)

    unique_values = non_null.nunique(dropna=True)
    uniqueness_score = unique_values / total_rows if total_rows else 0.0
    is_constant = unique_values <= 1

    return {
        "non_null_ratio": non_null_ratio,
        "uniqueness_score": round(uniqueness_score, 3),
        "numeric_ratio": numeric_ratio,
        "date_ratio": date_ratio,
        "is_constant": is_constant,
    }


def confidence_from_score(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"


def name_match_score(column: str, keywords: List[str]) -> float:
    normalized_column = normalize_name(column)
    if not normalized_column:
        return 0.0
    best = 0.0
    for keyword in keywords:
        normalized_keyword = normalize_name(keyword)
        if not normalized_keyword:
            continue
        if normalized_keyword in normalized_column:
            return 1.0
        if normalized_column.startswith(normalized_keyword[:3]):
            best = max(best, 0.5)
        if normalized_column.endswith(normalized_keyword[-3:]):
            best = max(best, 0.4)
    return best


def data_type_score(ks: Dict[str, float], expected: str) -> float:
    if expected == "numeric":
        return ks["numeric_ratio"]
    if expected == "date":
        return ks["date_ratio"]
    if expected == "id":
        return min(1.0, ks["uniqueness_score"] + 0.2)
    if expected in ("text", "category"):
        return 1.0 - ks["numeric_ratio"]
    return 0.4


def apply_negative_signals(expected: str, metrics: Dict[str, float]) -> Tuple[float, List[str]]:
    penalty = 0.0
    signals: List[str] = []
    if metrics["non_null_ratio"] < 0.2:
        penalty += 0.1
        signals.append("❌ high null ratio")
    if metrics["is_constant"]:
        penalty += 0.2
        signals.append("❌ constant values")
    if expected == "numeric" and metrics["numeric_ratio"] < 0.2:
        penalty += 0.15
        signals.append("❌ not numeric")
    if expected == "id" and metrics["uniqueness_score"] < 0.2:
        penalty += 0.15
        signals.append("❌ not ID")
    return penalty, signals


def calculate_score(
    column: str,
    metrics: Dict[str, float],
    expected_type: str,
    keywords: List[str],
) -> Tuple[float, List[str]]:
    name = name_match_score(column, keywords)
    data_type = data_type_score(metrics, expected_type)
    base_score = (
        0.4 * name
        + 0.3 * data_type
        + 0.2 * metrics["non_null_ratio"]
        + 0.1 * metrics["uniqueness_score"]
    )

    penalty, signals = apply_negative_signals(expected_type, metrics)
    final_score = max(0.0, base_score - penalty)
    return round(final_score, 4), signals


ROLE_DEFINITIONS = [
    {
        "id": "date",
        "keywords": [
            "date",
            "order_date",
            "transaction_date",
            "invoice_date",
            "timestamp",
            "datetime",
            "created_at",
            "sales_date",
        ],
        "expected": "date",
        "section": "Section_A",
    },
    {
        "id": "sales",
        "keywords": [
            "sales",
            "revenue",
            "amount",
            "total",
            "net_sales",
            "gross_sales",
            "sales_value",
            "order_value",
            "gmv",
            "booking_value",
        ],
        "expected": "numeric",
        "section": "Section_A",
    },
    {
        "id": "product_id",
        "keywords": ["sku", "product_id", "item_id", "product_code"],
        "expected": "id",
        "section": "Section_B",
    },
    {
        "id": "product_name",
        "keywords": ["product", "product_name", "item_name", "description"],
        "expected": "text",
        "section": "Section_B",
    },
    {
        "id": "category",
        "keywords": ["category", "product_category", "segment", "type"],
        "expected": "category",
        "section": "Section_B",
    },
    {
        "id": "store_id",
        "keywords": ["store", "store_id", "shop", "outlet", "branch"],
        "expected": "id",
        "section": "Section_C",
    },
    {
        "id": "store_name",
        "keywords": ["store_name", "store", "shop", "branch"],
        "expected": "text",
        "section": "Section_C",
    },
    {
        "id": "region",
        "keywords": ["region", "region_name"],
        "expected": "text",
        "section": "Section_C",
    },
    {
        "id": "city",
        "keywords": ["city", "town", "metro", "district"],
        "expected": "text",
        "section": "Section_C",
    },
    {
        "id": "state",
        "keywords": ["state", "province", "state_region", "state/region"],
        "expected": "text",
        "section": "Section_C",
    },
    {
        "id": "country",
        "keywords": ["country", "nation", "country_name"],
        "expected": "text",
        "section": "Section_C",
    },
    {
        "id": "area",
        "keywords": ["area", "zone", "territory"],
        "expected": "text",
        "section": "Section_C",
    },
    {
        "id": "salesperson",
        "keywords": ["salesperson", "sales_rep", "agent", "employee"],
        "expected": "text",
        "section": "Section_D",
    },
    {
        "id": "units",
        "keywords": ["units", "quantity", "qty", "volume", "items_sold", "units_sold"],
        "expected": "numeric",
        "section": "Section_D",
    },
    {
        "id": "unit_price",
        "keywords": ["unit_price", "price", "selling_price", "avg_price", "mrp"],
        "expected": "numeric",
        "section": "Section_D",
    },
]


def format_role_entry(entry: Optional[Dict]) -> Dict[str, Optional[str]]:
    if not entry:
        return {"column": None, "confidence": "low", "score": 0.0, "negative_signals": []}
    return {
        "column": entry["column"],
        "confidence": confidence_from_score(entry["score"]),
        "score": round(entry["score"], 3),
        "negative_signals": entry["negative_signals"],
        "role": entry["role"],
    }


def detect_column_roles(df: DataFrame) -> Dict[str, Dict]:
    result = {
        "Section_A": {},
        "Section_B": {},
        "Section_C": {},
        "Section_D": [],
    }

    if df.empty:
        return result

    total_rows = len(df)
    columns = list(df.columns)
    metrics_map = {
        column: compute_column_metrics(df[column], total_rows) for column in columns
    }

    best_matches: Dict[str, Optional[Dict]] = {
        role["id"]: None for role in ROLE_DEFINITIONS
    }

    for column in columns:
        metrics = metrics_map[column]
        for role in ROLE_DEFINITIONS:
            score, negatives = calculate_score(
                column, metrics, role["expected"], role["keywords"]
            )
            candidate = {
                "column": column,
                "score": score,
                "negative_signals": negatives,
                "role": role["id"],
                "section": role["section"],
            }
            current = best_matches[role["id"]]
            if not current or candidate["score"] > current["score"]:
                best_matches[role["id"]] = candidate

    assignment_map: Dict[str, List[str]] = {
        "Section_A": ["date", "sales"],
        "Section_B": ["product_id", "product_name", "category"],
        "Section_C": ["store_id", "store_name", "region", "city", "state", "country", "area"],
    }

    assigned_columns = set()
    for section, role_ids in assignment_map.items():
        for role_id in role_ids:
            entry = best_matches.get(role_id)
            formatted = format_role_entry(entry)
            if formatted["column"]:
                assigned_columns.add(formatted["column"])
            result[section][role_id] = formatted

    remaining = [col for col in columns if col not in assigned_columns]
    for column in remaining:
        metrics = metrics_map[column]
        best_extra: Optional[Dict] = None
        for role in ROLE_DEFINITIONS:
            if role["section"] != "Section_D":
                continue
            score, negatives = calculate_score(
                column, metrics, role["expected"], role["keywords"]
            )
            candidate = {
                "column": column,
                "score": score,
                "confidence": confidence_from_score(score),
                "suggested_role": role["id"],
                "negative_signals": negatives,
            }
            if not best_extra or candidate["score"] > best_extra["score"]:
                best_extra = candidate

        result["Section_D"].append(
            {
                "column": column,
                "confidence": best_extra["confidence"] if best_extra else "low",
                "score": round(best_extra["score"], 3) if best_extra else 0.0,
                "suggested_role": best_extra["suggested_role"]
                if best_extra
                else None,
                "negative_signals": best_extra["negative_signals"]
                if best_extra
                else [],
            }
        )

    return result
