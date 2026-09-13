import streamlit as st
import pandas as pd
import sqlite3

# -----------------------------------------------------------------------------
# 1. KONFIGURASI DAN KONEKSI DATABASE LOKAL (SQLITE)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="LMS Sekolah Digital", page_icon="🎓", layout="wide")

DB_FILE = "lms_database.db"

def init_db():
    """Membuat database dan data awal jika belum ada"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Buat Tabel Users
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            nama TEXT,
            role TEXT
        )
    ''')
    
    # Buat Tabel Materi
    c.execute('''
        CREATE TABLE IF NOT EXISTS materi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            judul TEXT,
            link TEXT,
            tanggal TEXT
        )
    ''')
    
    # Buat Tabel Tugas
    c.execute('''
        CREATE TABLE IF NOT EXISTS tugas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_siswa TEXT,
            judul_tugas TEXT,
            link_tugas TEXT,
            nilai TEXT
        )
    ''')
    
    # Isi data akun awal jika masih kosong
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users VALUES ('guru1', '12345', 'Pak Budi', 'Guru')")
        c.execute("INSERT INTO users VALUES ('siswa1', '12345', 'Siti', 'Siswa')")
        c.execute("INSERT INTO materi (judul, link, tanggal) VALUES ('Matematika Dasar', 'https://drive.google.com', '2026-09-13')")
        conn.commit()
        
    conn.close()

# Jalankan inisialisasi database
init_db()

def run_query(query, params=()):
    """Fungsi untuk membaca data"""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def execute_query(query, params=()):
    """Fungsi untuk menambah/mengubah data"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

# -----------------------------------------------------------------------------
# 2. INISIALISASI SESSION STATE (STATUS LOGIN)
# -----------------------------------------------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = {}

# -----------------------------------------------------------------------------
# 3. HALAMAN LOGIN & REGISTRASI
# -----------------------------------------------------------------------------
if not st.session_state['logged_in']:
    st.title("🎓 Portal LMS Sekolah Digital")
    
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Daftar Akun Siswa"])
    
    # --- TAB 1: LOGIN ---
    with tab1:
        st.subheader("Masuk ke Sistem")
        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type="password")
        
        if st.button("Masuk"):
            df_users = run_query("SELECT * FROM users WHERE username=? AND password=?", (username_input, password_input))
            
            if not df_users.empty:
                st.session_state['logged_in'] = True
                st.session_state['user_info'] = df_users.iloc[0].to_dict()
                st.success("Login Berhasil!")
                st.rerun()
            else:
                st.error("Username atau Password salah!")

    # --- TAB 2: REGISTRASI SISWA ---
    with tab2:
        st.subheader("Pendaftaran Akun Siswa Baru")
        reg_username = st.text_input("Buat Username Baru")
        reg_password = st.text_input("Buat Password Baru", type="password")
        reg_nama = st.text_input("Nama Lengkap Siswa")
        
        if st.button("Daftar Sekarang"):
            if reg_username and reg_password and reg_nama:
                try:
                    execute_query("INSERT INTO users VALUES (?, ?, ?, 'Siswa')", (reg_username, reg_password, reg_nama))
                    st.success("Akun berhasil dibuat! Silakan login di tab Login.")
                except Exception as e:
                    st.error("Username sudah digunakan, cari username lain.")
            else:
                st.warning("Lengkapi semua form pendaftaran!")

# -----------------------------------------------------------------------------
# 4. DASHBOARD UTAMA (SETELAH LOGIN)
# -----------------------------------------------------------------------------
else:
    role = st.session_state['user_info'].get('role', 'Siswa')
    nama = st.session_state['user_info'].get('nama', 'User')
    
    # Sidebar Navigation
    st.sidebar.title(f"Selamat Datang, {nama}!")
    st.sidebar.write(f"**Role:** {role}")
    
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['user_info'] = {}
        st.rerun()
        
    # --- DASHBOARD GURU ---
    if str(role).lower() == 'guru':
        st.title("👨‍🏫 Dashboard Guru")
        
        menu_guru = st.selectbox("Pilih Menu Guru", ["Daftar Materi", "Tambah Materi", "Daftar Tugas Siswa"])
        
        if menu_guru == "Daftar Materi":
            st.subheader("Materi Pelajaran Aktif")
            df_materi = run_query("SELECT * FROM materi")
            st.dataframe(df_materi, use_container_width=True)
            
        elif menu_guru == "Tambah Materi":
            st.subheader("Tambah Materi Baru")
            judul = st.text_input("Judul Materi")
            link = st.text_input("Link Materi (Google Drive / YouTube / PDF)")
            tgl = st.date_input("Tanggal Upload")
            
            if st.button("Simpan Materi"):
                execute_query("INSERT INTO materi (judul, link, tanggal) VALUES (?, ?, ?)", (judul, link, str(tgl)))
                st.success("Materi berhasil ditambahkan!")
                
        elif menu_guru == "Daftar Tugas Siswa":
            st.subheader("Tugas yang Dikumpulkan Siswa")
            df_tugas = run_query("SELECT * FROM tugas")
            st.dataframe(df_tugas, use_container_width=True)

    # --- DASHBOARD SISWA ---
    else:
        st.title("👨‍🎓 Dashboard Siswa")
        
        menu_siswa = st.selectbox("Pilih Menu Siswa", ["Lihat Materi", "Kumpul Tugas"])
        
        if menu_siswa == "Lihat Materi":
            st.subheader("Materi Pelajaran")
            df_materi = run_query("SELECT * FROM materi")
            st.dataframe(df_materi, use_container_width=True)
                
        elif menu_siswa == "Kumpul Tugas":
            st.subheader("Form Pengumpulan Tugas")
            judul_tugas = st.text_input("Judul Tugas")
            link_tugas = st.text_input("Link Tugas (Google Drive / GitHub / PDF)")
            
            if st.button("Kirim Tugas"):
                execute_query("INSERT INTO tugas (nama_siswa, judul_tugas, link_tugas, nilai) VALUES (?, ?, ?, 'Belum Dinilai')", 
                              (nama, judul_tugas, link_tugas))
                st.success("Tugas Anda berhasil terkirim!")