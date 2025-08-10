"""
- 2025-08-07 - [추가] - v0.2.0: OCR 모듈 생성
- 기능: Tesseract를 이용하여 이미지에서 텍스트 추출
- 2025-08-07 - [수정] - v0.5.2: 메모리 직접 처리
- 기능: 파일 경로 대신 Pillow 이미지 객체를 직접 받아 OCR 처리
- 2025-08-07 - [수정] - v0.6.1: 정규 표현식을 이용한 텍스트 정제 기능 추가
- 기능: OCR 결과물에서 불필요한 문자를 제거하고 지역 이름만 추출
- 2025-08-07 - [수정] - v0.6.2: OCR 후처리 로직 강화
- 기능: 정규식 처리 후, 마지막 단어가 짧은 대문자일 경우 제거하는 규칙 추가
- 2025-08-07 - [수정] - v0.6.3: OpenCV를 이용한 이미지 전처리 기능 추가
- 기능: OCR 정확도 향상을 위해 이미지 확대, 흑백 변환, 이진화 처리
- 2025-08-08 - [수정] - v0.6.6: OpenCV를 이용한 이미지 전처리 기능 추가
- 기능: OCR 정확도 향상을 위해 이미지 확대, 흑백 변환, 이진화 처리
- 2025-08-08 - [수정] - v1.2.1: OCR 로직 단순화 및 최종화
- 2025-08-09 - [수정] - v1.5.7: OCR 정확도 향상을 위한 PSM 설정 추가
- 기능: Tesseract의 페이지 세분화 모드를 '7' (한 줄의 텍스트)로 설정
- 2025-08-09 - [수정] - v1.5.8: 다중 패스 OCR 전략 도입
- 기능: 여러 Tesseract 설정을 순차적으로 시도하여 인식률 향상
- 2025-08-09 - [수정] - v1.6.5: OCR 후처리기 연동
- 기능: Tesseract 결과물을 ocr_postprocessor로 전달하여 텍스트 교정
- 2025-08-09 - [수정] - v1.6.6: OCR 사전 필터링 기능 추가
- 기능: 유사도 검사 전, 정규식으로 오염된 텍스트를 먼저 정제
- 2025-08-09 - [수정] - v2.2.0: 역할 분리 기반 OCR 아키텍처
- 기능: 인증용과 지역 이름 인식용 OCR 함수를 분리하여 정확도 향상


"""
import pytesseract
import re
import cv2
import numpy as np
from src.config.settings import TESSERACT_CMD_PATH
from src.core.ocr_postprocessor import find_best_match

pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD_PATH


def _preprocess_image(pil_image):
    """(내부용) 이미지를 전처리합니다."""
    image_np = np.array(pil_image)
    gray_image = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
    scaled_image = cv2.resize(gray_image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    _, binary_image = cv2.threshold(scaled_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    inverted_image = cv2.bitwise_not(binary_image)
    cv2.imwrite("processed_for_ocr.png", inverted_image)
    return inverted_image


def _get_raw_text(processed_image, config):
    """(내부용) Tesseract를 호출하여 텍스트를 추출합니다."""
    return pytesseract.image_to_string(processed_image, lang='eng+kor', config=config).strip()


def ocr_for_zone_name(pil_image):
    """'지역 이름' 인식을 위한 전문 OCR 함수"""
    if pil_image is None: return ""
    try:
        processed_image = _preprocess_image(pil_image)
        raw_text = _get_raw_text(processed_image, r'--psm 6')
        if not raw_text: return ""
        print(f"1차 OCR (Zone): '{raw_text}'")

        candidates = re.findall(r'[A-Z][a-zA-Z\s]+', raw_text)
        if not candidates: return ""

        pre_filtered_text = max(candidates, key=len).strip()
        print(f"사전 필터링 (Zone): '{pre_filtered_text}'")

        corrected_text = find_best_match(pre_filtered_text)
        if corrected_text:
            print(f"후처리 (Zone): '{corrected_text}'")
            return corrected_text
        return pre_filtered_text
    except Exception as e:
        print(f"OCR (Zone) 처리 중 오류: {e}")
        return ""
def _list_installed_tess_langs():
    """설치된 Tesseract 언어 목록을 반환. 실패 시 {'eng'}."""
    try:
        if pytesseract is None:
            return {"eng"}
        langs = pytesseract.get_languages(config="")
        return set(langs) if langs else {"eng"}
    except Exception:
        return {"eng"}

def _pick_available_langs(preferred_list):
    """
    선호 언어 목록 중 설치되어 있는 것만 '+'로 조합해 문자열로 반환.
    전혀 없으면 'eng' 반환. (ex) 'eng+kor'
    """
    avail = _list_installed_tess_langs()
    selected = [l for l in preferred_list if l in avail]
    return "+".join(selected) if selected else "eng"

def ocr_for_authentication(pil_image):
    """'사용자 인증'을 위한 전문 OCR 함수"""
    if pil_image is None: return ""
    try:
        processed_image = _preprocess_image(pil_image)
          # 다양한 배치/분산 텍스트 대응: psm 11 (sparse text)
          # Tesseract 언어는 설치 여부에 따라 eng(+kor+spa)로 구성.
        langs = _pick_available_langs(["eng", "kor", "spa"])
          # NOTE: 기존 _get_raw_text 시그니처를 유지하기 위해 config 문자열 내에 -l 전달.
          # (pytesseract에선 lang= 파라미터 권장이지만, 여기선 내부 구현 변경 없이 호환 유지)
        custom_config = rf'--psm 11 -l {langs}'
        raw_text = _get_raw_text(processed_image, custom_config)
        print(f"OCR (Auth): '{raw_text}'")
        return raw_text
    except Exception as e:
        print(f"OCR (Auth) 처리 중 오류: {e}")
        return ""
