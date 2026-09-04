# JS·Python 연동 메모

현재 HTML/CSS에는 화면과 조작 요소까지 구성되어 있습니다. 아래 항목은 팀 코드에서 실제 동작을 연결해야 합니다.

| 화면·기능 | HTML ID | JavaScript 역할 | Python/API 역할 |
|---|---|---|---|
| 장바구니 전체 선택 | `cartSelectAll` | 모든 `.cart-checkbox` 선택·해제 및 금액 재계산 | 선택 상태 전송 시 주문 대상 검증 |
| 장바구니 선택 삭제 | `cartSelectedDeleteButton` | 선택된 장바구니 ID 수집, 삭제 확인 | `cart` 데이터 삭제 후 합계 반환 |
| 환불 요청 | `refundRequestButton` | 환불 사유 팝업과 확인 처리 | 주문·결제 상태 및 환불 가능 여부 검증 후 상태 변경 |
| 예약 우선순위 확인 | `reservationPriorityButton` | 조회 결과 팝업 출력 | 같은 상품의 유효 예약을 날짜순으로 계산해 현재 순위 반환 |
| 예약 취소 | `reservationCancelButton` | 취소 확인 및 화면 갱신 | 예약 상태 변경, 배정된 예약재고가 있으면 재고 복원 |
| 문의 삭제 | `inquiryDeleteButton` | 삭제 확인 | 본인 문의인지 확인한 후 삭제 또는 비활성 처리 |
| AI 결과 주문 | `recommendedCheckoutButton` | 선택한 추천 상품을 주문서로 전달 | 상품·재고 검증 후 주문서 데이터 구성 |
| 전문가 상담 | `expertConsultButton` | 상담 또는 문의 화면으로 이동 | 필요 시 상담 가능 기관·문의 데이터 조회 |
| 공지사항 상세 | HTML `details` 사용 | 기본 열기/닫기는 JS 불필요, API 적용 시 목록 렌더링 | 공지 목록과 상세 내용 조회 |
| 일시 품절 | `productSoldOutButton` | 처리 확인과 상태 표시 변경 | 상품 판매 상태 변경 및 판매 버튼 비활성화 |
| 배송 알림 | `shippingNotificationButton` | 발송 확인과 완료 메시지 | 해당 회원에게 배송 시작 알림 저장·발송 |
| 완료 알림 | `completionNotificationButton` | 발송 확인과 완료 메시지 | 배송완료 상태 확인 후 완료 알림 저장·발송 |
| 메인 베스트 이동 | `bestProductPrevious`, `bestProductNext` | 표시할 상품 인덱스 변경 | 필요 시 인기 상품 목록 조회 |
| 메인 랜덤 상품 | `randomProductRefresh` | 다시 불러오기 및 카드 교체 | 판매 가능한 상품 중 중복 없이 무작위 조회 |

## 처리 시 주의사항

- 환불 버튼은 결제완료 상태이면서 환불 가능한 주문에만 표시합니다.
- 문의 삭제는 답변 여부에 따라 정책을 정합니다. 기록 보존이 필요하면 실제 삭제 대신 삭제 상태를 사용합니다.
- 배송 알림은 버튼을 여러 번 눌러 중복 발송되지 않도록 발송 여부를 저장하는 편이 안전합니다.
- 재고·예약 취소·환불 처리는 동시에 실행될 수 있으므로 데이터베이스 트랜잭션으로 묶습니다.
