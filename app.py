import random
from dataclasses import dataclass
from typing import Any, Dict, List

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Integer Knapsack - Program Dinamis Maju",
    layout="wide",
)

NEG_INF = -10**12


@dataclass
class Item:
    name: str
    weight: int
    profit: int


def normalize_items(df: pd.DataFrame) -> List[Item]:
    items: List[Item] = []
    for idx, row in df.iterrows():
        raw_name = row.get("Nama Barang", f"Barang {idx + 1}")
        name = str(raw_name).strip() if str(raw_name).strip() else f"Barang {idx + 1}"
        try:
            weight = int(row.get("Berat", 0))
            profit = int(row.get("Keuntungan", 0))
        except Exception as exc:
            raise ValueError("Berat dan keuntungan harus berupa bilangan bulat.") from exc

        if weight <= 0:
            raise ValueError(f"Berat untuk {name} harus lebih dari 0.")
        if profit < 0:
            raise ValueError(f"Keuntungan untuk {name} tidak boleh negatif.")

        items.append(Item(name=name, weight=weight, profit=profit))

    return items


def auto_generate_items(
    n_items: int,
    capacity: int,
    min_weight: int,
    max_weight: int,
    min_profit: int,
    max_profit: int,
    seed: int,
) -> List[Item]:
    rng = random.Random(seed)
    min_weight = max(1, int(min_weight))
    max_weight = max(min_weight, int(max_weight))
    max_weight = min(max_weight, max(1, int(capacity)))
    min_profit = max(0, int(min_profit))
    max_profit = max(min_profit, int(max_profit))

    return [
        Item(
            name=f"Barang {idx + 1}",
            weight=rng.randint(min_weight, max_weight),
            profit=rng.randint(min_profit, max_profit),
        )
        for idx in range(int(n_items))
    ]


def solve_knapsack_forward_dp(items: List[Item], capacity: int) -> Dict[str, Any]:
    """
    Integer knapsack 0/1 dengan program dinamis maju.

    dp[k][y] = keuntungan maksimum menggunakan k barang pertama
               dengan kapasitas maksimum y.
    take[k][y] = True jika barang ke-k diambil pada solusi optimal untuk state (k, y).
    """
    n = len(items)
    dp = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]
    take = [[False for _ in range(capacity + 1)] for _ in range(n + 1)]

    # Menyimpan vektor solusi sementara (x1..xn) untuk setiap state.
    solution_vectors = [
        [[0 for _ in range(n)] for _ in range(capacity + 1)]
        for _ in range(n + 1)
    ]

    stage_tables = []

    for k in range(1, n + 1):
        item = items[k - 1]
        rows = []

        for y in range(capacity + 1):
            not_take_value = dp[k - 1][y]

            if y - item.weight >= 0:
                include_prev = dp[k - 1][y - item.weight]
                take_value = item.profit + include_prev
                take_expr = f"{item.profit} + {include_prev} = {take_value}"
            else:
                take_value = NEG_INF
                take_expr = "-∞"

            # Jika seri, dipilih tidak ambil agar barang hanya diambil bila benar-benar meningkatkan profit.
            if take_value > not_take_value:
                dp[k][y] = take_value
                take[k][y] = True
                vec = solution_vectors[k - 1][y - item.weight].copy()
                vec[k - 1] = 1
                decision = f"Ambil {item.name}"
            else:
                dp[k][y] = not_take_value
                take[k][y] = False
                vec = solution_vectors[k - 1][y].copy()
                decision = f"Tidak ambil {item.name}"

            solution_vectors[k][y] = vec
            rows.append({
                "y": y,
                f"f{k-1}(y)": not_take_value,
                f"p{k} + f{k-1}(y - w{k})": take_expr,
                f"f{k}(y)": dp[k][y],
                "Keputusan": decision,
                "Solusi sementara (x1..xn)": "(" + ", ".join(map(str, vec)) + ")",
            })

        stage_tables.append({
            "stage": k,
            "item": item,
            "formula": rf"f_{k}(y) = \max\{{f_{k-1}(y),\ {item.profit} + f_{k-1}(y - {item.weight})\}}",
            "table": pd.DataFrame(rows),
        })

    selected_vector = solution_vectors[n][capacity]
    selected_items = [item for item, selected in zip(items, selected_vector) if selected == 1]

    return {
        "dp": dp,
        "take": take,
        "solution_vectors": solution_vectors,
        "stage_tables": stage_tables,
        "selected_vector": selected_vector,
        "selected_items": selected_items,
        "total_weight": sum(item.weight for item in selected_items),
        "total_profit": dp[n][capacity],
    }


