"""Design-only update install implementation plan for Deimos.

This module intentionally does not launch helpers, replace executables, or perform
installation. It provides a structured contract that future implementation work
must satisfy before any install execution can be considered.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List

INSTALL_EXECUTION_ENABLED = False
HELPER_LAUNCH_ENABLED = False
AUTOMATIC_INSTALL_ENABLED = False


@dataclass(frozen=True)
class InstallImplementationStep:
    step_id: str
    title: str
    required_checks: List[str]
    forbidden_actions: List[str]
    expected_outputs: List[str]


@dataclass(frozen=True)
class InstallImplementationPlan:
    install_execution_enabled: bool
    helper_launch_enabled: bool
    automatic_install_enabled: bool
    phases: List[InstallImplementationStep]
    required_user_confirmations: List[str]
    rollback_requirements: List[str]
    post_install_verification: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "install_execution_enabled": self.install_execution_enabled,
            "helper_launch_enabled": self.helper_launch_enabled,
            "automatic_install_enabled": self.automatic_install_enabled,
            "phases": [asdict(step) for step in self.phases],
            "required_user_confirmations": list(self.required_user_confirmations),
            "rollback_requirements": list(self.rollback_requirements),
            "post_install_verification": list(self.post_install_verification),
        }


def build_install_implementation_plan() -> InstallImplementationPlan:
    """Return the locked final implementation design for a future updater install path."""
    return InstallImplementationPlan(
        install_execution_enabled=INSTALL_EXECUTION_ENABLED,
        helper_launch_enabled=HELPER_LAUNCH_ENABLED,
        automatic_install_enabled=AUTOMATIC_INSTALL_ENABLED,
        phases=[
            InstallImplementationStep(
                step_id="preflight",
                title="Verify staged update before helper launch",
                required_checks=[
                    "release-manifest.json exists and validates",
                    "Deimos.exe exists in staging and matches Deimos.exe.sha256",
                    "deimos-updater-helper.exe exists and matches checksum if helper is required",
                    "current executable path is outside staging folder",
                    "rollback folder can be created and written",
                    "install log path can be created and written",
                ],
                forbidden_actions=[
                    "do not replace Deimos.exe from the GUI process",
                    "do not launch helper without final user confirmation",
                    "do not proceed on checksum mismatch",
                ],
                expected_outputs=["validated helper manifest", "final confirmation model"],
            ),
            InstallImplementationStep(
                step_id="confirmation",
                title="Collect explicit final user confirmation",
                required_checks=[
                    "show current version and target version",
                    "show executable path that will be replaced",
                    "show rollback path",
                    "show install lock warnings",
                    "require an explicit confirmation action",
                ],
                forbidden_actions=["do not auto-confirm", "do not use startup/background confirmation"],
                expected_outputs=["user-confirmed install request"],
            ),
            InstallImplementationStep(
                step_id="helper_launch_design",
                title="Launch external helper only after Deimos exits",
                required_checks=[
                    "helper is launched with --manifest, --wait-pid, and --log",
                    "helper receives only validated absolute paths",
                    "helper waits for current Deimos process to exit before file replacement",
                    "helper writes JSONL log records for every action",
                ],
                forbidden_actions=["do not perform replacement in GUI process", "do not relaunch until verification passes"],
                expected_outputs=["helper process started", "GUI exits cleanly"],
            ),
            InstallImplementationStep(
                step_id="rollback_design",
                title="Backup and rollback before replacement",
                required_checks=[
                    "copy current Deimos.exe to rollback folder before replacement",
                    "verify rollback copy hash/size before replacing",
                    "restore rollback copy if replacement or verification fails",
                    "keep log even on failure",
                ],
                forbidden_actions=["do not delete rollback before post-install verification"],
                expected_outputs=["rollback artifact", "helper log"],
            ),
            InstallImplementationStep(
                step_id="post_install_verification",
                title="Verify installed executable before success",
                required_checks=[
                    "new Deimos.exe exists at target path",
                    "new Deimos.exe hash matches staged expected hash",
                    "helper log records install_success only after verification",
                    "optional relaunch only after verification and only when explicitly requested",
                ],
                forbidden_actions=["do not report success before hash verification"],
                expected_outputs=["verified installed executable", "final helper exit code"],
            ),
        ],
        required_user_confirmations=[
            "manual check/download has already completed",
            "staged file review has been shown",
            "install design review has been shown",
            "final install confirmation is explicit and not default-selected",
        ],
        rollback_requirements=[
            "rollback folder must be separate from staging folder",
            "rollback copy must be verified before replacement",
            "rollback restore must be attempted on replacement failure",
            "rollback logs must be retained",
        ],
        post_install_verification=[
            "target executable exists",
            "target executable hash matches staged Deimos.exe hash",
            "helper log contains install_success only after verification",
            "exit code maps to documented helper exit-code contract",
        ],
    )


def build_locked_install_summary() -> Dict[str, Any]:
    plan = build_install_implementation_plan().to_dict()
    plan["locked"] = not plan["install_execution_enabled"]
    plan["summary"] = "Phase 51 is design-only; real install execution remains disabled."
    return plan
