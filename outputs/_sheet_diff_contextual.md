================================================================================
CONTEXTUAL DIFF REPORT
================================================================================


────────────────────────────────────────────────────────────────────────────────
📋 3.유저(앱)_회원  (12 filled cells)
────────────────────────────────────────────────────────────────────────────────

  [H8] (row 8, col H)
    field:  user_id
    meaning:앱 유저 한 명을 서버가 구분하기 위한 내부 ID입니다. 화면에 직접 보여주지 않습니다....
    ask:    대부분 화면에 직접 보여주지 않는 내부 식별값입니다. 상세 화면 이동, 딥링크, 디버깅에 필요한지만 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음

  [H9] (row 9, col H)
    field:  auth_method
    meaning:로그인 제공자입니다. 현재는 Apple Sign In만 가정합니다....
    ask:    입력 UI, placeholder, 누락 시 에러 문구, 최대/최소 길이 또는 선택 옵션을 정해주세요....
    ✏️  FILLED: Apple Sign In + 구글 로그인 + dev 로그인

  [H10] (row 10, col H)
    field:  apple_user_id
    meaning:Apple이 유저별로 내려주는 고유 식별값입니다. 같은 유저의 재로그인 식별에 사용합니다....
    ask:    대부분 화면에 직접 보여주지 않는 내부 식별값입니다. 상세 화면 이동, 딥링크, 디버깅에 필요한지만 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음
구글

  [H11] (row 11, col H)
    field:  nickname
    meaning:앱 커뮤니티와 프로필에 표시되는 유저 이름입니다....
    ask:    입력 UI, placeholder, 누락 시 에러 문구, 최대/최소 길이 또는 선택 옵션을 정해주세요....
    ✏️  FILLED: 닉네임: 한글/영문/숫자, 2~12자. 중복 불가, 공백 불가. 욕설/금칙어 필터링은 P1

  [H12] (row 12, col H)
    field:  profile_image_url
    meaning:프로필 사진의 저장 URL입니다. 실제 파일 업로드 후 서버가 URL을 저장합니다....
    ask:    입력하지 않았을 때 숨길지, 빈 문구를 보여줄지, 나중에 수정 가능하게 할지 정해주세요....
    ✏️  FILLED: 선택. 미입력 시 기본 아바타 표시. 

  [I12] (row 12, col I)
    field:  profile_image_url
    meaning:프로필 사진의 저장 URL입니다. 실제 파일 업로드 후 서버가 URL을 저장합니다....
    ask:    입력하지 않았을 때 숨길지, 빈 문구를 보여줄지, 나중에 수정 가능하게 할지 정해주세요....
    ✏️  FILLED: -> 달팽이 아바타 이미지 만들어야됨

  [H13] (row 13, col H)
    field:  bio
    meaning:프로필에 표시되는 짧은 자기소개입니다....
    ask:    입력하지 않았을 때 숨길지, 빈 문구를 보여줄지, 나중에 수정 가능하게 할지 정해주세요....
    ✏️  FILLED: 프로필 탭에서는 안보이고, 

  [H14] (row 14, col H)
    field:  preferred_tags
    meaning:유저가 선호하는 네일 스타일 태그입니다. 추천/온보딩에 활용할 수 있습니다....
    ask:    입력하지 않았을 때 숨길지, 빈 문구를 보여줄지, 나중에 수정 가능하게 할지 정해주세요....
    ✏️  FILLED: 선택. 최대 5개. 표준 태그 사전에서만 선택 (자유 입력 X). 온보딩에서 입력 권유

  [H15] (row 15, col H)
    field:  device_token
    meaning:APNs 푸시 발송에 필요한 기기 토큰입니다. 유저가 직접 입력하지 않습니다....
    ask:    입력 UI, placeholder, 누락 시 에러 문구, 최대/최소 길이 또는 선택 옵션을 정해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인 / 앱 실행 시 자동 갱신

  [H16] (row 16, col H)
    field:  app_version
    meaning:앱 강제 업데이트나 호환성 판단에 쓰는 클라이언트 버전입니다....
    ask:    입력 UI, placeholder, 누락 시 에러 문구, 최대/최소 길이 또는 선택 옵션을 정해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인 / 강제 업데이트 정책은 P1

  [H17] (row 17, col H)
    field:  created_at
    meaning:데이터가 처음 생성된 시각입니다. 화면에서는 작성일/등록일/가입일로 표시될 수 있습니다....
    ask:    직접 입력받지 않습니다. 목록/상세/상태 표시 또는 정렬·필터에 필요한지 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인

  [A20] (row 20, col A)
    field:  커뮤니티 탭 프로필이랑 자기소개 필요
    ✏️  FILLED: 커뮤니티 탭 프로필이랑 자기소개 필요

