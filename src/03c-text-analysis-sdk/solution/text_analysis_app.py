from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from dotenv import load_dotenv


DEFAULT_INPUT = Path("data/03c-text-analysis-sdk/review.txt")
DEFAULT_OUTPUT = Path("analysis-result.json")


@dataclass(frozen=True)
class Settings:
    endpoint: str
    key: str


def load_settings(environment: Mapping[str, str] | None = None) -> Settings:
    if environment is None:
        load_dotenv()
        environment = os.environ
    missing = [
        name
        for name in ("LANGUAGE_ENDPOINT", "LANGUAGE_KEY")
        if not environment.get(name)
    ]
    if missing:
        raise ValueError(f"環境変数が設定されていません: {', '.join(missing)}")
    return Settings(
        endpoint=environment["LANGUAGE_ENDPOINT"].rstrip("/"),
        key=environment["LANGUAGE_KEY"],
    )


def read_review(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {path}")
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"入力ファイルが空です: {path}")
    return text


def create_client(settings: Settings):
    from azure.ai.textanalytics import TextAnalyticsClient
    from azure.core.credentials import AzureKeyCredential

    return TextAnalyticsClient(
        endpoint=settings.endpoint,
        credential=AzureKeyCredential(settings.key),
    )


def _document(response, feature_name: str):
    document = response[0]
    if document.is_error:
        raise RuntimeError(
            f"{feature_name}に失敗しました: "
            f"{document.error.code}: {document.error.message}"
        )
    return document


def analyze_review(client, text: str) -> dict[str, object]:
    language_doc = _document(client.detect_language([text]), "言語検出")
    language = language_doc.primary_language
    language_code = language.iso6391_name

    sentiment = _document(
        client.analyze_sentiment([text], language=language_code),
        "感情分析",
    )
    entities = _document(
        client.recognize_entities([text], language=language_code),
        "固有表現認識",
    )
    key_phrases = _document(
        client.extract_key_phrases([text], language=language_code),
        "キーフレーズ抽出",
    )
    pii = _document(
        client.recognize_pii_entities([text], language=language_code),
        "PII検出",
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


def save_report(report: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Azure Language SDKでレビューを分析します。"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"分析するUTF-8テキスト（既定: {DEFAULT_INPUT}）",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"JSONの保存先（既定: {DEFAULT_OUTPUT}）",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    client = None
    try:
        settings = load_settings()
        review = read_review(args.input)
        client = create_client(settings)
        report = analyze_review(client, review)
        save_report(report, args.output)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        print(f"\n保存先: {args.output.resolve()}")
        return 0
    except Exception as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())
