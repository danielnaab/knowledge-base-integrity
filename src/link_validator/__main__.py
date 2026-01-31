# spec: specs/link-validator.md
# spec-section: Behavior/Exit codes

"""CLI entry point for the link validator."""

from link_validator.validator import ValidateResult, validate
from tool_cli import run_tool


def _serialize(result: ValidateResult) -> dict:
    """Convert ValidateResult to a JSON-serializable dict."""
    return {
        "violations": [
            {
                "file": v.file,
                "target": v.target,
                "resolved": v.resolved,
                "rule": v.rule,
                "message": v.message,
            }
            for v in result.violations
        ],
        "summary": {
            "files_checked": result.files_checked,
            "links_checked": result.links_checked,
            "broken": len(result.violations),
        },
    }


def main() -> None:
    run_tool(
        runner=validate,
        serializer=_serialize,
        has_failures=lambda r: bool(r.violations),
    )


if __name__ == "__main__":
    main()
