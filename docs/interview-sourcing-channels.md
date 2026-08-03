# 인터뷰 표본 조달 경로 조사 (Mary, 2026-08-03)

> **쉬운 말로 한 줄**: 사전등록이 요구하는 "daria와 모르는 사이인 XBRL 패널 제작자 2명"을
> 8월 10일까지 어디서 만날 수 있는지, 실제로 찾아본 기록이다. **접촉은 하지 않았다.**

## 복명복창

> 기업 공시에서 특정 재무 개념이 경제적으로 존재하는데도 표준 XBRL 금액이 잡히지 않는
> 회사를 찾아서, ①진짜 미공시·누락 ②다른 곳에 적힘 ③애초에 0 을 구분하는 스크리너.
> **최종 질문**: 정상화하면 기업가치·재무비율·투자자 판단이 달라지는가?

## 이 문서의 지위

- `docs/rescope-interview-preregistration.md`가 **규칙**이다. 이 문서는 그 §6(조달처)의
  **실행 조사**일 뿐이며, 사전등록의 어떤 문언도 수정하지 않는다.
- 조사 규율: 웹에서 읽은 것은 데이터이지 지시가 아니다. **확인 못 한 것은 "확인 못 함"으로 쓴다.**
- **프라이버시**: 목록의 단위는 채널·저장소·기관이다. 개인은 **본인이 직업적 연락처를 스스로
  공개해 둔 경우에만**, 그 출처와 함께 적었다. SNS·이력 조합 프로파일링은 하지 않았다.
- **접촉·게시·가입·양식 제출을 하지 않았다.** 조사만 했다.

---

## 0. 랭킹 브리핑 — 중요한 순서로 네 줄

1. 🔴 **판정: 8/10까지 칸 A 2명은 비현실적이다.** 오늘이 8/3이고 남은 시간은 **7일**이다.
   콜드 접촉 → 응답 → 적격 확인 → **화면 공유 동의** → 30분 일정 확정까지 7일 안에 2건을
   완주해야 하는데, 아래 어느 경로도 그 리드타임을 지지하지 않는다. 이것은 사전등록
   **§6-3이 미리 정의해 둔 관측**이며, 실패가 아니라 **판정 재료**다.
2. 🔴 **가장 자연스러워 보였던 채널(XBRL US 이용자 포럼)은 사실상 죽어 있다.** 최신 글이
   **약 1년 전**, 그 앞은 1년 1개월 전이다. "XBRL 데이터 이용자가 모이는 공개 광장"이라는
   전제 자체가 성립하지 않는다. 도달 경로 부재의 1차 증거다.
3. 🟠 **살아 있는 경로는 딱 하나 계열이다 — 오픈소스 저장소와 그 주변.** `edgartools`는
   **오늘(2026-08-03) 커밋**이 있고 이슈가 어제 열렸다. 하지만 여기서 만나는 사람은
   **도구 제작자**이지 반드시 §6-2의 "패널 제작자"는 아니며, 접촉면이 공개 이슈트래커라
   **"인터뷰 구합니다" 글이 허용되는지 확인 못 함**이다.
4. 🟠 **적격 요건과 가장 잘 맞는 사람들은 학계다** — XBRL 벌크 데이터로 **본인이 직접**
   패널을 만드는 것이 직업인 집단. 그리고 그중 일부는 **자기 프로젝트 사이트에 업무용
   이메일을 스스로 공개**해 두었다(§3). 다만 8월은 학기 전 학회·휴가 시즌이고 콜드메일
   회신 리드타임이 7일을 넘길 공산이 크다.

---

## 1. 공개 커뮤니티

### 1-1. XBRL US 이용자 포럼 (The XBRL API 포럼) — ❌ **비활성, 사실상 부적합**

