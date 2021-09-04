# Grimp6 - Certificates

This scripts downloads medical certificates and waivers from Hello Asso.

## Warning

It will download documents containing personal data.
Please handle the information with care, and ensure that they will be available only to the strictly necessary people.

## Installation

```bash
pip install requests
```

## Configuration

This script requires the following data:
- API credentials: **clientId** and **clientSecret**. It can be found on https://admin.helloasso.com/grimpo6/integrations
- The **tm5-HelloAsso** cookie.

Cookie can be retrieved with the following process:
- Open Chrome and go to https://admin.helloasso.com/grimpo6/accueil
- Right-click on an empty space on the website and select "Inspect."
- In the developer tools that open, click on the "Application" tab.
- Under the "Storage" section, click on "Cookies" and then select https://admin.helloasso.com
- In the right-hand pane, you will see a list of cookies for the website. Click on **tm5-HelloAsso**
- Select the Cookie Value displayed under, and copy the value pressing "Ctrl+C" (or "Cmd+C" on a Mac).

## Usage

```bash
python3 main.py
```

