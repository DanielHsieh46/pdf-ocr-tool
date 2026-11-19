#!/usr/bin/env python
# coding: utf-8

import os
import sys

from PyQt6.QtCore import QProcess, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


base_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
icon_path = os.path.join(base_dir, "PDF_OCR.ico")
os.environ["PATH"] = os.pathsep.join(
    [os.path.join(base_dir, folder) for folder in ("tesseract", "ghostscript", "pngquant")]
    + [os.environ["PATH"]]
)


class OCRWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF OCR Tool")
        self.resize(600, 260)
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.is_stopping = False
        self.output_path = ""
        self.process = QProcess(self)
        self.process.finished.connect(self.ocr_finished)
        self.process.errorOccurred.connect(self.ocr_error)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 15, 24, 15)
        header = QLabel("PDF OCR Tool")
        header.setStyleSheet("font: bold 16pt 'Segoe UI';")
        layout.addWidget(header, alignment=Qt.AlignmentFlag.AlignCenter)
        label = QLabel("1. Choose a PDF\n2. Choose output location")
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)

        buttons = QHBoxLayout()
        buttons.addStretch()
        self.btn_start = QPushButton("Start OCR")
        self.btn_start.setMinimumWidth(130)
        self.btn_start.clicked.connect(self.run_ocr)
        buttons.addWidget(self.btn_start)
        self.btn_stop = QPushButton("Stop OCR")
        self.btn_stop.setMinimumWidth(130)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_ocr)
        buttons.addWidget(self.btn_stop)
        buttons.addStretch()
        layout.addLayout(buttons)

        self.progress = QProgressBar()
        self.progress.setFixedWidth(280)
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress, alignment=Qt.AlignmentFlag.AlignCenter)
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignCenter)

    def run_ocr(self):
        input_path, _ = QFileDialog.getOpenFileName(
            self, "Select a PDF to OCR", "", "PDF files (*.pdf)"
        )
        if not input_path:
            return

        default_name = os.path.splitext(os.path.basename(input_path))[0] + "_ocr.pdf"
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Save OCR Output As", default_name, "PDF files (*.pdf)"
        )
        if not output_path:
            return
        if not os.path.splitext(output_path)[1]:
            output_path += ".pdf"

        self.output_path = output_path
        self.is_stopping = False
        self.progress.setRange(0, 0)
        self.status_label.setText("Processing... Please wait")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.process.start(
            "ocrmypdf",
            [
                "--force-ocr",
                "--language", "chi_tra+eng",
                "--rotate-pages",
                "--optimize", "3",
                "--output-type", "pdf",
                "--jobs", "8",
                input_path,
                output_path,
            ],
        )

    def reset_controls(self):
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.status_label.setText("OCR Stopped" if self.is_stopping else "Ready")
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def ocr_finished(self, exit_code, exit_status):
        error = bytes(self.process.readAllStandardError()).decode(errors="replace")
        self.process.readAllStandardOutput()
        self.reset_controls()
        if self.is_stopping:
            return
        if exit_code == 0 and exit_status == QProcess.ExitStatus.NormalExit:
            QMessageBox.information(
                self, "Success", f"OCR completed!\nSaved to:\n{self.output_path}"
            )
        else:
            QMessageBox.critical(self, "Error", f"OCR failed:\n{error}")

    def ocr_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.reset_controls()
            QMessageBox.critical(
                self, "Error", f"OCR failed:\n{self.process.errorString()}"
            )

    def stop_ocr(self):
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.is_stopping = True
            self.status_label.setText("Canceling...")
            self.btn_stop.setEnabled(False)
            self.process.kill()

    def closeEvent(self, event):
        self.stop_ocr()
        self.process.waitForFinished(3000)
        event.accept()


if __name__ == "__main__":
    app = QApplication.instance()
    created_app = app is None
    if created_app:
        app = QApplication([sys.argv[0]])
    window = OCRWindow()
    window.show()
    if created_app:
        sys.exit(app.exec())
