#!/usr/bin/env python3
"""Builds onair/index.html (artifact page) and docs/ (GitHub Pages site: full document + used assets).

Data comes from the two 2026 PDFs (쇼호스트 / 스포츠아나운서), the Naver Shopping Live
replay API, her Instagram (@c._.1ee) and press coverage gathered on 2026-10-02.
"""
import base64, html, json, pathlib, re, shutil, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
FONT_CACHE = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / ".fontcache"
e = html.escape

NAVER = "#03C75A"; YT = "#FF0033"; IG = "#E1306C"

# ───────────────────────── data ─────────────────────────
LIVE = [  # 20 broadcast stills from the show-host PDF (pp.3–7); 12 carry links in the PDF
    dict(f="fashion_1", cat="fashion", brand="폰드패션몰", sub="네파이젠벅 · 캘빈클라인 스포츠", title="[썸머 바캉스룩] 여름 인기 아이템 단독 특가! UP TO 69%", date="2026.07.16", dur="1:01:39", url="https://view.shoppinglive.naver.com/replays/1966015", w=518, h=831),
    dict(f="fashion_2", cat="fashion", brand="푸마 바디웨어", sub="공식스토어", title="푸마 바디웨어 BEST 어워즈 · 30% 쿠폰+적립까지 역대 찬스", date="2026.06.26", dur="1:00:40", url="https://view.shoppinglive.naver.com/replays/1937158"),
    dict(f="fashion_3", cat="fashion", brand="커플 폴로 룩", sub="패션 라이브", title="남녀 커플 코디 라이브", date="2026", dur=None, url=None),
    dict(f="fashion_4", cat="fashion", brand="푸스토어", sub="피에르가르뎅", title="피에르가르뎅 우양산 LIVE 특가", date="2026.07.16", dur="1:01:13", url="https://view.shoppinglive.naver.com/replays/1972450"),
    dict(f="fashion_5", cat="fashion", brand="SATIN", sub="패션 라이브", title="SATIN 2인 진행 라이브", date="2026", dur=None, url=None),
    dict(f="fashion_6", cat="fashion", brand="GANNI", sub="패션 라이브", title="GANNI 티셔츠 · 데님 스타일링 라이브", date="2026", dur=None, url=None),
    dict(f="fashion_7", cat="fashion", brand="DOROSIWA", sub="란제리 라이브", title="도로시와 란제리 2인 진행 라이브", date="2026", dur=None, url=None),
    dict(f="fashion_8", cat="fashion", brand="Calvin Klein", sub="패션 라이브", title="캘빈클라인 데님 · 캐주얼 라이브", date="2026", dur=None, url=None),
    dict(f="wellness_1", cat="wellness", brand="에르고바디", sub="EMS", title="EMS 1등! 에르고바디 EMS 레깅스 런칭 특가 ~57%", date="2026.07.13", dur="1:01:05", url="https://view.shoppinglive.naver.com/replays/1970810"),
    dict(f="wellness_2", cat="wellness", brand="OVERTHE", sub="오버더바이크", title="러닝 대신 방구석 벚꽃 라이딩 · 오버더바이크 & 통곡의계단", date="2026.03.30", dur="1:01:09", url="https://view.shoppinglive.naver.com/replays/1882279", w=494, h=793),
    dict(f="wellness_3", cat="wellness", brand="풀무원", sub="풀무원건강생활", title="풀무원 리셋클렌즈 48시간 36% 할인 + 구매별 사은품", date="2026.07.30", dur="1:03:06", url="https://view.shoppinglive.naver.com/replays/1952024"),
    dict(f="wellness_4", cat="wellness", brand="OVERTHE", sub="오버더바이크", title="[오버더 최대 65% 라이브 혜택] 나만 없어, 오버더 바이크!", date="2025.07.31", dur="1:01:22", url="https://view.shoppinglive.naver.com/replays/1690223"),
    dict(f="home_1", cat="home", brand="LG전자", sub="YouTube Shorts", title="LG전자 라이브커머스 진행 클립", date="2026.08.06", dur="1:17", url="https://youtube.com/shorts/VBcknkIJFeo", plat="yt"),
    dict(f="home_2", cat="home", brand="아에르", sub="아에르 샵", title="[아에르 본사 Live] 아에르 썸머특가", date="2026.07.08", dur="1:00:41", url="https://view.shoppinglive.naver.com/replays/1967887"),
    dict(f="home_3", cat="home", brand="오드앵글", sub="오드앵글 스토어", title="오드앵글 여름가전 LIVE · 무드등 BLDC 선풍기", date="2026.05.18", dur="1:00:06", url="https://view.shoppinglive.naver.com/replays/1920555"),
    dict(f="home_4", cat="home", brand="아에르", sub="아에르 샵", title="[아에르 본사 Live] 6월의 시작, 특별한 혜택", date="2026.06.10", dur="1:01:03", url="https://view.shoppinglive.naver.com/replays/1941242"),
    dict(f="travel_1", cat="travel", brand="서해랑 × 평화곤돌라", sub="제부도해상케이블카 · 파주임진각", title="서해랑 제부도해상케이블카 × 파주임진각평화곤돌라", date="2024.10.02", dur="1:01:05", url="https://view.shoppinglive.naver.com/replays/1453755"),
    dict(f="travel_2", cat="travel", brand="워터밤 2026", sub="더현대Hi 티켓", title="워터밤 2026 대표 썸머 뮤직 페스티벌 티켓 라이브", date="2026", dur=None, url=None),
    dict(f="travel_3", cat="travel", brand="KLPGA", sub="골프 라이브", title="KLPGA 2026 시즌 굿즈 · 티켓 라이브", date="2026", dur=None, url=None),
    dict(f="travel_4", cat="travel", brand="골프 라이브", sub="HONMA", title="골프 패션 · 장비 라이브", date="2026", dur=None, url=None),
]
CATS = [("all", "ALL"), ("fashion", "FASHION"), ("wellness", "WELLNESS"), ("home", "HOME & LIVING"), ("travel", "TRAVEL")]

