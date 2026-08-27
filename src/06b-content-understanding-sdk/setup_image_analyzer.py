from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence


MODULE_DIR = Path(__file__).resolve().parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from solution.content_understanding_app import create_client, load_settings


DEFAULT_SCHEMA = MODULE_DIR / "image-analyzer-schema.json"


def load_schema(path: Path, completion_model: str) -> dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(f"スキーマファイルが見つかりません: {path}")
    schema = json.loads(path.read_text(encoding="utf-8"))
    if schema.get("baseAnalyzerId") != "prebuilt-image":
        raise ValueError("画像アナライザーはprebuilt-imageを基にしてください。")
    models = schema.setdefault("models", {})
    if not isinstance(models, dict):
        raise ValueError("スキーマのmodelsはJSONオブジェクトにしてください。")
    models["completion"] = completion_model
    return schema


def create_analyzer(
    client,
    analyzer_id: str,
    schema: dict[str, object],
):
    poller = client.begin_create_analyzer(
        analyzer_id,
        schema,
        allow_replace=True,
    )
    return poller.result()


def delete_analyzer(client, analyzer_id: str) -> None:
    client.delete_analyzer(analyzer_id)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="研修用の設備ラベル画像アナライザーを作成または削除します。"
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--create", action="store_true", help="作成または置換します。")
    action.add_argument("--delete", action="store_true", help="削除します。")
    parser.add_argument(
        "--analyzer-id",
        help=(
            "アナライザーID。省略時は"
            "CONTENTUNDERSTANDING_IMAGE_ANALYZER_IDを使います。"
        ),
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA,
        help=f"作成用JSONスキーマ（既定: {DEFAULT_SCHEMA}）",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    client = None
    try:
        settings = load_settings()
        analyzer_id = args.analyzer_id or settings.image_analyzer_id
        if not analyzer_id:
            raise ValueError(
                "--analyzer-idまたは"
                "CONTENTUNDERSTANDING_IMAGE_ANALYZER_IDを設定してください。"
            )
        client = create_client(settings)
        if args.create:
            schema = load_schema(args.schema, settings.completion_model)
            create_analyzer(client, analyzer_id, schema)
            print(f"アナライザーを作成しました: {analyzer_id}")
        else:
            delete_analyzer(client, analyzer_id)
            print(f"アナライザーを削除しました: {analyzer_id}")
        return 0
    except Exception as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())
