from flask import Flask, render_template, request, jsonify
import pandas as pd
import plotly.express as px
import plotly
import json
import os

app = Flask(__name__)

def load_data():
    file_path = os.path.join('data', 'medical_data.csv')
    if not os.path.exists(file_path): return pd.DataFrame()
    df = pd.read_csv(file_path)
    
    df['age_num'] = pd.to_numeric(df['age'], errors='coerce').fillna(0).astype(int)
    df['age_group'] = (df['age_num'] // 10 * 10).astype(str) + "대"
    df['total_cost'] = pd.to_numeric(df['total_cost'], errors='coerce').fillna(0)
    return df

df = load_data()

@app.route('/')
def index():
    if df.empty: return "데이터를 찾을 수 없습니다."
    return render_template('index.html', 
                           genders=sorted(df['gender'].unique()), 
                           diseases=sorted(df['disease'].unique()), 
                           regions=sorted(df['region'].unique()))

@app.route('/dashboard-data')
def dashboard_data():
    f_df = df.copy()
    g, d, r = request.args.get('gender'), request.args.get('disease'), request.args.get('region')

    if g and g != 'All': f_df = f_df[f_df['gender'] == g]
    if d and d != 'All': f_df = f_df[f_df['disease'] == d]
    if r and r != 'All': f_df = f_df[f_df['region'] == r]

    # 1. 연령대별 차트
    age_sum = f_df.groupby(['age_group', 'gender'])['total_cost'].sum().reset_index()
    if not age_sum.empty:
        age_sum = age_sum.sort_values('age_group', key=lambda x: x.str.replace('대','').astype(int))
    
    age_chart = px.bar(age_sum, x='age_group', y='total_cost', color='gender', 
                       title='연령대별 총 진료비 분포 (10세 단위)', barmode='group',
                       labels={'age_group': '연령대', 'total_cost': '진료비', 'gender': '성별'})

    # 2. 진료과목별 차트
    disease_sum = f_df.groupby('disease')['total_cost'].sum().reset_index()
    disease_chart = px.bar(disease_sum, x='disease', y='total_cost', title='진료과목별 총 진료비',
                           labels={'disease': '진료과목', 'total_cost': '진료비'})

    # 3. 지역별 비중 (원 그래프 전용 합산 데이터 생성)
    region_sum_df = f_df.groupby('region')['total_cost'].sum().reset_index()
    region_chart = px.pie(region_sum_df, names='region', values='total_cost', title='지역별 진료비 비중')

    # 막대 그래프 레이아웃 및 툴팁 설정
    for c in [age_chart, disease_chart]:
        current_max = age_sum['total_cost'].max() if c == age_chart else disease_sum['total_cost'].max()
        tick_vals = [i * 1_000_000_000_000 for i in range(int(current_max / 1_000_000_000_000) + 2)]
        tick_text = [f"{i} 조" for i in range(len(tick_vals))]

        c.update_layout(
            yaxis=dict(tickvals=tick_vals, ticktext=tick_text, fixedrange=True, rangemode='tozero'),
            xaxis=dict(fixedrange=True)
        )
        
        if c == age_chart:
            for trace in c.data:
                relevant_data = age_sum[age_sum['gender'] == trace.name]['total_cost'] / 1_000_000_000_000
                trace.customdata = relevant_data.tolist()
                trace.hovertemplate = '<b>%{x}</b><br>성별: %{fullData.name}<br>진료비: %{customdata:.2f} 조<extra></extra>'
        else:
            c.update_traces(
                customdata=(disease_sum['total_cost'] / 1_000_000_000_000).tolist(),
                hovertemplate='<b>%{x}</b><br>진료비: %{customdata:.2f} 조<extra></extra>'
            )

    # 원 그래프 툴팁 수정 (핵심 부분)
    # 합산된 데이터인 region_sum_df를 기준으로 customdata 주입
    region_custom_data = (region_sum_df['total_cost'] / 1_000_000_000_000).tolist()
    region_chart.update_traces(
        customdata=region_custom_data,
        hovertemplate='<b>%{label}</b><br>비중: %{percent}<br>진료비: %{customdata:.2f} 조<extra></extra>'
    )

    region_chart.update_layout(margin=dict(l=10, r=10, t=50, b=10), dragmode=False)

    return jsonify({
        'age_chart': json.dumps(age_chart, cls=plotly.utils.PlotlyJSONEncoder),
        'disease_chart': json.dumps(disease_chart, cls=plotly.utils.PlotlyJSONEncoder),
        'region_chart': json.dumps(region_chart, cls=plotly.utils.PlotlyJSONEncoder)
    })

if __name__ == '__main__':
    app.run(debug=True)