# Naver replays first (as in the PDF), then YouTube (filled from research), then Instagram
YOUTUBE = json.loads((HERE / "youtube.json").read_text()) if (HERE / "youtube.json").exists() else []
INSTAGRAM = [
    dict(url="https://www.instagram.com/reel/DEkfIhLPSqi/", title="개통 전 고덕토평대교 첫 주행 — 채널A 〈스마트 도로〉 드라이버", meta="REEL · 2025.01 · 조회 149.9만", tag="TV"),
    dict(url="https://www.instagram.com/reel/DZ_Ygxbu5eE/", title="KBS 뉴스 · 2026 월드컵 현장 시민 인터뷰 출연", meta="REEL · 2026.06", tag="TV"),
    dict(url="https://www.instagram.com/reel/Dd8_deYPG4P/", title="패션플러스 라이브커머스 진행 클립", meta="REEL · 2026.10", tag="LIVE"),
    dict(url="https://www.instagram.com/p/Dd8aB1ClDki/", title="리본카 자동차 라이브 — 1년 넘게 고정 진행 중인 '사심방송'", meta="VIDEO POST · 2026.10", tag="LIVE"),
    dict(url="https://www.instagram.com/p/DaQD2PhFKou/?img_index=3", title="2026 세나 설악그란폰도 — 출발 라인 · 시상식 현장 영상", meta="VIDEO POST · 2026.07", tag="SPORTS"),
    dict(url="https://www.instagram.com/p/Dci4irYlOtH/", title="롯데시네마 굿즈 라이브 — 콘셉트 코스프레 1시간 진행", meta="VIDEO POST · 2026.08", tag="LIVE"),
    dict(url="https://www.instagram.com/p/DY7IcDjlKLw/", title="필립스 프레스티지 울트라 i9000 — 레이싱 콘셉트 라이브", meta="VIDEO POST · 2026.05", tag="LIVE"),
    dict(url="https://www.instagram.com/reel/C83YW83PHYj/", title="2024 현대 N 페스티벌 서킷 현장", meta="REEL · 2024.07", tag="MOTOR"),
]
EVENT_VIDEOS = [  # broadcaster / organiser uploads where she is verified on screen (face match or name caption)
    dict(url="https://www.youtube.com/watch?v=AKxH1HtPqNU", title="2026 SENA 설악그란폰도 공식 영상 — 무대 MC", meta="위즈런 · 2026.06", dur="3:39", thumb="assets/yt/AKxH1HtPqNU.jpg"),
    dict(url="https://www.youtube.com/watch?v=XM6qcm6RUC0", title="2025 손기정 평화마라톤 공식 영상 — 현장 러너 인터뷰", meta="위즈런 · 2025.11", dur="3:59", thumb="assets/yt/XM6qcm6RUC0.jpg"),
    dict(url="https://www.youtube.com/watch?v=HD9epIX40nI", title="[LIVE] 2025 문경 오미자 축제 OBS 특별 생방송 — 리포터 2:02~", meta="OBS · 2025.09.19", dur="49:09", thumb="assets/yt/HD9epIX40nI.jpg"),
    dict(url="https://www.youtube.com/watch?v=bM01n4yXPRw", title="2025 자이언트 설악그란폰도 공식 영상 — 무대 MC · 라이더 인터뷰", meta="위즈런 · 2025.05", dur="3:23", thumb="assets/yt/bM01n4yXPRw.jpg"),
    dict(url="https://www.youtube.com/watch?v=mO9U-28inOE", title="채널A 〈스마트 도로〉 — 개통 전 고덕토평대교 주행 0:53~", meta="채널A · 2025.01 방송", dur="7:42", thumb="assets/yt/mO9U-28inOE.jpg"),
    dict(url="https://www.youtube.com/watch?v=DBVLzGeZ2Fk", title="채널A 〈스마트 도로〉 — 드라이버 인터뷰 1:50~", meta="채널A · 2025.01 방송", dur="8:17", thumb="assets/yt/DBVLzGeZ2Fk.jpg"),
    dict(url="https://www.youtube.com/watch?v=yDPbAM92HaM", title="채널A 〈스마트 도로〉 — 고속 주행 촬영분", meta="채널A · 2025.01 방송", dur="8:46", thumb="assets/yt/yDPbAM92HaM.jpg"),
    dict(url="https://www.youtube.com/watch?v=g3l0FmRp-gc", title="2024 손기정 평화마라톤 공식 영상 — 무대 공동 진행", meta="위즈런 · 2024.11", dur="6:12", thumb="assets/yt/g3l0FmRp-gc.jpg"),
]

SEASON = "2024—2026"
COURSE = [
    dict(kind="flag", top="START", right="0.000 KM", title="START LINE", desc="3 · 2 · 1, 출발 카운트다운"),
    dict(kind="cp", top=SEASON, right="SEASON 3", title="화천 DMZ 랠리", desc="메인 MC · 자전거 73km DMZ 코스"),
    dict(kind="photo", img="ev_granfondo.jpg", w=1448, h=1086, alt="수천 명의 자전거 라이더 앞 출발 무대에서 남성 MC와 함께 선 이채원", cap="라이더 앞 출발선 진행", right="DMZ RALLY"),
    dict(kind="cp", top=SEASON, right="SEASON 3", title="설악그란폰도", desc="메인 MC · 인제 208km / 105km", video="https://www.youtube.com/watch?v=bM01n4yXPRw"),
    dict(kind="cp", top=SEASON, right="SEASON 3", title="철원 DMZ 국제평화마라톤", desc="메인 MC · 2026년 약 12,000명 참가"),
    dict(kind="cp", top=SEASON, right="SEASON 3", title="양양 강변 전국 마라톤", desc="메인 MC · 양양 남대천"),
    dict(kind="cp", top=SEASON, right="SEASON 3", title="강서 허준런", desc="메인 MC · 서울식물원 출발"),
    dict(kind="cp", top=SEASON, right="SEASON 3", title="손기정 평화마라톤", desc="메인 MC · 무대 진행 · 러너 인터뷰", video="https://www.youtube.com/watch?v=g3l0FmRp-gc"),
    dict(kind="cp", top="2024—2025", right="SEASON 2", title="양양그란폰도", desc="메인 MC · 양양 남대천"),
    dict(kind="cp", top="2025.02", right="", title="제31회 충남 장애인체육대회 D-100 기념행사", desc="MC · 서산 중앙호수공원"),
    dict(kind="cp", top="2025.06—07", right="", title="IBK 유스파이크", desc="경기 진행 MC · 유소년 배구"),
    dict(kind="cp", top="2025.07", right="", title="양양군민 명랑운동회", desc="메인 MC"),
    dict(kind="cp", top="2025.10", right="", title="제106회 전국체육대회 리셉션", desc="진행 · 부산"),
    dict(kind="cp", top="2025.11", right="", title="우이런 · 북한산페스타", desc="메인 MC · 강북구 10km"),
    dict(kind="photo", img="ev_kolon.jpg", w=1206, h=804, alt="코오롱 트레일캠프 울릉 야간 무대에서 마이크를 들고 진행하는 이채원", cap="코오롱 트레일캠프 in 울릉 · 메인 MC", right="2026.06"),
    dict(kind="cp", top="2026.10.11", right="NEXT", title="MBN 전국 나주 마라톤", desc="메인 MC", when="2026-10-11"),
    dict(kind="flag", top="FINISH", right="42.195 KM", title="FINISH", desc="다음 출발선에서 만나요"),
]
UPCOMING = [  # from her Instagram post of 2026-09-30
    ("2026-09-05", "철원 DMZ 국제평화마라톤"), ("2026-09-12", "양양 강변 전국 마라톤"),
    ("2026-10-10", "강서 허준런"), ("2026-10-11", "MBN 전국 나주 마라톤"),
    ("2026-10-24", "평창 불닭 버닝 트레일런"), ("2026-11-15", "손기정 평화마라톤"),
]
PRESS = [
    ("한국일보 · 2026.09.05", "철원 DMZ 국제평화마라톤 — 1만2000명, 평화를 향해 달렸다", "https://www.hankookilbo.com/news/article/A2026090513470000105"),
    ("한국일보 · 2025.09.21", "민통선 달린 7500명의 건각 — 식전 행사 사회", "https://www.hankookilbo.com/News/Read/A2025091714510001737"),
    ("철원DMZ국제평화마라톤 · 공식 화보", "2025 대회 무대 사진", "https://dmzrun.co.kr/page/photo?caid=12"),
    ("화천군의회 · 2025.05", "2025 화천 DMZ 랠리 개회식", "https://blog.naver.com/hwacheoncouncil/223873175723"),
]

TV = [
    dict(ch="KBS", date="2026.06", title="KBS 뉴스 · 2026 월드컵 현장 인터뷰", role="시민 인터뷰 출연", bg="linear-gradient(135deg,#0A2A66,#2563D9)", link="https://www.instagram.com/reel/DZ_Ygxbu5eE/"),
    dict(ch="OBS", date="2025.09", title="문경오미자축제 특별 생방송", role="리포터", bg="linear-gradient(135deg,#2E145F,#7B3FE0)", link="https://www.youtube.com/watch?v=HD9epIX40nI"),
    dict(ch="채널A", date="2025.01", title="특별기획 〈먼저 만나는 미래, 스마트 도로〉", role="드라이버 출연", bg="linear-gradient(135deg,#6B0C26,#E32652)", link="https://www.youtube.com/watch?v=mO9U-28inOE"),
    dict(ch="KBS", date="2023—24", title="시니어토크쇼 〈황금연못〉", role="출연", bg="linear-gradient(135deg,#0B3B2E,#1F9E73)", link=None),
    dict(ch="arirang", date="2023.07", title="arirang TV 〈I'm Live〉", role="출연", bg="linear-gradient(135deg,#073C47,#11A6A8)", link=None),
    dict(ch="KBS", date="2022.12", title="〈불후의 명곡〉", role="출연", bg="linear-gradient(135deg,#3A1A06,#E07A12)", link=None),
    dict(ch="Mnet", date="2022.06", title="〈뚝딱이의 역습〉", role="출연", bg="linear-gradient(135deg,#111111,#E6007E)", link=None),
]
BARS = ["#C0C0C0", "#C0C000", "#00C0C0", "#00C000", "#C000C0", "#C00000", "#0000C0"]

