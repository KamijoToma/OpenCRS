#!/usr/bin/env python3

# OpenCRS(CRSPlus core v0.5.1)
import requests
import os
import sys
import time
import traceback
from queue import Queue
from enum import Enum
import threading
import asyncio
import m3u8
import json
import logging

LOG_FILE_NAME = time.strftime('CRSPlus_%Y_%m_%dAT%Hh%Mm%Ss_Log.log', time.localtime())

class TaskTypeEnum(Enum):
    DOWNLOAD_TS = 0
    DOWNLOAD_M3U8 = 1
    pass

class Task:
    def __init__(self,):
        self.task_type = None
        pass

    def task_type(self, target=None):
        if target == None:
            return self.task_type
        else:
            return self.task_type == target

    async def run(self,) -> bool:
        pass

    def __str__(self,) -> str:
        return 'BaseTask Object'
    pass

class DownloadTSFileTask(Task):
    def __init__(self, ts_url: str, target_dir:str, ctx, file_name='', callback=None, logger=None):
        super().__init__()
        self.ts_url = ts_url
        self.dir = target_dir
        self.ctx = ctx
        self.done = False
        self.task_type = TaskTypeEnum.DOWNLOAD_TS
        self.file_name = file_name
        self.callback = callback if not callback == None else lambda status:None
        self.LOG = logger if not logger == None else lambda x,exec_info=False:None
        pass

    async def run(self,) -> bool:
        # Download the ts file
        done = download_single(self.ts_url, stream=True, path=self.dir, file_name=self.file_name)
        self.done = done
        try:
            self.callback(done)
        except:
            self.LOG.error(f'Error when call the callback of the url {self.ts_url}. Stack Trace:', exc_info=True)
            pass
        self.ctx.DATABASE.append(self.ts_url)
        return done

    def __str__(self,) -> str:
        return "TSFileDownloadTask URL["+self.ts_url+f"] STATUS={'Done' if self.done else 'Pending'}"
    pass

class DumpM3U8FileTask(Task):
    def __init__(self, ctx, callback=lambda status:False):
        self.ctx = ctx
        self.callback = callback
        pass

    async def run(self, ) -> bool:
        try:
            # Dump the m3u8 file first
            m3u8_file_path = os.path.join(self.ctx.TARGET_FOLDER, 'index.m3u8')
            with open(m3u8_file_path, 'w+') as fp:
                fp.write(self.ctx.M3U8_OBJECT.dumps())
                pass
            # Dump the debug info second
            debug_file_path = os.path.join(self.ctx.TARGET_FOLDER, 'debug.json')
            debug_message = {
                'ctx.target_url': self.ctx.TARGET_URL,
                'ctx.target_folder': self.ctx.TARGET_FOLDER,
                'ctx.ts_file_list': self.ctx.TS_FILE_DICT,
                'ctx.database:': self.ctx.DATABASE
                }
            json_message = json.dumps(debug_message)
            with open(debug_file_path, 'w+') as fp:
                fp.write(json_message)
                pass
            self.callback(True)
            return True
        except:
            print('Error when try to dump the m3u8 index file. Stack Trace:')
            traceback.print_exc()
            self.callback(False)
            return False

    def __str__(self,) -> str:
        return f'DumpM3U8FileTask with ctx.path={self.ctx.TARGET_FOLDER}'
    pass

##### Useful functions #####

def download_single(url, file_name = '', stream=False, path='./', try_time=5):
    if file_name == '' or file_name == None:
        file_name = url.split('/')[-1]
        pass
    if path == None:
        path = './'
        pass
    download_path = os.path.join(path, file_name)
    # Try to download
    for i in range(0, 5):
        try:
            fp = open(download_path, 'wb+')
            resp = requests.get(url, stream=stream)
            if not resp.status_code == 200:
                time.sleep(0.2)
                continue
            if stream:
                for chunk in resp.iter_content(chunk_size=102400):
                    fp.write(chunk)
                    pass
                pass
            else:
                fp.write(resp.content)
                pass
            return True
        except Exception as e:
            traceback.print_exc()
            time.sleep(0.2)
            pass
        finally:
            if fp in locals() or fp in globals():
                fp.close()
                os.remove(download_path)
                pass
            pass
        pass
    return False

def get_timestamp_from_ts_filename(filename:str) -> int:
    return int(filename.split('.')[0].split('-')[1])

