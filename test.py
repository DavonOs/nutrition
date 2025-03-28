import pandas as pd
from pypinyin import lazy_pinyin

def clean_columns(df):
    """统一列名格式"""
    return df.rename(columns={
        '食物类 Food group': 'category',
        '食物名称 Food name': 'name',
        '鸟嘌呤 Guanine': 'guanine',
        '腺嘌呤 Adenine': 'adenine',
        '次黄嘌呤 Hypoxanthine': 'hypoxanthine',
        '黄嘌呤 Xanthine': 'xanthine',
        '总嘌呤 Purine': 'total',
        '采样地 Sampling site': 'origin'
    })

def process_data(csv_path):
    """处理CSV并生成Parquet"""
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    
    # 列名清洗
    df = clean_columns(df)
    
    # 数据清洗
    purine_cols = ['guanine', 'adenine', 'hypoxanthine', 'xanthine', 'total']
    for col in purine_cols:
        df[col] = (
            df[col].astype(str)
            .str.replace('Tr', '0')
            .str.replace('[^0-9.]', '', regex=True)
        )
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # 生成搜索字段
    df['pinyin'] = df['name'].apply(lambda x: ''.join(lazy_pinyin(x)).lower())
    df['initials'] = df['pinyin'].apply(lambda x: ''.join([i[0] for i in x.split()]))
    
    # 保存Parquet
    df.to_parquet("purine_data.parquet", engine='pyarrow')
    return df

if __name__ == "__main__":
    process_data("purine_data.csv")
    print("转换完成！生成文件：purine_data.parquet")