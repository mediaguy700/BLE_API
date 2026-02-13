#!/usr/bin/env bash
# Generate a credentials file to hand to developers (URL + API key only).
# Run this once if you have AWS CLI access; share the output file securely.
# Option: --static-2weeks = same URL + key, valid for 2 weeks (full API access).
# Option: --third-party = output URL + token for a 3rd party application to test the API.
# The API key is kept STATIC across runs: first run fetches from AWS and caches it;
# later runs reuse the cached key. Use --refresh-key to fetch a new key from AWS.
set -e
STACK_NAME="${STACK_NAME:-ble-people-tracker}"
REGION="${REGION:-us-east-2}"
OUTPUT_FILE=""
STATIC_2WEEKS=0
REFRESH_KEY=0
THIRD_PARTY=0
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STATIC_KEY_CACHE="$PROJECT_ROOT/.static-api-key.cache"

while [ $# -gt 0 ]; do
  case "$1" in
    --static-2weeks)
      STATIC_2WEEKS=1
      shift
      ;;
    --third-party)
      THIRD_PARTY=1
      shift
      ;;
    --refresh-key)
      REFRESH_KEY=1
      shift
      ;;
    *)
      if [ -z "$OUTPUT_FILE" ]; then
        OUTPUT_FILE="$1"
      fi
      shift
      ;;
  esac
done

if [ -z "$OUTPUT_FILE" ]; then
  if [ "$THIRD_PARTY" = 1 ]; then
    OUTPUT_FILE="third_party_api_access.env"
  elif [ "$STATIC_2WEEKS" = 1 ]; then
    OUTPUT_FILE="static-2week-api-access.env"
  else
    OUTPUT_FILE="developer-credentials.env"
  fi
fi

API_URL=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text)
API_KEY_ID=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiKeyId`].OutputValue' \
  --output text)

if [ -z "$API_URL" ] || [ -z "$API_KEY_ID" ]; then
  echo "Error: Could not get ApiUrl or ApiKeyId from stack $STACK_NAME. Is it deployed?" >&2
  exit 1
fi

API_URL="${API_URL%/}"

# Static API key: use cache so the same key is always output unless --refresh-key
if [ "$REFRESH_KEY" = 1 ] || [ ! -s "$STATIC_KEY_CACHE" ]; then
  API_KEY_VALUE=$(aws apigateway get-api-key \
    --api-key "$API_KEY_ID" \
    --include-value \
    --region "$REGION" \
    --query 'value' \
    --output text)
  printf '%s' "$API_KEY_VALUE" > "$STATIC_KEY_CACHE"
  [ "$REFRESH_KEY" = 1 ] && echo "Refreshed API key and updated cache."
else
  API_KEY_VALUE=$(cat "$STATIC_KEY_CACHE")
  echo "Using static (cached) API key – same key every time. Use --refresh-key to fetch a new one."
fi

if [ "$THIRD_PARTY" = 1 ]; then
  # 3rd party: URL + token for an external application to test the API
  if date -v+14d +%Y-%m-%d &>/dev/null; then
    VALID_UNTIL=$(date -v+14d +%Y-%m-%d)
  else
    VALID_UNTIL=$(date -d "+14 days" +%Y-%m-%d 2>/dev/null || echo "14 days from issue")
  fi
  cat > "$OUTPUT_FILE" << EOF
# BLE People Tracker API – 3rd party test credentials (do not commit; share securely)
# Give this URL and token to an external application to test the API.
# Send the token on every request: header "x-api-key: <TOKEN>"

URL=$API_URL
TOKEN=$API_KEY_VALUE
VALID_UNTIL=$VALID_UNTIL
EOF
  echo "Created: $OUTPUT_FILE (URL + token for 3rd party application testing)"
  echo "Share this file with the 3rd party. They use URL as base and send TOKEN in header: x-api-key"
elif [ "$STATIC_2WEEKS" = 1 ]; then
  # Compute date 2 weeks from now (works on macOS and Linux)
  if date -v+14d +%Y-%m-%d &>/dev/null; then
    VALID_UNTIL=$(date -v+14d +%Y-%m-%d)
  else
    VALID_UNTIL=$(date -d "+14 days" +%Y-%m-%d 2>/dev/null || echo "14 days from issue")
  fi
  cat > "$OUTPUT_FILE" << EOF
# BLE People Tracker API – static URL and API key, full access, valid for 2 weeks
# Do not commit. Share securely. After 2 weeks, request a new key from your admin.
# Use: BASE_URL for all requests; send API_KEY in header: x-api-key

BASE_URL=$API_URL
API_KEY=$API_KEY_VALUE
VALID_UNTIL=$VALID_UNTIL
EOF
  echo "Created: $OUTPUT_FILE (static URL + key, full API access, valid until $VALID_UNTIL)"
else
  cat > "$OUTPUT_FILE" << EOF
# BLE People Tracker API – for developers (do not commit; share securely)
# Use BASE_URL for all requests; send API_KEY in header: x-api-key

BASE_URL=$API_URL
API_KEY=$API_KEY_VALUE
EOF
  echo "Created: $OUTPUT_FILE"
fi

echo "Share this file (or its contents) over a secure channel."
echo "Recipients need only the URL and token/key; no CLI or AWS access required."