────────────────────────────────────────────────────────────────────────────────
📋 5.사장님(웹)_샵관리  (16 filled cells)
────────────────────────────────────────────────────────────────────────────────

  [H8] (row 8, col H)
    field:  owner_id
    meaning:사장님 계정 한 명을 서버가 구분하기 위한 내부 ID입니다. 사장님 웹 권한 확인에 사용합니다....
    ask:    대부분 화면에 직접 보여주지 않는 내부 식별값입니다. 상세 화면 이동, 딥링크, 디버깅에 필요한지만 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인

  [H9] (row 9, col H)
    field:  email
    meaning:로그인과 계정 식별에 사용하는 이메일입니다....
    ask:    입력 UI, placeholder, 누락 시 에러 문구, 최대/최소 길이 또는 선택 옵션을 정해주세요....
    ✏️  FILLED: 이메일 형식 검증 필수. 중복 가입 불가. 인증 메일 발송은 P1

  [H10] (row 10, col H)
    field:  password
    meaning:사장님 웹 로그인에 사용하는 비밀번호입니다. 서버에는 원문이 아니라 해시로 저장합니다....
    ask:    입력 UI, placeholder, 누락 시 에러 문구, 최대/최소 길이 또는 선택 옵션을 정해주세요....
    ✏️  FILLED: 최소 8자, 영문+숫자 조합. 특수문자 권장. 비밀번호 변경 P1

  [H11] (row 11, col H)
    field:  owner_name
    meaning:사업자 또는 사장님 이름입니다. 계정/사업자 인증 화면과 연결됩니다....
    ask:    입력 UI, placeholder, 누락 시 에러 문구, 최대/최소 길이 또는 선택 옵션을 정해주세요....
    ✏️  FILLED: 한글 2~20자, 사업자등록증과 일치해야 함

  [H12] (row 12, col H)
    field:  phone
    meaning:연락처입니다. 알림톡 수신 또는 샵 문의에 사용될 수 있습니다....
    ask:    입력 UI, placeholder, 누락 시 에러 문구, 최대/최소 길이 또는 선택 옵션을 정해주세요....
    ✏️  FILLED: 010-XXXX-XXXX 형식. SMS 인증 P1

  [H13] (row 13, col H)
    field:  business_number
    meaning:사업자등록번호입니다. 형식 검증과 외부 검증 여부를 정해야 합니다....
    ask:    입력 UI, placeholder, 누락 시 에러 문구, 최대/최소 길이 또는 선택 옵션을 정해주세요....
    ✏️  FILLED: 10자리 숫자, 국세청 형식 검증. 외부 검증 API는 P1 (MVP는 어드민 수동 검토)

  [H14] (row 14, col H)
    field:  business_license_image
    meaning:사업자등록증 파일입니다. 이미지 또는 PDF 업로드 정책이 필요합니다....
    ask:    입력 UI, placeholder, 누락 시 에러 문구, 최대/최소 길이 또는 선택 옵션을 정해주세요....
    ✏️  FILLED: 이미지/PDF, 최대 10MB. 어드민 검토용. 승인 후에도 보관

  [H15] (row 15, col H)
    field:  verification_status
    meaning:사업자 인증 진행 상태입니다. 승인 대기/승인/반려 화면에 사용합니다....
    ask:    직접 입력받지 않습니다. 목록/상세/상태 표시 또는 정렬·필터에 필요한지 확인해주세요....
    ✏️  FILLED: pending/approved/rejected. 승인 전엔 샵 등록만 가능, 디자인/예약은 X

  [H48] (row 48, col H)
    field:  designer_id
    meaning:디자이너 한 명을 서버가 구분하기 위한 내부 ID입니다. 예약 배정과 스케줄 계산에 사용합니다....
    ask:    대부분 화면에 직접 보여주지 않는 내부 식별값입니다. 상세 화면 이동, 딥링크, 디버깅에 필요한지만 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인

  [H49] (row 49, col H)
    field:  shop_id
    meaning:네일샵 하나를 서버가 구분하기 위한 내부 ID입니다. 샵 상세, 예약, 디자인, 리뷰를 연결합니다....
    ask:    대부분 화면에 직접 보여주지 않는 내부 식별값입니다. 상세 화면 이동, 딥링크, 디버깅에 필요한지만 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인

  [H50] (row 50, col H)
    field:  name
    meaning:사람, 샵, 디자이너 등 화면에 표시되는 이름입니다....
    ask:    입력 UI, placeholder, 누락 시 에러 문구, 최대/최소 길이 또는 선택 옵션을 정해주세요....
    ✏️  FILLED: 디자이너 이름. 한글/영문 1~15자

  [H51] (row 51, col H)
    field:  career_years
    meaning:디자이너 경력 연수입니다. 프로필 표시용입니다....
    ask:    입력하지 않았을 때 숨길지, 빈 문구를 보여줄지, 나중에 수정 가능하게 할지 정해주세요....
    ✏️  FILLED: 선택. 0~50년. 미입력 시 프로필에서 숨김

  [H52] (row 52, col H)
    field:  rank
    meaning:원장, 실장, 주니어 같은 직급입니다. 자유 입력인지 선택값인지 정해야 합니다....
    ask:    입력하지 않았을 때 숨길지, 빈 문구를 보여줄지, 나중에 수정 가능하게 할지 정해주세요....
    ✏️  FILLED: 선택. 표준 풀에서 선택 (원장/실장/디자이너/주니어). 자유 입력 X

  [H53] (row 53, col H)
    field:  profile_image_url
    meaning:프로필 사진의 저장 URL입니다. 실제 파일 업로드 후 서버가 URL을 저장합니다....
    ask:    입력하지 않았을 때 숨길지, 빈 문구를 보여줄지, 나중에 수정 가능하게 할지 정해주세요....
    ✏️  FILLED: 선택. 미입력 시 기본 아바타

  [H54] (row 54, col H)
    field:  specialty_tags
    meaning:디자이너가 잘하는 스타일 태그입니다. 사장님 웹에서 선택하게 할 수 있습니다....
    ask:    입력하지 않았을 때 숨길지, 빈 문구를 보여줄지, 나중에 수정 가능하게 할지 정해주세요....
    ✏️  FILLED: 선택. 최대 5개. 표준 태그 사전에서 선택

  [H55] (row 55, col H)
    field:  is_active
    meaning:현재 사용 가능한 대상인지 나타냅니다. 삭제 대신 비활성화할 때 사용합니다....
    ask:    입력 UI, placeholder, 누락 시 에러 문구, 최대/최소 길이 또는 선택 옵션을 정해주세요....
    ✏️  FILLED: 기본 true. 비활성 시 가용 슬롯 계산에서 제외. 삭제 대신 비활성화 권장