CORPORATE = [
    ("2026.01", "타린로즈 VIP 고객 초청행사", "메인 MC"),
    ("2025.07", "유세린 VIP 고객 초청행사", "MC"),
    ("2025.06", "연천 청소년 AI센터 개관식", "MC"),
    ("2024—2026", "BMW M클럽 코리아 신년회", "MC"),
    ("2024.04", "크립토닷컴 코리아 런칭파티", "MC · 포시즌스 호텔 서울"),
    ("2023.12", "삼성 멤버스 스타즈 발대식", "MC"),
    ("2023.11", "중기부 K-소셜벤처 페스타 2023", "MC · 서초 엘타워"),
    ("2023.12", "MK유니버셜 VIP 연말행사", "MC"),
    ("2022.12", "현대자동차 아이디어 페스티벌", "단독 MC"),
]
RECREATION = [
    ("2024—2025", "캐치! 티니핑 전국 싱어롱쇼", "메인 MC"),
    ("2024—2025", "미니특공대 전국투어", "메인 MC"),
    ("2025.09", "수유시장 맥주축제", "레크리에이션"),
    ("2022.09", "연천군 동막계곡 힐링야행", "레크리에이션 MC"),
    ("2022.07—08", "보령머드축제", "도슨트"),
]
REPORTER = [
    ("2025.09", "OBS 문경오미자축제 생방송", "리포터"),
    ("2024.10", "고양특례시민의 날 기념식", "리포터"),
    ("2023.01", "코리아세일페스타 이천 사기막골", "리포팅"),
]

CAREER = [
    ("2016.03 — 2021.02", "남서울대학교 국제유통학과 졸업", "EDUCATION", "", "4Y 11M"),
    ("2019.10 — 2020.01", "W쇼핑 모바일 홈쇼핑 마케팅 (대학교 인턴십)", "MARKETING", "", "3M"),
    ("2020.09 — 2022.04", "YD컴퍼니 모바일 광고마케팅 (주임)", "MARKETING", "", "1Y 7M"),
    ("2022", "미스인터콘티넨탈 수도권 스타상 수상", "AWARD", "award", "—"),
    ("2022", "쥬빈뜨 비타스틱 뷰티모델", "MODEL", "", "—"),
    ("2022.10 — 2023.02", "휴먼웍스 모바일 라이브커머스 (IT · 생활용품 전문)", "LIVE COMMERCE", "", "4M"),
    ("2023", "베스트퀸코리아어워즈 인플루언서상 수상", "AWARD", "award", "—"),
    ("2023", "바바요 스틱콜라겐 뷰티모델", "MODEL", "", "—"),
    ("2023.04 — 2023.11", "삼성전자 갤럭시 큐레이터", "CURATOR", "", "7M"),
    ("2023 — 現", "스포츠 아나운서 · 라이브커머스 쇼호스트", "ON AIR", "onair", "LIVE ●"),
]

BRANDS_A = ["PUMA BODYWEAR", "CALVIN KLEIN", "LG전자", "풀무원", "Aer", "ODDANGLE", "OVERTHE", "ERGOBODY", "PIERRE CARDIN", "SATIN", "GANNI", "DOROSIWA", "패션플러스", "PHILIPS", "정관장", "리본카"]
BRANDS_B = ["BMW M CLUB KOREA", "CRYPTO.COM", "SAMSUNG", "HYUNDAI", "EUCERIN", "TARYN ROSE", "KOLON SPORT", "SENA", "KLPGA", "WATERBOMB", "KBS", "OBS", "채널A", "MBN", "arirang", "Mnet"]
MORE_AIR = ["LG 그램 전속 쇼호스트", "삼성전자 갤럭시 Z플립 · Z폴드 · 탭 런칭 방송", "리본카 자동차 라이브 고정 진행", "패션플러스", "롯데시네마 굿즈 라이브", "필립스", "정관장", "카카오쇼핑라이브", "하이마트 노트북 대전", "트로이아르케", "캐논", "유한양행", "브람스 안마의자"]
ROLES = ["스포츠 아나운서", "라이브커머스 쇼호스트", "마라톤 · 그란폰도 메인 MC", "기업 · VIP 행사 MC", "방송 리포터"]
CRAWL = [
    ("NEXT", "10.10 강서 허준런 메인 MC", "2026-10-10"), ("NEXT", "10.11 MBN 전국 나주 마라톤 메인 MC", "2026-10-11"),
    ("2026.09", "철원 DMZ 국제평화마라톤 개막 공식행사 MC · 12,000명"), ("2026.06", "KBS 뉴스 2026 월드컵 현장 인터뷰"),
    ("2026.06", "코오롱 트레일캠프 in 울릉 메인 MC"), ("LIVE", "네이버 쇼핑라이브 푸마 바디웨어 · 풀무원 · 아에르 · 오버더"),
    ("2026.01", "타린로즈 VIP 고객 초청행사 메인 MC"), ("2024—2026", "화천 DMZ 랠리 · 설악그란폰도 메인 MC"),
    ("2024.04", "크립토닷컴 코리아 런칭파티 MC"), ("2025.01", "채널A 〈스마트 도로〉 드라이버 출연"),
]

# ───────────────────────── helpers ─────────────────────────
def seg_head(no, label, title, sub, extra=""):
    return f'''<header class="seg-head">
      <div class="seg-meta mono"><b>{e(no)}</b><span>{e(label)}</span>{extra}</div>
      <h2 class="seg-title" data-split>{e(title)}</h2>
      <p class="seg-sub">{sub}</p>
    </header>'''

def cue_cards(items, seed):
    out = []
    for i, (d, t, r) in enumerate(items):
        rot = [-1.6, 1.1, -0.6, 1.8, -1.2, 0.7, -1.9, 1.4, -0.4][(i + seed) % 9]
        out.append(f'<li class="cue-card" style="--rot:{rot}deg"><span class="mono">{e(d)}</span><b>{e(t)}</b><span>{e(r)}</span></li>')
    return "\n".join(out)

def plat_badge(kind):
    return {"naver": f'<span class="plat" style="--pc:{NAVER}"><i></i>NAVER LIVE</span>',
            "yt": f'<span class="plat" style="--pc:{YT}"><i></i>YOUTUBE</span>',
            "ig": f'<span class="plat" style="--pc:{IG}"><i></i>INSTAGRAM</span>'}[kind]

def vod_row(n, url, title, meta, kind, thumb=None, dur="", land=False):
    th = (f'<span class="vod-thumb{" land" if land else ""}"><img src="{e(thumb)}" alt="" loading="lazy" decoding="async"></span>' if thumb
          else f'<span class="vod-thumb ph ph-{kind}" aria-hidden="true"><span>▶</span></span>')
    data_thumb = f' data-thumb="{e(thumb)}"' + (' data-land="1"' if land else '') if thumb else ""
    return f'''<li><a class="vod-row" href="{e(url)}" target="_blank" rel="noopener"{data_thumb} data-cursor="재생 ↗">
        <span class="vod-no mono">{n:02d}</span>{th}
        <span class="vod-main"><b>{e(title)}</b><span>{plat_badge(kind)}{meta}</span></span>
        <span class="vod-dur">{e(dur or "")}</span><span class="vod-arrow" aria-hidden="true">↗</span></a></li>'''