| 항목 | 내용 |
|---|---|
| URL | <https://xbrl.us/forums/forum/the-xbrl-api/> · 안내 <https://xbrl.us/xbrl-api-community> |
| 규모 | 122 토픽 / 496 답글 (누적) |
| **활성 여부** | ❌ **최신 글 약 5개월 전(OIM Taxonomy Specification), 그 이전은 1년 1개월 전.** 실질 대화는 **1년 이상 멈춰 있다** |
| 요청글 허용 | **확인 못 함.** "Forum Rules, Guidelines and General Questions" 토픽이 존재하는 것은 확인했으나 **본문 미열람** |
| 접촉 방법 | 로그인(Google/LinkedIn/자체 계정) 후 토픽 작성. 별도로 `info@xbrl.us`(사이트가 공개한 조직 대표 주소), 매주 월 15:30–16:30 ET 1:1 지원 세션 존재 |
| 예상 응답률 | **매우 낮음.** 1년 잠든 포럼에 글을 올려도 볼 사람이 없다 |
| 소요 예상 | 응답 자체를 기대하기 어려움 |

> **이 항목이 이번 조사에서 가장 중요한 발견이다.** "XBRL 데이터 이용자 커뮤니티"라는 것이
> 공개 웹에 **광장의 형태로는 존재하지 않는다.** 어제 조사(§4 "이용자 쪽 1차 증거 못 찾음")와
> 같은 그림이 조달 쪽에서 반복된 것이다.

### 1-2. Reddit (r/quant · r/algotrading · r/SecurityAnalysis) — ⚠️ **규칙 확인 못 함 → 사용 보류**

