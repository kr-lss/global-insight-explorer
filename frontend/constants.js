/**
 * 프론트엔드 상수 정의
 */

// Stance 타입 상수
export const STANCE_TYPES = {
  SUPPORTING: 'supporting',
  OPPOSING: 'opposing',
  NEUTRAL: 'neutral',
};

// Stance별 아이콘
export const STANCE_ICONS = {
  [STANCE_TYPES.SUPPORTING]: '✅',
  [STANCE_TYPES.OPPOSING]: '❌',
  [STANCE_TYPES.NEUTRAL]: '⚪',
};

// Stance별 라벨
export const STANCE_LABELS = {
  [STANCE_TYPES.SUPPORTING]: '지지',
  [STANCE_TYPES.OPPOSING]: '반대',
  [STANCE_TYPES.NEUTRAL]: '중립',
};

// Stance별 제목
export const STANCE_TITLES = {
  [STANCE_TYPES.SUPPORTING]: '✅ 이 주장을 지지하는 보도',
  [STANCE_TYPES.OPPOSING]: '❌ 이 주장에 반대하는 보도',
  [STANCE_TYPES.NEUTRAL]: '⚪ 중립적/사실 중심 보도',
};

// Credibility 등급
export const CREDIBILITY_LEVELS = {
  HIGH: { min: 80, label: '높은 신뢰도', class: 'high' },
  MEDIUM: { min: 60, max: 79, label: '중간 신뢰도', class: 'medium' },
  LOW: { max: 59, label: '낮은 신뢰도', class: 'low' },
};

// 기타 UI 상수
export const UI_CONSTANTS = {
  DEFAULT_CREDIBILITY: 50,
  CONFIDENCE_DECIMAL_PLACES: 0,
  DEFAULT_BIAS: 'N/A',
  DEFAULT_DATE: 'N/A',
};

// API 관련 상수
export const API_PATHS = {
  ANALYZE: '/api/analyze',
  FIND_SOURCES: '/api/find-sources',
  POPULAR: '/api/history/popular',
  RECENT: '/api/history/recent',
};
