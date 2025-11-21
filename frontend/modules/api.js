/**
 * API 호출 로직 (ES Module)
 *
 * 표준화된 에러 핸들링과 타임아웃 처리를 제공합니다.
 */

import { API_ENDPOINTS } from './constants.js';
import { CONFIG, logger } from './config.js';

/**
 * API 에러 클래스 (표준화된 에러 객체)
 */
class ApiError extends Error {
  constructor(message, statusCode, originalError) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.originalError = originalError;
    this.timestamp = new Date().toISOString();
  }
}

/**
 * 타임아웃 처리를 포함한 fetch 래퍼
 * @param {string} url - 요청 URL
 * @param {Object} options - fetch 옵션
 * @param {number} timeout - 타임아웃 시간 (ms)
 * @returns {Promise<Response>}
 */
async function fetchWithTimeout(url, options = {}, timeout = CONFIG.API_TIMEOUT_MS) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new ApiError('요청 시간이 초과되었습니다', 408, error);
    }
    throw error;
  }
}

/**
 * API 응답 처리 및 에러 핸들링 (공통 로직)
 * @param {Response} response - fetch 응답
 * @param {string} defaultErrorMessage - 기본 에러 메시지
 * @returns {Promise<Object>} 파싱된 JSON 데이터
 * @throws {ApiError} API 요청 실패 시
 */
async function handleApiResponse(response, defaultErrorMessage) {
  // HTTP 에러 처리
  if (!response.ok) {
    let errorMessage = defaultErrorMessage;
    let errorData = null;

    try {
      errorData = await response.json();
      errorMessage = errorData.error || errorData.message || defaultErrorMessage;
    } catch (parseError) {
      // JSON 파싱 실패 시 기본 메시지 사용
      logger.warn('Failed to parse error response:', parseError);
    }

    throw new ApiError(
      errorMessage,
      response.status,
      errorData
    );
  }

  // JSON 파싱
  try {
    const data = await response.json();

    // 백엔드 success 플래그 확인
    if (data.success === false) {
      throw new ApiError(
        data.error || defaultErrorMessage,
        response.status,
        data
      );
    }

    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError('응답 데이터를 처리할 수 없습니다', 500, error);
  }
}

/**
 * API 호출 공통 래퍼 (에러 핸들링 포함)
 * @param {Function} apiCall - API 호출 함수
 * @returns {Promise<any>} API 응답 데이터
 */
async function withErrorHandling(apiCall) {
  try {
    return await apiCall();
  } catch (error) {
    // ApiError는 그대로 throw
    if (error instanceof ApiError) {
      logger.error('API Error:', error.message, error);
      throw error;
    }

    // 네트워크 에러 등 기타 에러 처리
    if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
      throw new ApiError('네트워크 연결을 확인해주세요', 0, error);
    }

    // 알 수 없는 에러
    logger.error('Unexpected error:', error);
    throw new ApiError('알 수 없는 오류가 발생했습니다', 500, error);
  }
}

/**
 * 1차 분석: 콘텐츠 분석 및 주장 추출
 * @param {string} url - 분석할 URL
 * @param {string} inputType - 입력 타입 ('youtube' 또는 'article')
 * @returns {Promise<Object>} 분석 결과
 * @throws {ApiError} API 요청 실패 시
 */
export async function analyzeContent(url, inputType) {
  return withErrorHandling(async () => {
    logger.log('Analyzing content:', url, inputType);

    const response = await fetchWithTimeout(
      `${CONFIG.API_BASE_URL}${API_ENDPOINTS.ANALYZE}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, inputType }),
      }
    );

    const data = await handleApiResponse(response, '분석 실패');
    return data.analysis;
  });
}

/**
 * 2차 분석: 선택된 주장에 대한 다양한 관점 찾기
 * @param {string} url - 원본 콘텐츠 URL
 * @param {string} inputType - 입력 타입 ('youtube' 또는 'article')
 * @param {Array<Object>} claimsData - 주장 데이터 배열
 *   [
 *     {
 *       claim_kr: "한국어 주장",
 *       search_keywords_en: ["keyword1", "keyword2"],
 *       target_country_codes: ["US", "CN"]
 *     },
 *     ...
 *   ]
 * @returns {Promise<Object>} { result: 분석 결과, articles: 기사 목록 }
 * @throws {ApiError} API 요청 실패 시
 */
export async function findSources(url, inputType, claimsData) {
  return withErrorHandling(async () => {
    logger.log('Finding sources for claims:', claimsData.length, 'claims');

    const response = await fetchWithTimeout(
      `${CONFIG.API_BASE_URL}${API_ENDPOINTS.FIND_SOURCES}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url,
          inputType,
          claims_data: claimsData,
        }),
      }
    );

    const data = await handleApiResponse(response, '기사 검색 실패');

    return {
      result: data.result,
      articles: data.articles,
    };
  });
}

/**
 * 인기 콘텐츠 로드
 * @param {number} limit - 가져올 개수 (기본값: 10)
 * @param {number} days - 기간 (기본값: 7일)
 * @returns {Promise<Array>} 인기 콘텐츠 목록
 * @throws {ApiError} API 요청 실패 시
 */
export async function loadPopularContent(limit = 10, days = 7) {
  return withErrorHandling(async () => {
    logger.log('Loading popular content:', limit, 'items,', days, 'days');

    const response = await fetchWithTimeout(
      `${CONFIG.API_BASE_URL}${API_ENDPOINTS.POPULAR}?limit=${limit}&days=${days}`
    );

    const data = await handleApiResponse(response, '인기 콘텐츠 로드 실패');

    if (!data.success || data.count === 0) {
      return [];
    }

    return data.data;
  });
}

/**
 * 최근 분석 히스토리 로드
 * @param {number} limit - 가져올 개수 (기본값: 20)
 * @returns {Promise<Array>} 최근 분석 목록
 * @throws {ApiError} API 요청 실패 시
 */
export async function loadRecentHistory(limit = 20) {
  return withErrorHandling(async () => {
    logger.log('Loading recent history:', limit, 'items');

    const response = await fetchWithTimeout(
      `${CONFIG.API_BASE_URL}${API_ENDPOINTS.RECENT}?limit=${limit}`
    );

    const data = await handleApiResponse(response, '최근 분석 로드 실패');

    if (!data.success || data.count === 0) {
      return [];
    }

    return data.data;
  });
}
