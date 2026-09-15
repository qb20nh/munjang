# Munjang 1.0.0

Korean writing and self-editing, with a portable Agent Skill and an auditable finite editing loop.

한국어 글쓰기, 보존 교열, 재구성을 위한 스킬/플러그인이다. 하나의 거대한 프롬프트만 붙이는 대신
작업 계약, 장르, 한국어 교열, 목소리, 근거, 진단/수정/검증을 분리했다.
원문을 더 많이 고치는 것이 아니라 필요한 수정만 검증 후 채택한다.

## 시작

### Codex 또는 Agent Skills 호스트

Python 3.10 이상에서 사용자 스킬로 설치:

```sh
python tools/install.py --host codex --scope user
```

`~/.agents/skills/korean-writing`에 복사한다. 실행 중인 호스트는 재시작하거나 스킬을 새로 검색한다.
Codex에서 `$korean-writing`을 명시적으로 호출한다. 예:

```text
$korean-writing
보존 교열로 draft.md를 다듬어줘. 주장 강도, 수치, 인용, 문장 순서를 유지해.
실행기로 검증하고 final.txt와 중요한 미해결 문제만 보여줘.
```

프로젝트 범위는 `--scope project --project /path/to/project`.
설치 전 확인은 `--dry-run`, 기존 설치 교체는 백업을 만드는 `--force`.
Claude 독립 스킬 설치는 `--host claude`; 경로는 `.claude/skills/korean-writing`이다.
일반 호스트의 임의 디렉터리는 `--host generic --destination /path/to/skills/korean-writing`.
선택적 리뷰어는 `--with-agents`; 호스트가 실제로 서브에이전트를 지원할 때만 사용한다.

### Claude Code 플러그인

```sh
claude --plugin-dir /absolute/path/to/munjang
```

`/munjang:korean-writing`으로 호출한다. 스킬과 읽기 전용 리뷰어 3개를 함께 제공한다.
위 standalone 설치와 플러그인을 동시에 활성화할 필요는 없다.

### Codex 플러그인 패키지

root `plugin.json` + `.agents/plugins/marketplace.json` + `.codex-plugin/plugin.json`을 제공한다.
로컬 카탈로그를 등록하는 명령은 다음과 같다.

```sh
codex plugin marketplace add /absolute/path/to/munjang
```

등록은 설치/활성화와 다르다. 호스트의 플러그인 화면에서 `munjang`을 설치하고 활성화한다.
CLI/앱 버전마다 UI가 다를 수 있다. 가장 단순한 경로는 앞의 standalone 스킬 설치다.
패키지 생성은 ChatGPT 공개 디렉터리 게시나 계정에 대한 설치 완료를 뜻하지 않는다.

## 사용 모드

| 모드 | 역할 |
| --- | --- |
| copyedit | 필요한 문장 내부 교정. 순서, 경계와 물리적 레이아웃을 보수적으로 보존 |
| restructure | 필수 의미/정보를 지키며 문단, 어순, 문장 경계를 재구성 |
| draft | 주제/자료에서 초안을 만들고 같은 유한 교열 루프 실행 |

설명문, 논증문, 업무문, 수필, 소설, 기술문, 짧은 게시물의 지침을 포함한다.
문체 카드는 사용자가 준 예문에서만 추출한다. 상투적 AI투는 문맥에서 진단하며 금지어 치환기로 처리하지 않는다.
문장 길이, 어휘 난도, perplexity/burstiness, AI 탐지 통과율을 품질 목표로 삼지 않는다.

## 파일 기반 실행

패키지 루트에서 고정 fixture를 이용한 오프라인 동작 확인:

```sh
python skills/korean-writing/scripts/workbench.py run --input skills/korean-writing/examples/input.md --brief skills/korean-writing/examples/copyedit.brief.json --output demo-run --backend demo
```

`demo`는 시뮬레이션이지 LLM이 아니다. 실제 작업은 현재 호스트의 request/submit 경로 또는 명시적으로 설정한 API로 실행한다.
Python 표준 라이브러리만 사용한다. 검사에는 GPU, 네트워크, API 키가 필요 없다.

```text
원본/계약 고정 -> [신규 작성 시 초안] -> 진단 -> 부분 수정
  -> 문자열/구조 검사 -> 별도 의미 검토 -> 채택 또는 기각
  -> 필요 시 반복, 기본 최대 3라운드 -> 마지막 통과본
```

지원 실행 경로:
- 현재 Codex/Claude 등 호스트: `prepare -> request -> submit`.
- Responses API: 사용자 지정 endpoint/model, `store:false`.
- Chat Completions 호환 서버: 로컬 또는 명시적으로 허용한 HTTPS endpoint.
- 사용자 어댑터: JSON stdin/stdout, `shell=False`.

[실행기 전체 안내](skills/korean-writing/references/runtime.md)에 명령어와 brief 옵션이 있다.

## 실제 보장 범위

해시와 검토 ID, 패치 원문 일치, 중복/누락, 보호 문자열, 인용/코드/링크/수식의 일부 자동 추출,
수치 토큰, 분량, 변경량, 단계 계약을 검사한다. 실패한 후보는 최종본으로 채택하지 않는다.
문장 경계와 자동 보호구간 인식은 휴리스틱이다. 완전한 한국어 구문 분석기나 사실 검증기가 아니다.
역할/조건/양태/인과 등 의미는 12차원 리뷰 기록을 요구하되 그 기록의 진실을 코드가 증명하지는 않는다.

출력: `final.txt`, `report.json`, `changes.diff`, 원문/계약/상태 및 단계별 감사 파일.
중단 후 재개, 순환 후보 방지, 자동 재시도 금지, 외부 전송 opt-in을 포함한다.
`chunks`는 호스트용 장문 분할 계획만 만든다. 자동 병합이나 무제한 원고 처리를 주장하지 않는다.

## 개발/검사

```sh
python tools/validate_package.py
python -m unittest discover -s skills/korean-writing/tests -v
```

테스트는 의미 품질 벤치마크가 아니다. 정확한 실행 환경과 결과는 [TEST-REPORT](docs/TEST-REPORT.md)에 있다.
[아키텍처](docs/ARCHITECTURE.md), [보안과 개인정보](SECURITY.md), [평가 설계](docs/EVALUATION.md),
[출처와 연구 한계](skills/korean-writing/references/sources.md)를 함께 참고한다.

## 라이선스

MIT. 책이나 외부 저장소의 원문을 재배포하지 않는다. 출처를 확인하지 못한 책에 내용을 귀속하지 않는다.
