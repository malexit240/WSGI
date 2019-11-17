from utils import base36_encode


def insert_url(redis, url) -> int:
    short_id = redis.get("reverse-url:" + url)
    if short_id is not None:
        return short_id.decode('utf-8')
    url_num = redis.incr("last-url-id")
    short_id = base36_encode(url_num)
    redis.set("url-target:" + short_id, url)
    redis.set("reverse-url:" + url, short_id)
    return int(short_id)


def get_url(redis, short_id):
    return redis.get("url-target:" + short_id).decode('utf-8')


def increment_url(redis, short_id):
    redis.incr("click-count:" + short_id)


def get_count(redis, short_id):
    return int(redis.get("click-count:" + short_id) or 0)

def get_list_urls(redis):  
    short_ids = [url.decode('utf-8') 
        for url in map(redis.get,redis.keys("reverse-url*"))]

    info = {}

    for id in short_ids:
        info[id] = [get_url(redis,id),get_count(redis,id)]
    return info

 