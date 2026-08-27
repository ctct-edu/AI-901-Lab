---
lab:
  title: Python SDKで音声を認識・合成しよう
  description: Azure Speech SDKを使い、WAVの音声認識と日本語音声合成を実装します。
  level: 200
  duration: 40 minutes
  islab: true
  primarytopics:
    - Microsoft Foundry
    - Azure Speech
    - Python
---

# Python SDKで音声を認識・合成しよう

この演習では、[04aの音声プレイグラウンド演習](./04a-speech.md)から一歩進み、Azure Speech SDKをPythonプログラムから利用します。用意された短いWAVファイルをテキストへ変換し、任意の日本語から別のWAVファイルを作成します。

作業時間の目安は **40分** です。

## 学習目標

- Azure Speechで使用するキーとリージョンを安全に設定する
- 音声認識（Speech to Text）でWAVをテキストへ変換する
- 音声合成（Text to Speech）で日本語WAVを作成する
- `ResultReason`、`NoMatch`、`Canceled`を使って結果を判定する
- 音声の形式、言語、マイク、認証の問題を切り分ける
- 録音データを扱う際の同意、保管、削除の必要性を説明する

## 前提条件

- Windows 11、Visual Studio Code、PowerShell
- 64-bit版Python 3.11
- [演習環境準備（00）](./00-create-project.md)で作成したMicrosoft Foundryプロジェクト
- Foundryリソースのキーとリージョンを確認できるAzure権限

## 演習

### Task 1: Speechの接続情報を確認する

