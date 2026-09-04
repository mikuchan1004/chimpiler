# ID, CLASS, 변수명 정리

## 공통 ID

| ID | 사용 위치 | JS/Python 변수명 예시 | 용도 |
|---|---|---|---|
| siteHeader | layout | site_header | 공통 헤더 |
| siteFooter | layout | site_footer | 공통 푸터 및 하단 이동 위치 |
| siteDrawer | layout | site_drawer | 햄버거 메뉴 영역 |
| menuOpenButton | layout | menu_open_button | 햄버거 메뉴 열기 |
| menuCloseButton | layout | menu_close_button | 햄버거 메뉴 닫기 |
| welcomeMessage | layout | welcome_message | 로그인 회원 환영 문구 |
| chatOpenButton | layout | chat_open_button | 챗봇 상담창 열기 |

## 상품·주문 ID

| ID | 변수명 예시 | 용도 |
|---|---|---|
| bestProductList | best_product_list | 메인 인기 상품 목록 |
| bestProductPrevious | best_product_previous | 인기 상품 이전 목록 이동 |
| bestProductNext | best_product_next | 인기 상품 다음 목록 이동 |
| randomProductList | random_product_list | 메인 랜덤 상품 출력 영역 |
| randomProductRefresh | random_product_refresh | 랜덤 상품 다시 불러오기 |
| categoryNavigation | category_navigation | 상품 카테고리 선택 |
| productSearchForm | product_search_form | 상품 검색 폼 |
| productSearchInput | product_search_input | 상품 검색어 |
| productSortSelect | product_sort_select | 조회순·가격순 정렬 |
| productList | product_list | 상품 목록 출력 영역 |
| productCount | product_count | 검색 결과 상품 개수 |
| productMainImage | product_main_image | 상품 상세 대표 이미지 |
| productName | product_name | 상품명 출력 |
| productPrice | product_price | 상품 단가 출력 |
| saleStock | sale_stock | 판매 가능 재고 |
| reservationStock | reservation_stock | 예약 배정 재고 |
| productQuantity | product_quantity | 구매 수량 |
| quantityMinus | quantity_minus | 수량 감소 |
| quantityPlus | quantity_plus | 수량 증가 |
| totalPrice | total_price | 수량 반영 상품 금액 |
| cartAddButton | cart_add_button | 장바구니 추가 |
| buyNowButton | buy_now_button | 즉시 구매 |
| reservationButton | reservation_button | 품절 상품 예약 |
| reservationConfirmModal | reservation_confirm_modal | 예약 확인 팝업 |
| reservationQueueNumber | reservation_queue_number | 예약 대기 순번 |
| cartItemList | cart_item_list | 장바구니 상품 목록 |
| cartSelectAll | cart_select_all | 장바구니 상품 전체 선택 |
| cartSelectedDeleteButton | cart_selected_delete_button | 선택한 장바구니 상품 삭제 |
| cartTotalPrice | cart_total_price | 장바구니 총금액 |
| cartCheckoutButton | cart_checkout_button | 선택 상품 주문 |
| checkoutForm | checkout_form | 주문서 작성 폼 |
| receiverName | receiver_name | 수령인 |
| receiverPhone | receiver_phone | 수령인 연락처 |
| receiverAddress | receiver_address | 배송지 기본 주소 |
| receiverAddressDetail | receiver_address_detail | 배송지 상세 주소 |
| addressSearchButton | address_search_button | 주소 검색 API 호출 |
| cardNumber | card_number | 카드번호 입력 |
| cardExpiry | card_expiry | 카드 유효기간 |
| cardCvc | card_cvc | 카드 CVC |
| paymentSubmitButton | payment_submit_button | 결제 검증 및 처리 |
| paymentResultTitle | payment_result_title | 결제 성공·실패 제목 |
| continueShoppingButton | continue_shopping_button | 상품 목록으로 돌아가기 |
| refundRequestButton | refund_request_button | 결제 주문 환불 요청 |
| reservationPriorityButton | reservation_priority_button | 현재 예약 우선순위 조회 |
| inquiryDeleteButton | inquiry_delete_button | 내 문의 삭제 |
| recommendedCheckoutButton | recommended_checkout_button | AI 추천 상품 주문서 작성 |
| healthHomeButton | health_home_button | AI 화면에서 메인으로 이동 |
| expertConsultButton | expert_consult_button | 전문가 상담 화면 이동 |

## 회원·마이페이지 ID

| ID | 변수명 예시 | 용도 |
|---|---|---|
| loginForm | login_form | 일반 로그인 폼 |
| loginUserId | login_user_id | 로그인 아이디 |
| loginPassword | login_password | 로그인 비밀번호 |
| loginErrorMessage | login_error_message | 로그인 오류 출력 |
| naverLoginButton | naver_login_button | 네이버 OAuth 시작 |
| kakaoLoginButton | kakao_login_button | 카카오 OAuth 시작 |
| signupForm | signup_form | 회원가입 폼 |
| signupUserId | signup_user_id | 가입 아이디 |
| idCheckButton | id_check_button | 아이디 중복 확인 |
| idCheckMessage | id_check_message | 중복 확인 결과 |
| signupPassword | signup_password | 가입 비밀번호 |
| signupPasswordConfirm | signup_password_confirm | 비밀번호 재확인 |
| signupAddressButton | signup_address_button | 가입 주소 검색 |
| phoneVerifyButton | phone_verify_button | 휴대폰 인증 |
| profileForm | profile_form | 회원정보 수정 폼 |
| passwordChangeButton | password_change_button | 비밀번호 팝업 열기 |
| passwordChangeModal | password_change_modal | 비밀번호 변경 팝업 |
| profileSaveButton | profile_save_button | 회원정보 저장 |
| reservationCancelButton | reservation_cancel_button | 예약 취소 확인 |

