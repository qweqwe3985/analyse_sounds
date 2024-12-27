FROM python:3.12-slim

WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install the required Python packages
RUN pip install -r requirements.txt

# Set the environment variable for the bot token (optional)
# You can also pass the token via an environment variable when running the container
ENV TELEGRAM_BOT_TOKEN="7545487742:AAHK31bh5-4YddWAiUJKXBjJVKMQ0bF8be"

# Command to run the bot when the container starts
CMD ["python", "bot.py"]
