---
lab:
  title: Responses APIで画像分析アプリを作ろう
  description: 画像と指示をResponses APIへ送り、Pydanticで構造化された分析結果を取得します。
  level: 200
  duration: 40 minutes
  islab: true
  primarytopics:
    - Microsoft Foundry
    - Azure OpenAI
    - Python
---

# Responses APIで画像分析アプリを作ろう

この演習では、[05aの画像プレイグラウンド演習](./05a-image-analysis.md)で試したマルチモーダルモデルを、Pythonアプリへ組み込みます。画像をBase64 data URIへ変換し、OpenAI Python 2.xのResponses APIへ送信します。結果は自由文ではなく、Pydanticで定義した同じ形のJSONとして保存します。

作業時間の目安は **40分** です。

## 学習目標

- Foundryでモデルのデプロイ名、Azure OpenAI v1 endpoint、キーを確認する
- ローカル画像をBase64 data URIへ変換する
- Responses APIへテキストと画像を一緒に渡す
- Pydanticモデルを使ってStructured Outputsを取得する
- 未完了、refusal、解析結果欠落を区別する
- マルチモーダルLLMと専用物体検出モデルの用途を比較する

## 前提条件

- Windows 11、Visual Studio Code、PowerShell
- 64-bit版Python 3.11と、リポジトリ直下の `.venv`
- [演習環境準備（00）](./00-create-project.md)で作成したMicrosoft Foundryプロジェクト
- 画像入力とStructured Outputsに対応するモデルデプロイ
- 05aで使用した[images.zip](../data/05a-image-analysis/images.zip)

本手順ではデプロイ名の例として `gpt-5-mini` を使います。モデル名ではなく、Foundryで作成した **デプロイ名** を環境変数へ設定します。別モデルを使う場合は、画像入力とStructured Outputsの両方に対応していることをモデル詳細で確認してください。

## 演習

### Task 1: 画像を展開する

リポジトリのルートで次を実行します。

```powershell
Expand-Archive data\05a-image-analysis\images.zip -DestinationPath data\05a-image-analysis\extracted -Force
Get-ChildItem data\05a-image-analysis\extracted\images
```

`image1.png`、`image2.png`、`image3.png` が表示されます。まず `image1.png` を開き、画像に写っている物体、場面、文字、安全上気になる点を自分でメモしてください。後でモデルの結果と比較します。

### Task 2: モデルの接続情報を確認する

