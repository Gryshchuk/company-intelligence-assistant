FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System libs LanceDB / trafilatura wheels expect at runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first for better layer caching.
COPY pyproject.toml ./
RUN pip install \
    "deepagents>=0.6.1" \
    "langchain>=1.3" \
    "langchain-openai>=1.2" \
    "langgraph>=1.0" \
    "openai>=2.0" \
    "streamlit>=1.49" \
    "lancedb>=0.30" \
    "pyarrow>=15" \
    "tavily-python>=0.7" \
    "wikipedia-api>=0.8" \
    "trafilatura>=2.0" \
    "httpx>=0.28" \
    "python-dotenv>=1.0" \
    "tiktoken>=0.13" \
    "pydantic>=2.7"

COPY . .
RUN pip install --no-deps -e .

# Skip Streamlit welcome prompt + bind to all interfaces.
RUN mkdir -p /root/.streamlit && \
    printf '[general]\nemail = ""\n' > /root/.streamlit/credentials.toml

EXPOSE 8501

CMD ["streamlit", "run", "app.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
