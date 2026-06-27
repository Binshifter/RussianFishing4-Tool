import sys
import os
import tkinter as tk


class LogRedirector:
    '''将 stdout 重定向到 Tkinter Text 控件 + 本地日志文件 + 原控制台'''
    
    def __init__(self, text_widget):
        self.text_widget = text_widget
        # 保存原始标准输出（关键：用于回写到PyCharm控制台）
        self.old_stdout = sys.__stdout__
        
        current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.log_file = os.path.join(current_dir, 'rf4_fishing.log')
        log_dir = os.path.dirname(self.log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        self.buffer = []
        self.log_fp = open(self.log_file, 'a', encoding='utf-8', buffering=1)
    
    def write(self, s):
        # 1. 写入GUI文本框
        self.buffer.append(s)
        if len(self.buffer) > 1000:
            self.buffer.pop(0)
        self.text_widget.after(0, self._update_text, s)
        
        # 2. 写入日志文件
        self.log_fp.write(s)
        
        # 3. 同时输出到 PyCharm/系统控制台
        self.old_stdout.write(s)
    
    def _update_text(self, s):
        self.text_widget.insert(tk.END, s)
        self.text_widget.see(tk.END)
    
    def flush(self):
        self.log_fp.flush()
        self.old_stdout.flush()
    
    def close(self):
        if hasattr(self, 'log_fp') and not self.log_fp.closed:
            self.log_fp.close()