def get_m3u8_ts_list(m3u8_url: str) -> {}:
    try:
        resp = requests.get(m3u8_url, timeout=1)
    except:
        traceback.print_exc()
        return {}
    m3u8_texts = resp.text.replace('\r', '').split('\n')
    ts_dict = {}
    # Remove the line which starts with '#'
    for text in m3u8_texts:
        if text.startswith('#'): continue
        if text == '': continue
        text = text.replace(' ', '')
        ts_dict[get_timestamp_from_ts_filename(text)] = text
        pass
    return ts_dict

def url_get_abs_path(url:str, https=False) -> str:
    # Disabled
    if url.startswith('http://') and not https: return url
    if url.startswith('https://') and https: return url
    pass

def get_start_stop_timestamp(timeStamp=int(time.time())):
    timeArray = time.localtime(timeStamp)
    otherStyleTime = time.strftime("%Y-%m-%d", timeArray)
    timeArray = time.strptime(otherStyleTime, "%Y-%m-%d")
    timeStamp = int(time.mktime(timeArray))
    return (timeStamp,timeStamp+86399)

'INFO(2016-10-09 19:11:19,434) file.py@211 mainLogger(Thread main) - Hello World'
logger_format = '%(levelname)s(%(asctime)s) %(filename)s@%(lineno)d %(name)s(%(threadName)s) - %(message)s'
def build_logger(name):
    global LOG_FILE_NAME
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(LOG_FILE_NAME, 'a+')
    fh.setLevel(logging.DEBUG)
    fh_formatter = logging.Formatter('%(levelname)s(%(asctime)s) %(filename)s@%(lineno)d %(name)s(%(threadName)s) - %(message)s')
    fh.setFormatter(fh_formatter)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch_formatter = logging.Formatter('%(levelname)s(%(asctime)s)%(name)s(%(threadName)s) - %(message)s')
    ch.setFormatter(ch_formatter)
    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger

##### Useful functions end #####

class Resource:
    TARGET_URL = ''
    TARGET_FOLDER = ''
    WORKERS_NUM = 5
    DATABASE = []
    TS_FILE_DICT = {}
    M3U8_OBJECT = m3u8.M3U8()
    DUMP_COUNT = 0
    pass

class Worker:
    def __init__(self, number:str):
        self.LOG = build_logger(f'Worker-{number}')
        self.number = number
        self.start = True
        pass

    def set_work_queue(self, queue):
        self.queue = queue
        pass

    def start_work(self):
        self.start = True
        pass

    def stop_work(self):
        self.start = False
        pass

    async def single_work(self, task) -> bool:
        '''
        print(type(task))
        if task.task_type(TaskTypeEnum.DOWNLOAD_TS):
            print(type(task))
            task.run()
            pass
        elif task.task_type(TaskTypeEnum.DOWNLOAD_M3U8):
            pass
        else:
            pass
            '''
        return await task.run()

    async def run(self,):
        while True:
            # Switch the running premission
            await asyncio.sleep(0.01)
            # Check if the FLAG of the self.start
            if not self.start:
                continue
            if self.queue.empty():
                continue
            task = self.queue.get(timeout=0.3)
            self.LOG.debug(f'[Worker {self.number}] Get a task [{str(task)}] from the queue.')
            done = await self.single_work(task)
            if done:
                self.queue.task_done()
                pass
            else:
                self.LOG.warning(f'Task {str(task)} unfinished. Please check the log file.')
                pass
        pass

class TaskManager(threading.Thread):
    def __init__(self, worker_number=5, ):
        super().__init__()
        self.setName('TaskManagerThread')
        self.LOG = build_logger('TaskManager')
        self.worker_number = worker_number
        self.queue = Queue(maxsize=50)
        # Set up workers
        self.workers = {}
        for i in range(0, worker_number):
            self.workers[i] = Worker(str(i))
            self.workers[i].set_work_queue(self.queue)
            pass
        # Setup event loop
        self.event_loop = asyncio.new_event_loop()
        pass

    def run(self,):
        # Make a event loop
        asyncio.set_event_loop(self.event_loop)
        task_list = []
        for i in self.workers.keys():
            self.workers[i].start_work()
            task_list.append(asyncio.ensure_future(self.workers[i].run()))
            pass
        self.LOG.info('TaskManager Worker Thread start to run.')
        self.event_loop.run_until_complete(asyncio.gather(*task_list))
        pass
    pass

class RecordLimitData:
    def __init__(self, start=0, stop=24*60*60):
        assert start >= 0 and type(start) == int
        assert stop >= 0 and type(stop) == int
        assert start < stop

        self.start = start
        self.stop = stop
        self.continued_time = stop - start
        pass

    def should_record(self, current_time=int(time.time())) -> bool:
        start_timestamp = get_start_stop_timestamp(current_time)[0]
        status = current_time in range(start_timestamp+self.start, start_timestamp+self.stop)
        #print('Status:', status, 'Range:', range(start_timestamp+self.start, start_timestamp+self.stop), 'from:', current_time)
        return status

    @staticmethod
    def mixed_up(limited_datas:list):
        pass
    pass

