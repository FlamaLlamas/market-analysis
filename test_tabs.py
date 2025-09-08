import streamlit as st

st.set_page_config(layout="wide")
st.title("Test Tabs")

# Add tabs
tab1, tab2, tab3 = st.tabs(["Tab 1", "Tab 2", "Tab 3"])

with tab1:
    st.write("This is Tab 1")

with tab2:
    st.write("This is Tab 2")

with tab3:
    st.write("This is Tab 3")
    st.write("Third tab is working!")
