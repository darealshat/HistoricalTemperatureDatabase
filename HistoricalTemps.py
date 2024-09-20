"""This program greets the user.

After it asks for their selection from the given menu.
"""
import pgeocode as pg
import math as m
import requests
import json

request_url = "https://archive-api.open-meteo.com/v1/archive"


class HistoricalTemps:
    """Access Historical Temperatures for zipcodes from start to end date."""

    def __init__(self, zip_code: str, start="1950-08-13", end="2023-08-25"):
        """Store values and save private values."""
        self._zip_code = zip_code
        self._start = start
        self._end = end
        results = HistoricalTemps.zip_to_loc_info(zip_code)
        if m.isnan(results[1]):
            raise LookupError
        else:
            lat, lon, loc_name = results
        self._lat = lat
        self._lon = lon
        self._loc_name = loc_name
        self._temp_list = None
        self._load_temps()

    @property
    def zip_code(self):
        """Get zipcode and return it."""
        return self._zip_code

    @property
    def start(self):
        """Get start date and return it."""
        return self._start

    @start.setter
    def start(self, start):
        """Change start date."""
        og_start = self._start
        self._start = start
        try:
            self._load_temps()
        except Exception:
            self._start = og_start
            self._load_temps()
            raise LookupError

    @property
    def end(self):
        """Get end date and return it."""
        return self._end

    @end.setter
    def end(self, end):
        """Change end date."""
        og_end = self._end
        self._end = end
        try:
            self._load_temps()
        except Exception:
            self._end = og_end
            self._load_temps()
            raise LookupError

    @staticmethod
    def _convert_json_to_list(data):
        """Convert json to list and return date and time tuple."""
        data = json.loads(data)
        daily_data = data['daily']
        for times in daily_data:
            if times == 'time':
                dates = daily_data[times]
            if times == 'temperature_2m_max':
                temps = daily_data[times]
        temp_list = [(dates, temps) for dates, temps
                     in zip(dates, temps)]
        return temp_list

    @staticmethod
    def zip_to_loc_info(zip_code: str):
        """Take zipcode and return latitude, longitude and city name."""
        geocoder = pg.Nominatim('us')
        result = geocoder.query_postal_code(zip_code)
        lat = result['latitude']
        lon = result['longitude']
        loc_name = result['place_name']
        return lat, lon, loc_name

    @property
    def loc_name(self):
        """Get location name."""
        return self._loc_name

    def _load_temps(self):
        """Make a list of dates and temperatures."""
        parameters = {"latitude": self._lat, "longitude": self._lon,
                      "start_date": self._start, "end_date": self._end,
                      "daily": "temperature_2m_max",
                      "timezone": "America/Los_Angeles"}
        results = requests.get(request_url, parameters)
        self._temp_list = (
            HistoricalTemps._convert_json_to_list(results.text))
        return self._temp_list

    def extreme_days(self, threshold: float):
        """Extract high temperature dates from temperature list."""
        extremes_list = [high_temps for high_temps in self._temp_list
                         if high_temps[1] > threshold]
        return extremes_list

    def average_temp(self):
        """Calculate average temperatures from list."""
        temperature_list = HistoricalTemps._load_temps(self)
        total_temps = 0
        for temperature in temperature_list:
            total_temps += temperature[1]
        avg_temp = (total_temps / len(self._temp_list))
        return avg_temp

    def top_x_days(self, num_days=10):
        """Return top 10 highest temperature days."""
        top_days = sorted(self._temp_list, key=lambda x: x[1], reverse=True)
        return top_days[:num_days]


def compare_average_temps(dataset_one: HistoricalTemps,
                          dataset_two: HistoricalTemps):
    """Compare average temperatures between two historical temperatures."""
    if dataset_one is None or dataset_two is None:
        print("Please load two datasets first")
        return None
    else:
        ds1_avg_temp = round(dataset_one.average_temp(), 2)
        ds2_avg_temp = round(dataset_two.average_temp(), 2)
        print(f"The average maximum temperatures for {dataset_one.loc_name} "
              f"was {ds1_avg_temp} degrees Celsius.")
        print(f"The average maximum temperatures for {dataset_two.loc_name}"
              f" was {ds2_avg_temp} degrees Celsius.")


