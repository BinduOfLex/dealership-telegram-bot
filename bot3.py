import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from openai import OpenAI
from dotenv import load_dotenv
from query_parser import extract_filters
from data_search import search_and_summarize
from stats_engine import count_by_field, extreme_value

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
DATA_FILE = "data.json"

# Load dataset
with open(DATA_FILE, "r", encoding="utf-8") as f:
    car_data = json.load(f)

# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.lower().strip()

    # 🔍 Trigger: City-wise car count
    if "show city stats" in user_text:
        city_counts = count_by_field(car_data, "city")
        summary = "\n".join([f"{city}: {count}" for city, count in city_counts])
        await update.message.reply_text(f"📊 City-wise car count:\n{summary}")
        return

    # 🔍 Trigger: Lowest mileage overall
    if "lowest mileage" in user_text:
        lowest = extreme_value(car_data, "mileage", "min")
        if lowest:
            reply = (
                f"🚗 {lowest['year']} {lowest['brand']} {lowest['name']} — {lowest['color']} in {lowest['city']}\n"
                f"🛞 {lowest['body_type']} | {lowest['cylinders']} cyl | {lowest['cylinder_size_liters']}L\n"
                f"📉 Mileage: {int(lowest['mileage']):,} km | 💰 {int(lowest['price']):,} SAR"
            )
        else:
            reply = "No car with valid mileage found."
        await update.message.reply_text(reply)
        return

    # 🧪 Debug: View raw filters
    if "debug" in user_text:
        filters = extract_filters(client, user_text)
        await update.message.reply_text(f"🧪 Extracted Filters:\n```json\n{json.dumps(filters, indent=2)}\n```", parse_mode="Markdown")
        return

    # 🔍 Standard flow
    filters = extract_filters(client, user_text)

    if "__error__" in filters:
        await update.message.reply_text(f"❌ Couldn't parse your request.\n{filters['__error__']}")
        return

    reply = search_and_summarize(filters, car_data, client, user_text)
    await update.message.reply_text(reply)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("🚗 Bot is live with full metrics and expanded dataset!")
    app.run_polling()