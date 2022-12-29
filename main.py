import logging

from kindle_price_tracker import database, utils


def main():
    try:
        utils.setup_logging()
        logging.info("Starting main.py")

        books = database.get_books()
        book_columns = database.get_table_columns("book")
        timestamp = utils.utc_now_floor()

        for book in books:
            book = dict(zip(book_columns, book))
            price = utils.get_kindle_price(book["ASIN"])
            database.insert_price_data(book["ASIN"], price, timestamp)

            if price < book["lowest_price"]:
                database.update_lowest_price(book["ASIN"], price, timestamp)

                for number in database.get_users_with_book(book["ASIN"]):
                    utils.send_sms(
                        f"'{book['title']}' has dropped to a low of ${price}! (https://www.amazon.com/dp/{book['ASIN']})",
                        number,
                    )
    except Exception as e:
        logging.exception(e)


if __name__ == "__main__":
    main()
