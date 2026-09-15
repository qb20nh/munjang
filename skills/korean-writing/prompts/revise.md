# 수정 단계
진단을 현재 원문과 문맥으로 다시 확인한다. 정당한 지적만 최소 범위로 고친다.
copyedit에서는 rewrite=null을 유지하고, 수정할 unit마다 patches 하나를 작성한다.
patch.before는 해당 unit의 전체 text를 한 글자도 바꾸지 않고 복사한다. after는 수정한 전체 unit text이다.
단위 밖의 공백·줄바꿈·목록기호를 바꾸지 않는다. issue_ids는 그 unit을 지목한 진단만 참조한다.
여러 진단이 한 unit에 걸리면 patch 하나에 issue_ids를 모은다. 같은 unit을 두 번 수정하지 않는다.
잘못된 진단이나 취향 차이는 적용하지 않고 skipped_issue_ids에 기록한다. 모든 진단은 적용 또는 건너뛰기로 처리한다.
restructure 또는 draft의 후속 편집에서는 필요할 때 patches=[]와 rewrite 전체 본문을 사용할 수 있다. 필수 정보와 의미는 유지한다.
표현의 개선을 위해 사실, 인용, 수치·단위, 주장 강도, 목소리를 바꾸지 않는다. 판단할 수 없으면 보존한다.
base_sha256을 그대로 복사하고 response_schema에 맞는 JSON만 반환한다. 새 아이디어를 이유 없이 덧붙이지 않는다.
