# CQC-Data cli

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/ouseful-datasupply/cqc_uk/master)

Simple CLI to download CQC data ([Using CQC data](http://www.cqc.org.uk/about-us/transparency/using-cqc-data)) and pop it into a `SQLite3` database.

By default, the database is created as `cqc_data.db` with tables:

- `location_service_type`
- `location_specialism`
- `locations`
- `active_locations`
- `active_location_measures`
- `ratings_locations`
- `rated_locations`
- `ratings_providers`
- `rated_providers`

The data tables are simple long form and partially normalised.

An easy way of querying the database via a browser is to use [*Franchise*](https://blog.ouseful.info/2017/09/25/asking-questions-of-csv-data-in-the-browser-with-franchise/).

See the database running as a [datasette](https://github.com/simonw/datasette) at: [https://ousefulnhsdata.herokuapp.com/](https://ousefulnhsdata.herokuapp.com/)

## Installation

`pip install --upgrade --no-deps git+https://github.com/ouseful-datasupply/cqc_uk.git`

## Usage

- `cqc_data collect `
- `cqc_data [OPTIONS] collect`

### Options:

- `--dbname`, *default='cqc_data.db'*, SQLite database name
