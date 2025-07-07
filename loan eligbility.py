import streamlit as st
import pandas as pd
import math
import datetime
import qrcode
from io import BytesIO

st.set_page_config(page_title="Loan Eligibility Checker", layout="wide")

st.markdown("""
    <style>
        .main-title {
            font-size: 36px;
            font-weight: bold;
            color: #2c3e50;
        }
        .section-header {
            font-size: 22px;
            font-weight: 600;
            color: #2980b9;
            margin-top: 1em;
        }
        .stTextInput>label, .stNumberInput>label, .stSlider>label {
            font-weight: 500;
        }
        .stDataFrame, .stMarkdown {
            font-size: 16px;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>🏡 Loan Eligibility Checker</div>", unsafe_allow_html=True)
st.caption("Alat bantu profesional untuk ejen hartanah menilai kelayakan pembiayaan pembeli berdasarkan DSR sebenar dan kadar bank semasa.")

# Maklumat Ejen Tetap
agent_name = "Syed Fadzil"
agent_id = "PEA2641"
agent_phone = "+60133632414"
wa_link = f"https://wa.me/{agent_phone[1:]}"

st.markdown("<div class='section-header'>👤 Maklumat Pembeli</div>", unsafe_allow_html=True)

client_name = st.text_input("Nama Penuh")
client_email = st.text_input("Alamat Emel")
client_phone = st.text_input("No. Telefon")

st.markdown("<div class='section-header'>🔍 Maklumat Kewangan Buyer</div>", unsafe_allow_html=True)

property_price = st.number_input("Harga Hartanah (RM)", min_value=50000, value=500000, step=10000)
margin = st.slider("Margin Pembiayaan (%)", 70, 100, 90)
tenure = st.slider("Tempoh Pinjaman (Tahun)", 5, 35, 30)

loan_amount = property_price * margin / 100

col1, col2 = st.columns(2)
with col1:
    income = st.number_input("Gaji Bersih Bulanan (RM)", min_value=1000, value=5000, step=100)
with col2:
    commitment = st.number_input("Komitmen Bulanan (RM)", min_value=0, value=1500, step=100)

st.markdown("<div class='section-header'>🏦 Keputusan Kelayakan Bank</div>", unsafe_allow_html=True)

try:
    bank_df = pd.read_excel("bank_rates.xlsx")
except:
    st.error("❌ Gagal baca fail 'bank_rates.xlsx'. Pastikan fail wujud & ada kolum 'Bank', 'Rate', 'NDI', dan 'DSR Max (%)'.")
    bank_df = pd.DataFrame(columns=["Bank", "Rate", "NDI", "DSR Max (%)"])

def calculate_installment(P, annual_rate, years):
    r = (annual_rate / 100) / 12
    n = years * 12
    if r == 0:
        return P / n
    return P * r * (1 + r) ** n / ((1 + r) ** n - 1)

available_income = income - commitment
max_monthly_installment = available_income * 0.70

est_interest = 0.032 / 12
months = tenure * 12
if est_interest > 0:
    max_loan = max_monthly_installment * ((1 + est_interest) ** months - 1) / (est_interest * (1 + est_interest) ** months)
else:
    max_loan = max_monthly_installment * months

st.success(f"💡 Anggaran kasar kelayakan pinjaman berdasarkan baki gaji (tanpa ansuran baru): RM{max_loan:,.2f}")

results = []
for index, row in bank_df.iterrows():
    bank = f"Bank {chr(65 + index)}"
    rate = row["Rate"]
    ndi = row["NDI"] if not pd.isna(row["NDI"]) else 0
    max_dsr = row["DSR Max (%)"] if not pd.isna(row["DSR Max (%)"]) else 70

    installment = calculate_installment(loan_amount, rate, tenure)
    total_commitment = commitment + installment + ndi
    dsr = (total_commitment / income) * 100
    status = "✅ LULUS" if dsr <= max_dsr else "❌ TOLAK"

    result = {
        "🏦 Bank": bank,
        "Kadar (%)": rate,
        "Ansuran (RM)": round(installment, 2),
        "DSR (%)": round(dsr, 2),
        "Status": status
    }
    results.append(result)

if results:
    df_result = pd.DataFrame(results)
    st.dataframe(df_result, use_container_width=True)

    if client_name or client_email or client_phone:
        df_result.insert(0, "Nama", client_name)
        df_result.insert(1, "Emel", client_email)
        df_result.insert(2, "Telefon", client_phone)
        df_result.insert(3, "Tarikh", datetime.date.today().strftime("%Y-%m-%d"))
        df_result.insert(4, "Ejen", agent_name)
        df_result.insert(5, "No Ejen", agent_id)

    st.download_button(
        label="📄 Muat Turun Hasil Sebagai CSV",
        data=df_result.to_csv(index=False).encode('utf-8'),
        file_name="keputusan_kelayakan.csv",
        mime="text/csv"
    )

    st.markdown("<div class='section-header'>📞 Hubungi Ejen Anda</div>", unsafe_allow_html=True)
    st.write(f"**Nama:** {agent_name}  ")
    st.write(f"**No Telefon:** {agent_phone}  ")
    st.write(f"**ID Ejen:** {agent_id}  ")

    # QR WhatsApp
    qr = qrcode.make(wa_link)
    buf = BytesIO()
    qr.save(buf)
    st.image(buf.getvalue(), caption="Imbas untuk WhatsApp Ejen", width=180)

st.markdown("""
<div style='margin-top: 2em; font-size: 14px; color: gray;'>
⚠️ <strong>Penafian:</strong> Kelulusan akhir pinjaman tertakluk kepada dasar dan penilaian dalaman pihak bank. Aplikasi ini dibangunkan untuk membantu ejen hartanah membuat tapisan awal berkenaan kelayakan pembeli secara profesional.
</div>
""", unsafe_allow_html=True)
