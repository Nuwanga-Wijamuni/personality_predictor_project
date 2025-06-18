# Use a slim Python base image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project directory into the container
# This copies app.py, data/, models/, etc.
COPY . .

# Expose the port that the Flask app will listen on
# This needs to match the PORT environment variable in app.py
EXPOSE 7860  

# Command to run the Flask application using Gunicorn
# 'app:app' means the 'app' variable inside the 'app.py' file
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "app:app"]
# Alternatively, if you prefer to use the PORT env var:
# CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "app:app"]
# In the `app.py`, `port = int(os.environ.get('PORT', 5000))` is used. So, let's stick to 5000 in CMD.
# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
# Let's adjust the `app.py` port default to 7860 to match HF Spaces common practice.
# (Correction in app.py above: `port = int(os.environ.get('PORT', 7860))` )

# Final CMD matching the app.py change:
# CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "app:app"]
# HF Spaces will set the $PORT environment variable for you.