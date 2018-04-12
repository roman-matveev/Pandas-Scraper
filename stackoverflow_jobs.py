from bs4 import BeautifulSoup
import requests
import pandas as pd
from time import time
from time import sleep
from random import randint

import plotly.graph_objs as gr
import plotly.offline as pl

job_titles = []
job_post_dates = []
company_names = []
company_locations = []
job_perks = []
job_equities = []
job_tags = []
job_links = []


def get_url(url):
    return requests.get(url).text


def scrape_jobs(query_url, search_query):

    search_prefix = '&q='
    page_prefix = '&pg='
    pages = [str(i) for i in range(1, 6)]

    request_start_time = time()
    requests_made = 0

    for page in pages:

        listing_page = get_url(query_url + page_prefix + page + search_prefix + search_query)

        sleep(randint(1, 2))
        requests_made += 1
        request_elapsed_time = time() - request_start_time
        print('Request {} - ({} requests per second)'.format(requests_made, requests_made / request_elapsed_time))

        listing_soup = BeautifulSoup(listing_page, 'lxml')

        for job_post in listing_soup.find_all('div', class_= '-job-summary '):

            job_title = job_post.find('a', class_ = 'job-link').text
            job_titles.append(job_title)

            job_post_date = job_post.find('p', class_ = '-posted-date g-col').text.strip()
            job_post_dates.append(job_post_date)

            company_name = job_post.find('div', class_ = '-name').text.strip()
            company_names.append(company_name)

            company_location = job_post.find('div', class_ = '-location').text.strip().split('\n')[1]
            company_locations.append(company_location)

            try:
                job_perk = job_post.find('div', class_ = '-perks g-row').span.text.split('\r\n')[1].strip()
            except Exception:
                job_perk = "Undisclosed"
            job_perks.append(job_perk)

            try:
                job_equity = job_post.find('div', class_ = '-perks g-row').span.text.split('\r\n')[4].strip()
            except Exception:
                job_equity = "None"
            job_equity += " offered"
            job_equities.append(job_equity)

            job_tags_list = []
            job_tags_text = ""
            for job_tag in job_post.find_all('a', class_ = 'post-tag job-link no-tag-menu'):
                job_tags_list.append(job_tag.text)
                job_tags_text = ', '.join(job_tags_list)
            job_tags.append(job_tags_text)

            site = 'https://stackoverflow.com'
            job_link_local = job_post.find('a', class_ = 'job-link').attrs['href']
            job_link_joined = site + job_link_local
            job_links.append(job_link_joined)


def display_jobs_in_console():

    pd.set_option('display.width', 1080)
    pd.set_option('display.max_colwidth', -1)
    pd.set_option('display.max_rows', 1000)
    pd.set_option('colheader_justify', 'center')

    jobs_frame = pd.DataFrame({
        'Job Title'   : job_titles,
        'Post Date'   : job_post_dates,
        'Company Name': company_names,
        'Location'    : company_locations,
        'Perks'       : job_perks,
        'Equities'    : job_equities,
        'Tags'        : job_tags,
        'Link'        : job_links})

    jobs_frame_ordered = jobs_frame[[
        'Job Title', 'Post Date', 'Company Name', 'Location', 'Perks', 'Equities', 'Tags', 'Link']]
    print(jobs_frame_ordered)
    return jobs_frame_ordered


def display_jobs_in_excel(jobs_frame_ordered):

    jobs_writer = pd.ExcelWriter('stackoverflow_jobs.xlsx', engine = 'xlsxwriter')
    jobs_frame_ordered.to_excel(jobs_writer, index = False, sheet_name = 'Jobs List')

    workbook = jobs_writer.book
    jobs_list_worksheet = jobs_writer.sheets['Jobs List']
    jobs_list_worksheet.set_column('A:A', 70)
    jobs_list_worksheet.set_column('B:B', 15)
    jobs_list_worksheet.set_column('C:C', 30)
    jobs_list_worksheet.set_column('D:D', 15)
    jobs_list_worksheet.set_column('E:E', 15)
    jobs_list_worksheet.set_column('F:F', 15)
    jobs_list_worksheet.set_column('G:G', 65)
    jobs_list_worksheet.set_column('H:H', 100)

    jobs_list_header_formatting = workbook.add_format({
        'fg_color': '#446CB3', 'font_size': 18, 'font_color': '#E4F1FE', 'align': 'center'})

    for col_num, value in enumerate(jobs_frame_ordered.columns.values):
        jobs_list_worksheet.write(0, col_num, value, jobs_list_header_formatting)

    jobs_writer.save()


def scrape_lat_and_lon(jobs_from_excel, latlon_from_csv):

    jobs_reader = pd.read_excel(jobs_from_excel)
    latlon_reader = pd.read_csv(latlon_from_csv)

    num_of_jobs_series = jobs_reader['Location'].value_counts()

    job_count_frame = pd.DataFrame({
        'Location': num_of_jobs_series.index,
        'JobCount': num_of_jobs_series.values})
    job_count_frame['JobCount'] = job_count_frame['JobCount'].astype(str)

    latlon_reader['info'] = latlon_reader['city'] + ', ' + latlon_reader[(latlon_reader['state'] == 'MA')
                                                                         | (latlon_reader['state'] == 'RI')]['state']
    latlon_reader['info'].dropna()

    latlon_reader.set_index('info')
    latlon_reader.drop('zip_code', axis=1, inplace=True)
    jobs_reader.set_index('Location')

    job_map = latlon_reader.merge(jobs_reader, left_on= 'info', right_on= 'Location', how= 'inner')
    job_map_with_count = job_map.merge(job_count_frame, left_on='info', right_on='Location', how='inner')
    return job_map_with_count


def display_map(coordinates_for_map, mapbox_token):

    job_locations = gr.Data([
        gr.Scattermapbox(
            lat = coordinates_for_map.latitude,
            lon = coordinates_for_map.longitude,
            mode = 'markers',
            marker = gr.Marker(
                size = 12,
                color = 'rgb(24, 108, 168)',
                opacity = 0.7
            ),
            text = coordinates_for_map['info'] + '<br>Jobs available in this area: ' + coordinates_for_map['JobCount'],
            hoverinfo = 'text'
        )
    ])

    map_layout = gr.Layout(
        title = 'Jobs in the MA/RI Area',
        autosize = True,
        hovermode = 'closest',
        showlegend = False,
        mapbox = dict(
            accesstoken = mapbox_token,
            bearing = 0,
            center = dict(
                lat = 42.4072,
                lon = -71.3824
            ),
            pitch = 10,
            zoom = 7,
            style = 'light'
        )
    )

    coordinates_for_map = dict(data = job_locations, layout = map_layout)
    pl.plot(coordinates_for_map, filename = 'stackoverflow_jobs_map.html')


def main():
    search_query = input('Enter a job search query (ie, software engineer, python r, sql): ')

    scrape_jobs('https://stackoverflow.com/jobs?sort=i&l=Bridgewater%2C+MA%2C+USA&d=50&u=Miles', search_query)
    display_jobs_in_excel(display_jobs_in_console())

    coordinates_for_map = scrape_lat_and_lon('stackoverflow_jobs.xlsx', 'https://www.gaslampmedia.com/wp-content/uploads/2013/08/zip_codes_states.csv')
    display_map(coordinates_for_map, 'pk.eyJ1Ijoicm1hdHZlZXYiLCJhIjoiY2pleG4wMzJpMThkcDMzcWplcDRpM3YwaCJ9.gtSLpI_cg_oJjCNH5ftxUA')


if __name__ == '__main__':
    main()