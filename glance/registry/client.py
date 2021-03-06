# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 OpenStack, LLC
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Simple client class to speak with any RESTful service that implements
the Glance Registry API
"""

import json
import urllib

from glance.common.client import BaseClient
from glance.registry import server


class RegistryClient(BaseClient):

    """A client for the Registry image metadata service"""

    DEFAULT_PORT = 9191

    def __init__(self, host, port=None, use_ssl=False, auth_tok=None):
        """
        Creates a new client to a Glance Registry service.

        :param host: The host where Glance resides
        :param port: The port where Glance resides (defaults to 9191)
        :param use_ssl: Should we use HTTPS? (defaults to False)
        :param auth_tok: The auth token to pass to the server
        """
        port = port or self.DEFAULT_PORT
        super(RegistryClient, self).__init__(host, port, use_ssl, auth_tok)

    def get_images(self, **kwargs):
        """
        Returns a list of image id/name mappings from Registry

        :param filters: dict of keys & expected values to filter results
        :param marker: image id after which to start page
        :param limit: max number of images to return
        :param sort_key: results will be ordered by this image attribute
        :param sort_dir: direction in which to to order results (asc, desc)
        """
        params = self._extract_params(kwargs, server.SUPPORTED_PARAMS)
        res = self.do_request("GET", "/images", params=params)
        data = json.loads(res.read())['images']
        return data

    def get_images_detailed(self, **kwargs):
        """
        Returns a list of detailed image data mappings from Registry

        :param filters: dict of keys & expected values to filter results
        :param marker: image id after which to start page
        :param limit: max number of images to return
        :param sort_key: results will be ordered by this image attribute
        :param sort_dir: direction in which to to order results (asc, desc)
        """
        params = self._extract_params(kwargs, server.SUPPORTED_PARAMS)
        res = self.do_request("GET", "/images/detail", params=params)
        data = json.loads(res.read())['images']
        return data

    def get_image(self, image_id):
        """Returns a mapping of image metadata from Registry"""
        res = self.do_request("GET", "/images/%s" % image_id)
        data = json.loads(res.read())['image']
        return data

    def add_image(self, image_metadata):
        """
        Tells registry about an image's metadata
        """
        headers = {
            'Content-Type': 'application/json',
        }

        if 'image' not in image_metadata.keys():
            image_metadata = dict(image=image_metadata)

        body = json.dumps(image_metadata)

        res = self.do_request("POST", "/images", body, headers=headers)
        # Registry returns a JSONified dict(image=image_info)
        data = json.loads(res.read())
        return data['image']

    def update_image(self, image_id, image_metadata, purge_props=False):
        """
        Updates Registry's information about an image
        """
        if 'image' not in image_metadata.keys():
            image_metadata = dict(image=image_metadata)

        body = json.dumps(image_metadata)

        headers = {
            'Content-Type': 'application/json',
        }

        if purge_props:
            headers["X-Glance-Registry-Purge-Props"] = "true"

        res = self.do_request("PUT", "/images/%s" % image_id, body, headers)
        data = json.loads(res.read())
        image = data['image']
        return image

    def delete_image(self, image_id):
        """
        Deletes Registry's information about an image
        """
        self.do_request("DELETE", "/images/%s" % image_id)
        return True

    def get_image_members(self, image_id):
        """Returns a list of membership associations from Registry"""
        res = self.do_request("GET", "/images/%s/members" % image_id)
        data = json.loads(res.read())['members']
        return data

    def get_member_images(self, member_id):
        """Returns a list of membership associations from Registry"""
        res = self.do_request("GET", "/shared-images/%s" % member_id)
        data = json.loads(res.read())['shared_images']
        return data

    def replace_members(self, image_id, member_data):
        """Replaces Registry's information about image membership"""
        if 'memberships' not in member_data.keys():
            member_data = dict(memberships=[member_data])

        body = json.dumps(member_data)

        headers = {'Content-Type': 'application/json', }

        res = self.do_request("PUT", "/images/%s/members" % image_id,
                              body, headers)
        return res.status == 204

    def add_member(self, image_id, member_id, can_share=None):
        """Adds to Registry's information about image membership"""
        body = None
        headers = {}
        # Build up a body if can_share is specified
        if can_share is not None:
            body = json.dumps(dict(member=dict(can_share=can_share)))
            headers['Content-Type'] = 'application/json'

        res = self.do_request("PUT", "/images/%s/members/%s" %
                              (image_id, member_id), body, headers)
        return res.status == 204

    def delete_member(self, image_id, member_id):
        """Deletes Registry's information about image membership"""
        res = self.do_request("DELETE", "/images/%s/members/%s" %
                              (image_id, member_id))
        return res.status == 204