def print_extreme_days(dataset: HistoricalTemps):
    """Print high temperature dates from temperature list."""
    if dataset is None:
        print("Please load this dataset first")
    else:
        threshold = input("List days above what temperature? ")
        try:
            threshold = float(threshold)
        except ValueError:
            print("Please enter a valid temperature")
            return None
        list_of_extreme_days = dataset.extreme_days(threshold)
        number_of_exceeded_days = len(list_of_extreme_days)
        print(f"There are {number_of_exceeded_days} days above {threshold} "
              f"in {dataset.loc_name}")
        for extreme_days in list_of_extreme_days:
            print(f"{extreme_days[0]}: {extreme_days[1]}")


def print_top_five_days(dataset: HistoricalTemps):
    """Print top 5 highest temperature days."""
    if dataset is None:
        print("Please load this dataset first")
    else:
        top_5_days = dataset.top_x_days(5)
        print(f"Following are the hottest five days in {dataset.loc_name} "
              f"on record from {dataset.start} to {dataset.end}")
        for extreme_days in top_5_days:
            print(f"Date {extreme_days[0]}: {extreme_days[1]}")


def change_dates(dataset: HistoricalTemps):
    """Change dates."""
    if dataset is None:
        print("Please load this dataset first")
    else:
        try:
            start_dates = input("Please enter a new start date (YYYY-MM-DD): ")
            dataset.start = start_dates
        except LookupError:
            print("Start date could not be changed. "
                  "Please check that the start date is in the "
                  "correct format and is before the current end date "
                  "of 2020-10-10")
            return None
        try:
            end_date = input("Please enter a new end date (YYYY-MM-DD): ")
            dataset.end = end_date
        except LookupError:
            print("End date could not be changed. "
                  "Please check that the end date is in the "
                  "correct format and is after the current "
                  "start date of 2022-11-10")
            return None


def main():
    """Ask the user for their name and greets them."""
    user_name = input("Please enter your name: ")
    print(f"Hi {user_name}, let's explore some historical temperatures.")
    menu()


def menu():
    """Print the menu and then ask the user for their choice.

    Confirms that the users input is values.
    """
    dataset_one = None
    dataset_two = None

    while True:
        print_menu(dataset_one, dataset_two)
        user_choice = input("What is your choice? ")
        # Check if user input is an integer. If not loop again
        try:
            int_choice = int(user_choice)
        except ValueError:
            print("Please enter a number only")
            continue
        match user_choice:
            case "1":
                dataset_one = create_dataset()
            case "2":
                dataset_two = create_dataset()
            case "3":
                compare_average_temps(dataset_one, dataset_two)
            case "4":
                print_extreme_days(dataset_one)
            case "5":
                print_top_five_days(dataset_one)
            case "6":
                change_dates(dataset_one)
            case "7":
                change_dates(dataset_two)
            case "8":
                print("Selection eight is not functional yet")
            case "9":
                print("Goodbye!  Thank you for using the database")
                break
            case _:
                print("That wasn't a valid selection")


def print_menu(dataset_one, dataset_two):
    """Print the menu."""
    print("Main Menu")
    if not dataset_one:
        print("1 - Load dataset one")
    else:
        print(f"1 - Replace {dataset_one.loc_name}")
    if not dataset_two:
        print("2 - Load dataset two")
    else:
        print(f"2 - Replace {dataset_two.loc_name}")
    print("3 - Compare average temperatures")
    print("4 - Dates above threshold temperature")
    print("5 - Highest historical dates")
    print("6 - Change start and end dates for dataset one")
    print("7 - Change start and end dates for dataset two")
    print("9 - Quit")


def create_dataset():
    """
    Create an object in the HistoricalTemps class for user given zipcode.

    After it returns it.
    """
    try:
        user_zipcode = HistoricalTemps(input("Please enter a zipcode "))
        return user_zipcode
    except LookupError:
        print("Data could not be loaded. Please check that the zip code"
              " is correct and that you have a working internet connection")
        return None


if __name__ == '__main__':
    """Run the main program."""
    main()
