#!/bin/bash
# 4象限テスト: [ローカル/Docker] x [AlphaVantage/FMP]
set -e

PASS=0
FAIL=0

run_test() {
  local label="$1"
  shift
  echo ""
  echo "========================================="
  echo " $label"
  echo "========================================="
  if "$@" 2>&1; then
    echo ">>> PASS: $label"
    PASS=$((PASS + 1))
  else
    echo ">>> FAIL: $label"
    FAIL=$((FAIL + 1))
  fi
}

echo "SSM Parameter Store からパラメータを取得中..."
MF_ID=$(aws ssm get-parameter --name mf_id --with-decryption --query Parameter.Value --output text)
MF_PASS=$(aws ssm get-parameter --name mf_pass --with-decryption --query Parameter.Value --output text)
MF_TWO_STEP_VERIFICATION=$(aws ssm get-parameter --name MF_TWO_STEP_VERIFICATION --query Parameter.Value --output text)
MF_TWO_STEP_VERIFICATION_TOTP_SECRET_KEY=$(aws ssm get-parameter --name MF_TWO_STEP_VERIFICATION_TOTP_SECRET_KEY --with-decryption --query Parameter.Value --output text)
ALPHAVANTAGE_API_KEY=$(aws ssm get-parameter --name alpha_vantage_api_key --with-decryption --query Parameter.Value --output text)
FMP_API_KEY=$(aws ssm get-parameter --name fmp_api_key --with-decryption --query Parameter.Value --output text)
echo "取得完了"

# macOS 用パス設定
if [ "$(uname)" = "Darwin" ]; then
  CHROME_BINARY="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  CHROMEDRIVER_PATH="$(find "$HOME/.cache/selenium" -name "chromedriver" -type f 2>/dev/null | sort | tail -1)"
fi

# --- ローカル実行関数 ---
run_local() {
  local provider="$1"
  export MF_ID MF_PASS MF_TWO_STEP_VERIFICATION MF_TWO_STEP_VERIFICATION_TOTP_SECRET_KEY
  export STOCK_PROVIDER="$provider"
  export ALPHAVANTAGE_API_KEY FMP_API_KEY
  export CHROME_BINARY CHROMEDRIVER_PATH
  python mf.py
}

# --- Docker 実行関数 ---
run_docker() {
  local provider="$1"
  docker run --rm \
    -e MF_ID="$MF_ID" \
    -e MF_PASS="$MF_PASS" \
    -e MF_TWO_STEP_VERIFICATION="$MF_TWO_STEP_VERIFICATION" \
    -e MF_TWO_STEP_VERIFICATION_TOTP_SECRET_KEY="$MF_TWO_STEP_VERIFICATION_TOTP_SECRET_KEY" \
    -e STOCK_PROVIDER="$provider" \
    -e ALPHAVANTAGE_API_KEY="$ALPHAVANTAGE_API_KEY" \
    -e FMP_API_KEY="$FMP_API_KEY" \
    mfstockupdater:local
}

# Docker イメージをビルド
echo ""
echo "Docker イメージをビルド中..."
docker build -t mfstockupdater:local . 2>&1 | tail -3

# 4象限テスト実行
run_test "[1/4] ローカル  x AlphaVantage" run_local alphavantage
run_test "[2/4] ローカル  x FMP"          run_local fmp
run_test "[3/4] Docker    x AlphaVantage" run_docker alphavantage
run_test "[4/4] Docker    x FMP"          run_docker fmp

# 結果サマリー
echo ""
echo "========================================="
echo " テスト結果: PASS=$PASS  FAIL=$FAIL"
echo "========================================="
[ "$FAIL" -eq 0 ]
