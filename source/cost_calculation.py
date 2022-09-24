#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collection of calculation function for main app to calculate the energy for device
in Daily, monthly, and yearly rhythm.
"""
import os
import re
import json
from datetime import datetime, timedelta
import support_functions as sf
from dateutil.relativedelta import relativedelta

TIME_OF_DAY_SCHEDULE_MATCH = r"^(?:[01]\d|2[0-3]):(?:[0-5]\d)$"
DAY_OF_MONTH_SCHEDULE_MATCH = r"^[\d]{2}$"
DATE_OF_YEAR_SCHEDULE_MATCH = r"^[\d]{2}[.][\d]{2}$"
TIMESTAMP_FORMAT_INPUT = "%Y-%m-%dT%H:%M:%S.%fZ"
TIMESTAMP_FORMAT_OUTPUT = "%Y-%m-%dT%H:%M:%S"


def check_cost_calc_request_time() -> str:
    """
    Check if a start time is given for cost calculation and have the right format. If something is
    wrong, a default time is returned.
    :return: Start time in string format
    """
    # Wenn es fehlschlägt, muss auch ein log Eintrag erstellt werden
    try:
        checked_requested_start_time = "00:00"
        with open("../files/config.json", encoding="utf-8") as file:
            data = json.load(file)
            if ("general" in data) and ("cost_calc_request_time" in data["general"]):
                requested_start_time = data["general"]["cost_calc_request_time"]
                if (
                    re.search(TIME_OF_DAY_SCHEDULE_MATCH, requested_start_time)
                    is not None
                ):
                    checked_requested_start_time = requested_start_time
        return checked_requested_start_time

    except FileNotFoundError as err:
        print(
            f"The file for general configuration could not be found. Please put it in the "
            f"folder you passed with the environment variables. The default values are used. "
            f"Error occurred during start the app with error message: {err}."
        )
        return checked_requested_start_time


def check_cost_config() -> float:
    """
    Check if a cost config for KWh is given for cost calculation and have the right format.
    If something is wrong, a default time is returned and a log entry is written.
    :return: price per KWh as a float
    """
    # Wenn es fehlschlägt, muss auch ein log Eintrag erstellt werden
    default_price = 0.3
    try:
        with open("../files/config.json", encoding="utf-8") as file:
            data = json.load(file)
            if ("general" in data) and ("price_kwh" in data["general"]):
                requested_kwh_price = data["general"]["price_kwh"]
                if not isinstance(requested_kwh_price, float):
                    requested_kwh_price = requested_kwh_price.replace(",", ".")
                checked_requested_kwh_price = round(float(requested_kwh_price), 3)
        return checked_requested_kwh_price

    except FileNotFoundError as err:
        print(
            f"The file for general configuration could not be found. Please put it in the "
            f"folder you passed with the environment variables. The default values are used. "
            f"Error occurred during start the app with error message: {err}."
        )
        return default_price
    except ValueError as err:
        print(f"The setting for the price is not a number. A default value of 0.30€ was assumed. "
              f"Error message: {err}")
        return default_price


def cost_calc_day(
    device_name: str, settings: dict, login_information: sf.DataApp, current_timestamp: datetime
) -> None:
    """
    Calculate the daily cost for a specific device.
    :param device_name: Name of the device
    :param settings: device parameters
    :param login_information: Login information to connect with the InfluxDB
    :param current_timestamp: Now date and time from request
    :return: None
    """
    start_date = (current_timestamp - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    end_date = current_timestamp.strftime("%Y-%m-%d %H:%M:%S")
    with sf.InfluxDBConnection(login_information=login_information) as conn:
        query = f'SELECT * FROM {conn.login_information.db_name}."autogen"."census" ' \
                f'WHERE device=$device AND time > $target_date AND time < $current_date'
        bind_params = {
            "device": device_name,
            "target_date": start_date,
            "current_date": end_date,
        }
        result = conn.query(query, bind_params=bind_params)

        success_measurements = list(
            filter(
                lambda measurement: measurement["fetch_success"] is True,
                result.get_points(),
            )
        )

        failed_measurements = list(
            filter(
                lambda measurement: measurement["fetch_success"] is False,
                result.get_points(),
            )
        )
        sum_of_energy_in_kwh = round(
            (sum(element["energy_wh"] for element in success_measurements)/1000), 2
        )
        cost_kwh = check_cost_config()
        count_measurements = len(success_measurements) + len(failed_measurements)
        if count_measurements == 0:
            return
        sum_of_sec = (current_timestamp - (current_timestamp - timedelta(days=1))).total_seconds()
        max_values = sum_of_sec/settings["update_time"]

        data = {"start_date": start_date,
                "end_date": end_date,
                "sum_of_energy": sum_of_energy_in_kwh,
                "total_cost": sum_of_energy_in_kwh * cost_kwh,
                "cost_kwh": cost_kwh,
                "error_rate_one": len(failed_measurements) * 100 / count_measurements,
                "error_rate_two": (max_values-len(success_measurements)) * 100 / max_values
                }
        sf.cost_logging(device_name+"_day", data)
        # Logging-Eintrag erstellen, dass keine Summe berechnet werden konnte


def cost_calc(
    device_name: str, settings: dict, login_information: sf.DataApp,
        current_timestamp: datetime, time_difference: relativedelta
) -> None:
    """
    Calculate the monthly cost for a specific device.
    :param device_name: Name of the device
    :param settings: device parameters
    :param login_information: Login information to connect with the InfluxDB
    :param current_timestamp: Now date and time from request
    :param time_difference: needed time difference for calculation
    :return: None
    """
    one_month = relativedelta(months=1)
    start_date = (current_timestamp - one_month)
    start_date_format = start_date.strftime("%Y-%m-%d %H:%M:%S")
    end_date = current_timestamp
    end_date_format = end_date.strftime("%Y-%m-%d %H:%M:%S")

    with sf.InfluxDBConnection(login_information=login_information) as conn:
        query = f'SELECT * FROM {conn.login_information.db_name}."autogen"."census" ' \
                f'WHERE device=$device AND time > $target_date AND time < $current_date'
        bind_params = {
            "device": device_name,
            "target_date": start_date_format,
            "current_date": end_date_format,
        }
        result = conn.query(query, bind_params=bind_params)

        success_measurements = list(
            filter(
                lambda measurement: measurement["fetch_success"] is True,
                result.get_points(),
            )
        )

        failed_measurements = list(
            filter(
                lambda measurement: measurement["fetch_success"] is False,
                result.get_points(),
            )
        )
        sum_of_energy_in_kwh = round(
            (sum(element["energy_wh"] for element in success_measurements)/1000), 2
        )
        cost_kwh = check_cost_config()
        count_measurements = len(success_measurements) + len(failed_measurements)
        if count_measurements == 0:
            return
        sum_of_sec = (end_date-start_date).total_seconds()
        max_values = sum_of_sec/settings["update_time"]

        data = {"start_date": start_date_format,
                "end_date": end_date_format,
                "sum_of_energy": sum_of_energy_in_kwh,
                "total_cost": sum_of_energy_in_kwh * cost_kwh,
                "cost_kwh": cost_kwh,
                "error_rate_one": len(failed_measurements) * 100 / count_measurements,
                "error_rate_two": (max_values-len(success_measurements)) * 100 / max_values
                }
        sf.cost_logging(device_name+"_month", data)
        # Logging-Eintrag erstellen, dass keine Summe berechnet werden konnte


def check_cost_calc_requested(settings: dict) -> dict:
    """
    Check if a cost calculation is requested for this device and if it has the correct formatting.
    :param settings: Settings for the selected device
    :return: The requested calculations in a dict
    """
    start_schedule_task = {
        "start_schedule_task": False,
        "cost_day": False,
        "cost_month": None,
        "cost_year": None,
    }
    if ("cost_calc_day" in settings) and (settings["cost_calc_day"]):
        start_schedule_task["cost_day"] = True
        start_schedule_task["start_schedule_task"] |= True
    if "cost_month" in settings:
        if re.search(DAY_OF_MONTH_SCHEDULE_MATCH, settings["cost_month"]) is not None:
            start_schedule_task["cost_month"] = settings["cost_month"]
            start_schedule_task["start_schedule_task"] |= True
    if "cost_year" in settings:
        if re.search(DATE_OF_YEAR_SCHEDULE_MATCH, settings["cost_year"]) is not None:
            start_schedule_task["cost_year"] = settings["cost_year"]
            start_schedule_task["start_schedule_task"] |= True
    return start_schedule_task


def cost_calc_handler(
    device_name: str, settings: dict, login_information: sf.DataApp, cost_calc_requested: dict
) -> None:
    """
    Check with costs are requested and call the correct calculations.
    :param device_name: Name of the device
    :param login_information: Login information to connect with the InfluxDB
    :param cost_calc_requested: Structure which calculations are requested
    :return: None
    """
    current_timestamp = datetime.utcnow()
    if cost_calc_requested["cost_day"]:
        cost_calc_day(device_name, settings, login_information, current_timestamp)
    if cost_calc_requested["cost_month"] is not None:
        pass
    if cost_calc_requested["cost_year"] is not None:
        pass


def main() -> None:
    """
    Scheduling function for regular call.
    :return: None
    """
    login_information = sf.DataApp()
    data = {
        "ip": "192.168.178.200",
        "update_time": 30,
        "cost_calc_day": True,
        "cost_calc_month": "01",
        "cost_calc_year": "01.01"
    }
    cost_calc_month("Kuehlschrank", data, login_information, datetime.utcnow())


if __name__ == "__main__":
    main()
