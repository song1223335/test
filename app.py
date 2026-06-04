import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json

# 페이지 설정
st.set_page_config(page_title="방송/고객 통합 대시보드", layout="wide", initial_sidebar_state="expanded")

# Supabase REST API 클라이언트
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets.get("supabase_url")
        key = st.secrets.get("supabase_key")

        if not url or not key:
            st.error("⚠️ Supabase 자격증명이 필요합니다.")
            st.info("Settings > Secrets에서 다음을 설정하세요:\n- supabase_url\n- supabase_key")
            st.stop()

        return {"url": url, "key": key}
    except Exception as e:
        st.error(f"❌ Supabase 초기화 오류: {str(e)}")
        st.stop()

supabase_config = init_supabase()

# 데이터 로드 함수
@st.cache_data(ttl=60)
def load_broadcast_data():
    url = f"{supabase_config['url']}/rest/v1/broadcast_schedule"
    headers = {
        "apikey": supabase_config['key'],
        "Authorization": f"Bearer {supabase_config['key']}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        st.error(f"❌ 방송 데이터 로드 실패: {response.text}")
        return pd.DataFrame()

    df = pd.DataFrame(response.json())
    df['방송날짜'] = pd.to_datetime(df['broadcast_date'])

    # 컬럼명 매핑
    column_mapping = {
        'broadcast_id': '방송ID',
        'product_id': '상품ID',
        'broadcast_time': '방송시간',
        'channel': '채널',
        'host': '진행자',
        'expected_rating': '예상시청률',
        'actual_rating': '실제시청률',
        'sales_target': '판매목표',
        'actual_sales': '실제판매액'
    }
    df = df.rename(columns=column_mapping)
    return df

@st.cache_data(ttl=60)
def load_customer_data():
    url = f"{supabase_config['url']}/rest/v1/customer"
    headers = {
        "apikey": supabase_config['key'],
        "Authorization": f"Bearer {supabase_config['key']}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        st.error(f"❌ 고객 데이터 로드 실패: {response.text}")
        return pd.DataFrame()

    df = pd.DataFrame(response.json())

    if len(df) > 0:
        # 스네이크케이스 컬럼명을 한글로 변환
        column_mapping = {
            'customer_id': '고객ID',
            'customer_name': '고객명',
            'gender': '성별',
            'age_group': '연령대',
            'region': '지역',
            'join_date': '가입일자',
            'purchase_count': '구매횟수',
            'total_purchase': '총구매액',
            'customer_grade': '고객등급',
            'active_status': '활성상태'
        }
        df = df.rename(columns=column_mapping)
        df['가입일자'] = pd.to_datetime(df['가입일자'])

    return df

# Supabase 업데이트 함수
def update_broadcast_rating(broadcast_id: str, actual_rating: float):
    url = f"{supabase_config['url']}/rest/v1/broadcast_schedule?broadcast_id=eq.{broadcast_id}"
    headers = {
        "apikey": supabase_config['key'],
        "Authorization": f"Bearer {supabase_config['key']}",
        "Content-Type": "application/json"
    }
    data = {"actual_rating": actual_rating}
    response = requests.patch(url, json=data, headers=headers)
    return response.status_code == 204

def update_broadcast_sales(broadcast_id: str, actual_sales: int):
    url = f"{supabase_config['url']}/rest/v1/broadcast_schedule?broadcast_id=eq.{broadcast_id}"
    headers = {
        "apikey": supabase_config['key'],
        "Authorization": f"Bearer {supabase_config['key']}",
        "Content-Type": "application/json"
    }
    data = {"actual_sales": actual_sales}
    response = requests.patch(url, json=data, headers=headers)
    return response.status_code == 204

def update_customer_purchase(customer_id: str, total_purchase: int):
    url = f"{supabase_config['url']}/rest/v1/customer?customer_id=eq.{customer_id}"
    headers = {
        "apikey": supabase_config['key'],
        "Authorization": f"Bearer {supabase_config['key']}",
        "Content-Type": "application/json"
    }
    data = {"total_purchase": total_purchase}
    response = requests.patch(url, json=data, headers=headers)
    return response.status_code == 204

# 제목
st.title("📺 방송 성과 & 👥 고객 분석 통합 대시보드")
st.markdown("---")

# 데이터 로드 (에러 발생해도 앱은 계속 실행)
try:
    df_broadcast = load_broadcast_data()
    df_customer = load_customer_data()

    # 데이터가 비어있으면 경고하고 계속
    data_loaded = not (df_broadcast.empty or df_customer.empty)

    if not data_loaded:
        st.warning("⚠️ 데이터를 불러올 수 없습니다.")
        st.info("확인사항:\n1. Streamlit Cloud Secrets 설정 확인\n2. Supabase URL과 API 키 확인\n3. 인터넷 연결 확인")
        st.stop()

    # 데이터 처리 - 방송 데이터
    df_broadcast['방송날짜'] = pd.to_datetime(df_broadcast['방송날짜'])
    df_broadcast['시청률달성률'] = (df_broadcast['실제시청률'] / df_broadcast['예상시청률'] * 100).round(1)
    df_broadcast['판매달성률'] = (df_broadcast['실제판매액'] / df_broadcast['판매목표'] * 100).round(1)

    # 데이터 처리 - 고객 데이터
    df_customer['가입일자'] = pd.to_datetime(df_customer['가입일자'])
    df_customer['연령대'] = df_customer['연령대'].replace('35세', '30대')

except Exception as e:
    st.error(f"❌ 데이터 로드 오류: {str(e)}")
    st.error(f"오류 타입: {type(e).__name__}")
    st.stop()

# 판매 데이터 (0 제외)
df_broadcast_sales = df_broadcast[df_broadcast['실제판매액'] > 0]

# ============================================================================
# 사이드바 필터
# ============================================================================
st.sidebar.header("🔍 필터")

st.sidebar.subheader("📺 방송 필터")
selected_channel = st.sidebar.multiselect("채널 선택", df_broadcast['채널'].unique(), default=df_broadcast['채널'].unique())
selected_host = st.sidebar.multiselect("진행자 선택", df_broadcast['진행자'].unique(), default=df_broadcast['진행자'].unique())

st.sidebar.subheader("👥 고객 필터")
selected_gender = st.sidebar.multiselect("성별 선택", df_customer['성별'].unique(), default=df_customer['성별'].unique())
selected_grade = st.sidebar.multiselect("고객등급 선택", df_customer['고객등급'].unique(), default=df_customer['고객등급'].unique())
selected_status = st.sidebar.multiselect("활성상태 선택", df_customer['활성상태'].unique(), default=df_customer['활성상태'].unique())

# 필터 적용
filtered_broadcast = df_broadcast[(df_broadcast['채널'].isin(selected_channel)) & (df_broadcast['진행자'].isin(selected_host))]
filtered_broadcast_sales = filtered_broadcast[filtered_broadcast['실제판매액'] > 0]
filtered_customer = df_customer[(df_customer['성별'].isin(selected_gender)) &
                               (df_customer['고객등급'].isin(selected_grade)) &
                               (df_customer['활성상태'].isin(selected_status))]

# ============================================================================
# KPI 메트릭 (상단) - 방송 + 고객
# ============================================================================
st.subheader("📊 핵심 지표")

col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)

with col1:
    st.metric(
        "📺 방송건수",
        len(filtered_broadcast)
    )

with col2:
    st.metric(
        "평균 시청률",
        f"{filtered_broadcast['실제시청률'].mean():.2f}%",
        f"{(filtered_broadcast['실제시청률'].mean() - filtered_broadcast['예상시청률'].mean()):.2f}%"
    )

with col3:
    st.metric(
        "총 판매액",
        f"₩{filtered_broadcast_sales['실제판매액'].sum():,.0f}",
        f"{((filtered_broadcast_sales['실제판매액'].sum() / filtered_broadcast_sales['판매목표'].sum() - 1) * 100):.1f}%" if len(filtered_broadcast_sales) > 0 else "N/A"
    )

with col4:
    st.metric(
        "판매달성률",
        f"{(filtered_broadcast_sales['실제판매액'].sum() / filtered_broadcast_sales['판매목표'].sum() * 100):.1f}%" if len(filtered_broadcast_sales) > 0 else "N/A"
    )

with col5:
    st.metric(
        "👥 총 고객수",
        len(filtered_customer)
    )

with col6:
    active_count = len(filtered_customer[filtered_customer['활성상태'] == '활성'])
    st.metric(
        "활성 고객수",
        active_count,
        f"{(active_count / len(filtered_customer) * 100):.1f}%" if len(filtered_customer) > 0 else "N/A"
    )

with col7:
    st.metric(
        "평균 구매액",
        f"₩{filtered_customer['총구매액'].mean():,.0f}"
    )

with col8:
    vip_count = len(filtered_customer[filtered_customer['고객등급'] == 'VIP'])
    st.metric(
        "VIP 고객수",
        vip_count
    )

st.markdown("---")

# ============================================================================
# 탭 구성
# ============================================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📋 방송 데이터", "📊 시청률 분석", "💰 판매 분석", "🎙️ 진행자 성과", "👥 고객 데이터", "📈 고객 분석"])

# ============================================================================
# 탭1: 방송 데이터
# ============================================================================
with tab1:
    st.subheader("방송 스케줄 데이터")

    display_cols = ['방송ID', '상품ID', '방송날짜', '방송시간', '채널', '진행자',
                   '예상시청률', '실제시청률', '시청률달성률', '판매목표', '실제판매액', '판매달성률']

    st.dataframe(
        filtered_broadcast[display_cols].sort_values('방송날짜', ascending=False),
        use_container_width=True,
        height=400
    )

    csv = filtered_broadcast[display_cols].to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 CSV 다운로드",
        data=csv,
        file_name="broadcast_schedule.csv",
        mime="text/csv"
    )