# ───────────────────────── sections ─────────────────────────
def hero():
    def crawl_item(item):
        if len(item) == 3:  # (label, text, date): "NEXT" until the day passes, then the date itself
            label, text, when = item
            past = when[:4] + "." + when[5:7] + "." + when[8:]
            text = text.split(" ", 1)[1] if text[:2].isdigit() else text
            return f'<span><em data-when="{when}" data-future="NEXT {e(when[5:].replace("-", "."))}" data-past="{past}">NEXT {e(when[5:].replace("-", "."))}</em>{e(text)}</span>'
        a, b = item
        return f'<span><em>{e(a)}</em>{e(b)}</span>'
    crawl = "".join(crawl_item(i) for i in CRAWL)
    return f'''
<section class="hero" id="top" data-chapter="ON AIR">
  <canvas class="hero-gl" aria-hidden="true"></canvas>
  <div class="hero-back" aria-hidden="true"><div class="hero-word" data-split>CHAEWON</div></div>
  <div class="hero-fig"><img class="hero-cut" src="assets/img/cut_pink_side.webp" width="591" height="1934" alt="핑크 스튜디오 배경 앞에서 미소 짓는 이채원" fetchpriority="high"></div>
  <div class="vf" aria-hidden="true">
    <i class="vf-c tl"></i><i class="vf-c tr"></i><i class="vf-c bl"></i><i class="vf-c br"></i>
    <div class="vf-rec"><i></i>REC <b class="js-tc">00:00:00:00</b></div>
    <div class="vf-spec">4K · 29.97P · ISO 400 · 1/60</div>
    <div class="vf-meter"><span><i></i></span><span><i></i></span><em>L</em><em>R</em></div>
    <div class="vf-focus"><b>AF · FACE</b></div>
    <div class="vf-cross"></div>
  </div>
  <div class="hero-front">
    <p class="hero-kicker mono"><i></i><span class="js-kicker">SPORTS · WELLNESS · FASHION · TECH</span></p>
    <h1 class="hero-title"><span class="ko" data-split>이채원</span><span class="en">LEE CHAEWON</span></h1>
    <p class="hero-copy">현장에는 에너지를, 방송에는 신뢰를 전하는 진행자</p>
    <div class="lt"><div class="lt-tag"><i></i>ON AIR</div><div class="lt-main"><b>이채원</b><span class="js-role" data-roles="{e('|'.join(ROLES))}">{e(ROLES[0])}</span></div></div>
    <p class="hero-next mono js-next" hidden></p>
  </div>
  <div class="crawl" role="marquee" aria-label="주요 이력 속보">
    <div class="crawl-label"><i></i>LIVE</div>
    <div class="crawl-vp"><div class="crawl-track">{crawl}</div></div>
  </div>
</section>'''

def prompter():
    lines = [
        '안녕하세요, 스포츠 아나운서이자 <mark>라이브커머스 쇼호스트 이채원</mark>입니다.',
        '마라톤 · 그란폰도 · 랠리의 <mark>출발선</mark>에서 현장을 이끌고,',
        '스튜디오에서는 <mark>한 시간</mark> 동안 브랜드의 이야기를 전합니다.',
        '안전한 운영 위에 <mark>최고의 즐거움</mark>을 더하는 진행.',
        '<mark>매출로 이어지는 진행</mark>, 브랜드를 빛내는 소통.',
        '현장에는 <mark>에너지</mark>를, 방송에는 <mark>신뢰</mark>를.',
        '<em>Be Healthy &amp; Wellthy.</em>',
    ]
    ls = "\n".join(f'<p class="pd-line">{l}</p>' for l in lines)
    return f'''
<section class="prompter seg" id="profile" data-chapter="PROMPTER">
  <div class="in">
    {seg_head("SEG 01", "PROMPTER", "HELLO, ON AIR", "마라톤 출발선과 라이브커머스 스튜디오, <strong>두 무대를 오가는 진행자</strong>의 인사말을 프롬프터로 읽어 보세요.")}
    <div class="pd">
      <div class="pd-top mono"><span><b>●</b> PROMPTER · CAM 1</span><span class="js-pd-count">01 / {len(lines):02d}</span></div>
      <div class="pd-win">
        <span class="pd-cue l" aria-hidden="true">▶</span><span class="pd-cue r" aria-hidden="true">◀</span>
        <div class="pd-lines">{ls}</div>
      </div>
      <div class="pd-foot mono"><span>SCROLL TO READ</span><span class="pd-bar"><i></i></span><span>이채원 · LEE CHAEWON</span></div>
    </div>
  </div>
</section>'''

def profile():
    return f'''
<section class="profile seg" data-chapter="PROFILE">
  <div class="in profile-grid">
    <figure class="frame">
      <div class="frame-img"><img src="assets/img/main_white_crouch.jpg" width="1187" height="1800" alt="흰 니트 크롭과 핑크 러닝화 차림으로 앉아 미소 짓는 이채원" loading="lazy" decoding="async"></div>
      <i class="crop tl"></i><i class="crop tr"></i><i class="crop bl"></i><i class="crop br"></i>
      <figcaption class="frame-cap mono"><i></i>CAM 2 · PROFILE</figcaption>
      <div class="frame-note mono"><span>168 CM</span><span>SPORTS · WELLNESS · FASHION · TECH</span></div>
    </figure>
    <div class="profile-side">
      {seg_head("SEG 02", "PROFILE", "PRESS PASS", "현장 출입증처럼 한 장에 정리한 기본 정보입니다. <strong>패션 방송 피팅 사이즈</strong>도 함께 적었습니다.")}
      <div class="pass-wrap">
        <div class="lanyard" aria-hidden="true"><span>ON AIR · 이채원 · ON AIR · 이채원 · ON AIR</span></div>
        <article class="pass" aria-label="이채원 프로필 카드">
          <div class="pass-top"><b>STAFF · MC</b><span class="mono">ALL ACCESS</span></div>
          <div class="pass-body">
            <div class="pass-photo"><img src="assets/img/main_headshot.jpg" width="411" height="517" alt="흰 오프숄더 니트를 입은 이채원 프로필 사진" loading="lazy"></div>
            <div class="pass-info"><h3>이채원</h3><p class="mono">LEE CHAEWON</p><p>스포츠 아나운서<br>라이브커머스 쇼호스트<br>행사 MC · 리포터</p></div>
          </div>
          <div class="pass-code"><i aria-hidden="true"></i><span class="mono"><span>@c._.1ee</span><span>BE HEALTHY &amp; WELLTHY</span></span></div>
        </article>
      </div>
      <p class="spec-cap mono">FITTING INFO</p>
      <dl class="spec">
        <dt class="mono">HEIGHT</dt><dd>168cm</dd>
        <dt class="mono">TOP</dt><dd>44반 – 55</dd>
        <dt class="mono">BOTTOM</dt><dd>25inch</dd>
        <dt class="mono">SHOES</dt><dd>235 – 240mm</dd>
        <dt class="mono">EDUCATION</dt><dd>남서울대학교 국제유통학과 졸업</dd>
        <dt class="mono">FIELD</dt><dd>스포츠 · 웰니스 · 패션 · 테크</dd>
      </dl>
    </div>
  </div>
</section>'''

def score():
    return '''
<section class="score" data-chapter="RECORD">
  <div class="in">
    <div class="board" role="group" aria-label="진행 기록 전광판">
      <div class="board-top mono"><span><b>●</b> ON AIR RECORD</span><span>2022 — 2026</span></div>
      <div class="board-grid">
        <div class="stat wide"><div class="odo" data-to="12000">12,000</div><p>러너 앞에서 연 개막 무대<small>2026 철원 DMZ 국제평화마라톤 · 한국일보 보도</small></p></div>
        <div class="stat"><div class="odo" data-to="14">14</div><p>스포츠 대회 · 행사 MC</p></div>
        <div class="stat"><div class="odo" data-to="20">20</div><p>라이브커머스 방송 포트폴리오</p></div>
        <div class="stat"><div class="odo" data-to="9">9</div><p>기업 · VIP 행사 MC</p></div>
        <div class="stat"><div class="odo" data-to="7">7</div><p>TV 방송 출연</p></div>
      </div>
      <div class="board-foot mono"><span>HOME · 이채원</span><span>FULL COURSE · 42.195 KM</span></div>
    </div>
  </div>
</section>'''

