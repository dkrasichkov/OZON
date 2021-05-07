
################## Importing libraries ##################

# Base
import pandas as pd
import requests
from io import BytesIO
from datetime import datetime
# Parsing
import tiingo as tiingo
from tiingo import TiingoClient
import yfinance as yf
import finnhub
# Visuals
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
# Streamlit
import streamlit as st
# TIINGO API setup
TIINGO_API_KEY = "c5effc453b818a3236c1d8636fd954344a14ddb9"
config = {
    'api_key': TIINGO_API_KEY,
    'session': True
}
client = TiingoClient(config)

finnhub_client = finnhub.Client(api_key='c29u1fqad3iap8v7c0t0')

################## Data  ##################

peergroup = ['OZON', 'FTCH', 'FVRR', 'GRUB', 'QRTEA', 'SFIX', 'AMZN', 'DASH', 'XLY']

metrics = ['metric.revenueGrowthTTMYoy',
           'metric.epsGrowthTTMYoy',
           'metric.grossMarginAnnual',
           'metric.revenueEmployeeTTM',
           'metric.netIncomeEmployeeTTM',
           'metric.freeOperatingCashFlow/revenueTTM',
           'metric.receivablesTurnoverAnnual',
           'metric.inventoryTurnoverAnnual',
           'metric.currentRatioAnnual',
           'metric.quickRatioAnnual',
           'metric.longTermDebt/equityAnnual',
           'metric.totalDebt/totalEquityAnnual',
           'metric.pbAnnual',
           'metric.psTTM']
peerfunds = []
for i in peergroup[0:-2]:
    x = pd.json_normalize(finnhub_client.company_basic_financials(i, 'all'))[metrics].rename({0:i}, axis = 0)
    peerfunds.append(x)
peerfunds = pd.concat(peerfunds, axis = 0, ignore_index=False)

start = '2020-12-01'
today = datetime.today().strftime('%Y-%m-%d')

prices = client.get_dataframe(peergroup, frequency='daily',
                            metric_name='close',
                            startDate=start,
                            endDate=today).dropna()

returns = round((prices.shift(1) - prices.shift(2)) / prices.shift(2), 4).cumsum()*100

ozon = pd.json_normalize(client.get_ticker_price('OZON', startDate=start,
                                       endDate=today,
                                       fmt='json',
                                       frequency='daily')
                        )[['close', 'volume', 'date']].set_index('date')

ozon['14dMA'] = ozon['close'].rolling(window = 14).mean()

recomedations = pd.json_normalize(finnhub_client.recommendation_trends('OZON')).set_index('period')
recomedations.drop('symbol', axis = 1, inplace = True)
recomedations.rename({'buy':'Buy', 'hold':'Hold', 'sell':'Sell', 'strongBuy': 'Strong Buy', 'strongSell':'Strong Sell'}, axis = 1, inplace = True)

################## App ##################

# Sidebar

st.sidebar.title('Company Related News')

news = pd.json_normalize(client.get_news(tickers=['OZON'],
                                  startDate=start,
                                  endDate=today))[['crawlDate', 'title', 'description', 'url']].set_index('crawlDate')
for v in news.values:
    for i in v:
        st.sidebar.write(i)

# Page
st.title('Capital markets update')
st.header('Market Perfomance')
fig = make_subplots(rows=2, cols=1, row_heights = [0.6, 0.4])

fig.append_trace(go.Scatter(x=ozon.index,
                            y=ozon['close'],
                            mode='lines',
                            line = dict(color='royalblue',
                                        width=3),
                            hoverlabel = dict(bgcolor = 'royalblue',
                                              font = dict(family='Arial',
                                                          size=15,
                                                          color='white'),
                                              align = 'left',
                                              namelength = 0),
                            hoverinfo = 'y'),
                 row=1, col=1)

fig.append_trace(go.Scatter(x=ozon.index,
                            y=ozon['14dMA'],
                            mode='lines',
                            line_shape='spline',
                            line = dict(color='red', width=1),
                            hoverlabel = dict(bgcolor = 'red',
                                              font = dict(family='Arial',
                                                          size=15,
                                                          color='white'),
                                              align = 'left',
                                              namelength = 0),
                            hoverinfo = 'y'),
                 row=1, col=1)

fig.add_annotation(x=1,
                   y=ozon['close'][-1],
                   xref='paper',
                   xanchor='left',
                   yanchor='top',
                   text='{:.2f} USD'.format(ozon['close'][-1]),
                   font=dict(family='Arial',
                             size=16,
                             color='royalblue'),
                   showarrow =False)

