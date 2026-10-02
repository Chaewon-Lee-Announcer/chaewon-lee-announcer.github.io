# 이채원 ON AIR

스포츠 아나운서 · 라이브커머스 쇼호스트 이채원의 방송 콘셉트 포트폴리오.

- 사이트: https://chaewon-lee-announcer.github.io/
- `onair/src/` — 페이지 소스 (`build.py`가 데이터 · HTML · 폰트 서브셋을 묶어 빌드)
- `docs/` — GitHub Pages 배포본 (`python3 onair/src/build.py <font-cache-dir>`로 생성)
- `onair/shorts/` — 15초 세로 쇼츠 (1080×1920 · 60fps · 합성 사운드). `build_shorts.py <font-cache-dir>`로 컴포지션을 만들고 `render_shorts.py video`로 `out/onair_shorts.mp4`를 렌더 (Playwright Chromium · ffmpeg 필요)
