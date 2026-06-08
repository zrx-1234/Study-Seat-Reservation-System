"""
Gunicorn 生产配置
"""
import multiprocessing
import os

bind = '0.0.0.0:5000'
workers = int(os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'sync'
worker_connections = 1000
timeout = 60
keepalive = 5

# 日志
accesslog = '-'  # stdout
errorlog = '-'   # stderr
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)s'

# 重启策略
max_requests = 1000
max_requests_jitter = 100

# 进程名
proc_name = 'study-seat-backend'
