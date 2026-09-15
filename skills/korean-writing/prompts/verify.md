# 검증 단계
수정자가 고쳤다는 사실을 개선의 증거로 삼지 않는다. 원래 요청, 원문과 자료, 현재 글과 후보를 직접 대조한다.
original_units와 candidate_units의 editable=true인 ID를 각각 빠짐없이 검토하고 대응하는 reviewed_*_ids에 기록한다.
required_checks의 12개 차원을 각각 pass/fail/uncertain과 짧고 구체적인 evidence로 평가한다.
특히 주체·대상 전도, 부정, 조건·예외, 가능·의무, 시작·진행·완료, 수량 범위, 수치와 대상의 연결, 상관과 인과, 발언 귀속을 확인한다.
evidence_fidelity는 제공된 자료와의 일치 여부다. 외부 웹을 실제로 확인하지 않았다면 외부 사실 검증을 했다고 주장하지 않는다.
불확실함을 통과로 채우지 않는다. 모든 필수 조건이 pass이고, 실제 지적 하나 이상을 해결했고, 새 문제가 없을 때만 accept다.
resolved_issue_ids와 unresolved_issue_ids는 전체 진단 ID를 겹치지 않게 나눈다. 새 문제는 new_issues에 쓴다.
위반이면 reject, 판단할 자료가 부족하면 needs_review, 단순히 다른 표현이면 기존 문장을 유지하도록 reject한다.
base_sha256과 candidate_sha256은 입력값을 복사한다. 결과는 response_schema에 맞는 JSON 한 개다.
검토 기록에는 관찰 가능한 근거만 간단히 남긴다. 숨은 사고 과정이나 모델의 자체 품질 점수를 요구하지 않는다.
