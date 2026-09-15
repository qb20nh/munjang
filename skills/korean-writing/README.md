# Korean Writing Skill 1.0.0

이 폴더 전체를 호스트의 스킬 디렉터리에 복사한다. 진입점은 `SKILL.md`다.
Codex 예: `~/.agents/skills/korean-writing/SKILL.md`.
Claude 독립 스킬 예: `~/.claude/skills/korean-writing/SKILL.md`.
호스트의 스킬 로딩 안내에 따라 재시작/새 검색 후 호출한다.

Python이 없어도 글쓰기 지침은 사용할 수 있다. 감사 가능한 실행기에는 Python 3.10 이상이 필요하다.
외부 패키지 설치는 없다. 네트워크/API는 사용자가 명시적으로 선택한 실제 모델 실행에만 필요하다.

```sh
python scripts/workbench.py --help
python scripts/workbench.py run --input examples/input.md --brief examples/copyedit.brief.json --output demo-run --backend demo
python -m unittest discover -s tests -v
```

데모는 시뮬레이터다. 실제 LLM 의미 품질을 측정하지 않는다.
[런타임 안내](references/runtime.md), [검증 한계](references/verification.md), [출처](references/sources.md)를 읽는다.
원문과 요청/응답이 로컬 실행 디렉터리에 남으므로 공개 전에 개인정보를 제거한다.
이 standalone 배포판은 root 플러그인 카탈로그와 선택적 호스트 에이전트가 없는 대신 스킬/실행기/테스트는 자체 포함한다.

[실제 테스트 범위](TEST-REPORT.md)도 확인한다.
