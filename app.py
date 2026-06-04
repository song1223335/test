import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(page_title="방송/고객 통합 대시보드", layout="wide", initial_sidebar_state="expanded")

# 제목
st.title("📺 방송 성과 & 👥 고객 분석 통합 대시보드")
st.markdown("---")

# CSV 파일 읽기
df_broadcast = pd.read_csv("broadcast_schedule.csv")
df_customer = pd.read_csv("customer.csv")

# 데이터 처리 - 방송 데이터
df_broadcast['방송날짜'] = pd.to_datetime(df_broadcast['방송날짜'])
df_broadcast['시청률달성률'] = (df_broadcast['실제시청률'] / df_broadcast['예상시청률'] * 100).round(1)
df_broadcast['판매달성률'] = (df_broadcast['실제판매액'] / df_broadcast['판매목표'] * 100).round(1)

# 데이터 처리 - 고객 데이터
df_customer['가입일자'] = pd.to_datetime(df_customer['가입일자'])
df_customer['연령대'] = df_customer['연령대'].replace('35세', '30대')

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
