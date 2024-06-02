FROM python:3.12-slim

# Create a user to run the app in Container Apps
RUN groupadd --gid 1000 appuser \
  && useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home appuser

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
COPY ./static /code/static/

# Expose the port
EXPOSE 8000

# Allow the user to create files in the main directory
RUN chown -R 1000 /code

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]