/**
 * API 호출 로직 (ES Module)
 */

import { API_ENDPOINTS } from './constants.js';
import { getApiBaseUrl } from './utils.js';

const API_BASE_URL = getApiBaseUrl();

/**
 * 1차 분석: 콘텐츠 분석 및 주장 추출
 * @param {string} url - 분석할 URL
 * @param {string} inputType - 입력 타입 ('youtube' 또는 'article')
 * @returns {Promise<Object>} 분석 결과
 * @throws {Error} API 요청 실패 시
 */
export async function analyzeContent(url, inputType) {
  const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.ANALYZE}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, inputType }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || '분석 실패');
  }

  const data = await response.json();

  if (!data.success) {
    throw new Error(data.error || '분석 실패');
  }

  return data.analysis;
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
 * @throws {Error} API 요청 실패 시
 */
export async function findSources(url, inputType, claimsData) {
  const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.FIND_SOURCES}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      url,
      inputType,
      claims_data: claimsData,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || '기사 검색 실패');
  }

  const data = await response.json();

  if (!data.success) {
    throw new Error(data.error || '기사 검색 실패');
  }

  return {
    result: data.result,
    articles: data.articles,
  };
}

/**
 * 인기 콘텐츠 로드
 * @param {number} limit - 가져올 개수 (기본값: 10)
 * @param {number} days - 기간 (기본값: 7일)
 * @returns {Promise<Array>} 인기 콘텐츠 목록
 * @throws {Error} API 요청 실패 시
 */
export async function loadPopularContent(limit = 10, days = 7) {
  const response = await fetch(
    `${API_BASE_URL}${API_ENDPOINTS.POPULAR}?limit=${limit}&days=${days}`
  );

  const data = await response.json();

  if (!data.success || data.count === 0) {
    return [];
  }

  return data.data;
}

/**
 * 최근 분석 히스토리 로드
 * @param {number} limit - 가져올 개수 (기본값: 20)
 * @returns {Promise<Array>} 최근 분석 목록
 * @throws {Error} API 요청 실패 시
 */
export async function loadRecentHistory(limit = 20) {
  const response = await fetch(
    `${API_BASE_URL}${API_ENDPOINTS.RECENT}?limit=${limit}`
  );

  const data = await response.json();

  if (!data.success || data.count === 0) {
    return [];
  }

  return data.data;
}
