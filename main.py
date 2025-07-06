import os
import pandas as pd
from ocr.extract_data import process_image, parse_ocr_text

def main():
    image_name = "IMG_4653.jpg"
    image_path = os.path.join("data", "images", image_name)
    text = process_image(image_path)
    print("Extracted Text:\n")
    print(text)
    print("\nExtracted Items:\n")
    items = parse_ocr_text(text)
    df = pd.DataFrame(items).to_csv("output/df_"+image_name.split("jpg")[0]+"csv")
    print(df)

if __name__ == "__main__":
    main()