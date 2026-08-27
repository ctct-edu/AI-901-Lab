from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from dotenv import load_dotenv
from pydantic import BaseModel, Field


@dataclass(frozen=True)
class Settings:
    base_url: str
    api_key: str
    deployment: str


class VisionAnalysis(BaseModel):
    objects: list[str] = Field(description="画像内で確認できる主な物体")
    scene: str = Field(description="画像全体のシーンや状況")
    text: list[str] = Field(description="画像内で読み取れた文字")
    safety_concern: str = Field(description="目視確認すべき安全上の懸念")


def load_settings(environment: Mapping[str, str] | None = None) -> Settings:
    if environment is None:
        load_dotenv()
        environment = os.environ
    names = (
        "AZURE_OPENAI_BASE_URL",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_DEPLOYMENT",
    )
    missing = [name for name in names if not environment.get(name)]
    if missing:
        raise ValueError(f"環境変数が設定されていません: {', '.join(missing)}")
    base_url = environment["AZURE_OPENAI_BASE_URL"].rstrip("/") + "/"
    if not re.fullmatch(
        r"https://[^/]+\.openai\.azure\.com/openai/v1/",
        base_url,
        re.IGNORECASE,
    ):
        raise ValueError(
            "AZURE_OPENAI_BASE_URLには "
            "https://<resource>.openai.azure.com/openai/v1/ 形式を指定してください。"
        )
    return Settings(
        base_url=base_url,
        api_key=environment["AZURE_OPENAI_API_KEY"],
        deployment=environment["AZURE_OPENAI_DEPLOYMENT"],
    )


def detect_media_type(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"画像ファイルが見つかりません: {path}")
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }
    media_type = media_types.get(path.suffix.lower())
    if media_type is None:
        raise ValueError("本編ではPNGまたはJPEG画像を指定してください。")
    return media_type


def encode_image(path: Path) -> str:
    media_type = detect_media_type(path)
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{media_type};base64,{encoded}"


def create_client(settings: Settings):
    # 演習: openai.OpenAIを読み込み、base_urlとapi_keyを渡します。
    raise NotImplementedError("LabManualのクライアント作成手順を完成させてください。")


def analyze_image(client, deployment: str, path: Path) -> VisionAnalysis:
    # 演習: 画像をdata URIへ変換してresponses.parseへ渡します。
    # 演習: status、refusal、output_parsedを確認します。
    raise NotImplementedError("LabManualの画像分析手順を完成させてください。")


def save_analysis(analysis: VisionAnalysis, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(analysis.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Responses APIで画像を構造化して分析します。"
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, default=Path("vision-analysis.json")
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    client = None
    try:
        settings = load_settings()
        client = create_client(settings)
        analysis = analyze_image(client, settings.deployment, args.input)
        save_analysis(analysis, args.output)
        print(json.dumps(analysis.model_dump(), ensure_ascii=False, indent=2))
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
