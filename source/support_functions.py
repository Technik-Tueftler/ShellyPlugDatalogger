#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collection of support function for main app with definition of classes and verification functions.
"""
from dataclasses import dataclass
import os
from requests.exceptions import ConnectTimeout
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError


@dataclass
class DataApp:  # pylint: disable=too-many-instance-attributes
    """
    Class to structure all environment variables and verify them.
    """

    db_ip_address: str = os.getenv("DB_IP_ADDRESS")
    db_user_name: str = os.getenv("DB_USER_NAME")
    db_user_password: str = os.getenv("DB_USER_PASSWORD", "")
    db_name: str = os.getenv("DB_NAME")
    ssl: bool = False
    verify_ssl: bool = False
    db_port: int = 0
    verified: bool = True
    try:
        if None in (db_ip_address, db_user_name, db_user_password, db_name):
            raise ValueError(
                "Not all env variable are defined. Please check the documentation and "
                "add all necessary login information."
            )
        db_port = os.getenv("DB_PORT")
        ssl = os.getenv("SSL")
        verify_ssl = os.getenv("VERIFY_SSL")
        if db_port is None:
            db_port = 8086
        elif db_port.isdecimal():
            db_port = int(db_port)
        else:
            raise ValueError("Environment variable DB_PORT is not a decimal number.")
        if ssl is None:
            ssl = False
        elif ssl == ("True" or "true"):
            ssl = True
        elif ssl == ("False" or "false"):
            ssl = False
        else:
            raise ValueError("Environment variable SSL is not True or False.")
        if verify_ssl is None:
            verify_ssl = False
        elif verify_ssl == ("True" or "true"):
            verify_ssl = True
        elif verify_ssl == ("False" or "false"):
            verify_ssl = False
        else:
            raise ValueError("Environment variable VERIFY_SSL is not True or False.")
    except ValueError as err:
        verified = False
        print(err)


class InfluxDBConnection:
    """
    InluxDB connection class for handling in context manager
    """
    def __init__(self, login_information: DataApp):
        login_information: DataApp
        self.client = InfluxDBClient(
            host=login_information.db_ip_address,
            port=login_information.db_port,
            username=login_information.db_user_name,
            password=login_information.db_user_password,
            ssl=login_information.ssl,
            verify_ssl=login_information.verify_ssl,
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.client.close()


def check_and_verify_db_connection(login_information: DataApp) -> None:
    """Function controls the passed env variables and checks if they are valid."""
    try:
        with InfluxDBConnection(login_information=login_information) as connection:
            connection.client.ping()
            connection.client.switch_database(login_information.db_name)
            login_information.all_verified = True
    except (InfluxDBClientError, ConnectTimeout) as err:
        print(
            f"Error occurred during setting the database with error message: {err}. All login"
            f"information correct? Like database address, user name and so on? "
            f"Check dokumentation for all environment variables"
        )
        login_information.all_verified = False


def main() -> None:
    """
    Scheduling function for regular call.
    :return: None
    """


if __name__ == "__main__":
    main()