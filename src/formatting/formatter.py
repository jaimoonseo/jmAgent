"""Code formatting module for language-specific formatting."""

import shutil
import subprocess
from typing import Optional, Dict
import re


def detect_language(code: str) -> str:
    """
    Detect programming language from code.

    Args:
        code: Code to detect language for

    Returns:
        Language name (python, javascript, typescript, sql, bash, go, rust, java, unknown)
    """
    if not code or not code.strip():
        return "unknown"

    code_lower = code.lower()

    # TypeScript - check before JavaScript since it's more specific
    if re.search(r'\b(interface|type)\s+\w+\s*[{=:]', code_lower) or \
       re.search(r':\s*(string|number|boolean|void|any)\b', code_lower):
        return "typescript"

    # Python
    if re.search(r'^\s*(def|class)\s+\w+', code, re.MULTILINE) or \
       re.search(r'\bself\b', code) or \
       re.search(r'^\s*(import|from)\s+\w+', code, re.MULTILINE):
        return "python"

    # SQL
    if re.search(r'\b(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP)\b', code, re.IGNORECASE):
        return "sql"

    # Bash
    if re.search(r'^#!/bin/bash', code, re.MULTILINE) or \
       re.search(r'\$\w+', code):
        return "bash"

    # Go
    if re.search(r'^\s*package\s+\w+', code, re.MULTILINE) or \
       re.search(r'^\s*func\s+\w+', code, re.MULTILINE):
        return "go"

    # Rust - check before JavaScript since it uses let/const too
    if re.search(r'\b(fn|impl|trait)\b', code) or \
       (re.search(r'\blet\b', code) and re.search(r':\s*\w+\s*=', code)):  # let with explicit type hints like i32
        return "rust"

    # JavaScript
    if re.search(r'\b(function|const|let|var)\s+\w+', code) or \
       re.search(r'\bconsole\.log\b', code):
        return "javascript"

    # Java
    if re.search(r'\b(public|private)\s+(class|void)\b', code) or \
       re.search(r'\bextends\b', code):
        return "java"

    return "unknown"


class CodeFormatter:
    """Format code in various languages with graceful degradation."""

    def __init__(self):
        """Initialize formatter and detect available formatting tools."""
        self.available_formatters = self._detect_formatters()

    def _detect_formatters(self) -> Dict[str, bool]:
        """
        Detect which formatting tools are available on the system.

        Returns:
            Dict mapping formatter names to availability status
        """
        formatters = {
            "black": shutil.which("black") is not None,
            "prettier": shutil.which("prettier") is not None,
            "sqlformat": shutil.which("sqlformat") is not None,
            "gofmt": shutil.which("gofmt") is not None,
            "rustfmt": shutil.which("rustfmt") is not None,
        }
        return formatters

    def format(self, code: str, language: Optional[str] = None) -> str:
        """
        Format code in the specified language.

        Args:
            code: Code to format
            language: Programming language (auto-detected if not provided)

        Returns:
            Formatted code (or original if formatter unavailable)
        """
        if not language:
            language = detect_language(code)

        if language == "python":
            return self._format_python(code)
        elif language == "javascript":
            return self._format_javascript(code)
        elif language == "typescript":
            return self._format_javascript(code)  # Use prettier for TypeScript too
        elif language == "sql":
            return self._format_sql(code)
        elif language == "go":
            return self._format_go(code)
        elif language == "rust":
            return self._format_rust(code)
        else:
            # Unknown language or no formatter available
            return code

    def _format_python(self, code: str) -> str:
        """
        Format Python code using black.

        Args:
            code: Python code to format

        Returns:
            Formatted code or original if black unavailable
        """
        if not self.available_formatters.get("black"):
            return code

        try:
            result = subprocess.run(
                ["black", "-q", "-"],
                input=code,
                text=True,
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout
            return code
        except (subprocess.TimeoutExpired, Exception):
            return code

    def _format_javascript(self, code: str) -> str:
        """
        Format JavaScript/TypeScript code using prettier.

        Args:
            code: JavaScript/TypeScript code to format

        Returns:
            Formatted code or original if prettier unavailable
        """
        if not self.available_formatters.get("prettier"):
            return code

        try:
            result = subprocess.run(
                ["prettier", "--stdin-filepath", "file.js"],
                input=code,
                text=True,
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout
            return code
        except (subprocess.TimeoutExpired, Exception):
            return code

    def _format_sql(self, code: str) -> str:
        """
        Format SQL code using sqlformat.

        Args:
            code: SQL code to format

        Returns:
            Formatted code or original if sqlformat unavailable
        """
        if not self.available_formatters.get("sqlformat"):
            return code

        try:
            result = subprocess.run(
                ["sqlformat", "-"],
                input=code,
                text=True,
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout
            return code
        except (subprocess.TimeoutExpired, Exception):
            return code

    def _format_go(self, code: str) -> str:
        """
        Format Go code using gofmt.

        Args:
            code: Go code to format

        Returns:
            Formatted code or original if gofmt unavailable
        """
        if not self.available_formatters.get("gofmt"):
            return code

        try:
            result = subprocess.run(
                ["gofmt"],
                input=code,
                text=True,
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout
            return code
        except (subprocess.TimeoutExpired, Exception):
            return code

    def _format_rust(self, code: str) -> str:
        """
        Format Rust code using rustfmt.

        Args:
            code: Rust code to format

        Returns:
            Formatted code or original if rustfmt unavailable
        """
        if not self.available_formatters.get("rustfmt"):
            return code

        try:
            result = subprocess.run(
                ["rustfmt"],
                input=code,
                text=True,
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout
            return code
        except (subprocess.TimeoutExpired, Exception):
            return code
