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


def analyze_review(client, text: str) -> dict[str, object]:
    # 演習: 言語検出を呼び出し、言語コードを取り出します。
    # 演習: 感情分析、固有表現認識、キーフレーズ抽出、PII検出を呼び出します。
    # 演習: 各応答の is_error を確認し、結果を辞書にまとめます。
    raise NotImplementedError("LabManualの手順に沿って analyze_review を完成させてください。")


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
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
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
