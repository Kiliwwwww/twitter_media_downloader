import re
import time
import json
import os
import asyncio
import httpx
from datetime import datetime
from typing import Callable, Optional

from logger import DownloadLogger


class TwitterDownloader:
    def __init__(self, user_id: str, download_path: str, 
                 proxy: str = "",
                 cookie: str = "",
                 task_id: str = None,
                 progress_callback: Optional[Callable] = None,
                 skip_existing: bool = True,
                 max_retries: int = 50):
        self.user_id = user_id
        self.download_path = download_path
        self.proxy = proxy
        self.cookie = cookie
        self.task_id = task_id
        self.progress_callback = progress_callback
        self.skip_existing = skip_existing
        self.max_retries = max_retries
        
        # 初始化日志器
        self.logger = DownloadLogger(task_id or 'unknown', user_id) if task_id else None
        self._log_manager = None
        
        self.user_info = {
            'screen_name': user_id,
            'rest_id': None,
            'name': None,
            'avatar_url': None,
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
        self.tweets_info = []  # 收集帖子信息，用于导出xlsx
        self.down_count = 0
        self.total_files = 0
        self.downloaded_files = 0
        self.skipped_files = 0
        self.failed_files = 0
        
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
    
    def set_log_manager(self, log_manager):
        """设置实时日志管理器"""
        self._log_manager = log_manager
    
    def _log(self, level: str, message: str, category: str = ''):
        """记录日志（同时写入文件和实时推送）"""
        # 写入文件日志
        if self.logger:
            getattr(self.logger, level, self.logger.info)(message)
        
        # 实时推送
        if self._log_manager and self.task_id:
            getattr(self._log_manager, level, self._log_manager.info)(
                self.task_id, self.user_id, message, category
            )
    
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
    
    def _file_exists(self, file_path: str) -> bool:
        """检查文件是否已存在且大小大于0"""
        if not self.skip_existing:
            return False
        return os.path.exists(file_path) and os.path.getsize(file_path) > 0
    
    @staticmethod
    def _format_size(size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f'{size:.1f} {unit}'
            size /= 1024
        return f'{size:.1f} TB'
    
    async def get_other_info(self):
        url = f'https://twitter.com/i/api/graphql/xc8f1g7BYqr6VTzTbvNlGw/UserByScreenName?variables={{"screen_name":"{self.user_info["screen_name"]}","withSafetyModeUserFields":false}}&features={{"hidden_profile_likes_enabled":false,"hidden_profile_subscriptions_enabled":false,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"subscriptions_verification_info_verified_since_enabled":true,"highlights_tweets_tab_ui_enabled":true,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"responsive_web_graphql_timeline_navigation_enabled":true}}&fieldToggles={{"withAuxiliaryUserLabels":false}}'
        
        try:
            async with self._get_client() as client:
                response = await client.get(self.quote_url(url), headers=self.headers, timeout=30.0)
                self.request_count += 1
                
                if response.status_code != 200:
                    error_msg = f'HTTP {response.status_code}'
                    try:
                        error_data = response.json()
                        if 'errors' in error_data:
                            error_msg += f': {error_data["errors"][0].get("message", "")}'
                    except:
                        pass
                    raise Exception(error_msg)
                
                raw_data = response.json()
                
                # 检查是否有错误
                if 'errors' in raw_data:
                    error_msg = raw_data['errors'][0].get('message', 'Unknown error')
                    error_code = raw_data['errors'][0].get('code', '')
                    raise Exception(f'API Error {error_code}: {error_msg}')
                
                if 'data' not in raw_data:
                    raise Exception('响应中没有data字段')
                
                user_result = raw_data['data']['user']['result']
                
                self.user_info['rest_id'] = user_result.get('rest_id') or user_result.get('id')
                self.user_info['name'] = user_result.get('legacy', {}).get('name')
                # 将头像URL替换为高清版本 _400x400
                avatar_url = user_result.get('legacy', {}).get('profile_image_url_https')
                if avatar_url:
                    avatar_url = avatar_url.replace('_normal', '_400x400')
                self.user_info['avatar_url'] = avatar_url
                self.user_info['statuses_count'] = user_result.get('legacy', {}).get('statuses_count')
                self.user_info['media_count'] = user_result.get('legacy', {}).get('media_count')
                
                # 更新总文件数（估算）
                self.total_files = min(self.user_info['media_count'] or 100, 500)
                
                self._log('info', f'获取用户信息成功: {self.user_info["name"]} (@{self.user_info["screen_name"]})', 'system')
                self._log('info', f'媒体数量: {self.user_info["media_count"]}', 'system')
                
                return True
        except Exception as e:
            self._log('error', f'获取用户信息失败: {e}', 'system')
            print(f'获取用户信息失败: {e}')
            raise
    
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
                        tweet_result = i[x_label]['itemContent']['tweet_results']['result']['tweet']
                        a = tweet_result['legacy']
                        tweet_msecs = int(tweet_result['edit_control']['editable_until_msecs']) - 3600000
                        tweet_id = tweet_result.get('rest_id', '')
                    else:
                        tweet_result = i[x_label]['itemContent']['tweet_results']['result']
                        a = tweet_result['legacy']
                        tweet_msecs = int(tweet_result['edit_control']['editable_until_msecs']) - 3600000
                        tweet_id = tweet_result.get('rest_id', '')
                    
                    timestr = self.stamp2time(tweet_msecs)
                    date_str = time.strftime("%Y-%m-%d", time.localtime(tweet_msecs / 1000))
                    result = self.time_comparison(tweet_msecs, self.start_time_stamp, self.end_time_stamp)
                    
                    if result[0]:
                        if 'retweeted_status_result' not in a:
                            name = self.user_info['name']
                            screen_name = self.user_info['screen_name']
                            if 'extended_entities' in a:
                                media_list = a['extended_entities']['media']
                                for idx, _media in enumerate(media_list):
                                    if 'video_info' in _media and self.has_video:
                                        url = self.get_heighest_video_quality(_media['video_info']['variants'])
                                        photo_lst.append((url, date_str, tweet_id, idx, len(media_list), [tweet_msecs, name, f'@{screen_name}', _media['expanded_url'], 'Video', url, '', a['full_text']]))
                                        self.tweets_info.append({'time': timestr, 'name': name, 'screen_name': f'@{screen_name}', 'text': a['full_text'], 'type': 'Video', 'media_url': _media['expanded_url'], 'download_url': url})
                                    else:
                                        url = _media['media_url_https']
                                        photo_lst.append((url, date_str, tweet_id, idx, len(media_list), [tweet_msecs, name, f'@{screen_name}', _media['expanded_url'], 'Image', url, '', a['full_text']]))
                                        self.tweets_info.append({'time': timestr, 'name': name, 'screen_name': f'@{screen_name}', 'text': a['full_text'], 'type': 'Image', 'media_url': _media['expanded_url'], 'download_url': url})
                        elif self.has_retweet:
                            name = a['retweeted_status_result']['result']['core']['user_results']['result']['legacy']['name']
                            screen_name = a['retweeted_status_result']['result']['core']['user_results']['result']['legacy']['screen_name']
                            full_text = a['retweeted_status_result']['result']['legacy']['full_text']
                            
                            if 'extended_entities' in a['retweeted_status_result']['result']['legacy'] and screen_name != self.user_info['screen_name']:
                                media_list = a['retweeted_status_result']['result']['legacy']['extended_entities']['media']
                                for idx, _media in enumerate(media_list):
                                    if 'video_info' in _media and self.has_video:
                                        url = self.get_heighest_video_quality(_media['video_info']['variants'])
                                        photo_lst.append((url, date_str, tweet_id, idx, len(media_list), [tweet_msecs, name, f"@{screen_name}", _media['expanded_url'], 'Video', url, '', full_text]))
                                        self.tweets_info.append({'time': timestr, 'name': name, 'screen_name': f'@{screen_name}', 'text': full_text, 'type': 'Video', 'media_url': _media['expanded_url'], 'download_url': url})
                                    else:
                                        url = _media['media_url_https']
                                        photo_lst.append((url, date_str, tweet_id, idx, len(media_list), [tweet_msecs, name, f"@{screen_name}", _media['expanded_url'], 'Image', url, '', full_text]))
                                        self.tweets_info.append({'time': timestr, 'name': name, 'screen_name': f'@{screen_name}', 'text': full_text, 'type': 'Image', 'media_url': _media['expanded_url'], 'download_url': url})
                    elif not result[1]:
                        self.start_label = False
                        break
                
                elif 'profile-conversation' in i['entryId']:
                    if 'tweet' in i[x_label]['items'][0]['item']['itemContent']['tweet_results']['result']:
                        tweet_result = i[x_label]['items'][0]['item']['itemContent']['tweet_results']['result']['tweet']
                        a = tweet_result['legacy']
                        tweet_msecs = int(tweet_result['edit_control']['editable_until_msecs']) - 3600000
                        tweet_id = tweet_result.get('rest_id', '')
                    else:
                        tweet_result = i[x_label]['items'][0]['item']['itemContent']['tweet_results']['result']
                        a = tweet_result['legacy']
                        tweet_msecs = int(tweet_result['edit_control']['editable_until_msecs']) - 3600000
                        tweet_id = tweet_result.get('rest_id', '')
                    
                    timestr = self.stamp2time(tweet_msecs)
                    date_str = time.strftime("%Y-%m-%d", time.localtime(tweet_msecs / 1000))
                    result = self.time_comparison(tweet_msecs, self.start_time_stamp, self.end_time_stamp)
                    
                    if result[0]:
                        if 'extended_entities' in a:
                            media_list = a['extended_entities']['media']
                            for idx, _media in enumerate(media_list):
                                if 'video_info' in _media and self.has_video:
                                    url = self.get_heighest_video_quality(_media['video_info']['variants'])
                                    photo_lst.append((url, date_str, tweet_id, idx, len(media_list), [tweet_msecs, self.user_info['name'], f'@{self.user_info["screen_name"]}', _media['expanded_url'], 'Video', url, '', a['full_text']]))
                                    self.tweets_info.append({'time': timestr, 'name': self.user_info['name'], 'screen_name': f'@{self.user_info["screen_name"]}', 'text': a['full_text'], 'type': 'Video', 'media_url': _media['expanded_url'], 'download_url': url})
                                else:
                                    url = _media['media_url_https']
                                    photo_lst.append((url, date_str, tweet_id, idx, len(media_list), [tweet_msecs, self.user_info['name'], f'@{self.user_info["screen_name"]}', _media['expanded_url'], 'Image', url, '', a['full_text']]))
                                    self.tweets_info.append({'time': timestr, 'name': self.user_info['name'], 'screen_name': f'@{self.user_info["screen_name"]}', 'text': a['full_text'], 'type': 'Image', 'media_url': _media['expanded_url'], 'download_url': url})
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
            url_bottom = '"includePromotedContent":false,"withQuickPromoteEligibilityTweetFields":true,"withVoice":true,"withV2Timeline":true}&features={"rweb_lists_timeline_redesign_enabled":true,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"tweetypie_unmention_optimization_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":false,"tweet_awards_web_tipping_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"rweb_video_timestamps_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_media_download_video_enabled":false,"responsive_web_enhance_cards_enabled":false}&fieldToggles={"withAuxiliaryUserLabels":false,"withArticleRichContentState":false}'
        else:
            url_top = f'https://twitter.com/i/api/graphql/Le6KlbilFmSu-5VltFND-Q/UserMedia?variables={{"userId":"{self.user_info["rest_id"]}","count":500,'
            url_bottom = '"includePromotedContent":false,"withClientEventToken":false,"withBirdwatchNotes":false,"withVoice":true,"withV2Timeline":true}&features={"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"tweetypie_unmention_optimization_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":false,"tweet_awards_web_tipping_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"rweb_video_timestamps_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_media_download_video_enabled":false,"responsive_web_enhance_cards_enabled":false}'
        
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
                        if self.logger:
                            self.logger.error('API次数已超限')
                        print('API次数已超限')
                    else:
                        if self.logger:
                            self.logger.error('获取数据失败')
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
            if self.logger:
                self.logger.error(f'获取推文信息错误: {e}')
            print(f'获取推文信息错误: {e}')
            return False
        
        return photo_lst
    
    async def download_file(self, url: str, date_str: str, tweet_id: str, media_index: int, media_count: int, csv_info: list, order: int):
        # 获取文件扩展名
        if '.mp4' in url:
            ext = 'mp4'
        else:
            try:
                if self.orig_format:
                    ext = csv_info[5][-3:]
                else:
                    ext = self.img_format
            except Exception as e:
                print(url)
                return False
        
        # 构建文件名
        if media_count == 1:
            # 单个文件：{date}_{tweet_id}.ext
            file_name = f'{self.user_info["save_path"]}/{date_str}_{tweet_id}.{ext}'
        else:
            # 多个文件：{date}_{tweet_id}_{index+1}.ext
            file_name = f'{self.user_info["save_path"]}/{date_str}_{tweet_id}_{media_index + 1}.{ext}'
        
        # 检查文件是否已存在
        if self._file_exists(file_name):
            self.skipped_files += 1
            self._log('info', f'[跳过] 文件已存在: {os.path.basename(file_name)}', 'download')
            # 更新进度
            if self.progress_callback:
                progress = min(int(((self.downloaded_files + self.skipped_files) / max(self.total_files, 1)) * 100), 100)
                self.progress_callback(progress, self.downloaded_files, self.total_files, self.skipped_files)
            return True
        
        # 处理URL
        if '.mp4' not in url and self.orig_format:
            url += '?name=orig'
        
        count = 0
        while True:
            try:
                async with self._get_client() as client:
                    response = await client.get(self.quote_url(url), timeout=(3.05, 16))
                    if response.status_code == 404:
                        raise Exception('404')
                    self.down_count += 1
                    self.downloaded_files += 1
                    
                    # 记录下载成功
                    file_size = len(response.content)
                    size_str = self._format_size(file_size)
                    self._log('success', f'[下载成功] {os.path.basename(file_name)} ({size_str})', 'download')
                    
                    # 更新进度
                    if self.progress_callback:
                        progress = min(int(((self.downloaded_files + self.skipped_files) / max(self.total_files, 1)) * 100), 100)
                        self.progress_callback(progress, self.downloaded_files, self.total_files, self.skipped_files)
                
                with open(file_name, 'wb') as f:
                    f.write(response.content)
                
                break
            except Exception as e:
                if '.mp4' in url or self.orig_format or str(e) != "404":
                    count += 1
                    if count >= self.max_retries:
                        self.failed_files += 1
                        self._log('error', f'[下载失败] {os.path.basename(file_name)} - 错误: {e} (已重试{count}次)', 'download')
                        break
                    self._log('warning', f'[重试] {os.path.basename(file_name)} - 第{count}/{self.max_retries}次重试', 'download')
                else:
                    url = url.replace('name=orig', 'name=4096x4096')
    
    async def download_control(self):
        page_count = 0
        while True:
            photo_lst = await self.get_download_url()
            if not photo_lst:
                break
            elif photo_lst[0] == True:
                continue
            
            page_count += 1
            self._log('info', f'开始处理第 {page_count} 页，包含 {len(photo_lst)} 个媒体文件', 'system')
            
            semaphore = asyncio.Semaphore(self.max_concurrent_requests)
            
            tasks = []
            for order, item in enumerate(photo_lst):
                # item = (url, date_str, tweet_id, media_index, media_count, csv_info)
                task = self.download_file(item[0], item[1], item[2], item[3], item[4], item[5], order)
                tasks.append(task)
            
            await asyncio.gather(*tasks)
            self.user_info['count'] += len(photo_lst)
            
            # 记录进度
            if self.logger:
                self.logger.log_progress(self.downloaded_files, self.downloaded_files + self.skipped_files + self.failed_files, self.skipped_files)
    
    async def start_download(self):
        """开始下载任务"""
        start_time = time.time()
        
        # 创建下载目录
        os.makedirs(self.download_path, exist_ok=True)
        
        self._log('info', f'下载目录: {self.download_path}', 'system')
        
        # 获取用户信息
        if not await self.get_other_info():
            raise Exception('获取用户信息失败')
        
        # 开始下载
        await self.download_control()
        
        # 计算总耗时
        total_time = time.time() - start_time
        
        # 记录任务完成
        self._log('info', f'下载完成 - 成功: {self.downloaded_files}, 失败: {self.failed_files}, 跳过: {self.skipped_files}, 耗时: {total_time:.1f}秒', 'system')
        
        return {
            'user_name': self.user_info['name'],
            'avatar_url': self.user_info['avatar_url'],
            'media_count': self.user_info['media_count'],
            'downloaded_files': self.downloaded_files,
            'skipped_files': self.skipped_files,
            'failed_files': self.failed_files,
            'request_count': self.request_count,
            'total_time': total_time,
            'tweets_info': self.tweets_info
        }