class M3U8Downloader(threading.Thread):
    def __init__(self, index_url: str, save_folder: str, ctx, time_per_video:int=18000, dump_time=60, folder_callback=None, limit_times=[ RecordLimitData(1, 24*60*60)]):
        super().__init__()
        self.setName('M3U8DownloaderThread')
        self.LOG = build_logger('M3U8Downloader')
        self.index_url = index_url
        self.save_folder = save_folder
        self.folder_name_callback = (lambda: 'test') if folder_callback == None else folder_callback
        self.ctx = ctx
        self.time_per_video = time_per_video
        self.task_manager = TaskManager()
        self.reset_recorder(first_start=True)
        self.last_dump_time = int(time.time())
        self.dump_time = dump_time
        self.limited_datas = limit_times 
        self.last_record_status = True
        self.record_status = False
        pass

    def single_loop(self,):
        time_now = int(time.time())
        # Check if should record live streams
        should_record = False
        for limited_data in self.limited_datas:
            if limited_data.should_record(time_now):
                should_record = True
                pass
            pass
        self.record_status = should_record
        if not should_record:
            # Block current thread and return.
            time.sleep(1)
            # Check if it is the first block
            if self.last_record_status == True:
                # Spawn a DumpM3U8Task to save the m3u8 file.
                self.LOG.debug('Record stop, dumping debug file...')
                task = DumpM3U8FileTask(self.ctx)
                self.task_manager.queue.put(task)
                self.last_record_status = False
                pass
            return
        self.last_record_status = True
        
        playlist = m3u8.load(self.index_url)
        save_folder = self.ctx.TARGET_FOLDER
        for segment in playlist.segments:
            timestamp = get_timestamp_from_ts_filename(segment.uri)
            if timestamp in ctx.TS_FILE_DICT.keys(): continue
            download_task = DownloadTSFileTask(segment.absolute_uri, save_folder, self.ctx, segment.uri)
            self.task_manager.queue.put(download_task)
            ctx.TS_FILE_DICT[timestamp] = segment.absolute_uri
            # Dump the segment into the m3u8 object
            segment.base_uri = ''
            self.ctx.M3U8_OBJECT.segments.append(segment)
            pass
        # Check time
        if time_now - self.start_time > self.time_per_video:
            # Reset video recorder
            self.LOG.info('Time reached, resetting recorder...')
            callback = lambda status:self.reset_recorder() if status else False
            task = DumpM3U8FileTask(self.ctx, callback)
            self.task_manager.queue.put(task)
            # Reset start_time
            self.start_time = self.start_time + 2
            pass
        if time_now - self.last_dump_time >= self.dump_time:
            self.LOG.debug('Auto dumping index file and debug info.')
            task = DumpM3U8FileTask(self.ctx)
            self.task_manager.queue.put(task)
            self.last_dump_time = time_now
            pass
        pass

    def reset_recorder(self, first_start=False):
        # Reset m3u8 object
        self.ctx.M3U8_OBJECT = m3u8.M3U8()
        self.ctx.M3U8_OBJECT.is_endlist = True
        self.ctx.M3U8_OBJECT.version = 3
        # Reset start time
        self.start_time = int(time.time())
        # Reset save folder
        self.ctx.TARGET_FOLDER = os.path.join(self.save_folder, self.folder_name_callback())
        # Create dir if not exists
        if not os.path.exists(self.ctx.TARGET_FOLDER):
            os.makedirs(self.ctx.TARGET_FOLDER)
            pass
        self.LOG.info('Recorder resetted.')
        pass

    def m3u8_index_dump(self,):
        selg.LOG.warning('Undumped')
        pass

    def run(self,):
        self.task_manager.start()
        while True:
            try:
                self.single_loop()
            except:
                self.LOG.error('Error found when looping single thread.', exc_info=True)
                pass
            pass
        pass
    pass


#### The test codes
ctx = Resource()
folder_callback = lambda: time.strftime('Record%Y_%m_%dAT%Hh%Mm%Ss_LiveStream', time.localtime())
downloader = M3U8Downloader('[PRIVATE]', 'LiveRecordData', ctx, dump_time=60, folder_callback=folder_callback)
downloader.start()
while True:
    time.sleep(0.5)
    pass

            
