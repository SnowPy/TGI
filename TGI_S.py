import streamlit as st
import pandas as pd
import os
from io import BytesIO

st.title("CSV/XLSX 合并 + TGI计算工具")

uploaded_files = st.file_uploader("选择多个文件", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    merged_data = []
    for file in uploaded_files:
        ext = os.path.splitext(file.name)[1]
        df = pd.read_csv(file) if ext == ".csv" else pd.read_excel(file)
        df = df[df["行为时间"] == "合计"]
        df["类别"] = os.path.splitext(file.name)[0]
        merged_data.append(df)

    if merged_data:
        merged_df = pd.concat(merged_data, ignore_index=True)
        st.success("合并成功！")

        st.write("合并数据预览：")
        st.dataframe(merged_df.head())

        if st.button("计算 TGI"):
            def find_col(keyword):
                for col in merged_df.columns:
                    if keyword in col:
                        return col
                return None

            col_qid = find_col("问题编号")
            col_qname = find_col("问题名称")
            col_ans = find_col("答案")
            col_user = find_col("用户数")
            col_cat = "类别"

            index_cols = [col for col in [col_qid, col_qname, col_ans] if col_qid]

            pivot = merged_df.pivot_table(index=index_cols, columns=col_cat, values=col_user, aggfunc="sum", fill_value=0)
            percent_list = []

            for key, group in pivot.groupby(level=0):
                total = group.sum(axis=0)
                percent = group / total
                percent_list.append(percent)

            percent_df = pd.concat(percent_list).sort_index()
            pivot.columns = [f"{col}_人数" for col in pivot.columns]
            percent_df.columns = [col.replace("_人数", "_占比") for col in pivot.columns]

            result = pd.concat([pivot, percent_df], axis=1).reset_index()

            st.write("TGI计算结果：")
            st.dataframe(result)

            towrite = BytesIO()
            result.to_excel(towrite, index=False)
            towrite.seek(0)

            st.download_button("下载结果 Excel", data=towrite, file_name="TGI结果.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
