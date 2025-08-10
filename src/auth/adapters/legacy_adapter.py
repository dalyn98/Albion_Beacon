# src/auth/adapters/legacy_adapter.py
import time

class LegacyAuthAdapter:
    """
    기존 인증 구현을 감싸는 어댑터.
    - 기존 함수 시그니처/반환값 유지
    - 자동 토큰갱신/에러메시지/로깅만 내부에서 강화
    """
    def __init__(self, legacy_impl, logger):
        self._impl = legacy_impl
        self._logger = logger
        self._last_refresh = 0

    def login(self, username: str, password: str) -> bool:
        try:
            ok = self._impl.login(username, password)  # 기존 구현 그대로 호출
            if ok:
                self._logger.info("Auth: login success")
            else:
                self._logger.warning("Auth: login failed")
            return ok
        except Exception as e:
            self._logger.exception("Auth: login error")
            return False

    def logout(self) -> None:
        try:
            self._impl.logout()
            self._logger.info("Auth: logout")
        except Exception:
            self._logger.exception("Auth: logout error")

    def current_user(self):
        try:
            return self._impl.current_user()
        except Exception:
            self._logger.exception("Auth: current_user error")
            return None

    def has_role(self, role: str) -> bool:
        try:
            return self._impl.has_role(role)
        except Exception:
            self._logger.exception("Auth: has_role error")
            return False

    def refresh_token(self) -> bool:
        try:
            now = time.time()
            if now - self._last_refresh < 30:
                return True  # 과도한 갱신 방지
            ok = getattr(self._impl, "refresh_token", lambda: True)()
            self._last_refresh = now
            return ok
        except Exception:
            self._logger.exception("Auth: refresh_token error")
            return False