────────────────────────────────────────────────────────────────────────────────
📋 6.사장님(웹)_디자인  (7 filled cells)
────────────────────────────────────────────────────────────────────────────────

  [H30] (row 30, col H)
    field:  image_id
    meaning:업로드된 이미지 한 장을 구분하는 내부 ID입니다....
    ask:    대부분 화면에 직접 보여주지 않는 내부 식별값입니다. 상세 화면 이동, 딥링크, 디버깅에 필요한지만 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인

  [H31] (row 31, col H)
    field:  design_id
    meaning:예약 가능한 네일 디자인 상품 하나를 구분하는 내부 ID입니다....
    ask:    대부분 화면에 직접 보여주지 않는 내부 식별값입니다. 상세 화면 이동, 딥링크, 디버깅에 필요한지만 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인

  [H32] (row 32, col H)
    field:  original_url
    meaning:사장님이 올린 원본 이미지 URL입니다. LLM 재분석과 증빙을 위해 보관합니다....
    ask:    입력 UI, placeholder, 누락 시 에러 문구, 최대/최소 길이 또는 선택 옵션을 정해주세요....
    ✏️  FILLED: JPG/PNG/HEIC, 최대 10MB/장, 디자인당 1~5장

  [H33] (row 33, col H)
    field:  cropped_url
    meaning:LLM이 네일 영역을 추출해 만든 노출용 이미지 URL입니다....
    ask:    직접 입력받지 않습니다. 목록/상세/상태 표시 또는 정렬·필터에 필요한지 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인 / LLM Transform 결과

  [H34] (row 34, col H)
    field:  sort_order
    meaning:이미지나 항목의 노출 순서입니다. 0번을 대표 이미지로 쓰는 식의 규칙이 필요합니다....
    ask:    입력 UI, placeholder, 누락 시 에러 문구, 최대/최소 길이 또는 선택 옵션을 정해주세요....
    ✏️  FILLED: 0부터 시작. 0번이 대표 이미지. 사장님이 드래그로 순서 변경 가능

  [H35] (row 35, col H)
    field:  ai_transform_status
    meaning:LLM 1단계 네일 추출 처리 상태입니다....
    ask:    직접 입력받지 않습니다. 목록/상세/상태 표시 또는 정렬·필터에 필요한지 확인해주세요....
    ✏️  FILLED: pending/processing/success/failed. 실패해도 디자인 노출에 영향 X

  [H36] (row 36, col H)
    field:  ai_classify_status
    meaning:LLM 2단계 태그 분류 처리 상태입니다....
    ask:    직접 입력받지 않습니다. 목록/상세/상태 표시 또는 정렬·필터에 필요한지 확인해주세요....
    ✏️  FILLED: pending/processing/success/failed. 동일

