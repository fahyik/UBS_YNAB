# -*- coding: utf-8 -*-
import csv
import datetime
import logging
import pprint
import sys

logger = logging.getLogger("ubs-")
handler = logging.StreamHandler()
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

pp = pprint.PrettyPrinter(indent=4)

KNOWN_PAYEES = [
    ("Coop", "Coop"),
    ("Migros", "Migros"),
    ("LIDL", "Lidl"),
    ("ASOS", "ASOS"),
    ("ZVV", "ZVV")
]


def main(*args):
    """A script used to convert UBS CH credit card statements to a YNAB-friendly
    format

    YNAB does not support banks outside of US, in order to use, we need to manually
    upload statements to the platform.

    Uplaod csv needs to be in a specific format, this script takes the raw download
    from UBS I-banking platform and converts it to a csv ready to upload to YNAB

    Parameters
    ----------
    *args
        takes the list of command line arguments, sys.argv

        args[0]:
            path to this script

        args[1]: str
            path to target file to parse

        args[2]: str, optional
            minimum date to parse from
            entries with date less than this minimum will not be parsed

    Returns
    -------
    None
        a csv with filename args[1]_output.csv will be generated
        file will be formatted in a way suitable for immediate upload to YNAB

    Raises
    ------
    ValueError
        If filename is not passed

    """

    try:
        filename = args[1]
        filename = filename[:-4]  # remove .csv
    except IndexError:
        raise ValueError('Input filename not specified')

    # get min_date, if specified
    try:
        min_date = args[2]
        min_date = datetime.datetime.strptime(min_date, "%Y-%m-%d")
    # else set as 2000-01-01
    except IndexError:
        min_date = datetime.datetime(2000, 1, 1)

    # invoice and transactions are parsed differently
    if "invoice" in filename:
        invoice = True
    else:
        invoice = False

    # import data
    with open(filename + ".csv", "rU") as csvfile:
        incsv = csv.reader(csvfile, delimiter=";")

        # ignore first row with sep=;
        next(incsv)

        # header row
        headers_in = tuple(next(incsv))

        if not invoice:
            # ignore third row with balance brought forward;
            next(incsv)

        with open(filename + '_output.csv', 'wu') as file:

            writer = csv.writer(file)
            headers_out = ["Date", "Payee", "Memo", "Inflow", "Outflow"]
            writer.writerow(headers_out)

            for each in incsv:

                each = dict(zip(headers_in, each))

                if not each:
                    break
                elif not each['Booked']:
                    continue
                elif datetime.datetime.strptime(each['Purchase date'], "%d.%m.%Y") < min_date:
                    continue

                if check_payees(each):
                    pass
                else:
                    each['Booking text'] = each['Booking text'].split(" ", 1)[0]

                writer.writerow([each["Purchase date"],
                                 each["Booking text"],
                                 each.get('Memo', None),
                                 each["Credit"],
                                 each["Debit"]
                                 ])


def check_payees(each):

    for payee in KNOWN_PAYEES:

        if payee[0] in each['Booking text']:
            each['Booking text'] = payee[1]
            return True

    return False


if __name__ == '__main__':
    main(*sys.argv)
