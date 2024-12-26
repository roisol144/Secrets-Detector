# Setting Gitleaks image as base image
FROM zricethezav/gitleaks:latest

# Installing Python
RUN apk add --no-cache python3 py3-pip

# Create a virtual environment
RUN python3 -m venv /app/venv

# Activte the virtual environment & installing required dependencies 
COPY requirements.txt /app/requirements.txt
RUN . /app/venv/bin/activate && pip install --no-cache-dir -r /app/requirements.txt

# Copy the Python scripts that handles everything
COPY main.py /app/main.py
COPY exceptions.py /app/exceptions.py
COPY schemas.py /app/schemas.py

# Copy set of regex and rules to find leaks (Don't have to use it)
# Use this only if you want to add specific regex recognition or unique tokens
COPY .gitleaks.toml /app/.gitleaks.toml


# Set work directory
WORKDIR /code

# Use virtual environment by default 
ENV PATH="/app/venv/bin:$PATH"

# Enable passing arguments to the container
ENTRYPOINT ["python3", "/app/main.py"]