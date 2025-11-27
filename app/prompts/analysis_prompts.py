"""
AI 분석을 위한 프롬프트 템플릿
"""


def get_first_analysis_prompt(content: str) -> str:
    """1차 분석 프롬프트: 핵심 주장 추출"""
    return f"""
다음 텍스트를 분석하여 JSON 형식으로 답변해주세요.

텍스트:
---
{content}
---

요구사항:
1. key_claims: 텍스트에서 언급된 핵심적인 주장이나 사실 (3-7개, 각각 명확하고 간결한 한 문장)
2. related_countries: 주된 관련 국가 (최대 5개, 국가 코드가 아닌 이름으로)
3. search_keywords: 각 주장을 검증하기 위한 영어 검색 키워드 (주장당 2-3개)
4. topics: 주제 분류 (예: 정치, 경제, 사회, 과학기술, 국제관계)
5. summary: 전체 내용을 요약 (2-3 문장)

응답 형식 (JSON):
{{
  "key_claims": ["주장 1", "주장 2"],
  "related_countries": ["국가1", "국가2"],
  "search_keywords": [["keyword1", "keyword2"], ["keyword3", "keyword4"]],
  "topics": ["주제1", "주제2"],
  "summary": "요약 내용"
}}

주의: 반드시 JSON 객체만 출력하고 다른 설명은 덧붙이지 마세요.
"""


def get_stance_analysis_prompt(
    original_content: str, claims: list, articles_text: str
) -> str:
    """2차 분석 프롬프트: 기사의 입장 분석"""
    claims_formatted = '\n'.join([f'- {c}' for c in claims])

    return f"""
당신은 편견 없는 정보 분석가입니다.
**각 기사가 선택한 주장에 대해 어떤 입장인지 분석해주세요.**

중요: 언론사의 "고정된 성향"이 아니라, "이 기사의 내용"만 기준으로 판단하세요.
- 같은 언론사도 이슈마다 다른 입장을 가질 수 있습니다.
- 절대로 사전에 정해진 라벨(보수/진보)을 사용하지 마세요.

[원본 콘텐츠 요약]
{original_content}

[사용자가 선택한 검증 대상 주장]
{claims_formatted}

[수집된 최신 기사 목록]
{articles_text}

[요청 작업]
각 기사에 대해 다음을 분석하세요:
1. 이 기사는 주장에 대해 어떤 입장인가?
   - supporting: 주장을 지지하거나 동의하는 내용
   - opposing: 주장에 반대하거나 부정하는 내용
   - neutral: 입장 없이 사실만 보도하거나 양쪽 입장 병기

2. 확신도 (0.0 ~ 1.0): 입장이 얼마나 명확한가?

3. 핵심 근거: 이 기사가 제시하는 구체적인 증거나 인용문 (1-2개)

4. 프레이밍: 이 기사가 사용하는 서술 방식이나 관점

[응답 형식 (JSON)]
{{
  "results": [
    {{
      "claim": "사용자가 선택한 첫 번째 주장",
      "article_analyses": [
        {{
          "article_index": 1,
          "stance": "supporting",
          "confidence": 0.85,
          "key_evidence": [
            "첫 번째 핵심 증거나 인용문",
            "두 번째 핵심 증거나 인용문"
          ],
          "framing": "이 기사가 사용하는 프레임 설명"
        }},
        {{
          "article_index": 2,
          "stance": "opposing",
          "confidence": 0.80,
          "key_evidence": [
            "첫 번째 핵심 증거나 인용문",
            "두 번째 핵심 증거나 인용문"
          ],
          "framing": "이 기사가 사용하는 프레임 설명"
        }},
        {{
          "article_index": 3,
          "stance": "neutral",
          "confidence": 0.70,
          "key_evidence": [
            "첫 번째 핵심 증거나 인용문",
            "두 번째 핵심 증거나 인용문"
          ],
          "framing": "이 기사가 사용하는 프레임 설명"
        }}
      ],
      "stance_summary": {{
        "supporting_count": 0,
        "opposing_count": 0,
        "neutral_count": 0,
        "common_supporting_arguments": [
          "지지 입장의 공통 논거",
          "또 다른 공통 논거"
        ],
        "common_opposing_arguments": [
          "반대 입장의 공통 논거",
          "또 다른 공통 논거"
        ]
      }}
    }}
  ]
}}

[주의사항]
- 절대로 주장의 참/거짓을 판단하지 마세요.
- 오직 "이 기사의 내용"을 기준으로 입장을 분석하세요.
- 언론사 이름으로 입장을 추측하지 마세요.
- 반드시 JSON 객체만 출력하고 다른 설명은 덧붙이지 마세요.
"""


def get_article_search_prompt(query: str) -> str:
    """기사 검색 프롬프트: Google Search Grounding 사용"""
    return f"""
다음 키워드와 관련된 최신 뉴스 기사를 검색하고, 각 기사에 대해 다음 정보를 JSON 배열로 반환해주세요:
- title: 기사 제목
- snippet: 기사 요약 (2-3문장)
- url: 기사 URL
- source: 언론사명
- published_date: 발행일 (YYYY-MM-DD 형식)

키워드: {query}

응답 형식:
{{"articles": [...]}}
"""


