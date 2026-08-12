import pandas as pd
import plotly.express as px
import ssl

# Bypass SSL if needed for Mac
ssl._create_default_https_context = ssl._create_unverified_context

# --- 1. DATA PROCESSING ---
Google_sheet_url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vSK6MIz-xpbq51W2Snfmgn1wZM_6qKuyjbUQx7DLsOcRvijwv7S7cfcImybwilA0zrEwhWjUZX4n3ss/pub?output=xlsx'
complete_transactions_df = pd.read_excel(Google_sheet_url, sheet_name='Daily Transactions')

complete_transactions_df['Date'] = pd.to_datetime(complete_transactions_df['Date'])
complete_transactions_df['Customer_Phone'] = complete_transactions_df['Customer_Phone'].astype(str).str.replace(r'\.0$',
                                                                                                                '',
                                                                                                                regex=True).str.strip()

yesterday_date = (pd.Timestamp.today() - pd.Timedelta(days=1)).date()
day_transactions_df = complete_transactions_df[complete_transactions_df['Date'].dt.date == yesterday_date]

day_order_value = day_transactions_df['Total_Bill_Value'].sum()
total_customers_arrived = day_transactions_df['Total_Bill_Value'].count()
avera_order_value = day_order_value / total_customers_arrived if total_customers_arrived > 0 else 0

past_transactions_df = complete_transactions_df[complete_transactions_df['Date'].dt.date < yesterday_date]
past_customers_list = past_transactions_df['Customer_Phone'].unique()
returning_customers_df = day_transactions_df[day_transactions_df['Customer_Phone'].isin(past_customers_list)]

num_returning = len(returning_customers_df)
num_new = total_customers_arrived - num_returning

individual_items = day_transactions_df['Dishes_Ordered'].str.split(',').explode().str.strip()
item_counts = individual_items.value_counts()
top_item_name = item_counts.index[0] if not item_counts.empty else "N/A"
top_item_qty = item_counts.values[0] if not item_counts.empty else 0
bottom_item_name = item_counts.index[-1] if not item_counts.empty else "N/A"

# --- 2. GENERATE INTERACTIVE PLOTLY CHARTS ---

# A. Top Sellers Bar Chart (Premium Sunset Colors)
bar_html = ""
if not item_counts.empty:
    top_10 = item_counts.head(10)
    fig_bar = px.bar(
        x=top_10.index, y=top_10.values,
        text=top_10.values,
        labels={'x': '', 'y': 'Quantity Sold'},
        color=top_10.values, color_continuous_scale='Sunsetdark'
    )
    fig_bar.update_layout(
        coloraxis_showscale=False,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=30, b=20),
        font=dict(color='#334155')
    )
    bar_html = fig_bar.to_html(full_html=False, include_plotlyjs='cdn')

# B. Customer Split Donut Chart (Modern Blue & Coral)
pie_html = ""
if total_customers_arrived > 0:
    fig_pie = px.pie(
        names=['New Customers', 'Returning Customers'],
        values=[num_new, num_returning],
        hole=0.55,
        color_discrete_sequence=['#F472B6', '#38BDF8']  # Pink/Coral and Light Blue
    )
    fig_pie.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        font=dict(color='#334155')
    )
    pie_html = fig_pie.to_html(full_html=False, include_plotlyjs='cdn')

# --- 3. BUILD RESPONSIVE HTML WEBPAGE ---
html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"> <!-- THIS FIXES THE RUPEE SYMBOL! -->
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kubera Vilas Dashboard</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #F8FAFC; color: #0F172A; margin: 0; padding: 15px; }}
        h1 {{ text-align: center; color: #1E293B; margin-bottom: 5px; font-size: 26px; letter-spacing: -0.5px; }}
        p.date {{ text-align: center; color: #64748B; margin-top: 0; margin-bottom: 25px; font-weight: 500; }}

        .grid-container {{ display: grid; grid-template-columns: 1fr; gap: 15px; margin-bottom: 20px; }}
        @media (min-width: 600px) {{ .grid-container {{ grid-template-columns: repeat(3, 1fr); }} }}

        .card {{ background: white; padding: 22px; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03); text-align: center; border: 1px solid #F1F5F9; }}
        .card-title {{ font-size: 13px; color: #64748B; margin-bottom: 8px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }}
        .card-value {{ font-size: 32px; color: #0F172A; font-weight: 800; margin: 0; }}
        .card-subtext {{ font-size: 13px; color: #94A3B8; margin-top: 8px; line-height: 1.5; }}

        .chart-container {{ background: white; padding: 15px; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); margin-bottom: 20px; border: 1px solid #F1F5F9; }}
        .chart-title {{ text-align: center; color: #1E293B; font-size: 18px; margin-top: 10px; font-weight: 700; }}
    </style>
</head>
<body>

    <h1>KUBERA VILAS</h1>
    <p class="date">Daily Performance | {yesterday_date}</p>

    <!-- Top KPI Cards -->
    <div class="grid-container">
        <div class="card">
            <div class="card-title">Total Revenue</div>
            <div class="card-value" style="color: #059669;">₹{day_order_value:,.0f}</div>
        </div>
        <div class="card">
            <div class="card-title">Total Orders</div>
            <div class="card-value">{total_customers_arrived}</div>
            <div class="card-subtext">Avg Value: <b>₹{avera_order_value:,.0f}</b></div>
        </div>
        <div class="card">
            <div class="card-title">Top/Bottom Items</div>
            <div class="card-subtext" style="margin-top:0;">
                <span style="color: #D97706; font-weight: bold;">★ Best:</span> {top_item_name} ({top_item_qty})<br><br>
                <span style="color: #64748B; font-weight: bold;">▼ Least:</span> {bottom_item_name}
            </div>
        </div>
    </div>

    <!-- Charts -->
    <div class="chart-container">
        <div class="chart-title">Top 10 Selling Dishes</div>
        {bar_html}
    </div>

    <div class="chart-container">
        <div class="chart-title">Customer Acquisition</div>
        {pie_html}
    </div>

</body>
</html>
"""

# Save the file WITH UTF-8 ENCODING!
html_filename = f"Kubera_Vilas_Dashboard_{yesterday_date}.html"
with open(html_filename, "w", encoding="utf-8") as file:
    file.write(html_template)

print(f"Mobile-friendly dashboard generated: {html_filename}")