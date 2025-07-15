from collections import Counter
from statistics import mean

# 🔹 Count frequency by field
def count_by_field(data, field):
    values = [entry[field] for entry in data if field in entry and entry[field] is not None]
    return Counter(values).most_common()

# 🔹 Count by field within specific city
def count_by_field_in_city(data, field, city_name):
    filtered = [entry for entry in data if entry.get("city", "").lower() == city_name.lower()]
    return count_by_field(filtered, field)

# 🔹 Count multiple fields
def count_fields_summary(data, fields):
    return {field: count_by_field(data, field) for field in fields}

# 🔹 Min / Max value for any numeric field
def extreme_value(data, field, mode="min", filters={}):
    filtered = [
        entry for entry in data
        if all(entry.get(k) == v for k, v in filters.items())
        and field in entry and isinstance(entry[field], (int, float))
    ]
    if not filtered:
        return None
    return min(filtered, key=lambda x: x[field]) if mode == "min" else max(filtered, key=lambda x: x[field])

# 🔹 Average value for any numeric field
def average_value(data, field, filters={}):
    filtered_values = [
        entry[field] for entry in data
        if all(entry.get(k) == v for k, v in filters.items())
        and field in entry and isinstance(entry[field], (int, float))
    ]
    return mean(filtered_values) if filtered_values else None

# 🔹 Utility: cars within a price bracket
def cars_in_price_range(data, min_price, max_price, filters={}):
    return [
        entry for entry in data
        if min_price <= entry.get("price", 0) <= max_price
        and all(entry.get(k) == v for k, v in filters.items())
    ]