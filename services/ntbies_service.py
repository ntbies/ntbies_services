# Odoo Module to Integrate NTBIES Services
# Streamlining data extraction from invoices, vendor bills, and prefilling business contact information.
# Copyright (C) 2024 Gerry Ntabuhashe for NTBIES SRL

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os

import requests
from odoo import _, api, models
from odoo.exceptions import UserError


class ServiceAbstract(models.AbstractModel):
    _name = "ntbies.service"
    _description = "Ntbies Service Abstract"
    _BASE_URL = "https://platforms.ntbies.com/api/v1"

    @api.model
    def _get_headers(self, access_key):
        """
        Get the headers for the API request.

        :param access_key: The access key for authorization
        :type access_key: str
        :return: A dictionary containing the headers
        :rtype: dict
        """
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {access_key}",
        }

    @api.model
    def get_buy_credits(self):
        """
        Get the URL for buying credits from the platform's billing account.
        """
        return "https://platforms.ntbies.com/account/billing"

    def get_base_url(self):
        """
        Return the base URL.
        """
        if os.environ.get("NTBIES_API_URL"):
            return os.environ.get("NTBIES_API_URL")
        return self._BASE_URL

    def post_request(self, endpoint, access_key, payload=None, files=None):
        """
        Send a POST request to the specified endpoint with the given access key, payload, and files.

        Args:
            endpoint (str): The endpoint to send the request to.
            access_key (str): The access key to use for the request.
            payload (dict, optional): The payload to include in the request. Defaults to None.
            files (dict, optional): The files to include in the request. Defaults to None.

        Returns:
            dict: The JSON response from the request.
        """
        if not access_key:
            raise UserError(
                _("The access key related to this document has not yet been configured")
            )
        url = "/".join([self.get_base_url(), endpoint])
        headers = self._get_headers(access_key)
        resp = requests.post(
            url, files=files, headers=headers, data=payload, verify=False
        )
        if resp.status_code not in [403, 422, 425]:
            resp.raise_for_status()
        return resp.json()

    def get_request(self, endpoint, access_key):
        """
        Send a GET request to the specified endpoint using the provided access key.

        :param endpoint: The endpoint to send the GET request to.
        :type endpoint: str
        :param access_key: The access key to use for authentication.
        :type access_key: str
        :return: The JSON response from the GET request.
        :rtype: dict
        """

        url = "/".join([self.get_base_url(), endpoint])
        resp = requests.get(url, headers=self._get_headers(access_key), verify=False)
        if resp.status_code not in [403, 422, 425]:
            resp.raise_for_status()
        return resp.json()
