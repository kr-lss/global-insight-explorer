/**
 * 애플리케이션 환경 설정 (ES Module)
 *
 * 환경별 설정을 중앙에서 관리합니다.
 * 배포 시 이 파일만 수정하면 전체 설정이 변경됩니다.
 */

/**
 * 현재 환경 감지
 */
const isDevelopment = () => {
  const hostname = window.location.hostname;
  return hostname === 'localhost' || hostname === '127.0.0.1';
};

/**
 * 환경별 설정
 */
const ENVIRONMENT = {
  development: {
    API_BASE_URL: 'http://127.0.0.1:8080',
    TIMEOUT_MS: 120000, // 2분 (개발 시 디버깅용)
    ENABLE_LOGGING: true,
  },
  production: {
    API_BASE_URL: `${window.location.protocol}//${window.location.hostname}${window.location.port ? ':' + window.location.port : ''}`,
    TIMEOUT_MS: 60000, // 1분
    ENABLE_LOGGING: false,
  },
};

/**
 * 현재 활성 설정
 */
const activeConfig = isDevelopment()
  ? ENVIRONMENT.development
  : ENVIRONMENT.production;

/**
 * Export: 애플리케이션 설정
 */
export const CONFIG = {
  // API 설정
  API_BASE_URL: activeConfig.API_BASE_URL,
  API_TIMEOUT_MS: activeConfig.TIMEOUT_MS,

  // 기능 플래그 (Feature Flags)
  ENABLE_LOGGING: activeConfig.ENABLE_LOGGING,
  ENABLE_ANALYTICS: false, // 추후 Google Analytics 등 추가 시

  // UI 설정
  MAX_RETRY_ATTEMPTS: 3,
  ERROR_DISPLAY_TIME: 5000, // ms

  // 개발 환경 여부
  IS_DEV: isDevelopment(),
};

/**
 * 로깅 유틸리티 (개발 환경에서만 동작)
 */
export const logger = {
  log: (...args) => {
    if (CONFIG.ENABLE_LOGGING) {
      console.log('[App]', ...args);
    }
  },
  error: (...args) => {
    if (CONFIG.ENABLE_LOGGING) {
      console.error('[App Error]', ...args);
    }
  },
  warn: (...args) => {
    if (CONFIG.ENABLE_LOGGING) {
      console.warn('[App Warning]', ...args);
    }
  },
};
