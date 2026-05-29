import re
import time
import json
import os
import asyncio
import httpx
from datetime import datetime
from typing import Callable, Optional

class TwitterDownloader:
    def __init__(self, user_id: str, download_path: str, 
                 proxy: str = "http://127.0.0.1:7890",
                 cookie: str = "auth_token=57e0355a3d8af03456b2363bc2e2414bd196ec3d; ct0=c5b52759848ec617418a1f8efd3ed113ceac195f8f6d4007bce0385b0b3f6abd342a12c9e77a4532ed056fb637d982328f96f2d2058b35214eff48b1806d9e151f266998a83a99a8e2a89554e9141aca",
                 progress_callback: Optional[Callable] = None):
        self.user_id = user_id
        self.download_path = download_path
        self.proxy = proxy
        self.cookie = cookie
        self.progress_callback = progress_callback
        
        self.user_info = {
            'screen_name': user_id,
            'rest_id': None,
            'name': None,
            'statuses_count': None,
            'media_count': None,
            'save_path': download_path,
            'cursor': None,
            'count': 0
        }
        
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
            'cookie': self.cookie
        }
        
        # 从cookie中提取csrf token
        re_token = r'ct0=([a-f0-9]+)'
        match = re.search(re_token, self.cookie)
        if match:
            self.headers['x-csrf-token'] = match.group(1)
        
        self.headers['referer'] = f'https://twitter.com/{self.user_id}'
        
        self.request_count = 0
        self.down_count = 0
        self.total_files = 0
        self.downloaded_files = 0
        
        # 下载配置
        self.has_retweet = False
        self.has_highlights = False
        self.has_likes = False
        self.has_video = True
        self.start_time_stamp = 655028357000  # 1990-10-04
        self.end_time_stamp = 2548484357000   # 2050-10-04
        self.start_label = True
        self.First_Page = True
        self.max_concurrent_requests = 8
        self.img_format = 'orig'
        self.orig_format = True
        
        # 处理代理配置
        self._proxy = proxy if proxy and proxy.strip() else None
    
    def _get_client(self) -> httpx.AsyncClient:
        """创建httpx客户端，支持可选代理"""
        if self._proxy:
            return httpx.AsyncClient(proxy=self._proxy)
        return httpx.AsyncClient()
    
    def quote_url(self, url: str) -> str:
        return url.replace('{', '%7B').replace('}', '%7D')
    
    def stamp2time(self, msecs_stamp: int) -> str:
        timeArray = time.localtime(msecs_stamp / 1000)
        return time.strftime("%Y-%m-%d %H-%M", timeArray)
    
    def time2stamp(self, timestr: str) -> int:
        datetime_obj = datetime.strptime(timestr, "%Y-%m-%d")
        return int(time.mktime(datetime_obj.timetuple()) * 1000.0 + datetime_obj.microsecond / 1000.0)
    
    def time_comparison(self, now: int, start: int, end: int):
        start_label = True
        start_down = False
        if now >= start and now <= end:
            start_down = True
        elif now < start:
            start_label = False
        return [start_down, start_label]
    
    async def get_other_info(self):
        url = f'https://twitter.com/i/api/graphql/xc8f1g7BYqr6VTzTbvNlGw/UserByScreenName?variables={{"screen_name":"{self.user_info["screen_name"]}","withSafetyModeUserFields":false}}&features={{"hidden_profile_likes_enabled":false,"hidden_profile_subscriptions_enabled":false,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"subscriptions_verification_info_verified_since_enabled":true,"highlights_tweets_tab_ui_enabled":true,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"responsive_web_graphql_timeline_navigation_enabled":true}}&fieldToggles={{"withAuxiliaryUserLabels":false}}'
        
        try:
            async with self._get_client() as client:
                response = await client.get(self.quote_url(url), headers=self.headers, timeout=30.0)
                self.request_count += 1
                
                if response.status_code != 200:
                    print(f'请求失败，状态码: {response.status_code}')
                    print(f'响应内容: {response.text[:500]}')
                    return False
                
                raw_data = response.json()
                
                # 检查是否有错误
                if 'errors' in raw_data:
                    print(f'API返回错误: {raw_data["errors"]}')
                    return False
                
                if 'data' not in raw_data:
                    print(f'响应中没有data字段，响应内容: {str(raw_data)[:500]}')
                    return False
                
                # 打印响应结构以便调试
                print(f'API响应: {json.dumps(raw_data, indent=2)[:1000]}')
                
                user_result = raw_data['data']['user']['result']
                print(f'user_result keys: {user_result.keys()}')
                
                self.user_info['rest_id'] = user_result.get('rest_id') or user_result.get('id')
                self.user_info['name'] = user_result.get('legacy', {}).get('name')
                self.user_info['statuses_count'] = user_result.get('legacy', {}).get('statuses_count')
                self.user_info['media_count'] = user_result.get('legacy', {}).get('media_count')
                
                # 更新总文件数（估算）
                self.total_files = min(self.user_info['media_count'] or 100, 500)
                
                return True
        except Exception as e:
            print(f'获取用户信息失败: {e}')
            import traceback
            traceback.print_exc()
            return False
    
    def get_heighest_video_quality(self, variants) -> str:
        if len(variants) == 1:
            return variants[0]['url']
        
        max_bitrate = 0
        heighest_url = None
        for i in variants:
            if 'bitrate' in i:
                if int(i['bitrate']) > max_bitrate:
                    max_bitrate = int(i['bitrate'])
                    heighest_url = i['url']
        return heighest_url
    
    def get_url_from_content(self, content):
        photo_lst = []
        x_label = 'content' if (self.has_retweet or self.has_highlights) else 'item'
        
        for i in content:
            try:
                if 'promoted-tweet' in i['entryId']:
                    continue
                if 'tweet' in i['entryId']:
                    if 'tweet' in i[x_label]['itemContent']['tweet_results']['result']:
                        a = i[x_label]['itemContent']['tweet_results']['result']['tweet']['legacy']
                        tweet_msecs = int(i[x_label]['itemContent']['tweet_results']['result']['tweet']['edit_control']['editable_until_msecs']) - 3600000
                    else:
                        a = i[x_label]['itemContent']['tweet_results']['result']['legacy']
                        tweet_msecs = int(i[x_label]['itemContent']['tweet_results']['result']['edit_control']['editable_until_msecs']) - 3600000
                    
                    timestr = self.stamp2time(tweet_msecs)
                    result = self.time_comparison(tweet_msecs, self.start_time_stamp, self.end_time_stamp)
                    
                    if result[0]:
                        if 'retweeted_status_result' not in a:
                            name = self.user_info['name']
                            screen_name = self.user_info['screen_name']
                            if 'extended_entities' in a:
                                for _media in a['extended_entities']['media']:
                                    if 'video_info' in _media and self.has_video:
                                        url = self.get_heighest_video_quality(_media['video_info']['variants'])
                                        photo_lst.append((url, f'{timestr}-vid', [tweet_msecs, name, f'@{screen_name}', _media['expanded_url'], 'Video', url, '', a['full_text']]))
                                    else:
                                        url = _media['media_url_https']
                                        photo_lst.append((url, f'{timestr}-img', [tweet_msecs, name, f'@{screen_name}', _media['expanded_url'], 'Image', url, '', a['full_text']]))
                        elif self.has_retweet:
                            name = a['retweeted_status_result']['result']['core']['user_results']['result']['legacy']['name']
                            screen_name = a['retweeted_status_result']['result']['core']['user_results']['result']['legacy']['screen_name']
                            full_text = a['retweeted_status_result']['result']['legacy']['full_text']
                            
                            if 'extended_entities' in a['retweeted_status_result']['result']['legacy'] and screen_name != self.user_info['screen_name']:
                                for _media in a['retweeted_status_result']['result']['legacy']['extended_entities']['media']:
                                    if 'video_info' in _media and self.has_video:
                                        url = self.get_heighest_video_quality(_media['video_info']['variants'])
                                        photo_lst.append((url, f'{timestr}-vid-retweet', [tweet_msecs, name, f"@{screen_name}", _media['expanded_url'], 'Video', url, '', full_text]))
                                    else:
                                        url = _media['media_url_https']
                                        photo_lst.append((url, f'{timestr}-img-retweet', [tweet_msecs, name, f"@{screen_name}", _media['expanded_url'], 'Image', url, '', full_text]))
                    elif not result[1]:
                        self.start_label = False
                        break
                
                elif 'profile-conversation' in i['entryId']:
                    if 'tweet' in i[x_label]['items'][0]['item']['itemContent']['tweet_results']['result']:
                        a = i[x_label]['items'][0]['item']['itemContent']['tweet_results']['result']['tweet']['legacy']
                        tweet_msecs = int(i[x_label]['items'][0]['item']['itemContent']['tweet_results']['result']['tweet']['edit_control']['editable_until_msecs']) - 3600000
                    else:
                        a = i[x_label]['items'][0]['item']['itemContent']['tweet_results']['result']['legacy']
                        tweet_msecs = int(i[x_label]['items'][0]['item']['itemContent']['tweet_results']['result']['edit_control']['editable_until_msecs']) - 3600000
                    
                    timestr = self.stamp2time(tweet_msecs)
                    result = self.time_comparison(tweet_msecs, self.start_time_stamp, self.end_time_stamp)
                    
                    if result[0]:
                        if 'extended_entities' in a:
                            for _media in a['extended_entities']['media']:
                                if 'video_info' in _media and self.has_video:
                                    url = self.get_heighest_video_quality(_media['video_info']['variants'])
                                    photo_lst.append((url, f'{timestr}-vid', [tweet_msecs, self.user_info['name'], f'@{self.user_info["screen_name"]}', _media['expanded_url'], 'Video', url, '', a['full_text']]))
                                else:
                                    url = _media['media_url_https']
                                    photo_lst.append((url, f'{timestr}-img', [tweet_msecs, self.user_info['name'], f'@{self.user_info["screen_name"]}', _media['expanded_url'], 'Image', url, '', a['full_text']]))
                    elif not result[1]:
                        self.start_label = False
                        break
            
            except Exception as e:
                continue
            
            if 'cursor-bottom' in i['entryId']:
                self.user_info['cursor'] = i['content']['value']
        
        return photo_lst
    
    async def get_download_url(self):
        if self.has_highlights:
            url_top = f'https://twitter.com/i/api/graphql/w9-i9VNm_92GYFaiyGT1NA/UserHighlightsTweets?variables={{"userId":"{self.user_info["rest_id"]}","count":20,'
            url_bottom = '"includePromotedContent":true,"withVoice":true}&features={"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"c9s_tweet_anatomy_moderator_badge_enabled":true,"tweetypie_unmention_optimization_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":false,"tweet_awards_web_tipping_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"rweb_video_timestamps_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_media_download_video_enabled":false,"responsive_web_enhance_cards_enabled":false}'
        elif self.has_likes:
            url_top = f'https://twitter.com/i/api/graphql/-fbTO1rKPa3nO6-XIRgEFQ/Likes?variables={{"userId":"{self.user_info["rest_id"]}","count":200,'
            url_bottom = '"includePromotedContent":false,"withClientEventToken":false,"withBirdwatchNotes":false,"withVoice":true,"withV2Timeline":true}&features={"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"c9s_tweet_anatomy_moderator_badge_enabled":true,"tweetypie_unmention_optimization_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":false,"tweet_awards_web_tipping_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"rweb_video_timestamps_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_media_download_video_enabled":false,"responsive_web_enhance_cards_enabled":false}'
        elif self.has_retweet:
            url_top = f'https://twitter.com/i/api/graphql/2GIWTr7XwadIixZDtyXd4A/UserTweets?variables={{"userId":"{self.user_info["rest_id"]}","count":20,'
            url_bottom = '"includePromotedContent":false,"withQuickPromoteEligibilityTweetFields":true,"withVoice":true,"withV2Timeline":true}&features={"rweb_lists_timeline_redesign_enabled":true,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"tweetypie_unmention_optimization_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":false,"tweet_awards_web_tipping_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_media_download_video_enabled":false,"responsive_web_enhance_cards_enabled":false}&fieldToggles={"withAuxiliaryUserLabels":false,"withArticleRichContentState":false}'
        else:
            url_top = f'https://twitter.com/i/api/graphql/Le6KlbilFmSu-5VltFND-Q/UserMedia?variables={{"userId":"{self.user_info["rest_id"]}","count":500,'
            url_bottom = '"includePromotedContent":false,"withClientEventToken":false,"withBirdwatchNotes":false,"withVoice":true,"withV2Timeline":true}&features={"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"tweetypie_unmention_optimization_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":false,"tweet_awards_web_tipping_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_media_download_video_enabled":false,"responsive_web_enhance_cards_enabled":false}'
        
        if self.user_info['cursor']:
            url = url_top + f'"cursor":"{self.user_info["cursor"]}",' + url_bottom
        else:
            url = url_top + url_bottom
        
        try:
            async with self._get_client() as client:
                response = await client.get(self.quote_url(url), headers=self.headers, timeout=30.0)
                self.request_count += 1
                
                try:
                    raw_data = response.json()
                except Exception:
                    if 'Rate limit exceeded' in response.text:
                        print('API次数已超限')
                    else:
                        print('获取数据失败')
                    return None
                
                if self.has_highlights:
                    raw_data = raw_data['data']['user']['result']['timeline']['timeline']['instructions'][-1]['entries']
                elif self.has_retweet:
                    raw_data = raw_data['data']['user']['result']['timeline_v2']['timeline']['instructions'][-1]['entries']
                else:
                    raw_data = raw_data['data']['user']['result']['timeline_v2']['timeline']['instructions']
                
                if (self.has_retweet or self.has_highlights) and 'cursor-top' in raw_data[0]['entryId']:
                    return False
                
                if not self.has_retweet and not self.has_highlights:
                    for i in raw_data[-1]['entries']:
                        if 'bottom' in i['entryId']:
                            self.user_info['cursor'] = i['content']['value']
                
                if self.start_label:
                    if not self.has_retweet and not self.has_highlights:
                        if self.First_Page:
                            raw_data = raw_data[-1]['entries'][0]['content']['items']
                            self.First_Page = False
                        else:
                            if 'moduleItems' not in raw_data[0]:
                                return False
                            else:
                                raw_data = raw_data[0]['moduleItems']
                    
                    photo_lst = self.get_url_from_content(raw_data)
                else:
                    return False
                
                if not photo_lst:
                    photo_lst.append(True)
        
        except Exception as e:
            print(f'获取推文信息错误: {e}')
            return False
        
        return photo_lst
    
    async def download_file(self, url: str, prefix: str, csv_info: list, order: int):
        if '.mp4' in url:
            file_name = f'{self.user_info["save_path"]}/{prefix}_{self.user_info["count"] + order}.mp4'
        else:
            try:
                if self.orig_format:
                    url += '?name=orig'
                    file_name = f'{self.user_info["save_path"]}/{prefix}_{self.user_info["count"] + order}.{csv_info[5][-3:]}'
                else:
                    file_name = f'{self.user_info["save_path"]}/{prefix}_{self.user_info["count"] + order}.{self.img_format}'
                    if self.img_format != 'png':
                        url += '?format=jpg&name=4096x4096'
                    else:
                        url += '?format=png&name=4096x4096'
            except Exception as e:
                print(url)
                return False
        
        count = 0
        while True:
            try:
                async with self._get_client() as client:
                    response = await client.get(self.quote_url(url), timeout=(3.05, 16))
                    if response.status_code == 404:
                        raise Exception('404')
                    self.down_count += 1
                    self.downloaded_files += 1
                    
                    # 更新进度
                    if self.progress_callback:
                        progress = min(int((self.downloaded_files / max(self.total_files, 1)) * 100), 100)
                        self.progress_callback(progress, self.downloaded_files, self.total_files)
                
                with open(file_name, 'wb') as f:
                    f.write(response.content)
                
                break
            except Exception as e:
                if '.mp4' in url or self.orig_format or str(e) != "404":
                    count += 1
                    if count >= 50:
                        print(f'{file_name}=====>第{count}次下载失败，已跳过该文件。')
                        break
                    print(f'{file_name}=====>第{count}次下载失败,正在重试')
                else:
                    url = url.replace('name=orig', 'name=4096x4096')
    
    async def download_control(self):
        while True:
            photo_lst = await self.get_download_url()
            if not photo_lst:
                break
            elif photo_lst[0] == True:
                continue
            
            semaphore = asyncio.Semaphore(self.max_concurrent_requests)
            
            tasks = []
            for order, url in enumerate(photo_lst):
                task = self.download_file(url[0], url[1], url[2], order)
                tasks.append(task)
            
            await asyncio.gather(*tasks)
            self.user_info['count'] += len(photo_lst)
    
    async def start_download(self):
        """开始下载任务"""
        # 创建下载目录
        os.makedirs(self.download_path, exist_ok=True)
        
        # 获取用户信息
        if not await self.get_other_info():
            raise Exception('获取用户信息失败')
        
        # 开始下载
        await self.download_control()
        
        return {
            'user_name': self.user_info['name'],
            'media_count': self.user_info['media_count'],
            'downloaded_files': self.downloaded_files,
            'request_count': self.request_count
        }