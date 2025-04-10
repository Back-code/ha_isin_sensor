# Mini Stock Pocket
<img src="images/Mini Stock Pocket Logo fav.png" alt="Mini Stock Pocket" width="260"/>
Stock Sensors for Home Assistant

## HACS
----------- HACS under construction -----------

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Back-code&repository=https%3A%2F%2Fgithub.com%2FBack-code%2Fha_isin_sensor&category=Stock)

----------- HACS under construction -----------

## Overview
The `Mini Stock Pocket` integration allows you to track stock prices and related information using ISIN (International Securities Identification Number) codes. This integration fetches every 5 minutes stock data and displays it as sensors in Home Assistant.

## Features
- **Add Stocks**: Add multiple stocks to a hub using their ISIN codes.
- **Real-Time Data**: Fetch real-time stock prices and additional details such as currency, market, and price changes.
- **Portfolio Management**: Organize stocks into hubs for better management.
- **Edit Stocks**: Update stock quantities or add more stocks to an existing hub.
- **Delete Stocks**: Remove stocks from your portfolio.
- **Configuration via UI**: Supports configuration and management via the Home Assistant UI.
- **Dynamic Attributes**: Automatically adjusts sensor attributes based on the type of financial instrument (e.g., Share, Fund, Bond, Krypto).
- **Custom Quantity Tracking**: Tracks the quantity of stocks in your portfolio and calculates the total value.
- **Localized Translations**: Supports multiple languages, including English and German.
- **Flexible Options Flow**: Allows editing, adding, or deleting stocks directly from the integration's options menu.

## Installation
1. Copy the `mini-stock-pocket` folder into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.
3. Add the integration via the Home Assistant UI by navigating to **Settings > Devices & Services > Add Integration** and searching for "Mini Stock Pocket".

## Configuration
### Adding a Hub
1. Provide a unique name for your hub.
2. Add stocks by entering their ISIN codes, names, and quantities.

### Editing Stocks
You can edit or add more stocks to an existing hub via the integration's options:
- **Edit Stock Quantity**: Update the number of stocks for a specific ISIN.
- **Add More Stocks**: Add additional stocks to your portfolio.

### Deleting Stocks
Remove a stock from your portfolio by selecting it in the options menu.

## Sensor Attributes
Each sensor provides the following attributes:
- **Name**: The name of the stock.
- **Price**: The current stock price.
- **Close**: The last closing price of the stock.
- **Bid**: The current bid price.
- **Bid Date**: The timestamp of the last bid price update.
- **Ask**: The current ask price.
- **Ask Date**: The timestamp of the last ask price update.
- **Change Percent**: The percentage change in the stock price.
- **Change Absolute**: The absolute change in the stock price.
- **Stock Market**: The stock market where the stock is listed.
- **ISIN**: The ISIN code of the stock.
- **WKN**: The German securities identification number (if available).
- **Internal ISIN**: The internal ISIN code used by the API.
- **Price Change Date**: The date of the last price change.
- **Currency**: The currency of the stock price.
- **Currency Sign**: The symbol of the currency.
- **Quantity**: The number of stocks in your portfolio.
- **Total Value**: The total value of the stock (price × quantity).

### Additional Attributes for Shares and Bonds
The following attributes are dynamically added for stocks of type `Share` and `Bond`:
- **Daily Low**: The lowest price of the stock for the current day.
- **Daily High**: The highest price of the stock for the current day.
- **52-Week Low**: The lowest price of the stock in the last 52 weeks.
- **52-Week High**: The highest price of the stock in the last 52 weeks.

## Dynamic Attributes Based on Instrument Type
The integration dynamically adjusts the attributes based on the type of financial instrument:
- **Shares**:
  - Includes bid/ask prices, change percentages, and market details.
- **Funds/ETFs**:
  - Includes closing prices, currency, and market details.
- **Bonds**:
  - Includes bid/ask prices, percentage trading, and additional bond-specific details.

## Example Use Case
Monitor your stock portfolio directly in Home Assistant and create automations based on stock price changes. For example:
- Send a notification when a stock price exceeds a certain threshold.
- Trigger automations based on percentage changes in stock prices.

## Troubleshooting
If you encounter issues:
- Check the Home Assistant logs for error messages.
- Ensure the ISIN code is valid and supported by the API.

## Links
- [Documentation](https://github.com/Back-code/ha_isin_sensor)
- [Issue Tracker](https://github.com/Back-code/ha_isin_sensor/issues)
- [API by ing.de](https://www.ing.de)
