import os
import re
import cv2
import numpy as np
from PIL import Image
import pytesseract
from pdf2image import convert_from_path

# --- Preprocessing ---
def remove_lines(img):
    horiz_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40,1))
    vert_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1,40))
    horiz_lines = cv2.morphologyEx(img, cv2.MORPH_OPEN, horiz_kernel, iterations=2)
    vert_lines = cv2.morphologyEx(img, cv2.MORPH_OPEN, vert_kernel, iterations=2)
    mask = cv2.add(horiz_lines, vert_lines)
    return cv2.bitwise_and(img, cv2.bitwise_not(mask))

def deskew_image(img):
    coords = np.column_stack(np.where(img > 0))
    if len(coords) == 0:
        return img
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    h, w = img.shape
    M = cv2.getRotationMatrix2D((w//2, h//2), angle, 1.0)
    return cv2.warpAffine(img, M, (w,h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

def preprocess_image(img_input, mode="camera"):
    if isinstance(img_input, str):
        img = cv2.imread(img_input)
        if img is None:
            raise FileNotFoundError(f"Image not found: {img_input}")
    else:
        img = cv2.cvtColor(np.array(img_input), cv2.COLOR_RGB2BGR)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    target_width = 1500 if mode=="pdf" else 2000
    h, w = gray.shape
    if w < target_width:
        scale = target_width / w
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    denoise = cv2.medianBlur(gray, 3 if mode=="pdf" else 5)
    if mode=="pdf":
        _, bw = cv2.threshold(denoise, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        bw = cv2.adaptiveThreshold(denoise, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)
    cleaned = remove_lines(cv2.bitwise_not(bw))
    deskewed = deskew_image(cleaned)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
    dilated = cv2.dilate(deskewed, kernel, iterations=1)
    return cv2.bitwise_not(dilated)

# --- Postprocessing ---
def postprocess_text(text):
    clean = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if sum(c.isalnum() for c in line)/max(len(line),1) < 0.3:
            continue
        if re.fullmatch(r'[-–—_\s]+', line):
            continue
        clean.append(line)
    return "\n".join(clean)

# --- Main parser ---
def parse_image(file_path, from_pdf=False):
    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)

    texts = []

    ext = os.path.splitext(file_path)[1].lower()
    if ext==".pdf" or from_pdf:
        try:
            images = convert_from_path(file_path, dpi=400)
        except Exception as e:
            raise RuntimeError(f"Failed to convert PDF to images: {e}")
        for img in images:
            processed = preprocess_image(img, mode="pdf")
            pil_img = Image.fromarray(processed)
            raw = pytesseract.image_to_string(pil_img, lang="eng", config="--psm 3")
            texts.append(postprocess_text(raw))
    else:
        processed = preprocess_image(file_path, mode="camera")
        pil_img = Image.fromarray(processed)
        raw = pytesseract.image_to_string(pil_img, lang="eng", config="--psm 3")
        texts.append(postprocess_text(raw))

    return "\n\n".join(texts).strip()
