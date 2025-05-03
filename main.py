import flet as ft
from flet import *
import os
import PyPDF2
from docx import Document
import subprocess
import platform
from threading import Timer
import json
import hashlib
import time
from pathlib import Path
import tempfile
import webbrowser
from datetime import datetime
import os
import re

#pip install flet pyinstaller PyPDF2 python-docx  PyMuPDF

# פונקציית עזר – נתיב אחסון לאפליקציה
def get_app_data_path():
    if platform.system() == 'Windows':
        app_data = os.path.join(os.getenv('APPDATA'), 'DocumentSearchApp')
    elif platform.system() == 'Darwin':
        app_data = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'DocumentSearchApp')
    else:
        app_data = os.path.join(os.path.expanduser('~'), '.config', 'DocumentSearchApp')
    os.makedirs(app_data, exist_ok=True)
    return app_data



def tokenize(text):
    # מפרק טקסט למילים בלבד, מתעלם מסימני פיסוק
    return re.findall(r'\w+', text.lower(), re.UNICODE)

#---------------------------------
# היסטורית חיפושים
#---------------------------------
class SearchHistory:
    def __init__(self, max_items=10):
        self.max_items = max_items
        self.history = []
        self.history_file = Path("search_history.json")
        self.load_history()

    def add(self, search_term):
        """הוספת חיפוש חדש להיסטוריה"""
        if search_term and search_term.strip():
            search_term = search_term.strip()
            # הסר את החיפוש אם הוא כבר קיים
            self.history = [h for h in self.history if h != search_term]
            # הוסף את החיפוש החדש בהתחלה
            self.history.insert(0, search_term)
            # שמור רק את מספר הפריטים המקסימלי
            self.history = self.history[:self.max_items]
            self.save_history()

    def get_history(self):
        """קבלת רשימת החיפושים"""
        return self.history

    def clear(self):
        """ניקוי ההיסטוריה"""
        self.history = []
        self.save_history()

    def remove_item(self, search_term):
        """הסרת פריט ספציפי מההיסטוריה"""
        self.history = [h for h in self.history if h != search_term]
        self.save_history()

    def load_history(self):
        """טעינת היסטוריית החיפושים מקובץ"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
        except Exception:
            self.history = []

    def save_history(self):
        """שמירת היסטוריית החיפושים לקובץ"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # במקרה של שגיאה בשמירה, נתעלם



class SearchOptions:
    def __init__(self):
        self.exact_match = False
        self.word_distance = None
        self.match_all_words = True
        self.exclude_words = []
        self.file_types = []
        self.date_range = {'start': None, 'end': None}
        self.min_word_count = None
        self.search_in_path = False        

#--------------------------
#    הגדרות
#--------------------------
class AppSettings:
    def __init__(self):
        self.app_data_path = get_app_data_path()
        self.settings_file = os.path.join(self.app_data_path, 'settings.json')
        self.default_settings = {
            'theme': 'light',
            'primary_color': '#0078D4',
            'font_size': 'normal',
            'indexes': [],
            'selected_indexes': []
        }
        self.settings = self.load_settings()
        self.validate_settings()

    def validate_settings(self):
        was_changed = False
        for key, default_value in self.default_settings.items():
            if key not in self.settings:
                self.settings[key] = default_value
                was_changed = True
        if was_changed:
            self.save_settings()

    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    settings = self.default_settings.copy()
                    settings.update(loaded_settings)
                    return settings
            except Exception as e:
                print(f"שגיאה בטעינת הגדרות: {e}")
                return self.default_settings.copy()
        return self.default_settings.copy()

    def save_settings(self):
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving settings: {str(e)}")

    def add_index(self, path):
        if 'indexes' not in self.settings:
            self.settings['indexes'] = []
        if path not in [idx['path'] for idx in self.settings['indexes']]:
            self.settings['indexes'].append({
                'path': path,
                'name': os.path.basename(path),
                'created': datetime.now().isoformat()
            })
            # תמיד הוסף ל-selected_indexes כברירת מחדל
            if 'selected_indexes' not in self.settings:
                self.settings['selected_indexes'] = []
            if path not in self.settings['selected_indexes']:
                self.settings['selected_indexes'].append(path)
            self.save_settings()

    def remove_index(self, path):
        if 'indexes' in self.settings:
            self.settings['indexes'] = [idx for idx in self.settings['indexes'] if idx['path'] != path]
        if 'selected_indexes' in self.settings:
            self.settings['selected_indexes'] = [p for p in self.settings['selected_indexes'] if p != path]
        self.save_settings()

    def get_selected_indexes(self):
        selected = self.settings.get('selected_indexes', [])
        if not selected:
            return [idx['path'] for idx in self.settings['indexes']]
        return selected

    def get_setting(self, key, default=None):
        return self.settings.get(key, default)
    
