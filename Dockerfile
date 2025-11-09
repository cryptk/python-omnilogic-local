# Multi-stage build for python-omnilogic-local CLI
# Stage 1: Builder
FROM python:3.12-slim AS builder

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md LICENSE ./
COPY pyomnilogic_local/ ./pyomnilogic_local/

# Install the package with CLI dependencies in a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e ".[cli]"

# Stage 2: Runtime
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies for scapy (needed for CLI packet capture tools)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tcpdump \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /build /build

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# Create non-root user for security
RUN useradd -m -u 1000 omnilogic && \
    chown -R omnilogic:omnilogic /app

USER omnilogic

# Set entrypoint to the omnilogic CLI
ENTRYPOINT ["omnilogic"]

# Default help command
CMD ["--help"]
