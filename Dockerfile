# ==============================================================================
# Stage 1: Build Tailwind CSS
# ==============================================================================
FROM node:20-bookworm-slim AS css-builder

WORKDIR /build

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy all source files needed for Tailwind to scan for classes
# Tailwind config scans ./**/templates/**/*.html
COPY . ./
RUN npm run build

# ==============================================================================
# Stage 2: Final Python image
# ==============================================================================
FROM python:3.13-slim-bookworm

ENV PYTHONUNBUFFERED=1

ARG INSTALL_PG_TOOLS=false

WORKDIR /code

# Install uv for fast dependency management
RUN pip install uv

# Install Python dependencies as root (they go to system site-packages)
COPY requirements.txt requirements.txt
RUN uv pip install --system -r requirements.txt

# Install PostgreSQL tools if needed
RUN if [ "$INSTALL_PG_TOOLS" = "true" ] ; then \
    apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/* ; \
    fi

ARG GIT_SHA
ENV GIT_SHA=${GIT_SHA}

# Copy application code for production builds
# In development, this is overridden by volume mount
COPY . /code

# Copy built CSS from the css-builder stage
COPY --from=css-builder /build/theme/static/dist /code/theme/static/dist

ENTRYPOINT ["/code/docker-entrypoint.sh"]
CMD ["prod"]
