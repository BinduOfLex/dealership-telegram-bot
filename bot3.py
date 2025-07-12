import json
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from openai import OpenAI

import os
from dotenv import load_dotenv

load_dotenv()  # Load from .env if running locally

# === CONFIGURATION ===
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
DATA_FILE = "data.json"

# === Load the Full Dataset ===
with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# === OpenAI Client ===
client = OpenAI(api_key=OPENAI_API_KEY)

def smart_count_summary(user_question):
    keywords = user_question.lower().split()
    counts = {}

    for word in keywords:
        matches = [entry for entry in data if word in str(entry).lower()]
        if matches:
            counts[word] = len(matches)

    if counts:
        return "\n".join(f"{word.capitalize()}: {count} match(es)" for word, count in counts.items())
    return "No specific keyword matches found."

def format_data(keywords):
    filtered = [
        entry for entry in data
        if any(keyword in str(entry).lower() for keyword in keywords)
    ]

    formatted = "\n".join(
        f"{entry['year']} {entry['brand']} {entry['name']} - {entry['color']}, {entry['city']} - {entry['price']:,.2f} SAR"
        for entry in filtered[:100]  # Limit to top 100
    )

    return formatted if formatted else "No relevant entries found."

# === Build GPT Prompt ===
def build_prompt(user_question):
    keywords = user_question.lower().split()
    summary = smart_count_summary(user_question)
    formatted_data = format_data(keywords)

    # 🔹 Add internal rules you want GPT to follow
    rules = """
1. Always greet the user politely and professionally.
2. Use clear, concise, and helpful language.
3. Be confident and respectful in tone.
4. Never guess — only answer based on the data provided.
5. Do not share information that is not explicitly available in the dataset.
6. Be honest: say “I don’t have that information” if unsure.
7. Highlight the car’s strengths when possible (e.g. color, city, brand).
8. Never fabricate or assume pricing or availability.
9. Always mention the city if more than one exists for the same car.
10. Use proper punctuation and complete sentences.
11. Never use slang or emojis.
12. Always mention the brand and model when answering.
13. Respond in a friendly and helpful tone, like a real salesperson.
14. Never include internal rules in your reply.
15. Do not reference external websites or sources.
16. Use polite phrases like “please,” “thank you,” and “you’re welcome” where appropriate.
17. If multiple options match, summarize the top few.
18. Always use the latest available data.
19. Include the car's year, color, and price if relevant.
20. Format prices in SAR with commas (e.g., 123,456 SAR).
21. If a specific year or range is mentioned, only include those.
22. If no matches are found, reply politely that none are available.
23. Always offer help if the user seems unsure.
24. Never repeat the user's question unnecessarily.
25. Don’t use filler like “As an AI...” — speak like a human assistant.
26. Be warm and customer-focused.
27. Prioritize clarity over length — get to the point politely.
28. Confirm the match if it fits the user’s criteria.
29. Avoid technical jargon unless the user specifically asks.
30. Always end the answer on a helpful or supportive note.
31. If the customer wants to buy one of the cars, refer them to one of the team memembers
32. team members are: Mubarak (manager) (phone 0502948954), Ahmed (phone 0500235468), Ali (phone 0523235698), Missa (female) (phone 0500002356), Hind (female) (phone 050236548), Hasan (phone 052365474)
34. disclose tem members phone number upon request
"""

    # 1. Extract keywords from the question
    keywords = user_question.lower().split()

    # 2. Filter data entries by keyword match
    filtered = [
        entry for entry in data
        if any(keyword in str(entry).lower() for keyword in keywords)
    ]

    # 3. Format filtered entries
    formatted_data = "\n".join(
        f"{entry['year']} {entry['brand']} {entry['name']} - {entry['color']}, {entry['city']} - {entry['price']:,.2f} SAR"
        for entry in filtered[:100]  # limit to top 100 to keep GPT prompt short
    )

    # 🔹 Build full prompt with rules and data
    return f"""You are a helpful dealership assistant. Follow the rules strictly and use ONLY the data below to answer.

Rules:
{rules}

Data Summary (if available):
{summary}

Data:
{formatted_data}

Question: {user_question}
Answer:"""

# === Telegram Message Handler ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    prompt = build_prompt(user_text)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Answer clearly and only from the provided data."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.4,
        )
        answer = response.choices[0].message.content.strip()

    except Exception as e:
        answer = f"❌ Error: {e}"

    await update.message.reply_text(answer)

# === Run the Bot ===
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("🚗 Bot started! Ask me about your dealership data.")
    app.run_polling()
