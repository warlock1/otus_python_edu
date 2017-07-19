#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gzip
import re
import json
import os

# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}

FIELDS = (
    ('remote_addr', r'(?P<remote_addr>\S+)'),
    ('remote_user', r'(?P<remote_user>\S+)'),
    ('http_x_real_ip', r'(?P<http_x_real_ip>\S+)'),
    ('time_local', r'\[(?P<time_local>.*)\]'),
    ('request', r'"(?P<request>.*)"'),
    ('status', r'(?P<status>\S+)'),
    ('body_bytes_sent', r'(?P<body_bytes_sent>\S+)'),
    ('http_referer', r'"(?P<http_referer>.*)"'),
    ('http_user_agent', r'"(?P<http_user_agent>.*)"'),
    ('http_x_forwarded_for', r'"(?P<http_x_forwarded_for>.*)"'),
    ('http_X_REQUEST_ID,', r'"(?P<http_X_REQUEST_ID>.*)"'),
    ('http_X_RB_USER', r'"(?P<http_X_RB_USER>.*)"'),
    ('request_time', r'(?P<request_time>\S+)'),
)
RE_PARSE_LINE = re.compile(r'\s+'.join(f[1] for f in FIELDS))

REPORT_TEMPLATE = 'report.html'
LOG_NAME_PREFIX = 'nginx-access-ui.log-'

def main(config):
    last_log_name = get_last_log_name(config['LOG_DIR'])
    if last_log_name:
        report_name = os.path.join(config['REPORT_DIR'], 'report-%s.html' % get_date_from_file_name(last_log_name))
        if not os.path.exists(report_name):
            data, count_all, time_all = parse_file(os.path.join(config['LOG_DIR'], last_log_name))
            result = calc_result(data, count_all, time_all, config['REPORT_SIZE'])
            render_result(result, report_name)


def get_date_from_file_name(file_name):
    tmp_date = file_name[len(LOG_NAME_PREFIX):len(LOG_NAME_PREFIX) + 8]
    return '%s.%s.%s' % (tmp_date[:4], tmp_date[4:6], tmp_date[6:8])


def get_last_log_name(log_dir):
    files = sorted([fn for fn in os.listdir(log_dir) if os.path.isfile(os.path.join(log_dir, fn))],
        reverse=True, key=get_date_from_file_name)
    if files:
        return files[0]
    return None


def parse_file(file_name):
    result = {}
    count_all = time_all = 0
    opener = gzip.open if file_name.endswith('.gz') else open
    for e, line in enumerate(opener(file_name), 1):
        rec = RE_PARSE_LINE.search(line).groupdict()
        req_split = rec['request'].split()
        if len(req_split) == 3:
            url = rec['request'].split()[1]
        else:
            url = rec['request']
        req_time = float(rec['request_time'])
        result.setdefault(url, []).append(req_time)
        count_all += 1
        time_all += req_time
    return result, count_all, time_all


def calc_result(data, count_all, time_all, report_size):
    CALC_VALUES = {
        'count': len,
        'count_perc': lambda v: round((100 * float(len(v))) / count_all, 3),
        'time_avg': lambda v: round(sum(v) / len(v), 3),
        'time_max': max,
        'time_med': lambda v: round(sorted(v)[len(v) // 2], 3),
        'time_perc': lambda v: round((100 * sum(v)) / time_all, 3),
        'time_sum': lambda v: round(sum(v), 3)
    }

    result = []
    for url, times in data.items():
        rec = {'url': url}
        for field, func in CALC_VALUES.items():
            rec[field] = func(times)
        result.append(rec)
    return sorted(result, reverse=True, key=lambda v: (v['time_perc'], v['time_sum']))[:report_size]


def render_result(data, report_file_name):
    template = open(REPORT_TEMPLATE).read()
    open(report_file_name, 'w').write(template.replace('$table_json', json.dumps(data)))


if __name__ == "__main__":
    main(config)
