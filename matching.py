"""
matching.py
-----------
Inti dari mesin deduplikasi (record linkage):
  - Global pairwise matching (TANPA groupby tanggal_lahir) agar typo
    tanggal lahir tetap bisa terdeteksi kemiripannya.
  - Weighted similarity scoring memakai RapidFuzz.
  - Menandai pasangan dengan skor >= threshold sebagai "Potensi Double Count".

Kompleksitas O(N^2) disengaja sesuai requirement — cocok untuk dataset
event per-sesi yang jumlah pesertanya ratusan-ribuan (bukan jutaan).
Untuk dataset sangat besar, pertimbangkan blocking/indexing tambahan
tanpa mengubah default behavior ini.
"""

from __future__ import annotations

import pandas as pd
from itertools import combinations
from rapidfuzz import fuzz

import config


def _clean_text(value) -> str:
    """Normalisasi ringan sebelum fuzzy matching: string, strip, lower, handle NaN."""
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def compute_pair_score(record_a: dict, record_b: dict) -> dict:
    """
    Menghitung skor kemiripan berbobot antara dua record.

    Menggunakan:
      - fuzz.token_sort_ratio untuk Nama (toleran nama terbalik/singkatan)
      - fuzz.ratio untuk Tanggal Lahir, Kelurahan, Area Program

    Returns
    -------
    dict berisi skor per-field + skor akhir (final_score)
    """
    nama_a, nama_b = _clean_text(record_a.get("nama")), _clean_text(record_b.get("nama"))
    dob_a, dob_b = _clean_text(record_a.get("tanggal_lahir")), _clean_text(record_b.get("tanggal_lahir"))
    kel_a, kel_b = _clean_text(record_a.get("kelurahan")), _clean_text(record_b.get("kelurahan"))
    area_a, area_b = _clean_text(record_a.get("area_program")), _clean_text(record_b.get("area_program"))

    score_nama = fuzz.token_sort_ratio(nama_a, nama_b) if nama_a and nama_b else 0.0
    score_dob = fuzz.ratio(dob_a, dob_b) if dob_a and dob_b else 0.0
    score_kelurahan = fuzz.ratio(kel_a, kel_b) if kel_a and kel_b else 0.0
    score_area = fuzz.ratio(area_a, area_b) if area_a and area_b else 0.0

    final_score = (
        score_nama * config.WEIGHT_NAMA
        + score_dob * config.WEIGHT_DOB
        + score_kelurahan * config.WEIGHT_KELURAHAN
        + score_area * config.WEIGHT_AREA
    )

    return {
        "score_nama": round(score_nama, 2),
        "score_dob": round(score_dob, 2),
        "score_kelurahan": round(score_kelurahan, 2),
        "score_area": round(score_area, 2),
        "final_score": round(final_score, 2),
    }


def find_duplicate_pairs(
    df_combined: pd.DataFrame,
    threshold: float = config.DUPLICATE_THRESHOLD,
    progress_callback=None,
) -> pd.DataFrame:
    """
    Melakukan GLOBAL PAIRWISE MATCHING (O(N^2)) di seluruh baris df_combined
    TANPA groupby tanggal_lahir, sesuai requirement (mengantisipasi typo DOB).

    Parameters
    ----------
    df_combined : pd.DataFrame
        Gabungan dataset Login + Register (harus punya kolom REQUIRED_MATCH_COLUMNS
        + kolom 'id_kobo' dan 'source' untuk identifikasi asal data).
    threshold : float
        Ambang batas skor akhir untuk dianggap "Potensi Double Count".
    progress_callback : callable, optional
        Fungsi callback(current, total) untuk update progress bar UI.

    Returns
    -------
    pd.DataFrame
        Daftar pasangan duplikat dengan kolom:
        id_a, id_b, source_a, source_b, <field>_a, <field>_b, score_*, final_score, status
    """
    missing_cols = [c for c in config.REQUIRED_MATCH_COLUMNS if c not in df_combined.columns]
    if missing_cols:
        raise ValueError(f"Kolom wajib untuk matching tidak ditemukan: {missing_cols}")

    records = df_combined.to_dict("records")
    n = len(records)
    total_pairs = n * (n - 1) // 2 if n > 1 else 0
    results = []

    if total_pairs == 0:
        return pd.DataFrame()

    processed = 0
    for i, j in combinations(range(n), 2):
        rec_a, rec_b = records[i], records[j]

        # Data A = input pertama (berdasarkan timestamp_submit jika tersedia),
        # Data B = input susulan.
        ts_a = rec_a.get("timestamp_submit")
        ts_b = rec_b.get("timestamp_submit")
        if pd.notna(ts_a) and pd.notna(ts_b) and ts_a > ts_b:
            rec_a, rec_b = rec_b, rec_a  # swap supaya A selalu lebih awal

        scores = compute_pair_score(rec_a, rec_b)

        processed += 1
        if progress_callback and (processed % 200 == 0 or processed == total_pairs):
            progress_callback(processed, total_pairs)

        if scores["final_score"] >= threshold:
            results.append({
                "pair_id": f"{rec_a.get('id_kobo')}__{rec_b.get('id_kobo')}",
                "id_a": rec_a.get("id_kobo"),
                "id_b": rec_b.get("id_kobo"),
                "source_a": rec_a.get("source"),
                "source_b": rec_b.get("source"),
                "nama_a": rec_a.get("nama"),
                "nama_b": rec_b.get("nama"),
                "tanggal_lahir_a": rec_a.get("tanggal_lahir"),
                "tanggal_lahir_b": rec_b.get("tanggal_lahir"),
                "kelurahan_a": rec_a.get("kelurahan"),
                "kelurahan_b": rec_b.get("kelurahan"),
                "area_program_a": rec_a.get("area_program"),
                "area_program_b": rec_b.get("area_program"),
                "timestamp_submit_a": rec_a.get("timestamp_submit"),
                "timestamp_submit_b": rec_b.get("timestamp_submit"),
                **scores,
                "status": "Potensi Double Count",
            })

    if not results:
        return pd.DataFrame()

    df_result = pd.DataFrame(results).sort_values("final_score", ascending=False).reset_index(drop=True)
    return df_result


def find_registered_not_logged_in(
    df_login: pd.DataFrame,
    df_register: pd.DataFrame,
    threshold: float = config.DUPLICATE_THRESHOLD,
) -> pd.DataFrame:
    """
    Mencari peserta yang sudah mengisi Register tetapi belum Login,
    menggunakan fuzzy match yang sama (bukan exact match) supaya typo
    nama/DOB tidak menyebabkan false negative (dianggap belum login padahal sudah).

    Logika: sebuah baris Register dianggap "sudah login" jika ada minimal satu
    baris Login dengan final_score >= threshold terhadap baris tersebut.

    Returns
    -------
    pd.DataFrame
        Subset df_register yang belum memiliki pasangan di df_login.
    """
    if df_register.empty:
        return df_register.copy()
    if df_login.empty:
        return df_register.copy()

    login_records = df_login.to_dict("records")
    not_logged_in_rows = []

    for _, reg_row in df_register.iterrows():
        reg_dict = reg_row.to_dict()
        matched = False
        for login_rec in login_records:
            scores = compute_pair_score(reg_dict, login_rec)
            if scores["final_score"] >= threshold:
                matched = True
                break
        if not matched:
            not_logged_in_rows.append(reg_dict)

    if not not_logged_in_rows:
        return pd.DataFrame(columns=df_register.columns)

    return pd.DataFrame(not_logged_in_rows).reset_index(drop=True)