1. [Azure portal](https://portal.azure.com) を開きます。
1. 演習環境準備（00）で作成したプロジェクトに関連付けられたFoundryリソースを開きます。
1. **リソース管理** > **キーとエンドポイント** を開き、`KEY 1` と **場所/リージョン** を確認します。
1. ポータル表示とSDK設定の違いを確認します。

    | ポータルの表示例 | `.env` に書く値 |
    |---|---|
    | East US | `eastus` |
    | West US 3 | `westus3` |
    | Japan East | `japaneast` |

このアプリは `SpeechConfig(subscription=..., region=...)` を使います。Speechには音声認識用・音声合成用のRESTエンドポイントもありますが、機能やリージョンによってパスが異なります。初心者が誤ったURLを組み立てるのを避けるため、本編では共通の **キーとリージョン** をSDKへ渡し、SDKに接続先を選ばせます。

### Task 2: パッケージと設定ファイルを準備する

1. リポジトリのルートで仮想環境を有効にします。

    ```powershell
    .\.venv\Scripts\Activate.ps1
    python -m pip install -r src\04b-speech-sdk\requirements.txt
    Copy-Item src\04b-speech-sdk\.env.example src\04b-speech-sdk\.env
    ```

1. `src/04b-speech-sdk/.env` を開き、値を設定します。

    ```dotenv
    SPEECH_KEY=<KEY 1の値>
    SPEECH_REGION=eastus
    SPEECH_RECOGNITION_LANGUAGE=ja-JP
    SPEECH_VOICE=ja-JP-NanamiNeural
    ```

    `SPEECH_REGION` は自分のリソースのリージョンへ変更してください。キーを引用符で囲む必要はありません。

### Task 3: 入力WAVとstarterを確認する

1. [ai-introduction.wav](../data/04b-speech-sdk/ai-introduction.wav)をWindowsのメディアプレーヤーで再生します。
1. 約15秒の日本語音声であることを確認します。このファイルは、研修用の架空原稿を音声合成して作ったものです。
1. [starterのspeech_app.py](../src/04b-speech-sdk/starter/speech_app.py)を開きます。
1. `Settings` にはキー、リージョン、認識言語、合成音声がまとめられています。
1. `create_speech_config` では1つの設定を認識と合成の両方に使います。

入力は **モノラル、16 kHz、16-bit PCMのWAV** です。`recognize_once_async()` は1回の短い発話を認識する用途に向き、長時間音声や連続会話には別の認識方式を使用します。

### Task 4: WAVの音声認識を実装する

starterの `transcribe_file` 関数内にあるコメントと `raise NotImplementedError(...)` を次のコードへ置き換えます。

```python
    path = validate_audio_path(path)
    if speech_module is None:
        import azure.cognitiveservices.speech as speech_module

    audio = speech_module.audio.AudioConfig(filename=str(path))
    recognizer = speech_module.SpeechRecognizer(
        speech_config=config,
        audio_config=audio,
    )
    result = recognizer.recognize_once_async().get()

    if result.reason == speech_module.ResultReason.RecognizedSpeech:
        return result.text
    if result.reason == speech_module.ResultReason.NoMatch:
        raise RuntimeError(
            "音声を認識できませんでした。言語設定と音声品質を確認してください。"
        )

    details = speech_module.CancellationDetails(result)
    raise RuntimeError(
        f"音声認識がキャンセルされました: {details.reason}; "
        f"{details.error_details}"
    )
```

`ResultReason` は処理結果の種類です。

- `RecognizedSpeech`: 音声を認識し、`result.text` を利用できる
- `NoMatch`: 音声は処理したが、認識できる発話が見つからない
- `Canceled`: 認証、ネットワーク、サービス側処理などで中止された

### Task 5: 音声認識を実行する

```powershell
python src\04b-speech-sdk\starter\speech_app.py transcribe --input data\04b-speech-sdk\ai-introduction.wav
```

うまくいかない場合は、完成済みコードで接続と入力を確認します。

```powershell
python src\04b-speech-sdk\solution\speech_app.py transcribe --input data\04b-speech-sdk\ai-introduction.wav
```

句読点や表記は元原稿と完全には一致しない場合があります。音声認識は音を文字列として推定しているためです。

### Task 6: 日本語の音声合成を実装する

starterの `synthesize_text` 関数内にあるコメントと `raise NotImplementedError(...)` を次のコードへ置き換えます。

```python
    if not text.strip():
        raise ValueError("読み上げるテキストを入力してください。")
    if speech_module is None:
        import azure.cognitiveservices.speech as speech_module

    output_path.parent.mkdir(parents=True, exist_ok=True)
    audio = speech_module.audio.AudioOutputConfig(filename=str(output_path))
    synthesizer = speech_module.SpeechSynthesizer(
        speech_config=config,
        audio_config=audio,
    )
    result = synthesizer.speak_text_async(text).get()

    if result.reason == speech_module.ResultReason.SynthesizingAudioCompleted:
        return output_path.resolve()

    detail_type = speech_module.SpeechSynthesisCancellationDetails
    details = (
        detail_type.from_result(result)
        if hasattr(detail_type, "from_result")
        else detail_type(result)
    )
    raise RuntimeError(
        f"音声合成がキャンセルされました: {details.reason}; "
        f"{details.error_details}"
    )
```

### Task 7: 音声合成を実行する

1. 次のコマンドを実行します。

    ```powershell
    python src\04b-speech-sdk\starter\speech_app.py synthesize --text "AIの出力は人が確認してから利用しましょう。" --output output.wav
    ```

1. リポジトリのルートに作成された `output.wav` を再生します。
1. `ja-JP-NanamiNeural` の日本語音声で読み上げられることを確認します。
1. 別の短い文章でも試します。個人情報や社外秘を入力しないでください。

## 実行結果例

音声認識:

```text
認識結果: 人工知能は画像や文章、音声などの情報から特徴を見つけ、人の判断を支援します。AIの出力は目的に合っているかを人が確認してから利用しましょう。
```

音声合成:

```text
音声を保存しました: C:\training\AI-901-Lab\output.wav
```

実際の認識文、句読点、絶対パスは環境によって異なります。

## トラブルシューティング

### 音声ファイルが見つからない

ターミナルがリポジトリのルートにあるか確認します。`Get-Location` で現在位置、`Test-Path data\04b-speech-sdk\ai-introduction.wav` でファイルを確認できます。

### `本編では16-bit PCM WAV` と表示される

MP3やM4Aを拡張子だけ変更してもWAVにはなりません。用意されたWAVを使います。独自音声を使う場合は、モノラルの16-bit PCM WAVへ正しく変換します。

### `NoMatch` または音声を認識できない

- `SPEECH_RECOGNITION_LANGUAGE=ja-JP` を確認します。
- 音量が小さすぎないか、無音が長すぎないか確認します。
- 日本語以外を認識する場合は、音声に合うロケールへ変更します。

### 認証エラーまたはCanceled

- `SPEECH_KEY` と `SPEECH_REGION` が同じFoundryリソースのものか確認します。
- `East US` を `eastus` のようなリージョン識別子にします。
- プロキシやファイアウォールでSpeechサービスへの通信が遮断されていないか確認します。
- `error_details` に表示される内容を確認します。キー自体はエラー報告へ貼り付けません。

## AI-901 試験範囲との対応

この演習は、AI-901の「音声を分析する軽量アプリケーションを作成する」に対応します。音声認識、音声合成、言語と音声の選択、SDK結果の判定、音声データの責任ある取り扱いを実践します。

## まとめ

Azure Speech SDKでは、同じ `SpeechConfig` を使って音声認識と音声合成を実装できます。成功、認識不成立、キャンセルを区別することで、利用者が原因を判断できるアプリになりました。次の演習では、画像をResponses APIへ送り、構造化された結果を取得します。

## 詳細を学ぶ

- [AI-901 Study Guide](https://learn.microsoft.com/credentials/certifications/resources/study-guides/ai-901)
- [Speech SDKの概要](https://learn.microsoft.com/azure/ai-services/speech-service/speech-sdk)
- [Pythonで音声をテキストへ変換する](https://learn.microsoft.com/azure/ai-services/speech-service/get-started-speech-to-text)
- [Pythonでテキストを音声へ変換する](https://learn.microsoft.com/azure/ai-services/speech-service/get-started-text-to-speech)
- [言語と音声のサポート](https://learn.microsoft.com/azure/ai-services/speech-service/language-support)
