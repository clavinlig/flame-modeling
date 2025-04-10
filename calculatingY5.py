import pandas as pd
import os
from pathlib import Path

bin_list = [f"Y_BIN{i}{letter}J" for i in range(5, 26) for letter in ['A', 'B', 'C']]

fixed_columns = ['grid', 'velocity', 'spread_rate', 'lambda', 'T', 'D', 'Y_H2O', 'Y_C6H6']
columns_to_keep = fixed_columns + bin_list

input_files = [
    '400_K_ethylene_Y.csv',
    '500_K_ethylene_Y.csv',
    '600_K_ethylene_Y.csv',
    '700_K_ethylene_Y.csv'
]

input_dir = 'input_dir'
output_dir = 'output_dir'

os.makedirs(output_dir, exist_ok=True)

for input_file_name in input_files:
    input_path = Path(input_dir) / input_file_name
    
    if not input_path.exists():
        print(f"Файл {input_file_name} не найден. Пропускаем...")
        continue
    
    data = pd.read_csv(input_path)
    new_data = data[columns_to_keep]
    
    # Суммируем значения по столбцам из bin_list
    columns_to_sum = bin_list
    new_data['sum_bin'] = new_data[columns_to_sum].sum(axis=1)

    output_file_name = f"prep_{input_file_name}"
    output_path = Path(output_dir) / output_file_name
    
    new_data.to_csv(output_path, index=False)
    
    print(f"Обработка файла {input_file_name} завершена. Результат сохранен в {output_file_name}")