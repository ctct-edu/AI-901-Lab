---
lab:
  title: Python SDKで顧客レビューを分析しよう
  description: Azure Language SDKを使い、レビューの言語、感情、固有表現、キーフレーズ、PIIを分析します。
  level: 200
  duration: 40 minutes
  islab: true
  primarytopics:
    - Microsoft Foundry
    - Azure Language
    - Python
---

# Python SDKで顧客レビューを分析しよう

この演習では、[03bのプレイグラウンド演習](./03b-text-analysis.md)で確認したAzure Languageの機能を、Pythonプログラムから呼び出します。ホテルのレビューを一度読み込み、言語検出、感情分析、固有表現認識、キーフレーズ抽出、個人を特定できる情報（PII）の検出を順番に実行します。

作業時間の目安は **40分** です。入力に含まれる氏名、メールアドレス、電話番号はすべて架空です。

## 学習目標

この演習を完了すると、次のことができるようになります。

- Azure Language用のキーとエンドポイントを安全に設定する
- Python仮想環境を作成し、Azure SDKをインストールする
- `TextAnalyticsClient`で5種類のテキスト分析を実行する
- SDKの構造化された応答とエラーを確認する
- PIIをマスクした結果をUTF-8のJSONファイルへ保存する
- 専用AIサービスと生成AIモデルの使い分けを説明する

## 前提条件

- Windows 11、Visual Studio Code、PowerShell
- 64-bit版Python 3.11
- [演習環境準備（00）](./00-create-project.md)で作成したMicrosoft Foundryプロジェクト
- Foundryプロジェクトに関連付けられたFoundryリソースを確認できるAzure権限
- このリポジトリをローカルに保存し、リポジトリのルートフォルダーをVisual Studio Codeで開いていること

> **重要**: この演習で使うのは、プロジェクトの管理に使う **Project endpoint** ではなく、Azure Languageを含むFoundryリソースの **サービス用エンドポイント** です。

## 演習

### Task 1: Azure Languageの接続情報を確認する

