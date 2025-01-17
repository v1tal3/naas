#!/usr/bin/env python3
# -*- coding: UTF-8 -*-


import ipaddress

from flask import current_app, request
from uuid import UUID
from werkzeug.exceptions import UnprocessableEntity, BadRequest


class Validate(object):
    """Validators and such"""

    def __init__(self):
        self._field_name = None
        self.http = ValidateHTTP()

    @staticmethod
    def custom_port():
        # If "port" is in payload, don't do anything, otherwise set it to 22
        request.json.setdefault("port", 22)

    def save_config(self):
        # If "save_config" bool is in payload, don't do anything, otherwise set it to False
        request.json.setdefault("save_config", False)

        # If it _was_ set, but it ain't a bool, get outta here fool
        if not isinstance(request.json["save_config"], bool):
            self._error("save_config must be a Boolean")

    def commit(self):
        # If "commit" bool is in payload, don't do anything, otherwise set it to False
        request.json.setdefault("commit", False)

        # If it _was_ set, but it ain't a bool, get outta here fool
        if not isinstance(request.json["commit"], bool):
            self._error("commit must be a Boolean")

    def is_ip_addr(self, ip, name=None):
        self._field_name = name
        self.is_not_none(ip, name)
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            self._error("invalid IP Address")

    def is_uuid(self, uuid: str):
        try:
            _ = UUID(uuid, version=4)
        except ValueError:
            self._error("invalid UUID")

    def is_json(self):
        if not request.json:
            self._error("json required")

    def is_not_none(self, s, name=None):
        self._field_name = name
        if s is None:
            self._error("value cannot be null")

    def is_command_set(self):
        if not request.json.get("commands"):
            self._error("please provide commands in a list")
        if not isinstance(request.json["commands"], list):
            self._error("please provide commands in a list", code=422)

    def has_device_type(self):
        if not request.json.get("device_type"):
            request.json["device_type"] = "cisco_ios"
        if not isinstance(request.json["device_type"], str):
            self._error("device_type must be a string", code=422)

    @staticmethod
    def _error(message, code=400):
        current_app.logger.error(message)
        if code == 400:
            raise BadRequest
        elif code == 422:
            raise UnprocessableEntity


class ValidateHTTP(object):
    def __init__(self):
        self.headers = {k.lower(): v for k, v in request.headers.items()}
        self.method = request.method

    @staticmethod
    def _error():
        current_app.logger.error("Invalid HTTP request")
        raise BadRequest
