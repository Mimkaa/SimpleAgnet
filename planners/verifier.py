from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class VerificationResult:
    status: str          # "PASS" or "FAIL"
    reason: str
    exit_code: int


class Verifier:
    FAIL_KEYWORDS = [
        "error",
        "failed",
        "failure",
        "exception",
        "traceback",
        "cannot find",
        "not recognized",
        "syntaxerror",
        "typeerror",
        "importerror",
        "build failed",
        "test failed",
    ]

    PASS_KEYWORDS = [
        "passed",
        "success",
        "ok",
        "build successful",
        "build success",
        "tests passed",
    ]

    def verify_command_result(
        self,
        exit_code: int,
        stdout: str = "",
        stderr: str = "",
    ) -> VerificationResult:
        """
        Decide whether a shell command result should count as PASS or FAIL.
        """

        stdout = stdout or ""
        stderr = stderr or ""

        combined_output = f"{stdout}\n{stderr}".lower()

        # Strong fail: command returned non-zero exit code
        if exit_code != 0:
            return VerificationResult(
                status="FAIL",
                reason=f"Command exited with code {exit_code}",
                exit_code=exit_code,
            )

        # Strong fail: output contains obvious failure words
        for keyword in self.FAIL_KEYWORDS:
            if keyword in combined_output:
                return VerificationResult(
                    status="FAIL",
                    reason=f"Output contains failure keyword: {keyword}",
                    exit_code=exit_code,
                )

        # Strong pass: output contains obvious success words
        for keyword in self.PASS_KEYWORDS:
            if keyword in combined_output:
                return VerificationResult(
                    status="PASS",
                    reason=f"Output contains success keyword: {keyword}",
                    exit_code=exit_code,
                )

        # Default: if exit code is 0 and nothing bad happened, treat as pass
        return VerificationResult(
            status="PASS",
            reason="Exit code was 0 and no failure keyword was found",
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
            use exit_code, stdout, stderr.

        For other tools:
            use result["ok"] for now.
        """

        tool = action.get("tool")

        if tool == "shell":
            return self.verify_command_result(
                exit_code=result.get("exit_code", result.get("returncode", 1)),
                stdout=result.get("stdout", ""),
                stderr=result.get("stderr", ""),
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