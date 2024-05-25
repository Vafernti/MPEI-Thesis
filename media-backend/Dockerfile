FROM python:3.12-slim

# Set the working directory
WORKDIR /code

# Install Poetry and any necessary dependencies
RUN pip install --no-cache-dir -U pip \
    && pip install poetry

# Copy poetry files
COPY ./pyproject.toml ./poetry.lock /code/

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-cache

# Copy the application code
COPY ./app /code/app

# Expose the port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]