def ident(kind):
    if kind == "sports":
        return '''
<section class="ident ident--sports" id="sports" data-chapter="CH 1 · SPORTS">
  <canvas class="ident-static" aria-hidden="true"></canvas>
  <div class="ident-osd" aria-hidden="true">CH 01<small>SPORTS</small></div>
  <div class="ident-card">
    <span class="ident-ch mono"><i></i>CHANNEL 1</span>
    <h2 class="ident-title"><span data-split>SPORTS</span><span class="alt" data-split>ANNOUNCER</span></h2>
    <p class="ident-sub">안전한 운영 위에 <mark>최고의 즐거움</mark>을 더하는 진행</p>
  </div>
</section>'''
    return '''
<section class="ident ident--live" id="live" data-chapter="CH 2 · LIVE">
  <canvas class="ident-static" aria-hidden="true"></canvas>
  <div class="ident-osd" aria-hidden="true">CH 02<small>LIVE</small></div>
  <div class="ident-card">
    <span class="ident-ch mono"><i></i>CHANNEL 2</span>
    <h2 class="ident-title"><span data-split>LIVE</span><span class="alt" data-split>COMMERCE</span></h2>
    <p class="ident-sub"><mark>매출로 이어지는 진행</mark>, 브랜드를 빛내는 소통</p>
  </div>
</section>'''

def course():
    lis = []
    cpn = 0
    for c in COURSE:
        if c["kind"] == "photo":
            lis.append(f'''<li class="cp cp--photo"><i class="cp-dot"></i><i class="cp-stem"></i><div class="cp-card"><figure>
          <img src="assets/img/{c['img']}" width="{c['w']}" height="{c['h']}" alt="{e(c['alt'])}" loading="lazy" decoding="async">
          <figcaption class="mono"><span>{e(c['cap'])}</span><span>{e(c['right'])}</span></figcaption></figure></div></li>''')
            continue
        if c["kind"] == "flag":
            lis.append(f'''<li class="cp cp--flag" data-name="{e(c['top'])}"><i class="cp-dot"></i><i class="cp-stem"></i><div class="cp-card"><div class="checker"></div>
          <div class="cp-top mono"><b>{e(c['top'])}</b><span>{e(c['right'])}</span></div><h3>{e(c['title'])}</h3><p>{e(c['desc'])}</p></div></li>''')
            continue
        cpn += 1
        vid = (f'<a class="cp-vid mono" href="{e(c["video"])}" target="_blank" rel="noopener" data-cursor="영상 ↗">▶ 공식 영상 ↗</a>' if c.get("video") else "")
        if c.get("when"):  # upcoming race: "· NEXT" / "· 예정" disappear once the day has passed
            right = f'<span data-when="{c["when"]}" data-future=" · {e(c["right"])}" data-past=""> · {e(c["right"])}</span>'
            soon = f'<span data-when="{c["when"]}" data-future=" · 예정" data-past=""> · 예정</span>'
        else:
            right = (" · " + e(c['right'])) if c['right'] else ""
            soon = ""
        lis.append(f'''<li class="cp" data-name="CP {cpn:02d} · {e(c['title'])}"><i class="cp-dot"></i><i class="cp-stem"></i><div class="cp-card">
          <div class="cp-top mono"><b>CP {cpn:02d}</b><span>{e(c['top'])}{right}</span></div>
          <h3>{e(c['title'])}</h3><p>{e(c['desc'])}{soon}</p>{vid}</div></li>''')
    up = "".join(f'<li data-date="{d}"><span class="mono up-d">{d[5:].replace("-", ".")}</span><b>{e(n)}</b><span class="mono up-state">메인 MC</span></li>' for d, n in UPCOMING)
    press = "".join(f'<li><a href="{e(u)}" target="_blank" rel="noopener" data-cursor="기사 ↗"><span class="mono">{e(s)}</span><b>{e(t)}</b><i aria-hidden="true">↗</i></a></li>' for s, t, u in PRESS)
    return f'''
<section class="course seg" data-chapter="RACE DAY">
  <div class="in">
    {seg_head("SEG 03", "RACE DAY", "RACE DAY", "마라톤 · 그란폰도 · 랠리의 <strong>출발선 메인 MC</strong>. 2024년부터 같은 대회 무대에 해마다 다시 서고 있습니다.", "<span>2024 — 2026</span>")}
    <div class="race-top">
      <blockquote class="press-q">
        <p>개막 공식행사 사회는 개그맨 전환규씨와 이채원 아나운서가 맡아 재치 있는 입담으로 출발선 앞에 선 참가자의 긴장을 풀어줬다.</p>
        <footer class="mono"><a href="https://www.hankookilbo.com/news/article/A2026090513470000105" target="_blank" rel="noopener" data-cursor="기사 ↗">한국일보 · 2026.09.05 · 철원 DMZ 국제평화마라톤 ↗</a></footer>
      </blockquote>
      <div class="upnext">
        <p class="mono upnext-cap"><span class="dot"></span>2026 하반기 진행 일정</p>
        <ol>{up}</ol>
      </div>
    </div>
  </div>
  <div class="course-pin">
    <div class="in course-hud mono"><span>KM <b class="js-km">0.000</b> / 42.195</span><span class="cp-now js-cpnow">START LINE</span><span class="course-hint">SCROLL →</span></div>
    <div class="course-track">
      <svg class="course-svg" aria-hidden="true"><path class="route-bg"></path><path class="route"></path></svg>
      <div class="runner" aria-hidden="true" data-km="0.0 KM"></div>
      <ol class="cps">{"".join(lis)}</ol>
    </div>
  </div>
  <div class="in">
    <ul class="press-list">{press}</ul>
  </div>
</section>'''

def pit():
    return f'''
<section class="pit seg" data-chapter="MOTORSPORTS">
  <div class="in">
    {seg_head("SEG 04", "PIT LANE", "MOTORSPORTS", "서킷과 랠리, 브랜드 클럽 행사, 자동차 라이브까지. <strong>모터스포츠 현장</strong>에서도 꾸준히 활동하고 있습니다.")}
    <div class="pit-grid">
      <div class="pit-left">
        <div class="gauge" aria-hidden="true"><svg class="js-gauge" viewBox="0 0 400 400"></svg>
          <div class="gauge-read"><b class="js-speed">120</b><span class="mono">KM/H</span></div><div class="gauge-gear js-gear">6</div></div>
        <div class="quote-cap">
          <div class="who">이채원 <span>/ 드라이버</span></div>
          <blockquote>최초로 120km/h 구간을 달려봐서 굉장히 속이 뻥 뚫리는 쾌감을 즐길 수 있었고요</blockquote>
          <cite class="mono">채널A 특별기획 〈먼저 만나는 미래, 스마트 도로〉 · 2025.01.04</cite>
        </div>
      </div>
      <div class="pit-right">
        <ul class="pit-list">
          <li><b>BMW M클럽 코리아 신년회 MC</b><span class="mono">2024 — 2026</span></li>
          <li><b>화천 DMZ 랠리 메인 MC</b><span class="mono">2024 — 2026</span></li>
          <li><b>채널A 〈스마트 도로〉 드라이버 출연</b><span class="mono">2025.01</span></li>
          <li><b>리본카 자동차 라이브 고정 진행</b><span class="mono">2025 —</span></li>
          <li><b>현대 N 페스티벌 · 람보르기니 슈퍼 트로페오 현장</b><span class="mono">2024 · 2026</span></li>
        </ul>
        <figure class="pit-photo"><img src="assets/img/ev_bmw.jpg" width="1067" height="1600" alt="BMW M Club Korea 신년회 백월 앞에서 포즈를 취한 이채원" loading="lazy" decoding="async"><figcaption class="mono">BMW M CLUB KOREA · NEW YEAR PARTY</figcaption></figure>
      </div>
    </div>
  </div>
</section>'''

