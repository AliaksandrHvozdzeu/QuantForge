#!/bin/bash
set -euo pipefail

MODEL_REPO="${MODEL_REPO:-Qwen/Qwen2.5-Coder-7B-Instruct}"
MODEL_BASE_DIR="${MODEL_BASE_DIR:-qwen2.5-coder-7b-instruct-base}"
GGUF_OUTPUT="${GGUF_OUTPUT:-Qwen2.5-Coder-7B-Q5_K_M.gguf}"
QUANT_TYPE="${QUANT_TYPE:-Q5_K_M}"
SKIP_DOWNLOAD="${SKIP_DOWNLOAD:-0}"
KEEP_BASE="${KEEP_BASE:-1}"

BASE_DIR="/models/${MODEL_BASE_DIR}"
FP16_OUT="/models/${GGUF_OUTPUT%.gguf}-FP16.gguf"
Q_OUT="/models/${GGUF_OUTPUT}"

cd /workspace/llama.cpp

# Detect downloaded weights (sharded or single file)
model_ready() {
    [ -f "${BASE_DIR}/model.safetensors.index.json" ] || \
    [ -f "${BASE_DIR}/model.safetensors" ] || \
    [ -n "$(find "${BASE_DIR}" -maxdepth 1 -name 'model-*.safetensors' 2>/dev/null | head -1)" ]
}

if [ "$SKIP_DOWNLOAD" != "1" ] && ! model_ready; then
    echo "========================================="
    echo "Downloading Qwen2.5-Coder-7B-Instruct..."
    echo "Repository: ${MODEL_REPO}"
    echo "========================================="
    python3 -c "
from huggingface_hub import snapshot_download
import os

model_repo = os.environ.get('MODEL_REPO', 'Qwen/Qwen2.5-Coder-7B-Instruct')
token = os.environ.get('HF_TOKEN') or None
base = '${BASE_DIR}'

os.makedirs(base, exist_ok=True)
print(f'Downloading {model_repo}...')
snapshot_download(repo_id=model_repo, local_dir=base, token=token)
print('Model downloaded successfully')
"
else
    echo "========================================="
    echo "Using existing model at ${BASE_DIR}"
    echo "========================================="
fi

echo ""
echo "========================================="
echo "Converting to GGUF format (FP16)..."
echo "========================================="
python3 convert_hf_to_gguf.py "${BASE_DIR}" --outfile "${FP16_OUT}" --outtype f16
echo "Conversion completed"

echo ""
echo "========================================="
echo "Quantizing to ${QUANT_TYPE}..."
echo "========================================="
./llama-quantize "${FP16_OUT}" "${Q_OUT}" "${QUANT_TYPE}"
echo "${QUANT_TYPE} quantization completed"

echo ""
echo "========================================="
echo "Running benchmark (CPU)..."
echo "========================================="
./llama-bench -m "${Q_OUT}" -n 128 -p 512 > /metrics/bench_results.txt 2>&1
echo "Benchmark completed"

echo ""
echo "========================================="
echo "Cleaning up temporary files..."
echo "========================================="
rm -f "${FP16_OUT}"
if [ "$KEEP_BASE" != "1" ]; then
    rm -rf "${BASE_DIR}"
fi
echo "Cleanup completed"

echo ""
echo "Output file:"
ls -lh "${Q_OUT}"
