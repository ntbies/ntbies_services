# NTBIES Services for Odoo 15

## Overview

NTBIES Services module for Odoo enables seamless integration with NTBIES services, allowing users to extract data from invoices and expenses and automatically integrate them into Odoo. This module fills the gap in the digitization module for the community versions of Odoo, aiming to simplify and automate the handling of vendor bills and expenses through digital extraction services.

### Key Features

- Automatic data extraction from invoices and receipts.
- Integration with NTBIES platform for advanced digitization.
- Supports Odoo versions 15.
- Configurable settings for manual or automatic data extraction.
- User account credit system for service usage.

## Prerequisites

- An account on the [NTBIES platform](https://platform.ntbies.com).
- Module `queue_job` from OCA installed. This can be found at [OCA/queue](https://github.com/OCA/queue).

## Installation

1. Ensure that Odoo is installed and running on your system.
2. Have the `queue_job` module from OCA in your installable module if that's not yet the case. This is a dependency for the NTBIES Services module.
   - Clone the `queue` repository:
     ```bash
     git clone https://github.com/OCA/queue.git
     ```
   - Make sure you are on branch 15.0
   - Follow the installation instructions provided in the `queue` repository.
3. Clone or download the NTBIES Services module into your Odoo addons directory.
4. Update the Odoo module list and install the NTBIES Services module through the Odoo backend interface.

## Configuration

1. Create an account at [https://platform.ntbies.com](https://platform.ntbies.com) and generate an **Access Key**.
2. In your Odoo instance, navigate to **Settings** > **NTBIES Services**.
3. Enter your Access key and configure your preferences for automatic data extraction.

## Usage

- To use the NTBIES Services module, import your invoices (Invoicing > Vendor Bills) or receipts (HR > Expenses) into the Odoo system.
- The module will automatically contact the NTBIES service to request data extraction, based on your configuration settings.
- Ensure your NTBIES platform account has sufficient credits for the service. Credits can be recharged directly on the NTBIES platform.

## Pricing

- The service is not free. Users must recharge credits on their NTBIES account to use the service.
- **Pricing:** 1 euro equals 100 credits. The account balance can then be used to pay the processing. For document extraction, the cost is **8** credit par page.

## Future Enhancements

- Additional features and integrations will be added in future updates to further enhance the module's capabilities and support for other operations.

## Support

For support, please create an issue on the module's GitHub repository or contact the NTBIES platform support team if it relates to credit usage.
