import stackoverflow_jobs
from bs4 import BeautifulSoup
from xlrd import open_workbook
import pandas as pd


def test_jobs_exist():

    try:
        listing_page = stackoverflow_jobs.get_url('https://stackoverflow.com/jobs?sort=i&l=Bridgewater%2C+MA%2C+USA&d=50&u=Miles')

    finally:
        pass

    listing_soup = BeautifulSoup(listing_page, 'lxml')
    job_post = listing_soup.find('div', class_ = '-job-summary ')
    assert job_post is not None


def test_number_of_columns():
    workbook = open_workbook('../stackoverflow_jobs.xlsx')
    sheet = workbook.sheet_by_name('Jobs List')

    number_of_columns = sheet.ncols

    assert (number_of_columns == 8)


def test_empty_cells():

    workbook = open_workbook('../stackoverflow_jobs.xlsx')
    sheet = workbook.sheet_by_name('Jobs List')

    number_of_rows = sheet.nrows
    number_of_columns = sheet.ncols

    empty_cell_found = False
    for row in range(1, number_of_rows):

        for col in range(number_of_columns):

            value = sheet.cell(row, col).value

            if len(value) == 0:
                empty_cell_found = True

    assert empty_cell_found is False


def test_no_value_in_jobs_amount():

    jobs_reader = pd.read_excel('../stackoverflow_jobs.xlsx')

    num_of_jobs_series = jobs_reader['Location'].value_counts()

    try:
        job_amount = pd.Index(num_of_jobs_series).get_loc(0)

    except Exception:
        assert True

    else:
        assert False