import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from itertools import combinations
import ssl

# Bypass Mac SSL issues for Google Sheets
ssl._create_default_https_context = ssl._create_unverified_context

# --- PAGE SETUP ---
st.set_page_config(page_title="Kubera Vilas Dashboard", page_icon="🍽️", layout="wide")

# --- CUSTOM CSS FOR DARK MODE, BORDERS, SHADOWS & GOLD ACCENTS ---
st.markdown("""
    <style>
    /* Global Dark Mode Background */
    .stApp { background-color: #0b0f19; color: #f8fafc; }
    /* Sleek Dark Mode Cards */
    .dashboard-card {
        background-color: #111827;
        border: 1px solid #1f2937;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
        margin-bottom: 20px;
    }
    /* Gold color for Revenue Highlights */
    .gold-metric { color: #fbbf24 !important; font-weight: 800; font-size: 38px !important; }
    /* Sidebar styling */
    div[data-testid="stSidebar"] { background-color: #030712; }
    div[data-testid="stSidebar"] * { color: #f8fafc !important; }
    /* Streamlit Tabs styling */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #111827; border-radius: 8px 8px 0 0; padding: 10px 20px; border: 1px solid #1f2937; border-bottom: none;}
    .stTabs [aria-selected="true"] { background-color: #1e1b4b; border-top: 3px solid #a855f7; }
    </style>
""", unsafe_allow_html=True)

# --- PASSWORD PROTECTION ---
PASSWORD = "admin"
entered_password = st.sidebar.text_input("Enter Password", type="password")
if entered_password != PASSWORD:
    st.sidebar.warning("Please enter the correct password to view the dashboard.")
    st.stop()


