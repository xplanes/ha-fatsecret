# FatSecret integration for Home Assistant

This is a custom [Home Assistant](https://www.home-assistant.io/) integration that connects to the [FatSecret API](https://platform.fatsecret.com/platform-api) to fetch your nutrition data for today (calories, macros, etc.) and expose them as sensors.

## Notes

- Requires a FatSecret API account to obtain the `Consumer Key` and the `Consumer Secret`.
- Data is fetched for the current day.
- Sensors update every 15 minutes.

# Installation

## Option A: Installing via HACS

1. Go to the HACS Integration Tab
2. Search the `FatSecret` component and click on it.
3. Click Download button at the bottom of the page. A pop up will be shown informing you that the component will be installed in the folder `/config/custom_components/fatsecret`. Click Download.

## Option B: Manual Installation

3. Clone or download the GitHub repository: [ha-fatsecret](https://github.com/xplanes/ha-fatsecret)
4. Copy the `custom_components/fatsecret` folder to your Home Assistant `config/custom_components/` directory: config/custom_components/fatsecret
5. Restart Home Assistant.

# Configuration

1. Go to **Settings > Devices & Services > Devices > Add Device**.
2. Search for `FatSecret` and add it.
3. Enter your credentials (`Consumer Key` and the `Consumer Secret`) from the **FatSecret Platform API**
4. A new popup window wil show you a FatSecret URL and a `verifier` field. Click on the URL
5. A FatSecret page will ask you to sign in to your FatSecret account to obtain the verifier code. Use your **FatSecret username and password**. Do not use the FatSecret Platform API credentials. Once signed in, copy the code and put this code in the verifier field of the FatSecret popup window.

# Services

The integration provides a service to manually refresh data: `update_fatsecret`
