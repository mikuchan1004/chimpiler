# CHIMPILER HEALTHCARE UI

PC/Mobile 스토리보드를 기준으로 만든 정적 HTML/CSS 화면입니다. Jinja, JavaScript, FastAPI 기능은 포함하지 않았으며 팀에서 연결할 수 있도록 주요 조작 요소에 ID를 지정했습니다.

## 폴더 구조

```text
chimpiler-ui/
├─ templates/
│  └─ layout.html
├─ static/
│  ├─ css/
│  │  ├─ common.css
│  │  ├─ components.css
│  │  ├─ pages.css
│  │  └─ responsive.css
│  └─ images/
│     ├─ chimpiler-logo.png
│     └─ 상품 이미지 60개
├─ main.html
├─ products.html
├─ product-detail.html
├─ cart.html
├─ checkout.html
├─ payment-result.html
├─ login.html
├─ signup.html
├─ terms.html
├─ mypage-dashboard.html
├─ mypage-profile.html
├─ mypage-orders.html
├─ mypage-reservations.html
├─ mypage-inquiries.html
├─ ai-health.html
├─ notice.html
├─ faq.html
├─ inquiry-write.html
├─ admin-dashboard.html
├─ admin-users.html
├─ admin-products.html
├─ admin-orders.html
├─ admin-reservations.html
├─ admin-inquiries.html
├─ error-404.html
├─ products.csv
├─ IMPLEMENTATION_NOTES.md
└─ NAMING_REFERENCE.md
```

## CSS 역할

| 파일 | 역할 |
|---|---|
| common.css | 컬러, 글꼴, 공통 레이아웃, 헤더, 푸터, 메뉴, 고정 버튼 |
| components.css | 버튼, 입력창, 테이블, 탭, 모달, 상태 배지 |
| pages.css | 상품, 주문, 회원, 마이페이지, 커뮤니티, AI, 관리자 화면 |
| responsive.css | 태블릿 및 모바일 반응형 배치 |

CSS 수정은 역할에 맞는 파일 한 곳에서 진행하면 같은 컴포넌트를 사용하는 모든 페이지에 반영됩니다.

## Jinja 적용 시

`templates/layout.html`의 `mainContent` 내부를 `{% block main %}{% endblock %}`으로 바꾸고, 각 페이지에서 `{% extends "layout.html" %}`를 사용하면 됩니다. 현재 HTML은 브라우저에서 바로 확인할 수 있도록 정적 경로를 사용했습니다.