────────────────────────────────────────────────────────────────────────────────
📋 8.커뮤니티_스네일  (15 filled cells)
────────────────────────────────────────────────────────────────────────────────

  [H8] (row 8, col H)
    field:  snap_id
    meaning:커뮤니티 스네일(Snap) 게시글 한 건을 구분하는 내부 ID입니다....
    ask:    대부분 화면에 직접 보여주지 않는 내부 식별값입니다. 상세 화면 이동, 딥링크, 디버깅에 필요한지만 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인

  [H9] (row 9, col H)
    field:  author_user_id
    meaning:스네일을 작성한 유저 ID입니다. 스네일은 일반 유저가 작성합니다....
    ask:    대부분 화면에 직접 보여주지 않는 내부 식별값입니다. 상세 화면 이동, 딥링크, 디버깅에 필요한지만 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인 / 작성자만 수정/삭제 가능

  [H10] (row 10, col H)
    field:  caption
    meaning:스네일 본문입니다. 선택 입력이지만 최대 길이와 금칙어 정책이 필요합니다....
    ask:    입력하지 않았을 때 숨길지, 빈 문구를 보여줄지, 나중에 수정 가능하게 할지 정해주세요....
    ✏️  FILLED: 선택. 최대 500자. 미입력 시 본문 영역 숨김. 금칙어는 P1

  [H11] (row 11, col H)
    field:  image_urls
    meaning:여러 장의 이미지 URL 목록입니다. 업로드 순서와 최대 장수를 화면에서 제한해야 합니다....
    ask:    입력 UI, placeholder, 누락 시 에러 문구, 최대/최소 길이 또는 선택 옵션을 정해주세요....
    ✏️  FILLED: 1~10장. JPG/PNG/HEIC, 장당 최대 10MB

  [H12] (row 12, col H)
    field:  tags
    meaning:검색, 분류, 필터에 사용하는 태그 목록입니다. 자유 입력인지 표준 태그 선택인지 확인이 필요합니다....
    ask:    입력하지 않았을 때 숨길지, 빈 문구를 보여줄지, 나중에 수정 가능하게 할지 정해주세요....
    ✏️  FILLED: 최대 8개. 표준 태그 사전에서 선택

  [H13] (row 13, col H)
    field:  tagged_shop_id
    meaning:스네일에 태그된 샵입니다. 샵 상세에 노출될 수 있습니다....
    ask:    대부분 화면에 직접 보여주지 않는 내부 식별값입니다. 상세 화면 이동, 딥링크, 디버깅에 필요한지만 확인해주세요....
    ✏️  FILLED: 선택. 1개만. 검색/탐색용

  [H14] (row 14, col H)
    field:  tagged_design_id
    meaning:스네일에 태그된 디자인입니다. 디자인 상세에 노출될 수 있습니다....
    ask:    대부분 화면에 직접 보여주지 않는 내부 식별값입니다. 상세 화면 이동, 딥링크, 디버깅에 필요한지만 확인해주세요....
    ✏️  FILLED: 선택. 1개만. 디자인 상세에 노출되는 조건

  [H15] (row 15, col H)
    field:  tagged_designer_id
    meaning:스네일에 태그된 디자이너입니다. 샵/디자인 태그와 함께 쓰입니다....
    ask:    대부분 화면에 직접 보여주지 않는 내부 식별값입니다. 상세 화면 이동, 딥링크, 디버깅에 필요한지만 확인해주세요....
    ✏️  FILLED: 선택. 1개만

  [H16] (row 16, col H)
    field:  tagged_reservation_id
    meaning:본인의 완료 예약을 태그한 경우 인증 뱃지 판단에 사용합니다....
    ask:    대부분 화면에 직접 보여주지 않는 내부 식별값입니다. 상세 화면 이동, 딥링크, 디버깅에 필요한지만 확인해주세요....
    ✏️  FILLED: 선택. 본인의 completed 예약만 연결 가능. 연결 시 '인증 스네일' 뱃지

  [H17] (row 17, col H)
    field:  like_count
    meaning:좋아요 수입니다. 서버가 자동 계산하며 화면에서는 숫자로 표시합니다....
    ask:    직접 입력받지 않습니다. 목록/상세/상태 표시 또는 정렬·필터에 필요한지 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인

  [H18] (row 18, col H)
    field:  comment_count
    meaning:댓글 수입니다. 서버가 자동 계산하며 목록 카드에서 표시할 수 있습니다....
    ask:    직접 입력받지 않습니다. 목록/상세/상태 표시 또는 정렬·필터에 필요한지 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인

  [H19] (row 19, col H)
    field:  view_count
    meaning:조회수입니다. 인기순/랭킹 계산에 활용될 수 있습니다....
    ask:    직접 입력받지 않습니다. 목록/상세/상태 표시 또는 정렬·필터에 필요한지 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인

  [H20] (row 20, col H)
    field:  popularity_score
    meaning:랭킹 탭 정렬에 쓰는 서버 계산 점수입니다....
    ask:    직접 입력받지 않습니다. 목록/상세/상태 표시 또는 정렬·필터에 필요한지 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인 / 좋아요×3 + 댓글×2 + 조회×0.1 + 최신성 가중치 (초안)

  [H21] (row 21, col H)
    field:  status
    meaning:현재 처리 상태입니다. 상태에 따라 화면 문구, 버튼 노출, 수정 가능 여부가 달라집니다....
    ask:    직접 입력받지 않습니다. 목록/상세/상태 표시 또는 정렬·필터에 필요한지 확인해주세요....
    ✏️  FILLED: active/hidden/deleted. hidden은 어드민/작성자 처리

  [H22] (row 22, col H)
    field:  created_at
    meaning:데이터가 처음 생성된 시각입니다. 화면에서는 작성일/등록일/가입일로 표시될 수 있습니다....
    ask:    직접 입력받지 않습니다. 목록/상세/상태 표시 또는 정렬·필터에 필요한지 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음.

