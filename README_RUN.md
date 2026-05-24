# Integer Knapsack dengan Program Dinamis Maju

Aplikasi Streamlit ini digunakan untuk mensimulasikan penyelesaian masalah integer knapsack 0/1 dengan pendekatan program dinamis maju.

## Fitur

- Input manual jumlah barang, berat, keuntungan, dan kapasitas maksimum.
- Generate kasus otomatis dengan jumlah barang dan seed random.
- Menampilkan tabel program dinamis untuk setiap tahap.
- Menampilkan rumus pada setiap tahap.
- Menampilkan solusi optimal, barang yang diambil, total berat, dan keuntungan maksimum.
- Menampilkan matriks akhir semua nilai `f_k(y)`.

## Cara Menjalankan di Windows

```bash
cd integer_knapsack_dp_app
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Cara Menjalankan di Mac/Linux

```bash
cd integer_knapsack_dp_app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Setelah dijalankan, buka browser ke:

```text
http://localhost:8501
```

## Catatan

Aplikasi ini menggunakan knapsack 0/1. Artinya, setiap barang hanya dapat dipilih satu kali atau tidak dipilih.
