import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLabel, QLineEdit, QComboBox, QPushButton, QGroupBox,
    QTableWidget, QHeaderView, QAbstractItemView, QProgressBar, QFileDialog,
    QTableWidgetItem, QMessageBox
)
from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtGui import QIcon, QAction

from src.ui.workers import DownloadWorker, WorkerThread
from src.config.settings_manager import SettingsManager
from src.ui.settings_dialog import SettingsDialog
from src.utils.notifications import send_system_notification # Added
import src.ui.themes as themes 
import os
import time

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.download_queue = {}
        self.task_id_counter = 0
        self.active_downloads = 0
        
        self.settings_manager = SettingsManager()
        # Initialize attributes that load_and_apply_settings will use.
        self.output_dir_display = None 
        self.conv_output_dir_display = None
        self.start_downloads_button = None
        self.start_conversions_button = None
        self.add_queue_button = None
        self.url_input = None 
        self.pause_selected_button = None
        self.cancel_selected_button = None
        self.clear_finished_tasks_button = None
        self.status_table = None
        self.current_theme = self.settings_manager.get_setting('theme') 

        self.load_and_apply_settings() # Load settings that don't depend on UI created yet

        self.queue_check_timer = QTimer(self)
        self.queue_check_timer.timeout.connect(self.process_download_queue)
        self.queue_check_timer.timeout.connect(self.process_conversion_queue)
        self.queue_check_timer.timeout.connect(self.update_control_states) 
        self.queue_check_timer.start(1000)

        self.conversion_queue = {}
        self.active_conversions = 0

        self.setWindowTitle("VersaDownloader & Converter")
        self.setMinimumSize(QSize(800, 600))
        
        self._create_menu_bar()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        self.create_downloader_tab()
        self.create_converter_tab()
        self.create_status_area()
        
        # Apply settings that depend on UI elements being created
        if self.output_dir_display: self.output_dir_display.setText(self.default_output_directory)
        if self.conv_output_dir_display: self.conv_output_dir_display.setText(self.default_conversion_output_directory)
        
        if self.status_table: self.status_table.itemSelectionChanged.connect(self.update_selection_dependent_buttons)

        self.update_control_states() 
        self.apply_current_theme() # Apply theme after UI is fully built

    def create_downloader_tab(self):
        self.downloader_tab = QWidget()
        self.tabs.addTab(self.downloader_tab, "Video Downloader")
        downloader_layout = QVBoxLayout(self.downloader_tab)
        url_group = QGroupBox("YouTube URL"); url_layout = QHBoxLayout(url_group)
        url_layout.addWidget(QLabel("YouTube URL:"))
        self.url_input = QLineEdit(); self.url_input.setToolTip("Enter YouTube video or playlist URL here.")
        url_layout.addWidget(self.url_input); downloader_layout.addWidget(url_group)
        options_group = QGroupBox("Download Options"); options_form_layout = QFormLayout(options_group)
        self.quality_combo = QComboBox(); self.quality_combo.addItems(["Best", "1080p", "720p", "480p", "Audio Only"])
        self.quality_combo.setToolTip("Select video/audio quality."); options_form_layout.addRow(QLabel("Quality:"), self.quality_combo)
        self.format_combo = QComboBox(); self.format_combo.addItems(["MP4", "MKV", "WebM", "MP3", "M4A", "OGG"]) 
        self.format_combo.setToolTip("Select output format."); options_form_layout.addRow(QLabel("Format:"), self.format_combo)
        output_dir_layout = QHBoxLayout(); self.output_dir_display = QLineEdit() 
        self.output_dir_display.setReadOnly(True); self.browse_button = QPushButton("Browse...")
        self.browse_button.setToolTip("Browse for download directory."); self.browse_button.clicked.connect(self.browse_output_directory) 
        output_dir_layout.addWidget(self.output_dir_display); output_dir_layout.addWidget(self.browse_button)
        options_form_layout.addRow(QLabel("Output Directory:"), output_dir_layout); downloader_layout.addWidget(options_group)
        actions_group = QGroupBox("Actions"); actions_layout = QHBoxLayout(actions_group)
        self.add_queue_button = QPushButton("Add to Queue"); self.add_queue_button.setToolTip("Add URL to queue.")
        self.add_queue_button.clicked.connect(self.add_item_to_queue); 
        if self.url_input: self.url_input.textChanged.connect(self.update_control_states) 
        self.start_downloads_button = QPushButton("Start Downloads"); self.start_downloads_button.setToolTip("Start queued downloads.")
        self.start_downloads_button.clicked.connect(self.process_download_queue) 
        self.pause_selected_button = QPushButton("Pause Selected"); self.pause_selected_button.setToolTip("Pause selected tasks.")
        self.pause_selected_button.clicked.connect(self.pause_selected_tasks) 
        self.cancel_selected_button = QPushButton("Cancel Selected"); self.cancel_selected_button.setToolTip("Cancel selected tasks.")
        self.cancel_selected_button.clicked.connect(self.cancel_selected_tasks) 
        self.clear_finished_tasks_button = QPushButton("Clear Finished"); self.clear_finished_tasks_button.setToolTip("Remove finished tasks.")
        self.clear_finished_tasks_button.clicked.connect(self.clear_finished_tasks) 
        for btn in [self.add_queue_button, self.start_downloads_button, self.pause_selected_button, self.cancel_selected_button, self.clear_finished_tasks_button]: actions_layout.addWidget(btn)
        actions_layout.addStretch(); downloader_layout.addWidget(actions_group); downloader_layout.addStretch()

    def create_converter_tab(self):
        self.converter_tab = QWidget()
        self.tabs.addTab(self.converter_tab, "File Converter")
        converter_main_layout = QVBoxLayout(self.converter_tab)
        conv_input_group = QGroupBox("Input & Format Selection"); conv_input_layout = QFormLayout(conv_input_group)
        self.conv_add_files_button = QPushButton("Add Files..."); self.conv_add_files_button.setToolTip("Add files for conversion.")
        self.conv_add_files_button.clicked.connect(self.add_conversion_files) 
        conv_input_layout.addRow(self.conv_add_files_button)
        self.conv_format_combo = QComboBox()
        self.conv_format_combo.addItems(["MP4 (Video)", "MKV (Video)", "AVI (Video)", "MOV (Video)", "WebM (Video)", "MP3 (Audio)", "AAC (Audio)", "WAV (Audio)", "OGG (Audio)", "FLAC (Audio)", "M4A (Audio)", "PNG (Image)", "JPG (Image)", "WEBP (Image)", "PDF (Document)"])
        self.conv_format_combo.setToolTip("Select target conversion format."); conv_input_layout.addRow(QLabel("Target Format:"), self.conv_format_combo)
        converter_main_layout.addWidget(conv_input_group)
        conv_output_group = QGroupBox("Output Options"); conv_output_layout = QFormLayout(conv_output_group)
        conv_output_dir_inner_layout = QHBoxLayout(); self.conv_output_dir_display = QLineEdit() 
        self.conv_output_dir_display.setReadOnly(True); self.conv_browse_output_button = QPushButton("Browse...")
        self.conv_browse_output_button.setToolTip("Browse for conversion output directory."); self.conv_browse_output_button.clicked.connect(self.browse_converter_output_directory) 
        conv_output_dir_inner_layout.addWidget(self.conv_output_dir_display); conv_output_dir_inner_layout.addWidget(self.conv_browse_output_button)
        conv_output_layout.addRow(QLabel("Output Directory:"), conv_output_dir_inner_layout); converter_main_layout.addWidget(conv_output_group)
        self.start_conversions_button = QPushButton("Start All Conversions"); self.start_conversions_button.setToolTip("Start all queued conversions.")
        self.start_conversions_button.clicked.connect(self.process_conversion_queue) 
        converter_main_layout.addWidget(self.start_conversions_button, alignment=Qt.AlignmentFlag.AlignLeft); converter_main_layout.addStretch() 

    def create_status_area(self):
        status_group = QGroupBox("Download & Conversion Status"); status_layout = QVBoxLayout(status_group)
        self.status_table = QTableWidget(); self.status_table.setColumnCount(7)
        self.status_table.setHorizontalHeaderLabels(["#", "File Name / URL", "Type", "Progress", "Speed", "ETR", "Status"])
        self.status_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        header = self.status_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) 
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive); self.status_table.setColumnWidth(3, 120) 
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents); self.status_table.setColumnWidth(6, 120) 
        status_layout.addWidget(self.status_table); self.main_layout.addWidget(status_group)

    def browse_output_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory", self.output_dir_display.text() or self.default_output_directory)
        if directory: self.output_dir_display.setText(directory); self.settings_manager.set_setting('download_dir', directory)

    def browse_converter_output_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Conversion Output Directory", self.conv_output_dir_display.text() or self.default_conversion_output_directory)
        if directory: self.conv_output_dir_display.setText(directory); self.settings_manager.set_setting('conversion_output_dir', directory)

    def generate_task_id(self): self.task_id_counter += 1; return f"task_{self.task_id_counter}_{int(time.time() * 1000)}"

    def load_and_apply_settings(self):
        self.default_output_directory = self.settings_manager.get_setting('download_dir')
        if self.output_dir_display: self.output_dir_display.setText(self.default_output_directory)
        os.makedirs(self.default_output_directory, exist_ok=True)
        self.default_conversion_output_directory = self.settings_manager.get_setting('conversion_output_dir')
        if self.conv_output_dir_display: self.conv_output_dir_display.setText(self.default_conversion_output_directory)
        os.makedirs(self.default_conversion_output_directory, exist_ok=True)
        self.MAX_CONCURRENT_DOWNLOADS = self.settings_manager.get_setting('max_concurrent_downloads')
        self.MAX_CONCURRENT_CONVERSIONS = self.settings_manager.get_setting('max_concurrent_conversions')
        self.auto_clear_completed = self.settings_manager.get_setting('auto_clear_completed')
        new_theme = self.settings_manager.get_setting('theme')
        if self.current_theme != new_theme: self.current_theme = new_theme # Update internal state
        # Actual application of theme QSS is now in apply_current_theme, called after UI setup
        self.update_control_states()

    def apply_current_theme(self):
        app = QApplication.instance()
        if app: # Ensure app instance exists
            if self.current_theme == 'Dark': app.setStyleSheet(themes.DARK_THEME_QSS)
            else: app.setStyleSheet(themes.LIGHT_THEME_QSS) 
            print(f"Theme '{self.current_theme}' applied via stylesheet.")

    def _create_menu_bar(self):
        menu_bar = self.menuBar(); file_menu = menu_bar.addMenu("&File")
        settings_action = QAction("&Settings", self); settings_action.triggered.connect(self.open_settings_dialog)
        file_menu.addAction(settings_action)

    def open_settings_dialog(self):
        dialog = SettingsDialog(self.settings_manager, self)
        if dialog.exec(): self.load_and_apply_settings(); self.apply_current_theme(); QMessageBox.information(self, "Settings Applied", "Settings updated.")

    def add_item_to_queue(self):
        url = self.url_input.text().strip(); quality = self.quality_combo.currentText(); video_format = self.format_combo.currentText().lower(); output_dir = self.output_dir_display.text()
        if not url: QMessageBox.warning(self, "Missing URL", "Please enter a YouTube URL."); return
        if not output_dir: QMessageBox.warning(self, "Missing Output Directory", "Please select download output directory."); return
        task_id = self.generate_task_id(); is_playlist = "playlist?" in url.lower(); is_video = "watch?" in url.lower() or "youtu.be/" in url.lower()
        if is_playlist:
            playlist_fetch_task_id = f"pl_fetch_{task_id}"
            worker_obj = DownloadWorker(playlist_fetch_task_id, 'playlist_info_fetch', url, output_dir, quality, video_format)
            thread = WorkerThread(worker_obj); worker_obj.playlist_entry_signal.connect(self.handle_playlist_entry); worker_obj.finished_signal.connect(self.handle_worker_finished)
            self.download_queue[playlist_fetch_task_id] = {'url': url, 'type': 'Playlist Info Fetch', 'status': 'fetching_info', 'worker_thread': thread, 'worker_obj': worker_obj, 'title': f"Playlist: {url}"}
            self.add_or_update_table_row(playlist_fetch_task_id, f"Playlist: {url}", "Info Fetch", "Fetching..."); thread.start(); self.url_input.clear()
        elif is_video:
            self.download_queue[task_id] = {'url': url, 'type': 'Single Video Download', 'status': 'queued', 'quality': quality, 'format': video_format, 'output_path': output_dir, 'title': url}
            self.add_or_update_table_row(task_id, url, "Video Download", "Queued"); self.url_input.clear()
        else: QMessageBox.warning(self, "Invalid URL", "Please enter a valid YouTube video or playlist URL.")
        self.update_control_states()

    def handle_playlist_entry(self, data):
        video_task_id = data['task_id']; playlist_title = "".join(c for c in data.get('playlist_title', 'pl') if c.isalnum()or c in (' ','-','_')).rstrip()
        item_output_path = os.path.join(data['output_path'], playlist_title)
        self.download_queue[video_task_id] = {'url':data['original_url'],'yt_id':data['id'],'type':'Video Download','status':'queued','quality':data['quality'],'format':data['video_format'],'output_path':item_output_path,'title':data['title']}
        self.add_or_update_table_row(video_task_id, data['title'], "Video Download", "Queued"); self.update_control_states()

    def find_row_by_task_id(self, task_id):
        for r in range(self.status_table.rowCount()):
            if self.status_table.item(r,0) and self.status_table.item(r,0).data(Qt.ItemDataRole.UserRole) == task_id: return r
        return -1

    def add_or_update_table_row(self, task_id, display_name, item_type_str, status_str):
        row = self.find_row_by_task_id(task_id)
        if row == -1: row = self.status_table.rowCount(); self.status_table.insertRow(row)
        id_display = task_id.split('_')[1] if ('_' in task_id and len(task_id.split('_')) > 1) else task_id
        id_item = QTableWidgetItem(id_display); id_item.setData(Qt.ItemDataRole.UserRole, task_id)
        self.status_table.setItem(row,0,id_item)
        if not self.status_table.cellWidget(row,3): prog_bar = QProgressBar(); prog_bar.setValue(0); prog_bar.setTextVisible(True); self.status_table.setCellWidget(row,3,prog_bar)
        self.status_table.setItem(row,1,QTableWidgetItem(display_name)); self.status_table.setItem(row,2,QTableWidgetItem(item_type_str))
        status_item = self.status_table.item(row,6) or QTableWidgetItem(); self.status_table.setItem(row,6,status_item)
        status_item.setText(status_str); status_item.setToolTip("") 

    def process_download_queue(self):
        if self.active_downloads >= self.MAX_CONCURRENT_DOWNLOADS: return
        for task_id, details in list(self.download_queue.items()):
            if self.active_downloads >= self.MAX_CONCURRENT_DOWNLOADS: break
            if details['status'] == 'queued' and details['type'] == 'Video Download':
                os.makedirs(details['output_path'], exist_ok=True)
                worker = DownloadWorker(task_id=task_id, item_id=details.get('yt_id',task_id), task_type='single_video_download', url=details['url'], output_path=details['output_path'], quality=details['quality'], video_format=details['format'])
                thread = WorkerThread(worker); worker.progress_signal.connect(self.update_download_progress); worker.finished_signal.connect(self.handle_worker_finished)
                details.update({'worker_thread':thread,'worker_obj':worker,'status':'starting'})
                self.add_or_update_table_row(task_id,details['title'],details['type'],"Starting...");thread.start();self.active_downloads+=1
        self.update_control_states()

    def update_download_progress(self, data):
        task_id=data['id']; row=self.find_row_by_task_id(task_id)
        if row == -1: return
        s_item=self.status_table.item(row,6) or QTableWidgetItem(); self.status_table.setItem(row,6,s_item); s_item.setToolTip("")
        prog_bar=self.status_table.cellWidget(row,3)
        if data.get('status') == 'retrying': 
            s_item.setText(data.get('message','Retrying...'))
            if isinstance(prog_bar, QProgressBar): prog_bar.setRange(0,0); prog_bar.setTextVisible(False)
        elif data.get('status') == 'downloading':
            if 'title' in data and data['title'] != "N/A": self.status_table.item(row,1).setText(data['title']); self.download_queue[task_id]['title']=data['title']
            if isinstance(prog_bar, QProgressBar): prog_bar.setRange(0,100); prog_bar.setValue(int(data['percentage'])); prog_bar.setTextVisible(True)
            self.status_table.setItem(row,4,QTableWidgetItem(str(data.get('speed','N/A')))); self.status_table.setItem(row,5,QTableWidgetItem(str(data.get('eta','0s'))))
            s_item.setText(data['status'].capitalize())
        self.update_control_states()

    def handle_worker_finished(self, data):
        task_id=data['id']; row=self.find_row_by_task_id(task_id)
        if row == -1: return
        s_txt=data['status'].capitalize(); s_item=self.status_table.item(row,6) or QTableWidgetItem(); self.status_table.setItem(row,6,s_item); s_item.setToolTip("")
        prog_bar=self.status_table.cellWidget(row,3)
        if isinstance(prog_bar, QProgressBar): prog_bar.setRange(0,100)
        if data['status']=='completed': s_txt="✔ Completed"; prog_bar.setValue(100) if isinstance(prog_bar, QProgressBar) else None
        elif data['status']=='failed': s_txt="✘ Failed"; s_item.setToolTip(data.get('message','Error')); prog_bar.setValue(0) if isinstance(prog_bar, QProgressBar) else None
        elif data['status']=='cancelled': s_txt="∅ Cancelled"
        s_item.setText(s_txt)
        if data.get('title') and data['title']!="N/A" and self.status_table.item(row,1) : self.status_table.item(row,1).setText(data['title']); self.download_queue[task_id]['title']=data['title']
        if task_id in self.download_queue:
            if self.download_queue[task_id].get('type')=='Video Download': self.active_downloads=max(0,self.active_downloads-1)
            self.download_queue[task_id].update({'status':data['status'],'worker_thread':None,'worker_obj':None})
            if data['status']=='completed' and data.get('filepath'): self.download_queue[task_id]['filepath']=data['filepath']
        self.process_download_queue()
        if data['status']=='completed' and self.auto_clear_completed: QTimer.singleShot(2000, lambda: self.clear_task_from_table(task_id,'download'))
        self.update_control_states()
        self.check_and_notify_batch_completion('download')


    def get_selected_task_ids(self): return [self.status_table.item(idx.row(),0).data(Qt.ItemDataRole.UserRole) for idx in self.status_table.selectionModel().selectedRows() if self.status_table.item(idx.row(),0)]

    def pause_selected_tasks(self): 
        task_ids = self.get_selected_task_ids()
        for task_id in task_ids:
            q, task_type_str = (self.download_queue, "Download") if task_id in self.download_queue else (self.conversion_queue, "Conversion") if task_id in self.conversion_queue else (None, None)
            if q and task_id in q:
                info = q[task_id]
                if info.get('status') in ['downloading', 'starting', 'converting']: 
                    if info.get('worker_obj'): info['worker_obj'].cancel() 
                info['status'] = 'paused'; self.add_or_update_table_row(task_id, info.get('title',''), info.get('type', task_type_str), "Paused")
        self.update_control_states()

    def cancel_selected_tasks(self): 
        task_ids = self.get_selected_task_ids()
        for task_id in task_ids:
            q, active_attr, type_str = (self.download_queue, 'active_downloads', "Download") if task_id in self.download_queue else \
                                       (self.conversion_queue, 'active_conversions', "Conversion") if task_id in self.conversion_queue else (None, None, None)
            if q and task_id in q:
                info = q[task_id]
                if info.get('worker_obj'): info['worker_obj'].cancel()
                else:
                    info['status'] = 'cancelled'; self.add_or_update_table_row(task_id, info.get('title',''), info.get('type', type_str), "Cancelled")
                    if info.get('worker_thread') and active_attr: setattr(self, active_attr, max(0, getattr(self, active_attr)-1))
                    info.update({'worker_obj':None,'worker_thread':None})
        self.process_download_queue(); self.process_conversion_queue(); self.update_control_states()

    def clear_finished_tasks(self): 
        dl_q, conv_q = self.download_queue, self.conversion_queue
        for r in range(self.status_table.rowCount()-1,-1,-1):
            t_id_item = self.status_table.item(r,0); 
            if not t_id_item: continue
            t_id = t_id_item.data(Qt.ItemDataRole.UserRole)
            stat = (dl_q.get(t_id) or conv_q.get(t_id) or {}).get('status')
            s_item = self.status_table.item(r,6)
            s_item_text = (s_item.text() if s_item else "").lower()
            if stat in ['completed','failed','cancelled'] or any(s in s_item_text for s in ["✔","✘","∅","fetched","error"]):
                self.status_table.removeRow(r)
                if t_id in dl_q: del dl_q[t_id]
                if t_id in conv_q: del conv_q[t_id]
        self.update_control_states()

    def add_conversion_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files", os.path.expanduser("~"), 
            "All Files (*);;Video (*.mp4 *.mkv);;Audio (*.mp3 *.aac);;Images (*.png *.jpg);;Docs (*.docx *.txt)")
        if not files: return
        s_fmt_str=self.conv_format_combo.currentText(); t_fmt,f_type=self.parse_format_string(s_fmt_str)
        if not t_fmt: QMessageBox.warning(self,"Invalid Format",f"Could not parse: {s_fmt_str}"); return
        out_dir=self.conv_output_dir_display.text()
        if not out_dir: QMessageBox.warning(self,"Missing Output","Select conversion output directory."); return
        exts={'video':['.mp4','.mkv','.avi','.mov','.webm','.flv','.ts'],'audio':['.mp3','.aac','.wav','.ogg','.flac','.m4a'],
              'image':['.png','.jpg','.jpeg','.webp','.heic','.heif'],'document':['.docx','.txt']}
        for path in files:
            t_id=self.generate_task_id(); b_name=os.path.basename(path); _,ext=os.path.splitext(path); ext=ext.lower()
            sub_type = next((k for k,v in exts.items() if ext in v), None)
            if not sub_type: QMessageBox.warning(self,"Unsupported File",f"File type for '{b_name}' not recognized."); continue
            valid=True
            if sub_type=='document' and (f_type!='document' or t_fmt!='pdf'): valid=False
            elif sub_type=='video' and f_type not in ['video','audio']: valid=False
            elif sub_type=='audio' and f_type!='audio': valid=False
            elif sub_type=='image' and f_type!='image': valid=False
            if not valid: QMessageBox.warning(self,"Format Mismatch",f"Cannot convert {sub_type} '{b_name}' to {s_fmt_str}."); continue
            if ext in ['.heic','.heif'] and sub_type=='image' and not self.check_heif_support(): QMessageBox.warning(self,"HEIF Missing",f"'{b_name}' needs 'pillow-heif'."); continue
            self.conversion_queue[t_id]={'input_filepath':path,'status':'queued','output_dir':out_dir,'target_format':t_fmt,'task_subtype':sub_type,'title':b_name}
            self.add_or_update_table_row(t_id,b_name,f"{sub_type.capitalize()} Conv.","Queued")
        self.update_control_states()

    def process_conversion_queue(self):
        if self.active_conversions >= self.MAX_CONCURRENT_CONVERSIONS: return
        for t_id,details in list(self.conversion_queue.items()):
            if self.active_conversions >= self.MAX_CONCURRENT_CONVERSIONS: break
            if details['status']=='queued':
                b_name_no_ext,_=os.path.splitext(os.path.basename(details['input_filepath'])); o_fname=f"{b_name_no_ext}.{details['target_format']}"; o_fpath=os.path.join(details['output_dir'],o_fname)
                os.makedirs(os.path.dirname(o_fpath),exist_ok=True)
                worker=ConversionWorker(t_id,details['input_filepath'],o_fpath,details['target_format'],details['task_subtype'])
                thread=WorkerThread(worker);worker.conversion_update_signal.connect(self.update_conversion_progress);worker.conversion_finished_signal.connect(self.handle_conversion_finished)
                details.update({'worker_thread':thread,'worker_obj':worker,'status':'starting','output_filepath_expected':o_fpath})
                self.add_or_update_table_row(t_id,details['title'],f"{details['task_subtype'].capitalize()} Conv.","Starting...")
                thread.start();self.active_conversions+=1
        self.update_control_states()

    def update_conversion_progress(self, data):
        t_id=data['id']; row=self.find_row_by_task_id(t_id)
        if row == -1: return
        s_item=self.status_table.item(row,6) or QTableWidgetItem(); self.status_table.setItem(row,6,s_item)
        s_item.setText(data.get('status_text','Converting...')); s_item.setToolTip("") 
        prog_bar=self.status_table.cellWidget(row,3)
        if isinstance(prog_bar,QProgressBar):
            t_type=data.get('type','video'); p_val=data.get('progress_value')
            if t_type in ['image','document'] or p_val is None: prog_bar.setRange(0,0); prog_bar.setTextVisible(False)
            else: prog_bar.setRange(0,100); prog_bar.setValue(p_val); prog_bar.setTextVisible(True)
        self.status_table.setItem(row,4,QTableWidgetItem("N/A")); self.status_table.setItem(row,5,QTableWidgetItem("N/A")) 
        if 'title' in data and self.status_table.item(row,1): self.status_table.item(row,1).setText(data['title'])
        self.update_control_states()

    def handle_conversion_finished(self, data):
        t_id=data['id']; row=self.find_row_by_task_id(t_id)
        if row == -1: return
        s_txt_disp=data['status'].capitalize(); s_item=self.status_table.item(row,6) or QTableWidgetItem(); self.status_table.setItem(row,6,s_item); s_item.setToolTip("")
        prog_bar=self.status_table.cellWidget(row,3)
        if isinstance(prog_bar,QProgressBar): prog_bar.setRange(0,100)
        if data['status']=='completed': s_txt_disp="✔ Completed"; prog_bar.setValue(100) if isinstance(prog_bar, QProgressBar) else None
        elif data['status']=='failed': s_txt_disp="✘ Failed"; s_item.setToolTip(data.get('message','Error')); prog_bar.setValue(0) if isinstance(prog_bar, QProgressBar) else None
        elif data['status']=='cancelled': s_txt_disp="∅ Cancelled"
        s_item.setText(s_txt_disp)
        if t_id in self.conversion_queue:
            self.conversion_queue[t_id].update({'status':data['status'],'worker_thread':None,'worker_obj':None})
            if data['status']=='completed' and data.get('output_filepath'): self.conversion_queue[t_id]['output_filepath_actual']=data['output_filepath']
            self.active_conversions=max(0,self.active_conversions-1)
        self.process_conversion_queue()
        if data['status']=='completed' and self.auto_clear_completed: QTimer.singleShot(2000,lambda:self.clear_task_from_table(t_id,'conversion'))
        self.update_control_states()
        self.check_and_notify_batch_completion('conversion')


    def check_and_notify_batch_completion(self, completed_task_type):
        if completed_task_type == 'download':
            if self.active_downloads == 0:
                # Check if any downloads are still queued or in an active-like state (starting, retrying)
                still_processing_downloads = any(
                    task['status'] in ['queued', 'starting', 'retrying'] 
                    for task in self.download_queue.values()
                )
                if not still_processing_downloads:
                    # Check if there were any tasks at all in the download queue that reached a final state
                    # This prevents notifications if the queue was empty and something external triggered this check.
                    if any(task['status'] in ['completed', 'failed', 'cancelled'] for task in self.download_queue.values()):
                         send_system_notification("Downloads Complete", "All video download tasks have finished processing.")
        
        elif completed_task_type == 'conversion':
            if self.active_conversions == 0:
                still_processing_conversions = any(
                    task['status'] in ['queued', 'starting'] 
                    for task in self.conversion_queue.values()
                )
                if not still_processing_conversions:
                    if any(task['status'] in ['completed', 'failed', 'cancelled'] for task in self.conversion_queue.values()):
                        send_system_notification("Conversions Complete", "All file conversion tasks have finished processing.")

    def clear_task_from_table(self, task_id, queue_type):
        row=self.find_row_by_task_id(task_id)
        if row != -1: self.status_table.removeRow(row)
        q=self.download_queue if queue_type=='download' else self.conversion_queue
        if task_id in q: del q[task_id]; print(f"Task {task_id} removed from {queue_type} queue.")
        self.update_control_states()

    def parse_format_string(self, format_str):
        try: p=format_str.split("(");a=p[0].strip().lower();t=p[1].replace(")","").strip().lower();return a,t
        except IndexError: print(f"Warning: Could not parse format: {format_str}"); return format_str.lower(),None

    def check_heif_support(self):
        try: from PIL import features; return features.check('heif')
        except ImportError: return False

    def update_control_states(self):
        if not hasattr(self, 'start_downloads_button') or not self.start_downloads_button: return 
        has_q_dl=any(t['status']=='queued' for t in self.download_queue.values())
        self.start_downloads_button.setEnabled(has_q_dl and self.active_downloads < self.MAX_CONCURRENT_DOWNLOADS)
        has_q_conv=any(t['status']=='queued' for t in self.conversion_queue.values())
        self.start_conversions_button.setEnabled(has_q_conv and self.active_conversions < self.MAX_CONCURRENT_CONVERSIONS)
        if self.url_input: self.add_queue_button.setEnabled(bool(self.url_input.text().strip()))
        self.update_selection_dependent_buttons()
        if self.status_table: self.clear_finished_tasks_button.setEnabled(self.status_table.rowCount() > 0)

    def update_selection_dependent_buttons(self):
        if not hasattr(self, 'status_table') or not self.status_table or not self.status_table.selectionModel(): return 
        has_selection=bool(self.status_table.selectionModel().selectedRows())
        self.pause_selected_button.setEnabled(has_selection)
        self.cancel_selected_button.setEnabled(has_selection)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
