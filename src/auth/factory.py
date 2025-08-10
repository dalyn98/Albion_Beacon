# src/auth/factory.py
import os
from .adapters.legacy_adapter import LegacyAuthAdapter
from .legacy_impl import LegacyAuthImpl  # ← 기존 구현 (그대로 유지)

def get_auth_service(logger):
    # 필요시 다른 구현을 끼워 넣을 수 있으나, 기본은 기존 구현
    impl = LegacyAuthImpl()
    return LegacyAuthAdapter(impl, logger)
