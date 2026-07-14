import pandas as pd
import matplotlib.pyplot as plt

csv_path = "data_files/Final_data/CaliforniaData.csv"
df = pd.read_csv(filepath_or_buffer=csv_path, sep=";")

mw_data = df["mw"].tolist()
mwg_data = df["mwg"].tolist()

log_m0_data = []
for mw in mw_data:
    log_m0 = (mw+10.7)*(3/2)
    log_m0_data.append(log_m0)

plt.figure(figsize=(10, 6))
plt.plot(log_m0_data, mw_data, color='blue', marker='o')

# Etiquetas para hacerlo legible
plt.title('Magnitud Mw por registro')
plt.xlabel('Log_M0')
plt.ylabel('Magnitud (Mw)')
plt.grid(True)

# Mostrar el gráfico
plt.show()