#--------------------
# איינדקסם
#---------------------
class FileIndex:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.app_data_path = get_app_data_path()
        self.index_file = self.get_index_file_path()
        self.index = self.load_index()

    def get_index_file_path(self):
        hashed = hashlib.md5(self.folder_path.encode()).hexdigest()
        return os.path.join(self.app_data_path, f'index_{hashed}.json')

    def load_index(self):
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"שגיאה בטעינת אינדקס: {e}")
                return {}
        return {}

    def save_index(self):
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, ensure_ascii=False, indent=2)

    def delete_index_file(self):
        if os.path.exists(self.index_file):
            os.remove(self.index_file)

    def get_file_hash(self, file_path):
        """החזרת hash של קובץ (md5)"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"שגיאה ביצירת hash לקובץ {file_path}: {e}")
            return None

    def needs_update(self):
        # בדוק אם קובץ האינדקס לא קיים או ריק
        if not os.path.exists(self.index_file) or not bool(self.index):
            return True
        # אפשר לבדוק תאריכים כאן (מתקדם)
        # לדוג' אם קובץ חדש נוצר בתיקיה אחרי האינדוקס האחרון
        return False            

    def extract_pdf_content(self, file_path):
        """מחלץ תוכן מקובץ PDF לפי עמודים"""
        contents = []
        try:
            with open(file_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    text = page.extract_text()
                    if text.strip():
                        contents.append({
                            'content': text,
                            'page': page_num
                        })
        except Exception as e:
            print(f"שגיאה בקריאת PDF {file_path}: {str(e)}")
        return contents

    def extract_docx_content(self, file_path):
        """מחלץ תוכן מקובץ DOCX לפי פסקאות"""
        contents = []
        try:
            doc = Document(file_path)
            for para_num, para in enumerate(doc.paragraphs, 1):
                text = para.text
                if text.strip():
                    contents.append({
                        'content': text,
                        'paragraph': para_num
                    })
        except Exception as e:
            print(f"שגיאה בקריאת DOCX {file_path}: {str(e)}")
        return contents


    def extract_txt_content(self, file_path):
        """מחלץ תוכן מקובץ TXT"""
        contents = []
        # רשימת קידודים נפוצים לניסיון
        encodings = [
            'utf-8', 'cp1255', 'ascii', 'iso-8859-8', 
            'gb18030', 'big5', 'cp949', 'euc-jp', 'euc-kr',
            'shift_jis', 'gb2312', 'gbk', 'iso-2022-jp',
            'utf-16', 'utf-32'
        ]
        
        # ניסיון לזהות את הקידוד של הקובץ
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as txt_file:
                    full_text = txt_file.read()
                    
                    # חלוקת הטקסט למילים
                    words = full_text.split()
                    
                    # חלוקה לחלקים של 200 מילים
                    chunk_size = 200
                    for i in range(0, len(words), chunk_size):
                        chunk_words = words[i:i + chunk_size]
                        chunk_text = ' '.join(chunk_words)
                        
                        if chunk_text.strip():
                            contents.append({
                                'content': chunk_text,
                                'chunk': (i // chunk_size) + 1
                            })
                    
                    # אם הצלחנו לקרוא את הקובץ, נצא מהלולאה
                    break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"שגיאה בקריאת TXT {file_path}: {str(e)}")
                break
        
        return contents

    def update_index(self, callback=None):
        """מעדכן את האינדקס"""
        if not self.folder_path:
            return
            
        # ספירת קבצים תחילה
        total_files = sum(1 for root, _, files in os.walk(self.folder_path)
                         for file in files if file.endswith(('.pdf', '.docx', '.txt')))
        
        files_processed = 0
        for root, _, files in os.walk(self.folder_path):
            for file in files:
                if file.endswith(('.pdf', '.docx', '.txt')):
                    file_path = os.path.join(root, file)
                    file_hash = self.get_file_hash(file_path)
                    
                    # עדכון התקדמות
                    files_processed += 1
                    if callback:
                        callback(files_processed, total_files)
                    
                    # בדיקה אם הקובץ השתנה
                    if file_path in self.index and self.index[file_path]['hash'] == file_hash:
                        continue
                    
                    # חילוץ תוכן הקובץ
                    if file.endswith('.pdf'):
                        contents = self.extract_pdf_content(file_path)
                    elif file.endswith('.docx'):
                        contents = self.extract_docx_content(file_path)
                    else:  # .txt
                        contents = self.extract_txt_content(file_path)
                    
                    # שמירה באינדקס
                    self.index[file_path] = {
                        'hash': file_hash,
                        'contents': contents,
                        'filename': file
                    }
        
        self.save_index()


    def search(self, query, search_options=None):
        #print("=== FILEINDEX.SEARCH CALLED ===")
        if search_options is None:
            search_options = SearchOptions()
        if not query:
            query = ""
        query_words = [w.lower() for w in tokenize(query)]
        exclude_words = [w.lower() for w in getattr(search_options, 'exclude_words', [])]
        #print(f"query_words={query_words}, search_options={vars(search_options)}")
        results = []

        for file_path, file_data in self.index.items():
            if not os.path.exists(file_path):
                continue

            # סינון לפי סוג קובץ
            if search_options.file_types and not any(file_path.lower().endswith(ft) for ft in search_options.file_types):
                continue

            # סינון לפי טווח תאריכים
            if getattr(search_options, "date_range", None):
                dr = search_options.date_range
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if (dr.get('start') and file_time < dr['start']) or (dr.get('end') and file_time > dr['end']):
                    continue

            # חיפוש רק בשם קובץ ונתיב
            if getattr(search_options, "search_in_path", False):
                path_text = " ".join(tokenize(f"{file_path} {file_data['filename']}"))
                if all(qw in path_text for qw in query_words):
                    results.append({
                        'filename': file_data['filename'],
                        'file_path': file_path,
                        'context': "[התאמה בשם הקובץ או הנתיב]",
                        'location': "שם קובץ"
                    })
                continue

            for content_item in file_data['contents']:
                content = content_item.get('content', "")
                words = tokenize(content)

                # סינון לפי מס' מילים מינימלי
                if getattr(search_options, "min_word_count", None) and len(words) < search_options.min_word_count:
                    continue

                # סינון מילים שיש להוציא
                if exclude_words and any(ex_word in words for ex_word in exclude_words):
                    continue

                match_found = False

                # ---- חיפוש עם מרחק בין מילים (window) ----
                if getattr(search_options, "word_distance", None) is not None and len(query_words) >= 2:
                    window_size = search_options.word_distance + 1 if search_options.word_distance > 0 else len(words)
                    found = False
                    for i in range(len(words) - window_size + 1):
                        window = words[i:i+window_size]
                        if all(qw in window for qw in query_words):
                            found = True
                            break
                    match_found = found

                # ---- חיפוש רגיל ----
                else:
                    if getattr(search_options, "exact_match", False):
                        # כל המילים חייבות להופיע בדיוק
                        if getattr(search_options, "match_all_words", True):
                            match_found = all(qw in words for qw in query_words)
                        else:
                            match_found = any(qw in words for qw in query_words)
                    else:
                        content_lower = " ".join(words)
                        if getattr(search_options, "match_all_words", True):
                            match_found = all(qw in content_lower for qw in query_words)
                        else:
                            match_found = any(qw in content_lower for qw in query_words)

                if match_found:
                    context = self.get_context(content, query_words, search_options, context_length=200) if hasattr(self, 'get_context') else ''
                    location_info = self.get_location_info(content_item) if hasattr(self, 'get_location_info') else ''
                    results.append({
                        'filename': file_data['filename'],
                        'file_path': file_path,
                        'context': context,
                        'location': location_info
                    })

        return results

    def get_location_info(self, content_item):
        """מחזיר מידע על מיקום התוכן בקובץ"""
        if 'page' in content_item:
            return f"עמוד {content_item['page']}"
        elif 'paragraph' in content_item:
            return f"פסקה {content_item['paragraph']}"
        else:
            return f"חלק {content_item['chunk']}"

    def get_context(self, text, query_words, search_options, context_length=200):
        """מחזיר את ההקשר המורחב סביב מילות החיפוש"""
        words = text.split()
        text_words = [w.lower() for w in words]
        
        # מציאת המיקום הראשון של מילת חיפוש
        first_match_index = -1
        last_match_index = -1
        
        for i, word in enumerate(text_words):
            for query_word in query_words:
                if (search_options.exact_match and word == query_word.lower()) or \
                   (not search_options.exact_match and query_word.lower() in word):
                    if first_match_index == -1:
                        first_match_index = i
                    last_match_index = i

        if first_match_index == -1:
            # אם לא נמצאה התאמה, מחזיר את context_length המילים הראשונות
            return ' '.join(words[:context_length])

        # חישוב טווח המילים להצגה
        start = max(0, first_match_index - context_length // 4)
        end = min(len(words), last_match_index + context_length // 4)
        
        context = ' '.join(words[start:end])
        
        if start > 0:
            context = "..." + context
        if end < len(words):
            context = context + "..."
            
        return context


#-------------------------------
#   מחלקה ראשית
#--------------------------------
class DocumentSearchApp:
    def __init__(self, page: Page):
        self.page = page
        self.page.title = "מנוע חיפוש מסמכים"
        self.page.rtl = True
        self.search_options = SearchOptions()
        self.status_timer = None
        self.current_book_path = None
        self.current_book_pages = []
        self.current_page_index = 0
        self.search_history = SearchHistory()
        self.app_settings = AppSettings()
        self.force_book_path = None

        self.selected_file_types = self.app_settings.settings.get('file_types', [".pdf", ".docx", ".txt"])
        self.word_distance = self.app_settings.settings.get('word_distance', 0)
        self.search_options.file_types = self.selected_file_types
        self.search_options.word_distance = self.word_distance

        self.apply_theme_settings()
        self.init_components()
        self.setup_ui()

    def get_selected_file_types(self):
        # תמיד מחזיר את הסוגים העדכניים
        return self.selected_file_types

    def create_file_type_buttons_row(self):
        file_types = self.get_selected_file_types()
        return ft.Row([
            ft.Text("סוגי קבצים:", size=14),
            ft.ElevatedButton(
                text="PDF",
                data=".pdf",
                bgcolor=ft.Colors.PRIMARY if ".pdf" in file_types else ft.Colors.SURFACE,
                color=ft.Colors.ON_PRIMARY if ".pdf" in file_types else ft.Colors.ON_SURFACE,
                on_click=self.toggle_file_filter
            ),
            ft.ElevatedButton(
                text="Word",
                data=".docx",
                bgcolor=ft.Colors.PRIMARY if ".docx" in file_types else ft.Colors.SURFACE,
                color=ft.Colors.ON_PRIMARY if ".docx" in file_types else ft.Colors.ON_SURFACE,
                on_click=self.toggle_file_filter
            ),
            ft.ElevatedButton(
                text="Text",
                data=".txt",
                bgcolor=ft.Colors.PRIMARY if ".txt" in file_types else ft.Colors.SURFACE,
                color=ft.Colors.ON_PRIMARY if ".txt" in file_types else ft.Colors.ON_SURFACE,
                on_click=self.toggle_file_filter
            ),
            ft.Container(width=20),
            ft.Text("מרחק בין מילים:", size=14),
            ft.TextField(
                value=str(self.word_distance),
                width=60,
                on_change=self.update_word_distance,
            ),
        ], spacing=10, alignment=ft.MainAxisAlignment.END)

    def toggle_file_filter(self, e):
        file_type = e.control.data
        file_types = self.get_selected_file_types().copy()
        if file_type in file_types:
            file_types.remove(file_type)
        else:
            file_types.append(file_type)
        self.selected_file_types = file_types
        self.search_options.file_types = file_types
        self.app_settings.settings['file_types'] = file_types
        self.app_settings.save_settings()
        # רענון שורת הכפתורים
        self.advanced_settings.content = self.build_advanced_settings_panel()
        self.advanced_settings.update()
        # בצע חיפוש אם יש טקסט
        if self.search_term.value:
            self.search_documents(None)

    def toggle_advanced_settings(self, e):
        self.advanced_settings.visible = not self.advanced_settings.visible
        self.advanced_settings.update()

    def update_word_distance(self, e):
        try:
            distance = int(e.control.value)
            if distance < 0:
                e.control.value = "0"
                distance = 0
            self.word_distance = distance
            self.search_options.word_distance = distance if distance > 0 else None
            self.app_settings.settings['word_distance'] = distance
            self.app_settings.save_settings()
        except ValueError:
            e.control.value = "0"
            self.word_distance = 0
            self.search_options.word_distance = None
            self.app_settings.settings['word_distance'] = 0
            self.app_settings.save_settings()


    def init_components(self):
        """אתחול כל הרכיבים הדרושים"""
        # רכיב הודעות
        self.message_container = Container(
            content=Row(
                controls=[
                    Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.WHITE),
                    Text("", color=ft.Colors.WHITE, size=16),
                ],
                alignment=ft.MainAxisAlignment.CENTER
            ),
            visible=False,
            bgcolor=ft.Colors.BLUE,
            padding=15,
            height=50,
            alignment=ft.alignment.center,
        )
        
        # אתחול מנגנוני חיפוש
        self.file_index = None
        self.folder_path = None
        #self.search_options = SearchOptions()
        
        # בחירת תיקייה וחיפוש
        self.folder_picker = FilePicker(on_result=self.pick_folder_result)
        self.selected_folder = Text("לא נבחרה תיקייה")
        self.search_term = TextField(
            label="מילות חיפוש",
            width=400,
            prefix_icon=ft.Icons.SEARCH,
            on_submit=self.search_documents,
        )
        
        # רכיבי התקדמות
        self.index_progress = Container(
            content=Column(
                controls=[
                    ProgressRing(),
                    Text("", size=16, color=ft.Colors.BLUE)
                ],
                horizontal_alignment="center"
            ),
            alignment=ft.alignment.center,
            visible=False
        )
        
        self.search_progress = Container(
            content=Column(
                controls=[
                    ProgressRing(),
                    Text("מחפש...", size=16, color=ft.Colors.BLUE)
                ],
                horizontal_alignment="center"
            ),
            alignment=ft.alignment.center,
            visible=False
        )
        
        # יצירת תצוגות
        self.search_view = self.create_search_view()
        self.books_view = self.create_books_view()
        self.books_view.visible = False
        self.settings_view = self.create_settings_view()
        
        # סרגל ניווט
        self.navigation_bar = NavigationBar(
            destinations=[
                NavigationBarDestination(
                    icon=ft.Icons.SEARCH,
                    label="חיפוש",
                ),
                NavigationBarDestination(
                    icon=ft.Icons.BOOK,
                    label="ספרים",
                ),
                NavigationBarDestination(
                    icon=ft.Icons.SETTINGS,
                    label="הגדרות",
                ),
            ],
            on_change=self.navigation_change,
            selected_index=0,
        )

    def create_search_view(self):
        import flet as ft

        self.results_counter = ft.Text("", size=14, color=ft.Colors.BLUE_GREY)

            # פאנל הגדרות מתקדמות
        self.advanced_settings = ft.Container(
        content=self.build_advanced_settings_panel(),
            visible=False,
            padding=10,
            border_radius=8,
            bgcolor=ft.Colors.SURFACE,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.12, ft.Colors.BLACK),
            ),
            margin=10,
            alignment=ft.alignment.center_left
        )

        self.results_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=10,
        )
        self.results_container = ft.Container(
            content=ft.Column(
                controls=[
                    self.results_counter,
                    self.search_progress,
                    self.results_list
                ],
                expand=True
            ),
            expand=True,
            height=600
        )

        self.toggle_advanced_button = ft.IconButton(
            icon=ft.Icons.TUNE,
            tooltip="הגדרות מתקדמות",
            on_click=self.toggle_advanced_settings,
            bgcolor=ft.Colors.BLUE_GREY,
        )

        self.history_popup = ft.Container(
            content=ft.Column(
                controls=[],
                spacing=2,
                scroll=ft.ScrollMode.AUTO,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            bgcolor=ft.Colors.SURFACE,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=8,
            padding=ft.padding.symmetric(vertical=5),
            margin=ft.margin.only(top=5),
            visible=False,
            width=400,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
            ),
            right=20,
            top=100,
            alignment=ft.alignment.top_right,
        )

        def on_search_focus(e):
            self.history_popup.visible = True
            self.history_popup.content.controls = [
                self.create_history_item(term) for term in self.search_history.get_history()[:5]
            ]
            self.history_popup.update()

        def on_search_blur(e):
            import threading
            def hide():
                self.history_popup.visible = False
                self.history_popup.update()
            threading.Timer(0.15, hide).start()

        self.search_term = ft.TextField(
            hint_text="הקלד טקסט לחיפוש...",
            width=600,
            expand=False,
            on_focus=on_search_focus,
            on_blur=on_search_blur,
            on_submit=self.search_documents,
            border_radius=8,
            filled=True,
        )

        # קבוצה ימנית: שדה חיפוש + כפתור חיפוש + כפתור הגדרות
        right_controls = ft.Row([
            self.search_term,
            ft.IconButton(
                icon=ft.Icons.SEARCH,
                tooltip="חפש",
                on_click=self.search_documents
            ),
            self.toggle_advanced_button,
        ], spacing=10, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # שורת עליונה: חיפוש מימין, הגדרות מתקדמות משמאל
        top_row = ft.Row([
            right_controls,           # יישאר בימין (ב־RTL)
            self.advanced_settings,   # יופיע בצד שמאל, לא משנה ה־visible
        ], spacing=0, alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        main_column = ft.Column([
            ft.Text("חיפוש במסמכים", size=30, weight="bold"),
            top_row,
            self.results_container,
        ])

        return ft.Container(
            content=ft.Stack([
                main_column,
                self.history_popup,
            ]),
            expand=True,
            padding=20,
        )

    def create_index_list(self):
        """יצירת רשימת האינדקסים"""
        index_list = ft.Column(spacing=10)
        for idx in self.app_settings.settings.get('indexes', []):
            index_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.FOLDER),
                        ft.Column([
                            ft.Text(idx['name'], size=14, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                idx['path'], 
                                size=12, 
                                color=ft.Colors.GREY_500,
                                overflow=ft.TextOverflow.ELLIPSIS
                            )
                        ], expand=True),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            tooltip="מחק אינדקס",
                            data=idx['path'],
                            on_click=self.remove_index
                        )
                    ]),
                    padding=10,
                    border=ft.border.all(1, ft.Colors.OUTLINE),
                    border_radius=5,
                    bgcolor=ft.Colors.SURFACE
                )
            )
        return index_list    

    def update_search_setting(self, setting_name: str, value):
        """עדכון הגדרת חיפוש"""
        self.app_settings.settings[setting_name] = value
        self.app_settings.save_settings()
        
        # עדכון אפשרויות החיפוש
        if setting_name == 'search_filenames_only':
            self.search_options.search_in_path = value
        elif setting_name == 'exact_match':
            self.search_options.exact_match = value
        elif setting_name == 'min_word_count':
            self.search_options.min_word_count = value
        
        # ביצוע חיפוש מחדש אם יש מילות חיפוש
        if hasattr(self, 'search_term') and self.search_term.value:
            self.search_documents(None)

    def create_settings_view(self):
        """יצירת דף ההגדרות"""
        color_options = [
            ('#0078D4', 'כחול'),
            ('#107C10', 'ירוק'),
            ('#D83B01', 'כתום'),
            ('#E81123', 'אדום'),
            ('#744DA9', 'סגול'),
            ('#018574', 'טורקיז'),
            ('#C239B3', 'ורוד'),
        ]

        def create_color_button(color, is_selected):
            return ft.Container(
                content=ft.Container(
                    bgcolor=color,
                    width=30,
                    height=30,
                    border_radius=15,
                    border=ft.border.all(2, ft.Colors.BLACK if is_selected else "transparent"),
                ),
                on_click=lambda _: self.change_primary_color(color),
                padding=5,
            )

        # לשונית ניהול אינדקסים
        index_management = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("ניהול תיקיות אינדקס", size=16, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.FOLDER_OPEN,
                            tooltip="הוסף תיקייה",
                            on_click=lambda _: self.folder_picker.get_directory_path()
                        ),
                        ft.IconButton(
                            icon=ft.Icons.REFRESH,
                            tooltip="רענן אינדקס",
                            on_click=self.refresh_index
                        )
                    ]),
                    self.index_progress,
                    ft.Divider(),
                    ft.Text("אינדקסים קיימים:", size=14),
                    self.create_index_list(),
                ],
                scroll=ft.ScrollMode.AUTO  # מאפשר גלילה עבור תוכן ארוך
            ),
            padding=20
        )

        # לשונית הגדרות חיפוש
        search_settings = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("הגדרות חיפוש", size=16, weight=ft.FontWeight.BOLD),
                    ft.Text("בחר אינדקסים לחיפוש:", size=14),
                    self.create_index_checkbox_list(),
                    ft.Divider(),
                    ft.Text("אפשרויות חיפוש נוספות:", size=14),
                    ft.Container(
                        content=ft.Column([

                        ]),
                        padding=10
                    )
                ],
                scroll=ft.ScrollMode.AUTO  # מאפשר גלילה עבור תוכן ארוך
            ),
            padding=20
        )

        # לשונית עיצוב
        theme_settings = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("ערכת נושא", size=16, weight=ft.FontWeight.BOLD),
                    ft.RadioGroup(
                        content=ft.Column([
                            ft.Radio(value="light", label="בהיר"),
                            ft.Radio(value="dark", label="כהה"),
                            ft.Radio(value="system", label="לפי מערכת ההפעלה")
                        ]),
                        value=self.app_settings.get_setting('theme'),
                        on_change=self.change_theme
                    ),
                    ft.Divider(),
                    ft.Text("צבע ראשי", size=14),
                    ft.Row(
                        controls=[
                            create_color_button(
                                color,
                                color == self.app_settings.get_setting('primary_color')
                            ) for color, _ in color_options
                        ],
                        wrap=True,
                    ),
                    ft.Divider(),
                    ft.Text("גודל טקסט", size=14),
                    ft.Dropdown(
                        width=200,
                        value=self.app_settings.get_setting('font_size'),
                        options=[
                            ft.dropdown.Option("small", "קטן"),
                            ft.dropdown.Option("normal", "רגיל"),
                            ft.dropdown.Option("large", "גדול")
                        ],
                        on_change=self.change_font_size
                    )
                ],
                scroll=ft.ScrollMode.AUTO  # מאפשר גלילה עבור תוכן ארוך
            ),
            padding=20
        )

        # יצירת המכל הראשי עם כל הלשוניות
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Text("הגדרות", size=30, weight="bold"),
                    margin=ft.margin.only(bottom=20)
                ),
                ft.Tabs(
                    selected_index=0,
                    animation_duration=300,
                    tabs=[
                        ft.Tab(text="תיקיות אינדקס", content=index_management),
                        ft.Tab(text="הגדרות חיפוש", content=search_settings),
                        ft.Tab(text="עיצוב", content=theme_settings),
                    ],
                    expand=True
                )
            ]),
            visible=False,
            expand=True,
            padding=20
        )

    def setup_ui(self):
        self.create_views()
        self.main_stack = ft.Stack([
            self.search_view,
            self.books_view,
            self.settings_view,
        ], expand=True)
        self.main_container = ft.Container(
            content=ft.Column([
                self.main_stack,
                self.navigation_bar,
                self.message_container,
            ]),
            expand=True,
        )
        self.page.padding = 0
        self.page.spacing = 0
        self.page.overlay.append(self.folder_picker)
        self.page.add(self.main_container)

    def create_views(self):
        # כל פעם שמרעננים, בונים מחדש את כל ה־views!
        self.search_view = self.create_search_view()
        self.books_view = self.create_books_view()
        self.settings_view = self.create_settings_view()
        self.search_view.visible = self.navigation_bar.selected_index == 0
        self.books_view.visible = self.navigation_bar.selected_index == 1
        self.settings_view.visible = self.navigation_bar.selected_index == 2
        
    def refresh_all_views(self):
        # קרא את זה בכל שינוי אינדקס!
        self.create_views()
        self.main_stack.controls.clear()
        self.main_stack.controls.extend([
            self.search_view,
            self.books_view,
            self.settings_view,
        ])
        self.page.update()

    def show_history(self, e):
        """הצגת או הסתרת היסטוריית החיפושים"""
        # מחליף את המצב הנוכחי - אם מוצג מסתיר, אם מוסתר מציג
        self.history_popup.visible = not self.history_popup.visible
        self.history_popup.update()

    def hide_history(self, e):
        """הסתרת היסטוריית החיפושים"""
        self.history_popup.visible = False
        self.history_popup.update()
        
    def select_history_item(self, term):
        """בחירת פריט מההיסטוריה"""
        self.search_term.value = term
        self.search_term.update()
        self.history_popup.visible = False
        self.history_popup.update()
        self.search_documents(None)  # ביצוע חיפוש אוטומטי

    def remove_from_history(self, term):
        """הסרת פריט מההיסטוריה"""
        self.search_history.remove_item(term)
        # עדכון תצוגת ההיסטוריה
        self.history_popup.content.controls = [
            self.create_history_item(term) 
            for term in self.search_history.get_history()
        ]
        self.history_popup.update()

    def apply_theme_settings(self):
        """החלת הגדרות העיצוב"""
        try:
            # החלת ערכת נושא
            theme = self.app_settings.get_setting('theme', 'light')
            if theme == "dark":
                self.page.theme_mode = ThemeMode.DARK
            elif theme == "light":
                self.page.theme_mode = ThemeMode.LIGHT
            else:  # system
                self.page.theme_mode = ThemeMode.SYSTEM

            # החלת צבע ראשי
            primary_color = self.app_settings.get_setting('primary_color', '#0078D4')
            self.page.theme = Theme(color_scheme_seed=primary_color)
            
            # החלת גודל טקסט
            font_size = self.app_settings.get_setting('font_size', 'normal')
            font_sizes = {
                'small': 0.8,
                'normal': 1.0,
                'large': 1.2
            }
            self.font_scale = font_sizes.get(font_size, 1.0)
            
        except Exception as e:
            print(f"שגיאה בהחלת הגדרות עיצוב: {str(e)}")        

    def navigation_change(self, e):
        selected_index = e.control.selected_index

        self.search_view.visible = selected_index == 0
        self.books_view.visible = selected_index == 1
        self.settings_view.visible = selected_index == 2

        self.message_container.visible = False

        if selected_index == 1:
            books = []
            for idx in self.app_settings.get_selected_indexes():
                file_index = FileIndex(idx)
                for file_path, file_data in file_index.index.items():
                    if file_path.lower().endswith('.pdf'):
                        books.append((file_path, file_data))
            books.sort(key=lambda x: x[1]['filename'])
            books.sort(key=lambda x: x[1]['filename'])
            if books:
                if self.force_book_path:
                    self.select_book(self.force_book_path)
                    self.force_book_path = None  # אפס את הדגל אחרי הבחירה!
                else:
                    self.select_book(books[0][0])

        self.page.update()
    
    def update_search_options(self, e):
        """עדכון אפשרויות החיפוש"""
        controls = self.search_controls.controls
        self.search_options.exact_match = controls[0].value
        self.search_options.search_in_path = controls[1].value
        self.page.update()

    def update_file_filters(self, e):
        """עדכון סינון סוגי קבצים"""
        # עדכון אפשרויות החיפוש
        selected_types = []
        for checkbox in self.filter_panel.controls[1].content.controls:
            if checkbox.value:
                selected_types.append(checkbox.data)
        
        self.search_options.file_types = selected_types
        
        # ביצוע חיפוש מחדש אם יש מילות חיפוש
        if self.search_term.value:
            self.search_documents(None)
            
    def create_history_item(self, search_term):
        return ft.Container(
            content=ft.TextButton(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.HISTORY, size=16, color=ft.Colors.GREY_500),
                        margin=ft.margin.only(right=10)
                    ),
                    ft.Text(
                        search_term,
                        size=14,
                        expand=True,
                        no_wrap=True,
                        overflow=ft.TextOverflow.ELLIPSIS
                    ),
                    ft.Container(
                        content=ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            icon_size=16,
                            tooltip="הסר מההיסטוריה",
                            on_click=lambda e, term=search_term: self.remove_from_history(term)
                        ),
                        margin=ft.margin.only(left=10)
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                spacing=5
                ),
                # חיפוש מיידי בלחיצה!
                on_click=lambda _, term=search_term: self.select_history_item(term),
                style=ft.ButtonStyle(
                    padding=ft.padding.all(10),
                    bgcolor=ft.Colors.SURFACE,
                    shape=ft.RoundedRectangleBorder(radius=8),
                ),
                expand=True,
            ),
            padding=ft.padding.symmetric(horizontal=5),
            margin=ft.margin.only(bottom=2),
        )

    def select_history_item(self, term):
        self.search_term.value = term
        self.search_term.update()
        self.history_popup.visible = False
        self.history_popup.update()
        self.search_documents(None)  # חיפוש מיידי!

    def search_documents(self, e):
        """ביצוע חיפוש"""
        search_term = self.search_term.value
        if search_term and search_term.strip():
            self.search_history.add(search_term)
            self.history_popup.content.controls = [
                self.create_history_item(term) 
                for term in self.search_history.get_history()
            ]
            self.history_popup.update()
        
        self.results_list.controls.clear()
        self.results_counter.value = ""
        
        if not self.search_term.value:
            self.show_status("נא להזין טקסט לחיפוש", True)
            return

        self.search_progress.visible = True
        self.page.update()

        try:
            # קבלת האינדקסים הנבחרים
            selected_indexes = self.app_settings.get_selected_indexes()
            all_results = []
            for index_path in selected_indexes:
                file_index = FileIndex(index_path)
                results = file_index.search(self.search_term.value, self.search_options)
                all_results.extend(results)
            
            # סינון לפי סוג קובץ אם נבחרו סוגי קבצים
            if self.search_options.file_types:
                filtered_results = []
                for result in all_results:
                    for file_type in self.search_options.file_types:
                        if result['file_path'].lower().endswith(file_type.lower()):
                            filtered_results.append(result)
                            break
                all_results = filtered_results
            
            self.results_list.controls = [
                self.create_result_container(result)
                for result in all_results
            ]
            
            results_count = len(all_results)
            if results_count == 0:
                self.show_status(f"לא נמצאו תוצאות עבור '{self.search_term.value}'")
            else:
                self.results_counter.value = f"נמצאו {results_count} תוצאות"
                self.hide_status()
        
        finally:
            self.search_progress.visible = False
            self.page.update()

    def create_result_container(self, result):
        text = result['context']
        file_path = result['file_path']
        location = result.get('location', '')

        # בניית spans להדגשת מילות החיפוש
        spans = []
        last_end = 0
        search_words = self.search_term.value.split()
        text_lower = text.lower()
        word_positions = []
        for word in search_words:
            word_lower = word.lower()
            start = 0
            while True:
                pos = text_lower.find(word_lower, start)
                if pos == -1:
                    break
                # אם לא דורשים התאמה מדויקת, או שיש גבולות מילה
                if not self.search_options.exact_match or (
                    (pos == 0 or not text[pos-1].isalnum()) and
                    (pos + len(word) == len(text) or not text[pos + len(word)].isalnum())
                ):
                    word_positions.append((pos, pos + len(word)))
                start = pos + 1
        word_positions.sort()

        for start, end in word_positions:
            if start > last_end:
                spans.append(ft.TextSpan(text=text[last_end:start]))
            spans.append(ft.TextSpan(
                text=text[start:end],
                style=ft.TextStyle(
                    color=ft.Colors.RED,
                    weight=ft.FontWeight.BOLD
                )
            ))
            last_end = end

        if last_end < len(text):
            spans.append(ft.TextSpan(text=text[last_end:]))

        # אייקון עין לפתיחה מהירה
        preview_icon = ft.IconButton(
            icon=ft.Icons.VISIBILITY,
            icon_size=24,
            tooltip="תצוגה מקדימה/פתח במיקום",
            on_click=lambda e, file_path=file_path, location=location: self.open_book_at_search_result(file_path, location)
        )

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.DESCRIPTION, color=ft.Colors.BLUE),
                    ft.Text(f"{result['filename']} ({location})", size=16, weight=ft.FontWeight.BOLD, expand=True),
                    preview_icon,
                ]),
                ft.Container(
                    content=ft.SelectionArea(
                        content=ft.Text(spans=spans)
                    ),
                    margin=ft.margin.only(left=20, top=5),
                    bgcolor=ft.Colors.BLUE_50,
                    padding=10,
                    border_radius=5,
                    expand=True,
                    on_click=lambda e: self.open_book_at_search_result(file_path, location)
                )
            ], expand=True),
            bgcolor=ft.Colors.WHITE,
            padding=10,
            border_radius=10,
            border=ft.border.all(1, ft.Colors.BLUE_GREY_200),
            expand=True
        )

    def copy_to_clipboard(self, text: str):
        """העתקת טקסט ללוח"""
        self.page.set_clipboard(text)
        self.show_status("הטקסט הועתק ללוח")

    def open_file_at_specific_location(self, file_path: str, location: str = ""):
        """פותח את הקובץ במיקום הספציפי"""
        try:
            if file_path.lower().endswith('.pdf'):
                self.open_pdf_at_location(file_path, location)
            elif file_path.lower().endswith('.docx'):
                if platform.system() == 'Windows':
                    subprocess.Popen(['start', '', file_path], shell=True)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.Popen(['open', file_path])
                else:  # Linux
                    subprocess.Popen(['xdg-open', file_path])
            else:  # טקסט או קבצים אחרים
                self.open_text_at_location(file_path, location)
                
            self.show_status("הקובץ נפתח בהצלחה")
        except Exception as e:
            self.show_status(f"שגיאה בפתיחת הקובץ: {str(e)}", True)

    def open_pdf_at_location(self, file_path: str, location: str):
        """פותח קובץ PDF בעמוד ספציפי"""
        try:
            # חילוץ מספר העמוד מהמיקום
            page_num = int(location.replace("עמוד ", "")) - 1 if location else 0
            
            if platform.system() == 'Windows':
                # שימוש ב-SumatraPDF אם קיים
                sumatra_path = r"C:\Program Files\SumatraPDF\SumatraPDF.exe"
                if os.path.exists(sumatra_path):
                    subprocess.Popen(['start', '', sumatra_path, '-page', str(page_num + 1), file_path], shell=True)
                    return
                    
                # אחרת, שימוש ב-Adobe Reader
                adobe_path = r"C:\Program Files (x86)\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe"
                if os.path.exists(adobe_path):
                    subprocess.Popen(['start', '', adobe_path, '/A', f'page={page_num+1}', file_path], shell=True)
                    return
                
                # אם אין תוכנה ייעודית, פתיחה רגילה
                subprocess.Popen(['start', '', file_path], shell=True)
                
            elif platform.system() == 'Darwin':  # macOS
                subprocess.Popen(['open', '-a', 'Preview', file_path])
            else:  # Linux
                subprocess.Popen(['xdg-open', file_path])
                
        except Exception as e:
            print(f"שגיאה בפתיחת PDF: {str(e)}")
            # אם נכשל, פתיחה רגילה
            if platform.system() == 'Windows':
                subprocess.Popen(['start', '', file_path], shell=True)
            elif platform.system() == 'Darwin':
                subprocess.Popen(['open', file_path])
            else:
                subprocess.Popen(['xdg-open', file_path])

    def open_text_at_location(self, file_path: str, location: str = ""):
        """פותח קובץ טקסט בחלק הספציפי"""
        try:
            if platform.system() == 'Windows':
                # נסה לפתוח עם Notepad++
                notepad_path = r"C:\Program Files\Notepad++\notepad++.exe"
                if os.path.exists(notepad_path):
                    # חילוץ מספר השורה/חלק
                    if location and "חלק" in location:
                        chunk = int(location.replace("חלק ", ""))
                        # חישוב מיקום משוער בקובץ
                        line_num = (chunk - 1) * 200 + 1
                    else:
                        line_num = 1
                    
                    subprocess.Popen(['start', '', notepad_path, '-n' + str(line_num), file_path], shell=True)
                    return
                
                # אם אין Notepad++, פתיחה רגילה
                subprocess.Popen(['start', '', file_path], shell=True)
            elif platform.system() == 'Darwin':
                subprocess.Popen(['open', '-a', 'TextEdit', file_path])
            else:
                subprocess.Popen(['xdg-open', file_path])
                
        except Exception as e:
            print(f"שגיאה בפתיחת קובץ טקסט: {str(e)}")
            # אם נכשל, פתיחה רגילה
            if platform.system() == 'Windows':
                subprocess.Popen(['start', '', file_path], shell=True)
            elif platform.system() == 'Darwin':
                subprocess.Popen(['open', file_path])
            else:
                subprocess.Popen(['xdg-open', file_path])

    def update_progress(self, current, total):
        """עדכון התקדמות האינדוקס"""
        self.index_progress.content.controls[1].value = f"מאנדקס {current}/{total} קבצים..."
        self.page.update()

    def pick_folder_result(self, e):
        # ... כל הקוד שלך ...
        if e.path:
            self.folder_path = e.path
            folder_name = os.path.basename(e.path)
            self.app_settings.add_index(e.path)
            file_index = FileIndex(e.path)
            try:
                if file_index.needs_update():
                    self.show_status("מאנדקס קבצים...")
                    self.index_progress.visible = True
                    self.page.update()
                    file_index.update_index(callback=self.update_progress)
                    self.index_progress.visible = False
                    self.show_status(f"האינדקס הושלם")
                else:
                    self.show_status(f"נטען אינדקס קיים")
            except Exception as e:
                self.show_status(f"שגיאה בעדכון האינדקס: {str(e)}", True)
            self.refresh_all_views()  # במקום self.settings_view = ...; self.page.update()
    def remove_index(self, e):
        path = e.control.data
        self.app_settings.remove_index(path)
        file_index = FileIndex(path)
        file_index.delete_index_file()
        self.refresh_all_views()

    def refresh_index(self, e=None):
        """מרענן את כל האינדקסים"""
        indexes = self.app_settings.settings.get('indexes', [])
        for idx in indexes:
            file_index = FileIndex(idx['path'])
            if file_index.needs_update():
                self.show_status(f"מעדכן אינדקס: {idx['name']}")
                self.index_progress.visible = True
                self.page.update()
                file_index.update_index(callback=self.update_progress)
                self.index_progress.visible = False
                self.show_status(f"האינדקס {idx['name']} עודכן בהצלחה")
        self.page.update()


    def create_index_checkbox_list(self):
        """יצירת רשימת תיבות סימון לאינדקסים לחיפוש"""
        import flet as ft
        from flet import Column, Container, Row, Checkbox, Icon, Text, border

        checkbox_list = Column(spacing=10)
        selected_indexes = self.app_settings.settings.get('selected_indexes', [])

        for idx in self.app_settings.settings['indexes']:
            is_selected = idx['path'] in selected_indexes
            checkbox_list.controls.append(
                Container(
                    content=Row([
                        Checkbox(
                            value=is_selected,
                            data=idx['path'],
                            on_change=self.toggle_index_selection
                        ),
                        Icon(ft.Icons.FOLDER),
                        Text(idx['name'], expand=True),
                        Text(idx['path'], color=ft.Colors.GREY_500, size=12),
                    ]),
                    padding=10,
                    border=border.all(1, ft.Colors.BLUE_GREY_200),
                    border_radius=5
                )
            )

        if not checkbox_list.controls:
            checkbox_list.controls.append(
                Text("אין אינדקסים מוגדרים", color=ft.Colors.GREY_500)
            )
        return checkbox_list

    def toggle_index_selection(self, e):
        """טיפול בשינוי בחירת אינדקס"""
        index_path = e.control.data
        selected_indexes = self.app_settings.settings.get('selected_indexes', [])

        if e.control.value:  # אם האינדקס נבחר
            if index_path not in selected_indexes:
                selected_indexes.append(index_path)
        else:  # אם האינדקס בוטל
            if index_path in selected_indexes:
                selected_indexes.remove(index_path)

        self.app_settings.settings['selected_indexes'] = selected_indexes
        self.app_settings.save_settings()
        self.update_search_indexes()  # אופציונלי: עדכון לוגיקת מנוע החיפוש  

    def show_status(self, message, is_error=False):
        """הצגת הודעת סטטוס עם טיימר"""
        if hasattr(self, 'status_timer') and self.status_timer:
            self.status_timer.cancel()
            self.status_timer = None

        self.message_container.bgcolor = ft.Colors.RED if is_error else ft.Colors.BLUE
        self.message_container.content.controls[1].value = message
        self.message_container.visible = True
        self.page.update()

        if not is_error:
            self.status_timer = Timer(3.0, self.hide_status)
            self.status_timer.start()

    def update_search_indexes(self):
        """עדכון האינדקסים לחיפוש במנוע החיפוש"""
        selected_indexes = self.app_settings.settings.get('selected_indexes', [])
        # אם אין אינדקסים נבחרים, נשתמש בכל האינדקסים
        if not selected_indexes:
            selected_indexes = [idx['path'] for idx in self.app_settings.settings['indexes']]
        
        # כאן נעדכן את הלוגיקה של החיפוש לפי האינדקסים שנבחרו
        self.search_options.selected_indexes = selected_indexes            

    def hide_status(self, e=None):
        """הסתרת הודעת סטטוס"""
        if hasattr(self, 'status_timer') and self.status_timer:
            self.status_timer.cancel()
            self.status_timer = None
        
        if hasattr(self, 'message_container'):
            self.message_container.visible = False
            self.page.update()

    def change_theme(self, e):
        """שינוי ערכת הנושא"""
        theme = e.control.value
        if theme == "dark":
            self.page.theme_mode = ThemeMode.DARK
        elif theme == "light":
            self.page.theme_mode = ThemeMode.LIGHT
        else:  # system
            self.page.theme_mode = ThemeMode.SYSTEM
        
        self.app_settings.settings['theme'] = theme
        self.app_settings.save_settings()
        self.page.update()

    def change_primary_color(self, color):
        self.app_settings.settings['primary_color'] = color
        self.app_settings.save_settings()
        self.page.theme = Theme(color_scheme_seed=color)
        self.page.update()
    
    def change_font_size(self, e):
        """שינוי גודל הטקסט"""
        self.app_settings.settings['font_size'] = e.control.value
        self.app_settings.save_settings()
        self.page.update()

    def open_file_at_location(self, file_path: str):
        """פותח את הקובץ בתוכנת ברירת המחדל של המערכת"""
        try:
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', file_path], check=True)
            else:  # Linux
                subprocess.run(['xdg-open', file_path], check=True)
                
            self.show_status("הקובץ נפתח בהצלחה")
        except Exception as e:
            self.show_status(f"שגיאה בפתיחת הקובץ: {str(e)}", True)

                
    def open_book_at_search_result(self, file_path: str, location: str = ""):
        print(f"DEBUG: open_book_at_search_result called with file_path={file_path} location={location}")
        self.force_book_path = file_path  # כדי ש-navigation_change יידע מה לבחור

        # מעבר כרטיסייה + עדכון תצוגה
        self.navigation_bar.selected_index = 1
        self.navigation_bar.update()

        # קריאה ידנית ל-navigation_change כדי להפעיל את הלוגיקה (כמו שהסברנו קודם)
        class DummyEvent:
            def __init__(self, control):
                self.control = control

        self.navigation_change(DummyEvent(self.navigation_bar))

        # קפיצה לעמוד
        if location and "עמוד" in location:
            try:
                page_num = int(location.replace("עמוד", "").strip()) - 1
                if 0 <= page_num < len(self.current_book_pages):
                    self.current_page_index = page_num
                    self.update_book_page()
            except Exception as ex:
                print(f"שגיאה במעבר לעמוד: {ex}")

        self.page.update()
                        

    def create_books_view(self):
        import flet as ft

        # ודא אתחול משתנים קריטיים
        if not hasattr(self, "current_book_path"):
            self.current_book_path = None
        if not hasattr(self, "current_book_pages"):
            self.current_book_pages = []
        if not hasattr(self, "current_page_index"):
            self.current_page_index = 0

        # --- איסוף כל הספרים מכל האינדקסים הנבחרים ---
        self.books = []
        for idx in self.app_settings.get_selected_indexes():
            file_index = FileIndex(idx)
            for file_path, file_data in file_index.index.items():
                if file_path.lower().endswith('.pdf'):
                    self.books.append((file_path, file_data))
        self.books.sort(key=lambda x: x[1]['filename'])

        self.book_title = ft.Text('', size=22, weight='bold', color=ft.Colors.PRIMARY)
        self.page_indicator = ft.Text('', size=15, color=ft.Colors.BLUE_GREY_700)
        self.book_page_text = ft.Text(
            '', selectable=True, size=16, max_lines=50,
            overflow=ft.TextOverflow.ELLIPSIS, color=ft.Colors.BLACK,
            text_align=ft.TextAlign.RIGHT,
        )

        # בניית רשימת ספרים עם שורה אחת לכל PDF
        def build_books_buttons():
            controls = []
            if not self.books:
                controls.append(
                    ft.Text(
                        "לא נמצאו ספרים במערכת",
                        size=16,
                        color=ft.Colors.ERROR,
                        text_align=ft.TextAlign.CENTER,
                    )
                )
            else:
                for file_path, file_data in self.books:
                    selected = file_path == self.current_book_path
                    controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.BOOKMARK_BORDER, color=ft.Colors.BLUE_400, size=18),
                                ft.Text(
                                    file_data['filename'],
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                    size=15,
                                    expand=True,
                                ),
                            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                            height=38,
                            bgcolor=ft.Colors.BLUE_50 if selected else ft.Colors.SURFACE,
                            border_radius=7,
                            padding=ft.padding.symmetric(horizontal=10, vertical=0),
                            ink=True,
                            on_click=lambda e, path=file_path: self.select_book(path),
                            alignment=ft.alignment.center_left,
                            border=ft.border.all(1, ft.Colors.with_opacity(0.025, ft.Colors.BLUE)) if selected else None,
                        )
                    )
            return controls

        self.build_books_buttons = build_books_buttons

        self.books_column = ft.Column(
            controls=self.build_books_buttons(),
            scroll=ft.ScrollMode.AUTO,
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            expand=True,
        )

        books_list_container = ft.Container(
            content=self.books_column,
            bgcolor=ft.Colors.SURFACE,
            border_radius=10,
            padding=ft.padding.all(10),
            width=230,
            expand=False,
            alignment=ft.alignment.top_center,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            shadow=ft.BoxShadow(
                spread_radius=0.5,
                blur_radius=6,
                color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK)
            ),
            margin=ft.margin.only(top=8, left=8, bottom=8, right=4)
        )

        # כפתורי דפדוף עמודים
        def prev_page(e=None):
            if self.current_book_pages and self.current_page_index > 0:
                self.current_page_index -= 1
                self.update_book_page()

        def next_page(e=None):
            if self.current_book_pages and self.current_page_index < len(self.current_book_pages) - 1:
                self.current_page_index += 1
                self.update_book_page()

        self.prev_page_btn = ft.IconButton(
            icon=ft.Icons.KEYBOARD_ARROW_UP,
            tooltip="עמוד קודם",
            icon_size=22,
            bgcolor=ft.Colors.BLUE_50,
            on_click=prev_page,
            disabled=True,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12))
        )
        self.next_page_btn = ft.IconButton(
            icon=ft.Icons.KEYBOARD_ARROW_DOWN,
            tooltip="עמוד הבא",
            icon_size=22,
            bgcolor=ft.Colors.BLUE_50,
            on_click=next_page,
            disabled=True,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12))
        )

        left_panel = ft.Container(
            content=ft.Column([
                self.book_title,
                ft.Divider(height=1),
                self.page_indicator,
                ft.Row([self.prev_page_btn], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(
                    self.book_page_text,
                    expand=True,
                    padding=20,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=7,
                    border=ft.border.all(1, ft.Colors.with_opacity(0.08, ft.Colors.BLUE)),
                    shadow=ft.BoxShadow(
                        spread_radius=0.5,
                        blur_radius=6,
                        color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK)
                    ),
                    alignment=ft.alignment.center,
                ),
                ft.Row([self.next_page_btn], alignment=ft.MainAxisAlignment.CENTER),
            ], expand=True, alignment=ft.MainAxisAlignment.START, spacing=11),
            expand=True,
            padding=ft.padding.all(10),
            bgcolor=ft.Colors.SURFACE,
            border_radius=10,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            shadow=ft.BoxShadow(
                spread_radius=0.5,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.07, ft.Colors.BLACK)
            ),
            margin=ft.margin.only(top=8, right=8, bottom=8, left=4)
        )

        vertical_divider = ft.Container(
            content=ft.VerticalDivider(
                width=1,
                color=ft.Colors.OUTLINE,
                thickness=1,
            ),
            margin=ft.margin.symmetric(vertical=12)
        )

        main_view = ft.Container(
            content=ft.Column([
                ft.Text("חיפוש בספרים", size=30, weight="bold"),
                ft.Divider(height=3),
                ft.Row([
                    books_list_container,
                    vertical_divider,
                    left_panel
                ], expand=True, spacing=0, alignment=ft.MainAxisAlignment.START)
            ], expand=True, spacing=5),
            padding=ft.padding.all(6),
            bgcolor=ft.Colors.SURFACE,
            expand=True
        )

        # --- עדכון רשימת הספרים ---
        def update_books_buttons():
            self.books_column.controls = self.build_books_buttons()
            self.books_column.update()

        self.update_books_buttons = update_books_buttons

        def update_nav_buttons():
            self.prev_page_btn.disabled = (self.current_page_index == 0)
            self.next_page_btn.disabled = (
                not self.current_book_pages or self.current_page_index >= len(self.current_book_pages) - 1
            )
            self.prev_page_btn.update()
            self.next_page_btn.update()

        self.update_nav_buttons = update_nav_buttons

        def select_book(file_path):
            file_data = None
            # עבור על כל האינדקסים הנבחרים
            for idx in self.app_settings.get_selected_indexes():
                file_index = FileIndex(idx)
                if file_path in file_index.index:
                    file_data = file_index.index.get(file_path)
                    break

            if not file_data:
                self.book_title.value = "לא נמצא ספר"
                self.book_page_text.value = ""
                self.page_indicator.value = ""
                self.current_book_path = None
                self.current_book_pages = []
            else:
                self.current_book_path = file_path
                self.current_book_pages = [page['content'] for page in file_data['contents']]
                self.current_page_index = 0
                self.book_title.value = file_data['filename']
                self.update_book_page()
            self.update_books_buttons()
            self.update_nav_buttons()
            self.page.update()

        self.select_book = select_book

        def update_book_page():
            if not self.current_book_pages:
                self.book_page_text.value = ""
                self.page_indicator.value = ""
            else:
                self.book_page_text.value = self.current_book_pages[self.current_page_index]
                self.page_indicator.value = f"עמוד {self.current_page_index + 1} מתוך {len(self.current_book_pages)}"
            self.book_page_text.update()
            self.page_indicator.update()
            self.update_nav_buttons()

        self.update_book_page = update_book_page

        return main_view

    def build_advanced_settings_panel(self):
        import flet as ft
        return ft.Column([
            self.create_file_type_buttons_row(),
            ft.Switch(
                label="חיפוש בשמות קבצים בלבד",
                value=self.app_settings.get_setting('search_filenames_only', False),
                on_change=lambda e: self.update_search_setting('search_filenames_only', e.control.value)
            ),
            ft.Switch(
                label="התאמה מדויקת",
                value=self.app_settings.get_setting('exact_match', False),
                on_change=lambda e: self.update_search_setting('exact_match', e.control.value)
            ),
        ])

def main(page: Page):
    app = DocumentSearchApp(page)

if __name__ == '__main__':
    ft.app(target=main)
