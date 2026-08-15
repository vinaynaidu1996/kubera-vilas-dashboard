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

# --- CUSTOM CSS FOR DARK MODE & WHITE VISIBILITY ---
st.markdown("""
    <style>
    /* Global Background */
    .stApp { background-color: #0b0f19; color: #ffffff; }

    /* Standard Cards */
    .dashboard-card {
        background-color: #111827;
        border: 1px solid #1f2937;
        padding: 22px;
        border-radius: 16px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
        margin-bottom: 25px;
    }

    /* UNIFIED EQUAL-HEIGHT KPI CARDS */
    .kpi-card {
        background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
        border-radius: 16px;
        padding: 22px;
        text-align: center;
        min-height: 230px; /* Increased to ensure ALL tiles perfectly match the height of the NPS tile */
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        margin-bottom: 25px;
    }

    .kpi-revenue { border: 1px solid #d97706; box-shadow: 0 8px 20px rgba(217, 119, 6, 0.2); }
    .kpi-orders { border: 1px solid #0284c7; box-shadow: 0 8px 20px rgba(2, 132, 199, 0.2); }
    .kpi-aov { border: 1px solid #db2777; box-shadow: 0 8px 20px rgba(219, 39, 119, 0.2); }
    .kpi-nps { border: 1px solid #a855f7; box-shadow: 0 8px 20px rgba(168, 85, 247, 0.2); }

    /* KPI Value Typography */
    .gold-metric { color: #fbbf24 !important; font-weight: 800; font-size: 42px !important; margin: 2px 0 !important; }
    .cyan-metric { color: #38bdf8 !important; font-weight: 800; font-size: 42px !important; margin: 2px 0 !important; }
    .pink-metric { color: #f472b6 !important; font-weight: 800; font-size: 42px !important; margin: 2px 0 !important; }
    .purple-metric { color: #c084fc !important; font-weight: 800; font-size: 42px !important; margin: 2px 0 !important; }
    .metric-title { color: #f8fafc; font-size: 15px; text-transform: uppercase; font-weight: 800; margin-bottom: 4px; letter-spacing: 1px; }

    /* STREAMLIT TABS: FORCE BRIGHT WHITE TEXT FOR ALL STATES */
    .stTabs [data-baseweb="tab-list"] { gap: 15px; margin-bottom: 20px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #1e293b !important; 
        border-radius: 10px 10px 0 0 !important; 
        padding: 12px 28px !important; 
        border: 1px solid #334155 !important; 
        border-bottom: none !important;
    }
    .stTabs [data-baseweb="tab"] * { 
        color: #ffffff !important; 
        font-size: 18px !important; 
        font-weight: 800 !important; 
    }
    .stTabs [aria-selected="true"] { 
        background: linear-gradient(135deg, #2e1065 0%, #3b0764 100%) !important; 
        border-top: 4px solid #c084fc !important; 
    }
    .stTabs [aria-selected="true"] * { 
        color: #ffffff !important; 
    }

    /* Sidebar styling */
    div[data-testid="stSidebar"] { background-color: #030712; }
    div[data-testid="stSidebar"] * { color: #ffffff !important; font-size: 16px; }

    /* Make Details summary marker white */
    details summary { color: #f8fafc; }
    </style>
""", unsafe_allow_html=True)

