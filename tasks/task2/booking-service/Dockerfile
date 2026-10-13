FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /usr/local/bin/uv

WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY booking.proto ./
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. booking.proto

COPY app ./app

EXPOSE 8080 9090
CMD ["python", "-m", "app.main"]
