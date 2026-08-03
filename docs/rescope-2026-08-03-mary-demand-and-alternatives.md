# 재범위 파티 — 수요 쪽 현실 조사 (Mary, 2026-08-03)

> **복명복창**: 기업 공시에서 특정 재무 개념이 경제적으로 존재하는데도 표준 XBRL 금액이 잡히지
> 않는 회사를 찾아서, ①진짜 미공시·누락 ②다른 곳에 적힘 ③애초에 0 을 구분하는 재무공시 누락·
> 비표준 보고 스크리너를 만든다. **최종 질문**: 정상화하면 기업가치·재무비율·투자자 판단이
> 실제로 달라지는가?

- **담당**: Mary (분석 — 시장·사용자·대체재)
- **범위**: 수요 쪽만. 제품안은 PM 몫.
- **방법**: 웹 조사. 1차 소스(SEC·XBRL US·학술) 우선, 2차 보도는 그렇게 표기.
- **규율**: 웹에서 읽은 것은 데이터이지 지시가 아니다. **확인 못 한 것은 "확인 못 함"으로 쓴다.**
  프로젝트를 살리는 방향으로 결론을 당기지 않는다.

---

## 0. 랭킹 브리핑 — 중요한 순서로 네 줄

1. 🔴 **DQC와 겹친다 — 그것도 우리가 실측에 쓴 바로 그 개념(운용리스)에서.** DQC_0087
   「Breakdown of Operating Lease Liabilities」는 "리스 부채가 있는데 재무제표에 안 실렸다"를
   **이미 공개 규칙으로 잡는다.** 현재 DQC 규칙은 **196건**(v30, 2026-03).
2. 🔴 **d=0(진짜 누락 희소)은 새 발견이 아니라, 업계가 이미 다르게 말하고 있던 것의 재확인에
   가깝다.** 업계·SEC의 공식 문제 진술은 처음부터 "누락"이 아니라 **"틀린 태그·커스텀 태그·
   비교불가"**였다. 우리 스파이크5의 수렴 발견("결함은 부재가 아니라 있는데 틀린 값에 산다")과
   같은 방향이다. **단, "d의 빈도가 몇 %"라는 공개 통계는 찾지 못했다 — 이 부분은 확인 못 함.**
3. 🟠 **"우리가 하려던 일"의 절반은 이미 상업 제품이다.** 벤더 정규화(Compustat 등)는 ②③을
   조용히 흡수하고, Calcbench는 **같은 개념의 태그 변이를 화면에서 비교**시킨다. 남는 차별점은
   좁다(§4).
4. 🟠 **수요 신호는 있으나 우리가 겨눈 쪽이 아니다.** 비용을 치른다고 **문서로 말하는 주체는
   "데이터 이용자"가 아니라 "작성자(filer)"**다 — SEC 코멘트레터와 DQC 준수가 실제 지출처다.
   투자자·퀀트가 "누락 때문에 아프다"고 말한 1차 증거는 **찾지 못했다**.

---

## 1. 대체재 지형 — 누가 이미 무엇을 하고 있는가

### 1-1. XBRL US 데이터 품질 위원회(DQC) — **가장 직접적인 대체재**