# --- HIDE STREAMLIT BRANDING UI & DEVELOPER BADGE ---
st.markdown("""
    <style>
    /* Hide menus and footers */
    #MainMenu {visibility: hidden !important; display: none !important;}
    footer {visibility: hidden !important; display: none !important;}
    [data-testid="stFooter"] {visibility: hidden !important; display: none !important;}
    
    /* Hide specific Streamlit Deploy & Source buttons */
    .stAppDeployButton {display: none !important;}
    [data-testid="stAppDeployButton"] {display: none !important;}
    button[title="View app source"] {display: none !important;}
    
    /* Hide the Streamlit Community Cloud Developer Badge (Profile Picture) */
    div[class^="viewerBadge"] {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# --- PASSWORD PROTECTION (Session State to Hide After Login) ---
PASSWORD = "admin"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_pw1, col_pw2, col_pw3 = st.columns([1, 2, 1])

    with col_pw2:
        entered_password = st.text_input("🔒 Enter Dashboard Password", type="password")

        if entered_password == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        elif entered_password != "":
            st.warning("Please enter the correct password to access the Kubera Vilas Dashboard.")

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
day_df = trans_df[trans_df['Date'].dt.date == selected_date]
prev_date = selected_date - pd.Timedelta(days=1)
prev_day_df = trans_df[trans_df['Date'].dt.date == prev_date]
day_feed_df = feed_df[feed_df['Call_Date'].dt.date == selected_date]

# --- HEADER WITH LOGO ---
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.image("IMG_5755 2.png", width=70)
with col_title:
    st.markdown("<h1 style='color: #ffffff; margin-bottom: 0px; font-size: 32px;'>KUBERA VILAS</h1>",
                unsafe_allow_html=True)

st.markdown(
    f"<p style='color: #cbd5e1; margin-top: -5px; font-size: 22px; margin-bottom: 20px;'><b>{selected_date}</b></p>",
    unsafe_allow_html=True)

if day_df.empty and day_feed_df.empty:
    st.info(f"No transactions or feedback recorded for {selected_date}.")
    st.stop()

# --- CREATE TWO TABS WITH BRIGHT WHITE LABELS ---
tab_ops, tab_cx = st.tabs(["📊 SALES & OPERATIONS", "⭐ CUSTOMER EXPERIENCE"])

# ==========================================
# TAB 1: SALES & OPERATIONS
# ==========================================
with tab_ops:
    if day_df.empty:
        st.warning("No sales data for this date.")
    else:
        # CALCULATE KPIS
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

        individual_items = day_df['Dishes_Ordered'].str.split(',').explode().str.strip()
        item_counts = individual_items.value_counts()
        top_3 = item_counts.head(3)
        bottom_3 = item_counts.tail(3)

        # AI SUMMARY
        rev_symbol = "▲" if rev_diff >= 0 else "▼"
        top_dish_name = top_3.index[0] if not top_3.empty else "N/A"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e1b4b 0%, #311042 100%); border-left: 6px solid #a855f7; padding: 20px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 10px rgba(0,0,0,0.5);">
            <h4 style="color: #d8b4fe; margin: 0 0 8px 0; font-size: 19px;">🤖 AI Daily Performance Summary</h4>
            <p style="color: #ffffff; font-size: 16px; margin: 0; line-height: 1.6;">
                On <b>{selected_date}</b>, Kubera Vilas processed <b>{orders} orders</b> generating <b>₹{revenue:,.0f}</b> ({rev_symbol} {abs(rev_dod_pct):.1f}% vs yesterday). 
                The top-performing item was <b>{top_dish_name}</b>. Retention stood at <b>{num_returning} returning</b> vs <b>{num_new} new customers</b>.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # CORE METRIC CARDS
        col1, col2, col3 = st.columns(3)
        rev_color = "#4ade80" if rev_diff >= 0 else "#f87171"
        ord_color = "#4ade80" if ord_diff >= 0 else "#f87171"

        with col1:
            st.markdown(f"""
            <div class="kpi-card kpi-revenue">
                <p class="metric-title">Total Revenue</p>
                <p class="gold-metric">₹{revenue:,.0f}</p>
                <p style="color: {rev_color}; font-size: 15px; font-weight: bold; margin:0;">{"▲" if rev_diff >= 0 else "▼"} ₹{abs(rev_diff):,.0f} ({'+' if rev_diff >= 0 else '-'}{abs(rev_dod_pct):.1f}%)</p>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="kpi-card kpi-orders">
                <p class="metric-title">Total Orders</p>
                <p class="cyan-metric">{orders}</p>
                <p style="color: {ord_color}; font-size: 15px; font-weight: bold; margin:0;">{"▲" if ord_diff >= 0 else "▼"} {abs(ord_diff)} orders ({'+' if ord_diff >= 0 else '-'}{abs(ord_dod_pct):.1f}%)</p>
            </div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="kpi-card kpi-aov">
                <p class="metric-title">Avg Order Value</p>
                <p class="pink-metric">₹{avg_order_value:,.0f}</p>
                <p style="color: #cbd5e1; font-size: 15px; font-weight: bold; margin:0;">Stable vs Yesterday</p>
            </div>""", unsafe_allow_html=True)

        # SPACING GAP BEFORE BEST/LEAST SELLERS
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

        # TOP 3 & LEAST 3
        col_top, col_bot = st.columns(2)
        with col_top:
            top_text = "<br>".join(
                [f"<b>{i + 1}. {item}</b> ({qty} units)" for i, (item, qty) in enumerate(top_3.items())])
            st.markdown(
                f"""<div class="dashboard-card" style="border-left: 5px solid #4ade80;"><p style="color: #4ade80; font-weight: 800; font-size: 18px;">🏆 Top 3 Best Sellers</p><p style="font-size: 16px;">{top_text}</p></div>""",
                unsafe_allow_html=True)
        with col_bot:
            bot_text = "<br>".join([f"<b>{item}</b> ({qty} units)" for item, qty in bottom_3.items()])
            st.markdown(
                f"""<div class="dashboard-card" style="border-left: 5px solid #f87171;"><p style="color: #f87171; font-weight: 800; font-size: 18px;">📉 Least 3 Sold Items</p><p style="font-size: 16px;">{bot_text}</p></div>""",
                unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        st.divider()

        # CHARTS WITH FULL HEIGHT (height=420)
        col_charts1, col_charts2 = st.columns(2)

        with col_charts1:
            top_10 = item_counts.head(10)
            max_bar_val = top_10.values.max() if not top_10.empty else 10

            fig_bar = px.bar(
                x=top_10.index, y=top_10.values, text=top_10.values,
                title="Individual Items Sold (Top 10)",
                color=top_10.values, color_continuous_scale='Tealgrn'
            )
            fig_bar.update_layout(
                height=420,
                coloraxis_showscale=False,
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#ffffff", size=14),
                title_font=dict(size=19, color="#ffffff"),
                margin=dict(l=10, r=10, t=50, b=10),
                xaxis=dict(tickfont=dict(size=13, color="#ffffff")),
                yaxis=dict(tickfont=dict(size=13, color="#ffffff"), range=[0, max_bar_val * 1.25])
            )
            fig_bar.update_traces(
                textposition='outside',
                textfont=dict(size=15, color='#ffffff', family="Arial Black"),
                marker_line_color='#ffffff',
                marker_line_width=1.5
            )
            if max_bar_val < 15: fig_bar.update_yaxes(dtick=1)
            st.plotly_chart(fig_bar, width='stretch', config={'staticPlot': True})

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

            fig_cat = px.bar(
                cat_counts, x='Quantity', y='Category', orientation='h',
                text='Quantity', title="Sales Volume by Category",
                color='Quantity', color_continuous_scale='Plasma'
            )
            fig_cat.update_layout(
                height=420,
                coloraxis_showscale=False,
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#ffffff", size=14),
                title_font=dict(size=19, color="#ffffff"),
                margin=dict(l=10, r=10, t=50, b=10),
                xaxis=dict(tickfont=dict(size=13, color="#ffffff")),
                yaxis=dict(tickfont=dict(size=13, color="#ffffff"))
            )
            fig_cat.update_traces(
                textfont=dict(size=15, color='#ffffff', family="Arial Black"),
                marker_line_color='#ffffff',
                marker_line_width=1.5
            )
            st.plotly_chart(fig_cat, width='stretch', config={'staticPlot': True})

        # COMBOS & PIE CHART
        col_c, col_p = st.columns(2)
        with col_c:
            st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
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
                    f"""<div class="dashboard-card" style="border-left: 5px solid #38bdf8; height: 100%;"><p style="color: #38bdf8; font-weight: 800; font-size: 18px;">🔗 Top Popular Combos</p><p style="font-size: 16px;">{combo_text}</p></div>""",
                    unsafe_allow_html=True)

        with col_p:
            if orders > 0:
                fig_pie = px.pie(
                    names=['New', 'Returning'], values=[num_new, num_returning], hole=0.55,
                    title="Customer Acquisition Split",
                    color_discrete_sequence=['#38bdf8', '#f472b6']
                )
                fig_pie.update_traces(
                    textinfo='value+percent',
                    textfont=dict(size=15, color='#ffffff', family="Arial Black"),
                    marker=dict(line=dict(color='#0b0f19', width=3))
                )
                fig_pie.update_layout(
                    height=380,
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="#ffffff", size=14),
                    title_font=dict(size=19, color="#ffffff"),
                    margin=dict(t=50, b=20, l=10, r=10),
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5,
                                font=dict(size=15, color="#ffffff"))
                )
                st.plotly_chart(fig_pie, width='stretch', config={'staticPlot': True})

# ==========================================
# TAB 2: CUSTOMER EXPERIENCE
# ==========================================
with tab_cx:
    if day_feed_df.empty:
        st.warning("No customer feedback collected for this date.")
    else:
        # CALCULATE CX METRICS
        nps_scores = day_feed_df['NPS_Score(How likely would you refer a friend)']
        promoters = len(nps_scores[nps_scores >= 9])
        passives = len(nps_scores[(nps_scores >= 7) & (nps_scores <= 8)])
        detractors = len(nps_scores[nps_scores <= 6])
        total_surveys = len(nps_scores)

        nps = ((promoters - detractors) / total_surveys) * 100 if total_surveys > 0 else 0
        complaints = len(day_feed_df[day_feed_df['Complaint_Flag'].str.upper() == 'YES'])
        comp_rate = (complaints / total_surveys) * 100 if total_surveys > 0 else 0

        # CX KPI CARDS (ALL UNIFORMLY MATCHED IN HEIGHT)
        cx_c1, cx_c2, cx_c3 = st.columns(3)

        with cx_c1:
            st.markdown(f"""
            <div class="kpi-card kpi-orders">
                <p class="metric-title">Total Feedback Calls</p>
                <p class="cyan-metric">{total_surveys}</p>
            </div>""", unsafe_allow_html=True)

        with cx_c2:
            nps_color = "#4ade80" if nps > 50 else ("#fbbf24" if nps > 0 else "#f87171")

            st.markdown(f"""
            <div class="kpi-card kpi-nps" style="border-color: {nps_color};">
                <p class="metric-title">Net Promoter Score (NPS)</p>
                <p class="purple-metric" style="color: {nps_color} !important;">{nps:,.0f}</p>
                <details style="margin-top: 15px; width: 100%; text-align: left; background-color: #2e1065; border: 1px solid #c084fc; border-radius: 8px; padding: 10px; box-sizing: border-box;">
                    <summary style="cursor: pointer; font-weight: bold; font-size: 14px; outline: none;">
                        ℹ️ What is NPS?
                    </summary>
                    <p style="color: #e2e8f0; font-size: 13px; margin-top: 10px; margin-bottom: 0; line-height: 1.4;">
                        NPS measures true customer loyalty (-100 to +100).<br><br>
                        <b>Promoters (9-10):</b> Enthusiastic<br>
                        <b>Passives (7-8):</b> Satisfied<br>
                        <b>Detractors (0-6):</b> Unhappy<br>
                        <br><i>NPS = % Promoters - % Detractors</i>
                    </p>
                </details>
            </div>""", unsafe_allow_html=True)

        with cx_c3:
            comp_color = "#f87171" if comp_rate > 10 else "#4ade80"
            st.markdown(f"""
            <div class="kpi-card kpi-aov" style="border-color: {comp_color};">
                <p class="metric-title">Complaint Rate</p>
                <p class="pink-metric" style="color: {comp_color} !important;">{complaints} Total</p>
                <p style="color: #cbd5e1; font-size: 15px; font-weight: bold; margin:0;">({comp_rate:.1f}%)</p>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        st.divider()

        # RADAR CHART & SENTIMENT
        rad_col, sent_col = st.columns(2)

        with rad_col:
            categories = ['Food_Quality', 'Ambiance', 'Service_Speed', 'Staff_Hospitality', 'Menu_Knowledge']
            avgs = [day_feed_df[c].mean() for c in categories]

            fig_radar = go.Figure(data=go.Scatterpolar(
                r=avgs + [avgs[0]],
                theta=['Food', 'Ambiance', 'Service', 'Hospitality', 'Menu Knowledge', 'Food'],
                fill='toself', line_color='#c084fc'
            ))
            fig_radar.update_layout(
                height=420,
                polar=dict(radialaxis=dict(visible=True, range=[0, 5], gridcolor='#334155',
                                           tickfont=dict(color='#cbd5e1', size=13)), bgcolor='#111827'),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#ffffff", size=15),
                title=dict(text="5-Pillar Satisfaction Radar", font=dict(size=19, color="#ffffff")),
                margin=dict(t=50, b=20, l=10, r=10)
            )
            st.plotly_chart(fig_radar, width='stretch', config={'staticPlot': True})

        with sent_col:
            st.markdown("<h4 style='color: #ffffff; font-size: 19px; margin-bottom: 15px;'>Dish Sentiment Tracker</h4>",
                        unsafe_allow_html=True)

            liked = day_feed_df['Most_Liked_Dish'].dropna().value_counts().head(3)
            disliked = day_feed_df['Least_Liked_Dish'].dropna().value_counts().head(3)

            st.markdown(
                f"<div class='dashboard-card' style='border-left: 5px solid #4ade80;'><p style='color: #4ade80; font-weight:800; font-size: 18px;'>👍 Most Loved Dishes Today</p><p style='font-size: 16px;'>{'<br>'.join([f'• {d} ({c} mentions)' for d, c in liked.items()]) if not liked.empty else 'No data'}</p></div>",
                unsafe_allow_html=True)
            st.markdown(
                f"<div class='dashboard-card' style='border-left: 5px solid #f87171;'><p style='color: #f87171; font-weight:800; font-size: 18px;'>👎 Most Disliked Dishes Today</p><p style='font-size: 16px;'>{'<br>'.join([f'• {d} ({c} mentions)' for d, c in disliked.items()]) if not disliked.empty else 'No negative feedback!'}</p></div>",
                unsafe_allow_html=True)

        # COMPLAINT LOG
        if complaints > 0:
            st.divider()
            st.markdown("<h4 style='color: #f87171; font-size: 19px;'>⚠️ Action Required: Complaint Log</h4>",
                        unsafe_allow_html=True)
            complaint_details = day_feed_df[day_feed_df['Complaint_Flag'].str.upper() == 'YES'][
                ['Order_ID', 'Complaint_Details']].dropna()
            for index, row in complaint_details.iterrows():
                st.warning(f"**Order {row['Order_ID']}**: {row['Complaint_Details']}")
