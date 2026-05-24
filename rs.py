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

def analyze_rs(img_path):
    """Возвращает метрику RS (разница R и S групп)"""
    try:
        img = Image.open(img_path).convert('L')
        px = np.array(img, dtype=np.int16)
        h, w = px.shape
        if h < 10 or w < 10: return None

        # Маска 1x4 пикселя: [1, 0, 0, 1]
        # Берем блоки 1x4
        # px[:, :-3] - берем все строки, колонки до конца-3
        groups = px[:, :-3:4] # Это упрощение для скорости
        
        # Но для точности лучше пройтись по 2x2 блокам или просто считать разность
        # Упрощенная логика RS: если инверсия LSB увеличивает "шум" (разность соседей), это Regular (R)
        # Если уменьшает - Singular (S)
        
        # 1. Считаем "шум" оригинала (сумма разностей соседних пикселей)
        # Горизонтальные разности
        diff_h = np.abs(px[:, :-1].astype(float) - px[:, 1:].astype(float))
        noise_orig = np.sum(diff_h)
        
        # 2. Инвертируем LSB в шахматном порядке
        px_mod = px.copy()
        px_mod[::2, ::2] = px_mod[::2, ::2] ^ 1 # XOR 1 инвертирует младший бит
        
        # 3. Считаем "шум" модифицированного
        diff_h_mod = np.abs(px_mod[:, :-1].astype(float) - px_mod[:, 1:].astype(float))
        noise_mod = np.sum(diff_h_mod)
        
        # Если шум вырос -> Regular, если упал -> Singular
        # Метрика: (NoiseMod - NoiseOrig). 
        # Для чистых фото это значение обычно отрицательное или близкое к 0.
        # Для стего (OutGuess) оно стремится к 0 или положительному.
        
        return float(noise_mod - noise_orig)
    except:
        return None

def run_analysis():
    print("🚀 Запуск RS-анализа...")
    results = []
    
    # Plain
    print("📂 Обработка Plain...")
    plain_files = [os.path.join(BASE_DIR, f) for f in os.listdir(BASE_DIR) 
                   if f.lower().endswith('.jpg') and not f.startswith('.')]
    plain_files = sorted(plain_files)[:LIMIT_PER_FOLDER]
    
    for f in tqdm(plain_files):
        val = analyze_rs(f)
        if val is not None:
            results.append({"folder": "0", "file": os.path.basename(f), "metric": val})

    # Stego
    for folder_name in FOLDERS:
        path = os.path.join(BASE_DIR, folder_name)
        if not os.path.exists(path): continue
        
        files = sorted([os.path.join(path, f) for f in os.listdir(path) if f.endswith('.jpg')])[:LIMIT_PER_FOLDER]
        print(f"📂 Обработка {folder_name} Б...")
        
        for f in tqdm(files):
            val = analyze_rs(f)
            if val is not None:
                results.append({"folder": folder_name, "file": os.path.basename(f), "metric": val})

    df = pd.DataFrame(results)
    if df.empty: return

    # Порог: берем среднее Plain + отклонение
    plain_data = df[df["folder"] == "0"]["metric"]
    # В RS стего обычно имеет БОЛЬШУЮ метрику (ближе к 0 или плюсу), чем чистые (минус)
    threshold = plain_data.mean() + 1.5 * plain_data.std()

    print(f"\n📊 Порог обнаружения: {threshold:.4f}")
    
    df["detected"] = df["metric"] > threshold
    
    summary = []
    for name, group in df.groupby("folder"):
        det = group["detected"].sum()
        total = len(group)
        print(f"   Папка {name} Б: {det}/{total} ({100*det/total:.1f}%)")
        summary.append({"Payload": name, "Detected": det, "Total": total, "Percent": 100*det/total})
        
    pd.DataFrame(summary).to_csv("result_rs.csv", index=False)
    print("✅ Сохранено в result_rs.csv")

if __name__ == "__main__":
    run_analysis()
