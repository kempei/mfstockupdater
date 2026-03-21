# MoneyForward Stock updater
## What's This?
MoneyForwardで米ドル建て外国株式の現物資産を前取引日の終値と現在の為替でアップデートします。

## Preparation
### MoneyForward
シャープ(#)で始まる次のフォーマットで株式(現物)の資産を手動追加しておきます。

```
#<ハイフン以外の任意の文字列>-<tick>-<株式数>
例: #MYSTOCK201902-AAPL-1
```

### 株価・為替プロバイダー
AlphaVantage または Financial Modeling Prep (FMP) のいずれかを使用します。

#### AlphaVantage（デフォルト）
以下からAPIキーを取得しておきます。
- https://www.alphavantage.co/support/#api-key

#### Financial Modeling Prep (FMP)
以下からAPIキーを取得しておきます。
- https://site.financialmodelingprep.com/

### Environment Variables
mf.pyでは以下の環境変数を用います。

| 環境変数 | 必須 | 説明 |
|---|---|---|
| `MF_ID` | 必須 | MoneyForwardのユーザ名 |
| `MF_PASS` | 必須 | MoneyForwardのパスワード |
| `STOCK_PROVIDER` | 任意 | 株価プロバイダー（`alphavantage` または `fmp`、デフォルト: `alphavantage`） |
| `ALPHAVANTAGE_API_KEY` | STOCK_PROVIDERがalphavantageの場合に必須 | AlphavantageのAPIキー |
| `FMP_API_KEY` | STOCK_PROVIDERがfmpの場合に必須 | Financial Modeling PrepのAPIキー |
| `CHROME_BINARY` | 任意 | Chromeバイナリのパス（デフォルト: `/usr/bin/chromium-browser`） |
| `CHROMEDRIVER_PATH` | 任意 | chromedriverのパス（デフォルト: `/usr/bin/chromedriver`） |

### Two Step Verification
MoneyForwardで二段階認証を有効にしている場合には、以下のオプションを有効にします。

#### Time-based OTPs
MoneyForward IDで「[二段階認証の設定](https://id.moneyforward.com/two_factor_auth_setting)」を行います。
二段階認証を有効にする際にQRコードと共に表示される32桁 (4桁×8) のシークレットキーを控えておきます。

以下の環境変数を設定します。
- `MF_TWO_STEP_VERIFICATION`: `TOTP` と指定
- `MF_TWO_STEP_VERIFICATION_TOTP_SECRET_KEY`: 控えておいたTime-based OTPsのシークレットキー

#### Gmail （メールでの二段階認証は古いタイプであり、現在は利用できません)
MoneyForwardの登録メールアドレスから、二段階認証用の確認メールを自身のGmailアカウントに転送するように設定しておきます。他の用途で使っていないGmailアカウントを使用することをお勧めします。
- MoneyForwardの登録メールアドレスがGmailの場合の設定例はこちら： https://support.google.com/mail/answer/10957

転送設定をしたGmailアカウントにおいて、アプリケーション用のパスワードを取得しておきます。
- https://support.google.com/accounts/answer/185833

以下の環境変数を設定します。
- `MF_TWO_STEP_VERIFICATION`: `Gmail` と指定
- `MF_TWO_STEP_VERIFICATION_GMAIL_ACCOUNT`: 転送先のGmailアカウント（メールアドレス）
- `MF_TWO_STEP_VERIFICATION_GMAIL_APP_PASS`: 転送先のGmailアカウントで発行したアプリケーション用のパスワード

## Execution
### Docker（AlphaVantage）
```
$ docker run -e MF_ID -e MF_PASS -e ALPHAVANTAGE_API_KEY -it public.ecr.aws/kempei/mfstockupdater
```

### Docker（FMP）
```
$ docker run -e MF_ID -e MF_PASS -e STOCK_PROVIDER=fmp -e FMP_API_KEY -it public.ecr.aws/kempei/mfstockupdater
```

[Public ECR Gallery](https://gallery.ecr.aws/kempei/mfstockupdater)

## Local Development & Testing
AWS Systems Manager Parameter Store に認証情報を格納している場合、以下のスクリプトで手元で実行・テストできます。

### ローカル実行
```bash
# AlphaVantage（デフォルト）
$ ./run_with_ssm.sh

# FMP
$ ./run_with_ssm.sh fmp
```

### 4象限テスト（ローカル × Docker ／ AlphaVantage × FMP）
```bash
$ ./test_all.sh
```

以下の4パターンを自動で順番に実行し、最後にPASS/FAILのサマリーを表示します。

| | AlphaVantage | FMP |
|---|---|---|
| ローカル | ✅ | ✅ |
| Docker | ✅ | ✅ |

> **前提:** AWS CLIの認証設定済み、macOSの場合はDocker Desktopが起動済みであること。
