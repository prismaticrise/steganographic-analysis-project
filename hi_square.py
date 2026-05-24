import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from scipy.stats import chisquare
from tqdm import tqdm

# === НАСТРОЙКИ ===
BASE_DIR = os.getcwd()
LIMIT_PER_FOLDER = 1000
FOLDERS = ["50", "100", "500", "1000"]

def analyze_chi_square(img_path):
    """Возвращает p-value"""
    try:
        img = Image.open(img_path).convert('L')
        px = np.array(img)
        
        # Берем выборку пикселей (каждый 8-й для скорости)
        # flatten делает массив одномерным
        sample = px[::8, ::8].flatten()
        
        if len(sample) < 50: return None
        
        # Считаем четные и нечетные значения (проверка LSB)
        evens = np.sum(sample % 2 == 0)
        odds = len(sample) - evens
        
        # Chi-Square тест на равномерность (50/50)
        _, p_val = chisquare([evens, odds], f_exp=[len(sample)/2, len(sample)/2])
        return float(p_val)
    except:
        return None

def run_analysis():
    print(" Запуск Chi-Square анализа...")
    results = []
    
    # 1. Сначала plain (корень папки)
    print("📂 Обработка Plain...")
    plain_files = [os.path.join(BASE_DIR, f) for f in os.listdir(BASE_DIR) 
                   if f.lower().endswith('.jpg') and not f.startswith('.')]
    plain_files = sorted(plain_files)[:LIMIT_PER_FOLDER]
    
    for f in tqdm(plain_files):
        p_val = analyze_chi_square(f)
        if p_val is not None:
            results.append({"folder": "0", "file": os.path.basename(f), "metric": p_val})

    # 2. Потом стего-папки
    for folder_name in FOLDERS:
        path = os.path.join(BASE_DIR, folder_name)
        if not os.path.exists(path): continue
        
        files = sorted([os.path.join(path, f) for f in os.listdir(path) if f.endswith('.jpg')])[:LIMIT_PER_FOLDER]
        print(f"📂 Обработка {folder_name} Б...")
        
        for f in tqdm(files):
            p_val = analyze_chi_square(f)
            if p_val is not None:
                results.append({"folder": folder_name, "file": os.path.basename(f), "metric": p_val})

    df = pd.DataFrame(results)
    if df.empty: return

    # Порог для Plain
    plain_data = df[df["folder"] == "0"]["metric"]
    threshold = plain_data.mean() + 2 * plain_data.std()

    print(f"\n Порог обнаружения: {threshold:.4f}")
    
    # Считаем детекцию
    df["detected"] = df["metric"] > threshold
    
    summary = []
    for name, group in df.groupby("folder"):
        det = group["detected"].sum()
        total = len(group)
        print(f"   Папка {name} Б: {det}/{total} ({100*det/total:.1f}%)")
        summary.append({"Payload": name, "Detected": det, "Total": total, "Percent": 100*det/total})
        
    pd.DataFrame(summary).to_csv("result_chi_square.csv", index=False)
    print("✅ Сохранено в result_chi_square.csv")

if __name__ == "__main__":
    run_analysis()
