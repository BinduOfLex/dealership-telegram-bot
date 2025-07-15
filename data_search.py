from collections import Counter
from itertools import product

def normalize(value):
    return str(value).strip().lower()

def value_matches(entry, key, val):
    if key not in entry: return False
    return normalize(entry[key]) == normalize(val)

def car_matches(car, filters):
    if "min_price" in filters and car.get("price", 0) < filters["min_price"]: return False
    if "max_price" in filters and car.get("price", 0) > filters["max_price"]: return False
    if "min_year" in filters and car.get("year", 0) < filters["min_year"]: return False
    if "max_year" in filters and car.get("year", 0) > filters["max_year"]: return False
    if "min_mileage" in filters and car.get("mileage", 0) < filters["min_mileage"]: return False
    if "max_mileage" in filters and car.get("mileage", 0) > filters["max_mileage"]: return False
    if "cylinders" in filters and car.get("cylinders", 0) != filters["cylinders"]: return False
    if "cylinder_size_liters" in filters and car.get("cylinder_size_liters", 0) != filters["cylinder_size_liters"]: return False
    return True

def search_and_summarize(filters, data, client, user_query):
    fields = ["brand", "name", "color", "city", "body_type"]
    filter_values = {}

    for field in fields:
        if field in filters:
            val = filters[field]
            filter_values[field] = val if isinstance(val, list) else [val]

    fallback_attempts = list(product(*(filter_values.get(f, [None]) for f in fields)))
    results = []
    attempt_index = 0

    for attempt in fallback_attempts:
        trial = dict(zip(fields, attempt))
        matches = [
            car for car in data
            if car_matches(car, filters)
            and all(value_matches(car, f, trial[f]) for f in trial if trial[f])
        ]
        if matches:
            results = matches
            break
        attempt_index += 1

    summary = "\n".join(
        f"🚗 {car['year']} {car['brand']} {car['name']} — {car['color']} in {car['city']}\n"
        f"🛞 {car['body_type']} | {car['cylinders']} cyl | {car['cylinder_size_liters']}L | {int(car['mileage']):,} km\n"
        f"💰 {car['price']:,.0f} SAR"
        for car in results[:30]
    ) or "No matching cars found."

    prompt = f"""
You're a helpful car assistant.

User query: "{user_query}"
Total matches: {len(results)}
Fallback level used: {attempt_index if attempt_index > 0 else 'Primary filters'}

---
{summary}
---

Reply clearly and mention fallback logic if used. Be conversational and concise.
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=400,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"GPT error: {e}"

def get_insights(data, field):
    valid = [item[field] for item in data if field in item]
    return Counter(valid).most_common()