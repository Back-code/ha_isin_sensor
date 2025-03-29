# ha_isin_sensor
Stock Sensors for Home Assistant

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Back-code&repository=https%3A%2F%2Fgithub.com%2FBack-code%2Fha_isin_sensor&category=Stock)

## Overview
The `ha_isin_sensor` integration allows you to track stock prices and related information using ISIN (International Securities Identification Number) codes. This integration fetches real-time stock data and displays it as sensors in Home Assistant.

## Features
- Add multiple stocks to a hub using their ISIN codes.
- Fetch real-time stock prices and additional details such as currency, market, and price changes.
- Organize stocks into hubs for better management.
- Supports configuration via the Home Assistant UI.

## Installation
1. Copy the `ha_isin_sensor` folder into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.
3. Add the integration via the Home Assistant UI by navigating to **Settings > Devices & Services > Add Integration** and searching for "ISIN Sensor".

## Configuration
### Adding a Hub
1. Provide a unique name for your hub.
2. Add stocks by entering their ISIN codes and names.

### Editing Stocks
You can edit or add more stocks to an existing hub via the integration's options.

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

## Example Use Case
Monitor your stock portfolio directly in Home Assistant and create automations based on stock price changes.

## Troubleshooting
If you encounter issues:
- Check the Home Assistant logs for error messages.
- Ensure the ISIN code is valid and supported by the API.

## Links
- [Documentation](https://github.com/Back-code/ha_isin_sensor)
- [Issue Tracker](https://github.com/Back-code/ha_isin_sensor/issues)
