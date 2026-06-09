FROM python:3.11-slim

# Install system dependencies for WeasyPrint and base packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libffi-dev \
    shared-mime-info \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libglib2.0-0 \
    fontconfig \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python requirements directly (avoiding extra files for requirements.txt if simple)
RUN pip install --no-cache-dir flask weasyprint

# Copy the app files into the container
COPY app.py /app/
COPY templates /app/templates/

# Expose the Flask port
EXPOSE 3333

# Set environment variables
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Run the app
CMD ["python", "app.py"]