def tv():
    slides, rows = [], []
    for i, t in enumerate(TV):
        bars = "".join(f'<i style="background:{c}"></i>' for c in BARS)
        slides.append(f'''<div class="tv-slide{" on" if i == 0 else ""}" style="--bg:{t['bg']}" data-ch="{e(t['ch'])}">
          <span class="s-bars" aria-hidden="true">{bars}</span>
          <span class="s-ch">{e(t['ch'])}</span><span class="s-title">{e(t['title'])}</span>
          <span class="s-meta mono"><span>{e(t['date'])}</span><span>{e(t['role'])}</span><span>이채원</span></span></div>''')
        link = (f'<a class="e-link mono" href="{e(t["link"])}" target="_blank" rel="noopener" data-cursor="영상 ↗">영상 ↗</a>' if t["link"] else "")
        rows.append(f'''<li class="{"has-link" if t["link"] else ""}"><button type="button" class="{"on" if i == 0 else ""}" data-i="{i}" aria-pressed="{"true" if i == 0 else "false"}">
          <span class="e-ch">{e(t['ch'])}</span><span class="e-date mono">{e(t['date'])}</span>
          <span class="e-title"><b>{e(t['title'])}</b><span>{e(t['role'])}</span></span></button>{link}</li>''')
    return f'''
<section class="tv seg" data-chapter="ON TV">
  <div class="in">
    {seg_head("SEG 05", "ON TV", "ON TV", "뉴스 인터뷰부터 생방송 리포터, 다큐 드라이버, 예능 출연까지. <strong>편성표를 눌러 채널을 돌려 보세요.</strong>")}
    <div class="tv-grid">
      <div class="tvset" aria-hidden="true">
        <div class="tv-screen">{"".join(slides)}<canvas class="tv-static"></canvas><div class="tv-osd js-osd">CH 1</div></div>
        <div class="tv-knobs mono"><span><i></i><i></i></span><span>이채원 ON TV</span></div>
      </div>
      <ol class="epg">{"".join(rows)}</ol>
    </div>
  </div>
</section>'''

def stage():
    return f'''
<section class="stage seg" data-chapter="ON STAGE">
  <div class="truss" aria-hidden="true"></div>
  <div class="beam b1" aria-hidden="true"></div><div class="beam b2" aria-hidden="true"></div><div class="beam b3" aria-hidden="true"></div>
  <div class="spot" aria-hidden="true"></div>
  <div class="in">
    {seg_head("SEG 06", "ON STAGE", "ON STAGE", "기업 VIP 행사와 런칭 파티, 아이들의 싱어롱쇼, 축제 현장 리포팅까지. <strong>무대마다 큐카드 한 장씩.</strong>")}
    <div class="stage-grid">
      <div class="stage-photos">
        <figure class="shot tall"><img src="assets/img/ev_yeoncheon.jpg" width="1179" height="1572" alt="연천 청소년 AI센터 개관식 무대 앞에 선 이채원" loading="lazy" decoding="async"><figcaption class="mono"><span>연천 청소년 AI센터 개관식</span><span>2025.06</span></figcaption></figure>
        <figure class="shot wide"><img src="assets/img/ev_interview.jpg" width="1600" height="1067" alt="야외 행사장에서 히잡을 쓴 참가자를 인터뷰하는 이채원" loading="lazy" decoding="async"><figcaption class="mono"><span>현장 인터뷰</span><span>REPORTER</span></figcaption></figure>
      </div>
      <div class="decks">
        <div class="deck"><h3>CORPORATE · VIP <span>{len(CORPORATE):02d}</span></h3><ul class="cards">{cue_cards(CORPORATE, 0)}</ul></div>
        <div class="deck"><h3>RECREATION · KIDS <span>{len(RECREATION):02d}</span></h3><ul class="cards">{cue_cards(RECREATION, 3)}</ul></div>
        <div class="deck"><h3>REPORTER <span>{len(REPORTER):02d}</span></h3><ul class="cards">{cue_cards(REPORTER, 5)}</ul></div>
      </div>
    </div>
  </div>
</section>'''

def multiview():
    chips = []
    for k, label in CATS:
        n = len(LIVE) if k == "all" else sum(1 for x in LIVE if x["cat"] == k)
        chips.append(f'<button type="button" class="chip" data-f="{k}" aria-pressed="{"true" if k == "all" else "false"}">{e(label)}<em>{n}</em></button>')
    mons = []
    for i, x in enumerate(LIVE):
        w, h = x.get("w", 536), x.get("h", 860)
        img = f'<img src="assets/live/{x["f"]}.jpg" width="{w}" height="{h}" alt="{e(x["brand"])} 라이브 방송을 진행하는 이채원" loading="lazy" decoding="async">'
        plat = "YOUTUBE" if x.get("plat") == "yt" else "NAVER LIVE"
        if x["url"]:
            dur_tag = f'<span>{e(x["dur"])}</span>' if x.get("dur") else "<span>SHORTS</span>"
            badge = f'<span class="rp">REPLAY</span>{dur_tag}'
            mons.append(f'''<a class="mon" data-cat="{x['cat']}" href="{e(x['url'])}" target="_blank" rel="noopener" data-cursor="다시보기 ↗">
          <span class="mon-screen">{img}<span class="mon-badge">{badge}</span><span class="mon-tally" aria-hidden="true"></span><span class="mon-go">다시보기<span>↗</span></span></span>
          <span class="mon-label"><span>CAM {i + 1:02d}</span><b>{e(x['brand'])}</b></span>
          <span class="mon-title">{e(x['title'])}</span><span class="mon-date">{e(x['date'])} · {plat}</span></a>''')
        else:
            mons.append(f'''<div class="mon" data-cat="{x['cat']}">
          <span class="mon-screen">{img}<span class="mon-badge"><span>ON AIR</span></span><span class="mon-tally" aria-hidden="true"></span></span>
          <span class="mon-label"><span>CAM {i + 1:02d}</span><b>{e(x['brand'])}</b></span>
          <span class="mon-title">{e(x['title'])}</span><span class="mon-date">{e(x['date'])} · 방송 화면</span></div>''')
    more = "".join(f"<li>{e(m)}</li>" for m in MORE_AIR)
    return f'''
<section class="mv seg" data-chapter="MULTIVIEW">
  <div class="in">
    {seg_head("SEG 07", "MULTIVIEW", "MULTIVIEW", "패션 · 웰니스 · 리빙 · 여행 라이브커머스 방송 화면입니다. <strong>REPLAY 표시가 있는 화면을 누르면 다시보기가 열립니다.</strong>")}
    <div class="mv-head">
      <div class="chips" role="group" aria-label="카테고리 필터">{"".join(chips)}</div>
      <p class="mono mv-legend"><span class="lg pgm"></span>PGM 송출 <span class="lg pvw"></span>PVW 대기</p>
    </div>
    <div class="mv-wall">{"".join(mons)}</div>
    <div class="more-air"><p class="mono">MORE ON AIR · 그 밖의 진행 브랜드와 방송</p><ul>{more}</ul></div>
  </div>
</section>'''