def make_items_dataframe(items: List[Item]) -> pd.DataFrame:
    return pd.DataFrame([
        {"Barang": item.name, "Berat": item.weight, "Keuntungan": item.profit}
        for item in items
    ])


def make_selected_items_dataframe(selected_items: List[Item]) -> pd.DataFrame:
    return pd.DataFrame([
        {"Barang": item.name, "Berat": item.weight, "Keuntungan": item.profit}
        for item in selected_items
    ])


def make_final_dp_matrix(result: Dict[str, Any], capacity: int) -> pd.DataFrame:
    dp = result["dp"]
    rows = []
    for k in range(len(dp)):
        row = {"Tahap": f"f{k}"}
        for y in range(capacity + 1):
            row[f"y={y}"] = dp[k][y]
        rows.append(row)
    return pd.DataFrame(rows)


def centered_table(df: pd.DataFrame):
    """Styler agar isi dan header tabel tampil rata tengah di Streamlit."""
    return (
        df.style
        .set_properties(**{"text-align": "center"})
        .set_table_styles([
            {"selector": "th", "props": [("text-align", "center")]},
            {"selector": "td", "props": [("text-align", "center")]},
        ])
    )


def show_centered_dataframe(df: pd.DataFrame, *, hide_index: bool = True):
    st.dataframe(centered_table(df), use_container_width=True, hide_index=hide_index)


def default_manual_dataframe(n_items: int) -> pd.DataFrame:
    return pd.DataFrame({
        "Nama Barang": [f"Barang {i + 1}" for i in range(n_items)],
        "Berat": ([2, 3, 1] + [1] * max(0, n_items - 3))[:n_items],
        "Keuntungan": ([65, 80, 30] + [10] * max(0, n_items - 3))[:n_items],
    })


def resize_manual_dataframe(n_items: int):
    default_data = default_manual_dataframe(n_items)
    old_df = st.session_state.get("manual_df", default_data)
    new_df = default_data.copy()

    for i in range(min(len(old_df), n_items)):
        for col in ["Nama Barang", "Berat", "Keuntungan"]:
            if col in old_df.columns:
                new_df.loc[i, col] = old_df.loc[i, col]

    st.session_state.manual_df = new_df


# =========================================================
# UI
# =========================================================

st.title("Integer Knapsack dengan Program Dinamis Maju")
st.caption("Simulasi tahap demi tahap untuk knapsack 0/1 menggunakan tabel program dinamis.")

