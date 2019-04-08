import json
import os
import time
import traceback
from scrapy import Spider, Request
from crawlers.utils import iso_today
from . import secret_id


def format_cookies_headers_params(timestamp):
    xsrf = '2|761069a4|73f9e261dd51da5dc5e9fcefb0832a56|{}'.format(timestamp)
    cookies = {
        'COURSERA_SUBMISSION_TOKEN': 'GLKxj8W0bfl8WmXc3txh',
        'thdmnzejgeuqmfmskemqnd-wkspc-sid': secret_id,
        '_xsrf': xsrf,
    }
    headers = {
        'Host': 'thdmnzejgeuqmfmskemqnd.coursera-apps.org',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Connection': 'keep-alive',
        'Accept-Language': 'en-us',
        'Accept-Encoding': 'br, gzip, deflate',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1.2 Safari/605.1.15',
        'Referer': 'https://thdmnzejgeuqmfmskemqnd.coursera-apps.org/tree/Week%202',
        'X-XSRFToken': xsrf,
        'X-Requested-With': 'XMLHttpRequest',
    }
    params = (
        ('type', 'directory'),
        ('_', '1554368957908'),
    )
    return {'cookies': cookies, 'headers': headers, 'params': params}


class CouserahubNotebookSpider(Spider):
    name = 'courserahub'
    overwrite_file = False  # if over write the old files
    target_directory = os.path.expanduser('~/CourseraHub/DNN/')
    tree_api = 'https://thdmnzejgeuqmfmskemqnd.coursera-apps.org/api/contents/{path}?type=directory&_={ts}'
    file_api = 'https://thdmnzejgeuqmfmskemqnd.coursera-apps.org/files/{path}?download=1'

    custom_settings = {
        'DOWNLOAD_DELAY': 1,
        'LOG_FILE': 'logs/%s_%s.log' % (name, iso_today()),
        # 'DUPEFILTER_CLASS': 'crawlers.dupefilters.DuplicateUrlFilter',
        'DOWNLOADER_MIDDLEWARES': {
            'crawlers.downloader_middlewares.CouserahubDownloader': 500,
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
        },
    }

    def start_requests(self):
        """
        从 root of tree 开始, path是 ''
        """
        timestamp = int(time.time())
        request_args = format_cookies_headers_params(timestamp)
        root_url = self.tree_api.format(path='', ts=timestamp)
        meta = {'path': '', 'type': 'directory'}
        yield Request(root_url, callback=self.parse, cookies=request_args['cookies'], headers=request_args['headers'],
                      meta=meta)

    def parse(self, response):
        """
        解析 层次结构
        """
        current_path = response.meta['path']
        if response.meta['type'] in ('notebook', 'file'):
            return
        try:
            data = json.loads(response.text)
        except Exception as e:
            traceback.print_exc()
            return
        timestamp = int(time.time())
        request_args = format_cookies_headers_params(timestamp)
        for line in data['content']:
            sub_path = current_path + '/' + line['name']
            sub_path = sub_path.strip('/')
            meta = {'path': sub_path, 'type': line['type']}
            if line['type'] == 'directory':
                # 目录: 递归访问
                meta['type'] = line['type']
                directory_url = self.tree_api.format(path=sub_path, ts=timestamp)
                directory_req = Request(directory_url, meta=meta)
                yield directory_req
            elif line['type'] in ('notebook', 'file'):
                # 文件: 下载文件
                file_url = self.file_api.format(path=sub_path)
                file_req = Request(file_url, callback=self.parse, cookies=request_args['cookies'],
                                   headers=request_args['headers'], meta=meta)
                yield file_req
            else:
                print("Unexpected file type: ", line)
