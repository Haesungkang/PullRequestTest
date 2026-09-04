"""예약 자리 감시 매크로.

사용법:
    python watcher.py cgv
    python watcher.py hwadamsup
    python watcher.py yanolja

동작 순서:
 1) 브라우저를 띄우고 config 에 지정한 예약 페이지를 연다
 2) (needs_login 이 true 면) 직접 로그인/캡차를 처리할 시간을 준다
 3) 자리가 날 때까지 새로고침하며 감시한다
 4) 자리가 나면 알림음을 내고 예약 버튼을 눌러준 뒤,
    결제/캡차는 사용자가 직접 마무리하도록 넘긴다

주의:
 - 개인적으로 정당하게 이용 가능한 예약에만 사용하세요.
 - 사이트 이용약관에서 자동화를 금지할 수 있습니다.
 - refresh_sec 를 너무 짧게 두면 사이트에 부담을 주고 차단될 수 있습니다(권장 3초 이상).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from common import beep, launch_browser, poll, wait_for_login

CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config(name: str) -> dict:
    if not CONFIG_PATH.exists():
        sys.exit("config.json 이 없습니다. config.example.json 을 복사해서 만드세요.")
    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if name not in data:
        sys.exit(f"'{name}' 설정이 config.json 에 없습니다. (가능: {', '.join(data)})")
    return data[name]


def is_available(page, cfg: dict) -> bool:
    """자리가 났는지 판단한다. 사이트별로 selector 를 config 에서 조정하세요."""
    # 1) '매진/마감' 문구가 보이면 아직 자리 없음
    sold_out = cfg.get("sold_out_text")
    if sold_out and page.get_by_text(sold_out).count() > 0:
        return False
    # 2) 예약 버튼이 존재하고 활성화돼 있으면 자리 있음
    loc = page.locator(cfg["available_selector"])
    return loc.count() > 0 and loc.first.is_enabled()


def main(name: str) -> None:
    cfg = load_config(name)
    pw, browser, page = launch_browser(headless=False)
    try:
        print(f"[{name}] 예약 페이지 여는 중: {cfg['url']}")
        page.goto(cfg["url"])

        if cfg.get("needs_login", True):
            wait_for_login()

        print(f"[{name}] 자리 감시 시작 (새로고침 {cfg['refresh_sec']}초 간격). Ctrl+C 로 중단.")

        def check() -> bool:
            # 날짜/옵션 선택 상태가 새로고침으로 초기화되는 페이지(야놀자 등)는
            # config 에서 "reload": false 로 두고 화면 갱신만 감시한다.
            if cfg.get("reload", True):
                page.reload()
                page.wait_for_load_state("networkidle")
            return is_available(page, cfg)

        found = poll(check, interval=cfg["refresh_sec"])
        if found:
            print(f"\n[{name}] 자리가 났습니다!")
            beep()
            try:
                page.locator(cfg["available_selector"]).first.click()
            except Exception as exc:  # 자동 클릭 실패해도 사용자가 이어서 진행
                print(f"자동 클릭 실패({exc}). 화면에서 직접 눌러 진행하세요.")
            input("결제/캡차를 완료한 뒤 Enter 를 누르면 종료합니다...")
    except KeyboardInterrupt:
        print("\n중단했습니다.")
    finally:
        browser.close()
        pw.stop()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("사용법: python watcher.py <config.json 에 정의한 이름>")
    main(sys.argv[1])
