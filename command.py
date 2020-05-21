"""
用于把企业的名单=>json
"""
import os
import json
import xlrd
from datetime import datetime
from CNKIPaSearch.utils import date2str


def write_from_xlsx(filename, output_file, pass_line=None, limit=None):
    data = xlrd.open_workbook(filename)
    # 获取第一个sheet
    table = data.sheet_by_index(0)
    # 公司名称 是否有专利
    col_values = table.col_values(0)
    applicants = []
    # 去掉第一行
    for index, name in enumerate(col_values):
        # 如果是第一行或者没有专利，则跳过
        applicant = name.strip()
        if (pass_line is not None and index == pass_line) or len(applicant) == 0 or applicant in applicants:
            continue
        if limit and index > limit:
            break
        values = applicant.split(',')
        applicants.extend(values)

    print('共计', len(applicants))
    now = datetime.now()
    last = datetime(year=now.year-5, month=now.month, day=now.day)
    # json_data = [{
    #      "applicant": applicant,
    #      "date_gkr_from": date2str(last),
    #      "date_gkr_to": date2str(date=now),
    #      "thesis_level": "1",
    #      }
    #     for applicant in applicants
    # ]
    json_data = [{
         "applicant": applicant,
         "publishdate_from": date2str(last),
         "publishdate_to": date2str(date=now),
         "thesis_level": "1",
         }
        for applicant in applicants
    ]
    # json_data = [{"applicant": applicant} for applicant in applicants]
    print(json_data)
    with open(output_file, 'w', encoding='utf-8') as fp:
        json.dump(json_data, fp, ensure_ascii=False, indent=2)
    print('写入到%s' % output_file)


if __name__ == '__main__':
    filename = '02-方宇.xls'
    output = os.path.join('files')
    if not os.path.exists(output):
        os.makedirs(output)
    write_from_xlsx(filename, os.path.join(output, 'applicants.json'), pass_line=0)
