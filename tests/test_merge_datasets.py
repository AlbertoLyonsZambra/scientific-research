"""
Tests para merge_datasets.py
Cubre:
  - haversine(): puntos idénticos, distancia conocida, dirección inversa
  - merge_cmt_isc(): archivos inexistentes, DataFrames vacíos, match correcto,
    filtro por tiempo, filtro por distancia, guardado de Excel de salida.
"""
import os
import math
import tempfile

import pandas as pd
import numpy as np
import pytest

# Asegurar que el directorio raíz del proyecto esté en el path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from merge_datasets import haversine, merge_cmt_isc


# ──────────────────────────────────────────────────────────────
# Fixtures: DataFrames de ejemplo
# ──────────────────────────────────────────────────────────────

def _make_cmt_df():
    """CMT mínimo con 2 sismos."""
    return pd.DataFrame({
        "event_id":      ["2023021A", "2023022B"],
        "location":      ["TURKEY",   "CHILE"],
        "date":          ["2023-02-06", "2023-02-07"],
        "centroid_time": ["01:28:00",   "05:30:00"],
        "latitude":      [37.0,         -33.0],
        "longitude":     [37.2,         -71.5],
        "depth":         [10.0,          20.0],
        "mw":            [7.8,            5.5],
        "mb":            [6.5,            4.8],
        "ms":            [7.5,            5.0],
    })


def _make_isc_df():
    """ISC mínimo con 2 sismos: uno coincidente con CMT, otro no."""
    return pd.DataFrame({
        "event_id": ["ISC001",      "ISC002"],
        "date":     ["2023-02-06 01:28:30",   # 30 seg después → match
                     "2023-02-07 12:00:00"],   # 6.5 h después → no match tiempo
        "latitude":  [37.1,   -33.0],
        "longitude": [37.3,   -71.5],
        "depth":     [12.0,    22.0],
        "magnitude": [7.7,      5.4],
    })


def _write_excel(df, path):
    """Helper: guarda un DataFrame como .xlsx."""
    df.to_excel(path, index=False)


# ──────────────────────────────────────────────────────────────
# Tests de haversine()
# ──────────────────────────────────────────────────────────────

class TestHaversine:
    def test_same_point_is_zero(self):
        """Misma coordenada → 0 km."""
        dist = haversine(37.0, 37.2, 37.0, 37.2)
        assert dist == pytest.approx(0.0, abs=1e-6)

    def test_known_distance_equator(self):
        """
        Dos puntos en el ecuador separados 1° de longitud ≈ 111.195 km.
        """
        dist = haversine(0.0, 0.0, 0.0, 1.0)
        assert dist == pytest.approx(111.195, rel=0.01)

    def test_symmetry(self):
        """haversine(A,B) == haversine(B,A)."""
        d1 = haversine(37.0, 37.2, -33.0, -71.5)
        d2 = haversine(-33.0, -71.5, 37.0, 37.2)
        assert d1 == pytest.approx(d2, rel=1e-9)

    def test_antipodal_points(self):
        """Puntos antipodales → ≈ π × R ≈ 20 015 km."""
        dist = haversine(0.0, 0.0, 0.0, 180.0)
        assert dist == pytest.approx(math.pi * 6371, rel=0.001)

    def test_returns_float(self):
        result = haversine(10.0, 20.0, 10.0, 20.0)
        assert isinstance(float(result), float)


# ──────────────────────────────────────────────────────────────
# Tests de merge_cmt_isc()
# ──────────────────────────────────────────────────────────────

