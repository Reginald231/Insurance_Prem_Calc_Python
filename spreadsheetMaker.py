import csv


class SpreadSheetMaker:

    data = list()
    preferred_sheet_name = None

    def build_spreadsheet(self):
        with open(self.preferred_sheet_name, newline='',mode='w') as csv_file:
            fieldnames = ['Zip Code', 'Annual Premium']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rowdicts=self.data)

        print('Created spreadsheet.')

    def __init__(self, data, preferred_sheet_name):
        self.data = data
        self.preferred_sheet_name = preferred_sheet_name + ".csv"
