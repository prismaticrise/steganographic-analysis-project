#!/usr/bin/env python3
import os
import subprocess
import tempfile
from pathlib import Path

# ================= НАСТРОЙКИ =================
WORK_DIR = Path(".")
OUTGUESS_KEY = "my_stego_key_2026"  # Ключ для outguess
LENGTHS = [50, 100, 500, 1000]      # Длины ПСП
NUM_IMAGES = 1000                   # Количество картинок
PSP_LOG_FILE = WORK_DIR / "psp_sequences.txt"
# =============================================

def generate_and_save_psp():
    """Генерирует ПСП и сохраняет их в текстовый файл (hex-формат)"""
    psp_bytes = {}
    print(f" Генерация ПСП и сохранение в {PSP_LOG_FILE.name}...")
    
    with open(PSP_LOG_FILE, "w", encoding="utf-8") as f:
        for length in LENGTHS:
            raw = os.urandom(length)
            psp_bytes[length] = raw
            f.write(f"Length {length}: {raw.hex()}\n")
            
    print("✅ ПСП сохранены.\n")
    return psp_bytes

def run_outguess(input_jpg, output_jpg, data_file, key):
    """Запускает outguess и возвращает (success: bool, message: str)"""
    cmd = [
        "outguess",
        "-d", str(data_file),
        str(input_jpg),
        str(output_jpg)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0 and output_jpg.exists():
            return True, "Успешно"
        else:
            err = result.stderr.strip() or result.stdout.strip() or "Неизвестная ошибка outguess"
            return False, err
    except FileNotFoundError:
        return False, "Утилита 'outguess' не найдена в PATH. Установите её или укажите полный путь."
    except Exception as e:
        return False, str(e)

def main():
    # 1. Генерация и сохранение ПСП
    psp_data = generate_and_save_psp()
    
    # 2. Подготовка временных файлов для outguess (-d принимает только файлы)
    temp_files = {}
    for length in LENGTHS:
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".bin")
        tf.write(psp_data[length])
        tf.close()
        temp_files[length] = tf.name
        
    # 3. Создание целевых папок
    for length in LENGTHS:
        (WORK_DIR / str(length)).mkdir(exist_ok=True)
        
    # 4. Статистика
    stats = {length: {"success": 0, "fail": 0} for length in LENGTHS}
    
    # 5. Основной цикл встраивания
    for length in LENGTHS:
        print(f"\n🔹 Обработка ПСП длины {length} байт:")
        print("-" * 40)
        
        for i in range(NUM_IMAGES):
            img_name = f"{i:05d}.jpg"
            input_path = WORK_DIR / img_name
            output_dir = WORK_DIR / str(length)
            output_name = f"{i:05d}_{length}.jpg"
            output_path = output_dir / output_name
            
            print(f"Начинаю встраивание в файл {img_name}...", end=" ")
            
            if not input_path.exists():
                print(f"❌ Ошибка: файл {img_name} не найден в рабочей директории.")
                stats[length]["fail"] += 1
                continue
                
            success, msg = run_outguess(input_path, output_path, temp_files[length], OUTGUESS_KEY)
            
            if success:
                print(f"✅ Успешно: -> {length}/{output_name}")
                stats[length]["success"] += 1
            else:
                print(f"❌ Не удалось: {msg}")
                stats[length]["fail"] += 1
                
    # 6. Очистка временных файлов
    for tf in temp_files.values():
        os.remove(tf)
        
    # 7. Итоговая статистика
    print("\n" + "="*50)
    print("📊 СТАТИСТИКА ВСТРАИВАНИЯ")
    print("="*50)
    for length in LENGTHS:
        s = stats[length]
        print(f"Длина ПСП {length:>4} байт | Успешно: {s['success']:>4} | Ошибки: {s['fail']:>4}")
    print("="*50)
    print("🏁 Работа скрипта завершена.")

if __name__ == "__main__":
    main()
