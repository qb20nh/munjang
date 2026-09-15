# 빠른 시작

압축을 풀어 `munjang` 폴더에서 실행한다. Python 실행 명령이 `python3`인 환경에서는 `python` 대신 `python3`를 쓴다.

## 스킬 설치

```sh
python tools/install.py --host codex --scope user --dry-run
python tools/install.py --host codex --scope user
```

Codex를 다시 열고 `$korean-writing`을 입력한다. Python이 없는 호스트에서는 `skills/korean-writing` 폴더 전체를
호스트가 안내하는 스킬 디렉터리에 복사한다. `SKILL.md`만 복사하면 참고파일과 검사 기능이 빠진다.

## 가장 간단한 호출

```text
$korean-writing 원문 뜻과 말투를 지키면서 보존 교열해줘. 최종본만.
[원문]
```

```text
$korean-writing 이 자료로 일반 독자용 설명문을 새로 써줘.
약 1,500자, 담백한 해요체. 자료에 없는 사실은 만들지 말고 불확실하면 표시해.
[자료]
```

```text
$korean-writing 이 글을 논증문으로 재구성해줘.
핵심 주장과 근거는 보존하되 가장 강한 반론을 검토해.
새 사실이 필요하면 지어내지 말고 확인 항목으로 남겨.
[원문]
```

## 오프라인 실행기 확인

```sh
python skills/korean-writing/scripts/workbench.py run --input skills/korean-writing/examples/input.md --brief skills/korean-writing/examples/copyedit.brief.json --output demo-run --backend demo
```

`demo-run/final.txt`는 '연구팀은 분석했다. 참가자는 12명이다.'이다.
이 데모는 고정된 예문의 단계와 검사만 시험한다. 실제 원고를 교열하는 AI 모델은 별도로 현재 호스트나 API로 연결한다.

## brief 최소 예시

```json
{
  "mode": "copyedit",
  "genre": "general",
  "protected_strings": ["캐스퍼 일렉트릭"],
  "semantic_invariants": ["가능성을 확정적인 사실로 바꾸지 않는다"],
  "max_rounds": 3
}
```

protected_strings는 원문에 실제로 있는 표현을 지정한다. sources/style_samples에는 파일 경로가 아니라 실제 텍스트를 넣는다.
원문과 brief를 준비한 뒤 [런타임 안내](skills/korean-writing/references/runtime.md)의 host 또는 API 경로를 선택한다.
