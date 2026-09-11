#!/usr/bin/env python3
"""Render a credential-free Codex host MCP config example when applicable."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from common import is_env_reference, stable_json, strict_json_load, validate_mcp_manifest


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _env_name(value: Any) -> str | None:
    if not is_env_reference(value):
        return None
    token = str(value).strip()
    return token[2:-1] if token.startswith("${") else token[1:]


def render(root: Path) -> tuple[str, dict[str, Any]]:
    path = root / "mcp.json"
    if not path.is_file():
        return "", {"status": "NOT_RUN", "applicable": False, "checks": ["no portable mcp.json"], "issues": []}
    manifest = strict_json_load(path)
    issues = validate_mcp_manifest(path, root)
    if issues:
        return "", {"status": "FAIL", "applicable": True, "checks": [], "issues": issues}
    servers = manifest["mcpServers"]
    lines = ["# Generated from portable mcp.json; credentials stay in host environment/OAuth config."]
    for name in sorted(servers):
        server = servers[name]
        table_name = name.replace("\\", "\\\\").replace('"', '\\"')
        lines.append("")
        lines.append(f'[mcp_servers."{table_name}"]')
        server_type = server.get("type")
        if server_type == "stdio":
            lines.append(f"command = {_toml_string(server['command'])}")
            args = server.get("args")
            if isinstance(args, list) and all(isinstance(item, str) for item in args):
                lines.append("args = [" + ", ".join(_toml_string(item) for item in args) + "]")
        else:
            lines.append(f"url = {_toml_string(server['url'])}")
            bearer = server.get("bearer_token_env_var")
            if isinstance(bearer, str) and bearer:
                lines.append(f"bearer_token_env_var = {_toml_string(bearer)}")
            headers = server.get("headers", {})
            if isinstance(headers, dict):
                for key, value in headers.items():
                    if str(key).lower() == "authorization" and isinstance(value, str):
                        parts = value.split(None, 1)
                        if len(parts) == 2 and parts[0].lower() == "bearer":
                            env_name = _env_name(parts[1])
                            if env_name:
                                lines.append(f"bearer_token_env_var = {_toml_string(env_name)}")
        env = server.get("env", {})
        env_names = sorted({name for value in env.values() for name in [_env_name(value)] if name}) if isinstance(env, dict) else []
        if env_names:
            lines.append("env_vars = [" + ", ".join(_toml_string(name) for name in env_names) + "]")
    return "\n".join(lines) + "\n", {
        "status": "PASS",
        "applicable": True,
        "checks": ["portable MCP validated", "credential-free host config rendered"],
        "issues": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin_root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format", choices={"json", "text"}, default="text")
    args = parser.parse_args()
    try:
        content, report = render(args.plugin_root)
        if args.output and report["status"] == "PASS":
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(content, encoding="utf-8")
            report["output"] = str(args.output)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        report = {"status": "FAIL", "applicable": True, "checks": [], "issues": [str(exc)]}
    if args.format == "json":
        print(stable_json(report), end="")
    else:
        print(f"{report['status']}: {args.plugin_root}")
        for issue in report.get("issues", []):
            print(f"- {issue.get('code', issue) if isinstance(issue, dict) else issue}")
    return 0 if report["status"] in {"PASS", "NOT_RUN"} else 1


if __name__ == "__main__":
    sys.exit(main())