with st.sidebar:
    st.header("Mode Input")
    mode = st.radio("Pilih mode", ["Manual", "Generate otomatis"])

    st.header("Kapasitas Knapsack")
    capacity_input = st.number_input("Kapasitas maksimum M", min_value=1, max_value=500, value=5, step=1)
    capacity_input = int(capacity_input)

    current_preview_df = None

    if mode == "Generate otomatis":
        st.header("Pengaturan Generator")
        n_items = st.slider("Jumlah barang", min_value=2, max_value=15, value=5)
        min_weight = st.number_input("Berat minimum", min_value=1, max_value=100, value=1, step=1)
        max_weight = st.number_input(
            "Berat maksimum",
            min_value=1,
            max_value=100,
            value=max(1, min(10, capacity_input)),
            step=1,
        )
        min_profit = st.number_input("Keuntungan minimum", min_value=0, max_value=1000, value=10, step=1)
        max_profit = st.number_input("Keuntungan maksimum", min_value=1, max_value=1000, value=100, step=1)
        seed = st.number_input("Seed random", min_value=0, max_value=999999, value=42, step=1)

        if "generated_items" not in st.session_state:
            st.session_state.generated_items = auto_generate_items(
                int(n_items), capacity_input, int(min_weight), int(max_weight),
                int(min_profit), int(max_profit), int(seed)
            )

        st.info("Data random tidak berubah otomatis saat parameter diubah. Klik tombol Generate kasus untuk membuat data baru.")

        if st.button("Generate kasus", use_container_width=True):
            st.session_state.generated_items = auto_generate_items(
                int(n_items), capacity_input, int(min_weight), int(max_weight),
                int(min_profit), int(max_profit), int(seed)
            )
            st.session_state.pop("calculated_problem", None)
            st.session_state.stage_index = 0
            st.success("Kasus random baru berhasil dibuat.")

        current_items = st.session_state.generated_items
        current_preview_df = make_items_dataframe(current_items)

    else:
        st.header("Input Manual")
        n_items = st.number_input("Jumlah barang", min_value=1, max_value=30, value=3, step=1)
        n_items = int(n_items)

        if "manual_n_items" not in st.session_state:
            st.session_state.manual_n_items = n_items
            resize_manual_dataframe(n_items)

        if st.session_state.manual_n_items != n_items:
            st.session_state.manual_n_items = n_items
            resize_manual_dataframe(n_items)
            st.session_state.pop("calculated_problem", None)
            st.session_state.stage_index = 0

        st.write("Masukkan berat dan keuntungan setiap barang:")
        edited_df = st.data_editor(
            st.session_state.manual_df,
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            column_config={
                "Nama Barang": st.column_config.TextColumn("Nama Barang"),
                "Berat": st.column_config.NumberColumn("Berat", min_value=1, step=1),
                "Keuntungan": st.column_config.NumberColumn("Keuntungan", min_value=0, step=1),
            },
        )
        st.session_state.manual_df = edited_df.copy()
        current_preview_df = edited_df.copy()
        st.info("Perubahan input manual tidak dihitung otomatis. Klik tombol Hitung solusi untuk memperbarui hasil.")

    st.divider()
    hitung_clicked = st.button("Hitung solusi", type="primary", use_container_width=True)

    if hitung_clicked:
        try:
            if mode == "Manual":
                items_to_solve = normalize_items(st.session_state.manual_df)
            else:
                items_to_solve = list(st.session_state.generated_items)

            st.session_state.calculated_problem = {
                "mode": mode,
                "capacity": capacity_input,
                "items": items_to_solve,
            }
            st.session_state.stage_index = 0
            st.success("Perhitungan berhasil dijalankan.")
        except ValueError as exc:
            st.error(str(exc))
            st.stop()


if current_preview_df is not None and "calculated_problem" not in st.session_state:
    st.subheader("Data yang Siap Dihitung")
    st.write(f"**Mode:** {mode}")
    st.write(f"**Kapasitas maksimum M:** {capacity_input}")
    show_centered_dataframe(current_preview_df)
    st.info("Klik tombol **Hitung solusi** di sidebar untuk menjalankan program dinamis.")
    st.stop()

if "calculated_problem" not in st.session_state:
    st.info("Atur data pada sidebar, lalu klik **Hitung solusi**.")
    st.stop()

problem = st.session_state.calculated_problem
items = problem["items"]
capacity = int(problem["capacity"])
result = solve_knapsack_forward_dp(items, capacity)

st.subheader("Data Permasalahan yang Dihitung")
st.write(f"**Mode:** {problem['mode']}")
st.write(f"**Jumlah barang:** {len(items)}")
st.write(f"**Kapasitas maksimum M:** {capacity}")
show_centered_dataframe(make_items_dataframe(items))

if capacity > 200 or len(items) > 20:
    st.info("Catatan: kapasitas atau jumlah barang besar akan membuat tabel lebih panjang.")

st.divider()
st.subheader("Konsep Perhitungan Program Dinamis")
st.markdown(
    """
Aplikasi ini menggunakan pendekatan **program dinamis maju**.

- `k` = tahap, yaitu barang ke-k yang sedang dipertimbangkan.
- `y` = kapasitas knapsack yang sedang diuji, dari 0 sampai M.
- `f_k(y)` = keuntungan maksimum jika hanya mempertimbangkan k barang pertama dengan kapasitas y.
- Setiap barang hanya punya dua keputusan: **diambil** atau **tidak diambil**.
"""
)
st.latex(r"f_k(y) = \max\{f_{k-1}(y),\ p_k + f_{k-1}(y-w_k)\}")
st.markdown("Jika `y - w_k < 0`, berarti barang ke-k tidak muat pada kapasitas tersebut. Pada tabel, kondisi itu ditulis sebagai `-∞`.")

