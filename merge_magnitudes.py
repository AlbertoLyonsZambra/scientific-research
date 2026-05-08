import pandas as pd
import math
mb_csv = "ISC_data/excelFiles/isc_mb.csv"
ms_csv = "ISC_data/excelFiles/isc_ms.csv"

mb_data = pd.read_csv(mb_csv, delimiter=";")
ms_data = pd.read_csv(ms_csv, delimiter=";")

columns = ["year", "month", "day", "hour", "minutes", "lat", "lon", "depth", "mb", "ms"]
merged_dataframe = pd.DataFrame(columns=columns)

encountered_same = False

for mb_index, mb_row in mb_data.iterrows():
    encountered_same = False
    new_data = {}
    for ms_index, ms_row in ms_data.iterrows():
        if mb_row["year"] == ms_row["year"] and mb_row["month"] == ms_row["month"] and mb_row["day"] == ms_row["day"] and mb_row["hour"] == ms_row["hour"] and mb_row["minutes"] == ms_row["minutes"]:
            if abs(mb_row["lat"] - ms_row["lat"]) < 1 and abs(mb_row["lon"] - ms_row["lon"]) < 1:
                encountered_same = True
                new_data = {
                    "year": [mb_row["year"]],
                    "month": [mb_row["month"]],
                    "day": [mb_row["day"]],
                    "hour": [mb_row["hour"]],
                    "minutes": [mb_row["minutes"]],
                    "lat": [mb_row["lat"]],
                    "lon": [mb_row["year"]],
                    "depth": [mb_row["depth"]],
                    "mb": [mb_row["mb"]],
                    "ms": [ms_row["ms"]]
                }
                new_row = pd.DataFrame(new_data)
                merged_dataframe = pd.concat([merged_dataframe, new_row], ignore_index=True)
                break
        else:
            new_data = {
                "year": [ms_row["year"]],
                "month": [ms_row["month"]],
                "day": [ms_row["day"]],
                "hour": [ms_row["hour"]],
                "minutes": [ms_row["minutes"]],
                "lat": [ms_row["lat"]],
                "lon": [ms_row["year"]],
                "depth": [ms_row["depth"]],
                "mb": ["n.a"],
                "ms": [ms_row["ms"]]
                }
            new_row = pd.DataFrame(new_data)
            merged_dataframe = pd.concat([merged_dataframe, new_row], ignore_index=True)
    if encountered_same:
        pass
    else:
        new_data = {
        "year": [mb_row["year"]],
        "month": [mb_row["month"]],
        "day": [mb_row["day"]],
        "hour": [mb_row["hour"]],
        "minutes": [mb_row["minutes"]],
        "lat": [mb_row["lat"]],
        "lon": [mb_row["year"]],
        "depth": [mb_row["depth"]],
        "mb": [mb_row["mb"]],
        "ms": ["n.a"]
        }
        new_row = pd.DataFrame(new_data)
        merged_dataframe = pd.concat([merged_dataframe, new_row], ignore_index=True)
print(merged_dataframe)
merged_dataframe.to_csv("ISC_output.csv")