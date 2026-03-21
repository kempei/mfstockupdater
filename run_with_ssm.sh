#!/bin/bash
# SSM Parameter Store から環境変数を取得して mf.py を実行するスクリプト
# 使用方法: ./run_with_ssm.sh [alphavantage|fmp]  (省略時: alphavantage)
set -e

PROVIDER="${1:-alphavantage}"
if [ "$PROVIDER" != "alphavantage" ] && [ "$PROVIDER" != "fmp" ]; then
  echo "エラー: プロバイダーは alphavantage または fmp を指定してください。"
  exit 1
fi
echo "株価プロバイダー: $PROVIDER"
export STOCK_PROVIDER="$PROVIDER"

# SSMパラメータ名:環境変数名 の対応（"SSM名 ENV名" 形式）
SSM_MAPPINGS=(
  "mf_id MF_ID"
  "mf_pass MF_PASS"
  "MF_TWO_STEP_VERIFICATION MF_TWO_STEP_VERIFICATION"
  "MF_TWO_STEP_VERIFICATION_TOTP_SECRET_KEY MF_TWO_STEP_VERIFICATION_TOTP_SECRET_KEY"
  "alpha_vantage_api_key ALPHAVANTAGE_API_KEY"
  "fmp_api_key FMP_API_KEY"
)

echo "SSM Parameter Store からパラメータを取得中..."

for MAPPING in "${SSM_MAPPINGS[@]}"; do
  SSM_NAME=$(echo "$MAPPING" | awk '{print $1}')
  ENV_NAME=$(echo "$MAPPING" | awk '{print $2}')
  VALUE=$(aws ssm get-parameter \
    --name "$SSM_NAME" \
    --with-decryption \
    --query "Parameter.Value" \
    --output text 2>/dev/null) || true

  if [ -n "$VALUE" ]; then
    export "$ENV_NAME"="$VALUE"
    echo "  取得: $SSM_NAME -> $ENV_NAME"
  else
    echo "  スキップ (未設定): $SSM_NAME"
  fi
done

# macOS の場合は Chrome / chromedriver パスを設定
if [ "$(uname)" = "Darwin" ]; then
  export CHROME_BINARY="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  export CHROMEDRIVER_PATH="$(find "$HOME/.cache/selenium" -name "chromedriver" -type f 2>/dev/null | sort | tail -1)"
fi

echo "mf.py を実行中..."
python mf.py
