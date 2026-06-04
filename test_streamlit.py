import streamlit as st

st.title("Streamlit 설치 확인")
st.write("✅ Streamlit이 정상 설치되었습니다!")
st.success("환영합니다!")

# 간단한 데이터 표시
st.write("### 간단한 테스트:")
import pandas as pd
df = pd.DataFrame({
    '이름': ['Alice', 'Bob', 'Charlie'],
    '점수': [90, 85, 92]
})
st.dataframe(df)