1. [Microsoft Foundry](https://ai.azure.com) を開き、演習環境準備（00）のプロジェクトを選択します。
1. 上部の **ビルド** を選択し、左側の **モデル** または **モデルとエンドポイント** を開きます。
1. 画像入力に対応したデプロイを選択します。既存の `gpt-5-mini` デプロイがある場合は再利用します。
1. **プレイグラウンドで開く** を選び、画像を1枚添付して短い質問を送ります。モデルが画像へ応答できることを確認します。
1. プレイグラウンドの **モデルを呼び出す** または **コードを表示** を選択します。
1. 次を選択します。

    - 言語: **Python**
    - SDK: **OpenAI SDK**
    - 認証方法: **Key authentication**

1. コード例から次の3項目を確認します。

    | 項目 | 例 |
    |---|---|
    | Azure OpenAI v1 base URL | `https://my-resource.openai.azure.com/openai/v1/` |
    | API key | リソースの秘密キー |
    | deployment name | `gpt-5-mini` |

> **区別してください**: `https://...services.ai.azure.com/api/projects/...` はFoundry Project endpointです。この演習の `OpenAI` クライアントには、`.openai.azure.com/openai/v1/` 形式のbase URLを使います。

画面構成が更新されてコード例を見つけにくい場合は、Azure portalでFoundryリソースの **キーとエンドポイント** を開きます。Azure OpenAI endpointへ `/openai/v1/` を付け、モデル画面で確認したデプロイ名と組み合わせます。

### Task 3: パッケージと `.env` を準備する

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r src\05b-vision-app\requirements.txt
Copy-Item src\05b-vision-app\.env.example src\05b-vision-app\.env
```

`src/05b-vision-app/.env` を開き、Task 2の値を設定します。

```dotenv
AZURE_OPENAI_BASE_URL=https://<リソース名>.openai.azure.com/openai/v1/
AZURE_OPENAI_API_KEY=<API key>
AZURE_OPENAI_DEPLOYMENT=gpt-5-mini
```

URL末尾の `/openai/v1/` を省略しないでください。API keyは画面共有、チャット、提出物へ含めません。

### Task 4: データ変換と出力モデルを確認する

[starterのvision_app.py](../src/05b-vision-app/starter/vision_app.py)を開きます。

`detect_media_type` は拡張子から `image/png` または `image/jpeg` を選びます。`encode_image` は画像のバイト列をBase64にし、次のようなdata URIへ変換します。

```text
data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...
```

Base64は暗号化ではありません。画像を文字としてAPI要求に含めるための表現です。

`VisionAnalysis` は結果の形を定義します。

```python
class VisionAnalysis(BaseModel):
    objects: list[str]
    scene: str
    text: list[str]
    safety_concern: str
```

この形を `text_format` に渡すと、SDKはJSON Schemaを作り、応答を検証済みのPydanticオブジェクトとして返します。

### Task 5: OpenAIクライアントを作成する

starterの `create_client` にあるコメントと `raise NotImplementedError(...)` を置き換えます。

```python
    from openai import OpenAI

    return OpenAI(
        base_url=settings.base_url,
        api_key=settings.api_key,
    )
```

従来のAzure専用クライアントではなく、OpenAI Python 2.xの `OpenAI` クライアントへAzure OpenAI v1 base URLを渡します。

### Task 6: 画像分析を実装する

starterの `analyze_image` にあるコメントと `raise NotImplementedError(...)` を次へ置き換えます。

```python
    image_data = encode_image(path)
    response = client.responses.parse(
        model=deployment,
        instructions=(
            "画像を観察し、見える物体、シーン、画像内の文字、安全上の懸念を"
            "日本語で整理してください。確認できない情報を推測せず、"
            "該当しない配列は空、文字列は空文字列にしてください。"
        ),
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "この画像を構造化して分析してください。",
                    },
                    {"type": "input_image", "image_url": image_data},
                ],
            }
        ],
        text_format=VisionAnalysis,
    )

    if response.status != "completed":
        raise RuntimeError(f"応答が完了しませんでした: {response.status}")

    for item in response.output or []:
        if getattr(item, "type", None) != "message":
            continue
        for content in getattr(item, "content", []):
            if getattr(content, "type", None) == "refusal":
                raise RuntimeError(
                    f"モデルが要求を拒否しました: {content.refusal}"
                )

    if response.output_parsed is None:
        raise RuntimeError("構造化された分析結果を取得できませんでした。")
    return response.output_parsed
