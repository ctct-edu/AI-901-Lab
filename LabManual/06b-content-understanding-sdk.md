---
lab:
  title: Content Understanding SDKで情報抽出アプリを作ろう
  description: Pythonから請求書PDFと設備画像を分析し、構造化された業務データを抽出します。
  level: 200
  duration: 60 minutes
  islab: true
  primarytopics:
    - Azure Content Understanding
    - Microsoft Foundry
    - Python
---

# Content Understanding SDKで情報抽出アプリを作ろう

この演習では、[06aのContent Understandingプレイグラウンド演習](./06a-content-understanding.md)で確認した情報抽出をPythonアプリへ組み込みます。最初に組み込みの請求書アナライザーでPDFを処理し、次に研修用のカスタム画像アナライザーを作成して設備ラベルを処理します。

作業時間の目安は **60分** です。

## 学習目標

- GA版 `ContentUnderstandingClient` を作成する
- PDFとJPEGをバイナリデータとして送信する
- 長時間処理（LRO）のpollerで分析完了を待つ
- 組み込みアナライザーとカスタムアナライザーを使い分ける
- SDKのフィールド値をJSON互換の値へ変換する
- 整形結果と、confidence・sourceを含む生の結果を確認する
- カスタムアナライザーを安全に作成・削除する

## 前提条件

- Windows 11、Visual Studio Code、PowerShell
- 64-bit版Python 3.11と、リポジトリ直下の `.venv`
- [演習環境準備（00）](./00-create-project.md)で作成したMicrosoft Foundryリソース
- [06a](./06a-content-understanding.md)を完了し、Content Understandingで利用する補完モデルと埋め込みモデルを構成済みであること
- Content Understanding対応リージョンのリソース。本教材では **East US** を基準にします
- Foundryリソースのキーを確認できるAzure権限

> **本編のバージョン**: `azure-ai-contentunderstanding` **1.1系** とGA API **2025-11-01** を使用します。新しいFoundryプレイグラウンドは時期により `2026-06-01-preview` を使う場合があり、画面の項目や生のJSONが本編SDKと異なることがあります。Preview SDKの例を本編コードへ混ぜないでください。

## 演習

### Task 1: 請求書PDFを展開する

リポジトリのルートで次を実行します。

```powershell
Expand-Archive data\06a-content-understanding\contoso-invoice-1.zip -DestinationPath data\06a-content-understanding\extracted -Force
Test-Path data\06a-content-understanding\extracted\contoso-invoice-1.pdf
```

`True` と表示されることを確認します。PDFを開き、仕入先名、請求書番号、日付、合計、明細が含まれていることを目視します。

### Task 2: Foundryリソースの接続情報を確認する

