FROM python:3.9-slim
WORKDIR /app

# Install dependencies 
RUN apt-get update && apt-get install -y libfreetype6-dev
RUN pip install --no-cache-dir pandas numpy matplotlib openpyxl pyyaml scipy

# Copy files into the container
COPY . .

# Set the default command to show help
ENTRYPOINT ["python", "main.py"]