#!/usr/bin/env bash
# 🤗 Submit the heritage-3d batch to Hugging Face Jobs (CPU).
#
# Prerequisites (all via environment, never hardcoded):
#   HF_TOKEN            – token with write access (fine-grained token required
#                         when submitting under an org namespace with a token policy)
#   HF_DATASET_REPO     – target dataset repo, e.g. your-user/heritage-3d-models
#   HF_CODE_REPO        – private repo used as code bundle (default: <dataset repo owner>/heritage-3d-code)
#   EE_PROJECT_ID       – Google Earth Engine project id
#   ~/.config/earthengine/credentials must exist (earthengine authenticate)
#
# Optional:
#   HF_JOB_NAMESPACE    – org namespace for org billing (default: your account)
#   HF_JOB_FLAVOR       – cpu-basic|cpu-upgrade|... (default: cpu-upgrade)
#   HF_JOB_TIMEOUT      – e.g. 6h (default: 6h)
#
# What it does:
#   1. Uploads the pipeline code to the private HF code repo
#   2. Submits an HF Job: install deps → restore EE credentials →
#      fetch catalogs → batch.py → upload_hf.py
#
# Usage:  ./submit_hf_job.sh [--pilot | --all --limit N | --sites ...]

set -euo pipefail

BATCH_ARGS="${*:---pilot}"
EE_PROJECT_ID="${EE_PROJECT_ID:?EE_PROJECT_ID not set (see .env.example)}"
: "${HF_TOKEN:?HF_TOKEN not set}"
: "${HF_DATASET_REPO:?HF_DATASET_REPO not set, e.g. your-user/heritage-3d-models}"
CODE_REPO="${HF_CODE_REPO:-${HF_DATASET_REPO%%/*}/heritage-3d-code}"
FLAVOR="${HF_JOB_FLAVOR:-cpu-upgrade}"
TIMEOUT="${HF_JOB_TIMEOUT:-6h}"
NAMESPACE="${HF_JOB_NAMESPACE:-}"

EE_CREDS="$HOME/.config/earthengine/credentials"
[ -f "$EE_CREDS" ] || { echo "❌ No EE credentials at $EE_CREDS — run: earthengine authenticate"; exit 1; }

echo "📦 Uploading code bundle to $CODE_REPO ..."
hf repos create "$CODE_REPO" --type dataset --private --exist-ok
STAGING=$(mktemp -d)
trap 'rm -rf "$STAGING"' EXIT
cp main.py pipeline.py batch.py quality_gate.py quality_config.py \
   unesco_data.py upload_hf.py smooth_export.py regen_smooth.py \
   analysis.py backfill_analysis.py "$STAGING/"
hf upload "$CODE_REPO" "$STAGING" --type dataset --private \
  --commit-message "pipeline code $(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo "🔐 Preparing job secrets (EE credentials, never stored in repo) ..."
SECRETS_FILE=$(mktemp /tmp/hf_job_secrets.XXXXXX)
trap 'rm -rf "$STAGING"; rm -f "$SECRETS_FILE"' EXIT
{
  echo "HF_TOKEN=$HF_TOKEN"
  echo "EE_CREDENTIALS=$(tr -d '\n' < "$EE_CREDS")"
} > "$SECRETS_FILE"

JOB_CMD=$(cat <<EOF
set -e &&
apt-get update -qq && apt-get install -y -qq libgl1 libglib2.0-0 > /dev/null &&
pip install -q voxcity==1.6.2 "overturemaps>=1.0.1" mapbox-earcut huggingface_hub requests python-dotenv rich tenacity pandas &&
mkdir -p ~/.config/earthengine &&
printf '%s' "\$EE_CREDENTIALS" > ~/.config/earthengine/credentials &&
hf download $CODE_REPO --type dataset --local-dir /tmp/code &&
cd /tmp/code &&
python unesco_data.py &&
python -u batch.py $BATCH_ARGS &&
python upload_hf.py --repo $HF_DATASET_REPO
EOF
)

echo "🚀 Submitting HF Job (namespace=${NAMESPACE:-personal}, flavor=$FLAVOR, timeout=$TIMEOUT, args: $BATCH_ARGS) ..."
NAMESPACE_ARGS=()
[ -n "$NAMESPACE" ] && NAMESPACE_ARGS=(--namespace "$NAMESPACE")
hf jobs run python:3.12-slim \
  "${NAMESPACE_ARGS[@]}" \
  --flavor "$FLAVOR" \
  --timeout "$TIMEOUT" \
  --secrets-file "$SECRETS_FILE" \
  --env "EE_PROJECT_ID=$EE_PROJECT_ID" \
  --env "PYTHONUNBUFFERED=1" \
  --detach \
  bash -c "$JOB_CMD"

echo "✅ Submitted. Track with: hf jobs list / hf jobs logs <JOB_ID> --follow"
