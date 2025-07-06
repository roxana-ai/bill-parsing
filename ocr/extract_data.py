# ocr/extract_data.py

import os
import subprocess
import tempfile
import re
import cv2
import numpy as np
from PIL import Image, ImageOps, ImageFilter
from config import config

def load_image(image_path):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    try:
        return Image.open(image_path)
    except Exception as e:
        raise IOError(f"Failed to open image: {e}")

def run_tesseract(image_path, lang=config.TESSERACT_LANG, psm=config.TESSERACT_PSM):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        tmp_path_no_ext = tmp.name.replace(".txt", "")
    command = [
        config.TESSERACT_PATH,
        image_path,
        tmp_path_no_ext,
        "-l", lang,
        "--psm", str(psm)
    ]
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        raise RuntimeError("Tesseract binary not found. Check TESSERACT_PATH in config.py.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Tesseract failed: {e}")
    txt_path = f"{tmp_path_no_ext}.txt"
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read()
    finally:
        if os.path.exists(txt_path):
            os.remove(txt_path)
    return text

def deskew_image(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    coords = np.column_stack(np.where(img > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    cv2.imwrite(tmp.name, rotated)
    return tmp.name

def preprocess_image(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    # Resize up if small
    if img.shape[1] < 1800:
        scale = 1800 / img.shape[1]
        img = cv2.resize(img, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    # Otsu's thresholding for better binarization
    _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    cv2.imwrite("debug_preprocessed.png", img)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    cv2.imwrite(tmp.name, img)
    return tmp.name

def process_image(image_path):
    preprocessed_path = preprocess_image(image_path)
    try:
        text = run_tesseract(preprocessed_path)
    finally:
        if os.path.exists(preprocessed_path):
            os.remove(preprocessed_path)
    return text

def clean_price(price_str):
    """
    Cleans common OCR mistakes in price strings, but does NOT guess decimals for 3/4 digit numbers.
    """
    price_str = price_str.upper()
    price_str = price_str.replace('B', '8').replace('b', '6').replace('O', '0').replace('D', '0').replace('I', '1').replace('L', '1')
    price_str = price_str.replace(',', '.')
    price_str = price_str.replace(' ', '')
    match = re.match(r'([\d\.]+)([A-Z]?)$', price_str)
    if match:
        value = match.group(1)
        code = match.group(2)
        # Fix multiple dots (keep only the last as decimal)
        if value.count('.') > 1:
            parts = value.split('.')
            value = ''.join(parts[:-1]) + '.' + parts[-1]
        # Do NOT guess decimals for 3/4 digit numbers!
        return value, code
    return price_str, ''

import re

def clean_product_name(name):
    # Remove leading codes like 'A ', 'E ', 'D ', 'SS ', '"XE ', etc.
    name = re.sub(r'^[^a-zA-Z0-9]*[A-Z]{1,3}\s+', '', name)
    # Remove trailing numbers/prices
    name = re.sub(r'[\d.,BODIl]+\s*[A-Za-z]?\s*$', '', name)
    return name.strip()

def parse_ocr_text(text):
    items = []
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        match = re.search(
            r'(?P<qty>\d{1,4}[\.,]?\d*)\s*BUC\.?\s*[xX×]\s*(?P<price>[0-9.,BODIl]+)\s*([A-Za-z]?)',
            line.replace(',', '.'), re.IGNORECASE)
        if match:
            qty = match.group('qty').replace('.', '').replace(',', '')
            price_raw = match.group('price')
            price, vat_code = clean_price(price_raw)
            name = ''
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line:
                    name = clean_product_name(next_line)
            items.append({
                'product': name,
                'quantity': qty,
                'unit_price': price,
                'vat_code': vat_code
            })
            i += 2
            continue

        match2 = re.search(
            r'^(?P<name>.+?)\s+([0-9]{1,3}[\.,][0-9]{2,3})\s*([A-Za-z]?)$', line.replace(',', '.'), re.IGNORECASE)
        if match2:
            name = clean_product_name(match2.group('name'))
            price_raw = match2.group(2)
            price, vat_code = clean_price(price_raw)
            items.append({
                'product': name,
                'quantity': '1',
                'unit_price': price,
                'vat_code': vat_code
            })
            i += 1
            continue

        i += 1
    return items