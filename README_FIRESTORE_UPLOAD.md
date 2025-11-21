# Firestore 언론사 데이터 업로드 가이드

## 📁 파일 구조

```
data/
  └─ media_countries.json         # 언론사 데이터 (JSON 형식)
scripts/
  └─ upload_media_to_firestore.py # Firestore 업로드 스크립트
```

---

## 🚀 사용 방법

### 1️⃣ 데이터 추가/수정

`data/media_countries.json` 파일을 편집하여 국가 추가:

```json
{
  "NL": {
    "name": "네덜란드",
    "broadcasting": [
      {"name": "NOS (NPO)", "type": "공영"},
      {"name": "RTL Nederland", "type": "민영"}
    ],
    "newspapers": [
      {"name": "De Telegraaf", "type": "민영"},
      {"name": "NRC Handelsblad", "type": "민영"}
    ]
  }
}
```

### 2️⃣ Firestore에 업로드

```bash
# GCP 인증 (최초 1회)
gcloud auth application-default login

# 데이터 업로드
python scripts/upload_media_to_firestore.py
```

### 3️⃣ 기존 데이터 삭제 (필요 시)

```bash
python scripts/upload_media_to_firestore.py --delete
```

---

## 📊 Firestore 구조

```
Collection: countries
  Document: US
    - name: "미국"
    - broadcasting: [{name: "PBS", type: "공영"}, ...]
    - newspapers: [{name: "NYT", type: "민영"}, ...]

  Document: KR
    - name: "대한민국"
    - broadcasting: [{name: "KBS", type: "공영"}, ...]
    - newspapers: [{name: "조선일보", type: "민영"}, ...]
```

---


## 💡 주의사항

1. **JSON 형식 검증**: 업로드 전에 JSON 유효성 확인
   ```bash
   python -m json.tool data/media_countries.json
   ```

2. **GCP 프로젝트 설정**: `.env` 파일에 프로젝트 ID 확인
   ```
   GCP_PROJECT=your-project-id
   ```

3. **Firestore 권한**: 읽기/쓰기 권한 필요

---

## 🔄 업로드 후 확인

스크립트 실행 시 자동으로 확인되지만, Firebase Console에서도 확인 가능:

https://console.firebase.google.com/project/[YOUR_PROJECT]/firestore

---

## 🛠️ 문제 해결

### "Firestore 연결 실패"
```bash
# GCP 인증 재설정
gcloud auth application-default login
```

### "JSON 파싱 오류"
```bash
# JSON 형식 확인
python -m json.tool data/media_countries.json
```

### "권한 오류"
- Firebase Console에서 Firestore 활성화 확인
- GCP IAM에서 Firestore 권한 확인
