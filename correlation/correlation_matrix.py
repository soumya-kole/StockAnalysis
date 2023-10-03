import logging
import os
import time

import matplotlib.pyplot as plt
import pandas as pd
import requests
import seaborn as sns

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)


def fetch_stock_data(symbols, start_date, end_date):
    stocks = []

    base_url = "https://www.alphavantage.co/query"
    function = "TIME_SERIES_DAILY"
    api_key = os.environ['API_KEY']
    max_retries = 3
    retry_delay = 5
    date_range = pd.date_range(start=start_date, end=end_date).strftime('%Y-%m-%d').tolist()
    try:
        for symbol in symbols:
            logger.debug(f'Fetching {symbol}')
            for retry in range(max_retries):
                url = f"{base_url}?function={function}&symbol={symbol}&apikey={api_key}"
                r = requests.get(url).json()
                if any(key in r for key in ['Error Message', 'Information']):
                    raise Exception(f"Error Message = {r.get('Error Message')}\nInformation={r.get('Information')}")
                data = r.get('Time Series (Daily)')
                if data is not None:
                    break
                if retry < max_retries - 1:
                    retry_delay = retry_delay * 2
                    logger.debug(f"Sleeping for {retry_delay} seconds")
                    time.sleep(retry_delay)
            filtered_data = [{'date': pd.to_datetime(d), symbol: round(float(data.get(d)['4. close']),)} for d in date_range if data.get(d)]
            df = pd.DataFrame(filtered_data)
            df.set_index("date", inplace=True)
            stocks.append(df)
    except requests.exceptions.ConnectionError as e:
        logger.error("Error in calling API")
        logger.exception(e)
    merged_stocks = pd.concat(stocks, axis=1)
    return merged_stocks


def calculate_daily_returns(stock_data):
    daily_returns = stock_data.pct_change().dropna()
    return daily_returns


def compute_correlation_matrix(daily_returns):
    correlation_matrix = daily_returns.corr()
    return correlation_matrix


def plot_correlation_heatmap(correlation_matrix):
    plt.figure(figsize=(8, 8))
    ax = sns.heatmap(
        correlation_matrix,
        annot=True,
        cmap="coolwarm",
        vmin=-1,
        vmax=1,
        square=True,
        linewidths=0.5,
        cbar_kws={"shrink": 0.8},
    )
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")
    plt.title("Correlation Matrix Heatmap", y=1.08)
    plt.show()


def main():
    symbols = ['AAPL']
    start_date = '2023-09-19'
    end_date = '2023-10-02'
    stock_data = fetch_stock_data(symbols, start_date, end_date)
    daily_returns = calculate_daily_returns(stock_data)
    print("daily_returns Matrix:")
    print(daily_returns)

    correlation_matrix = compute_correlation_matrix(daily_returns)

    print("Correlation Matrix:")
    print(correlation_matrix)

    plot_correlation_heatmap(correlation_matrix)


if __name__ == "__main__":
    main()
