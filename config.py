"""
config.py
---------
Konfigurasi terpusat: mapping kolom KoboToolbox, bobot scoring,
threshold, dan konstanta lain yang dipakai di seluruh aplikasi.

Memusatkan konfigurasi di sini memudahkan maintenance jika suatu saat
struktur form Kobo berubah (tambah field, ganti nama field, dsb).
"""

# =========================================================
# 1. MAPPING KOLOM KOBOTOOLBOX -> NAMA KOLOM INTERNAL
# =========================================================

LOGIN_COLUMN_MAP = {
    "_id": "id_kobo",
    "_submission_time": "timestamp_submit",
    "nama_child": "nama",
    "tgl_lahir_child": "tanggal_lahir",
    "Kelurahan": "kelurahan",
    "Tuliskan_Kelurahannya": "kelurahan_lainnya",
    "group_ys5yz58/Area_Program": "area_program",
    "group_ys5yz58/Judul_Kegiatan": "judul_kegiatan",
    "group_ys5yz58/Tanggal_Kegiatan": "tanggal_kegiatan",
}

REGISTER_COLUMN_MAP = {
    "_id": "id_kobo",
    "_submission_time": "timestamp_submit",
    "group_digital_absensi/group_informasi_respondent/nama_lengkap_parent": "nama",
    "group_digital_absensi/group_informasi_respondent/tgl_lahir_parent": "tanggal_lahir",
    "group_digital_absensi/group_informasi_respondent/Jenis_Kelamin": "jenis_kelamin",
    "group_digital_absensi/group_informasi_respondent/usia": "usia",
    "group_digital_absensi/group_informasi_respondent/Nama_Kepala_Keluarga": "nama_kepala_keluarga",
    "group_digital_absensi/group_informasi_respondent/Kelurahan": "kelurahan",
    "group_digital_absensi/group_informasi_respondent/Tuliskan_Kelurahannya": "kelurahan_lainnya",
    "group_digital_absensi/group_informasi_respondent/RT": "rt",
    "group_digital_absensi/group_informasi_respondent/RW": "rw",
    "group_digital_absensi/group_informasi_respondent/Nomor_WA_HP": "nomor_hp",
    "group_digital_absensi/group_wx4wq68/Area_Program": "area_program",
    "group_digital_absensi/group_wx4wq68/Judul_Kegiatan": "judul_kegiatan",
    "group_digital_absensi/group_wx4wq68/Tanggal_Kegiatan": "tanggal_kegiatan",
    "group_digital_absensi/group_informasi_respondent/Apakah_Anda_memiliki_kebutuhan": "tipe_disabilitas",
    "group_digital_absensi/group_informasi_respondent/Kategori_Peserta": "kategori_peserta",
}

# Kolom minimal yang WAJIB ada supaya proses matching bisa berjalan
REQUIRED_MATCH_COLUMNS = ["nama", "tanggal_lahir", "kelurahan", "area_program"]

# Kolom yang dipakai untuk ditampilkan di UI reviewer (urutan tampil)
DISPLAY_COLUMNS = [
    "id_kobo",
    "nama",
    "tanggal_lahir",
    "kelurahan",
    "area_program",
    "judul_kegiatan",
    "tanggal_kegiatan",
    "timestamp_submit",
]

# =========================================================
# 2. BOBOT SCORING (WEIGHTED SIMILARITY)
# =========================================================
WEIGHT_NAMA = 0.45
WEIGHT_DOB = 0.25
WEIGHT_KELURAHAN = 0.20
WEIGHT_AREA = 0.10

# Validasi total bobot = 1.0 (100%)
assert abs((WEIGHT_NAMA + WEIGHT_DOB + WEIGHT_KELURAHAN + WEIGHT_AREA) - 1.0) < 1e-6, \
    "Total bobot scoring harus = 1.0"

# =========================================================
# 3. THRESHOLD ATURAN
# =========================================================
DUPLICATE_THRESHOLD = 95.0  # >= nilai ini => "Potensi Double Count"

# =========================================================
# 4. KOBOTOOLBOX API DEFAULT
# =========================================================
# Ambil token API di: https://kf.kobotoolbox.org/token/?format=json
# CATATAN KEAMANAN: menyimpan token langsung di source code hanya disarankan
# untuk penggunaan lokal/internal. Untuk deployment (Streamlit Cloud, dsb),
# gunakan st.secrets atau environment variable, JANGAN commit token ke repo publik.
KOBO_TOKEN = "c710cac4d6d5fafbda973f04b30a2c27bda914c4"  # ganti dengan token API pribadi Anda

KOBO_ENDPOINT = "https://kf.kobotoolbox.org/api/v2"
KOBO_API_BASE_URL = KOBO_ENDPOINT  # alias, dipakai oleh kobo_api.py

# Asset UID (Form UID) masing-masing form Kobo.
# Setiap form punya UID unik yang bisa dilihat di URL form tersebut
# di dashboard KoboToolbox (kf.kobotoolbox.org/#/forms/<UID>/...).
FORM_UID_REGISTRASI = "aRVadKAkpz2PYMaZH2gXKU"  # Form UID khusus Registrasi
FORM_UID_LOGIN = "aE3xS8zXQsU9KQsiT9T7PA"  # TODO: isi dengan Form UID khusus Login/Absensi Anda

KOBO_REQUEST_TIMEOUT = 30  # detik

# =========================================================
# 5. SESSION STATE KEYS (biar konsisten, hindari typo string literal)
# =========================================================
SS_LOGIN_DF = "df_login"
SS_REGISTER_DF = "df_register"
SS_DUPLICATE_PAIRS = "df_duplicate_pairs"
SS_REVIEW_DECISIONS = "review_decisions"     # dict: pair_id -> keputusan
SS_REMOVED_IDS = "removed_ids"               # set id_kobo yang sudah dihapus/keputusan
SS_NOT_LOGIN_YET = "df_not_login_yet"
SS_APPENDED_IDS = "appended_ids"             # id_kobo dari register yang sudah di-append ke login