────────────────────────────────────────────────────────────────────────────────
📋 9.커뮤니티_댓글  (10 filled cells)
────────────────────────────────────────────────────────────────────────────────

  [H8] (row 8, col H)
    field:  comment_id
    meaning:댓글 한 건을 구분하는 내부 ID입니다....
    ask:    대부분 화면에 직접 보여주지 않는 내부 식별값입니다. 상세 화면 이동, 딥링크, 디버깅에 필요한지만 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인

  [H9] (row 9, col H)
    field:  snap_id
    meaning:커뮤니티 스네일(Snap) 게시글 한 건을 구분하는 내부 ID입니다....
    ask:    대부분 화면에 직접 보여주지 않는 내부 식별값입니다. 상세 화면 이동, 딥링크, 디버깅에 필요한지만 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인

  [H10] (row 10, col H)
    field:  parent_comment_id
    meaning:대댓글이면 부모 댓글 ID가 들어가고, 일반 댓글이면 비어 있습니다....
    ask:    대부분 화면에 직접 보여주지 않는 내부 식별값입니다. 상세 화면 이동, 딥링크, 디버깅에 필요한지만 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인 / depth 2까지만 (대댓글까지). 대대댓글 X

  [H11] (row 11, col H)
    field:  author_type
    meaning:댓글 작성자가 일반 유저인지 샵 계정인지 구분합니다....
    ask:    입력 UI, placeholder, 누락 시 에러 문구, 최대/최소 길이 또는 선택 옵션을 정해주세요....
    ✏️  FILLED: user/shop. 샵 계정도 댓글 가능 (의사결정기록 4번 참조)

  [H12] (row 12, col H)
    field:  author_user_id
    meaning:일반 유저 댓글일 때 작성자 ID입니다....
    ask:    대부분 화면에 직접 보여주지 않는 내부 식별값입니다. 상세 화면 이동, 딥링크, 디버깅에 필요한지만 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인

  [H13] (row 13, col H)
    field:  author_shop_id
    meaning:샵 계정 댓글일 때 작성 샵 ID입니다....
    ask:    대부분 화면에 직접 보여주지 않는 내부 식별값입니다. 상세 화면 이동, 딥링크, 디버깅에 필요한지만 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인

  [H14] (row 14, col H)
    field:  content
    meaning:댓글 본문입니다. 최대 길이와 신고/금칙어 정책이 필요합니다....
    ask:    입력 UI, placeholder, 누락 시 에러 문구, 최대/최소 길이 또는 선택 옵션을 정해주세요....
    ✏️  FILLED: 최대 300자. 금칙어/도배 방지는 P1

  [H15] (row 15, col H)
    field:  like_count
    meaning:좋아요 수입니다. 서버가 자동 계산하며 화면에서는 숫자로 표시합니다....
    ask:    직접 입력받지 않습니다. 목록/상세/상태 표시 또는 정렬·필터에 필요한지 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인

  [H16] (row 16, col H)
    field:  status
    meaning:현재 처리 상태입니다. 상태에 따라 화면 문구, 버튼 노출, 수정 가능 여부가 달라집니다....
    ask:    직접 입력받지 않습니다. 목록/상세/상태 표시 또는 정렬·필터에 필요한지 확인해주세요....
    ✏️  FILLED: active/hidden/deleted. 삭제된 댓글은 '삭제된 댓글입니다' 표시

  [H17] (row 17, col H)
    field:  created_at
    meaning:데이터가 처음 생성된 시각입니다. 화면에서는 작성일/등록일/가입일로 표시될 수 있습니다....
    ask:    직접 입력받지 않습니다. 목록/상세/상태 표시 또는 정렬·필터에 필요한지 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인

