from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Sequence, TypeAlias

from dotenv import load_dotenv


JSONScalar: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]


@dataclass(frozen=True)
class Settings:
    endpoint: str
    key: str
    image_analyzer_id: str | None = None
    completion_model: str = "gpt-5.2"


def load_settings(environment: Mapping[str, str] | None = None) -> Settings:
    if environment is None:
        load_dotenv()
        environment = os.environ
    required = ("CONTENTUNDERSTANDING_ENDPOINT", "CONTENTUNDERSTANDING_KEY")
    missing = [name for name in required if not environment.get(name)]
    if missing:
        raise ValueError(f"環境変数が設定されていません: {', '.join(missing)}")
    endpoint = environment["CONTENTUNDERSTANDING_ENDPOINT"].rstrip("/") + "/"
    if "/api/projects/" in endpoint.lower() or not re.fullmatch(
        r"https://[^/]+\.services\.ai\.azure\.com/",
        endpoint,
        re.IGNORECASE,
    ):
        raise ValueError(
            "CONTENTUNDERSTANDING_ENDPOINTにはFoundryリソースの "
            "https://<resource>.services.ai.azure.com/ を指定してください。"
        )
    image_analyzer_id = environment.get("CONTENTUNDERSTANDING_IMAGE_ANALYZER_ID")
    return Settings(
        endpoint=endpoint,
        key=environment["CONTENTUNDERSTANDING_KEY"],
        image_analyzer_id=image_analyzer_id or None,
        completion_model=environment.get(
            "CONTENTUNDERSTANDING_COMPLETION_MODEL", "gpt-5.2"
        ),
    )


def to_json_compatible(value) -> JSONValue:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if hasattr(value, "as_dict"):
        return to_json_compatible(value.as_dict())
    if isinstance(value, Mapping):
        return {
            str(key): to_json_compatible(item) for key, item in value.items()
        }
    if isinstance(value, Iterable) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        return [to_json_compatible(item) for item in value]
    if hasattr(value, "value"):
        return to_json_compatible(value.value)
    return str(value)


def detect_content_type(path: Path) -> str:
    content_types = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }
    if not path.is_file():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {path}")
    content_type = content_types.get(path.suffix.lower())
    if content_type is None:
        raise ValueError("本編ではPDF、PNG、JPEGを指定してください。")
    return content_type


def create_client(settings: Settings):
    from azure.ai.contentunderstanding import ContentUnderstandingClient
    from azure.core.credentials import AzureKeyCredential

    return ContentUnderstandingClient(
        endpoint=settings.endpoint,
        credential=AzureKeyCredential(settings.key),
        api_version="2025-11-01",
    )


def analyze_binary_file(client, analyzer_id: str, path: Path):
    # 演習: content typeを調べ、begin_analyze_binaryでファイルを送信します。
    # 演習: poller.result()で完了を待ち、resultとoperation_idを返します。
    raise NotImplementedError("LabManualのバイナリ分析手順を完成させてください。")


def _fields(result) -> Mapping[str, object]:
    if not result.contents:
        raise RuntimeError("分析結果にcontentがありません。")
    return result.contents[0].fields or {}


def _value(fields: Mapping[str, object], *names: str) -> JSONValue:
    for name in names:
        field = fields.get(name)
        if field is not None:
            return to_json_compatible(field.value)
    return None


def format_invoice_result(result) -> dict[str, JSONValue]:
    # 演習: prebuilt-invoiceの主要フィールドを業務用の名前へ整形します。
    raise NotImplementedError("LabManualの請求書フィールド手順を完成させてください。")


def format_equipment_result(result) -> dict[str, JSONValue]:
    # 演習: カスタム画像アナライザーの4フィールドを整形します。
    raise NotImplementedError("LabManualの設備フィールド手順を完成させてください。")


def save_json(value: JSONValue, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Azure Content Understanding SDKでPDFまたは画像を分析します。"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    invoice = subparsers.add_parser("invoice")
    invoice.add_argument("--input", type=Path, required=True)
    invoice.add_argument(
        "--output", type=Path, default=Path("content-understanding-invoice.json")
    )
    invoice.add_argument(
        "--raw-output",
        type=Path,
        default=Path("content-understanding-invoice-raw.json"),
    )
    equipment = subparsers.add_parser("equipment")
    equipment.add_argument("--input", type=Path, required=True)
    equipment.add_argument(
        "--output",
        type=Path,
        default=Path("content-understanding-equipment.json"),
    )
    equipment.add_argument(
        "--raw-output",
        type=Path,
        default=Path("content-understanding-equipment-raw.json"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    client = None
    try:
        settings = load_settings()
        analyzer_id = "prebuilt-invoice"
        formatter = format_invoice_result
        if args.command == "equipment":
            if not settings.image_analyzer_id:
                raise ValueError(
                    "CONTENTUNDERSTANDING_IMAGE_ANALYZER_IDを設定してください。"
                )
            analyzer_id = settings.image_analyzer_id
            formatter = format_equipment_result
        client = create_client(settings)
        result, operation_id = analyze_binary_file(client, analyzer_id, args.input)
        summary = formatter(result)
        save_json(summary, args.output)
        save_json(to_json_compatible(result), args.raw_output)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        print(f"\n操作ID: {operation_id}")
        print(f"整形結果: {args.output.resolve()}")
        print(f"生の結果: {args.raw_output.resolve()}")
        return 0
    except Exception as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())
