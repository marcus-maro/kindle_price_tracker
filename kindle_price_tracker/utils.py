import json
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import requests
from bs4 import BeautifulSoup
from twilio.rest import Client

from . import database


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
    "Accept-Language": "en-US, en;q=0.5",
}


def setup_logging() -> None:
    # Create logger that writes to file using basic config
    logging.basicConfig(
        filename=Path(__file__).parent.resolve() / "log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def utc_now_floor() -> str:
    now = datetime.utcnow()
    now = now.replace(second=0, microsecond=0, minute=0, hour=now.hour)
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")


def get_kindle_price(asin: str) -> float:
    url = f"https://www.amazon.com/dp/{asin}"
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.content, "html.parser")
    element = soup.find(id="kindle-price")
    price = float(element.text.strip().replace("$", "").replace(",", ""))

    return price


def plot_price_data() -> None:
    books = database.get_books()
    book_columns = database.get_table_columns("book")
    df_books = pd.DataFrame(books, columns=book_columns)

    price_data = database.get_price_data()
    price_data_columns = database.get_table_columns("price_data")
    df_price_data = pd.DataFrame(price_data, columns=price_data_columns)

    df_plot = pd.merge(df_books, df_price_data, on="ASIN")
    df_plot = df_plot.pivot(index="timestamp", columns="title", values="price")
    df_plot.index = pd.to_datetime(df_plot.index).tz_convert("US/Mountain")
    df_plot.columns = [
        (col[:30].strip() + "...") if len(col) > 30 else col for col in df_plot.columns
    ]
    df_plot.columns.name = None

    figure = go.Figure()
    for column in df_plot.columns:
        figure.add_trace(
            go.Scatter(
                x=df_plot.index,
                y=df_plot[column],
                mode="lines+markers",
                name=column,
            )
        )

    figure.update_layout(
        title="Kindle Price Tracker",
        yaxis_title="Price",
        yaxis_tickprefix="$",
        yaxis_tickformat=",.",
    )

    figure.show()


def send_sms(message: str, number: int) -> None:
    to = f"+1{number}"

    account_sid = json.load(open("kindle_price_tracker/auth.json"))[
        "twilio_account_sid"
    ]
    auth_token = json.load(open("kindle_price_tracker/auth.json"))["twilio_auth_token"]
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=message,
        from_=json.load(open("kindle_price_tracker/auth.json"))["twilio_number"],
        to=to,
    )
