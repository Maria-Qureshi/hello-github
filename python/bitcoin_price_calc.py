# this program calculates the price of one or less thanone or multiple bitcoins
#usage: {program name} number_of coins

import requests
import sys

def main():

    try:
        num_bitcoin = float(sys.argv[1])
    except ValueError:
        sys.exit("invalid type ")

    try:
        API = requests.get(" https://api.coindesk.com/v1/bpi/currentprice.json")

    except requests.RequestException:
        sys.exit("error making request")

    API = API.json()

    price = API["bpi"]["USD"]["rate_float"]

    amount = price * num_bitcoin

    print(f"${amount:,.4f}")

if __name__ == "__main__":
    main()

