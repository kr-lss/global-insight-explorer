/**
 * 프론트엔드 상수 정의 (ES Module)
 */

// API 엔드포인트
export const API_ENDPOINTS = {
  ANALYZE: '/api/analyze',
  FIND_SOURCES: '/api/find-sources',
  POPULAR: '/api/history/popular',
  RECENT: '/api/history/recent',
};

// Stance 타입 상수
export const STANCE = {
  SUPPORTING: 'supporting',
  OPPOSING: 'opposing',
  NEUTRAL: 'neutral',
};

// Stance별 UI 설정
export const STANCE_CONFIG = {
  [STANCE.SUPPORTING]: {
    icon: '✅',
    label: '지지',
    title: '✅ 이 주장을 지지하는 보도',
    colorClass: 'stance-supporting',
  },
  [STANCE.OPPOSING]: {
    icon: '❌',
    label: '반대',
    title: '❌ 이 주장에 반대하는 보도',
    colorClass: 'stance-opposing',
  },
  [STANCE.NEUTRAL]: {
    icon: '⚪',
    label: '중립',
    title: '⚪ 중립적/사실 중심 보도',
    colorClass: 'stance-neutral',
  },
};

// 국가 플래그 매핑
export const COUNTRY_FLAGS = {
  'KR': '🇰🇷',
  'US': '🇺🇸',
  'UK': '🇬🇧',
  'GB': '🇬🇧',
  'JP': '🇯🇵',
  'CN': '🇨🇳',
  'DE': '🇩🇪',
  'FR': '🇫🇷',
  'QA': '🇶🇦',
  'RU': '🇷🇺',
  'IN': '🇮🇳',
  'BR': '🇧🇷',
  'CA': '🇨🇦',
  'AU': '🇦🇺',
  'IT': '🇮🇹',
  'ES': '🇪🇸',
};

// UI 기본값
export const UI_DEFAULTS = {
  CONFIDENCE_DECIMALS: 0,
  BIAS: 'N/A',
  DATE: 'N/A',
  LOADING_MESSAGE: '분석 중입니다...',
  ERROR_DISPLAY_TIME: 5000, // ms
};

// 메시지 상수
export const MESSAGES = {
  ERROR: {
    NO_URL: 'URL을 입력해주세요',
    INVALID_URL: '올바른 URL 형식이 아닙니다',
    NO_CLAIMS: '위의 주장을 선택하거나, 직접 주장을 입력해주세요',
    ANALYSIS_FAILED: '분석 실패',
    SEARCH_FAILED: '기사 검색 실패',
  },
  LOADING: {
    ANALYZING: '주장을 분석하고 있습니다...',
    SEARCHING: '다양한 관점의 출처를 찾고 있습니다...',
  },
};
