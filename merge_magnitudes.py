import pandas as pd

mb_data = pd.read_csv("ISC_data/excelFiles/isc_mb.csv", delimiter=";")
ms_data = pd.read_csv("ISC_data/excelFiles/isc_ms.csv", delimiter=";")

tiempo_cols = ["year", "month", "day", "hour", "minutes"]

merged = pd.merge(mb_data, ms_data, on=tiempo_cols, how='outer', suffixes=('_mb', '_ms'))

mask_distancia = (abs(merged['lat_mb'] - merged['lat_ms']) < 1) & (abs(merged['lon_mb'] - merged['lon_ms']) < 1)

final_df = merged.copy()

final_df['lat'] = final_df['lat_mb'].fillna(final_df['lat_ms'])
final_df['lon'] = final_df['lon_mb'].fillna(final_df['lon_ms'])
final_df['depth'] = final_df['depth_mb'].fillna(final_df['depth_ms'])

final_df['mb'] = final_df['mb'].fillna("n.a")
final_df['ms'] = final_df['ms'].fillna("n.a")

columns = ["year", "month", "day", "hour", "minutes", "lat", "lon", "depth", "mb", "ms"]
final_df = final_df[columns]

final_df = final_df.drop_duplicates()

print(final_df)
final_df.to_csv("ISC_output.csv", index=False)