"""공통 유틸: 브라우저 실행, 알림음, 감시 루프 헬퍼."""
from __future__ import annotations

import sys
import time

from playwright.sync_api import sync_playwright, Page


def launch_browser(headless: bool = False):
    """브라우저를 띄우고 (playwright, browser, page) 를 돌려준다.

    headless=False 로 띄워야 직접 로그인/결제/캡차를 처리할 수 있다.
    """
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=headless)
    context = browser.new_context()
    page = context.new_page()
    return pw, browser, page


def beep(times: int = 5):
    """터미널 비프음으로 '자리 났음' 을 알린다."""
    for _ in range(times):
        sys.stdout.write("\a")
        sys.stdout.flush()
        time.sleep(0.3)


def wait_for_login(prompt: str = "로그인을 완료한 뒤 이 창에서 Enter 를 누르세요...") -> None:
    """사용자가 직접 로그인/캡차를 처리하도록 잠시 멈춘다."""
    input(prompt)


def poll(check, interval: float = 3.0, max_tries: int | None = None):
    """check() 가 참을 돌려줄 때까지 interval 초마다 반복.

    자리가 나면 check() 의 결과(참값)를 그대로 반환한다.
    """
    tries = 0
    while True:
        result = check()
        if result:
            return result
        tries += 1
        if max_tries is not None and tries >= max_tries:
            return None
        time.sleep(interval)
