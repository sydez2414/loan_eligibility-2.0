import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Loan Eligibility Tool", layout="centered")

st.title("🏡 Loan Eligibility Matcher - Ejen Hartanah")
st.caption("Versi lengkap dengan kiraan ansuran dan DSR sebenar berdasarkan kadar bank & sokongan edit kadar dari Excel")

st.markdown("---")

st.subheader("🔍 Maklumat Kewangan Buyer")

property_price = st.number_input("Harga Hartanah (RM)", min_value=50000, value=500000, step=10000)
margin = st.slider("Margin Pembiayaan (%)", 70, 100, 90)
tenure = st.slider("Tempoh Pinjaman (Tahun)", 5, 35, 30)

loan_amount = property_price * margin / 100

col1, col2 = st.columns(2)
with col1:
    income = st.number_input("Gaji Bersih Bulanan (RM)", min_value=1000, value=5000, step=100)
with col2:
    commitment = st.number_input("Komitmen Bulanan (RM)", min_value=0, value=1500, step=100)

st.markdown("---")

st.subheader("🏦 Keputusan Kelayakan Bank")

# Muat naik kadar faedah dari Excel
try:
    bank_df = pd.read_excel("bank_rates.xlsx")
except:
    st.error("❌ Gagal baca fail 'bank_rates.xlsx'. Pastikan fail wujud & ada kolum 'Bank', 'Rate', 'NDI', dan 'DSR Max (%)'.")
    bank_df = pd.DataFrame(columns=["Bank", "Rate", "NDI", "DSR Max (%)"])

# Fungsi kira installment
def calculate_installment(P, annual_rate, years):
    r = (annual_rate / 100) / 12
    n = years * 12
    if r == 0:
        return P / n
    return P * r * (1 + r) ** n / ((1 + r) ** n - 1)

# Kira kelayakan maksimum berdasarkan baki gaji selepas komitmen (tanpa ambil kira installment baru)
available_income = income - commitment
max_monthly_installment = available_income * 0.70  # anggap DSR limit 70% pada baki ini

# Kira kelayakan kasar
est_interest = 0.032 / 12  # 3.2% default (boleh ubah ikut bank nanti)
months = tenure * 12
if est_interest > 0:
    max_loan = max_monthly_installment * ((1 + est_interest) ** months - 1) / (est_interest * (1 + est_interest) ** months)
else:
    max_loan = max_monthly_installment * months

st.info(f"💡 Anggaran kasar kelayakan pinjaman berdasarkan baki gaji (tanpa ansuran baru): **RM{max_loan:,.2f}**")

# Simulasi bank-bank
results = []
for index, row in bank_df.iterrows():
    bank = row["Bank"]
    rate = row["Rate"]
    ndi = row["NDI"] if not pd.isna(row["NDI"]) else 0
    max_dsr = row["DSR Max (%)"] if not pd.isna(row["DSR Max (%)"]) else 70

    installment = calculate_installment(loan_amount, rate, tenure)
    total_commitment = commitment + installment + ndi
    dsr = (total_commitment / income) * 100

    result = {
        "Bank": bank,
        "Interest Rate (%)": rate,
        "Installment (RM)": round(installment, 2),
        "NDI (RM)": ndi,
        "Total Commitment (RM)": round(total_commitment, 2),
        "DSR (%)": round(dsr, 2),
        "Status": "APPROVE" if dsr <= max_dsr else "DECLINE"
    }
    results.append(result)

# Papar hasil
for res in results:
    status_color = "✅" if res["Status"] == "APPROVE" else "❌"
    st.markdown(f"**{status_color} {res['Bank']}**  ")
    st.write(f"Kadar Faedah: {res['Interest Rate (%)']}%  |  Ansuran: RM{res['Installment (RM)']:,}  |  NDI: RM{res['NDI (RM)']}  |  DSR: {res['DSR (%)']:.2f}% → **{res['Status']}**")
    st.markdown("---")

st.caption("💡 Nota: Kadar, NDI & DSR Max boleh diubah dalam fail 'bank_rates.xlsx'. Pastikan fail tersebut ada dalam folder sama dengan app ini.")
