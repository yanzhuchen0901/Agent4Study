"""Report preview API routes."""

from fastapi import APIRouter

from src.config import ROOT_DIR


router = APIRouter(prefix="/api/report", tags=["report"])


FALLBACK_MARKDOWN = """# 竞赛报告

## 1. Abstract

待 Task8 生成完整报告。

## 2. Problem Statement

待补充。

## 3. Proposed Approach

待补充。

## 4. Experiments & Results

待补充。

## 5. Limitations & Future Work

待补充。

## 6. References

待补充。
"""


@router.get("/markdown")
def get_report_markdown() -> dict:
    path = ROOT_DIR / "report" / "整合报告.md"
    if path.exists():
        markdown = path.read_text(encoding="utf-8").strip()
        if markdown:
            return {"title": "整合报告", "markdown": markdown, "source": str(path)}
    return {"title": "竞赛报告", "markdown": FALLBACK_MARKDOWN, "source": "fallback"}
