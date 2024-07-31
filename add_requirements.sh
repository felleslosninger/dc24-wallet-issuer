#!/bin/bash

# Check if requirements.txt file exists
if [ ! -f requirements.txt ]; then
  echo "requirements.txt not found!"
  exit 1
fi

# Read each line in requirements.txt and add it to Poetry
while IFS= read -r package || [[ -n "$package" ]]; do
  poetry add "$package"
done < requirements.txt