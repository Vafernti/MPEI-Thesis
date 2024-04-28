FROM python:3.12

WORKDIR /code

RUN pip3 install -U pip poetry

COPY ./poetry.lock ./pyproject.toml /code/

RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-cache

COPY ./app /code/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]