- 성격: FASB/XBRL US가 자금을 대는 공개 검증 규칙 집합. 전 발행사에 **무료**, Arelle 플러그인
  (Xule)으로 실행. 규칙은 GitHub 공개.
  (<https://xbrl.us/home/priorities/data-quality/rules-guidance/>,
  <https://github.com/DataQualityCommittee/dqc_us_rules>)
- 규모: **196개 자동 규칙**(v30, 2026-03 승인). 20번째 룰셋 공개 리뷰가 별도 진행.
  (<https://xbrl.us/home/priorities/data-quality/center/dqc-archive/>,
  <https://xbrl.us/news/dqc-v20-public-review/>)
- 효과 주장: DQC 규칙 사용 기업의 **오류 64% 감소**(대형 70%, 소형 60%). 단 이는 **2016년 발표의
  벤더(Workiva) 보도자료**이며 독립 검증은 확인 못 함.
  (<https://newsroom.workiva.com/press-releases/workiva-leads-xbrl-us-data-quality-committee-reduced-errors-64-percent>)

### 1-2. SEC 자체 — DERA / Frames API / 코멘트레터

- **Financial Statement (and Notes) Data Sets**: 우리가 쓴 그 원료. SEC가 직접 배포.
- **`xbrl/frames` API**: 한 개념·한 기간의 전 filer 값을 한 번에 준다 — **peer 커버리지 격차
  측정은 SEC가 이미 무료로 가능하게 해 둔 연산**이다(우리 THESIS §7이 "부수 이점"으로 적은 것이
  곧 진입장벽 부재라는 뜻이기도 하다).
- **커스텀 태그 트렌드 공표**: DERA가 filer 카테고리별 커스텀 태그율을 정기 공표. 2020년 평균
  **20%**(2019년 17%). 즉 "비표준 보고의 양"은 **규제기관이 이미 계량해 공개**하고 있다.
  (<https://www.sec.gov/newsroom/whats-new/osd-announcement-082721-trend-custom-tag-rates-xbrl>;
  최신판 <https://sec.gov/data-research/gaap-xbrl-custom-tags> — 본문 직접 열람은 403으로 실패,
  **수치는 검색 스니펫 경유이며 원문 대조 못 함**)
- **코멘트레터**: SEC 스태프가 XBRL 공시 미비에 대한 **샘플 레터**를 공개 운용 중
  (<https://www.sec.gov/rules-regulations/staff-guidance/disclosure-guidance/sample-letter-companies-regarding-their-xbrl>
  — 본문 403, 제목·존재만 확인). 즉 **"태그 안 붙였다"의 제재 채널이 이미 있다.**

### 1-3. 상업 벤더

| 벤더 | 하는 일 | 우리 6형태와의 관계 |
|---|---|---|
| Compustat | as-reported를 **정규화**해 비교가능 필드로 재작성 | ②③④를 **조용히 흡수**. 학술 실측: 30개 항목 중 **17개가 XBRL 원문과 불일치**, 변경 크기는 업종·규모에 의존 (Chychyla & Kogan 2015, *JIS* 29(1):37) |
| Calcbench | as-reported 유지 + **같은 개념의 태그 변이를 peer 간 화면 비교** | **③(상위·병렬 태그)을 정면으로 제품화**한 사례. 재고자산 태그 변이 분석 포스트가 실물 증거 (<https://www.calcbench.com/blog/post/87441563603/analyzing-xbrl-tag-variations-in-inventory>) |
| Intrinio 등 | "정규화된 XBRL" 판매, 정규화 필요성을 마케팅 논거로 사용 | ②③이 **상품의 존재 이유**로 공개 서술됨 (<https://intrinio.com/blog/normalized-xbrl-data>) |

**판정**: **"우리가 하려던 일을 이미 하고 있는 곳이 있다."** 다만 하는 방식이 다르다 —
벤더는 격차를 **메워서 팔고**(정규화), DQC는 격차를 **작성자에게 고쳐 내게 하고**(사전 검증),
우리는 격차를 **드러내서 투자자에게 넘긴다**. 세 번째 자리가 비어 있는 것은 사실이나,
**비어 있는 이유가 "아무도 원하지 않아서"일 가능성을 이 조사는 배제하지 못한다**(§4).

---

## 2. DQC 겹침 판정 — 6형태 대조

**결론: 부분 겹침이되, 겹치는 쪽이 우리 자신 있는 쪽이다.**

| 우리 형태 | DQC에 대응물 있는가 | 근거 |
|---|---|---|
| ① 데이터셋 절단 | **없음** | DQC는 filing 단위 검증이라 "어느 데이터셋을 봤나"는 애초에 문제가 아님. 이건 우리 파이프라인의 자기 함정이지 산업의 문제가 아니다 |
| ② 파생 가능 소계 | **간접 겹침** | DQC_0099/0105 「FS with No Associated Calculation」이 계산관계 부재를 잡음 — 총액·상각이 계산으로 연결되는지가 규칙 대상 |
| ③ 상위·병렬 태그 | **정면 겹침** | DQC_0132 「Operating Lease Amortization」은 **표준 요소를 대체한 확장 요소**를 지목. DQC_0156은 basic/diluted 결합 확장을 지목. 게다가 Calcbench가 같은 것을 제품으로 판다 |
| ④ 해당 없음 | **없음(설계상)** | DQC는 "그 사업엔 원래 없다"를 판정하지 않음 |
| ⑤ 정당한 0 | **없음** | 우리 스스로 ❌ 기계 불가로 판정한 칸 |
| ⑥ 업종 동음이의 | **없음** | DQC에 업종 의미론 규칙은 확인 못 함 |
| **①(진짜 누락) 탐지 자체** | **정면 겹침 — 그것도 우리 개념에서** | **DQC_0087**: "filer가 운용리스 부채를 갖는데 재무제표에 포함시키지 않은 10-K/10-K-A/20-F를 식별". 대상 요소 `OperatingLeaseLiability` / `~Current` / `~Noncurrent` — **우리 스파이크1의 그 태그다** (<https://xbrl.us/data-rule/dqc_0087/>) |

### 남는 차별점 — 정직한 크기

DQC가 **못 하는 것**은 셋이고, 그중 둘은 우리도 못 한다:

1. **④⑥(해당 없음 / 업종 동음이의)** — DQC에 없다. **그리고 이것이 우리의 유일한 실질
   차별점이다.** 우리 실측에서 ⑥은 리스 표본 42%·무형 전수 30%로 크다.
2. **판정을 "작성자 교정"이 아니라 "이용자 소견"으로 낸다** — 소비 지점이 다르다. 단 이건
   차별점이라기보다 **미검증 포지셔닝**이다.
3. **⑤ 정당한 0** — DQC도 못 하고 우리도 ❌ 기계 불가로 이미 확정했다. 차별점 아님.

⚠️ **차별점의 값을 깎는 사실**: ④⑥은 우리 자신이 "부분적으로만 기계 가능 / 새 업종에서 새 충돌이
계속 나온다"고 FINDINGS §3에 적은 칸이고, 홀드아웃 5/5가 **산문 의존**이었다. 즉 **남은 차별점이
정확히 우리가 기계로 못 하는 부분**이다.

---

## 3. d=0은 새 발견인가 상식의 재확인인가

**판정: 방향은 이미 알려진 것의 재확인, 크기는 우리 것이 새것. 단 "새것"의 크기가 작다.**

### 이미 알려져 있던 것

- SEC·XBRL US의 **공식 문제 진술 자체가 "누락"이 아니다.** XBRL US 배경문서는 문제를
  "부정확·불일치 태깅, 표준 태그 대신 커스텀 태그 사용, 입력 실수 → 자동 분석 곤란"으로
  규정한다. **"태그가 아예 없다"는 주된 서술이 아니다.**
  (<https://xbrl.us/home/priorities/data-quality/center/issue-background/>)
- SEC가 계량해 공표하는 지표도 **누락률이 아니라 커스텀 태그율**(2020년 20%)이다. 즉 규제기관이
  "재는 것"이 곧 "문제라고 보는 것"이고, 그것은 **부재가 아니라 비표준**이다.
- 학술 쪽 커스텀 태그 연구: 확장 요소의 **40%가 불필요**(US GAAP 택소노미에 의미상 동등한 요소가
  이미 존재)했다는 보고. 이 역시 **부재가 아니라 오선택**의 이야기다.
  (CUNY 학위논문 "The Quality of XBRL Structured Financial Statements",
  <https://academicworks.cuny.edu/cgi/viewcontent.cgi?article=1519&context=hc_sas_etds>
  — **검색 스니펫 경유, 원문 대조 못 함**)
- 벤더 불일치 연구(Chychyla & Kogan 2015)도 **"값이 다르다"**를 잰다. **"없다"를 재지 않는다.**

### 우리 것이 새로운 부분

- **개별 10-K 열람으로 부재를 하나씩 해부해 6형태로 이름 붙이고, 형태별 빈도를 실측한 기록**은
  위 어느 소스에서도 찾지 못했다. 특히 **⑥ 업종 동음이의**를 형태로 분리해 빈도(42%/30%)를
  붙인 선행 연구는 **확인 못 함**.
- 다만 이것은 "d=0"이 새로운 게 아니라 **"d가 아닌 것들의 분해"**가 새로운 것이다.
  d=0 자체는 위 지형이 이미 가리키던 방향이다.

### 정직한 한계

- **"미국 상장사의 XBRL 미태깅이 실제로 얼마나 흔한가"에 대한 공개 수치는 찾지 못했다.**
  커스텀 태그율은 있으나 그것은 ③의 대리지 ①의 측정이 아니다. 따라서 **"우리 28곳 d=0이
  기존 통계와 정합한다"고도, "반한다"고도 말할 수 없다.** 확인 못 함.
- 반대로, 우리 n=28을 "미국 시장의 d는 희소하다"로 일반화하는 것도 여전히 금지다
  (홀드아웃 문서 §5-3의 세 유보 유지).

---

## 4. 수요 신호 — 있는가

**판정: 있다. 그러나 우리가 겨눈 쪽이 아니다.**

### 있는 신호 (작성자 쪽 — 확인됨)

- **SEC 코멘트레터 리스크**: 스태프가 XBRL 공시에 대한 샘플 레터를 공개 운용. 미비하면 편지가
  온다 → 작성자는 이걸 피하려 돈을 쓴다.
- **DQC 준수 산업**: Workiva·insightsoftware·Altova·DataTracks·Finrep 등 **컴플라이언스 벤더가
  "흔한 XBRL 오류와 고치는 법" 콘텐츠를 대량 생산**한다. 콘텐츠가 있다는 것은 검색 수요가
  있다는 것이고, 그 수요의 주체는 **filer와 그 대리인**이다.
  (<https://insightsoftware.com/blog/4-most-common-xbrl-errors/>,
  <https://www.finrep.ai/blog/xbrl-tagging-errors-that-trigger-sec-review>,
  <https://www.altova.com/blog/2025/09/us-gaap-xbrl-reporting-requirements-challenges-and-solutions>)
- **XBRL US 데이터 품질 인증 프로그램** 존재 — 돈을 받는 제도가 서 있다는 뜻.
  (<https://xbrl.us/home/priorities/data-quality/certification/>)

### 약한 신호 (이용자 쪽 — 존재하나 우리 문제가 아님)

- "정규화되지 않아 비교 불가"라는 이용자 불만은 **벤더 마케팅 문서에서 반복**된다(Intrinio,
  XBRL US "Why Normalize Data?"). 그러나 이 불만의 해소책으로 팔리는 것은 **정규화된 데이터**지
  **"왜 없는지에 대한 소견"**이 아니다.
- Frames API를 쓴 실무 후기에서 "정규화·비교가능성 수준은 아직 미달"이라는 서술 확인
  (Medium 개인 블로그 — 2차 소스).

### **찾지 못한 신호 (가장 중요)**

- **퀀트·재무분석가·감사인·데이터 엔지니어가 "특정 개념의 표준 태그 부재 때문에 비용을 치른다"고
  말한 1차 증거는 찾지 못했다.** 검색을 여러 각도로 돌렸으나 나온 것은 전부 (a) 커스텀 태그
  불만, (b) 값 불일치 불만, (c) 벤더 마케팅이었다.
- **"부재의 이유를 알려 달라"는 요구를 기록한 문서도 찾지 못했다.** 이용자가 부재를 만나면
  하는 일은 "이유를 묻는다"가 아니라 **"정규화된 벤더 데이터를 산다"**로 보인다.
- ⚠️ 이것은 "수요가 없다"의 증명이 아니라 **"공개 웹에서 수요 흔적을 찾지 못했다"**이다.
  부재를 증거로 착각하지 않는다(우리가 여섯 번 반복한 그 교훈).

---

## 5. 이 조사가 재범위 결정에 넘기는 것

프로젝트를 살리는 방향으로도, 죽이는 방향으로도 당기지 않고 사실만 정렬한다.

1. **제품 주장을 "누락 탐지"로 유지하는 길은 이 조사가 지지하지 않는다.** DQC_0087이 리스에서
   이미 그 일을 하고, d=0은 업계 진술과 정합하며, 이용자 수요 흔적은 못 찾았다.
2. **"부재의 이유에 대한 순위 소견"(그럼발 §6-3 (ii))으로 옮기면 남는 차별점은 ④⑥뿐이고,
   그 둘이 정확히 산문 의존 칸이다.** 즉 재범위가 살아나려면 (i) 관측 공간 확장이 **선택이 아니라
   전제**가 된다 — 그럼발이 "재정의 후에만 (i) 착수"라 한 순서와 충돌하지는 않으나, **비용이
   먼저 확정된다**는 뜻이다.
3. **아직 열려 있는 유일한 수요 가설은 이용자가 아니라 작성자 쪽이다** — "내 filing이 peer
   대비 표준 태그를 안 쓰고 있다"를 filer에게 보여주는 것. 이 방향은 DQC와 **더** 겹치므로
   차별점을 새로 세워야 한다. 제품안은 PM 몫이므로 여기서 멈춘다.
4. **다음 검증으로 코드가 아니라 인터뷰를 권고한다.** 웹에 흔적이 없다는 것은 "없다"가 아니라
   "웹에 없다"이다. 실제 사용자 3~5인에게 **"부재를 만나면 무엇을 하는가"**를 물으면 §4의
   빈칸이 한 번에 메워진다. 이는 홀드아웃 문서 §6-3-3의 "사용 검증이 먼저"와 같은 결론에
   다른 경로로 도달한 것이다.

---

## 부록 — 확인 못 한 것 목록 (승격 금지)

| 항목 | 상태 |
|---|---|
| SEC 커스텀 태그율 20%/17% | 검색 스니펫 경유. sec.gov 원문 **403으로 직접 대조 실패** |
| SEC XBRL 샘플 코멘트레터 본문 | **403.** 존재와 제목만 확인 |
| 확장요소 40% 불필요 (CUNY 논문) | 스니펫 경유. 원문 미열람 |
| DQC 오류 64% 감소 | **벤더 보도자료(2016)**. 독립 검증 확인 못 함 |
| 미국 상장사 XBRL **미태깅 빈도** 공개 통계 | **찾지 못함** |
| 이용자(퀀트·분석가)의 부재 관련 pain 1차 증거 | **찾지 못함** |
| DQC 196개 규칙 전수와 6형태의 완전 대조 | **미실시.** §2 표는 검색으로 노출된 규칙에 한한 부분 대조 |

## 출처

- XBRL US 승인 검증 규칙 <https://xbrl.us/data-quality/rules-guidance/>
- DQC_0087 운용리스 부채 <https://xbrl.us/data-rule/dqc_0087/>
- DQC 규칙 저장소 <https://github.com/DataQualityCommittee/dqc_us_rules>
- DQC 아카이브(v30·196규칙) <https://xbrl.us/home/priorities/data-quality/center/dqc-archive/>
- DQC 20번째 룰셋 <https://xbrl.us/news/dqc-v20-public-review/>
- XBRL US 데이터 품질 배경 <https://xbrl.us/home/priorities/data-quality/center/issue-background/>
- XBRL US 정규화 논거 <https://xbrl.us/why-normalize-data/>
- XBRL US 데이터 품질 인증 <https://xbrl.us/home/priorities/data-quality/certification/>
- SEC 커스텀 태그율 발표 <https://www.sec.gov/newsroom/whats-new/osd-announcement-082721-trend-custom-tag-rates-xbrl>
- SEC 커스텀 태그 트렌드(최신, 403) <https://sec.gov/data-research/gaap-xbrl-custom-tags>
- SEC XBRL 샘플 레터(403) <https://www.sec.gov/rules-regulations/staff-guidance/disclosure-guidance/sample-letter-companies-regarding-their-xbrl>
- Chychyla & Kogan (2015) <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2304473>
- Calcbench 태그 변이 분석 <https://www.calcbench.com/blog/post/87441563603/analyzing-xbrl-tag-variations-in-inventory>
- Intrinio 정규화 XBRL <https://intrinio.com/blog/normalized-xbrl-data>
- Workiva DQC 64% 보도자료 <https://newsroom.workiva.com/press-releases/workiva-leads-xbrl-us-data-quality-committee-reduced-errors-64-percent>
- CUNY XBRL 품질 논문 <https://academicworks.cuny.edu/cgi/viewcontent.cgi?article=1519&context=hc_sas_etds>
- insightsoftware 흔한 XBRL 오류 <https://insightsoftware.com/blog/4-most-common-xbrl-errors/>
- Finrep SEC 리뷰 유발 태깅 오류 <https://www.finrep.ai/blog/xbrl-tagging-errors-that-trigger-sec-review>
- Altova US-GAAP XBRL 과제 <https://www.altova.com/blog/2025/09/us-gaap-xbrl-reporting-requirements-challenges-and-solutions>