fig.add_annotation(x=1,
                   y=ozon['14dMA'][-1],
                   xref='paper',
                   xanchor='left',
                   yanchor='top',
                   text='14 MA',
                   font=dict(family='Arial',
                             size=16,
                             color='red'),
                   showarrow =False)


fig.update_layout(xaxis=dict(showline=True,
                             showticklabels=True,
                             linecolor='gray',
                             linewidth=2,
                             ticks='outside',
                             tickfont=dict(family='Arial',
                                           size=12,
                                           color='gray')),
                  yaxis=dict(zeroline=False,
                             showline=False,
                             showticklabels=False),
                  showlegend=False,
                  plot_bgcolor='white',
                  title = dict(x = 0.5,
                               text = 'Stock Price & Volume',
                               font = dict(family='Arial',
                                           size=28,
                                           color='black')))

fig.append_trace(go.Bar(y = ozon['volume'],
                        marker_color='royalblue',
                        hoverlabel = dict(bgcolor = 'royalblue',
                                          font = dict(family='Arial',
                                                      size=15,
                                                      color='white'),
                                          align = 'left',
                                          namelength = 0),
                        hoverinfo = 'y'),
                 row=2, col=1)

fig.update_xaxes(showline=True,
                 showticklabels=False,
                 row = 2,
                 col=1)

fig.add_hrect(y0=ozon['volume'].median(),
              y1= ozon['volume'].max(),
              line_width=0,
              fillcolor="green",
              opacity=0.1,
              row = 2,
              col=1)

st.write(fig)

fig = make_subplots(rows=4, cols=2, subplot_titles = peergroup, shared_xaxes=True)

fig.add_trace(go.Scatter(x=returns.index,
                         y=returns['OZON'],
                         ),row=1, col=1)

fig.add_trace(go.Scatter(x=returns.index,
                         y=returns['XLY'],
                         line = dict(color='grey', width=1)
                         ),row=1, col=1)

fig.add_trace(go.Scatter(x=returns.index,
                         y=returns['FTCH'],
                         line = dict(color='red', width=2)
                         ),row=1, col=2)

fig.add_trace(go.Scatter(x=returns.index,
                         y=returns['XLY'],
                         line = dict(color='grey', width=1)
                         ),row=1, col=2)

fig.add_trace(go.Scatter(x=returns.index,
                         y=returns['FVRR'],
                         line = dict(color='red', width=2)
                         ),row=2, col=1)

fig.add_trace(go.Scatter(x=returns.index,
                         y=returns['XLY'],
                         line = dict(color='grey', width=1)
                         ),row=2, col=1)

fig.add_trace(go.Scatter(x=returns.index,
                         y=returns['GRUB'],
                         line = dict(color='red', width=2)
                         ),row=2, col=2)

fig.add_trace(go.Scatter(x=returns.index,
                         y=returns['XLY'],
                         line = dict(color='grey', width=1)
                         ),row=2, col=2)

fig.add_trace(go.Scatter(x=returns.index,
                         y=returns['QRTEA'],
                         line = dict(color='red', width=2)
                         ),row=3, col=1)

fig.add_trace(go.Scatter(x=returns.index,
                         y=returns['XLY'],
                         line = dict(color='grey', width=1)
                         ),row=3, col=1)

fig.add_trace(go.Scatter(x=returns.index,
                         y=returns['SFIX'],
                         line = dict(color='red', width=2)
                         ),row=3, col=2)

fig.add_trace(go.Scatter(x=returns.index,
                         y=returns['XLY'],
                         line = dict(color='grey', width=1)
                         ),row=3, col=2)

fig.add_trace(go.Scatter(x=returns.index,
                         y=returns['AMZN'],
                         line = dict(color='red', width=2)
                         ),row=4, col=1)

fig.add_trace(go.Scatter(x=returns.index,
                         y=returns['XLY'],
                         line = dict(color='grey', width=1)
                         ),row=4, col=1)

fig.add_trace(go.Scatter(x=returns.index,
                         y=returns['DASH'],
                         line = dict(color='red', width=2)
                         ),row=4, col=2)

fig.add_trace(go.Scatter(x=returns.index,
                         y=returns['XLY'],
                         line = dict(color='grey', width=1)
                         ),row=4, col=2)

fig.update_layout(showlegend=False,
                  plot_bgcolor='white',
                  title = dict(x = 0.5,
                               text = 'Market vs Benchmark (XLY)',
                               font = dict(family='Arial',
                                           size=28,
                                           color='black')))

st.write(fig)