class TestMergeCmtIsc:

    # ── Manejo de errores de entrada ──────────────────────────

    def test_returns_none_if_cmt_path_invalid(self, tmp_path):
        isc_file = tmp_path / "isc.xlsx"
        _write_excel(_make_isc_df(), isc_file)
        result = merge_cmt_isc(
            str(tmp_path / "no_existe.xlsx"),
            str(isc_file),
            str(tmp_path / "out.xlsx"),
        )
        assert result is None

    def test_returns_none_if_isc_path_invalid(self, tmp_path):
        cmt_file = tmp_path / "cmt.xlsx"
        _write_excel(_make_cmt_df(), cmt_file)
        result = merge_cmt_isc(
            str(cmt_file),
            str(tmp_path / "no_existe.xlsx"),
            str(tmp_path / "out.xlsx"),
        )
        assert result is None

    def test_returns_empty_df_if_cmt_empty(self, tmp_path):
        cmt_file = tmp_path / "cmt.xlsx"
        isc_file = tmp_path / "isc.xlsx"
        _write_excel(pd.DataFrame(), cmt_file)
        _write_excel(_make_isc_df(), isc_file)
        result = merge_cmt_isc(str(cmt_file), str(isc_file), str(tmp_path / "out.xlsx"))
        assert isinstance(result, pd.DataFrame) and result.empty

    def test_returns_empty_df_if_isc_empty(self, tmp_path):
        cmt_file = tmp_path / "cmt.xlsx"
        isc_file = tmp_path / "isc.xlsx"
        _write_excel(_make_cmt_df(), cmt_file)
        _write_excel(pd.DataFrame(), isc_file)
        result = merge_cmt_isc(str(cmt_file), str(isc_file), str(tmp_path / "out.xlsx"))
        assert isinstance(result, pd.DataFrame) and result.empty

    # ── Lógica de fusión ──────────────────────────────────────

    def test_match_correct_event(self, tmp_path):
        """
        El sismo ISC001 debe coincidir con 2023021A (Turquía).
        Diferencia de tiempo: 30 s < 120 s.
        Distancia Haversine ≈ 12 km < 200 km.
        """
        cmt_file = tmp_path / "cmt.xlsx"
        isc_file = tmp_path / "isc.xlsx"
        out_file = tmp_path / "out.xlsx"
        _write_excel(_make_cmt_df(), cmt_file)
        _write_excel(_make_isc_df(), isc_file)

        result = merge_cmt_isc(str(cmt_file), str(isc_file), str(out_file))

        assert result is not None
        assert len(result) == 1
        # Debe contener el evento de Turquía
        assert "ISC001" in result["event_id_isc"].values

    def test_no_match_when_time_tol_very_small(self, tmp_path):
        """Con tolerancia de 1 segundo, ningún evento debe coincidir (diff=30s)."""
        cmt_file = tmp_path / "cmt.xlsx"
        isc_file = tmp_path / "isc.xlsx"
        out_file = tmp_path / "out.xlsx"
        _write_excel(_make_cmt_df(), cmt_file)
        _write_excel(_make_isc_df(), isc_file)

        result = merge_cmt_isc(
            str(cmt_file), str(isc_file), str(out_file), time_tol_sec=1
        )
        assert result is not None
        assert result.empty

    def test_no_match_when_dist_tol_very_small(self, tmp_path):
        """Con tolerancia de 1 km, el evento de Turquía no debe coincidir (~12 km)."""
        cmt_file = tmp_path / "cmt.xlsx"
        isc_file = tmp_path / "isc.xlsx"
        out_file = tmp_path / "out.xlsx"
        _write_excel(_make_cmt_df(), cmt_file)
        _write_excel(_make_isc_df(), isc_file)

        result = merge_cmt_isc(
            str(cmt_file), str(isc_file), str(out_file), dist_tol_km=1
        )
        assert result is not None
        assert result.empty

    def test_output_excel_is_created(self, tmp_path):
        """Cuando hay matches, el archivo Excel de salida debe ser creado."""
        cmt_file = tmp_path / "cmt.xlsx"
        isc_file = tmp_path / "isc.xlsx"
        out_file = tmp_path / "out.xlsx"
        _write_excel(_make_cmt_df(), cmt_file)
        _write_excel(_make_isc_df(), isc_file)

        merge_cmt_isc(str(cmt_file), str(isc_file), str(out_file))

        assert out_file.exists()

    def test_output_excel_readable(self, tmp_path):
        """El Excel de salida debe poder leerse de vuelta con pandas."""
        cmt_file = tmp_path / "cmt.xlsx"
        isc_file = tmp_path / "isc.xlsx"
        out_file = tmp_path / "out.xlsx"
        _write_excel(_make_cmt_df(), cmt_file)
        _write_excel(_make_isc_df(), isc_file)

        merge_cmt_isc(str(cmt_file), str(isc_file), str(out_file))

        df_out = pd.read_excel(out_file, sheet_name="Merged_Earthquakes")
        assert not df_out.empty

    def test_result_sorted_by_isc_datetime(self, tmp_path):
        """El resultado debe estar ordenado de forma ascendente por datetime_isc."""
        # Añadir un tercer sismo coincidente pero cronológicamente anterior
        cmt_extra = _make_cmt_df().copy()
        isc_extra = _make_isc_df().copy()

        # Agregar un segundo match claro: mismas coords, fecha anterior, diff 10s
        cmt_extra.loc[2] = {
            "event_id": "2023020XA", "location": "TURKEY2",
            "date": "2023-02-05", "centroid_time": "10:00:00",
            "latitude": 37.0, "longitude": 37.2,
            "depth": 10.0, "mw": 5.0, "mb": 4.0, "ms": 4.5,
        }
        isc_extra.loc[2] = {
            "event_id": "ISC003",
            "date": "2023-02-05 10:00:10",
            "latitude": 37.0, "longitude": 37.2,
            "depth": 10.0, "magnitude": 5.0,
        }

        cmt_file = tmp_path / "cmt.xlsx"
        isc_file = tmp_path / "isc.xlsx"
        out_file = tmp_path / "out.xlsx"
        _write_excel(cmt_extra, cmt_file)
        _write_excel(isc_extra, isc_file)

        result = merge_cmt_isc(str(cmt_file), str(isc_file), str(out_file))

        assert result is not None
        assert len(result) >= 2
        datetimes = pd.to_datetime(result["datetime_isc"])
        assert (datetimes.diff().dropna() >= pd.Timedelta(0)).all(), \
            "Los resultados no están ordenados de forma ascendente"

    def test_temp_columns_removed(self, tmp_path):
        """Las columnas temporales 'join_date' y 'date_str' no deben aparecer en el resultado."""
        cmt_file = tmp_path / "cmt.xlsx"
        isc_file = tmp_path / "isc.xlsx"
        out_file = tmp_path / "out.xlsx"
        _write_excel(_make_cmt_df(), cmt_file)
        _write_excel(_make_isc_df(), isc_file)

        result = merge_cmt_isc(str(cmt_file), str(isc_file), str(out_file))

        assert result is not None
        assert "join_date" not in result.columns
        assert "date_str" not in result.columns
