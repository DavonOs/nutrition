import streamlit as st
import pandas as pd

# 配置页面
st.set_page_config(page_title="嘌呤查询系统", layout="wide")

# 读取数据（假设文件名为purine_data.csv）
@st.cache_data
def load_data():
    df = pd.read_csv("purine_data.csv")
    # 处理列名中的特殊字符和空格
    df.columns = df.columns.str.replace('﻿', '').str.strip()
    # 处理可能的异常值（将Tr替换为0）
    for col in ['鸟嘌呤 Guanine', '腺嘌呤 Adenine', '次黄嘌呤 Hypoxanthine', '黄嘌呤 Xanthine', '总嘌呤 Purine']:
        df[col] = pd.to_numeric(df[col].replace('Tr', 0), errors='coerce')
    return df

df = load_data()

# 页面布局
st.markdown("# 🍲 食物嘌呤含量查询系统")
st.markdown("### 数据来源：国家粮食局食物成分监测中心")

# 侧边栏筛选器
with st.sidebar:
    st.header("🔍 筛选条件")
    
    # 食物类别多选
    categories = st.multiselect(
        "选择食物类别",
        options=df['食物类 Food group'].unique(),
        default=["谷类及制品", "蔬菜类及制品"]
    )
    
    # 嘌呤范围滑块
    purine_range = st.slider(
        "总嘌呤范围 (mg/100g)",
        min_value=int(df['总嘌呤 Purine'].min()),
        max_value=int(df['总嘌呤 Purine'].max()),
        value=(0, 500)
    )

# 主界面搜索框
search_term = st.text_input("输入食物名称关键字搜索", help="支持中文或拼音首字母")

# 数据过滤
filtered_df = df[
    (df['食物类 Food group'].isin(categories)) &
    (df['总嘌呤 Purine'].between(purine_range[0], purine_range[1])) &
    (df['食物名称 Food name'].str.contains(search_term, case=False))
]

# 显示数据
st.markdown(f"找到 {len(filtered_df)} 条记录")
st.dataframe(
    filtered_df.sort_values("总嘌呤 Purine", ascending=False),
    column_config={
        "食物类 Food group": "类别",
        "食物名称 Food name": "食物名称",
        "鸟嘌呤 Guanine": st.column_config.NumberColumn("鸟嘌呤 (mg)"),
        "腺嘌呤 Adenine": st.column_config.NumberColumn("腺嘌呤 (mg)"),
        "次黄嘌呤 Hypoxanthine": st.column_config.NumberColumn("次黄嘌呤 (mg)"),
        "黄嘌呤 Xanthine": st.column_config.NumberColumn("黄嘌呤 (mg)"),
        "总嘌呤 Purine": st.column_config.NumberColumn("总嘌呤 (mg)", 
            help="每100克可食部含量"),
        "采样地 Sampling site": "采样地区"
    },
    height=600,
    use_container_width=True
)

# 数据下载按钮
st.download_button(
    label="下载筛选结果",
    data=filtered_df.to_csv(index=False).encode('utf-8-sig'),
    file_name="filtered_purine_data.csv",
    mime="text/csv"
)

# 添加可视化分析
st.markdown("## 📊 数据分析")
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 各品类嘌呤分布")
    category_purine = df.groupby('食物类 Food group')['总嘌呤 Purine'].mean().sort_values()
    st.bar_chart(category_purine)

with col2:
    st.markdown("### 高嘌呤食物TOP10")
    top10 = df.nlargest(10, '总嘌呤 Purine')[['食物名称 Food name', '总嘌呤 Purine']]
    st.dataframe(top10, hide_index=True)