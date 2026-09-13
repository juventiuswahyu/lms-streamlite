import streamlit as st
import pandas as pd
import sqlite3
import base64
import os

# -----------------------------------------------------------------------------
# 1. KONFIGURASI DAN KONEKSI DATABASE LOKAL (SQLITE)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="LMS Sertifikasi Bismind Universitas Karangturi Semarang", page_icon="🎓", layout="wide")

DB_FILE = "lms_database.db"

def init_db():
    """Membuat database dan direktori upload jika belum ada"""
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
        
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Buat Tabel Users
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            nama TEXT,
            role TEXT,
            status TEXT DEFAULT 'Aktif'
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
    
    # Buat Tabel Progress Siswa
    c.execute('''
        CREATE TABLE IF NOT EXISTS progress_siswa (
            username TEXT,
            materi_id INTEGER,
            PRIMARY KEY (username, materi_id)
        )
    ''')
    
    # Buat Tabel Tugas (Ditambahkan tipe pengumpulan)
    c.execute('''
        CREATE TABLE IF NOT EXISTS tugas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_siswa TEXT,
            judul_tugas TEXT,
            link_tugas TEXT,
            nilai TEXT
        )
    ''')
    
    try:
        c.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'Aktif'")
    except:
        pass

    # Inisialisasi Akun Bawaan
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users VALUES ('guru1', '12345', 'Pak Budi (Super Admin)', 'Super Admin', 'Aktif')")
        c.execute("INSERT INTO users VALUES ('guru2', '12345', 'Pak Pengajar', 'Guru', 'Aktif')")
        c.execute("INSERT INTO users VALUES ('siswa1', '12345', 'Siti', 'Siswa', 'Aktif')")
        c.execute("INSERT INTO materi (judul, link, tanggal) VALUES ('Dasar-Dasar Barista', 'https://drive.google.com', '2026-09-13')")
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
    """Fungsi untuk menambah/mengubah/menghapus data"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

def get_image_base64(path):
    """Fungsi pembantu untuk meletakkan gambar di tengah menggunakan HTML"""
    try:
        with open(path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        return f"data:image/png;base64,{encoded_string}"
    except:
        return None

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
    
    img_base64 = get_image_base64("Logo.png")
    
    title_html = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@800;900&display=swap');
        .main-title {
            font-family: 'Montserrat', 'Arial Black', sans-serif;
            font-size: 30px;
            font-weight: 900;
            color: #111111;
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-top: 15px;
            margin-bottom: 5px;
            line-height: 1.3;
        }
    </style>
    """
    st.markdown(title_html, unsafe_allow_html=True)
    
    if img_base64:
        st.markdown(
            f"""
            <div style="text-align: center;">
                <img src="{img_base64}" width="260" style="margin-bottom: 10px;">
                <div class="main-title">
                    LMS SERTIFIKASI BISMIND<br>UNIVERSITAS KARANGTURI SEMARANG
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div style="text-align: center;">
                <h1 style="font-size: 80px; margin-bottom: 0;">🎓</h1>
                <div class="main-title">
                    LMS SERTIFIKASI BISMIND<br>UNIVERSITAS KARANGTURI SEMARANG
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    st.divider()
    
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Daftar Akun Siswa"])
    
    # --- TAB 1: LOGIN ---
    with tab1:
        st.subheader("Masuk ke Sistem")
        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type="password")
        
        if st.button("Masuk"):
            df_users = run_query("SELECT * FROM users WHERE username=? AND password=?", (username_input, password_input))
            
            if not df_users.empty:
                user_status = df_users.iloc[0].get('status', 'Aktif')
                if user_status == 'Terkunci':
                    st.error("🔒 Akun Anda masih terkunci / menunggu persetujuan dari Guru. Silakan hubungi pengajar Anda.")
                else:
                    st.session_state['logged_in'] = True
                    st.session_state['user_info'] = df_users.iloc[0].to_dict()
                    st.success("Login Berhasil!")
                    st.rerun()
            else:
                st.error("Username atau Password salah!")

    # --- TAB 2: REGISTRASI SISWA ---
    with tab2:
        st.subheader("Pendaftaran Akun Siswa Baru")
        st.info("ℹ️ Setelah mendaftar, akun Anda perlu disetujui terlebih dahulu oleh Guru/Admin sebelum dapat digunakan untuk login.")
        reg_username = st.text_input("Buat Username Baru")
        reg_password = st.text_input("Buat Password Baru", type="password")
        reg_nama = st.text_input("Nama Lengkap Siswa")
        
        if st.button("Daftar Sekarang"):
            if reg_username and reg_password and reg_nama:
                try:
                    execute_query("INSERT INTO users VALUES (?, ?, ?, 'Siswa', 'Terkunci')", (reg_username, reg_password, reg_nama))
                    st.success("🎉 Pendaftaran berhasil! Akun Anda sedang menunggu persetujuan dari Guru. Silakan beri tahu Guru Anda.")
                except Exception as e:
                    st.error("Username sudah digunakan, cari username lain.")
            else:
                st.warning("Lengkapi semua form pendaftaran!")

# -----------------------------------------------------------------------------
# 4. DASHBOARD UTAMA (SETELAH LOGIN)
# -----------------------------------------------------------------------------
else:
    username = st.session_state['user_info'].get('username', '')
    role = st.session_state['user_info'].get('role', 'Siswa')
    nama = st.session_state['user_info'].get('nama', 'User')
    
    is_super_admin = (username == 'guru1') or (role == 'Super Admin')
    
    st.sidebar.title(f"Selamat Datang, {nama}!")
    st.sidebar.write(f"**Hak Akses:** {'Super Admin 🔑' if is_super_admin else role}")
    
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['user_info'] = {}
        st.rerun()
        
    # --- DASHBOARD GURU & SUPER ADMIN ---
    if 'guru' in str(role).lower() or is_super_admin:
        st.title("👨‍🏫 Dashboard Pengajar / Admin")
        st.caption("LMS Sertifikasi Bismind - Universitas Karangturi Semarang")
        
        menu_options = ["Daftar Materi", "Tambah Materi", "🔒 Kelola & Kunci User"]
        if is_super_admin:
            menu_options.extend(["✏️ Edit Manual Materi", "🗑️ Hapus Materi", "Daftar Tugas Siswa"])
        else:
            menu_options.append("Daftar Tugas Siswa")
            
        menu_guru = st.selectbox("Pilih Menu", menu_options)
        
        if menu_guru == "Daftar Materi":
            st.subheader("Materi Pelajaran Aktif")
            df_materi = run_query("SELECT id, judul, link, tanggal FROM materi")
            
            if df_materi.empty:
                st.info("Belum ada materi.")
            else:
                # Bersihkan teks judul
                df_materi['judul'] = df_materi['judul'].apply(lambda x: str(x).replace('*', '').strip())
                st.dataframe(
                    df_materi[['judul', 'link', 'tanggal']], 
                    hide_index=True, 
                    use_container_width=True,
                    column_config={
                        "link": st.column_config.LinkColumn("Link Materi"),
                        "judul": "Judul Pelajaran",
                        "tanggal": "Tanggal Upload"
                    }
                )
            
        elif menu_guru == "Tambah Materi":
            st.subheader("Tambah Materi Baru")
            judul = st.text_input("Judul Materi")
            link = st.text_input("Link Materi (URL Google Drive / Youtube / PDF)")
            tgl = st.date_input("Tanggal Upload")
            
            if st.button("Simpan Materi"):
                if judul:
                    clean_judul = judul.replace('*', '').strip()
                    execute_query("INSERT INTO materi (judul, link, tanggal) VALUES (?, ?, ?)", (clean_judul, link, str(tgl)))
                    st.success("Materi berhasil ditambahkan!")
                    st.rerun()
                else:
                    st.warning("Judul materi wajib diisi!")

        elif menu_guru == "🔒 Kelola & Kunci User":
            st.subheader("👥 Kelola Status & Persetujuan Akun Siswa")
            st.caption("Guru dapat mengaktifkan (menyetujui), mengunci, atau menghapus akun siswa di bawah ini.")
            
            df_users = run_query("SELECT username, nama, role, status FROM users WHERE role='Siswa'")
            
            if df_users.empty:
                st.info("Belum ada akun siswa yang mendaftar.")
            else:
                for idx, u_row in df_users.iterrows():
                    u_user = u_row['username']
                    u_nama = u_row['nama']
                    u_status = u_row['status']
                    
                    col_user, col_status_badge, col_act1, col_act2 = st.columns([3, 2, 2, 2])
                    
                    with col_user:
                        st.write(f"**{u_nama}** (`{u_user}`)")
                    
                    with col_status_badge:
                        if u_status == 'Aktif':
                            st.success("🟢 Aktif")
                        else:
                            st.error("🔒 Terkunci / Pending")
                            
                    with col_act1:
                        if u_status == 'Terkunci':
                            if st.button("✅ Setujui / Buka", key=f"app_{u_user}"):
                                execute_query("UPDATE users SET status='Aktif' WHERE username=?", (u_user,))
                                st.success(f"Akun {u_nama} berhasil diaktifkan!")
                                st.rerun()
                        else:
                            if st.button("🔒 Kunci Akun", key=f"lock_{u_user}"):
                                execute_query("UPDATE users SET status='Terkunci' WHERE username=?", (u_user,))
                                st.warning(f"Akun {u_nama} telah dikunci.")
                                st.rerun()
                                
                    with col_act2:
                        if st.button("🗑️ Hapus", key=f"del_{u_user}"):
                            execute_query("DELETE FROM users WHERE username=?", (u_user,))
                            st.success(f"Akun {u_nama} berhasil dihapus!")
                            st.rerun()
                            
                    st.divider()

        elif menu_guru == "✏️ Edit Manual Materi" and is_super_admin:
            st.subheader("✏️ Edit Manual Data Materi (Super Admin)")
            df_materi = run_query("SELECT id, judul, link, tanggal FROM materi")
            
            edited_df = st.data_editor(
                df_materi, 
                hide_index=True, 
                use_container_width=True,
                disabled=["id"],
                key="editor_materi"
            )
            
            if st.button("Simpan Perubahan Tabel"):
                conn = sqlite3.connect(DB_FILE)
                edited_df.to_sql("materi", conn, if_exists="replace", index=False)
                conn.close()
                st.success("Perubahan data materi berhasil disimpan!")
                st.rerun()

        elif menu_guru == "🗑️ Hapus Materi" and is_super_admin:
            st.subheader("🗑️ Hapus Materi Pelajaran")
            df_materi = run_query("SELECT * FROM materi")
            
            if df_materi.empty:
                st.info("Belum ada materi.")
            else:
                materi_list = df_materi['judul'].tolist()
                pilihan_materi = st.selectbox("Pilih Materi yang Akan Dihapus", materi_list)
                selected_row = df_materi[df_materi['judul'] == pilihan_materi].iloc[0]
                
                if st.button(f"Hapus Permanen '{pilihan_materi}'", type="primary"):
                    execute_query("DELETE FROM materi WHERE id=?", (int(selected_row['id']),))
                    execute_query("DELETE FROM progress_siswa WHERE materi_id=?", (int(selected_row['id']),))
                    st.success("Materi berhasil dihapus!")
                    st.rerun()
                
        elif menu_guru == "Daftar Tugas Siswa":
            st.subheader("Tugas yang Dikumpulkan Siswa")
            df_tugas = run_query("SELECT nama_siswa, judul_tugas, link_tugas, nilai FROM tugas")
            
            if df_tugas.empty:
                st.info("Belum ada tugas yang dikumpulkan siswa.")
            else:
                st.dataframe(
                    df_tugas, 
                    hide_index=True, 
                    use_container_width=True,
                    column_config={
                        "link_tugas": st.column_config.LinkColumn("Link / File Tugas"),
                        "nama_siswa": "Nama Siswa",
                        "judul_tugas": "Judul Tugas",
                        "nilai": "Status/Nilai"
                    }
                )

    # --- DASHBOARD SISWA ---
    else:
        st.title("👨‍🎓 Dashboard Siswa")
        st.caption("LMS Sertifikasi Bismind - Universitas Karangturi Semarang")
        
        menu_siswa = st.selectbox("Pilih Menu Siswa", ["Lihat Materi & Progress", "Kumpul Tugas"])
        
        if menu_siswa == "Lihat Materi & Progress":
            st.subheader("📚 Materi Pelajaran & Progress Belajar")
            
            df_materi = run_query("SELECT id, judul, link, tanggal FROM materi")
            df_progress = run_query("SELECT materi_id FROM progress_siswa WHERE username=?", (username,))
            completed_ids = set(df_progress['materi_id'].tolist()) if not df_progress.empty else set()
            
            total_materi = len(df_materi)
            completed_count = len(completed_ids.intersection(set(df_materi['id'].tolist()))) if total_materi > 0 else 0
            
            progress_percent = int((completed_count / total_materi) * 100) if total_materi > 0 else 0
            
            st.markdown(f"### 📈 Progress Sertifikasi Anda: **{progress_percent}%** ({completed_count}/{total_materi} Materi Selesai)")
            st.progress(progress_percent / 100)
            st.divider()
            
            if df_materi.empty:
                st.info("Belum ada materi pelajaran yang tersedia.")
            else:
                st.write("#### Daftar Modul Pelajaran:")
                for idx, row in df_materi.iterrows():
                    m_id = row['id']
                    # Pembersihan karakter bintang agar selalu tercetak bold tanpa cacat
                    m_judul = str(row['judul']).replace('*', '').strip()
                    m_link = row['link']
                    m_tgl = row['tanggal']
                    
                    is_completed = m_id in completed_ids
                    
                    col_status, col_info, col_link = st.columns([1, 4, 2])
                    
                    with col_status:
                        check = st.checkbox("Selesai", value=is_completed, key=f"check_{m_id}_{idx}")
                        if check != is_completed:
                            if check:
                                execute_query("INSERT OR IGNORE INTO progress_siswa VALUES (?, ?)", (username, m_id))
                            else:
                                execute_query("DELETE FROM progress_siswa WHERE username=? AND materi_id=?", (username, m_id))
                            st.rerun()
                            
                    with col_info:
                        if is_completed:
                            st.markdown(f"~~**{m_judul}**~~ ✅ *(Selesai)*")
                        else:
                            st.markdown(f"**{m_judul}**")
                        st.caption(f"Diunggah: {m_tgl}")
                        
                    with col_link:
                        if m_link and str(m_link).strip() != "":
                            st.link_button("📖 Buka Materi", m_link)
                        else:
                            st.caption("Link belum tersedia")
                    
                    st.divider()
                
        elif menu_siswa == "Kumpul Tugas":
            st.subheader("📤 Form Pengumpulan Tugas")
            judul_tugas = st.text_input("Judul Tugas / Modul")
            
            metode_kumpul = st.radio("Pilih Metode Pengumpulan:", ["Upload File Dokumen (PDF/Word/Gambar/Zip)", "Kirim Link (Google Drive / GitHub / URL)"])
            
            link_final = ""
            
            if metode_kumpul == "Upload File Dokumen (PDF/Word/Gambar/Zip)":
                uploaded_file = st.file_uploader("Pilih File Tugas", type=['pdf', 'docx', 'doc', 'jpg', 'png', 'zip', 'rar', 'pptx'])
                if uploaded_file is not None:
                    file_path = os.path.join("uploads", f"{username}_{uploaded_file.name}")
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    link_final = file_path
            else:
                link_final = st.text_input("Masukkan URL / Link Tugas")

            if st.button("Kirim Tugas Sekarang"):
                if judul_tugas and link_final:
                    execute_query("INSERT INTO tugas (nama_siswa, judul_tugas, link_tugas, nilai) VALUES (?, ?, ?, 'Belum Dinilai')", 
                                  (nama, judul_tugas, link_final))
                    st.success("🎉 Tugas Anda berhasil terkirim!")
                else:
                    st.warning("Mohon isi judul tugas dan upload file atau sertakan link tugas Anda!")