────────────────────────────────────────────────────────────────────────────────
📋 10.커뮤니티_리뷰  (14 filled cells)
────────────────────────────────────────────────────────────────────────────────

  [H8] (row 8, col H)
    field:  review_id
    meaning:리뷰 한 건을 구분하는 내부 ID입니다....
    ask:    대부분 화면에 직접 보여주지 않는 내부 식별값입니다. 상세 화면 이동, 딥링크, 디버깅에 필요한지만 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인

  [H9] (row 9, col H)
    field:  reservation_id
    meaning:예약 한 건을 구분하는 내부 ID입니다. 리뷰, 알림, 취소/노쇼 이력과 연결됩니다....
    ask:    대부분 화면에 직접 보여주지 않는 내부 식별값입니다. 상세 화면 이동, 딥링크, 디버깅에 필요한지만 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인 / 1예약=1리뷰 UNIQUE 제약

  [H10] (row 10, col H)
    field:  author_user_id
    meaning:리뷰를 작성한 유저 ID입니다. 예약자와 일치해야 합니다....
    ask:    대부분 화면에 직접 보여주지 않는 내부 식별값입니다. 상세 화면 이동, 딥링크, 디버깅에 필요한지만 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인

  [H11] (row 11, col H)
    field:  shop_id
    meaning:네일샵 하나를 서버가 구분하기 위한 내부 ID입니다. 샵 상세, 예약, 디자인, 리뷰를 연결합니다....
    ask:    대부분 화면에 직접 보여주지 않는 내부 식별값입니다. 상세 화면 이동, 딥링크, 디버깅에 필요한지만 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인

  [H12] (row 12, col H)
    field:  design_id
    meaning:예약 가능한 네일 디자인 상품 하나를 구분하는 내부 ID입니다....
    ask:    대부분 화면에 직접 보여주지 않는 내부 식별값입니다. 상세 화면 이동, 딥링크, 디버깅에 필요한지만 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인

  [H13] (row 13, col H)
    field:  rating
    meaning:샵에 대한 별점입니다. 디자이너 별점은 저장하지 않습니다....
    ask:    입력 UI, placeholder, 누락 시 에러 문구, 최대/최소 길이 또는 선택 옵션을 정해주세요....
    ✏️  FILLED: 1~5점, 정수만. 0점 또는 소수점 X

  [H14] (row 14, col H)
    field:  content
    meaning:리뷰 본문입니다. 최소/최대 길이를 정해야 합니다....
    ask:    입력 UI, placeholder, 누락 시 에러 문구, 최대/최소 길이 또는 선택 옵션을 정해주세요....
    ✏️  FILLED: 최소 10자, 최대 1,000자

  [H15] (row 15, col H)
    field:  image_urls
    meaning:여러 장의 이미지 URL 목록입니다. 업로드 순서와 최대 장수를 화면에서 제한해야 합니다....
    ask:    입력하지 않았을 때 숨길지, 빈 문구를 보여줄지, 나중에 수정 가능하게 할지 정해주세요....
    ✏️  FILLED: 선택. 0~5장. JPG/PNG/HEIC, 장당 최대 10MB

  [H16] (row 16, col H)
    field:  tags
    meaning:검색, 분류, 필터에 사용하는 태그 목록입니다. 자유 입력인지 표준 태그 선택인지 확인이 필요합니다....
    ask:    입력하지 않았을 때 숨길지, 빈 문구를 보여줄지, 나중에 수정 가능하게 할지 정해주세요....
    ✏️  FILLED: 선택. 최대 5개. 표준 태그 사전에서 선택 (예: 친절함, 분위기 좋음)

  [H17] (row 17, col H)
    field:  shop_reply
    meaning:사장님이 리뷰에 남기는 답변입니다....
    ask:    입력하지 않았을 때 숨길지, 빈 문구를 보여줄지, 나중에 수정 가능하게 할지 정해주세요....
    ✏️  FILLED: 선택. 사장님만 작성. 최대 500자. 1리뷰당 1답변

  [H18] (row 18, col H)
    field:  shop_reply_at
    meaning:사장님 답변 작성 시각입니다....
    ask:    직접 입력받지 않습니다. 목록/상세/상태 표시 또는 정렬·필터에 필요한지 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인

  [H19] (row 19, col H)
    field:  like_count
    meaning:좋아요 수입니다. 서버가 자동 계산하며 화면에서는 숫자로 표시합니다....
    ask:    직접 입력받지 않습니다. 목록/상세/상태 표시 또는 정렬·필터에 필요한지 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인

  [H20] (row 20, col H)
    field:  status
    meaning:현재 처리 상태입니다. 상태에 따라 화면 문구, 버튼 노출, 수정 가능 여부가 달라집니다....
    ask:    직접 입력받지 않습니다. 목록/상세/상태 표시 또는 정렬·필터에 필요한지 확인해주세요....
    ✏️  FILLED: active/hidden/deleted. 작성 후 7일 내 수정/삭제 가능

  [H21] (row 21, col H)
    field:  created_at
    meaning:데이터가 처음 생성된 시각입니다. 화면에서는 작성일/등록일/가입일로 표시될 수 있습니다....
    ask:    직접 입력받지 않습니다. 목록/상세/상태 표시 또는 정렬·필터에 필요한지 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인

────────────────────────────────────────────────────────────────────────────────
📋 11.커뮤니티_신고  (8 filled cells)
────────────────────────────────────────────────────────────────────────────────

  [H8] (row 8, col H)
    field:  report_id
    meaning:신고 한 건을 구분하는 내부 ID입니다....
    ask:    대부분 화면에 직접 보여주지 않는 내부 식별값입니다. 상세 화면 이동, 딥링크, 디버깅에 필요한지만 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인

  [H9] (row 9, col H)
    field:  reporter_id
    meaning:신고한 사람의 ID입니다. 유저 또는 사장님일 수 있습니다....
    ask:    대부분 화면에 직접 보여주지 않는 내부 식별값입니다. 상세 화면 이동, 딥링크, 디버깅에 필요한지만 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인 / 동일 신고자가 같은 대상 24시간 내 중복 신고 불가

  [H10] (row 10, col H)
    field:  target_type
    meaning:신고 대상 종류입니다. 스네일, 댓글, 리뷰, 유저, 샵 중 하나입니다....
    ask:    입력 UI, placeholder, 누락 시 에러 문구, 최대/최소 길이 또는 선택 옵션을 정해주세요....
    ✏️  FILLED: snap/comment/review/user/shop

  [H11] (row 11, col H)
    field:  target_id
    meaning:신고 대상의 실제 ID입니다....
    ask:    대부분 화면에 직접 보여주지 않는 내부 식별값입니다. 상세 화면 이동, 딥링크, 디버깅에 필요한지만 확인해주세요....
    ✏️  FILLED: 내부 식별값. 화면 노출 없음. → 프론트(곽민지) 확인

  [H12] (row 12, col H)
    field:  reason_code
    meaning:신고 사유 선택값입니다. 프론트/UI가 문구를 확정해야 합니다....
    ask:    입력 UI, placeholder, 누락 시 에러 문구, 최대/최소 길이 또는 선택 옵션을 정해주세요....
    ✏️  FILLED: 선택지 (MVP):