## 커뮤니티·AI ID

| ID | 변수명 예시 | 용도 |
|---|---|---|
| noticeSearchForm | notice_search_form | 공지사항 검색 |
| noticeList | notice_list | 공지사항 목록 |
| faqList | faq_list | FAQ 목록 |
| inquiryForm | inquiry_form | 1:1 문의 폼 |
| inquiryType | inquiry_type | 문의 유형 |
| inquiryTitle | inquiry_title | 문의 제목 |
| inquiryDetail | inquiry_detail | 문의 내용 |
| inquiryAttachment | inquiry_attachment | 문의 첨부파일 |
| healthCheckForm | health_check_form | 건강정보 입력 폼 |
| healthWeight | health_weight | 체중 입력 |
| healthAge | health_age | 나이 입력 |
| healthGender | health_gender | 성별 선택 |
| healthSleep | health_sleep | 수면시간 입력 |
| healthCheckButton | health_check_button | AI 분석 요청 |
| healthResultPanel | health_result_panel | AI 결과 출력 영역 |
| recommendedProductList | recommended_product_list | 추천 상품 목록 |
| healthResultSaveButton | health_result_save_button | 결과 DB 저장 |

## 관리자 ID

| ID | 변수명 예시 | 용도 |
|---|---|---|
| adminUserTable | admin_user_table | 회원관리 목록 |
| adminUserSearchInput | admin_user_search_input | 회원 검색 |
| adminProductTable | admin_product_table | 상품관리 목록 |
| adminProductSearchInput | admin_product_search_input | 상품 검색 |
| productCreateButton | product_create_button | 상품 추가 팝업 |
| stockEditButton | stock_edit_button | 재고 보충 팝업 |
| productSoldOutButton | product_sold_out_button | 상품 일시 품절 처리 |
| stockEditModal | stock_edit_modal | 판매·예약 재고 입력 |
| saleStockInput | sale_stock_input | 판매재고 입력 |
| reservationStockInput | reservation_stock_input | 예약재고 입력 |
| adminOrderTable | admin_order_table | 주문·배송 목록 |
| orderStatusFilter | order_status_filter | 주문 상태 필터 |
| deliveryCompleteButton | delivery_complete_button | 배송완료 처리 |
| shippingNotificationButton | shipping_notification_button | 배송 시작 알림 발송 |
| completionNotificationButton | completion_notification_button | 배송 완료 알림 발송 |
| adminReservationTable | admin_reservation_table | 예약자 목록 |
| adminInquiryTable | admin_inquiry_table | 문의관리 목록 |
| inquiryStatusFilter | inquiry_status_filter | 문의 상태 필터 |
| inquiryAnswerForm | inquiry_answer_form | 문의 답변 폼 |
| inquiryAnswer | inquiry_answer | 관리자 답변 내용 |

## 주요 CLASS

| CLASS | 용도 |
|---|---|
| container | 콘텐츠 최대 폭과 좌우 여백 |
| site-header, header-inner | 공통 sticky 헤더 |
| brand, brand-logo, brand-name | 로고 및 서비스명 |
| user-nav | 로그인·장바구니 사용자 메뉴 |
| drawer, drawer-panel | 햄버거 전체 메뉴 |
| site-footer, footer-grid | 공통 푸터 |
| floating-tools, floating-button | 챗봇·상단·하단 고정 도구 |
| page-section, page-heading, page-title | 페이지 공통 제목 영역 |
| button | 기본 버튼 |
| secondary, success, danger | 버튼 상태 변형 |
| card, panel | 카드형 콘텐츠 컨테이너 |
| form-grid, form-field, form-control | 입력 폼 배치 |
| table-wrap, data-table | 모바일 가로 스크롤 표 |
| badge | 주문·예약·문의 상태 표시 |
| modal, modal-dialog | 팝업 배경과 본문 |
| product-grid, product-card | 상품 목록 그리드 |
| product-toolbar, category-nav | 상품 검색·정렬·카테고리 |
| detail-grid, purchase-bar | 상품 상세와 모바일 구매 바 |
| cart-layout, cart-item | 장바구니 화면 |
| checkout-layout, sticky-summary | 주문서와 결제 요약 |
| mypage-layout, side-nav | 마이페이지 메뉴와 콘텐츠 |
| dashboard-cards, metric | 상태 요약 카드 |
| post-list, post-row | 공지사항 목록 |
| ai-layout, ai-result | AI 건강 체크 화면 |
| admin-header, admin-nav | 관리자 상단 메뉴 |
| admin-layout, admin-toolbar | 관리자 콘텐츠 영역 |
| split-view | 관리자 목록·상세 2단 배치 |

## 변수명 규칙

| 대상 | 규칙 | 예시 |
|---|---|---|
| HTML ID | camelCase | productSearchInput |
| CSS CLASS | kebab-case | product-search-box |
| JavaScript 변수·함수 | camelCase | loadProductList() |
| Python 변수·함수 | snake_case | load_product_list() |
| DB 컬럼 | snake_case | product_sale_stock |
| 상수 | UPPER_SNAKE_CASE | DEFAULT_PAGE_SIZE |
