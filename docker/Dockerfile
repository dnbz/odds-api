FROM python:3.11-slim
WORKDIR /app

# install PDM
RUN pip install -U pip setuptools wheel
RUN pip install pdm

COPY pyproject.toml pdm.lock ./
RUN pdm install --prod --no-lock --no-editable

COPY .. .
COPY ./entrypoints/* ./

ENTRYPOINT ["./entrypoint.sh"]