# ============================================================================
# 탭2: 시청률 분석
# ============================================================================
with tab2:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("채널별 평균 시청률")
        channel_viewership = filtered_broadcast.groupby('채널')[['예상시청률', '실제시청률']].mean()
        fig = px.bar(
            channel_viewership,
            barmode='group',
            labels={'value': '시청률 (%)', 'index': '채널'},
            title="예상 vs 실제 시청률"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("진행자별 평균 시청률")
        host_viewership = filtered_broadcast.groupby('진행자')['실제시청률'].mean().sort_values(ascending=False)
        fig = px.bar(
            x=host_viewership.index,
            y=host_viewership.values,
            labels={'x': '진행자', 'y': '평균 시청률 (%)'},
            title="진행자별 실제 시청률"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("시청률 달성률 분포")
    fig = px.histogram(
        filtered_broadcast,
        x='시청률달성률',
        nbins=15,
        labels={'시청률달성률': '달성률 (%)', 'count': '방송 건수'},
        title="시청률 달성률의 분포"
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# 탭3: 판매 분석
# ============================================================================
with tab3:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("채널별 판매 성과")
        channel_sales = filtered_broadcast_sales.groupby('채널')[['판매목표', '실제판매액']].sum()
        if len(channel_sales) > 0:
            fig = px.bar(
                channel_sales,
                barmode='group',
                labels={'value': '금액 (₩)', 'index': '채널'},
                title="목표 vs 실제 판매액"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("판매 데이터가 없습니다.")

    with col2:
        st.subheader("진행자별 판매액")
        host_sales = filtered_broadcast_sales.groupby('진행자')['실제판매액'].sum().sort_values(ascending=False)
        if len(host_sales) > 0:
            fig = px.bar(
                x=host_sales.index,
                y=host_sales.values,
                labels={'x': '진행자', 'y': '판매액 (₩)'},
                title="진행자별 총 판매액"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("판매 데이터가 없습니다.")

    st.subheader("판매 달성률 분석")
    if len(filtered_broadcast_sales) > 0:
        fig = px.scatter(
            filtered_broadcast_sales,
            x='판매목표',
            y='실제판매액',
            hover_data=['방송ID', '진행자', '채널'],
            trendline='ols',
            labels={'판매목표': '판매 목표 (₩)', '실제판매액': '실제 판매액 (₩)'},
            title="판매 목표 vs 실제 판매액"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("판매 데이터가 없습니다.")

# ============================================================================
# 탭4: 진행자별 성과
# ============================================================================
with tab4:
    st.subheader("진행자별 상세 성과")

    host_summary = filtered_broadcast.groupby('진행자').agg({
        '방송ID': 'count',
        '실제시청률': 'mean',
        '실제판매액': 'sum',
        '판매목표': 'sum'
    }).round(2)
    host_summary.columns = ['방송건수', '평균시청률(%)', '총판매액(₩)', '총목표액(₩)']
    host_summary['달성률(%)'] = (host_summary['총판매액(₩)'] / host_summary['총목표액(₩)'] * 100).round(1)
    host_summary = host_summary.sort_values('총판매액(₩)', ascending=False)

    st.dataframe(host_summary, use_container_width=True)

    selected_host_detail = st.selectbox("진행자 선택 (상세 보기):", filtered_broadcast['진행자'].unique())

    host_data = filtered_broadcast[filtered_broadcast['진행자'] == selected_host_detail]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("방송 건수", len(host_data))
    with col2:
        st.metric("평균 시청률", f"{host_data['실제시청률'].mean():.2f}%")
    with col3:
        st.metric("총 판매액", f"₩{host_data['실제판매액'].sum():,.0f}")

    st.write(f"**{selected_host_detail}의 방송 기록**")
    st.dataframe(
        host_data[['방송ID', '상품ID', '방송날짜', '채널', '실제시청률', '실제판매액']],
        use_container_width=True
    )

# ============================================================================
# 탭5: 고객 데이터
# ============================================================================
with tab5:
    st.subheader("고객 데이터")

    display_cols_customer = ['고객ID', '고객명', '성별', '연령대', '지역', '가입일자',
                           '구매횟수', '총구매액', '고객등급', '활성상태']

    st.dataframe(
        filtered_customer[display_cols_customer].sort_values('가입일자', ascending=False),
        use_container_width=True,
        height=400
    )

    csv = filtered_customer[display_cols_customer].to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 CSV 다운로드",
        data=csv,
        file_name="customer.csv",
        mime="text/csv"
    )

# ============================================================================
# 탭6: 고객 분석
# ============================================================================
with tab6:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("성별별 고객 수")
        gender_count = filtered_customer['성별'].value_counts()
        fig = px.pie(
            values=gender_count.values,
            names=gender_count.index,
            title="성별 구성"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("연령대별 고객 수")
        age_count = filtered_customer['연령대'].value_counts()
        fig = px.bar(
            x=age_count.index,
            y=age_count.values,
            labels={'x': '연령대', 'y': '고객수'},
            title="연령대 분포"
        )
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("지역별 고객 수")
        region_count = filtered_customer['지역'].value_counts()
        fig = px.bar(
            x=region_count.index,
            y=region_count.values,
            labels={'x': '지역', 'y': '고객수'},
            title="지역 분포"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.subheader("고객등급별 구매액")
        grade_sales = filtered_customer.groupby('고객등급')['총구매액'].sum().sort_values(ascending=False)
        fig = px.bar(
            x=grade_sales.index,
            y=grade_sales.values,
            labels={'x': '고객등급', 'y': '총구매액 (₩)'},
            title="등급별 총 구매액"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("고객등급별 상세 분석")
    grade_summary = filtered_customer.groupby('고객등급').agg({
        '고객ID': 'count',
        '구매횟수': 'mean',
        '총구매액': ['mean', 'sum']
    }).round(0)
    grade_summary.columns = ['고객수', '평균구매횟수', '평균구매액(₩)', '총구매액(₩)']
    grade_summary = grade_summary.sort_values('총구매액(₩)', ascending=False)

    st.dataframe(grade_summary, use_container_width=True)

st.markdown("---")
st.info("💡 팁: 사이드바에서 조건을 선택하여 데이터를 필터링할 수 있습니다.")

# ============================================================================
# 데이터 수정 섹션
# ============================================================================
st.markdown("---")
st.subheader("✏️ 데이터 수정 (테스트용)")

edit_tab1, edit_tab2 = st.tabs(["📺 방송 데이터 수정", "👥 고객 데이터 수정"])

with edit_tab1:
    st.write("**방송 데이터를 수정하면 Supabase에 즉시 반영됩니다.**")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("시청률 수정")
        selected_broadcast_rating = st.selectbox(
            "수정할 방송 선택 (시청률):",
            df_broadcast['방송ID'].values,
            key="rating_select"
        )
        broadcast_row = df_broadcast[df_broadcast['방송ID'] == selected_broadcast_rating].iloc[0]
        new_rating = st.number_input(
            f"새로운 시청률 ({broadcast_row['방송ID']} - 현재: {broadcast_row['실제시청률']}%):",
            min_value=0.0,
            max_value=100.0,
            value=float(broadcast_row['실제시청률']),
            step=0.1,
            key="rating_input"
        )

        if st.button("시청률 수정 저장", key="rating_btn"):
            if update_broadcast_rating(selected_broadcast_rating, new_rating):
                st.success(f"✅ {selected_broadcast_rating} 시청률을 {new_rating}%로 수정했습니다!")
                st.cache_data.clear()
            else:
                st.error(f"❌ 수정 실패했습니다.")

    with col2:
        st.subheader("판매액 수정")
        selected_broadcast_sales = st.selectbox(
            "수정할 방송 선택 (판매액):",
            df_broadcast['방송ID'].values,
            key="sales_select"
        )
        broadcast_row = df_broadcast[df_broadcast['방송ID'] == selected_broadcast_sales].iloc[0]
        new_sales = st.number_input(
            f"새로운 판매액 ({broadcast_row['방송ID']} - 현재: ₩{broadcast_row['실제판매액']:,}):",
            min_value=0,
            value=int(broadcast_row['실제판매액']),
            step=100000,
            key="sales_input"
        )

        if st.button("판매액 수정 저장", key="sales_btn"):
            if update_broadcast_sales(selected_broadcast_sales, new_sales):
                st.success(f"✅ {selected_broadcast_sales} 판매액을 ₩{new_sales:,}로 수정했습니다!")
                st.cache_data.clear()
            else:
                st.error(f"❌ 수정 실패했습니다.")

with edit_tab2:
    st.write("**고객 데이터를 수정하면 Supabase에 즉시 반영됩니다.**")

    selected_customer = st.selectbox(
        "수정할 고객 선택:",
        df_customer['고객ID'].values,
        key="customer_select"
    )
    customer_row = df_customer[df_customer['고객ID'] == selected_customer].iloc[0]

    new_purchase = st.number_input(
        f"새로운 구매액 ({customer_row['고객ID']} {customer_row['고객명']} - 현재: ₩{customer_row['총구매액']:,}):",
        min_value=0,
        value=int(customer_row['총구매액']),
        step=100000,
        key="purchase_input"
    )

    if st.button("구매액 수정 저장", key="purchase_btn"):
        if update_customer_purchase(selected_customer, new_purchase):
            st.success(f"✅ {selected_customer} {customer_row['고객명']}의 구매액을 ₩{new_purchase:,}로 수정했습니다!")
            st.cache_data.clear()
        else:
            st.error(f"❌ 수정 실패했습니다.")