def vod():
    rows_n = []
    n = 0
    for x in LIVE:
        if x["url"] and x.get("plat") != "yt":
            n += 1
            rows_n.append(vod_row(n, x["url"], x["title"], f'{e(x["brand"])} · {e(x["date"])}', "naver", f'assets/live/{x["f"]}.jpg', x["dur"]))
    rows_y = []
    for y in YOUTUBE:
        n += 1
        rows_y.append(vod_row(n, y["url"], y["title"], e(y["meta"]), "yt", y.get("thumb"), y.get("dur", ""), land=y.get("land", False)))
    rows_o = []
    for y in EVENT_VIDEOS:
        n += 1
        rows_o.append(vod_row(n, y["url"], y["title"], e(y["meta"]), "yt", y.get("thumb"), y.get("dur", ""), land=True))
    rows_i = []
    for y in INSTAGRAM:
        n += 1
        rows_i.append(vod_row(n, y["url"], y["title"], e(y["meta"]), "ig"))
    total = n
    return f'''
<section class="vod seg" id="vod" data-chapter="VOD">
  <div class="in">
    {seg_head("SEG 08", "VOD LIBRARY", "VOD LIBRARY", f"영상은 모두 <strong>원본 링크 {total}개</strong>로 정리했습니다. 누르면 새 창에서 열립니다.")}
    <p class="vod-group mono">NAVER SHOPPING LIVE · 다시보기 {len(rows_n)}</p>
    <ol class="vod-list">{"".join(rows_n)}</ol>
    <p class="vod-group mono">YOUTUBE · 방송인 이채원 채널 {len(rows_y)}</p>
    <ol class="vod-list">{"".join(rows_y)}</ol>
    <p class="vod-group mono">BROADCAST · 방송사 · 행사 공식 영상 {len(rows_o)}</p>
    <ol class="vod-list">{"".join(rows_o)}</ol>
    <p class="vod-group mono">INSTAGRAM · @c._.1ee {len(rows_i)}</p>
    <ol class="vod-list">{"".join(rows_i)}</ol>
    <p class="vod-note">방송사 · 행사 공식 영상은 진행 장면이 일부 구간에만 나와서, 확인된 시점을 제목에 적었습니다.</p>
  </div>
</section>'''

def brands():
    def row(items):
        return "".join(f'<span>{e(b)}</span><span class="sep" aria-hidden="true">✦</span>' for b in items)
    return f'''
<section class="brands" aria-label="함께한 브랜드와 방송사">
  <div class="in brands-cap mono"><span>WORKED WITH</span><span>BRANDS · BROADCASTERS · EVENTS</span></div>
  <div class="mq-vp"><div class="marquee js-mq" data-dir="-1">{row(BRANDS_A)}</div></div>
  <div class="mq-vp"><div class="marquee outline js-mq" data-dir="1">{row(BRANDS_B)}</div></div>
</section>'''

def cue():
    rows = []
    for i, (when, item, cat, cls, dur) in enumerate(CAREER):
        rows.append(f'''<li class="sheet-row"><span class="r-no">{i + 1:02d}</span><span class="r-when">{e(when)}</span><span class="r-item" data-text="{e(item)}">{e(item)}</span>
          <span class="r-cat {cls}">{e(cat)}</span><span class="r-dur{" live" if cls == "onair" else ""}">{e(dur)}</span></li>''')
    return f'''
<section class="cue seg" id="career" data-chapter="CUE SHEET">
  <div class="in">
    {seg_head("SEG 09", "CUE SHEET", "CUE SHEET", "학력과 경력, 수상 이력을 <strong>방송 큐시트 순서</strong>대로 정리했습니다.")}
    <div class="sheet">
      <div class="sheet-head mono"><span>PROGRAM <b>이채원 ON AIR</b></span><span>HOST <b>LEE CHAEWON</b></span><span>UPDATED <b>2026.10</b></span></div>
      <div class="sheet-cols mono" aria-hidden="true"><span>NO</span><span>PERIOD</span><span>ITEM</span><span>CATEGORY</span><span style="text-align:right">DUR</span></div>
      <ol class="sheet-list">{"".join(rows)}</ol>
      <div class="sheet-now" aria-hidden="true"><span>NOW</span></div>
    </div>
  </div>
</section>'''

def offair():
    def credits(hidden=False):
        aria = ' aria-hidden="true"' if hidden else ""
        sports = " · ".join(c["title"] for c in COURSE if c["kind"] == "cp")
        tvs = " · ".join(t["title"] for t in TV)
        corp = " · ".join(t for _, t, _ in CORPORATE)
        rec = " · ".join(t for _, t, _ in RECREATION + REPORTER)
        live = " · ".join(dict.fromkeys(x["brand"] for x in LIVE))
        return f'''<div class="credits-set"{aria}>
          <div class="cr-block"><h4>Presented by</h4><p class="cr-big">이채원</p><p>LEE CHAEWON</p></div>
          <div class="cr-block"><h4>Host</h4><p>스포츠 아나운서 · 라이브커머스 쇼호스트 · 행사 MC · 리포터</p></div>
          <div class="cr-block"><h4>Sports</h4><p>{e(sports)}</p></div>
          <div class="cr-block"><h4>On TV</h4><p>{e(tvs)}</p></div>
          <div class="cr-block"><h4>Corporate · VIP</h4><p>{e(corp)}</p></div>
          <div class="cr-block"><h4>Recreation · Reporter</h4><p>{e(rec)}</p></div>
          <div class="cr-block"><h4>Live Commerce</h4><p>{e(live)}</p></div>
          <div class="cr-block"><h4>Motto</h4><p>Be Healthy &amp; Wellthy</p></div>
        </div>'''
    return f'''
<section class="offair seg" id="contact" data-chapter="OFF AIR">
  <div class="in">
    <div class="off-grid">
      <div class="off-visual"><img src="assets/img/cut_pink_full.webp" width="460" height="1664" alt="핑크 스튜디오에서 한 손을 머리 위로 올린 이채원 전신 사진" loading="lazy" decoding="async"><span class="off-sign mono js-offsign"><i></i><span>ON AIR</span></span></div>
      <div class="off-copy">
        <div class="seg-meta mono"><b>SEG 10</b><span>CLOSING</span><span>CONTACT</span></div>
        <h2 class="off-h"><mark>안전은 기본, 즐거움은 완성.</mark><br>모두가 웃으며 기억하는 <mark>현장을 만들겠습니다.</mark></h2>
        <p class="off-sub">현장에는 에너지를, 방송에는 신뢰를 전하는 진행자 이채원</p>
        <p class="off-motto">Be Healthy &amp; Wellthy</p>
        <div class="contact">
          <div class="c-row"><span class="mono">PHONE</span><b>010-5091-6614</b><button class="c-btn" type="button" data-copy="010-5091-6614" data-cursor="복사">복사</button></div>
          <div class="c-row"><span class="mono">E-MAIL</span><b>yh15325@naver.com</b><button class="c-btn" type="button" data-copy="yh15325@naver.com" data-cursor="복사">복사</button></div>
          <div class="c-row"><span class="mono">INSTAGRAM</span><a class="val" href="https://www.instagram.com/c._.1ee/" target="_blank" rel="noopener">@c._.1ee</a><a class="c-btn" href="https://www.instagram.com/c._.1ee/" target="_blank" rel="noopener" data-cursor="열기 ↗">열기 ↗</a></div>
          <div class="c-row"><span class="mono">YOUTUBE</span><a class="val" href="https://www.youtube.com/@chea_1ee" target="_blank" rel="noopener">방송인 이채원</a><a class="c-btn" href="https://www.youtube.com/@chea_1ee" target="_blank" rel="noopener" data-cursor="열기 ↗">열기 ↗</a></div>
        </div>
      </div>
    </div>
    <div class="credits" aria-label="엔딩 크레딧"><div class="credits-roll">{credits()}{credits(True)}</div></div>
    <div class="signoff"><div class="signoff-tv"><b>OFF AIR</b><i></i></div><p class="mono">THANK YOU FOR WATCHING · 이채원</p></div>
    <footer class="foot mono"><span>© 2026 이채원 LEE CHAEWON</span><span>PORTFOLIO · DRAFT</span></footer>
  </div>
</section>'''

