# 설계 근거와 자료 범위

검토 기준일: 2026-09-15. 이 패키지는 대화에서 작성한 한국어 통합 프롬프트와 운영 메모를 모듈화하고,
새 Python 실행기, 프로토콜, 테스트, 설치 지침을 구현한 것이다. 특정 모델에서 글의 품질이 최적이라는 실험 결과는 아니다.

## 이전 조사에 기반한 참고 자료

- epoko77-ai/im-not-ai: https://github.com/epoko77-ai/im-not-ai
- Turtle-Hwan/im-ai-copyeditor: https://github.com/Turtle-Hwan/im-ai-copyeditor
- 김정선, 《내 문장이 그렇게 이상한가요?》: 군더더기, 표현 관계와 맥락적 교열.
- 배상복, 《문장기술》: 호응, 정확한 표현, 어순과 읽기 흐름.
- 윌리엄 케인, 《위대한 작가는 어떻게 쓰는가》: 개별 문체 복제보다 목적에 맞는 기법 선택.
- 스티븐 킹, 《유혹하는 글쓰기》: 구체성, 상투성 점검과 자기 목소리.
- 윌리엄 진서, 《글쓰기 생각쓰기》: 간소함, 독자, 통일성과 목소리.
- William Strunk Jr., The Elements of Style, 공개된 원판: https://www.gutenberg.org/ebooks/37134

책의 전문을 모두 읽었다고 주장하지 않는다. 이전 조사는 공개된 목차, 소개, 확인 가능한 발췌 범위였다.
Strunk 공개 원판을 Strunk/White 합저 개정판 전체와 동일한 자료로 취급하지 않는다.
《소설가의 낱말》과 제시된 공저자 조합, 이정록의 《시인의 감성사전》은 이전 조사에서 확인되지 않았다.
이 두 자료의 내용을 추측하여 저자에게 귀속하지 않는다. 어휘/감각 예시는 이 패키지의 독자적 예시다.
저장소의 소스코드나 책의 본문을 복사해 포함하지 않았다. 라이선스가 다른 자료를 자동으로 MIT로 바꾼 것이 아니다.

## 반복 교열과 평가의 한계

Self-Refine: https://arxiv.org/abs/2303.17651
Large Language Models Cannot Self-Correct Reasoning Yet: https://arxiv.org/abs/2310.01798
CRITIC: https://arxiv.org/abs/2305.11738

자기 피드백의 개선 가능성과 실패 가능성을 함께 고려한다. 해당 연구 결과를 한국어 모든 장르와 현재 모든 모델로 일반화하지 않는다.
기본 3라운드는 무한 루프와 비용을 제한하는 운영값이다. 역할 분리, 다른 리뷰어, 해시 검사는 독립적인 진실 보증이 아니다.

## 설치 형식의 공식 문서

- Agent Skills specification: https://agentskills.io/specification
- Codex / ChatGPT skills: https://developers.openai.com/codex/skills/
- Portable plugins: https://developers.openai.com/plugins/build/plugins
- Agent plugin schema: https://agent-plugins.org/schemas/1.0.0/plugin.schema.json
- Claude Code plugins: https://code.claude.com/docs/en/plugins
- Claude Code subagents: https://code.claude.com/docs/en/sub-agents
- Codex custom subagents: https://learn.chatgpt.com/docs/agent-configuration/subagents

portable root plugin.json과 호환용 호스트 manifest를 함께 제공한다. 문서 구조를 따랐다는 것과 실제 호스트에서 설치 시험을 마쳤다는 것은 다르다.
실제 시험 범위는 패키지 `docs/TEST-REPORT.md`에 기록한다. 공개 디렉터리 등록, 서명, 계정 설치는 하지 않았다.