fig = px.bar(recomedations, barmode='stack')
fig.update_layout(xaxis=dict(showline=True,
                             showticklabels=True,
                             linecolor='gray',
                             linewidth=2,
                             ticks='outside',
                             tickfont=dict(family='Arial',
                                           size=12,
                                           color='gray')),
                  yaxis=dict(zeroline=False,
                             showline=False,
                             showticklabels=False),
                  legend_title_text='Recomendation',
                  plot_bgcolor='white',
                  title = dict(x = 0.5,
                               text = 'Analyst Recomendation',
                               font = dict(family='Arial',
                                           size=28,
                                           color='black')))
fig.update_xaxes(title_text=None)
fig.update_yaxes(title_text=None)
st.write(fig)

st.header('Fundamentals')
fig = make_subplots(rows=1,
                    cols=2,
                    subplot_titles = ['Revenue Growth', 'EPS Growth'],
                    shared_xaxes=False,
                    shared_yaxes=False,
                   )

fig.add_trace(go.Bar(x = peerfunds.index,
                     y = peerfunds['metric.revenueGrowthTTMYoy'].dropna(),
                     marker_color='royalblue'),
              row=1,
              col=1)

fig.add_hrect(y0 = 0,
              y1 = peerfunds['metric.revenueGrowthTTMYoy'].median(),
              line_width=0,
              fillcolor="red",
              opacity=0.2,
              row=1,
              col=1)

fig.add_trace(go.Bar(x = peerfunds.index,
                     y = peerfunds['metric.epsGrowthTTMYoy'].dropna(),
                     marker_color='royalblue'),
              row=1,
              col=2)

fig.add_hrect(y0 = peerfunds['metric.epsGrowthTTMYoy'].min(),
              y1 = peerfunds['metric.epsGrowthTTMYoy'].median(),
              line_width=0,
              fillcolor="red",
              opacity=0.2,
              row =1,
              col=2)


fig.update_layout(showlegend=False,
                  plot_bgcolor='white',
                  title = dict(x = 0.5,
                               text = 'Growth',
                               font = dict(family='Arial',
                                           size=28,
                                           color='black')))

st.write(fig)

fig = make_subplots(rows=2,
                    cols=2,
                    subplot_titles = ['Gross Margin', 'Revenue per Employee', 'Net Income per Employee', 'FCF / Revenue'],
                    shared_xaxes=False,
                    shared_yaxes=False,
                   )

fig.add_trace(go.Bar(x = peerfunds.index,
                     y = peerfunds['metric.grossMarginAnnual'].dropna(),
                     marker_color='royalblue'),
              row=1,
              col=1)

fig.add_hrect(y0 = peerfunds['metric.grossMarginAnnual'].min(),
              y1 = peerfunds['metric.grossMarginAnnual'].median(),
              line_width=0,
              fillcolor="red",
              opacity=0.2,
              row=1,
              col=1)

fig.add_trace(go.Bar(x = peerfunds.index,
                     y = peerfunds['metric.revenueEmployeeTTM'].dropna(),
                     marker_color='royalblue'),
              row=1,
              col=2)

fig.add_hrect(y0 = 0,
              y1 = peerfunds['metric.revenueEmployeeTTM'].median(),
              line_width=0,
              fillcolor="red",
              opacity=0.2,
              row =1,
              col=2)

fig.add_trace(go.Bar(x = peerfunds.index,
                     y = peerfunds['metric.netIncomeEmployeeTTM'].dropna(),
                     marker_color='royalblue'),
              row=2,
              col=1)

fig.add_hrect(y0 = peerfunds['metric.netIncomeEmployeeTTM'].min(),
              y1 = peerfunds['metric.netIncomeEmployeeTTM'].median(),
              line_width=0,
              fillcolor="red",
              opacity=0.2,
              row=2,
              col=1)

fig.add_trace(go.Bar(x = peerfunds.index,
                     y = peerfunds['metric.freeOperatingCashFlow/revenueTTM'].dropna(),
                     marker_color='royalblue'),
              row=2,
              col=2)

fig.add_hrect(y0 = peerfunds['metric.freeOperatingCashFlow/revenueTTM'].min(),
              y1 = peerfunds['metric.freeOperatingCashFlow/revenueTTM'].median(),
              line_width=0,
              fillcolor="red",
              opacity=0.2,
              row =2,
              col=2)


fig.update_layout(showlegend=False,
                  plot_bgcolor='white',
                  title = dict(x = 0.5,
                               text = 'Margin and Ratios',
                               font = dict(family='Arial',
                                           size=28,
                                           color='black')))
st.write(fig)

fig = make_subplots(rows=1,
                    cols=2,
                    subplot_titles = ['Receivables Turnover', 'Inventory Turnover'],
                    shared_xaxes=False,
                    shared_yaxes=False,
                   )

fig.add_trace(go.Bar(x = peerfunds.index,
                     y = peerfunds['metric.receivablesTurnoverAnnual'].dropna(),
                     marker_color='royalblue'),
              row=1,
              col=1)

