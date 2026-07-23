# 🗺️ TripFit AI (무장애 & 맞춤형 여행 코스 추천 AI 서버 API)

> **공공 데이터**와 **Google Gemini AI**를 결합하여 반려동물, 휠체어, 영유아, 고령자 등 **이용자 유형별 맞춤형 무장애 여행 코스**를 생성해 주는 Fast API/Python 기반 비동기 AI 서버입니다.

---

## 💡 Key Features (주요 기능)

- **🎯 이동 약자 맞춤형 필터링**: PET(반려동물), WHEELCHAIR(휠체어), BABY(영유아), ELDERLY(고령자) 맞춤 AI 코스 데이터 정제
- **⚡ Async Connection Pooling**: 공공 데이터 상세 조회 API로 수집할 데이터 `httpx.AsyncClient` + `asyncio.gather`로 병렬 처리
- **🤖 Gemini LLM**: 동반자 유형 맞춤 필터링 데이터를 기반으로 동선이 최적화된 일자별 여행 코스 자동 생성
- **📡 SSE (Server-Sent Events) Real-time Logging**: AI 분석 및 코스 생성 과정을 클라이언트에 실시간 스트리밍 로그로 전달

---

## 🛠️ Tech Stack (기술 스택)

| Category | Technologies |
| --- | --- |
| **Framework** | FastAPI, Python 3.13 |
| **Asynchronous & HTTP** | Asyncio, HTTPX |
| **AI / LLM** | Google Gemini API (Prompt Engineering) |
| **External API** | 한국관광공사 TourAPI (국문 관광정보 & 반려동물 동반 여행정보 & 무장애 여행정보) |

---
<!--
## 🏗️ System Architecture & Workflow (시스템 흐름)

```text
[Client] ──(SSE Request)──> [FastAPI Server]
                               │
                               ├── 1️⃣ Async TourAPI Data Collection (HTTPX Pool)
                               ├── 2️⃣ Barrier-Free Data Filtering & Clean-up
                               ├── 3️⃣ Gemini AI Course Optimization Prompting
                               └── 4️⃣ Stream Status Logs & Final Structured JSON Output
 -->
