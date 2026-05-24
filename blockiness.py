import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from tqdm import tqdm

# === НАСТРОЙКИ ===
BASE_DIR = os.getcwd()
LIMIT_PER_FOLDER = 1000
FOLDERS = ["50", "100", "500", "1000"]

def analyze_blockiness(img_path):
    """Возвращает среднюю разность пикселей на границах блоков 8x8"""
    try:
        img = Image.open(img_path).convert('L')
        px = np.array(img, dtype=np.float32)
        h, w = px.shape
        if h < 16 or w < 16: return None

        # 1. Вертикальные границы (разница между столбцами 7 и 8, 15 и 16...)
        # Берем столбцы на границах блоков
        col_left = px[:, 7::8]  # 7, 15, 23...
        col_right = px[:, 8::8] # 8, 16, 24...
        
        # Выравниваем длину (если ширина не кратна 8)
        min_w = min(col_left.shape[1], col_right.shape[1])
        diff_x = np.abs(col_left[:, :min_w] - col_right[:, :min_w])
        
        # 2. Горизонтальные границы
        row_top = px[7::8, :]
        row_bottom = px[8::8, :]
        min_h = min(row_top.shape[0], row_bottom.shape[0])
        diff_y = np.abs(row_top[:min_h, :] - row_bottom[:min_h, :])
        
        # Суммируем разности
        total_diff = np.sum(diff_x) + np.sum(diff_y)
        total_pixels = diff_x.size + diff_y.size
        
        if total_pixels == 0: return None
        
        return float(total_diff / total_pixels)
    except:
        return None

def run_analysis():
    print("🚀 Запуск Blockiness анализа...")
    results = []
    
    # Plain
    print("📂 Обработка Plain...")
    plain_files = [os.path.join(BASE_DIR, f) for f in os.listdir(BASE_DIR) 
                   if f.lower().endswith('.jpg') and not f.startswith('.')]
    plain_files = sorted(plain_files)[:LIMIT_PER_FOLDER]
    
    for f in tqdm(plain_files):
        val = analyze_blockiness(f)
        if val is not None:
            results.append({"folder": "0", "file": os.path.basename(f), "metric": val})

    # Stego
    for folder_name in FOLDERS:
        path = os.path.join(BASE_DIR, folder_name)
        if not os.path.exists(path): continue
        
        files = sorted([os.path.join(path, f) for f in os.listdir(path) if f.endswith('.jpg')])[:LIMIT_PER_FOLDER]
        print(f"📂 Обработка {folder_name} Б...")
        
        for f in tqdm(files):
            val = analyze_blockiness(f)
            if val is not None:
                results.append({"folder": folder_name, "file": os.path.basename(f), "metric": val})

    df = pd.DataFrame(results)
    if df.empty: return

    # Порог: Plain + отклонение
    plain_data = df[df["folder"] == "0"]["metric"]
    threshold = plain_data.mean() + 2 * plain_data.std()

    print(f"\n📊 Порог обнаружения: {threshold:.4f}")
    
    # Блочность растет при стего -> ищем значения > порога
    df["detected"] = df["metric"] > threshold
    
    summary = []
    for name, group in df.groupby("folder"):
        det = group["detected"].sum()
        total = len(group)
        print(f"   Папка {name} Б: {det}/{total} ({100*det/total:.1f}%)")
        summary.append({"Payload": name, "Detected": det, "Total": total, "Percent": 100*det/total})
        
    pd.DataFrame(summary).to_csv("result_blockiness.csv", index=False)
    print("✅ Сохранено в result_blockiness.csv")

if __name__ == "__main__":
    run_analysis()