NAV = [("profile", "PROFILE"), ("sports", "SPORTS"), ("live", "LIVE"), ("vod", "VOD"), ("career", "CAREER"), ("contact", "CONTACT")]

def chrome_top():
    nav = "".join(f'<a href="#{i}" data-nav="{i}">{l}</a>' for i, l in NAV)
    menu = "".join(f'<a href="#{i}" data-nav="{i}"><span>{n + 1:02d}</span>{l}</a>' for n, (i, l) in enumerate(NAV))
    return f'''
<div class="grain" aria-hidden="true"></div>
<header class="bar">
  <a class="bar-brand glass" href="#top" aria-label="맨 위로"><span class="tally js-tally"><i></i><span>ON AIR</span></span><span class="bar-name">이채원<small>LEE CHAEWON</small></span></a>
  <div class="bar-tc glass" aria-hidden="true"><span>TC</span><b class="js-tc">00:00:00:00</b></div>
  <nav class="bar-nav glass" aria-label="섹션 이동">{nav}</nav>
  <button class="menu-btn" type="button" aria-expanded="false" aria-controls="menu">RUNDOWN</button>
</header>
<div class="menu" id="menu" hidden><button class="menu-close" type="button">CLOSE ✕</button>{menu}</div>'''

def chrome_bottom():
    return '''
<div class="scrub glass" aria-hidden="true"><span class="scrub-now"><b class="js-segno">01</b><span class="js-segname">ON AIR</span></span>
  <span class="scrub-track"><span class="scrub-fill"></span><span class="scrub-head"></span></span><span class="scrub-count js-segcount">01 / 15</span></div>
<div class="cursor" aria-hidden="true"><div class="cursor-ring"><span class="cursor-label"></span></div><div class="cursor-dot"></div></div>
<div class="vod-preview" aria-hidden="true"><img alt=""></div>
<div class="toast" role="status" aria-live="polite"></div>'''

CDN = [
    "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.13.0/gsap.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.13.0/ScrollTrigger.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.13.0/ScrambleTextPlugin.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.13.0/Flip.min.js",
    "https://cdn.jsdelivr.net/npm/lenis@1.3.26/dist/lenis.min.js",
]

# ───────────────────────── fonts (Pretendard, official dynamic subsets) ─────────────────────────
PRET_BASE = "https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/variable/"

def parse_ranges(ur):
    out = []
    for part in ur.split(","):
        part = part.strip().upper().replace("U+", "")
        if "-" in part:
            a, b = part.split("-"); out.append((int(a, 16), int(b, 16)))
        elif "?" in part:
            out.append((int(part.replace("?", "0"), 16), int(part.replace("?", "F"), 16)))
        else:
            v = int(part, 16); out.append((v, v))
    return out

def font_faces(text):
    FONT_CACHE.mkdir(parents=True, exist_ok=True)
    css_p = FONT_CACHE / "dyn.css"
    if not css_p.exists():
        css_p.write_bytes(subprocess.run(["curl", "-sL", PRET_BASE + "pretendardvariable-dynamic-subset.css"], capture_output=True, check=True).stdout)
    css = css_p.read_text()
    used = {ord(c) for c in text}
    faces = []
    for m in re.finditer(r"src:\s*url\(\./(woff2-dynamic-subset/[^)]+)\)[^;]*;\s*unicode-range:\s*([^;]+);", css):
        path, ur = m.group(1), m.group(2)
        ranges = parse_ranges(ur)
        if not any(a <= cp <= b for cp in used for a, b in ranges):
            continue
        f = FONT_CACHE / pathlib.Path(path).name
        if not f.exists():
            f.write_bytes(subprocess.run(["curl", "-sL", PRET_BASE + path], capture_output=True, check=True).stdout)
        b64 = base64.b64encode(f.read_bytes()).decode()
        faces.append(f"@font-face{{font-family:'Pretendard Variable';font-style:normal;font-display:swap;font-weight:45 920;"
                     f"src:url(data:font/woff2;base64,{b64}) format('woff2-variations');unicode-range:{ur.strip()}}}")
    lic = "/* Pretendard — Copyright (c) 2021 Kil Hyung-jin, SIL Open Font License 1.1. Official dynamic-subset files, unmodified. */"
    return lic + "\n" + "\n".join(faces), len(faces)

# ───────────────────────── assemble ─────────────────────────
def main():
    css = (HERE / "styles.css").read_text() + "\n" + (HERE / "extra.css").read_text()
    js = (HERE / "app.js").read_text()
    body = "\n".join([chrome_top(), '<main id="main">', hero(), prompter(), profile(), score(), ident("sports"), course(), pit(), tv(), stage(),
                      ident("live"), multiview(), vod(), brands(), cue(), offair(), "</main>", chrome_bottom()])
    scripts = "\n".join(f'<script src="{u}"></script>' for u in CDN) + f"\n<script>\n{js}\n</script>"
    glyph_text = body + js + "".join(chr(c) for c in range(0x20, 0x7F)) + "가나다라마바사아자차카타파하·—–“”‘’↗▶◀✦●✕→←↑↓"
    faces, nfaces = font_faces(glyph_text)
    title = "<title>이채원 ON AIR</title>\n<meta name=\"description\" content=\"스포츠 아나운서 · 라이브커머스 쇼호스트 이채원의 방송 콘셉트 포트폴리오\">"
    page = f"{title}\n<style>\n{faces}\n{css}\n</style>\n{body}\n{scripts}\n"
    (ROOT / "index.html").write_text(page)
    site = "https://yeongyu.me/chaewon.lee.portfolio/"
    og = (f'<link rel="canonical" href="{site}">\n'
          '<meta property="og:type" content="website">\n'
          '<meta property="og:title" content="이채원 ON AIR — 스포츠 아나운서 · 라이브커머스 쇼호스트">\n'
          '<meta property="og:description" content="마라톤 출발선의 메인 MC부터 라이브커머스 스튜디오까지. 이채원의 방송 포트폴리오.">\n'
          f'<meta property="og:url" content="{site}">\n'
          f'<meta property="og:image" content="{site}assets/img/og.jpg">\n'
          '<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n'
          '<meta name="twitter:card" content="summary_large_image">\n'
          '<meta name="theme-color" content="#FE8AAD">\n'
          '<link rel="icon" href="assets/favicon/favicon.svg" type="image/svg+xml">\n'
          '<link rel="icon" href="assets/favicon/favicon-32.png" sizes="32x32" type="image/png">\n'
          '<link rel="icon" href="assets/favicon/favicon.ico" sizes="16x16 32x32 48x48">\n'
          '<link rel="apple-touch-icon" href="assets/favicon/apple-touch-icon.png">')
    full = ("<!doctype html>\n<html lang=\"ko\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\">\n"
            f"{title}\n{og}\n<style>\n{faces}\n{css}\n</style>\n</head>\n<body>\n{body}\n{scripts}\n</body>\n</html>\n")
    # GitHub Pages output: a full document plus only the assets the page references
    docs = ROOT.parent / "docs"
    if docs.exists(): shutil.rmtree(docs)
    (docs / "assets").mkdir(parents=True)
    (docs / "index.html").write_text(full)
    (docs / ".nojekyll").write_text("")
    used = set(re.findall(r'assets/[\w\-./]+\.(?:jpg|jpeg|png|webp)', body)) | {"assets/img/og.jpg"}
    used |= {f"assets/favicon/{n}" for n in ("favicon.svg", "favicon-32.png", "favicon-16.png", "favicon.ico", "apple-touch-icon.png", "icon-512.png")}
    for u in sorted(used):
        src = ROOT / u
        if src.exists():
            (docs / u).parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, docs / u)
    print(f"index.html {len(page)/1024:.0f} KB · font subsets {nfaces} · youtube rows {len(YOUTUBE)}")

if __name__ == "__main__":
    main()
