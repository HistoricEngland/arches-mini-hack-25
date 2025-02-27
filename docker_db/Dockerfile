FROM postgis/postgis:14-3.2

# Install necessary packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       clang-11 \
       llvm-11 \
       llvm-11-dev \
       libpq-dev \
       wget \
       git \
       postgresql-server-dev-14 \
    && git clone --branch v0.8.0 https://github.com/pgvector/pgvector.git /tmp/pgvector \
    && cd /tmp/pgvector \
    && make USE_PGXS=1 \
    && make install USE_PGXS=1 \
    && echo "shared_preload_libraries = 'vector'" >> /usr/share/postgresql/postgresql.conf.sample \
    # Verify installation
    && ls -la /usr/share/postgresql/14/extension/vector* \
    # Clean up
    && cd / \
    && apt-get purge -y --auto-remove build-essential postgresql-server-dev-14 libpq-dev wget git \
    && rm -rf /var/lib/apt/lists/* /tmp/pgvector

COPY ./docker-entrypoint-initdb.d/ /docker-entrypoint-initdb.d/