# --- DATA LOADING (FROM GOOGLE SHEETS) ---
@st.cache_data(ttl=600)
def load_data():
    url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vSK6MIz-xpbq51W2Snfmgn1wZM_6qKuyjbUQx7DLsOcRvijwv7S7cfcImybwilA0zrEwhWjUZX4n3ss/pub?output=xlsx'
    xls = pd.ExcelFile(url)

    trans_df = pd.read_excel(xls, sheet_name='Daily Transactions')
    trans_df['Date'] = pd.to_datetime(trans_df['Date'])
    trans_df['Customer_Phone'] = trans_df['Customer_Phone'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

    feed_df = pd.read_excel(xls, sheet_name='Customer Feedback')
    feed_df['Call_Date'] = pd.to_datetime(feed_df['Call_Date'])

    return trans_df, feed_df


try:
    trans_df, feed_df = load_data()
except Exception as e:
    st.error("Could not load data from Google Sheets. Please check your internet connection.")
    st.stop()

# --- SIDEBAR: DATE PICKER ---
st.sidebar.header("📅 Filter Date")
min_date = trans_df['Date'].min().date()
max_date = trans_df['Date'].max().date()
yesterday = (pd.Timestamp.today() - pd.Timedelta(days=1)).date()
default_date = yesterday if min_date <= yesterday <= max_date else max_date

selected_date = st.sidebar.date_input("Select Date", default_date, min_value=min_date, max_value=max_date)

# --- FILTER DATA ---
# Transactions
day_df = trans_df[trans_df['Date'].dt.date == selected_date]
prev_date = selected_date - pd.Timedelta(days=1)
prev_day_df = trans_df[trans_df['Date'].dt.date == prev_date]

# Feedback
day_feed_df = feed_df[feed_df['Call_Date'].dt.date == selected_date]

# --- HEADER WITH LOGO ---
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.image("https://cdn-icons-png.flaticon.com/512/3075/3075977.png", width=65)
with col_title:
    st.markdown("<h1 style='color: #f8fafc; margin-bottom: 0px; font-size: 28px;'>KUBERA VILAS</h1>",
                unsafe_allow_html=True)
st.markdown(
    f"<p style='color: #94a3b8; margin-top: -5px; font-size: 14px;'>Enterprise Dashboard | <b>{selected_date}</b></p>",
    unsafe_allow_html=True)

if day_df.empty and day_feed_df.empty:
    st.info(f"No transactions or feedback recorded for {selected_date}.")
    st.stop()

# --- CREATE TWO TABS ---
tab_ops, tab_cx = st.tabs(["📊 Sales & Operations", "⭐ Customer Experience"])

# ==========================================
# TAB 1: SALES & OPERATIONS
# ==========================================
with tab_ops:
    if day_df.empty:
        st.warning("No sales data for this date.")
    else:
        # CALCULATE KPIS & COMPARISONS
        revenue = day_df['Total_Bill_Value'].sum()
        prev_revenue = prev_day_df['Total_Bill_Value'].sum()
        rev_diff = revenue - prev_revenue
        rev_dod_pct = ((revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0

        orders = day_df['Total_Bill_Value'].count()
        prev_orders = prev_day_df['Total_Bill_Value'].count()
        ord_diff = orders - prev_orders
        ord_dod_pct = ((orders - prev_orders) / prev_orders * 100) if prev_orders > 0 else 0
        avg_order_value = revenue / orders if orders > 0 else 0

        past_df = trans_df[trans_df['Date'].dt.date < selected_date]
        num_returning = len(day_df[day_df['Customer_Phone'].isin(past_df['Customer_Phone'].unique())])
        num_new = orders - num_returning

        # Item Counts
        individual_items = day_df['Dishes_Ordered'].str.split(',').explode().str.strip()
        item_counts = individual_items.value_counts()
        top_3 = item_counts.head(3)
        bottom_3 = item_counts.tail(3)

        # AI SUMMARY
        rev_symbol = "▲" if rev_diff >= 0 else "▼"
        top_dish_name = top_3.index[0] if not top_3.empty else "N/A"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e1b4b 0%, #311042 100%); border-left: 5px solid #a855f7; padding: 15px; border-radius: 12px; margin-bottom: 20px;">
            <h4 style="color: #c084fc; margin: 0 0 8px 0; font-size: 16px;">🤖 AI Daily Performance Summary</h4>
            <p style="color: #e2e8f0; font-size: 14px; margin: 0;">
                On <b>{selected_date}</b>, Kubera Vilas processed <b>{orders} orders</b> generating <b>₹{revenue:,.0f}</b> ({rev_symbol} {abs(rev_dod_pct):.1f}% vs yesterday). 
                The top-performing item was <b>{top_dish_name}</b>. Retention stood at <b>{num_returning} returning</b> vs <b>{num_new} new customers</b>.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # 3 CORE METRIC CARDS
        col1, col2, col3 = st.columns(3)
        rev_color = "#4ade80" if rev_diff >= 0 else "#f87171"
        ord_color = "#4ade80" if ord_diff >= 0 else "#f87171"

        with col1:
            st.markdown(
                f"""<div class="dashboard-card" style="text-align: center;"><p style="color: #94a3b8; font-weight: 700;">Total Revenue</p><p class="gold-metric">₹{revenue:,.0f}</p><p style="color: {rev_color};">{"▲" if rev_diff >= 0 else "▼"} ₹{abs(rev_diff):,.0f} ({'+' if rev_diff >= 0 else '-'}{abs(rev_dod_pct):.1f}%)</p></div>""",
                unsafe_allow_html=True)
        with col2:
            st.markdown(
                f"""<div class="dashboard-card" style="text-align: center;"><p style="color: #94a3b8; font-weight: 700;">Total Orders</p><p style="color: #38bdf8; font-size: 38px; font-weight:800; margin:0;">{orders}</p><p style="color: {ord_color};">{"▲" if ord_diff >= 0 else "▼"} {abs(ord_diff)} orders ({'+' if ord_diff >= 0 else '-'}{abs(ord_dod_pct):.1f}%)</p></div>""",
                unsafe_allow_html=True)
        with col3:
            st.markdown(
                f"""<div class="dashboard-card" style="text-align: center;"><p style="color: #94a3b8; font-weight: 700;">Avg Order Value</p><p style="color: #f472b6; font-size: 38px; font-weight:800; margin:0;">₹{avg_order_value:,.0f}</p><p style="color: #94a3b8;">Stable vs Yesterday</p></div>""",
                unsafe_allow_html=True)

        # TOP 3 & LEAST 3
        col_top, col_bot = st.columns(2)
        with col_top:
            top_text = "<br>".join(
                [f"<b>{i + 1}. {item}</b> ({qty} units)" for i, (item, qty) in enumerate(top_3.items())])
            st.markdown(
                f"""<div class="dashboard-card" style="border-left: 4px solid #4ade80;"><p style="color: #4ade80; font-weight: 700;">🏆 Top 3 Best Sellers</p><p>{top_text}</p></div>""",
                unsafe_allow_html=True)
        with col_bot:
            bot_text = "<br>".join([f"<b>{item}</b> ({qty} units)" for item, qty in bottom_3.items()])
            st.markdown(
                f"""<div class="dashboard-card" style="border-left: 4px solid #f87171;"><p style="color: #f87171; font-weight: 700;">📉 Least 3 Sold Items</p><p>{bot_text}</p></div>""",
                unsafe_allow_html=True)

        st.divider()

        # INDIVIDUAL DISHES GRAPH & CATEGORY GRAPH
        col_charts1, col_charts2 = st.columns(2)

        with col_charts1:
            top_10 = item_counts.head(10)
            fig_bar = px.bar(x=top_10.index, y=top_10.values, text=top_10.values,
                             title="Individual Items Sold (Top 10)", color=top_10.values,
                             color_continuous_scale='Oryel')
            fig_bar.update_layout(coloraxis_showscale=False, paper_bgcolor='rgba(0,0,0,0)',
                                  plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#f8fafc"),
                                  margin=dict(l=10, r=10, t=40, b=10))
            fig_bar.update_traces(textposition='outside')
            if top_10.values.max() < 15: fig_bar.update_yaxes(dtick=1)
            st.plotly_chart(fig_bar, width='stretch')

        with col_charts2:
            def get_category(dish):
                d = dish.lower()
                if 'biryani' in d:
                    return 'Biryanis'
                elif any(x in d for x in ['coke', 'sprite', 'soda', 'pepsi']):
                    return 'Beverages'
                elif any(x in d for x in ['naan', 'roti', 'rice', 'pulao']):
                    return 'Breads & Rice'
                else:
                    return 'Starters & Mains'


            cat_df = day_df.copy()
            cat_df['Item_List'] = cat_df['Dishes_Ordered'].apply(lambda x: [i.strip() for i in str(x).split(',')])
            cat_df = cat_df.explode('Item_List')
            cat_df['Category'] = cat_df['Item_List'].apply(get_category)
            cat_counts = cat_df['Category'].value_counts().reset_index()
            cat_counts.columns = ['Category', 'Quantity']

            fig_cat = px.bar(cat_counts, x='Quantity', y='Category', orientation='h', text='Quantity',
                             title="Sales Volume by Category", color='Quantity', color_continuous_scale='Plasma')
            fig_cat.update_layout(coloraxis_showscale=False, paper_bgcolor='rgba(0,0,0,0)',
                                  plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#f8fafc"),
                                  margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_cat, width='stretch')

        # COMBOS & PIE CHART
        col_c, col_p = st.columns(2)
        with col_c:
            combo_list = []
            for dishes_str in day_df['Dishes_Ordered']:
                items = [i.strip() for i in str(dishes_str).split(',')]
                if len(items) > 1:
                    for pair in combinations(sorted(set(items)), 2): combo_list.append(pair)

            if combo_list:
                combo_series = pd.Series(combo_list).value_counts().head(4)
                combo_text = "<br><br>".join(
                    [f"✨ <b>{pair[0]}</b> + <b>{pair[1]}</b> ({count} times)" for pair, count in combo_series.items()])
                st.markdown(
                    f"""<div class="dashboard-card" style="border-left: 4px solid #38bdf8; height: 100%;"><p style="color: #38bdf8; font-weight: 700;">🔗 Top Combos (Bought Together)</p><p>{combo_text}</p></div>""",
                    unsafe_allow_html=True)

        with col_p:
            if orders > 0:
                fig_pie = px.pie(names=['New', 'Returning'], values=[num_new, num_returning], hole=0.55,
                                 title="Customer Acquisition", color_discrete_sequence=['#38bdf8', '#f472b6'])
                fig_pie.update_traces(textinfo='value+percent')
                fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                      font=dict(color="#f8fafc"), margin=dict(t=40, b=10),
                                      legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5))
                st.plotly_chart(fig_pie, width='stretch')

# ==========================================
# TAB 2: CUSTOMER EXPERIENCE
# ==========================================
with tab_cx:
    if day_feed_df.empty:
        st.warning("No customer feedback collected for this date.")
    else:
        # 1. NPS SCORE CALCULATION
        nps_scores = day_feed_df['NPS_Score(How likely would you refer a friend)']
        promoters = len(nps_scores[nps_scores >= 9])
        passives = len(nps_scores[(nps_scores >= 7) & (nps_scores <= 8)])
        detractors = len(nps_scores[nps_scores <= 6])
        total_surveys = len(nps_scores)

        nps = ((promoters - detractors) / total_surveys) * 100 if total_surveys > 0 else 0

        # 2. COMPLAINT RATE
        complaints = len(day_feed_df[day_feed_df['Complaint_Flag'].str.upper() == 'YES'])
        comp_rate = (complaints / total_surveys) * 100 if total_surveys > 0 else 0

        # Draw CX KPI Cards
        cx_c1, cx_c2, cx_c3 = st.columns(3)
        with cx_c1:
            st.markdown(
                f"""<div class="dashboard-card" style="text-align: center;"><p style="color: #94a3b8; font-weight: 700;">Total Feedback Calls</p><p style="color: #f8fafc; font-size: 38px; font-weight:800; margin:0;">{total_surveys}</p></div>""",
                unsafe_allow_html=True)
        with cx_c2:
            nps_color = "#4ade80" if nps > 50 else ("#fbbf24" if nps > 0 else "#f87171")
            st.markdown(
                f"""<div class="dashboard-card" style="text-align: center;"><p style="color: #94a3b8; font-weight: 700;">Net Promoter Score (NPS)</p><p style="color: {nps_color}; font-size: 38px; font-weight:800; margin:0;">{nps:,.0f}</p></div>""",
                unsafe_allow_html=True)
        with cx_c3:
            comp_color = "#f87171" if comp_rate > 10 else "#4ade80"
            st.markdown(
                f"""<div class="dashboard-card" style="text-align: center;"><p style="color: #94a3b8; font-weight: 700;">Complaint Rate</p><p style="color: {comp_color}; font-size: 38px; font-weight:800; margin:0;">{comp_rate:.1f}%</p></div>""",
                unsafe_allow_html=True)

        st.divider()

        # RADAR CHART & SENTIMENT
        rad_col, sent_col = st.columns(2)

        with rad_col:
            categories = ['Food_Quality', 'Ambiance', 'Service_Speed', 'Staff_Hospitality', 'Menu_Knowledge']
            avgs = [day_feed_df[c].mean() for c in categories]

            fig_radar = go.Figure(data=go.Scatterpolar(
                r=avgs + [avgs[0]],
                theta=['Food', 'Ambiance', 'Service', 'Hospitality', 'Menu Knowledge', 'Food'],
                fill='toself', line_color='#a855f7'
            ))
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 5], gridcolor='#334155', tickfont=dict(color='#94a3b8')),
                    bgcolor='#111827'),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#f8fafc"),
                title="5-Pillar Satisfaction Radar"
            )
            st.plotly_chart(fig_radar, width='stretch')

        with sent_col:
            st.markdown("<h4 style='color: #f8fafc;'>Dish Sentiment Tracker</h4>", unsafe_allow_html=True)

            liked = day_feed_df['Most_Liked_Dish'].dropna().value_counts().head(3)
            disliked = day_feed_df['Least_Liked_Dish'].dropna().value_counts().head(3)

            st.markdown(
                f"<div class='dashboard-card' style='border-left: 4px solid #4ade80;'><p style='color: #4ade80; font-weight:bold;'>👍 Most Loved Dishes Today</p><p>{'<br>'.join([f'• {d} ({c} mentions)' for d, c in liked.items()]) if not liked.empty else 'No data'}</p></div>",
                unsafe_allow_html=True)
            st.markdown(
                f"<div class='dashboard-card' style='border-left: 4px solid #f87171;'><p style='color: #f87171; font-weight:bold;'>👎 Most Disliked Dishes Today</p><p>{'<br>'.join([f'• {d} ({c} mentions)' for d, c in disliked.items()]) if not disliked.empty else 'No negative feedback!'}</p></div>",
                unsafe_allow_html=True)

        # COMPLAINT LOG
        if complaints > 0:
            st.divider()
            st.markdown("<h4 style='color: #f87171;'>⚠️ Complaint Action Log</h4>", unsafe_allow_html=True)
            complaint_details = day_feed_df[day_feed_df['Complaint_Flag'].str.upper() == 'YES'][
                ['Order_ID', 'Complaint_Details']].dropna()
            for index, row in complaint_details.iterrows():
                st.warning(f"**Order {row['Order_ID']}**: {row['Complaint_Details']}")