fig.add_hrect(y0 = peerfunds['metric.receivablesTurnoverAnnual'].max(),
              y1 = peerfunds['metric.receivablesTurnoverAnnual'].median(),
              line_width=0,
              fillcolor="red",
              opacity=0.2,
              row=1,
              col=1)

fig.add_trace(go.Bar(x = peerfunds.index,
                     y = peerfunds['metric.inventoryTurnoverAnnual'].dropna(),
                     marker_color='royalblue'),
              row=1,
              col=2)

fig.add_hrect(y0 = peerfunds['metric.inventoryTurnoverAnnual'].max(),
              y1 = peerfunds['metric.inventoryTurnoverAnnual'].median(),
              line_width=0,
              fillcolor="red",
              opacity=0.2,
              row =1,
              col=2)


fig.update_layout(showlegend=False,
                  plot_bgcolor='white',
                  title = dict(x = 0.5,
                               text = 'Turnover',
                               font = dict(family='Arial',
                                           size=28,
                                           color='black')))
st.write(fig)

fig = make_subplots(rows=2,
                    cols=2,
                    subplot_titles = ['Current Ratio', 'Quick Ratio', 'LT Debt / Equity', 'Total Debt / Equty'],
                    shared_xaxes=False,
                    shared_yaxes=False,
                   )

fig.add_trace(go.Bar(x = peerfunds.index,
                     y = peerfunds['metric.currentRatioAnnual'].dropna(),
                     marker_color='royalblue'),
              row=1,
              col=1)

fig.add_hrect(y0 = 1,
              y1 = 0,
              line_width=0,
              fillcolor="red",
              opacity=0.2,
              row=1,
              col=1)

fig.add_trace(go.Bar(x = peerfunds.index,
                     y = peerfunds['metric.quickRatioAnnual'].dropna(),
                     marker_color='royalblue'),
              row=1,
              col=2)

fig.add_hrect(y0 = 1,
              y1 = 0,
              line_width=0,
              fillcolor="red",
              opacity=0.2,
              row =1,
              col=2)

fig.add_trace(go.Bar(x = peerfunds.index,
                     y = peerfunds['metric.longTermDebt/equityAnnual'].dropna(),
                     marker_color='royalblue'),
              row=2,
              col=1)

fig.add_hrect(y0 = peerfunds['metric.longTermDebt/equityAnnual'].max(),
              y1 = peerfunds['metric.longTermDebt/equityAnnual'].median(),
              line_width=0,
              fillcolor="red",
              opacity=0.2,
              row=2,
              col=1)

fig.add_trace(go.Bar(x = peerfunds.index,
                     y = peerfunds['metric.totalDebt/totalEquityAnnual'].dropna(),
                     marker_color='royalblue'),
              row=2,
              col=2)

fig.add_hrect(y0 = peerfunds['metric.totalDebt/totalEquityAnnual'].max(),
              y1 = peerfunds['metric.totalDebt/totalEquityAnnual'].median(),
              line_width=0,
              fillcolor="red",
              opacity=0.2,
              row =2,
              col=2)


fig.update_layout(showlegend=False,
                  plot_bgcolor='white',
                  title = dict(x = 0.5,
                               text = 'Debt and Liquidity',
                               font = dict(family='Arial',
                                           size=28,
                                           color='black')))
st.write(fig)

fig = make_subplots(rows=1,
                    cols=2,
                    subplot_titles = ['Price to Book', 'Price to Sales'],
                    shared_xaxes=False,
                    shared_yaxes=False,
                   )

fig.add_trace(go.Bar(x = peerfunds.index,
                     y = peerfunds['metric.pbAnnual'].dropna(),
                     marker_color='royalblue'),
              row=1,
              col=1)

fig.add_hrect(y0 = peerfunds['metric.pbAnnual'].max(),
              y1 = peerfunds['metric.pbAnnual'].median(),
              line_width=0,
              fillcolor="red",
              opacity=0.2,
              row=1,
              col=1)

fig.add_trace(go.Bar(x = peerfunds.index,
                     y = peerfunds['metric.psTTM'].dropna(),
                     marker_color='royalblue'),
              row=1,
              col=2)

fig.add_hrect(y0 = peerfunds['metric.psTTM'].max(),
              y1 = peerfunds['metric.psTTM'].median(),
              line_width=0,
              fillcolor="red",
              opacity=0.2,
              row =1,
              col=2)


fig.update_layout(showlegend=False,
                  plot_bgcolor='white',
                  title = dict(x = 0.5,
                               text = 'Valuation',
                               font = dict(family='Arial',
                                           size=28,
                                           color='black')))
st.write(fig)


st.title('Case study')