with st.expander("Lihat matriks akhir seluruh tahap"):
    show_centered_dataframe(make_final_dp_matrix(result, capacity))

st.divider()
st.subheader("Tabel Program Dinamis per Tahap")

view_mode = st.radio("Mode tampilan tahap", ["Tab semua tahap", "Navigasi tahap"], horizontal=True)
stage_tables = result["stage_tables"]

if view_mode == "Tab semua tahap":
    tabs = st.tabs([f"Tahap {stage['stage']}" for stage in stage_tables])
    for tab, stage in zip(tabs, stage_tables):
        with tab:
            k = stage["stage"]
            item = stage["item"]
            st.markdown(f"### Tahap {k}: Mempertimbangkan {item.name}")
            st.write(f"Berat `w{k}` = **{item.weight}**, keuntungan `p{k}` = **{item.profit}**")
            st.latex(stage["formula"])
            show_centered_dataframe(stage["table"])
else:
    if "stage_index" not in st.session_state:
        st.session_state.stage_index = 0
    if st.session_state.stage_index >= len(stage_tables):
        st.session_state.stage_index = len(stage_tables) - 1

    nav1, nav2, nav3, nav4, nav5 = st.columns([1, 1, 2, 1, 1])
    with nav1:
        if st.button("⏮ Awal", use_container_width=True, disabled=st.session_state.stage_index == 0):
            st.session_state.stage_index = 0
            st.rerun()
    with nav2:
        if st.button("◀ Sebelumnya", use_container_width=True, disabled=st.session_state.stage_index == 0):
            st.session_state.stage_index -= 1
            st.rerun()
    with nav3:
        st.markdown(
            f"<div style='text-align:center; padding-top:0.5rem;'><b>Tahap {st.session_state.stage_index + 1} dari {len(stage_tables)}</b></div>",
            unsafe_allow_html=True,
        )
    with nav4:
        if st.button("Berikutnya ▶", use_container_width=True, disabled=st.session_state.stage_index == len(stage_tables) - 1):
            st.session_state.stage_index += 1
            st.rerun()
    with nav5:
        if st.button("Akhir ⏭", use_container_width=True, disabled=st.session_state.stage_index == len(stage_tables) - 1):
            st.session_state.stage_index = len(stage_tables) - 1
            st.rerun()

    stage = stage_tables[st.session_state.stage_index]
    k = stage["stage"]
    item = stage["item"]
    st.markdown(f"### Tahap {k}: Mempertimbangkan {item.name}")
    st.write(f"Berat `w{k}` = **{item.weight}**, keuntungan `p{k}` = **{item.profit}**")
    st.latex(stage["formula"])
    show_centered_dataframe(stage["table"])

st.divider()
st.subheader("Ringkasan Solusi Optimal")

metric_col1, metric_col2, metric_col3 = st.columns(3)
with metric_col1:
    st.metric("Keuntungan maksimum", result["total_profit"])
with metric_col2:
    st.metric("Total berat terpilih", result["total_weight"])
with metric_col3:
    st.metric("Kapasitas maksimum", capacity)

st.write("**Vektor solusi:**")
st.code("(" + ", ".join(map(str, result["selected_vector"])) + ")")

selected_df = make_selected_items_dataframe(result["selected_items"])
if selected_df.empty:
    st.info("Tidak ada barang yang dipilih.")
else:
    st.write("**Barang yang diambil:**")
    show_centered_dataframe(selected_df)

st.divider()
st.subheader("Penjelasan Hasil Akhir")

if result["selected_items"]:
    item_names = ", ".join(item.name for item in result["selected_items"])
    st.markdown(
        f"""
Solusi optimal diperoleh dengan memilih **{item_names}**.

Total berat barang terpilih adalah **{result['total_weight']}**, sehingga tidak melebihi kapasitas maksimum **{capacity}**.

Total keuntungan yang diperoleh adalah **{result['total_profit']}**.
"""
    )
else:
    st.markdown(f"Tidak ada barang yang dipilih. Keuntungan maksimum adalah **{result['total_profit']}**.")

st.caption("Catatan: aplikasi ini menyelesaikan integer knapsack 0/1, sehingga setiap barang hanya boleh dipilih satu kali atau tidak dipilih sama sekali.")
