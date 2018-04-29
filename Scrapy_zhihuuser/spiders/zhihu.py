# -*- coding: utf-8 -*-
import json
from Scrapy_zhihuuser.items import UserItem

from scrapy import Spider, Request


class ZhihuSpider(Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']
    # 程序如何入口用户(轮子哥)
    start_user = "excited-vczh"

    # 用户详情url
    user_url = "https://www.zhihu.com/api/v4/members/{user}?include={include}"
    user_query = "allow_message,is_followed,is_following,is_org,is_blocking,employments,answer_count,follower_count,articles_count,gender,badge[?(type=best_answerer)].topics"

    # 关注者的url
    follows_url = "https://www.zhihu.com/api/v4/members/{user}/followees?include={include}&offset={offset}&limit={limit}"
    follows_query = "data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics"

    # 粉丝的url
    followers_url = "https://www.zhihu.com/api/v4/members/{user}/followers?include={include}&offset={offset}&limit={limit}"
    followers_query = "data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics"

    # 开始首次请求，获取第一个用户的个人信息、关注者信息和粉丝信息
    def start_requests(self):
        yield Request(self.user_url.format(user=self.start_user, include=self.user_query), self.parse_user)
        yield Request(self.follows_url.format(user=self.start_user, include=self.follows_query, offset=0, limit=20), callback=self.parse_follows)
        yield Request(self.followers_url.format(user=self.start_user, include=self.followers_query, offset=0, limit=20), callback=self.parse_followers)

    # 解析获取每个用户的详细信息
    def parse_user(self, response):
        result = json.loads(response.text)
        item = UserItem()
        for field in item.fields:
            if field in result.keys():
                item[field] = result.get(field)
        yield item
        # 获取每个用户的关注者和粉丝
        yield Request(self.follows_url.format(user=result.get("url_token"), include=self.follows_query, limit=20, offset=0), self.parse_follows)
        yield Request(self.followers_url.format(user=result.get("url_token"), include=self.followers_query, limit=20, offset=0), self.parse_followers)

    # 获取每个关注者的个人url,并进行翻页，获取所有的关注者
    def parse_follows(self, response):
        results = json.loads(response.text)

        if "data" in results.keys():
            for result in results.get("data"):
                yield Request(self.user_url.format(user=result.get("url_token"), include=self.user_query), self.parse_user)

            if "paging" in results.keys() and results.get("paging").get("is_end") == False:
                next_page = results.get("paging").get("next")
                yield Request(next_page, self.parse_follows)

    # 获取每个粉丝的个人url,并进行翻页，获取所有的关注者
    def parse_followers(self, response):
        results = json.loads(response.text)

        if "data" in results.keys():
            for result in results.get("data"):
                yield Request(self.user_url.format(user=result.get("url_token"), include=self.user_query), self.parse_user)

            if "paging" in results.keys() and results.get("paging").get("is_end") == False:
                next_page = results.get("paging").get("next")
                yield Request(next_page, self.parse_followers)