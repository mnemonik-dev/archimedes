# Stage 1: install Python dependencies into an isolated directory.
# python:3.12-slim is used only as a build tool — nothing from it reaches the runtime.
FROM python:3.12-slim AS builder
RUN pip install --no-cache-dir --target=/deps lizard

# Stage 2: distroless Python runtime — no shell, no package manager, no root.
# The analysis script is pure Python (no subprocess/git calls), so no extras needed.
FROM gcr.io/distroless/python3-debian12:nonroot
COPY --from=builder /deps /deps
ENV PYTHONPATH=/deps
WORKDIR /workspace
