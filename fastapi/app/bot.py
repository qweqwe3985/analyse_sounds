from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import json
import asyncio

# File to store user IDs
USER_DATA_FILE = "users.json"


# Function to load users from file
def load_users():
    try:
        with open(USER_DATA_FILE, "r") as file:
            users = json.load(file)
            if not users:  # If the file is empty, return an empty list
                return []
            return users
    except (FileNotFoundError, json.JSONDecodeError):
        # If the file doesn't exist or contains invalid JSON, return an empty list
        return []


# Function to save users to file
def save_users(users):
    with open(USER_DATA_FILE, "w") as file:
        json.dump(users, file)


# Function to handle the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_chat.id
    users = load_users()

    if user_id not in users:
        users.append(user_id)
        save_users(users)
        await update.message.reply_text("You are now subscribed to broadcasts!")
    else:
        await update.message.reply_text("You are already subscribed.")


# Function to broadcast a message to all subscribers
async def broadcast_message(application, message: str):
    users = load_users()
    for user_id in users:
        try:
            await application.bot.send_message(chat_id=user_id, text=message)
        except Exception as e:
            print(f"Failed to send message to user {user_id}: {e}")


# Main function to trigger a broadcast programmatically
async def trigger_broadcast(
    application, message="This is a programmatically triggered broadcast!"
):
    await broadcast_message(application, message)


def init_bot():
    # Create the application
    application = (
        ApplicationBuilder()
        .token("7545487742:AAHK31bh5-4YddWAiUJKXBjJVKMQ0bF8beE")
        .build()
    )

    # Register command handlers
    application.add_handler(CommandHandler("start", start))

    # Start the bot
    print("Bot is running!")
    application.run_polling()


if __name__ == "__main__":
    init_bot()
