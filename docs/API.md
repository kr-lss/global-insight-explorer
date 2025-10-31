# API Documentation

## Base URL

```
http://localhost:8080
```

## Endpoints

### 1. Health Check

서버 상태 확인

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "media_database_size": 19
}
```

---

### 2. Content Analysis (1차 분석)

URL에서 콘텐츠를 추출하고 핵심 주장을 분석합니다.

**Endpoint:** `POST /api/analyze`

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=example",
  "inputType": "youtube"
}
```

**Parameters:**
- `url` (required): 분석할 콘텐츠의 URL
- `inputType` (optional): 콘텐츠 타입 (`youtube` 또는 `article`, 기본값: `youtube`)

**Response:**
```json
{
  "success": true,
  "cached": false,
  "analysis": {
    "key_claims": [
      "주장 1",
      "주장 2",
      "주장 3"
    ],
    "related_countries": ["미국", "한국"],
    "search_keywords": [
      ["keyword1", "keyword2"],
      ["keyword3", "keyword4"]
    ],
    "topics": ["정치", "경제"],
    "summary": "콘텐츠 요약 내용..."
  }
}
```

---

### 3. Find Related Sources (2차 분석)

선택된 주장에 대한 관련 기사를 검색하고 분석합니다.

**Endpoint:** `POST /api/find-sources`

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=example",
  "inputType": "youtube",
  "selected_claims": ["주장 1", "주장 2"],
  "search_keywords": ["keyword1", "keyword2", "keyword3"]
}
```

**Parameters:**
- `url` (required): 원본 콘텐츠 URL
- `inputType` (optional): 콘텐츠 타입
- `selected_claims` (required): 검증할 주장 목록
- `search_keywords` (optional): 검색 키워드

**Response:**
```json
{
  "success": true,
  "articles_count": 15,
  "articles": [
    {
      "title": "기사 제목",
      "snippet": "기사 요약...",
      "url": "https://example.com/article",
      "source": "BBC",
      "country": "UK",
      "credibility": 92,
      "bias": "중립",
      "published_date": "2024-01-01"
    }
  ],
  "result": {
    "results": [
      {
        "claim": "주장 1",
        "related_articles": [
          {
            "article_index": 1,
            "relevance_score": 90,
            "perspective": "이 기사는..."
          }
        ],
        "missing_context": "추가 맥락 정보...",
        "coverage_countries": ["미국", "영국"]
      }
    ]
  }
}
```

---

### 4. Get Media Credibility List

전체 언론사 신뢰도 목록을 반환합니다.

**Endpoint:** `GET /api/media-credibility`

**Response:**
```json
{
  "BBC": {
    "credibility": 92,
    "bias": "중립",
    "country": "UK"
  },
  "CNN": {
    "credibility": 75,
    "bias": "중도좌파",
    "country": "US"
  }
}
```

---

### 5. Get Specific Media Credibility

특정 언론사의 신뢰도 정보를 조회합니다.

**Endpoint:** `GET /api/media-credibility/<source>`

**Example:** `GET /api/media-credibility/BBC`

**Response:**
```json
{
  "source": "BBC",
  "credibility": 92,
  "bias": "중립",
  "country": "UK"
}
```

---

## Error Responses

모든 엔드포인트는 오류 발생 시 다음 형식으로 응답합니다:

```json
{
  "error": "오류 메시지"
}
```

**Common HTTP Status Codes:**
- `200 OK`: 성공
- `400 Bad Request`: 잘못된 요청 (필수 파라미터 누락 등)
- `500 Internal Server Error`: 서버 내부 오류
