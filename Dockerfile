# syntax=docker/dockerfile:1
# QuantForge - multi-stage image for llama.cpp quantization
# Build: docker build -t llama-quantizer:latest .

ARG PYTHON_IMAGE=python:3.10-slim-bookworm
ARG LLAMA_CPP_REPO=https://github.com/ggml-org/llama.cpp.git
ARG LLAMA_CPP_REF=b9193

# -----------------------------------------------------------------------------
# Stage 1: compile llama.cpp tools (llama-quantize, llama-bench, ...)
# -----------------------------------------------------------------------------
FROM debian:bookworm-slim AS llama-builder

ARG LLAMA_CPP_REPO
ARG LLAMA_CPP_REF

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    git \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
RUN git clone --depth 1 --branch "${LLAMA_CPP_REF}" "${LLAMA_CPP_REPO}" llama.cpp

WORKDIR /src/llama.cpp
RUN cmake -B build -DCMAKE_BUILD_TYPE=Release -DLLAMA_BUILD_TESTS=OFF \
    && cmake --build build --config Release -j"$(nproc)"

# Symlink binaries next to convert_hf_to_gguf.py (quantize.sh expects ./llama-quantize)
RUN for bin in llama-quantize llama-bench; do \
      if [ -f "build/bin/${bin}" ]; then ln -sf "build/bin/${bin}" "./${bin}"; fi; \
    done

# -----------------------------------------------------------------------------
# Stage 2: Python dependencies for HuggingFace download + GGUF conversion
# -----------------------------------------------------------------------------
FROM ${PYTHON_IMAGE} AS py-deps

COPY docker/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# -----------------------------------------------------------------------------
# Stage 3: runtime (llama.cpp tree + tools + Python)
# -----------------------------------------------------------------------------
FROM ${PYTHON_IMAGE} AS runtime

LABEL org.opencontainers.image.title="QuantForge llama-quantizer"
LABEL org.opencontainers.image.description="llama.cpp quantization toolchain for QuantForge"

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=llama-builder /src/llama.cpp /workspace/llama.cpp
COPY --from=py-deps /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=py-deps /usr/local/bin /usr/local/bin

RUN mkdir -p /models /metrics

WORKDIR /workspace/llama.cpp

CMD ["/bin/bash"]
