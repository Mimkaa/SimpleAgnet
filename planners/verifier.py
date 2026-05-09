from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class VerificationResult:
    status: str          # "PASS" or "FAIL"
    reason: str
    exit_code: int


class Verifier:
    """
    Verifies whether an action result should count as PASS or FAIL.

    Important rule:
    - For shell commands, the exit code is the strongest signal.
    - If exit code is non-zero, the command failed.
    - If exit code is zero, the command usually passed.
    - Do not blindly fail just because stdout contains words like "failed",
      because file listings can contain paths like .pytest_cache/lastfailed.
    """

    FAIL_KEYWORDS = [
        "traceback",
        "syntaxerror",
        "typeerror",
        "importerror",
        "modulenotfounderror",
        "not recognized as an internal or external command",
        "no module named",
        "command not found",
    ]

    PASS_KEYWORDS = [
        "passed",
        "success",
        "ok",
        "build successful",
        "build success",
        "tests passed",
    ]

    def should_scan_output_for_failure_keywords(
        self,
        command: str,
        stdout: str,
        stderr: str,
    ) -> bool:
        """
        Decide whether keyword scanning is safe.

        We avoid scanning generic file listings because paths can contain words
        like 'lastfailed', which are not actual failures.
        """

        command_lower = (command or "").lower().strip()

        # File listing commands often output filenames like:
        # .pytest_cache/v/cache/lastfailed
        # That should not make the action fail.
        listing_commands = [
            "dir",
            "dir /s /b",
            "ls",
            "tree",
        ]

        if command_lower in listing_commands:
            return False

        if command_lower.startswith("dir "):
            return False

        if command_lower.startswith("ls "):
            return False

        # For stderr, scanning is usually useful because real Python errors
        # often appear there.
        if stderr.strip():
            return True

        # For known test/build commands, scanning stdout can be useful.
        test_or_build_indicators = [
            "pytest",
            "unittest",
            "gradle",
            "mvn",
            "npm test",
            "go test",
            "cargo test",
        ]

        return any(indicator in command_lower for indicator in test_or_build_indicators)

    def verify_command_result(
        self,
        exit_code: int,
        stdout: str = "",
        stderr: str = "",
        command: str = "",
    ) -> VerificationResult:
        """
        Decide whether a shell command result should count as PASS or FAIL.
        """

        stdout = stdout or ""
        stderr = stderr or ""

        # Strong fail: command returned non-zero exit code.
        if exit_code != 0:
            return VerificationResult(
                status="FAIL",
                reason=f"Command exited with code {exit_code}",
                exit_code=exit_code,
            )

        # Strong pass: command returned zero.
        # Only scan output for failure keywords in contexts where that makes sense.
        if self.should_scan_output_for_failure_keywords(command, stdout, stderr):
            combined_output = f"{stdout}\n{stderr}".lower()

            for keyword in self.FAIL_KEYWORDS:
                if keyword in combined_output:
                    return VerificationResult(
                        status="FAIL",
                        reason=f"Output contains failure keyword: {keyword}",
                        exit_code=exit_code,
                    )

            for keyword in self.PASS_KEYWORDS:
                if keyword in combined_output:
                    return VerificationResult(
                        status="PASS",
                        reason=f"Output contains success keyword: {keyword}",
                        exit_code=exit_code,
                    )

        return VerificationResult(
            status="PASS",
            reason="Exit code was 0",
            exit_code=exit_code,
        )

    def verify_action_result(
        self,
        task,
        action: Dict[str, Any],
        result: Dict[str, Any],
    ) -> VerificationResult:
        """
        Decide whether an executed action should count as PASS or FAIL.

        For shell actions:
            use returncode / exit_code first.

        For other tools:
            use result["ok"] for now.
        """

        tool = action.get("tool")

        if tool == "shell":
            return self.verify_command_result(
                exit_code=result.get("exit_code", result.get("returncode", 1)),
                stdout=result.get("stdout", ""),
                stderr=result.get("stderr", ""),
                command=action.get("command", ""),
            )

        if result.get("ok"):
            return VerificationResult(
                status="PASS",
                reason="Tool returned ok=True",
                exit_code=0,
            )

        return VerificationResult(
            status="FAIL",
            reason=result.get("stderr", result.get("message", "Tool failed")),
            exit_code=result.get("exit_code", result.get("returncode", 1)),
        )