1. ブラウザーで [Microsoft Foundry](https://ai.azure.com) を開き、演習環境準備（00）で作成したプロジェクトを選択します。
1. プロジェクトの概要または管理画面で、プロジェクトが使用している **Foundryリソース** の名前とリソースグループを確認します。
1. [Azure portal](https://portal.azure.com) を別のタブで開きます。
1. 上部の検索欄にFoundryリソース名を入力し、対象リソースを開きます。
1. 左側のメニューで **リソース管理** > **キーとエンドポイント** を開きます。表示名はポータル更新により **キーとエンドポイント** または **Keys and Endpoint** の場合があります。
1. `KEY 1` とサービス用エンドポイントを一時的にメモします。エンドポイントは通常、次の形式です。

    ```text
    https://<リソース名>.cognitiveservices.azure.com/
    ```

次のようなProject endpointは、このプログラムには使用しません。

```text
https://<リソース名>.services.ai.azure.com/api/projects/<プロジェクト名>
```

Project endpointを指定すると、認証に成功してもLanguage APIのパスが存在せず、`404 Resource Not Found` になることがあります。

### Task 2: Python仮想環境を準備する

1. Visual Studio Codeで **ターミナル** > **新しいターミナル** を選択します。
1. ターミナル左側に `PS` と表示され、現在位置がリポジトリのルートであることを確認します。
1. 次のコマンドを1行ずつ実行します。

    ```powershell
    py -3.11 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    python -m pip install -r src\03c-text-analysis-sdk\requirements.txt
    ```

    コマンド先頭に `(.venv)` と表示されれば、仮想環境が有効です。

> **`py` が見つからない場合**: Python 3.11をインストールし、インストーラーの **Install launcher for all users** と **Add python.exe to PATH** を有効にします。会社管理PCでは講師に確認してください。

### Task 3: `.env` ファイルを設定する

1. 次のコマンドで設定例をコピーします。

    ```powershell
    Copy-Item src\03c-text-analysis-sdk\.env.example src\03c-text-analysis-sdk\.env
    ```

1. Visual Studio Codeで `src/03c-text-analysis-sdk/.env` を開きます。
1. Task 1で確認した値を設定します。`YOUR-...` を残さないでください。

    ```dotenv
    LANGUAGE_ENDPOINT=https://<リソース名>.cognitiveservices.azure.com
    LANGUAGE_KEY=<KEY 1の値>
    ```

1. ファイルを保存します。

`.env` は秘密情報を含むため、このリポジトリの `.gitignore` でGit管理から除外されています。画面共有、チャット、メール、提出物へキーを貼り付けないでください。

### Task 4: 入力データとstarterを確認する

1. [review.txt](../data/03c-text-analysis-sdk/review.txt)を開きます。
1. 肯定的な表現、否定的な表現、場所、人物名、メールアドレス、電話番号を探します。
1. [starterのtext_analysis_app.py](../src/03c-text-analysis-sdk/starter/text_analysis_app.py)を開きます。
1. 次の役割を持つ部分を確認します。

    - `load_settings`: `.env` から接続情報を読み込む
    - `read_review`: UTF-8テキストを読み込む
    - `create_client`: `TextAnalyticsClient`を作成する
    - `analyze_review`: これから完成させる分析処理
    - `save_report`: 日本語を保持したJSONを保存する
    - `main`: コマンドライン引数を受け取り、処理を順番に呼ぶ

### Task 5: 5種類の分析を実装する

starterの `analyze_review` 関数にある3行のコメントと `raise NotImplementedError(...)` を、次のコードで置き換えます。インデントは関数内の4文字分の空白を保ってください。

```python
    language_result = client.detect_language([text])[0]
    if language_result.is_error:
        raise RuntimeError(
            f"言語検出に失敗しました: {language_result.error.code}: "
            f"{language_result.error.message}"
        )
    language = language_result.primary_language
    language_code = language.iso6391_name

    sentiment = client.analyze_sentiment([text], language=language_code)[0]
    entities = client.recognize_entities([text], language=language_code)[0]
    key_phrases = client.extract_key_phrases([text], language=language_code)[0]
    pii = client.recognize_pii_entities([text], language=language_code)[0]

    for feature_name, result in (
        ("感情分析", sentiment),
        ("固有表現認識", entities),
        ("キーフレーズ抽出", key_phrases),
        ("PII検出", pii),
    ):
        if result.is_error:
            raise RuntimeError(
                f"{feature_name}に失敗しました: {result.error.code}: "
                f"{result.error.message}"
            )

    return {
        "language": {
            "name": language.name,
            "iso6391_name": language_code,
            "confidence_score": language.confidence_score,
        },
        "sentiment": {
            "label": sentiment.sentiment,
            "confidence_scores": {
                "positive": sentiment.confidence_scores.positive,
                "neutral": sentiment.confidence_scores.neutral,
                "negative": sentiment.confidence_scores.negative,
            },
        },
        "entities": [
            {
                "text": entity.text,
                "category": entity.category,
                "subcategory": entity.subcategory,
                "confidence_score": entity.confidence_score,
            }
            for entity in entities.entities
        ],
        "key_phrases": list(key_phrases.key_phrases),
        "pii_entities": [
            {
                "text": entity.text,
                "category": entity.category,
                "subcategory": entity.subcategory,
                "confidence_score": entity.confidence_score,
            }
            for entity in pii.entities
        ],
        "redacted_text": pii.redacted_text,
    }
```

`[text]` の角括弧は誤記ではありません。Text Analytics SDKは複数文書をまとめて処理できるため、1件のレビューもリストとして渡します。戻り値も文書ごとのリストなので、`[0]` で最初の結果を取得します。

### Task 6: プログラムを実行する

1. starterを実行します。

    ```powershell
    python src\03c-text-analysis-sdk\starter\text_analysis_app.py --input data\03c-text-analysis-sdk\review.txt
    ```

1. ターミナルにJSONが表示され、リポジトリのルートに `analysis-result.json` が作成されたことを確認します。
1. starterの編集でエラーが解消できない場合は、完成済みコードでも接続を確認できます。

    ```powershell
    python src\03c-text-analysis-sdk\solution\text_analysis_app.py --input data\03c-text-analysis-sdk\review.txt
    ```

1. 出力された `analysis-result.json` を開き、元の日本語が文字化けしていないことを確認します。

### Task 7: 結果を読み解く

- `language`: `ja` と検出されること、信頼度が表示されることを確認します。
- `sentiment`: 肯定と否定を含むため、結果や信頼度が一方に大きく偏らない場合があります。
- `entities`: 人物、場所、組織などの候補を確認します。すべての固有名詞が必ず抽出されるわけではありません。
- `key_phrases`: レビューの主要語句を確認します。
- `pii_entities`: 人物名、メール、電話番号などの検出候補を確認します。
- `redacted_text`: 検出されたPIIがマスク文字へ置き換わっていることを確認します。

## 実行結果例

サービスのモデル更新により、カテゴリや信頼度は例と異なる場合があります。

```json
{
  "language": {
    "name": "Japanese",
    "iso6391_name": "ja",
    "confidence_score": 1.0
  },
  "sentiment": {
    "label": "mixed",
    "confidence_scores": {
      "positive": 0.45,
      "neutral": 0.08,
      "negative": 0.47
    }
  },
  "key_phrases": [
    "リバーサイド東京",
    "Wi-Fi"
  ],
  "redacted_text": "先週、東京都内の架空のホテル…"
}
```

専用サービスと生成AIモデルには、次のような違いがあります。

| 観点 | Azure Language | 生成AIモデル |
|---|---|---|
| 呼び出し方 | 機能ごとのSDKメソッド | 自然言語プロンプト |
| 出力 | カテゴリ、信頼度、位置などの構造化結果 | 指示に応じた柔軟な文章やJSON |
| 再現性 | 同じ機能・入力では比較的一貫 | プロンプトや生成設定で変化しやすい |
| 適した用途 | 定型処理、PII検出、集計パイプライン | 要約、説明、複数タスクの柔軟な統合 |

## トラブルシューティング

### `401` または認証エラー

- `LANGUAGE_KEY` に余分な空白や引用符がないか確認します。
- キーとエンドポイントが同じFoundryリソースのものか確認します。
- キーを再生成した場合は `.env` も更新します。

### `404 Resource Not Found`

- `LANGUAGE_ENDPOINT` が `.cognitiveservices.azure.com` で終わるサービス用エンドポイントか確認します。
- `.services.ai.azure.com/api/projects/...` 形式のProject endpointを使用していないか確認します。
- エンドポイント末尾の `/` はプログラムが取り除きます。

### `429` または利用制限エラー

短時間の呼び出し回数、価格レベルの上限、リージョンのクォータを確認します。数十秒待ってから再実行し、研修で同じリソースを共有している場合は実行タイミングをずらします。

### 日本語が文字化けする

- 入力ファイルをVisual Studio Code右下の表示から **UTF-8** で保存します。
- PowerShellの表示だけが崩れる場合も、`analysis-result.json` をVisual Studio Codeで開いて確認します。

### 一部のPIIや固有表現が検出されない

AIの結果は完全ではありません。対象言語でその機能がサポートされているかを公式ドキュメントで確認し、業務利用時は信頼度、ルール、人による確認を組み合わせます。PII検出結果だけで安全性を保証しないでください。

## 後片付け

1. 秘密情報を含む `.env` と、生成したJSONを削除します。

    ```powershell
    Remove-Item src\03c-text-analysis-sdk\.env -ErrorAction SilentlyContinue
    Remove-Item analysis-result.json -ErrorAction SilentlyContinue
    ```

1. 続けて別の演習を行う場合、共有のFoundryリソースやプロジェクトは削除しません。
1. 研修全体を終了し、講師から削除を指示された場合だけ、演習環境準備（00）の手順に従ってリソースグループを削除します。

## AI-901 試験範囲との対応

この演習は、AI-901の「テキストを分析する軽量アプリケーションを作成する」に対応します。特に、言語検出、感情分析、固有表現認識、キーフレーズ抽出、PII検出、専用AIサービスのSDK利用、責任あるAIの確認を実践します。

## まとめ

Azure Language SDKを使うと、プレイグラウンドで確認したテキスト分析を定型プログラムへ組み込めます。接続情報と処理を分け、SDKのエラーを確認し、構造化結果をUTF-8 JSONへ保存しました。次に同様の考え方でAzure SpeechをPythonから利用します。

## 詳細を学ぶ

- [AI-901 Study Guide](https://learn.microsoft.com/credentials/certifications/resources/study-guides/ai-901)
- [Azure Languageの概要](https://learn.microsoft.com/azure/ai-services/language-service/overview)
- [Python用Text Analyticsクライアントライブラリ](https://learn.microsoft.com/python/api/overview/azure/ai-textanalytics-readme)
- [PIIの言語サポート](https://learn.microsoft.com/azure/ai-services/language-service/personally-identifiable-information/language-support)
- [PIIの透明性に関する情報](https://learn.microsoft.com/legal/cognitive-services/language-service/transparency-note-personally-identifiable-information)