1. [Microsoft Foundry](https://ai.azure.com) で演習プロジェクトを開き、関連付けられたFoundryリソースの名前とリソースグループを確認します。
1. [Azure portal](https://portal.azure.com) でそのFoundryリソースを開きます。
1. **リソース管理** > **キーとエンドポイント** を開きます。
1. `KEY 1` とFoundryリソースのエンドポイントを確認します。

正しいエンドポイントは次の形式です。

```text
https://<リソース名>.services.ai.azure.com/
```

次のProject endpointは使用しません。

```text
https://<リソース名>.services.ai.azure.com/api/projects/<プロジェクト名>
```

Content UnderstandingはFoundry **リソース** に対して呼び出します。`/api/projects/` を含むURLを指定すると、アナライザーAPIへ正しく到達できません。

### Task 3: パッケージと `.env` を準備する

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r src\06b-content-understanding-sdk\requirements.txt
Copy-Item src\06b-content-understanding-sdk\.env.example src\06b-content-understanding-sdk\.env
```

`src/06b-content-understanding-sdk/.env` を開きます。

```dotenv
CONTENTUNDERSTANDING_ENDPOINT=https://<リソース名>.services.ai.azure.com/
CONTENTUNDERSTANDING_KEY=<KEY 1の値>
CONTENTUNDERSTANDING_IMAGE_ANALYZER_ID=ai901-equipment-analyzer
CONTENTUNDERSTANDING_COMPLETION_MODEL=gpt-5.2
```

- `CONTENTUNDERSTANDING_IMAGE_ANALYZER_ID` はリソース内で一意にします。共有環境では講師が指定した接頭辞や受講者番号を付けてください。
- `CONTENTUNDERSTANDING_COMPLETION_MODEL` は **モデルのデプロイ名ではなく、Content Understandingが要求する対応モデル名** です。本教材の確認時点では `gpt-5.2` を例にしています。提供前と実施前に公式の対応モデル一覧を確認し、06aで構成した対応モデルへ合わせます。
- `gpt-5-mini` をContent Understanding用モデルとして無条件に流用しないでください。

### Task 4: SDKクライアントとLROを確認する

[starterのcontent_understanding_app.py](../src/06b-content-understanding-sdk/starter/content_understanding_app.py)を開きます。

`create_client` では次の3点を指定済みです。

- Foundryリソースのendpoint
- `AzureKeyCredential`にしたキー
- GA APIバージョン `2025-11-01`

Content Understandingの分析は処理時間が一定ではないため、呼び出し直後に最終結果を返さず、**poller** を返します。`poller.result()` はサービス側の処理が終わるまで待ち、成功時に `AnalysisResult` を返します。

starterの `analyze_binary_file` にあるコメントと `raise NotImplementedError(...)` を次へ置き換えます。

```python
    content_type = detect_content_type(path)
    poller = client.begin_analyze_binary(
        analyzer_id,
        path.read_bytes(),
        content_type=content_type,
    )
    return poller.result(), poller.operation_id
```

`content_type` を正しく付けることで、PDF、PNG、JPEGを同じ関数から送信できます。`operation_id` は問い合わせや問題調査で処理を識別するために役立ちます。秘密キーではありません。

### Task 5: 請求書フィールドを整形する

`format_invoice_result` のコメントと `raise NotImplementedError(...)` を次へ置き換えます。

```python
    fields = _fields(result)
    return {
        "vendor": _value(fields, "VendorName", "Vendor"),
        "invoice_number": _value(fields, "InvoiceId", "InvoiceNumber"),
        "invoice_date": _value(fields, "InvoiceDate"),
        "total": _value(fields, "InvoiceTotal", "Total"),
        "items": _value(fields, "Items") or [],
    }
```

組み込みアナライザーのフィールド名を、アプリで使いやすい小文字の名前へ変えています。見つからない項目は例外にせず `null`、明細は空配列にします。実務では欠損項目を人の確認キューへ送る処理を追加します。

### Task 6: 請求書を分析する

```powershell
python src\06b-content-understanding-sdk\starter\content_understanding_app.py invoice --input data\06a-content-understanding\extracted\contoso-invoice-1.pdf
```

編集でエラーが解消できない場合は、完成済みコードで接続を確認します。

```powershell
python src\06b-content-understanding-sdk\solution\content_understanding_app.py invoice --input data\06a-content-understanding\extracted\contoso-invoice-1.pdf
```

処理には数十秒以上かかることがあります。ターミナルを閉じずに待ちます。完了すると次が作成されます。

- `content-understanding-invoice.json`: 主要業務フィールドだけの整形結果
- `content-understanding-invoice-raw.json`: SDK応答全体をJSON互換にした結果

### Task 7: 設備ラベルとスキーマを確認する

1. [equipment-label.jpg](../data/06b-content-understanding-sdk/equipment-label.jpg)を開きます。
1. `CONTOSO INDUSTRIAL`、`MX-200`、`CT-2026-00125`、`HIGH VOLTAGE - DO NOT OPEN` が読めることを確認します。すべて架空の教材データです。
1. [image-analyzer-schema.json](../src/06b-content-understanding-sdk/image-analyzer-schema.json)を開きます。

`baseAnalyzerId` は `prebuilt-image`、`fieldSchema.fields` には次の4項目があります。

- `manufacturer`
- `model`
- `serial_number`
- `warning`

`models.completion` は、アナライザー作成時に `.env` の値で置き換えられます。

### Task 8: カスタム画像アナライザーを作成する

完成済みの[setup_image_analyzer.py](../src/06b-content-understanding-sdk/setup_image_analyzer.py)を実行します。

```powershell
python src\06b-content-understanding-sdk\setup_image_analyzer.py --create
```

スクリプトは `begin_create_analyzer(..., allow_replace=True)` を呼び、pollerで作成完了を待ちます。同じIDがある場合は置き換えます。共有リソースでは他の受講者のIDを指定しないでください。

### Task 9: 設備フィールドを整形する

starterの `format_equipment_result` のコメントと `raise NotImplementedError(...)` を次へ置き換えます。

```python
    fields = _fields(result)
    return {
        "manufacturer": _value(fields, "manufacturer"),
        "model": _value(fields, "model"),
        "serial_number": _value(fields, "serial_number"),
        "warning": _value(fields, "warning"),
    }
```

### Task 10: 設備画像を分析する

```powershell
python src\06b-content-understanding-sdk\starter\content_understanding_app.py equipment --input data\06b-content-understanding-sdk\equipment-label.jpg
```

完成済みコードで確認する場合は次を実行します。

```powershell
python src\06b-content-understanding-sdk\solution\content_understanding_app.py equipment --input data\06b-content-understanding-sdk\equipment-label.jpg
```

整形結果とraw JSONを開きます。raw JSON内で各フィールドの `confidence` と `source` を探します。

- `confidence`: モデルが抽出結果をどの程度確からしいと評価したか
- `source`: 元コンテンツのどこを根拠にしたかを示す情報

信頼度は正しさの保証ではありません。元画像を表示できるレビュー画面と組み合わせます。

### 発展課題: 音声・動画へ広げる

Content Understandingはドキュメントと画像だけでなく、音声と動画も同じ長時間処理の考え方で扱えます。対応する `prebuilt-audioSearch`、`prebuilt-videoSearch`、またはカスタムアナライザーを選び、`begin_analyze_binary` へ対応形式を送ります。

本編へ含めない理由は、音声・動画は処理時間、入力サイズ、費用が増えやすく、録音への同意や動画内の顔・会話・位置情報の管理も必要になるためです。発展実装前に、最新の対応形式、サイズ、時間上限、リージョンを公式ドキュメントで確認してください。

## 実行結果例

請求書の整形結果例:

```json
{
  "vendor": "CONTOSO LTD.",
  "invoice_number": "1",
  "invoice_date": "2019-11-15",
  "total": 610.0,
  "items": []
}
```

設備画像の整形結果例:

```json
{
  "manufacturer": "CONTOSO INDUSTRIAL",
  "model": "MX-200",
  "serial_number": "CT-2026-00125",
  "warning": "HIGH VOLTAGE - DO NOT OPEN"
}
```

モデル更新や入力品質により、文字の大小、空白、項目の有無は変わる場合があります。

## トラブルシューティング

### Foundryリソースのendpointエラー

- `.services.ai.azure.com/` 形式か確認します。
- `/api/projects/` を含むProject endpointを使っていないか確認します。
- endpointとキーが同じFoundryリソースのものか確認します。

### `403` Forbidden

本編のキー認証では、有効なリソースキーか、ローカルポリシーでキー認証が無効化されていないかを確認します。Entra ID認証へ変更した場合は、実行ユーザーまたはマネージドIDに **Cognitive Services User** など必要なロールがあるか確認します。キー認証とEntra ID認証の問題を混同しないでください。

### リージョンまたは機能がサポートされない

Content Understandingの利用可能リージョンを確認します。本教材はEast USを基準にしています。別リージョンの既存リソースで利用できない場合は、講師の指示なく新しい課金リソースを作らないでください。

### アナライザー作成でモデルエラーになる

- 06aでContent Understanding用の補完モデルと埋め込みモデルを構成したか確認します。
- `.env` の補完モデルが公式の対応モデル一覧にあるか確認します。
- モデルのリージョン、デプロイ、クォータ、廃止予定を確認します。
- ポータルのPreview例をGA 1.1 SDKへそのままコピーしていないか確認します。

### AnalyzerNotFound

`CONTENTUNDERSTANDING_IMAGE_ANALYZER_ID` と `--create` で作ったIDが一致しているか確認します。作成が完了してから分析します。請求書は `prebuilt-invoice` を使うため、カスタムIDは不要です。

### ファイル形式、サイズ、LROエラー

本編ではPDF、PNG、JPEGだけを受け付けます。ファイルが破損していないか開いて確認し、最新のサービス制限内か確認します。LROが失敗した場合は、表示されたoperation ID、時刻、リージョン、analyzer IDを記録します。秘密キーや入力内の個人情報はエラー報告へ含めません。

### フィールドが `null` または誤っている

元データの画質、向き、文字サイズ、フィールド説明を確認します。confidenceが高くても正しいとは限らないため、重要項目はsourceと原本を人が確認します。

## 後片付け

1. 自分が作成したカスタム画像アナライザーを削除します。

    ```powershell
    python src\06b-content-understanding-sdk\setup_image_analyzer.py --delete
    ```

1. 秘密情報と生成JSONを削除します。

    ```powershell
    Remove-Item src\06b-content-understanding-sdk\.env -ErrorAction SilentlyContinue
    Remove-Item content-understanding-*.json -ErrorAction SilentlyContinue
    ```

1. 共有のFoundryリソース、06aで構成したモデル、リソースグループは削除しません。

## AI-901 試験範囲との対応

この演習は、AI-901の次の要件に対応します。

- Azure Content Understandingでドキュメントやフォームから情報を抽出する
- Content Understandingで画像から情報を抽出する
- 音声・動画の情報抽出方法を説明する
- 情報抽出機能を含む軽量アプリケーションを作成する
- confidence、source grounding、人による確認を組み合わせる

## まとめ

GA 1.1系のContent Understanding SDKから、組み込み請求書アナライザーとカスタム画像アナライザーを利用しました。pollerで完了を待ち、SDK固有の型をJSONへ変換し、業務用の整形結果と監査用のraw結果を分けて保存しました。カスタムアナライザーは演習後に削除し、共有リソースは残しました。

## 詳細を学ぶ

- [AI-901 Study Guide](https://learn.microsoft.com/credentials/certifications/resources/study-guides/ai-901)
- [Azure Content Understandingの概要](https://learn.microsoft.com/azure/ai-services/content-understanding/overview)
- [Python用Content Understandingクライアントライブラリ](https://learn.microsoft.com/python/api/overview/azure/ai-contentunderstanding-readme)
- [組み込みアナライザー](https://learn.microsoft.com/azure/ai-services/content-understanding/concepts/prebuilt-analyzers)
- [サービスの制限とリージョン](https://learn.microsoft.com/azure/ai-services/content-understanding/service-limits)
