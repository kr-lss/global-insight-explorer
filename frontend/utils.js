/**
 * 프론트엔드 유틸리티 함수들
 */

import { CREDIBILITY_LEVELS, UI_CONSTANTS } from './constants.js';

/**
 * HTML 특수문자 이스케이프
 */
export function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * 국가 코드로 국기 이모지 반환
 */
export function getCountryFlag(country) {
  const flags = {
    US: '🇺🇸',
    KR: '🇰🇷',
    GB: '🇬🇧',
    CN: '🇨🇳',
    JP: '🇯🇵',
    RU: '🇷🇺',
    FR: '🇫🇷',
    DE: '🇩🇪',
  };
  return flags[country] || '🌍';
}

/**
 * 신뢰도 점수에 따른 CSS 클래스 반환
 */
export function getCredibilityClass(credibility) {
  const score = credibility || UI_CONSTANTS.DEFAULT_CREDIBILITY;

  if (score >= CREDIBILITY_LEVELS.HIGH.min) {
    return CREDIBILITY_LEVELS.HIGH.class;
  } else if (score >= CREDIBILITY_LEVELS.MEDIUM.min) {
    return CREDIBILITY_LEVELS.MEDIUM.class;
  } else {
    return CREDIBILITY_LEVELS.LOW.class;
  }
}

/**
 * 확신도를 퍼센트로 변환
 */
export function confidenceToPercent(confidence) {
  if (confidence === undefined || confidence === null) return 'N/A';
  return (confidence * 100).toFixed(UI_CONSTANTS.CONFIDENCE_DECIMAL_PLACES);
}

/**
 * HTML 엘리먼트 생성 헬퍼
 */
export function createElement(tag, className, innerHTML = '') {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (innerHTML) element.innerHTML = innerHTML;
  return element;
}

/**
 * 배지 HTML 생성
 */
export function createBadge(label, value, cssClass = '') {
  return `
    <div class="badge ${cssClass}">
      <span class="badge-value">${escapeHtml(String(value))}</span>
      <span class="badge-label">${escapeHtml(label)}</span>
    </div>
  `;
}

/**
 * 태그 HTML 생성
 */
export function createTag(text, className = 'tag') {
  return `<span class="${className}">${escapeHtml(text)}</span>`;
}

/**
 * 리스트 HTML 생성
 */
export function createList(items, className = '') {
  if (!items || items.length === 0) return '';

  const listItems = items.map(item => `<li>${escapeHtml(item)}</li>`).join('');
  return `<ul class="${className}">${listItems}</ul>`;
}

/**
 * 섹션 헤더 생성
 */
export function createSectionHeader(title, count = null) {
  const countText = count !== null ? ` (${count}개)` : '';
  return `<h5 class="section-subtitle">${escapeHtml(title)}${countText}</h5>`;
}
