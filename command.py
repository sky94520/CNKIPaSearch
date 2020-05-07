"""
用于把企业的名单=>json
"""
import os
import json
import xlrd


def write_from_xlsx(filename, output_file, pass_line=None):
    data = xlrd.open_workbook(filename)
    # 获取第一个sheet
    table = data.sheet_by_index(0)
    rows = table.nrows  # 总行数
    cols = table.ncols  # 总列数
    # 公司名称 是否有专利
    col_values = table.col_values(0)
    applicants = []
    # 去掉第一行
    for index, name in enumerate(col_values):
        # 如果是第一行或者没有专利，则跳过
        applicant = name.strip()
        if (pass_line and index == pass_line) or len(applicant) == 0 or applicant in applicants:
            continue
        applicants.append(applicant)

    print('共计', len(applicants))
    json_data = [{"applicant": applicant, "thesis_level": "4"} for applicant in applicants]
    # json_data = [{"applicant": company} for company in companies]
    print(json_data)
    with open(output_file, 'w', encoding='utf-8') as fp:
        json.dump(json_data, fp, ensure_ascii=False, indent=2)
    print('写入成功')


if __name__ == '__main__':
    filename = ''
    output = os.path.join('files', 'pending')
    if not os.path.exists(output):
        os.makedirs(output)
    write_from_xlsx(filename, os.path.join(output, 'applicants.json'))