# 검색 쿼리 최적화 프롬프트
QUERY_OPTIMIZATION_PROMPT = """
You are a GDELT (Global Database of Events, Language, and Tone) Search Optimization Expert.
Your mission is to convert user questions into highly optimized search keywords that maximize article discovery.

[CRITICAL: GDELT URL Structure Understanding]
GDELT searches news article URLs (DocumentIdentifier), which typically follow this pattern:
- Example: ".../south-korea-china-trade-benefits-2024..."
- URLs contain hyphenated keywords from article titles
- Abstract words like "policy", "economy" rarely appear in URLs
- Country names and specific events DO appear in URLs

User's Input: "{user_input}"

Context (Content being analyzed):
- Title: "{context_title}"
- Related Claims: {context_claims}

[Task Steps]
1. **Intent Analysis**: Understand what the user wants to know
   - If vague (e.g., "is this true?"), infer from context
   - Identify issue type: Single country event OR Multi-country conflict

2. **Target Countries**: Select 3-5 relevant country codes (ISO alpha-2)
   - Primary stakeholders (parties directly involved)
   - Secondary stakeholders (neighbors, affected countries, beneficiaries)

3. **OPTIMIZED Keyword Generation Rules** ⭐ MOST IMPORTANT ⭐

   [Rule A: Country Name Injection - MANDATORY]
   - EVERY keyword MUST include a country name or location
   - Bad ❌: "trade war", "economic sanctions"
   - Good ✅: "China Japan trade war", "US sanctions impact"

   [Rule B: Composite Phrases - 2 to 4 words]
   - Use news headline style phrases
   - Bad ❌: "trade" (too short), "economic policy response analysis" (too long)
   - Good ✅: "export controls", "tariff dispute", "supply chain shift"

   [Rule C: Specific Events over Abstract Concepts]
   - Use concrete actions, not abstract nouns
   - Bad ❌: "policy", "development", "situation"
   - Good ✅: "visa restriction", "import ban", "factory relocation"

   [Rule D: URL-Friendly Terms]
   - Think: "Would this appear in a news article URL?"
   - Bad ❌: "econ trade" (abbreviation), "INTL relations" (code)
   - Good ✅: "trade agreement", "diplomatic relations"

   [Rule E: Timely Language]
   - For recent events, include recency indicators
   - Good ✅: "2024 tariff increase", "latest trade data", "ongoing dispute"

4. **English Keywords (Primary)**: Generate 5-7 keywords
   - First 2-3: "{Country Name} + {Main Topic}"
   - Example: "South Korea export opportunity", "Vietnam supply chain alternative"
   - Next 2-3: Specific events or impacts
   - Example: "semiconductor export ban", "rare earth restrictions"
   - Last 1-2: Broader context
   - Example: "trade war beneficiaries", "economic decoupling"

5. **Korean Keywords (Secondary)**: 3-5 keywords for local coverage
   - Use natural Korean phrases that would appear in Korean news
   - Example: "한국 수출 기회", "베트남 공급망 이전"

6. **Confidence Score**: 0.0 to 1.0
   - High (>0.8): Clear, specific question with identifiable countries
   - Medium (0.5-0.8): Somewhat vague but context helps
   - Low (<0.5): Gibberish or completely unclear

[Output Format - JSON ONLY]
{{
    "interpreted_intent": "What the user wants to know (1 sentence in English)",
    "search_keywords_en": [
        "Country1 main topic keyword",
        "Country2 specific event",
        "concrete action phrase",
        "impact or outcome phrase",
        "broader context keyword"
    ],
    "search_keywords_kr": [
        "국가명 포함 키워드1",
        "구체적 사건 키워드2",
        "영향 키워드3"
    ],
    "target_country_codes": ["KR", "CN", "JP", "VN", "US"],
    "confidence": 0.95
}}

[Examples]

Input: "중국과 일본이 경제 보복을 한다는데 반사이익을 보는 나라는?"
Output:
{{
    "interpreted_intent": "Identify countries benefiting from China-Japan economic retaliation",
    "search_keywords_en": [
        "South Korea China Japan trade",
        "Vietnam supply chain alternative",
        "Korea export opportunity",
        "semiconductor production shift",
        "trade war beneficiaries Asia"
    ],
    "search_keywords_kr": [
        "한국 중일 무역분쟁 수혜",
        "베트남 공급망 대체",
        "반도체 생산 이전"
    ],
    "target_country_codes": ["KR", "VN", "TH", "IN", "MX"],
    "confidence": 0.92
}}

Input: "Is Biden's chip policy working?"
Output:
{{
    "interpreted_intent": "Evaluate effectiveness of Biden's semiconductor policy",
    "search_keywords_en": [
        "Biden CHIPS Act impact",
        "US semiconductor manufacturing",
        "Intel TSMC factory investment",
        "China chip export controls",
        "American chip industry revival"
    ],
    "search_keywords_kr": [
        "바이든 반도체 정책 효과",
        "미국 칩 제조 부활"
    ],
    "target_country_codes": ["US", "CN", "KR", "TW"],
    "confidence": 0.88
}}

CRITICAL REMINDER: Your keywords will be used to search GDELT URLs. Make them concrete, specific, and URL-friendly!
"""
