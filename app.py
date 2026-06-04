import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json

# 페이지 설정 (가장 먼저)
st.set_page_config(page_title="방송/고객 통합 대시보드", layout="wide", initial_sidebar_state="expanded")

# 제목 표시
st.title("📺 방송 성과 & 👥 고객 분석 통합 대시보드")
st.markdown("---")

# Supabase 설정 확인
try:
    SUPABASE_URL = st.secrets.get("supabase_url")
    SUPABASE_KEY = st.secrets.get("supabase_key")

    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("❌ Supabase 자격증명이 없습니다.")
        st.info("""
        **설정 방법:**

        1. Streamlit Cloud 대시보드 접속
        2. 앱 선택 > Settings > Secrets
        3. 다음 입력:
        ```
        supabase_url = "https://ipwbhyigwgwprtqghrdo.supabase.co"
        supabase_key = "YOUR_API_KEY"
        ```
        4. Save 클릭
        """)
        st.stop()

except Exception as e:
    st.error(f"⚠️ Secrets 접근 오류: {str(e)}")
    st.stop()

# Supabase REST API 함수들
@st.cache_data(ttl=60)
def load_broadcast_data():
    try:
        url = f"{SUPABASE_URL}/rest/v1/broadcast_schedule"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            st.error(f"방송 데이터 로드 실패 (코드: {response.status_code})")
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

    except Exception as e:
        st.error(f"방송 데이터 로드 오류: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_customer_data():
    try:
        url = f"{SUPABASE_URL}/rest/v1/customer"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            st.error(f"고객 데이터 로드 실패 (코드: {response.status_code})")
            return pd.DataFrame()

        df = pd.DataFrame(response.json())

        if len(df) > 0:
            # 컬럼명 매핑
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

    except Exception as e:
        st.error(f"고객 데이터 로드 오류: {str(e)}")
        return pd.DataFrame()

def update_broadcast_rating(broadcast_id: str, actual_rating: float):
    try:
        url = f"{SUPABASE_URL}/rest/v1/broadcast_schedule?broadcast_id=eq.{broadcast_id}"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        data = {"actual_rating": actual_rating}
        response = requests.patch(url, json=data, headers=headers, timeout=10)
        return response.status_code == 204
    except Exception as e:
        st.error(f"업데이트 오류: {str(e)}")
        return False

def update_broadcast_sales(broadcast_id: str, actual_sales: int):
    try:
        url = f"{SUPABASE_URL}/rest/v1/broadcast_schedule?broadcast_id=eq.{broadcast_id}"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        data = {"actual_sales": actual_sales}
        response = requests.patch(url, json=data, headers=headers, timeout=10)
        return response.status_code == 204
    except Exception as e:
        st.error(f"업데이트 오류: {str(e)}")
        return False

def update_customer_purchase(customer_id: str, total_purchase: int):
    try:
        url = f"{SUPABASE_URL}/rest/v1/customer?customer_id=eq.{customer_id}"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        data = {"total_purchase": total_purchase}
        response = requests.patch(url, json=data, headers=headers, timeout=10)
        return response.status_code == 204
    except Exception as e:
        st.error(f"업데이트 오류: {str(e)}")
        return False

# 데이터 로드
df_broadcast = load_broadcast_data()
df_customer = load_customer_data()

# 데이터가 비어있으면 경고
if df_broadcast.empty or df_customer.empty:
    st.warning("⚠️ 데이터를 불러올 수 없습니다.")
    st.info("""
    **확인사항:**
    - Streamlit Cloud Secrets 설정됨?
    - Supabase URL과 API 키가 올바름?
    - 인터넷 연결 확인?
    """)
    st.stop()

# 데이터 처리
try:
    # 방송 데이터
    df_broadcast['방송날짜'] = pd.to_datetime(df_broadcast['방송날짜'])
    df_broadcast['시청률달성률'] = (df_broadcast['실제시청률'] / df_broadcast['예상시청률'] * 100).round(1)
    df_broadcast['판매달성률'] = (df_broadcast['실제판매액'] / df_broadcast['판매목표'] * 100).round(1)

    # 고객 데이터
    df_customer['가입일자'] = pd.to_datetime(df_customer['가입일자'])
    df_customer['연령대'] = df_customer['연령대'].replace('35세', '30대')

    # 판매 데이터 (0 제외)
    df_broadcast_sales = df_broadcast[df_broadcast['실제판매액'] > 0]

except Exception as e:
    st.error(f"데이터 처리 오류: {str(e)}")
    st.stop()

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
# KPI 메트릭 (상단)
# ============================================================================
st.subheader("📊 핵심 지표")

col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)

with col1:
    st.metric("📺 방송건수", len(filtered_broadcast))

with col2:
    st.metric("평균 시청률", f"{filtered_broadcast['실제시청률'].mean():.2f}%",
              f"{(filtered_broadcast['실제시청률'].mean() - filtered_broadcast['예상시청률'].mean()):.2f}%")

with col3:
    st.metric("총 판매액", f"₩{filtered_broadcast_sales['실제판매액'].sum():,.0f}",
              f"{((filtered_broadcast_sales['실제판매액'].sum() / filtered_broadcast_sales['판매목표'].sum() - 1) * 100):.1f}%" if len(filtered_broadcast_sales) > 0 else "N/A")

with col4:
    st.metric("판매달성률",
              f"{(filtered_broadcast_sales['실제판매액'].sum() / filtered_broadcast_sales['판매목표'].sum() * 100):.1f}%" if len(filtered_broadcast_sales) > 0 else "N/A")

with col5:
    st.metric("👥 총 고객수", len(filtered_customer))

with col6:
    active_count = len(filtered_customer[filtered_customer['활성상태'] == '활성'])
    st.metric("활성 고객수", active_count,
              f"{(active_count / len(filtered_customer) * 100):.1f}%" if len(filtered_customer) > 0 else "N/A")

with col7:
    st.metric("평균 구매액", f"₩{filtered_customer['총구매액'].mean():,.0f}")

with col8:
    vip_count = len(filtered_customer[filtered_customer['고객등급'] == 'VIP'])
    st.metric("VIP 고객수", vip_count)

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
