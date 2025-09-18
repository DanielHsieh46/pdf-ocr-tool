#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

# --- 設定依賴環境路徑 ---
try:
    base_dir = os.path.dirname(os.path.abspath(__file__))  # 正常 .py / .exe 情況
    icon_path = os.path.join(base_dir, "PDF_OCR.ico")
except NameError:
    base_dir = os.getcwd()  # 在 Jupyter / 互動環境下
    icon_path = "PDF_OCR.ico"
    
os.environ["PATH"] = (
    os.path.join(base_dir, "tesseract") + ";" +
    os.path.join(base_dir, "ghostscript") + ";" +
    os.path.join(base_dir, "pngquant") + ";" +
    os.environ["PATH"]
)

# 全域變數
current_process = None
is_stopping = False  # 用來標記是否使用者按了停止

def run_ocr():
    """選擇檔案並執行 OCR"""
    global current_process, is_stopping
    is_stopping = False

    # 選擇輸入 PDF
    input_path = filedialog.askopenfilename(
        title="Select a PDF to OCR",
        filetypes=[("PDF files", "*.pdf")]
    )
    if not input_path:
        return

    # 設定輸出檔案名稱
    default_name = os.path.splitext(os.path.basename(input_path))[0] + "_ocr.pdf"
    output_path = filedialog.asksaveasfilename(
        title="Save OCR Output As",
        defaultextension=".pdf",
        initialfile=default_name,
        filetypes=[("PDF files", "*.pdf")]
    )
    if not output_path:
        return

    # UI 狀態更新
    progress.start(10)
    status_label.config(text="⏳ Processing... Please wait")
    btn_start.config(state=DISABLED)
    btn_stop.config(state=NORMAL)

    def task():
        global current_process
        try:
            # 用 subprocess 執行 ocrmypdf
            cmd = [
                "ocrmypdf",
                "--language", "chi_tra+eng",
                "--rotate-pages",
                "--optimize", "3",
                "--output-type", "pdf",
                "--jobs", "8",
                input_path,
                output_path
            ]
            current_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = current_process.communicate()

            if current_process.returncode == 0 and not is_stopping:
                root.after(0, lambda: messagebox.showinfo(
                    "Success", f"OCR completed!\nSaved to:\n{output_path}"
                ))
            elif not is_stopping:
                root.after(0, lambda: messagebox.showerror(
                    "Error", f"OCR failed:\n{stderr.decode(errors='ignore')}"
                ))

        except Exception as e:
            if not is_stopping:
                root.after(0, lambda: messagebox.showerror("Error", f"OCR failed:\n{e}"))

        finally:
            current_process = None
            root.after(0, progress.stop)
            if is_stopping:
                root.after(0, lambda: status_label.config(text="🛑 OCR Stopped"))
            else:
                root.after(0, lambda: status_label.config(text="✅ Ready"))
            root.after(0, lambda: btn_start.config(state=NORMAL))
            root.after(0, lambda: btn_stop.config(state=DISABLED))

    threading.Thread(target=task, daemon=True).start()


def stop_ocr():
    """強制停止 OCR"""
    global current_process, is_stopping
    if current_process and current_process.poll() is None:
        is_stopping = True
        current_process.terminate()
        status_label.config(text="🛑 Canceling...")
        progress.stop()
        btn_stop.config(state=DISABLED)


def on_close():
    """關閉應用程式"""
    stop_ocr()
    try:
        progress.stop()
    except Exception:
        pass
    root.destroy()
    root.quit()


# --- 建立介面 ---
root = ttk.Window(themename="superhero")
root.title("PDF OCR Tool")
root.geometry("600x260")
if os.path.exists(icon_path):
    root.iconbitmap(icon_path)

# 標題
header = ttk.Label(root, text="PDF OCR Tool", font=("Segoe UI", 16, "bold"))
header.pack(pady=(15, 5))

# 說明文字
label = ttk.Label(root, text="1. Choose a PDF\n2. Choose output location", font=("Segoe UI", 11))
label.pack(pady=5)

# 按鈕區
frame = ttk.Frame(root)
frame.pack(pady=10)

btn_start = ttk.Button(frame, text="Start OCR", bootstyle=SUCCESS, command=run_ocr, width=15)
btn_start.pack(side="left", padx=10)

btn_stop = ttk.Button(frame, text="Stop OCR", bootstyle=DANGER, command=stop_ocr, width=15, state=DISABLED)
btn_stop.pack(side="left", padx=10)

# 進度條
progress = ttk.Progressbar(root, mode="indeterminate", length=280, bootstyle=INFO)
progress.pack(pady=10)

# 狀態文字
status_label = ttk.Label(root, text="✅ Ready", bootstyle=INFO)
status_label.pack(pady=5)

# 關閉事件
root.protocol("WM_DELETE_WINDOW", on_close)

root.mainloop()


# In[ ]:




