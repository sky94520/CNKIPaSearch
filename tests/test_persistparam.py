import os
import pytest
from CNKIPaSearch.PersistParam import PersistParam


@pytest.fixture(scope='function')
def params():
    basedir = os.path.realpath(os.path.dirname(__file__))
    params = PersistParam(basedir)
    params.request_queue = [
        {'applicant': '东南大学'},
        {'applicant': '浙江大学'}
    ]
    yield params


def test_set_groups(params):
    years = [1985, 1987, 1986, 1990, 1996, 1993, 1995, 1997, 1991, 1989, 1988, 2000, 1998, 1999, 1994, 1992, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020]
    numbers = [10, 31, 37, 44, 46, 48, 58, 64, 65, 66, 71, 77, 79, 85, 87, 93, 106, 293, 527, 556, 1124, 1397, 1573, 1916, 2037, 2665, 2760, 3099, 3292, 3209, 3594, 3259, 3613, 4082, 7082, 1293]
    params.set_groups(years, numbers, 6000)
    for datum in params.request_queue:
        print(datum)


def test_set_groups2(params):
    years = [2016, 2017]
    numbers = [6001, 2855]
    params.set_groups(years, numbers, 6000)
    for datum in params.request_queue:
        print(datum)


def test_set_groups3(params):
    years = [2016]
    numbers = [2382]
    params.set_groups(years, numbers, 6000)
    for datum in params.request_queue:
        print(datum)


if __name__ == '__main__':
    pytest.main([__file__, '-s'])
