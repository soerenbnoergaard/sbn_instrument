import csv

class CsvWriter:
    """Continuous CSV file writer, opening and closing the file for each
    write.
    """

    def __init__(self, filename):
        self.filename = filename
        self.columns = None
        self.csv_args = {"delimiter":",", "quotechar":'"', "quoting":csv.QUOTE_MINIMAL}

    def write(self, data):
        """Write a data record to the file. A data records is a dict with the
        column names as keys and data as values.
        """

        self.write_all([data])

    def write_all(self, data_list):
        """Write a list of data records to a file (see the ``write()`` method
        for details).
        """

        # Write column header
        if self.columns is None:
            self.columns = list(data_list[0].keys())
            with open(self.filename, "w", newline="") as f_h:
                csv_h = csv.writer(f_h, **self.csv_args)
                csv_h.writerow(self.columns)

        # Write data
        with open(self.filename, "a", newline="") as f_h:
            csv_h = csv.writer(f_h, **self.csv_args)
            csv_h.writerows([[data[k] for k in self.columns] for data in data_list])