- spam (스팸/광고)
- inappropriate (부적절/혐오)
- false_info (허위정보)
- impersonation (사칭)
- copyright (저작권 침해)
- other (기타)
→ 디자이너 UI 문구 협의

  [H13] (row 13, col H)
    field:  reason_detail
    meaning:신고나 처리 사유를 더 자세히 적는 선택 입력값입니다....
    ask:    입력하지 않았을 때 숨길지, 빈 문구를 보여줄지, 나중에 수정 가능하게 할지 정해주세요....
    ✏️  FILLED: 선택. 최대 500자

  [H14] (row 14, col H)
    field:  status
    meaning:현재 처리 상태입니다. 상태에 따라 화면 문구, 버튼 노출, 수정 가능 여부가 달라집니다....
    ask:    직접 입력받지 않습니다. 목록/상세/상태 표시 또는 정렬·필터에 필요한지 확인해주세요....
    ✏️  FILLED: pending/reviewing/resolved/dismissed

  [H15] (row 15, col H)
    field:  resolved_action
    meaning:운영자가 신고 처리 후 적용한 조치입니다....
    ask:    입력하지 않았을 때 숨길지, 빈 문구를 보여줄지, 나중에 수정 가능하게 할지 정해주세요....
    ✏️  FILLED: hide/delete/warn/ban/none. 어드민이 처리 후 입력

────────────────────────────────────────────────────────────────────────────────
📋 12.LLM명세  (22 filled cells)
────────────────────────────────────────────────────────────────────────────────

  [C10] (row 10, col C)
    A: 목적
    B: 원본 사진에서 네일 영역 추출 + 규격화
    C: 원본 사진에서 네일 영역 추출 + 정사각형 정규화 (동일)
    ✏️  FILLED: 원본 사진에서 네일 영역 추출 + 정사각형 정규화 (동일)

  [C11] (row 11, col C)
    A: 제안 endpoint
    B: /v1/transform
    C: 그대로 사용 OK / 비동기 처리이므로 큐 기반으로 운영
    ✏️  FILLED: 그대로 사용 OK / 비동기 처리이므로 큐 기반으로 운영

  [C12] (row 12, col C)
    A: Request fields
    B: image_url, image_id, callback_url, options.output_size, options.background
    C: input:
- image_url (string): 원본 이미지 URL (S3)
- image_id (string): 백엔드가 부여하는 식별자
...
    ✏️  FILLED: input:
- image_url (string): 원본 이미지 URL (S3)
- image_id (string): 백엔드가 부여하는 식별자
- callback_url (string): 분석 완료 시 호출
- options.output_size (int, default=1024): 정사각형 한 변 길이
- options.background (enum: w...

  [C13] (row 13, col C)
    A: Response fields
    B: image_id, status, cropped_image_url, cropped_image_size, confidence, nail_count_...
    C: output (예시):
- image_id (string): 요청과 동일한 ID 에코
- status (enum: success / failed...
    ✏️  FILLED: output (예시):
- image_id (string): 요청과 동일한 ID 에코
- status (enum: success / failed)
- cropped_image_url (string): 처리된 이미지 URL
- cropped_image_size (int): 한 변 크기
- confidence (float): 0.0~1.0
- nail_coun...

  [C14] (row 14, col C)
    A: 운영 권장
    B: 5초 이내면 동기, 10초 이상이면 비동기 webhook 권장
    C: 비동기 callback 권장 (Module 1 합쳐 1~10분 소요).
동기 5초 기준은 못 맞춤 → 큐+webhook 방식으로 운영.
사용자 ...
    ✏️  FILLED: 비동기 callback 권장 (Module 1 합쳐 1~10분 소요).
동기 5초 기준은 못 맞춤 → 큐+webhook 방식으로 운영.
사용자 노출엔 영향 없음 (분석 안 끝나도 사장님 태그로 노출).

  [C19] (row 19, col C)
    A: 목적
    B: cropped 이미지에서 태그/색상/스타일 분류
    C: cropped 이미지에서 태그/색상/스타일/분위기 분류 (동일)
    ✏️  FILLED: cropped 이미지에서 태그/색상/스타일/분위기 분류 (동일)

  [C20] (row 20, col C)
    A: 제안 endpoint
    B: /v1/classify
    C: 그대로 사용 OK / 비동기 처리
    ✏️  FILLED: 그대로 사용 OK / 비동기 처리

  [C21] (row 21, col C)
    A: Request fields
    B: image_url, image_id, locale, options.max_tags, options.include_color_palette, op...
    C: input:
- image_url (string): cropped 이미지 URL
- image_id (string)
- locale (strin...
    ✏️  FILLED: input:
- image_url (string): cropped 이미지 URL
- image_id (string)
- locale (string, default="ko"): 한글/영문 태그 반환 결정
- options.max_tags (int, default=5)
- options.include_color_palette (bool, default=true...

  [C22] (row 22, col C)
    A: Response fields
    B: image_id, status, tags, color_palette, style_category, nail_shape, confidence_ov...
    C: output (예시):
- image_id (string)
- status (enum: success / failed)
- tags (strin...
    ✏️  FILLED: output (예시):
- image_id (string)
- status (enum: success / failed)
- tags (string[]): 표준 태그 사전 내 값 (최대 5개)
- color_palette ({hex, name_ko}[]): 주요 색상 (최대 3개)
- style_category (enum): simple/glamour/cla...

  [C27] (row 27, col C)
    A: style
    B: 프렌치, 옴브레, 그라데이션, 마그넷, 글리터, 큐빅, 라인아트, 캐릭터, 무광, 유광
    C: 제안 그대로 OK. 운영하며 새 트렌드 발견 시 추가 가능 (Y2K, 청키 등)
    ✏️  FILLED: 제안 그대로 OK. 운영하며 새 트렌드 발견 시 추가 가능 (Y2K, 청키 등)

  [C28] (row 28, col C)
    A: color
    B: 핑크, 레드, 누드, 블랙, 화이트, 베이지, 블루, 그린, 옐로우, 퍼플, 브라운, 골드, 실버
    C: 제안 그대로 OK. hex 코드와 한글 라벨 동시 반환 (예: {"hex":"#FFB6C1","name":"핑크"})
    ✏️  FILLED: 제안 그대로 OK. hex 코드와 한글 라벨 동시 반환 (예: {"hex":"#FFB6C1","name":"핑크"})

  [C29] (row 29, col C)
    A: mood
    B: 봄, 여름, 가을, 겨울, 시크, 러블리, 심플, 글래머, 내추럴, 키치, 모던
    C: 제안 그대로 OK. 봄/여름/가을/겨울은 mood가 아닌 season으로 분리 권장
    ✏️  FILLED: 제안 그대로 OK. 봄/여름/가을/겨울은 mood가 아닌 season으로 분리 권장

  [C30] (row 30, col C)
    A: technique
    B: 젤, 매니큐어, 페디큐어, 연장, 케어, 제거
    C: 제안에서 일부 조정 필요.
'페디큐어/연장/케어/제거'는 시술 카테고리라 디자인 태그로는 부적합.
디자인용으로는 '젤, 매니큐어, 페디큐어' 정...
    ✏️  FILLED: 제안에서 일부 조정 필요.
'페디큐어/연장/케어/제거'는 시술 카테고리라 디자인 태그로는 부적합.
디자인용으로는 '젤, 매니큐어, 페디큐어' 정도만 사용 권장.
나머지는 샵 메타데이터로 분리하는 게 좋음.

  [C31] (row 31, col C)
    A: shape
    B: 스퀘어, 라운드, 오벌, 아몬드, 스틸레토, 발레리나
    C: 제안 그대로 OK.
    ✏️  FILLED: 제안 그대로 OK.

  [C32] (row 32, col C)
    A: style_category
    B: simple, glamour, classic, trendy, chic
    C: 제안 그대로 OK. 영문 키 유지 (UI 표시는 한글 라벨 매핑 테이블로 처리)
    ✏️  FILLED: 제안 그대로 OK. 영문 키 유지 (UI 표시는 한글 라벨 매핑 테이블로 처리)

  [C33] (row 33, col C)
    A: occasion
    B: 웨딩, 데일리, 파티, 오피스, 데이트
    C: 제안 그대로 OK.
    ✏️  FILLED: 제안 그대로 OK.

  [D38] (row 38, col D)
    A: NO_NAIL
    B: 사진에서 네일이 감지되지 않음
    C: 사진에서 네일을 찾지 못했어요. 손이 잘 보이는 사진으로 다시 올려주세요.
    D: 코드명 변경 제안: NO_NAIL → NAIL_NOT_DETECTED (더 명확)
메시지 OK.
    ✏️  FILLED: 코드명 변경 제안: NO_NAIL → NAIL_NOT_DETECTED (더 명확)
메시지 OK.

  [D39] (row 39, col D)
    A: LOW_QUALITY
    B: 해상도 낮음/블러/조명 부족
    C: 사진 화질이 낮아요. 좀 더 선명한 사진으로 시도해주세요.
    D: 그대로 OK.
    ✏️  FILLED: 그대로 OK.

  [D40] (row 40, col D)
    A: MULTIPLE_HANDS
    B: 여러 명의 손이 섞임
    C: 한 사람의 손만 나오는 사진으로 올려주세요.
    D: 그대로 OK.
    ✏️  FILLED: 그대로 OK.

  [D41] (row 41, col D)
    A: OBSTRUCTED
    B: 네일이 가려짐
    C: 네일이 잘 보이도록 다시 촬영해주세요.
    D: 그대로 OK.
    ✏️  FILLED: 그대로 OK.

  [D42] (row 42, col D)
    A: INAPPROPRIATE
    B: 부적절 콘텐츠 감지
    C: 이 사진은 업로드할 수 없습니다.
    D: 그대로 OK.
부적절 콘텐츠 감지 시 어드민 알림 함께 발송 권장.
    ✏️  FILLED: 그대로 OK.
부적절 콘텐츠 감지 시 어드민 알림 함께 발송 권장.

  [D43] (row 43, col D)
    A: INTERNAL_ERROR
    B: LLM 내부 에러
    C: 잠시 후 다시 시도해주세요.
    D: 그대로 OK.
백엔드는 INTERNAL_ERROR만 재시도, 나머지는 사장님에게 즉시 노출.
    ✏️  FILLED: 그대로 OK.
백엔드는 INTERNAL_ERROR만 재시도, 나머지는 사장님에게 즉시 노출.

────────────────────────────────────────────────────────────────────────────────
📋 14.의사결정기록  (1 filled cells)
────────────────────────────────────────────────────────────────────────────────

  [D61] (row 61, col D)
    A: 문서 버전 전략
    B: v3를 계속 수정할지, v4 파일로 분리해 확정본을 만들지 결정
    C: 팀 내부
    D: 필요 없음
    ✏️  FILLED: 필요 없음