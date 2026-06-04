import streamlit as st

# 페이지 설정 (가장 먼저)
st.set_page_config(page_title="방송/고객 통합 대시보드", layout="wide")

# 제목
st.title("📺 방송 성과 & 👥 고객 분석 통합 대시보드")

# Secrets 확인
try:
    supabase_url = st.secrets.get("supabase_url")
    supabase_key = st.secrets.get("supabase_key")

    if supabase_url and supabase_key:
        st.success("✅ Supabase 연결 설정됨")
        st.write(f"URL: {supabase_url[:50]}...")
    else:
        st.error("❌ Supabase 설정 없음")
        st.write("Secrets에서 설정해주세요.")

except Exception as e:
    st.error(f"❌ 에러: {str(e)}")

st.markdown("---")
st.info("앱이 정상 로드되었습니다!")
