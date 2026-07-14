import pandas as pd
import math

csv_path = "data_files/Final_data/CaliforniaData.csv"
df = pd.read_csv(filepath_or_buffer=csv_path, sep=";")

mb_data = df["mb"].tolist()

ms_data = []
for mw in mb_data:
    ms = mw*1.74 - 3.82
    ms_data.append(math.trunc(ms*10)/10)
df["ms"] = ms_data
print(df['ms'])
df.to_csv(csv_path, index=False, sep=";")