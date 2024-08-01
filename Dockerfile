FROM python:3.12-slim-bookworm

# Install required dependencies
RUN apt-get update && \
    apt-get install -y git openssl gcc && \
    apt-get clean


# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Run main.py when the container launches
CMD ["fastapi", "run"]