#!/bin/bash
# Reproducible ONNX -> TensorRT export. Run on the Jetson that will use the engine.
#   ./export_engine.sh training/models/mymodel.onnx [out.trt]
set -euo pipefail
ONNX="${1:?usage: export_engine.sh model.onnx [out.trt]}"
OUT="${2:-${ONNX%.onnx}.trt}"
TRTEXEC="${TRTEXEC:-/usr/src/tensorrt/bin/trtexec}"
"$TRTEXEC" --onnx="$ONNX" --saveEngine="$OUT" --fp16 --workspace=1024 --verbose \
  | tee "${OUT}.build.log"
sha256sum "$ONNX" "$OUT" | tee "${OUT}.sha256"
echo "engine written to $OUT"
