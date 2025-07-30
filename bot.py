import time
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler
)
import urllib.parse
from auction_scraper import get_vins_from_auction
from nhtsa import decode_vin, is_manual

ASK_AUCTION, ASK_FILTER, GET_FILTERS, PROCESS_VINS = range(4)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! Would you like to fetch vehicle data from the Houston Police Auction site? (yes/no)"
    )
    return ASK_AUCTION

def make_address_link(address: str) -> str:
    encoded = urllib.parse.quote(address)
    return f"[📍 {address}](https://www.google.com/maps/search/?api=1&query={encoded})"

async def split_and_send_message(text: str, update: Update, parse_mode="Markdown"):
    max_len = 4096
    parts = [text[i:i+max_len] for i in range(0, len(text), max_len)]
    for part in parts:
        await update.message.reply_text(part, parse_mode=parse_mode)

async def handle_auction_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip().lower()
    if choice == "yes":
        await update.message.reply_text("Scraping auction site for VINs...")
        vin_groups = get_vins_from_auction()  # dict: {address: [VINs]}

        total_vins = sum(len(vins) for vins in vin_groups.values())
        await update.message.reply_text(f"Found {total_vins} VINs across {len(vin_groups)} locations. Filtering for manual transmissions...")

        for address, vins in vin_groups.items():
            manual_cars = []
            for vin in vins:
                decoded = decode_vin(vin)
                if decoded and is_manual(decoded):
                    car_info = (
                        f" {decoded.get('ModelYear')} {decoded.get('Make')} {decoded.get('Model')} - {vin} \n"
                 )
                    manual_cars.append(car_info)
            time.sleep(0.5)

            if manual_cars:
                address_link = make_address_link(address)
                message = f"📍 *{address_link}* — {len(manual_cars)} manual cars found:\n" + "\n".join(manual_cars)
                await split_and_send_message(message, update, parse_mode="Markdown")
            # else:
                # await update.message.reply_text(f"📍 {address} — no manual cars found.")
    else:
        await update.message.reply_text("Okay! Send a VIN directly to decode (coming soon).")

    return ConversationHandler.END

# async def handle_auction_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     choice = update.message.text.strip().lower()
#     if choice == "yes":
#         context.user_data["vins"] = get_vins_from_auction()
#         await update.message.reply_text("Apply filters to the results? (yes/no)")
#         return ASK_FILTER
#     else:
#         await update.message.reply_text("Okay! Send a VIN directly to decode.")
#         return ConversationHandler.END

# async def handle_filter_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     choice = update.message.text.strip().lower()
#     if choice == "yes":
#         await update.message.reply_text("Enter filters in this format:\n`transmission=automatic; year>=2010`")
#         return GET_FILTERS
#     else:
#         context.user_data["filters"] = {}
#         return await process_vins(update, context)

# async def get_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     filters_input = update.message.text.strip()
#     filters = {}
#     for item in filters_input.split(";"):
#         if '=' in item:
#             key, value = item.strip().split('=')
#             filters[key.strip()] = value.strip()
#         elif '>=' in item:
#             key, value = item.strip().split(">=")
#             filters[key.strip()] = f">={value.strip()}"
#         elif '<=' in item:
#             key, value = item.strip().split("<=")
#             filters[key.strip()] = f"<={value.strip()}"
#     context.user_data["filters"] = filters
#     return await process_vins(update, context)

# async def process_vins(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     vins = context.user_data.get("vins", [])
#     filters = context.user_data.get("filters", {})
#     results = []

#     await update.message.reply_text(f"Processing {len(vins)} VINs...")

    # for vin in vins:
    #     decoded = decode_vin(vin)

    #     # Apply filters
    #     passes = True
    #     for key, value in filters.items():
    #         actual = decoded.get(key.capitalize())
    #         if not actual:
    #             passes = False
    #             break
    #         if ">=" in value:
    #             if not actual.isdigit() or int(actual) < int(value[2:]):
    #                 passes = False
    #         elif "<=" in value:
    #             if not actual.isdigit() or int(actual) > int(value[2:]):
    #                 passes = False
    #         else:
    #             if actual.lower() != value.lower():
    #                 passes = False

    #     if passes:
    #         results.append((vin, decoded.get("Make", "Unknown"), decoded.get("Model", "Unknown"), decoded.get("Model Year", "N/A")))

    # if not results:
    #     await update.message.reply_text("No vehicles matched your filters.")
    # else:
    #     msg = "\n\n".join([f"{vin}\nMake: {make}\nModel: {model}\nYear: {year}" for vin, make, model, year in results])
    #     await update.message.reply_text(msg[:4096])

    # return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_AUCTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_auction_choice)],
            # ASK_FILTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_filter_choice)],
            # GET_FILTERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_filters)],
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)
    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
