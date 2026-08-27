from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    key: str
    region: str
    recognition_language: str = "ja-JP"
    voice: str = "ja-JP-NanamiNeural"


def load_settings(environment: Mapping[str, str] | None = None) -> Settings:
    if environment is None:
        load_dotenv()
        environment = os.environ
    missing = [
        name
        for name in ("SPEECH_KEY", "SPEECH_REGION")
        if not environment.get(name)
    ]
    if missing:
        raise ValueError(f"環境変数が設定されていません: {', '.join(missing)}")
    return Settings(
        key=environment["SPEECH_KEY"],
        region=environment["SPEECH_REGION"].strip().lower().replace(" ", ""),
        recognition_language=environment.get(
            "SPEECH_RECOGNITION_LANGUAGE", "ja-JP"
        ),
        voice=environment.get("SPEECH_VOICE", "ja-JP-NanamiNeural"),
    )


def validate_audio_path(path: Path) -> Path:
    if not path.is_file():
        raise FileNotFoundError(f"音声ファイルが見つかりません: {path}")
    if path.suffix.lower() != ".wav":
        raise ValueError("本編では16-bit PCM WAVファイルを指定してください。")
    return path


def create_speech_config(settings: Settings, speech_module=None):
    if speech_module is None:
        import azure.cognitiveservices.speech as speech_module
    config = speech_module.SpeechConfig(
        subscription=settings.key,
        region=settings.region,
    )
    config.speech_recognition_language = settings.recognition_language
    config.speech_synthesis_voice_name = settings.voice
    return config


def transcribe_file(config, path: Path, speech_module=None) -> str:
    # 演習: WAV用AudioConfigとSpeechRecognizerを作成します。
    # 演習: recognize_once_async().get() のResultReasonを判定します。
    raise NotImplementedError("LabManualの音声認識手順を完成させてください。")


def synthesize_text(
    config,
    text: str,
    output_path: Path,
    speech_module=None,
) -> Path:
    # 演習: 空文字を検証し、AudioOutputConfigとSpeechSynthesizerを作成します。
    # 演習: speak_text_async(text).get() のResultReasonを判定します。
    raise NotImplementedError("LabManualの音声合成手順を完成させてください。")


def transcribe_microphone(config, speech_module=None) -> str:
    if speech_module is None:
        import azure.cognitiveservices.speech as speech_module
    audio = speech_module.audio.AudioConfig(use_default_microphone=True)
    recognizer = speech_module.SpeechRecognizer(
        speech_config=config,
        audio_config=audio,
    )
    result = recognizer.recognize_once_async().get()
    if result.reason == speech_module.ResultReason.RecognizedSpeech:
        return result.text
    if result.reason == speech_module.ResultReason.NoMatch:
        raise RuntimeError("音声を認識できませんでした。")
    details = speech_module.CancellationDetails(result)
    raise RuntimeError(
        f"音声認識がキャンセルされました: {details.reason}; "
        f"{details.error_details}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Azure Speech SDKで音声認識と音声合成を実行します。"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    transcribe_parser = subparsers.add_parser("transcribe")
    transcribe_parser.add_argument("--input", type=Path, required=True)
    synthesize_parser = subparsers.add_parser("synthesize")
    synthesize_parser.add_argument("--text", required=True)
    synthesize_parser.add_argument(
        "--output", type=Path, default=Path("output.wav")
    )
    subparsers.add_parser("microphone")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        settings = load_settings()
        config = create_speech_config(settings)
        if args.command == "transcribe":
            print(f"認識結果: {transcribe_file(config, args.input)}")
        elif args.command == "synthesize":
            output_path = synthesize_text(config, args.text, args.output)
            print(f"音声を保存しました: {output_path}")
        else:
            print("マイクに向かって短く話してください。")
            print(f"認識結果: {transcribe_microphone(config)}")
        return 0
    except Exception as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
