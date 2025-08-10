# src/core/env_guard.py
from __future__ import annotations
import os
import ctypes
from typing import Callable, Any

try:
    import winreg  # type: ignore[attr-defined]
except Exception:
    winreg = None  # 리눅스/맥 대비 (테스트/타입용)

class NpcapMissingError(RuntimeError):
    """Npcap 미설치 또는 로드 실패."""

def has_npcap() -> bool:
    """Windows에서 Npcap 설치 여부를 빠르고 확실하게 판단."""
    if os.name != "nt":
        return False
    # 1) 레지스트리 존재 확인
    if winreg is not None:
        for path in (r"SOFTWARE\Npcap", r"SOFTWARE\WOW6432Node\Npcap"):
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path):
                    return True
            except OSError:
                pass
    # 2) 핵심 DLL 로드 시도
    for dll in ("wpcap.dll", "Packet.dll"):
        try:
            ctypes.WinDLL(dll)
            return True
        except Exception:
            continue
    return False

def ensure_npcap() -> None:
    """Npcap 없으면 명확한 예외 발생."""
    if not has_npcap():
        raise NpcapMissingError(
            "Npcap is required. Install Npcap (WinPcap API-compatible) and retry."
        )

def requires_npcap(func: Callable[..., Any]) -> Callable[..., Any]:
    """함수/메서드 실행 전 Npcap 보장하는 데코레이터."""
    def wrapper(*args, **kwargs):
        ensure_npcap()
        return func(*args, **kwargs)
    return wrapper
