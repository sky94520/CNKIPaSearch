import os
import csv
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

from CNKIPaSearch.settings import BASEDIR, PAGE_DIR
from CNKIPaSearch.utils import date2str
from CNKIPaSearch.hownet_config import FROM_DATE_KEY, TO_DATE_KEY


if __name__ == '__main__':
    filename = os.path.join(BASEDIR, 'files', 'schools.csv')
    fp = open(filename, 'r', encoding='utf-8')
    reader = csv.DictReader(fp)
    json_data = []
    for datum in reader:
        # 添加申请日 开始时间和结束时间
        to_date = datetime.now()
        from_date = to_date - relativedelta(years=10)
        datum[FROM_DATE_KEY] = date2str(date=from_date)
        datum[TO_DATE_KEY] = date2str(date=to_date)
        json_data.append(datum)
    fp.close()

    path = os.path.join(PAGE_DIR, 'pending')
    if not os.path.exists(path):
        os.makedirs(path)
    with open(os.path.join(path, 'applicants.json'), 'w', encoding='utf-8') as fp:
        json.dump(json_data, fp, ensure_ascii=False, indent=1)
