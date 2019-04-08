import os


class CouserahubDownloader(object):
    """
    对于 目录, 新建目录;
    对于 文件, 新建文件.
    """
    def process_response(self, request, response, spider):
        path = spider.target_directory + request.meta['path']
        is_file = 1 if request.meta['type'] in ('file', 'notebook') else 0
        is_existed = os.path.exists(path)
        if is_existed and not spider.overwrite_file:
            return response
        if is_file:
            # save content to file
            with open(path, 'wb') as f:
                f.write(response.body)
        elif is_existed:
            # mkdir -p path
            os.makedirs(path)
        return response
     
