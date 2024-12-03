from mftool import Mftool
import streamlit as st, pandas as pd, numpy as np, plotly.express as px

mf = Mftool()

st.title('Mutual Fund Dashboard')

option = st.sidebar.selectbox( 'Select an option:', ('View Available Schemes', 'Scheme Details','Historical NAV','Compare NAV','AUM','Performance Heatmap','Risk and Volitility Analysis'))


scheme_names = {v: k for k, v in mf.get_scheme_codes().items()}

if option == 'View Available Schemes':
    st.header('View Available Schemes')
    amc = st.sidebar.text_input('Enter AMC Name:', 'SBI')
    schemes = mf.get_available_schemes(amc)
    st.write(pd.DataFrame(schemes.items(), columns = ['Scheme Code','Scheme Name']) if schemes else 'No Schemes Found')

if option == 'Scheme Details':
    st.header('Scheme Details')
    scheme_code = scheme_names[st.sidebar.selectbox('Select a Scheme', scheme_names.keys())]
    details = pd.DataFrame(mf.get_scheme_details(scheme_code)).iloc[0]
    st.write(details)

if option == 'Historical NAV':
    st.header('Historical NAV')
    scheme_code = scheme_names[st.sidebar.selectbox('Select a Scheme', scheme_names.keys())]
    details = mf.get_scheme_historical_nav(scheme_code,as_Dataframe=True)
    st.write(details)             

if option == 'Compare NAV':
    st.header('Compare NAV')
    selected_schemes = st.sidebar.multiselect('Select a Schemes to compare', options=list(scheme_names.keys()))
    if selected_schemes:
        comparision_df = pd.DataFrame()
        for scheme in selected_schemes:
            code = scheme_names[scheme]
            data = mf.get_scheme_historical_nav(code,as_Dataframe=True)
            data = data.reset_index().rename(columns={'index':'Date'})
            data['date'] = pd.to_datetime(data['date'],dayfirst=True).sort_values()
            data['nav'] = data['nav'].replace(0,None).interpolate()
            comparision_df[scheme] = data.set_index('date')['nav']
        fig = px.line(comparision_df, title='Comparision of NAVs')
        st.plotly_chart(fig)
    else:
        st.write("Please Select atleast one scheme")

if option == 'AUM':
    st.header('AUM')
    aum_data = mf.get_average_aum('July - September 2024', False)
    if aum_data:
        aum_df = pd.DataFrame(aum_data)
        aum_df['Total AUM'] = aum_df[['AAUM Domestic','AAUM Overseas']].astype('float').sum(axis = 1)
        st.write(aum_df[['Fund Name', 'Total AUM']])
    else:
        st.write("No Data Available.")

if option == 'Performance Heatmap':
    st.header('Performance Heatmap')
    scheme_code = scheme_names[st.sidebar.selectbox('Select a Scheme', scheme_names.keys())]
    nav_data = mf.get_scheme_historical_nav(scheme_code,as_Dataframe=True)
    if not nav_data.empty:
        nav_data = nav_data.reset_index().rename(columns={'index':'date'})
        nav_data['month'] = pd.DatetimeIndex(nav_data['date']).month
        nav_data['nav'] = nav_data['nav'].astype('float')
        
        heatmap_data = nav_data.groupby('month')['dayChange'].mean().reset_index()
        heatmap_data['month'] = heatmap_data['month'].astype(str)
        fig = px.density_heatmap(heatmap_data, x = 'month', y = 'dayChange', title='NAV Performance Heatmap', color_continuous_midpoint=0)
        st.plotly_chart(fig)
    else:
        st.write("No Data Available.")

if option == 'Risk and Volitility Analysis':
    st.header('Risk and Volitility Analysis')
    scheme_name = st.sidebar.selectbox('Select a Scheme', scheme_names.keys())
    scheme_code = scheme_names[scheme_name]
    nav_data = mf.get_scheme_historical_nav(scheme_code,as_Dataframe=True)
    if not nav_data.empty:
        nav_data = nav_data.reset_index().rename(columns={'index':'date'})
        nav_data['date'] = pd.to_datetime(nav_data['date'],dayfirst=True)
        
        nav_data['nav'] = pd.to_numeric(nav_data['nav'],errors='coerce')
        nav_data = nav_data.dropna(subset=['nav'])
        
        nav_data['returns'] = nav_data['nav']/nav_data['nav'].shift(-1)-1
        nav_data = nav_data.dropna(subset=['returns'])
        
        annualized_volitility = nav_data["returns"].std() * np.sqrt(252)
        annualized_return = (1 + nav_data['returns'].mean())**252 - 1

        risk_free_rate = 0.06
        sharpe_ratio = (annualized_return - risk_free_rate) / annualized_volitility
        st.write(f'### Metrics for {scheme_name}')
        st.metric('Annualized volatility', f'{annualized_volitility:.2%}')
        st.metric('Annualized return', f'{annualized_return:.2%}')
        st.metric('sharpe ratio', f'{sharpe_ratio:.2f}')

        fig = px.scatter(
            nav_data, x = 'date', y = 'returns',
            title='Risk-Return Scatter for {scheme_name}',
            labels={'returns':'Daily Returns', 'date': 'Date'})
        st.plotly_chart(fig)