```

- `instructions`: すべての要求に共通するモデルの役割と制約
- `input_text`: 今回の質問
- `input_image`: Base64 data URIにした画像
- `text_format`: 必要な結果構造
- `output_parsed`: 検証済みの `VisionAnalysis`

### Task 7: アプリを実行する

```powershell
python src\05b-vision-app\starter\vision_app.py --input data\05a-image-analysis\extracted\images\image1.png
```

編集で解決できない場合は、完成済みコードで接続を確認します。

```powershell
python src\05b-vision-app\solution\vision_app.py --input data\05a-image-analysis\extracted\images\image1.png
```

`vision-analysis.json` を開き、4項目が常に同じ構造で保存されていることを確認します。次に `image2.png` または `image3.png` を指定して比較します。

## 実行結果例

画像により内容は異なります。次は構造の例です。

```json
{
  "objects": [
    "食材",
    "調理器具"
  ],
  "scene": "キッチンの作業台に食材が並んでいます。",
  "text": [],
  "safety_concern": "画像だけでは衛生状態を確定できません。"
}
```

画像分析の方法は目的により選びます。

| 項目 | マルチモーダルLLM | 専用Object Detection |
|---|---|---|
| 出力 | 説明、意味、柔軟なJSON | ラベル、confidence、bounding box |
| 長所 | 幅広い画像質問に対応 | 位置情報が必要な処理に適する |
| 注意 | 位置を厳密に保証しない | 対応クラスやモデル準備が必要 |

この演習の `objects` は文章上の一覧であり、物体位置を示すbounding boxではありません。

## トラブルシューティング

### `/openai/v1/ 形式を指定` と表示される

- Azure OpenAI v1 base URLを使用します。
- Foundry Project endpointや `.cognitiveservices.azure.com` のURLを貼り付けていないか確認します。
- `https://` と末尾の `/openai/v1/` を確認します。

### `401` または認証エラー

base URLとAPI keyが同じリソースのものか確認します。キーを再生成した場合は `.env` を更新します。

### `404` またはDeploymentNotFound

`AZURE_OPENAI_DEPLOYMENT` にはモデルの製品名ではなく、Foundryで表示されるデプロイ名を設定します。作成直後は反映に時間がかかる場合があります。

### `400`、画像入力エラー、Structured Outputsエラー

- モデルデプロイが画像入力に対応しているか確認します。
- モデルとAPIがStructured Outputsに対応しているか確認します。
- 本編ではPNGまたはJPEGを使い、破損していない画像か開いて確認します。
- 大きすぎる画像は縮小し、必要な部分が読める解像度を保ちます。

### `429` または利用制限

リージョンのモデルクォータ、デプロイのレート制限、研修参加者の同時実行を確認します。少し待って再実行し、繰り返し発生する場合は講師がデプロイ設定を確認します。

### 内容が事実と違う、文字を誤読する

マルチモーダルモデルは画像にない情報を推測したり、小さい文字を誤読したりする場合があります。安全判断、本人確認、品質検査を自動確定せず、元画像と人による確認を残します。

## 後片付け

```powershell
Remove-Item src\05b-vision-app\.env -ErrorAction SilentlyContinue
Remove-Item vision-analysis.json -ErrorAction SilentlyContinue
```

`data/05a-image-analysis/extracted` は秘密情報を含まない教材画像ですが、ディスク容量を戻したい場合は削除できます。共有のFoundryリソースとモデルデプロイは、続く演習で使うため残します。

## AI-901 試験範囲との対応

この演習は、AI-901の「画像を分析する軽量アプリケーションを作成する」に対応します。画像入力、マルチモーダルモデル、構造化出力、専用Computer Visionとの使い分け、画像利用に関する責任あるAIを実践します。

## まとめ

画像をBase64 data URIとしてResponses APIへ送り、Pydanticで一定のJSON構造へ変換しました。柔軟な意味理解が必要な画像質問にはマルチモーダルLLMが役立ちますが、位置の厳密さや業務上の安全性が必要な場合は専用モデルと人の確認を組み合わせます。

## 詳細を学ぶ

- [AI-901 Study Guide](https://learn.microsoft.com/credentials/certifications/resources/study-guides/ai-901)
- [Azure OpenAI v1 API](https://learn.microsoft.com/azure/ai-foundry/openai/api-version-lifecycle)
- [OpenAI Python SDKをAzure OpenAIで使用する](https://learn.microsoft.com/azure/ai-foundry/openai/how-to/switching-endpoints)
- [画像入力を使用する](https://learn.microsoft.com/azure/ai-foundry/openai/how-to/gpt-with-vision)
- [Structured Outputs](https://learn.microsoft.com/azure/ai-foundry/openai/how-to/structured-outputs)
