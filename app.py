import streamlit as st
import pandas as pd
from pypinyin import lazy_pinyin

# 配置页面
st.set_page_config(page_title="嘌呤查询系统", layout="wide")
# 配置列名映射（与Parquet文件一致）
COLUMN_MAP = {
    'category': '食物类别',
    'name': '食物名称',
    'guanine': '鸟嘌呤',
    'adenine': '腺嘌呤', 
    'hypoxanthine': '次黄嘌呤',
    'xanthine': '黄嘌呤',
    'total': '总嘌呤',
    'origin': '采样地',
    'pinyin': '_拼音',
    'initials': '_首字母'
}

@st.cache_data
def load_data():
    df = pd.read_csv("purine_data.csv", encoding='utf-8-sig')
    
    # 列名标准化
    df.columns = [
        '食物类', '食物名称', '鸟嘌呤', '腺嘌呤',
        '次黄嘌呤', '黄嘌呤', '总嘌呤', '采样地'
    ]
    
    # 数据清洗
    purine_cols = ['鸟嘌呤', '腺嘌呤', '次黄嘌呤', '黄嘌呤', '总嘌呤']
    for col in purine_cols:
        df[col] = (
            df[col].astype(str)
            .str.replace('Tr', '0')
            .str.replace('[^0-9.]', '', regex=True)
        )
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # 生成搜索辅助字段
    df['_名称拼音'] = df['食物名称'].apply(lambda x: ''.join(lazy_pinyin(x)).lower())
    df['_名称首字母'] = df['_名称拼音'].apply(lambda x: ''.join([i[0] for i in x.split()]))
    
    return df

# 初始化session状态
if 'purine_range' not in st.session_state:
    st.session_state.purine_range = (0, 0)
if 'filter_changed' not in st.session_state:
    st.session_state.filter_changed = False

df = load_data()
purine_max = int(df['总嘌呤'].max())

# 页面布局
st.markdown("# 🍲 食物嘌呤含量查询系统")
st.markdown("### 数据来源：国家粮食局食物成分监测中心")

# 主搜索框
search_term = st.text_input(
    "🔍 输入食物名称/拼音/首字母",
    placeholder="例：牛肉 或 niurou 或 NR",
    help="支持中文名称、全拼或拼音首字母组合搜索",
    key="search_input"
)

# 筛选面板
with st.container():
    cols = st.columns([2, 3])
    with cols[0]:
        categories = st.multiselect(
            "选择食物类别",
            options=df['食物类'].unique(),
            default=[],
            key="category_select"
        )
    with cols[1]:
        # 动态调整滑块范围
        current_min, current_max = st.session_state.purine_range
        
        # 当有搜索词或选择类别时自动调整范围
        if (search_term.strip() or categories) and not st.session_state.filter_changed:
            current_max = purine_max
        
        purine_range = st.slider(
            "总嘌呤范围 (mg/100g)",
            min_value=0,
            max_value=purine_max,
            value=(current_min, current_max),
            key="purine_slider",
            on_change=lambda: setattr(st.session_state, 'filter_changed', True)
        )

# 构建过滤条件
filter_condition = df['总嘌呤'].between(*purine_range)
if categories:
    filter_condition &= df['食物类'].isin(categories)
if search_term.strip():
    filter_condition &= df.apply(lambda x: (
        (search_term.lower() in x['食物名称'].lower()) or
        (search_term.lower() in x['_名称拼音']) or
        (search_term.upper() == x['_名称首字母'])
    ), axis=1)

filtered_df = df[filter_condition]

# 判断是否需要显示结果
has_active_filter = any([
    search_term.strip() != "",
    len(categories) > 0,
    purine_range != (0, 0)
])

# 显示结果逻辑
if has_active_filter:
    if not filtered_df.empty:
        st.success(f"✅ 找到 {len(filtered_df)} 条记录")
        
        display_columns = ['食物类', '食物名称', '鸟嘌呤', '腺嘌呤',
                         '次黄嘌呤', '黄嘌呤', '总嘌呤', '采样地']
        
        with st.expander("📋 查看详细数据", expanded=True):
            st.dataframe(
                filtered_df[display_columns].sort_values("总嘌呤", ascending=False),
                column_config={
                    "总嘌呤": st.column_config.NumberColumn(
                        "总嘌呤 (mg)",
                        format="%d",
                        help="每100克可食部含量"
                    )
                },
                height=600,
                use_container_width=True,
                hide_index=True
            )
        
        st.download_button(
            label="📥 导出当前结果 (CSV)",
            data=filtered_df[display_columns].to_csv(index=False).encode('utf-8-sig'),
            file_name=f"purine_data_{search_term[:20]}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.warning("⚠ 未找到匹配结果，请调整筛选条件")
else:
    st.info("🔍 请输入搜索词或设置筛选条件以显示结果")

# 数据分析模块
st.markdown("## 📊 数据洞察")
viz_cols = st.columns(2)

with viz_cols[0]:
    st.markdown("### 品类嘌呤分布")
    category_avg = df.groupby('食物类')['总嘌呤'].mean().sort_values(ascending=False)
    st.bar_chart(category_avg)

with viz_cols[1]:
    st.markdown("### 高嘌呤食物TOP10")
    top10 = df.nlargest(10, '总嘌呤')[['食物名称', '总嘌呤']]
    st.dataframe(
        top10,
        column_config={"总嘌呤": "含量 (mg)"},
        hide_index=True,
        height=400
    )