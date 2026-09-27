# hanjiyoung-discord

한지영(키움증권) 텔레그램 채널(`t.me/hedgecat0301`) 새 글을 감지해서
**디스코드**로 알림을 보내고, 저녁 코스피 리포트가 참조할 수 있도록
`reports/hanjiyoung/YYYY-MM-DD.md`에 글 전문을 저장하는 저장소.

기존 `hanjiyoung-alert`(카카오톡 버전)와는 완전히 별개로 동작하며, 서로 영향을 주지 않는다.

## 1. 디스코드 웹훅 URL 만들기

1. 디스코드에서 알림을 받을 서버/채널을 정한다 (없으면 서버 하나 새로 만들어도 됨).
2. 채널 이름 옆 톱니바퀴(채널 설정) → **연동(Integrations)** → **웹후크(Webhooks)** → **새 웹후크(New Webhook)**.
3. 이름을 원하는 대로 정하고 **웹후크 URL 복사**를 누른다.
4. 이 URL은 카카오 REST API 키처럼 **민감정보로 취급**한다 (남에게 노출되면 그 사람도 이 채널에 메시지를 보낼 수 있음).

## 2. GitHub 저장소 만들기

1. GitHub에서 새 저장소 생성: 이름 `hanjiyoung-discord`, **Public**으로 설정 (민감정보가 코드에 없으므로 안전).
2. 이 폴더의 파일들을 그대로 올린다:
   - `check_and_notify.py`
   - `requirements.txt`
   - `.github/workflows/check.yml` (`.github` 폴더는 Finder에서 숨김 폴더라 드래그 업로드 시 빠질 수 있음 — GitHub 웹에서 "Add file → Create new file"로 경로를 `.github/workflows/check.yml`라고 직접 타이핑해서 만드는 게 안전)

## 3. GitHub Secret 등록

저장소 **Settings → Secrets and variables → Actions → New repository secret**

- Name: `DISCORD_WEBHOOK_URL`
- Value: 1단계에서 복사한 웹훅 URL

## 4. 수동 실행으로 테스트

**Actions** 탭 → 왼쪽에서 워크플로 선택 → **Run workflow** 버튼으로 수동 실행.
디스코드 채널에 알림이 오는지, `reports/hanjiyoung/오늘날짜.md` 파일이 생기는지 확인한다.

## 5. 저녁 리포트에서 참조하기

저장소가 Public이므로 아래 형태의 raw URL로 오늘 글을 바로 읽을 수 있다:

```
https://raw.githubusercontent.com/<사용자명>/hanjiyoung-discord/main/reports/hanjiyoung/{오늘날짜}.md
```

저녁 Cowork 예약 작업 프롬프트에서 이 URL을 읽도록 지정하면,
텔레그램에 직접 접속해서 글 번호를 추정하는 불안정한 방식 대신
**이미 확보된 정적 파일을 읽는 것**이라 실패할 일이 거의 없다.

## 동작 스케줄

- KST 07:02~09:57, 5분 간격 (아침 — 한지영이 보통 이 시간에 글을 올림)
- KST 19:03~20:53, 10분 간격 (저녁 — 혹시 있을 추가 글 대비)
- 두 스케줄 모두 새 글이 없으면 아무 것도 하지 않고 조용히 끝남
