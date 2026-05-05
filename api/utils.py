import hashlib
import json
import re

def parse_query_to_filters(q):
    q = q.lower()
    filters = {}

    if re.search(r"\b(women|woman|female|females)\b", q):
        filters["gender"] = "female"
    elif re.search(r"\b(men|man|male|males)\b", q):
        filters["gender"] = "male"

    if "young" in q:
        filters["min_age"] = 18
        filters["max_age"] = 35

    age_range = re.search(r"(\d+)\s*(?:-|to|and)\s*(\d+)", q)
    if age_range:
        filters["min_age"] = int(age_range.group(1))
        filters["max_age"] = int(age_range.group(2))

    if "nigeria" in q or "nigerian" in q or "ng" in q:
        filters["country_id"] = "NG"

    return filters

def normalize_filters(filters):
    normalized = {}

    if filters.get("gender"):
        gender = filters["gender"].lower()
        if gender in ["women", "woman", "female", "females"]:
            gender = "female"
        elif gender in ["men", "man", "male", "males"]:
            gender = "male"
        normalized["gender"] = gender

    if filters.get("country_id"):
        normalized["country_id"] = filters["country_id"].upper()

    if filters.get("age_group"):
        normalized["age_group"] = filters["age_group"].lower()

    for field in ["min_age", "max_age", "min_gender_probability", "min_country_probability"]:
        if filters.get(field) is not None:
            normalized[field] = filters[field]

    normalized["sort_by"] = filters.get("sort_by", "created_at")
    normalized["order"] = filters.get("order", "asc")
    normalized["page"] = int(filters.get("page", 1))
    normalized["limit"] = int(filters.get("limit", 10))

    return dict(sorted(normalized.items()))


def make_cache_key(prefix, filters):
    normalized = normalize_filters(filters)
    raw = json.dumps(normalized, sort_keys=True)
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return f"{prefix}:{hashed}"