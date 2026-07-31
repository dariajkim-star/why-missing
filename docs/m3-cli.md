# M3 — 대화형 CLI (2026-07-31)

> **기준**: 미학습 신규 회사 1곳에 대해 입력→출력 30초 내, 근거 한 줄 포함.
> **결과**: **실측 2.0~2.3초** (5곳 측정). 통과.

```bash
python -m adjudicator.cli RGR finite_lived_intangibles_net
python -m adjudicator.cli NKE operating_lease_liability
```

## 파티 결정 5건 (2026-07-31)

| # | 결정 | 근거 |
|---|---|---|
| 1 | 단건 경로 = **companyfacts + accession 필터**. 무필터 경로는 **코드에 존재 금지** | 벌크 zip은 수백 MB → 30초 불가(그럼발). 스파이크6의 companyfacts 금지 사유(정정 병합)는 각 fact의 `accn`으로 필터하면 소멸(Mary), 단 무필터 경로 금지가 조건(레아) |
| 2 | 대상 = **최신 10-K**, accession은 submissions API에서 확정 | 계보 계약 조항 1 |
| 3 | **차원 태그·본문 기재 비가시**를 후보 판정에 필수 병기 | companyfacts는 무차원 사실만 준다 → 골든의 iWallet·EVA Live를 못 본다(Boundary). 안 붙이면 "기계가 없다면 없다"로 읽힘(Sally) |
| 4 | peer 맥락은 **캐시 있을 때만**, 없으면 명시적 부재 표기 | 억지 셀 금지의 맥락판(Winston) |
| 5 | 입력은 **티커·CIK·회사명** 허용, 모호하면 되물음 | 애널리스트는 CIK를 모른다(John) |

## 실측 (2026-07-31)

| 회사 | 판정 | 시간 |
|---|---|---|
| **Sturm Ruger** (골든 b) | `CANDIDATE_OMISSION` + 사각 2건 + 영구 단서 | 2.0s |
| HCA | `REPORTED_ELSEWHERE` (M1이 등록한 umbrella 태그) | 2.2s |
| Trex | `PRESENT` (FY2025엔 Net을 태깅) | 2.3s |
| NIKE · Crocs (미학습) | `PRESENT` | ~2s |
| AAPL + 주식보상(흐름) | **거부**, exit 2, 네트워크 접근 0 | — |
| "TRUST" (363곳 매치) | **되물음**, exit 1 | — |

**Sturm Ruger가 이 도구의 정직성을 보여준다**: 골든에서 사람이 *주석 6 "Other Assets"*에서
찾아낸 회사인데, 도구는 확정이 아니라 **후보**로 내놓고 *"본문 기재는 이 문으로 못 본다"*는
바로 그 사각을 스스로 경고한다.

## 테스트 (53 passed, 변이 19/19 KILLED)

CLI 계층 변이 5종 전부 사망: 사각 경고 억제 · accession 누락 · peer 맥락 줄 삭제 ·
흐름 개념 문 우회 · **companyfacts 무필터 복귀**(구조적 금지가 테스트로 고정).

## 남은 한계

- **차원 태그·본문 기재 비가시** — 구조적. 출력이 매번 말한다.
- **peer 맥락 없음** — 캐시된 분기 없이는 단일 회사 관측만으로 판정. M1 스냅샷과의 연결은 미구현.
- 최신 10-K만 본다(과거 연도 지정 불가).
