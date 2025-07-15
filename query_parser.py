import json

def extract_filters(client, query: str) -> dict:
    prompt = f"""
You are a filter-extraction assistant for car data queries.

Extract a valid lowercase JSON object from this user query.
Supported filters:
- brand, name, color, city, body_type
- min_price, max_price
- min_year, max_year
- min_mileage, max_mileage
- cylinders
- cylinder_size_liters

Values may be strings, numbers, or arrays if multiple choices apply.

Example:
User: "Show me red Toyotas or Kias in Riyadh or Abha under 200K with less than 100,000 km"
JSON:
{{
  "brand": ["toyota", "kia"],
  "color": "red",
  "city": ["riyadh", "abha"],
  "max_price": 200000,
  "max_mileage": 100000
}}

Now extract filters from:
"{query}"

Return JSON only:
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=200,
        )
        text = response.choices[0].message.content.strip()
        return json.loads(text[text.find("{"):text.rfind("}") + 1])
    except Exception as e:
        return {"__error__": str(e)}