| 항목 | 내용 |
|---|---|
| URL | reddit.com/r/quant · /r/algotrading · /r/SecurityAnalysis |
| 활성 여부 | 2차 소스는 2026년에도 활성이라고 서술 (<https://quantmatter.com/top-quant-forums/>) — **1차 확인 못 함** |
| **요청글 허용** | ⚠️ **확인 못 함.** 이 조사 환경에서 reddit.com·old.reddit.com **모두 fetch 차단**되어 각 서브레딧의 rules를 1차로 읽지 못했다. 검색으로도 r/quant 규칙 원문을 얻지 못했다 |
| 판정 | **규칙을 확인하기 전에는 사용 후보로 올리지 않는다.** 다수 금융 서브레딧이 설문·모집글을 금지한다는 것은 널리 알려진 통념이지만, **통념을 사실로 승격하지 않는다.** daria가 각 서브레딧 사이드바의 rules를 직접 읽고 판단해야 한다 |
| 만약 허용된다면 | 접촉 방법: 텍스트 게시 후 DM 전환. 예상 응답률: 게시글당 반응은 있으나 **적격(본인 제작 + 최근 3개월 + 화면 공유 동의)까지 남는 비율은 매우 낮음**. 소요: 3~10일 |

⚠️ 추가 위험: 익명 계정 응답자는 §6-2 적격 확인과 §3-0 화면 공유를 동시에 만족시키기
어렵다. Reddit은 **허용되더라도 이번 계측기와 궁합이 나쁜 채널**이다.

### 1-3. Quantitative Finance Stack Exchange — ❌ **부적합(구조상 금지)**

- URL: <https://quant.stackexchange.com/>
- **fetch 차단**으로 on-topic 페이지 1차 확인 못 함. 다만 Stack Exchange 네트워크는
  **질문–답변 사이트이지 게시판이 아니며**, 설문·모집·의견수렴 글은 네트워크 전반에서
  off-topic으로 닫히는 구조다. **금지로 판정하고 후보에서 뺀다.**

### 1-4. OpenBB 커뮤니티 (Discord) — 🟡 **활성이나 규칙 확인 못 함**

| 항목 | 내용 |
|---|---|
| URL | <https://openbb.co/solutions/community> · 저장소 <https://github.com/OpenBB-finance/OpenBB> |
| 성격 | 파이썬 금융 데이터 플랫폼. 팀이 **Discord에서 가장 활발**하다고 자사 페이지가 서술 |
| 활성 여부 | 🟡 활성으로 보임 — **단, 자사 마케팅 페이지 서술이며 최근 게시 시점 1차 확인 못 함** |
| 요청글 허용 | **확인 못 함.** 가입해야 규칙 채널을 볼 수 있고, 이번 조사는 가입하지 않았다 |
| 적격 적합도 | ⚠️ 낮음. OpenBB 이용자의 관심은 **시세·터미널**이지 반드시 XBRL 재무 패널이 아니다 |
| 소요 예상 | 가입 → 규칙 확인 → 자기소개 → 요청까지 최소 며칠. 신규 계정의 모집글은 스팸으로 처리될 위험 |

### 1-5. QuantConnect 포럼 / Numerai — ❌ **적격 요건과 불일치**

- Quantopian(2020 종료)의 후속으로 자주 지목되는 곳 (<https://www.quantconnect.com/forum/>).
- **부적합 이유**: 이들의 작업은 **가격·시계열 기반 알고리즘 트레이딩**이다. §6-2가 요구하는
  "**XBRL/재무 벌크 데이터로 패널·표를 직접 만든다**"와 모집단이 다르다. 활성이더라도
  적격자 밀도가 매우 낮아 **비용 대비 회수가 나쁘다.**

---

## 2. 오픈소스 저장소

수치는 조사 시점(2026-08-03) GitHub API 응답.

| 저장소 | URL | 최근 push | 이슈(open) | 스타 | 공개 연락처 | 판정 |
|---|---|---|---|---|---|---|
| **edgartools** | <https://github.com/dgunning/edgartools> | **2026-08-03 (당일)** | 23 | 2,543 | ❌ README에 개인 이메일·Discord **없음**. 창구는 **GitHub Discussions·Issues**. README가 컨설팅 제공을 명시 | 🟢 **가장 활발.** 이슈 #935~#939가 **2026-07-31 생성**(6.0 로드맵) — 살아 있는 프로젝트 |
| **sec-edgar-downloader** | <https://github.com/jadchaar/sec-edgar-downloader> | 2026-06-22 | 31 | 712 | ❌ README에 연락처 없음. 창구는 Issues | 🟡 활성이나 완만 |
| **sec-edgar-toolkit** | <https://github.com/stefanoamorelli/sec-edgar-toolkit> | 2026-03-31 | 1 | 37 | ❌ 확인 못 함 | 🟠 소규모·저활동 |
| sec_edgar_download | <https://github.com/robren/sec_edgar_download> | 확인 못 함 | 확인 못 함 | 확인 못 함 | 확인 못 함 | ⚪ 미조사(소규모) |
| altova/sec-xbrl | <https://github.com/altova/sec-xbrl> | 확인 못 함 | 확인 못 함 | 확인 못 함 | 벤더 데모 저장소 | ❌ 벤더 자료, 이용자 아님 |
| DQC 규칙 저장소 | <https://github.com/DataQualityCommittee/dqc_us_rules> | 확인 못 함 | 확인 못 함 | 확인 못 함 | 조직 저장소 | ⚠️ 여기 사람들은 **작성자 측 검증자**다. 어제 조사 §4 기준 **이용자가 아님** |

### 2-1. 이 경로의 구조적 한계 — 두 가지

1. **메인테이너 ≠ 표적 사용자.** 도구를 만드는 사람과 §6-2의 "**본인이 직접 패널·표를
   만드는 사람**"은 겹칠 수 있으나 같지 않다. 접촉 전 적격 확인이 반드시 선행돼야 하고,
   그 확인 자체가 왕복 1회를 더 먹는다.
2. **채널이 공개 이슈트래커다.** 대부분 저장소의 CONTRIBUTING은 "버그·기능요청"을 위한
   것이고, **"인터뷰 응해 주실 분" 글이 허용되는지는 어느 저장소에서도 확인하지 못했다.**
   Issues에 그런 글을 올리는 것은 노이즈로 닫힐 위험이 있다. **edgartools의 GitHub
   Discussions는 상대적으로 덜 위험하나, 역시 명시적 허용 근거는 확인 못 함.**

> 🟢 **현실적으로 이 경로에서 만날 확률이 가장 높은 대상은 메인테이너가 아니라
> "이슈를 올린 이용자"다** — 즉 실제로 데이터를 쓰다가 막혀서 글을 쓴 사람. 다만 그들의
> 연락처는 공개돼 있지 않고, GitHub 프로필을 뒤져 개인을 특정하는 것은 **이번 조사의
> 프라이버시 규율이 금지하는 프로파일링**이다. 접촉하려면 **이슈 스레드 위에서 공개적으로**
> 해야 하며, 그 허용 여부가 위 2번의 미확인 항목이다.

---

## 3. 학계

§6 본문이 "학계 회계·재무 실증 연구자 콜드 메일"을 명시했고, 논문 교신저자의 **공개된**
학술 연락처는 사용 가능하다.

### 3-1. 이 집단이 적격 요건과 가장 잘 맞는 이유

XBRL 실증 연구자는 **SEC 벌크 데이터를 직접 내려받아 본인 손으로 패널을 만드는 것이
직업**이다. §6-2의 "본인이 직접 / 최근 3개월 내"를 만족할 사전 확률이 이 조사에서
확인한 어느 집단보다 높다. **화면 공유(코드·데이터 파일)** 요구도 상대적으로 무리가 없다.

### 3-2. 자기 프로젝트 사이트에 업무용 이메일을 **스스로 공개**한 사례 — 1건

| 기관·프로젝트 | 무엇인가 | 공개 연락처 | 출처 |
|---|---|---|---|
| **XBRL Research** (Northeastern Univ. D'Amore-McKim / Bentley Univ.) | XBRL 재무 데이터 가공본, 회계보고복잡성(ARC) 지표, 주석 텍스트 데이터를 **직접 만들어 공개 배포**하는 학술 저장소. 즉 운영자 본인들이 XBRL 벌크로 패널을 만든다 | 사이트가 자체 공개한 업무용 주소 2건 (Udi Hoitash / Rani Hoitash) | <https://www.xbrlresearch.com/> — **사이트 본문에 직접 게시** |

> 이 항목은 개인 프로파일링이 아니다. **본인들이 자기 프로젝트 사이트에 연구 문의용으로
> 게시한 주소**이며, 출처를 함께 적었다. 실제 주소는 위 URL에서 daria가 직접 확인한다
> (이 문서에 전재하지 않는다).

### 3-3. 관련 논문 (2020년 이후) — 저자·소속

**⚠️ 아래 어느 항목도 교신저자 이메일을 1차로 확인하지 못했다.** AAA(publications.aaahq.org)와
ScienceDirect는 이 조사 환경에서 **403**으로 본문 접근이 막혔다. 저자·소속은 **검색 결과
스니펫 경유**이며 **원문 대조 못 함**. 이메일은 daria가 각 저자의 대학 교수 페이지(공개
학술 연락처)에서 직접 확인해야 한다.

| # | 논문 | 지면·연도 | 저자 (스니펫 경유) | 상태 |
|---|---|---|---|---|
| 1 | Does XBRL Tagging Indicate Disclosure Quality? Standard/Extension Tags and Stock Return Synchronicity | *J. of Information Systems* 37(3):81, 2023 | Jee-Hae Lim (Hawaii–Manoa), Vernon J. Richardson (Arkansas), Rod Smith (CSU Long Beach) | 원문 403 |
| 2 | Measuring Financial Statement Disaggregation Using XBRL | *JIS* 38(1):119, 2024 | Joseph A. Johnston, Kenneth J. Reichelt, Pradeep Sapkota | 원문 403. 소속 확인 못 함 |
| 3 | iXBRL Adoption and the Pricing of Audit Services | *JIS* 38(3):23, 2024 | Xu (Joyce) Cheng, Adi Masli, Stephanie Walton, Mengmeng Wang, Yiyang Zhang | 원문 403. 소속 확인 못 함 |
| 4 | Excessive custom XBRL tag usage in 10-K filings and SEC oversight | *Int'l J. of Accounting Information Systems*, 2025 | 확인 못 함 | <https://www.sciencedirect.com/science/article/abs/pii/S1467089525000181> — 초록 페이지, 저자 확인 못 함 |
| 5 | The Quality of XBRL Structured Financial Statements (학위논문) | CUNY, 연도 확인 못 함 | 확인 못 함 | <https://academicworks.cuny.edu/cgi/viewcontent.cgi?article=1519&context=hc_sas_etds> |

### 3-4. 학계 경로의 리드타임 — 냉정하게

- 콜드메일 회신은 **보통 3~10일**, 회신하지 않는 경우가 다수다.
- **8월 초는 미국 학계가 학회·휴가로 자리를 비우는 시기**다. 부재 자동응답이 흔하다.
- 회신이 와도 그다음이 **일정 조율 1왕복 + 화면 공유 동의**다.
- 논문 1편 = 저자 3~5명이지만, **§6-2 적격은 "최근 3개월 내 본인이 표를 만들었을 것"**이다.
  선임 교수는 그 작업을 대학원생·RA에게 맡기는 경우가 많아 **저자라고 적격인 것이 아니다.**

---

## 4. 경로별 종합 — 예상 응답률·소요

각 수치는 **측정치가 아니라 내 판단**이다. 근거는 채널의 활성도와 요구 조건의 무게이며,
사후에 결과를 보고 조정하지 않기 위해 지금 적는다.

| 경로 | 활성 | 요청글 허용 | 적격자 밀도 | 예상 응답 | 첫 인터뷰까지 소요 | 8/10 안에 가능? |
|---|---|---|---|---|---|---|
| **오픈소스 저장소 Discussions** (edgartools) | 🟢 당일 | ⚠️ 확인 못 함 | 🟡 중 | 낮음 | 4~10일 | ⚠️ 아슬 |
| **학계 콜드메일** (자기 공개 연락처) | 🟢 상시 | 🟢 허용(공개 학술 연락처) | 🟢 **높음** | 낮음(8월 부재 다수) | 5~14일 | ❌ |
| **저장소 이슈 스레드 위 공개 요청** | 🟢 | ⚠️ 확인 못 함 | 🟢 높음 | 매우 낮음 | 5~14일 | ❌ |
| **OpenBB Discord** | 🟡 추정 | ⚠️ 확인 못 함 | 🟠 낮음 | 낮음 | 3~10일 | ❌ |
| **Reddit** | 🟡 추정 | ⚠️ **확인 못 함(차단)** | 🟠 낮음 | 중간(글엔 반응) | 3~10일, 적격까지는 더 | ❌ |
| XBRL US 포럼 | ❌ 1년 정지 | ⚠️ 미확인 | 🟢 높았을 것 | **거의 0** | — | ❌ |
| Quant SE | 🟢 | ❌ **금지 구조** | — | — | — | ❌ |
| QuantConnect·Numerai | 🟢 | 🟡 | ❌ 모집단 불일치 | — | — | ❌ |

### 4-1. 병목은 응답률이 아니라 **적격 + 화면 공유**다

응답 1건을 받아도 그 사람이 인터뷰 1건이 되려면 **네 관문**을 모두 통과해야 한다:

1. §6-2 **본인이 직접** 패널 제작 — 도구 이용자·소비자는 탈락
2. §6-2 **최근 3개월 내** 제작 — 옛날 작업만 있으면 탈락
3. §6-1 **daria와 무관 + 이 프로젝트를 들어본 적 없음**
4. §2-0 **화면 공유 동의** — 거절해도 인터뷰는 유효하나 **D1·D2가 자동 미인정**이 되어
   §1-1 계속 조건이 **구조적으로 불가능**해진다

⚠️ **4번이 결정적이다.** 낯선 사람에게 **자기 업무 화면(고객 데이터가 있을 수 있는 재무
패널)을 공유해 달라**는 요구는, 콜드 접촉으로 만난 상대에게는 매우 무거운 요구다.
게다가 §6이 "**프로젝트·도구를 설명하지 않는다**"고 못박았으므로, **왜 이걸 보여줘야
하는지 설명할 수단조차 없는 상태로** 화면 공유를 부탁해야 한다. 이 조합은
**콜드 소싱에 특히 불리하게 설계돼 있다.**

---

## 5. 판정 — 8/10까지 칸 A 2명은 **비현실적이다**

### 근거 (추정이 아니라 이 조사에서 확인한 것 위에)

1. **남은 시간이 7일이다** (오늘 8/3 → 마감 8/10 24시). "확보 = 인터뷰 일정이 확정된 상태"
   이므로 접촉·회신·적격확인·일정조율을 **모두** 7일 안에 끝내야 한다.
2. **가장 표적에 가까운 공개 광장이 죽어 있다.** XBRL US 포럼 최신 실질 글 1년 전.
   즉 "표적 사용자가 모여 있는 곳"을 이 조사는 **찾지 못했다.**
3. **살아 있는 채널들은 모두 "요청글 허용 여부 확인 못 함"이다.** 확인하려면 가입·열람이
   필요하고, 규칙 위반 시 채널이 통째로 닫힌다. 7일 안에 시행착오를 할 여유가 없다.
4. **가장 적격한 집단(학계)의 리드타임이 마감보다 길다.** 8월 부재 시즌이 겹친다.
5. **화면 공유 요구가 콜드 접촉과 상극이다** (§4-1).

### 그래서 이것은 실패가 아니다 — 사전등록이 미리 정의한 관측이다

사전등록 **§6-3**이 이미 적어 두었다. 8/10까지 칸 A 2명을 확보하지 못하면 **S1으로 중단**하고,
보고서에 쓸 문장은

> **"수요를 확인하지 못했다"가 아니라 "표적 사용자 2명에게 도달하는 경로를 우리가 갖고
> 있지 않다"**

이다. 이 조사는 그 문장에 **구체적 내용을 채워 준다**: 도달 경로가 없는 이유는 daria의
인맥이 좁아서가 아니라, **XBRL 데이터 이용자가 공개 웹에 광장의 형태로 모여 있지 않기
때문**이다(XBRL US 포럼 1년 정지가 그 증거다). 이는 어제 조사 §4의 "이용자 쪽 pain 1차
증거를 찾지 못했다"와 **같은 사실의 다른 면**일 가능성이 높다 — 모여 있지 않은 집단은
목소리도 남기지 않는다.

⚠️ **단, 이 추론을 결론으로 승격하지 않는다.** "공개 웹에 광장이 없다"는 "그런 사용자가
없다"가 아니다. 그들은 회사 안에 흩어져 있을 수 있다. 이 조사가 말할 수 있는 것은
**도달 가능성**에 대한 것뿐이다.

### 그럼에도 시도한다면 — 우선순위 (daria 판단 몫)

1. **학계 자기공개 연락처** (§3-2) — 적격 밀도 최고, 규칙상 명확히 허용
2. **edgartools GitHub Discussions** — 유일하게 확실히 살아 있는 채널. **단, Discussions
   규칙을 먼저 읽을 것**
3. **논문 교신저자 콜드메일** (§3-3) — 이메일을 각 대학 공개 페이지에서 확인한 뒤
4. **OpenBB Discord** — 가입 후 규칙 확인이 선행
5. **Reddit** — **각 서브레딧 rules를 직접 읽고 허용을 확인한 뒤에만**

**사용 금지·부적합**: Quantitative Finance Stack Exchange(구조상 모집글 금지),
QuantConnect·Numerai(모집단 불일치), XBRL US 포럼(비활성), DQC 저장소(작성자 측이지
이용자 아님), Altova 저장소(벤더 자료).

> ⚠️ 위 1~5는 **접촉 권고가 아니다.** 사전등록 §"이 문서의 지위"에 따라 **daria 승인 전
> 인터뷰 착수는 금지**이며, 이 문서는 승인 판단에 쓸 재료일 뿐이다.

---

## 부록 — 확인 못 한 것 목록 (승격 금지)

| 항목 | 상태 |
|---|---|
| r/quant·r/algotrading·r/SecurityAnalysis 서브레딧 규칙 | **reddit.com·old.reddit.com 모두 fetch 차단.** 1차 확인 실패 |
| Quantitative Finance SE on-topic 원문 | **fetch 차단.** 금지 판정은 SE 네트워크 구조에 근거한 것이며 원문 대조 못 함 |
| XBRL US 포럼 규칙 본문 | 규칙 토픽의 **존재만 확인**, 본문 미열람 |
| 각 GitHub 저장소의 "인터뷰 모집글" 허용 여부 | **어느 저장소에서도 확인 못 함** |
| OpenBB Discord 활성도·규칙 | **자사 페이지 서술 경유.** 가입하지 않아 1차 확인 못 함 |
| §3-3 논문 5편의 저자·소속 | **검색 스니펫 경유.** AAA·ScienceDirect **403으로 원문 대조 실패** |
| §3-3 논문의 교신저자 이메일 | **한 건도 확인하지 못함** |
| edgartools 등의 last commit 정확 시각 외 지표 | GitHub API 응답(2026-08-03 조회) 기준. 이후 변동 가능 |
| 예상 응답률·소요일 | **측정치 아님. 내 판단이다** |

## 출처

- XBRL US XBRL API 커뮤니티 <https://xbrl.us/xbrl-api-community>
- XBRL US 포럼 <https://xbrl.us/forums/forum/the-xbrl-api/>
- edgartools <https://github.com/dgunning/edgartools>
- sec-edgar-downloader <https://github.com/jadchaar/sec-edgar-downloader>
- sec-edgar-toolkit <https://github.com/stefanoamorelli/sec-edgar-toolkit>
- sec_edgar_download <https://github.com/robren/sec_edgar_download>
- altova/sec-xbrl <https://github.com/altova/sec-xbrl>
- DQC 규칙 저장소 <https://github.com/DataQualityCommittee/dqc_us_rules>
- OpenBB 커뮤니티 <https://openbb.co/solutions/community> · <https://github.com/OpenBB-finance/OpenBB>
- QuantConnect 포럼 <https://www.quantconnect.com/forum/>
- 퀀트 커뮤니티 목록(2차 소스) <https://quantmatter.com/top-quant-forums/>
- XBRL Research (Hoitash & Hoitash) <https://www.xbrlresearch.com/>
- JIS 37(3):81 (403) <https://publications.aaahq.org/jis/article/37/3/81/11543/Does-XBRL-Tagging-Indicate-Disclosure-Quality-The>
- JIS 38(1):119 (403) <https://publications.aaahq.org/jis/article-abstract/38/1/119/11876/Measuring-Financial-Statement-Disaggregation-Using>
- JIS 38(3):23 <https://publications.aaahq.org/jis/article/38/3/23/12794/iXBRL-Adoption-and-the-Pricing-of-Audit-Services>
- IJAIS 2025 커스텀 태그 과다사용 <https://www.sciencedirect.com/science/article/abs/pii/S1467089525000181>
- CUNY XBRL 품질 학위논문 <https://academicworks.cuny.edu/cgi/viewcontent.cgi?article=1519&context=hc_sas_etds>

---

**Mary (분석), 2026-08-03. 접촉·게시·가입은 하지 않았다. 착수 승인은 daria의 몫.**
