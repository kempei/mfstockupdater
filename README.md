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

### Alphavantage
株価/為替取得のため、AlphavantageのAPIを使っています。以下からご自身のAlphavantageのAPIキーを取得しておきます。
- https://www.alphavantage.co/support/#api-key

### Environment Variables
mf.pyでは以下の環境変数を用います。
- MF_ID: MoneyForwardのユーザ名
- MF_PASS: MoneyForwardのパスワード
- ALPHAVANTAGE_API_KEY: AlphavantageのAPIKEY

### Two Step Verification
MoneyForwardで二段階認証を有効にしている場合には、以下のオプションを有効にします。

#### Time-based OTPs
MoneyForward IDで「[二段階認証の設定](https://id.moneyforward.com/two_factor_auth_setting)」を行います。
二段階認証を有効にする際に表示される32桁 (4桁×8) のシークレットキーを控えておきます。

以下の環境変数を設定します。
- MF_TWO_STEP_VERIFICATION: "TOTP"と指定
- MF_TWO_STEP_VERIFICATION_TOTP_SECRET_KEY: 控えておいたTime-based OTPsのシークレットキー

#### Gmail （メールでの二段階認証は古いタイプであり、現在は利用できません)
MoneyForwardの登録メールアドレスから、二段階認証用の確認メールを自身のGmailアカウントに転送するように設定しておきます。他の用途で使っていないGmailアカウントを使用することをお勧めします。
- MoneyForwardの登録メールアドレスがGmailの場合の設定例はこちら： https://support.google.com/mail/answer/10957

転送設定をしたGmailアカウントにおいて、アプリケーション用のパスワードを取得しておきます。
- https://support.google.com/accounts/answer/185833

以下の環境変数を設定します。
- MF_TWO_STEP_VERIFICATION: "Gmail"と指定
- MF_TWO_STEP_VERIFICATION_GMAIL_ACCOUNT: 転送先のGmailアカウント（メールアドレス）
- MF_TWO_STEP_VERIFICATION_GMAIL_APP_PASS: 転送先のGmailアカウントで発行したアプリケーション用のパスワード

## Execution
```
$ docker run -e MF_ID -e MF_PASS -e ALPHAVANTAGE_API_KEY -it public.ecr.aws/kempei/mfstockupdater
```

[Public ECR Gallery](https://gallery.ecr.aws/kempei/mfstockupdater)
