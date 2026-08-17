#!/usr/bin/env bash
# 🤗 Submit the heritage-3d batch to Hugging Face Jobs (CPU).
#
# Prerequisites (all via environment, never hardcoded):
#   HF_TOKEN            – token with write access to the dataset/code repos
#   HF_JOBS_TOKEN       – optional: separate token for `hf jobs run` (e.g. a
#                         fine-grained token with Jobs permission under an org);
#                         defaults to HF_TOKEN
#   HF_DATASET_REPO     – target dataset repo, e.g. your-user/heritage-3d-models
#   HF_CODE_REPO        – private repo used as code bundle (default: <dataset repo owner>/heritage-3d-code)
#   EE_PROJECT_ID       – Google Earth Engine project id
#   ~/.config/earthengine/credentials must exist (earthengine authenticate)
#
# Optional:
#   HF_JOB_NAMESPACE    – org namespace for org billing (default: your account)
#   HF_JOB_FLAVOR       – cpu-basic|cpu-upgrade|... (default: cpu-basic)
#   HF_JOB_TIMEOUT      – e.g. 6h (default: 72h when sharded, else 6h)
#
# Sharding (for the full catalog):
#   ./submit_hf_job.sh --shards 8 --all
#   submits 8 parallel jobs; job i runs batch.py --all --shard i/8.
#   Each job works in WAVES (batch → upload --no-card, repeated) so results
#   reach the dataset incrementally even if the job later hits its timeout.
#   After ALL shards finish, rebuild the dataset card once:
#     python upload_hf.py --rebuild-card
#
# Usage:  ./submit_hf_job.sh [--shards N] [--pilot | --all [--limit N] | --sites ...]

set -euo pipefail

SHARDS=1
if [ "${1:-}" = "--shards" ]; then
  SHARDS="${2:?--shards needs a number}"
  shift 2
fi

BATCH_ARGS="${*:---pilot}"
EE_PROJECT_ID="${EE_PROJECT_ID:?EE_PROJECT_ID not set (see .env.example)}"
: "${HF_TOKEN:?HF_TOKEN not set}"
: "${HF_DATASET_REPO:?HF_DATASET_REPO not set, e.g. your-user/heritage-3d-models}"
CODE_REPO="${HF_CODE_REPO:-${HF_DATASET_REPO%%/*}/heritage-3d-code}"
FLAVOR="${HF_JOB_FLAVOR:-cpu-basic}"
if [ "$SHARDS" -gt 1 ]; then
  TIMEOUT="${HF_JOB_TIMEOUT:-72h}"
else
  TIMEOUT="${HF_JOB_TIMEOUT:-6h}"
fi
NAMESPACE="${HF_JOB_NAMESPACE:-}"
JOBS_TOKEN="${HF_JOBS_TOKEN:-$HF_TOKEN}"

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

# Waves: batch is resume-safe (skips already-passed), so each wave picks up
# where the previous one stopped; upload runs after EVERY wave so partial
# results survive a job timeout. --no-card: parallel shards must not
# overwrite the shared dataset card (rebuilt once at the end).
JOB_CMD_TEMPLATE=$(cat <<EOF
set -e &&
apt-get update -qq && apt-get install -y -qq libgl1 libglib2.0-0 > /dev/null &&
pip install -q voxcity==1.6.2 "overturemaps>=1.0.1" mapbox-earcut huggingface_hub requests python-dotenv rich tenacity pandas &&
mkdir -p ~/.config/earthengine &&
printf '%s' "\$EE_CREDENTIALS" > ~/.config/earthengine/credentials &&
hf download $CODE_REPO --type dataset --local-dir /tmp/code &&
cd /tmp/code &&
python unesco_data.py &&
for wave in 1 2 3; do
  echo "=== wave \$wave ===" &&
  (python -u batch.py __BATCH_ARGS__ || true) &&
  (python upload_hf.py --repo $HF_DATASET_REPO --no-card || true);
done
EOF
)

NAMESPACE_ARGS=()
[ -n "$NAMESPACE" ] && NAMESPACE_ARGS=(--namespace "$NAMESPACE")

for ((i = 0; i < SHARDS; i++)); do
  if [ "$SHARDS" -gt 1 ]; then
    ARGS="$BATCH_ARGS --shard $i/$SHARDS"
  else
    ARGS="$BATCH_ARGS"
  fi
  JOB_CMD="${JOB_CMD_TEMPLATE/__BATCH_ARGS__/$ARGS}"
  echo "🚀 Submitting job $((i + 1))/$SHARDS (namespace=${NAMESPACE:-personal}, flavor=$FLAVOR, timeout=$TIMEOUT, args: $ARGS) ..."
  HF_TOKEN="$JOBS_TOKEN" hf jobs run python:3.12-slim \
    "${NAMESPACE_ARGS[@]}" \
    --flavor "$FLAVOR" \
    --timeout "$TIMEOUT" \
    --secrets-file "$SECRETS_FILE" \
    --env "EE_PROJECT_ID=$EE_PROJECT_ID" \
    --env "PYTHONUNBUFFERED=1" \
    --detach \
    bash -c "$JOB_CMD"
done

echo "✅ $SHARDS job(s) submitted. Track with: hf jobs list / hf jobs logs <JOB_ID> --follow"
if [ "$SHARDS" -gt 1 ]; then
  echo "🃏 After ALL shards complete, rebuild the dataset card:"
  echo "   python upload_hf.py --rebuild-card"
fi
