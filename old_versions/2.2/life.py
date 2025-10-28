# Life | Lifeness Simulator | MJ

# Utilities
from __future__ import annotations
import os
import sys
import time
import math
import logging
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass, field
from PIL import Image, ImageSequence
from typing import List, Optional, Dict
from datetime import datetime
from platformdirs import user_documents_dir

# GUI, OpenGL
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QPushButton, QListWidget, QTextEdit, QHBoxLayout, QVBoxLayout, QSplitter, QSlider, QMessageBox,QDialog, QFormLayout, QComboBox)
from PySide6.QtGui import QFont, QAction, QIcon
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *

# DOCX
from docx import Document
from docx.shared import Pt

# ---------------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
BASE_LOG = user_documents_dir()
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LOGS_DIR = os.path.join(BASE_LOG, "Lifeness Simulator/logs")
EXPORT_DIR = os.path.join(BASE_DIR, "export")

os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOGS_DIR, "life_log.log")
logger = logging.getLogger("lifeness")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    fh = RotatingFileHandler(LOG_FILE, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)
logger.info("Launching Lifeness Simulator ..")

# ---------------------------------------------------------------------------
@dataclass
class Enfermedad:
    id: str
    nombre: str
    categoria: str
    descripcion: str
    origen: Optional[str] = None
    transmision: Optional[str] = None
    prevencion: Optional[str] = None
    tratamiento: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

@dataclass
class MetaProyecto:
    titulo: str = "Lifeness Simulator"
    autores: str = "A Biomedic app made by the Lifeness Project Team."
    version: str = "2.1"
    fecha: str = "2025-09-10"
    idioma: str = "es"
    descripcion: str = "Simulation that transforms"

# ---------------------------------------------------------------------------
class OBJ:
    def __init__(self, filename: str):
        self.filename = filename
        self.vertices: List[List[float]] = []
        self.normals: List[List[float]] = []
        self.texcoords: List[List[float]] = []
        self.faces: List[List[tuple]] = []
        self.gl_list = None
        if os.path.isfile(filename):
            try:
                self._load_file(filename)
                logger.info("OBJ Success: %s (v:%d f:%d)", filename, len(self.vertices), len(self.faces))
            except Exception as e:
                logger.exception("Error OBJ %s: %s", filename, e)
        else:
            logger.warning("OBJ not found: %s", filename)

    def _load_file(self, filename: str):
        with open(filename, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                parts = line.strip().split()
                if not parts:
                    continue
                if parts[0] == 'v' and len(parts) >= 4:
                    self.vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
                elif parts[0] == 'vn' and len(parts) >= 4:
                    self.normals.append([float(parts[1]), float(parts[2]), float(parts[3])])
                elif parts[0] == 'vt' and len(parts) >= 3:
                    self.texcoords.append([float(parts[1]), float(parts[2])])
                elif parts[0] == 'f':
                    face = []
                    for v in parts[1:]:
                        vals = v.split('/')
                        vi = int(vals[0]) - 1 if vals[0] else -1
                        ti = int(vals[1]) - 1 if len(vals) > 1 and vals[1] else -1
                        ni = int(vals[2]) - 1 if len(vals) > 2 and vals[2] else -1
                        face.append((vi, ti, ni))
                    self.faces.append(face)

    def create_gl_list(self):
        if self.gl_list is not None:
            return
        try:
            self.gl_list = glGenLists(1)
            glNewList(self.gl_list, GL_COMPILE)
            glEnable(GL_NORMALIZE)
            for face in self.faces:
                if len(face) == 3:
                    glBegin(GL_TRIANGLES)
                    for (vi, ti, ni) in face:
                        if ni >= 0 and ni < len(self.normals):
                            glNormal3fv(self.normals[ni])
                        if ti >= 0 and ti < len(self.texcoords):
                            glTexCoord2fv(self.texcoords[ti])
                        if vi >= 0 and vi < len(self.vertices):
                            glVertex3fv(self.vertices[vi])
                    glEnd()
                else:
                    glBegin(GL_POLYGON)
                    for (vi, ti, ni) in face:
                        if ni >= 0 and ni < len(self.normals):
                            glNormal3fv(self.normals[ni])
                        if ti >= 0 and ti < len(self.texcoords):
                            glTexCoord2fv(self.texcoords[ti])
                        if vi >= 0 and vi < len(self.vertices):
                            glVertex3fv(self.vertices[vi])
                    glEnd()
            glEndList()
        except Exception as e:
            logger.exception("Error making GL Lists %s: %s", self.filename, e)
            try:
                if self.gl_list:
                    glDeleteLists(self.gl_list, 1)
                self.gl_list = None
            except Exception:
                pass

    def render(self):
        if self.gl_list is None:
            self.create_gl_list()
        if self.gl_list:
            try:
                glCallList(self.gl_list)
            except Exception as e:
                logger.exception("Error en glCallList: %s", e)

# ---------------------------------------------------------------------------
class GLHumanWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model_male_path = os.path.join("assets/humans", "male.obj")
        self.model_female_path = os.path.join("assets/humans", "female.obj")
        self.model_male = OBJ(self.model_male_path) if os.path.isfile(self.model_male_path) else None
        self.model_female = OBJ(self.model_female_path) if os.path.isfile(self.model_female_path) else None
        self.current_model = self.model_male or self.model_female
        self.yaw = 0.0
        self.last_mouse_x = None
        self.zoom = -6.0
        self.bg_black = True
        self.reaction_id: Optional[str] = None
        self.reaction_start = 0.0
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(30)

        # Fondo animado (GIF)
        self.bg_frames = []
        self.bg_index = 0
        self.last_frame_time = time.time()
        self.frame_delay = 0.1
    
    def mousePressEvent(self, event):
        try:
            self.last_mouse_x = event.position().x()
        except AttributeError:
            self.last_mouse_x = event.x()

    def mouseMoveEvent(self, event):
        try:
            cur_x = event.position().x()
        except AttributeError:
            cur_x = event.x()
        if self.last_mouse_x is None:
            self.last_mouse_x = cur_x
            return
        dx = cur_x - self.last_mouse_x
        self.yaw += dx * 0.3
        self.yaw = self.yaw % 360
        self.last_mouse_x = cur_x
        self.update()

    def mouseReleaseEvent(self, event):
        self.last_mouse_x = None

    def wheelEvent(self, event):
        # soporta PySide6: event.angleDelta().y()
        delta = event.angleDelta().y() / 120.0
        self.zoom += delta * 0.6
        self.zoom = max(-20.0, min(-2.0, self.zoom))
        self.update()

    def mouseDoubleClickEvent(self, event):
        self.bg_black = not self.bg_black
        self.update()

    # OpenGL lifecycle
    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, [4.0, 4.0, 10.0, 1.0])
        glEnable(GL_COLOR_MATERIAL)

        gif_path = os.path.join(ASSETS_DIR, "backgrounds", "bg.gif")
        if not os.path.isfile(gif_path):
            # intentar ruta base assets
            gif_path = os.path.join(ASSETS_DIR, "backgrounds", "bg.gif")
        if os.path.isfile(gif_path):
            try:
                self.load_gif(gif_path)
            except Exception as e:
                logger.warning("GIF not loaded: %s", e)
                self.bg_frames = []
        else:
            logger.info("GIF not found")
            self.bg_frames = []
        logger.debug("Launching Life")

    def load_gif(self, path):
        if not os.path.isfile(path):
            logger.warning("load_gif: file doesn't exists: %s", path)
            return
        gif = Image.open(path)
        self.bg_frames = []
        for frame in ImageSequence.Iterator(gif):
            frame = frame.convert("RGB")
            img_data = frame.tobytes("raw", "RGB", 0, -1)
            tex_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, frame.width, frame.height, 0, GL_RGB, GL_UNSIGNED_BYTE, img_data)
            self.bg_frames.append(tex_id)
        logger.info("Correctly backgrounds loaded with %d frames.", len(self.bg_frames))

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h if h > 0 else 1)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(50.0, w / max(1.0, h), 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if self.bg_frames:
            glDisable(GL_DEPTH_TEST)
            glDisable(GL_LIGHTING)
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()
            glLoadIdentity()
            glOrtho(-1, 1, -1, 1, -1, 1)
            glMatrixMode(GL_MODELVIEW)
            glPushMatrix()
            glLoadIdentity()

            glEnable(GL_TEXTURE_2D)

            now = time.time()
            if now - self.last_frame_time > self.frame_delay:
                self.bg_index = (self.bg_index + 1) % len(self.bg_frames)
                self.last_frame_time = now

            tex = self.bg_frames[self.bg_index]
            glBindTexture(GL_TEXTURE_2D, tex)
            glBegin(GL_QUADS)
            glTexCoord2f(0, 0); glVertex2f(-1, -1)
            glTexCoord2f(1, 0); glVertex2f(1, -1)
            glTexCoord2f(1, 1); glVertex2f(1, 1)
            glTexCoord2f(0, 1); glVertex2f(-1, 1)
            glEnd()
            glDisable(GL_TEXTURE_2D)

            glPopMatrix()
            glMatrixMode(GL_PROJECTION)
            glPopMatrix()
            glMatrixMode(GL_MODELVIEW)
        else:
            # fondo sólido
            glClearColor(0.05, 0.05, 0.06, 1.0)

        # --- Modelo 3D encima del fondo ---
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, self.zoom)
        glRotatef(self.yaw, 0.0, 1.0, 0.0)

        # efecto reacción pulsante
        alpha = 0.0
        if self.reaction_id:
            t = time.time() - self.reaction_start
            alpha = 0.25 + 0.5 * (0.5 + 0.5 * math.sin(t * 5.0))

        if alpha > 0:
            glColor3f(1.0, 0.6 * (1 - alpha), 0.6 * (1 - alpha))
        else:
            glColor3f(0.9, 0.88, 0.85)

        # render modelo con fallback seguro
        try:
            if self.current_model:
                self.current_model.render()
            else:
                self._draw_placeholder_human()
        except Exception as e:
            logger.exception("Error al renderizar modelo GL: %s", e)
            self._draw_placeholder_human()

    def _draw_placeholder_human(self):
        glPushMatrix()
        glTranslatef(0.0, 0.6, 0.0)
        quad = gluNewQuadric()
        gluSphere(quad, 0.25, 16, 12)
        gluDeleteQuadric(quad)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0.0, -0.25, 0.0)
        glScalef(1.0, 1.6, 0.5)
        self._draw_cube(0.4)
        glPopMatrix()

    def _draw_cube(self, s):
        glBegin(GL_QUADS)
        glVertex3f(-s, -s, s)
        glVertex3f(s, -s, s)
        glVertex3f(s, s, s)
        glVertex3f(-s, s, s)
        glVertex3f(-s, -s, -s)
        glVertex3f(-s, s, -s)
        glVertex3f(s, s, -s)
        glVertex3f(s, -s, -s)
        glEnd()

    def apply_reaction(self, enfermedad_id: Optional[str]):
        self.reaction_id = enfermedad_id
        if enfermedad_id:
            self.reaction_start = time.time()
        self.update()

    def set_gender_model(self, gender: str):
        if gender.lower().startswith("m") and self.model_male:
            self.current_model = self.model_male
        elif gender.lower().startswith("f") and self.model_female:
            self.current_model = self.model_female
        self.update()

# ---------------------------------------------------------------------------
class SettingsDialog(QDialog):
    def __init__(self, parent=None, current_lang="es"):
        super().__init__(parent)
        self.setWindowTitle("Ajustes")
        self.resize(450, 200) # Ancho, Alto
        layout = QFormLayout(self)
        self.sldr_brightness = QSlider(QtCore.Qt.Horizontal)
        self.sldr_brightness.setRange(0, 100); self.sldr_brightness.setValue(50)
        self.sldr_contrast = QSlider(QtCore.Qt.Horizontal)
        self.sldr_contrast.setRange(0, 100); self.sldr_contrast.setValue(50)
        self.chk_fullscreen = QtWidgets.QCheckBox("Pantalla completa")
        self.cmb_lang = QComboBox()
        self.cmb_lang.addItems(["Español", "English"])
        self.cmb_lang.setCurrentText(current_lang)
        layout.addRow("Brillo", self.sldr_brightness)
        layout.addRow("Contraste", self.sldr_contrast)
        layout.addRow(self.chk_fullscreen)
        layout.addRow("Idioma", self.cmb_lang)
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def values(self):
        return {
            "brightness": self.sldr_brightness.value(),
            "contrast": self.sldr_contrast.value(),
            "fullscreen": self.chk_fullscreen.isChecked(),
            "lang": self.cmb_lang.currentText()
        }

# ---------------------------------------------------------------------------
class ReportGenerator:
    def __init__(self, meta: MetaProyecto, enfermedades: List[Enfermedad]):
        self.meta = meta
        self.enfermedades = enfermedades

        # Carpeta universal de documentos
        documents_dir = user_documents_dir()
        self.output_dir = os.path.join(documents_dir, "Lifeness Simulator/Reports")
        logger.info("Success!. Report saved correctly in Documents.")
        os.makedirs(self.output_dir, exist_ok=True)

        # Plantilla incluida en el exe (gracias a resource_path)
        self.out_path = os.path.join(self.output_dir, f"Life Report.docx")

    def generate(self) -> str:
        doc = Document("life_report_template.docx")
        today = datetime.today().strftime("%Y-%m-%d")

        # Ejemplo: reemplazo de campos "-" en tablas
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip() == "-":
                        if "Fecha" in row.cells[0].text:
                            cell.text = today
                        elif "enfermedades" in row.cells[0].text.lower():
                            cell.text = "\n".join([e.nombre for e in self.enfermedades[:5]])
                        else:
                            cell.text = "OK"
        doc.save(self.out_path)
        return self.out_path

# ---------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self, parser, meta: MetaProyecto):
        super().__init__()
        self.parser = parser
        self.meta = meta

        self.setWindowTitle("Life")
        ico_path = os.path.join(ASSETS_DIR, "icons", "ico1.ico")
        self.setWindowIcon(QIcon(ico_path))

        # Estilo global para toda la app usado mediante la propiedad setStyleSheet
        self.setStyleSheet("""
            QPushButton{
                background-color: #0078D7;
                color: white;
                font: bold 10pt "Segoe UI";
                border-radius: 10px;
                padding: 8px 16px;
            }
            QPushButton:hover{
                background-color: #1493FF;
            }
            QPushButton:pressed{
                background-color: #005A9E;
            }
            QLabel{
                font: 10pt "Segoe UI";
            }
        """)

        # MENÚ SUPERIOR
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar{
                background-color: #1E1E1E;
                color: white;
                font: bold 11pt "Segoe UI";
            }
            QMenuBar::item:selected{
                background-color: #0078D7;
            }
            QMenu{
                background-color: #2D2D2D;
                color: white;
                font: 10pt "Segoe UI";
            }
            QMenu::item:selected{
                background-color: #0078D7;
            }
        """)

        menu_first = menubar.addMenu("☰  Analisis") # MENÚ1
        # Subopciones
        first_report = QAction("Guardar Reporte", self)
        first_report.triggered.connect(self.generate_report)

        menu_second = menubar.addMenu("☰ Preferencias") # MENÚ2
        # Subopciones
        sec_ajustes = QAction("Ajustes", self)
        sec_ajustes.triggered.connect(self.show_settings)

        menu_third = menubar.addMenu("☰ Registro") # MENÚ3
        # Subopciones
        third_reg=QAction("Registro del producto", self)
        third_reg.triggered.connect(self.show_registration)

        menu_fourth = menubar.addMenu("☰ Life") # MENÚ4
        # Subopciones
        fourth_version=QAction("Versión", self)
        fourth_version.triggered.connect(self.show_info)
        fourth_info=QAction("Información", self)
        fourth_info.triggered.connect(self.show_credits)

        menu_fifth=menubar.addMenu("☰ Salir") # MENÚ5
        # Subopciones
        fifth_exit=QAction("Salir de la aplicacion", self)
        fifth_exit.triggered.connect(self.confirm_exit)

        # Agregar acciones a los menús
        menu_second.addAction(sec_ajustes)
        menu_third.addAction(third_reg)
        menu_fourth.addAction(fourth_info)
        menu_fourth.addSeparator()
        menu_fourth.addAction(fourth_version)
        menu_fifth.addAction(fifth_exit)
        menu_first.addAction(first_report)

        self.resize(1400, 820)
        main_split = QSplitter(QtCore.Qt.Horizontal)

        # BOTÓN DESLIZANTE MODO OSCURO
        self.dark_mode = False  # Por defecto: modo claro
        self.toggle_button = QPushButton("🌞 Modo Claro", self)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setGeometry(1000, 5, 120, 30)  # posición aprox.
        self.toggle_button.clicked.connect(self.toggle_dark_mode)
        #  Estilo del toggle button
        self.toggle_button.setStyleSheet("""
            QPushButton{
                background-color: #d9d9d9;
                color: #202020;
                border-radius: 10px;
                font: bold 10pt "Segoe UI";
                padding: 5px;
            }
            QPushButton:checked {
                background-color: #2c2c2c;
                color: #ffffff;
            }
        """)

        left_widget = QWidget() # Panel izquierdo
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(6, 6, 6, 6)

        self.btn_sim=QPushButton("Enfermedades")
        self.btn_book=QPushButton("Lifenesss Booklet")
        for btn in (self.btn_sim, self.btn_book):
            btn.setMinimumHeight(56)
            btn.setFont(QFont("Arial Black", 12))
            btn.setToolTip("Click para descubrir")
            left_layout.addWidget(btn)
        left_layout.addStretch()
        left_scroll = QtWidgets.QScrollArea()
        left_scroll.setWidget(left_widget)
        left_scroll.setWidgetResizable(True)
        left_scroll.setFixedWidth(320)
        main_split.addWidget(left_scroll)

        center_widget = QWidget() # Panel central
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(6, 6, 6, 6)

        title_lbl = QLabel("Life | Lifeness Simulator") # Titulo central
        title_lbl.setFont(QFont("Arial Black", 15))
        title_lbl.setAlignment(QtCore.Qt.AlignCenter)
        center_layout.addWidget(title_lbl)

        self.gl_widget = GLHumanWidget() # Widget OpenGL
        center_layout.addWidget(self.gl_widget, 1)

        timeline_bar = QWidget()
        t_layout = QHBoxLayout(timeline_bar)
        self.btn_play = QPushButton("Play")
        self.btn_pause = QPushButton("Pause")
        self.cmb_speed = QComboBox()
        self.cmb_speed.addItems(["0.5x", "1x", "2x"])
        self.cmb_speed.setCurrentText("1x")
        self.tslider = QSlider(QtCore.Qt.Horizontal)
        self.tslider.setRange(0, 100); self.tslider.setValue(0)
        t_layout.addWidget(self.btn_play)
        t_layout.addWidget(self.btn_pause)
        t_layout.addWidget(self.cmb_speed)
        t_layout.addWidget(self.tslider)
        center_layout.addWidget(timeline_bar)
        main_split.addWidget(center_widget)

        right_widget = QWidget() # Panel derecho
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(6, 6, 6, 6)
        self.txt_oms = QTextEdit()
        self.txt_oms.setReadOnly(True)
        self.txt_oms.setHtml("<b><center>OMS | Recursos y referencias</center></b>"
                             "<p>Aplicacion evaluada profesionalmente, para más informacion registre el producto.</p>")
        right_layout.addWidget(self.txt_oms, 1)
        self.lst_enf = QListWidget() # Lista de enfermedades
        right_layout.addWidget(QLabel("Escoja una enfermedad:"))
        right_layout.addWidget(self.lst_enf, 1)
        self.btn_tratamiento = QPushButton("Threatment")
        right_layout.addWidget(self.btn_tratamiento)
        main_split.addWidget(right_widget)
        main_split.setStretchFactor(1, 2)

        central = QWidget() # Contenedor central
        central_layout = QHBoxLayout(central)
        central_layout.addWidget(main_split)
        self.setCentralWidget(central)

        # Conexiones
        self.btn_book.clicked.connect(self.show_booklet)
        self.btn_sim.clicked.connect(self.show_sim_categories)
        self.lst_enf.itemClicked.connect(self.on_enfermedad_selected)
        self.btn_tratamiento.clicked.connect(self.on_tratamiento_clicked)
        self.btn_play.clicked.connect(self.on_play)
        self.btn_pause.clicked.connect(self.on_pause)
        self.cmb_speed.currentTextChanged.connect(self.on_speed_change)
        self.tslider.valueChanged.connect(self.on_timeline_move)

        QtGui_short_f11 = QAction(self)
        QtGui_short_f11.setShortcut("F11")
        QtGui_short_f11.triggered.connect(self.toggle_fullscreen)
        self.addAction(QtGui_short_f11)
        QtGui_short_esc = QAction(self)
        QtGui_short_esc.setShortcut("Esc")
        QtGui_short_esc.triggered.connect(self.on_escape)
        self.addAction(QtGui_short_esc)

        self.populate_categories()

        self.timeline_playing = False
        self.timeline_speed = 1.0
        self.timeline_timer = QtCore.QTimer()
        self.timeline_timer.timeout.connect(self.advance_timeline)

    def toggle_dark_mode(self):
        if self.toggle_button.isChecked():
            self.dark_mode = True
            self.toggle_button.setText("🌙 Modo Oscuro")
            self.setStyleSheet("""
                QWidget {
                    background-color: #1e1e1e;
                    color: white;
                }
                QPushButton {
                    background-color: #3a3a3a;
                    color: white;
                    border-radius: 10px;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
            """)
        else:
            self.dark_mode = False
            self.toggle_button.setText("🌞 Modo Claro")
            self.setStyleSheet("""
                QWidget {
                    background-color: #1e1e1e;
                    color: white;
                }
                QPushButton{
                    background-color: #0078D7;
                    color: white;
                    font: bold 10pt "Segoe UI";
                    border-radius: 10px;
                    padding: 8px 16px;
                }
                QPushButton:hover{
                    background-color: #1493FF;
                }
                QPushButton:pressed{
                    background-color: #005A9E;
                }
                QLabel{
                    font: 10pt "Segoe UI";
                }
            """)

    def populate_categories(self):
        self.lst_enf.clear()
        if not hasattr(self.parser, "enfermedades") or not self.parser.enfermedades:
            return
        for e in self.parser.enfermedades[:50]:
            self.lst_enf.addItem(f"{e.nombre} [{e.categoria}]")
            item = self.lst_enf.item(self.lst_enf.count() - 1)
            item.setToolTip(e.descripcion[:200])

    def show_info(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Preferencias")
        info = (
            f"<b>{self.meta.titulo}</b><br>"
            f"{self.meta.autores}<br>"
            f"Versión: {self.meta.version}<br>"
            f"Fecha: {self.meta.fecha}<br>"
            f"Idioma: {self.meta.idioma}<br><br>"
            f"{self.meta.descripcion}<br><br>"
            "Aplicacion evaluada por profesionales, no sustituye evaluacion medica."
        )
        dlg.setText(info)
        dlg.exec()

    def show_credits(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Creditos y Agradecimientos")
        dlg.resize(800, 400)
        credits = (
            "<b>Créditos</b><br>"
            "Desarrollado por el equipo de Lifeness Project.<br>"
            "Agradecimientos especiales a todos los colaboradores y beta testers.<br>"
            "Especiales agradecimientos.<br>"
            "Modelos 3D por Matthias Jiménez y otros recursos libres.<br>"
            "Estadisticas Reales y actualizadas. Para más informacion ingrese a la plataforma OMS.<br>"
            "www.who.int<br><br>"
        )
        dlg.setText(credits)
        dlg.exec()

    def show_booklet(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Lifeness Booklet | Libro Oficial")
        booklet = (
            "<b><center>Lifeness Booklet</center></b><br>"
            "Lifeness Booklet es un manual/instructivo, recurso educativo complementario esencial de la aplicación.<br>"
            "Incluye información sobre enfermedades, prevención, habitos y salud pública.<br>"
            "Consulte el libro dentro de la carpeta de guardado o en el disco oficial."
        )
        dlg.setText(booklet)
        dlg.exec()

    def show_registration(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Life | Clave de registro")
        dialog.setFixedSize(900, 650)
        layout = QVBoxLayout(dialog)

        label = QLabel("Registre su producto para obtener soporte técnico, acceso a recursos exclusivos y mensajes especiales por parte del equipo.")
        layout.addWidget(label)

        self.input_key = QLineEdit()
        self.input_key.setPlaceholderText("XXX-XXX-XXX-XXX")
        self.input_key.setEchoMode(QLineEdit.Normal)
        layout.addWidget(self.input_key)

        label_two= QLabel("Para registrar el producto, consulte el libro 'Lifeness Booklet' o contacte con su docente guia para completar el proceso de registro.")
        layout.addWidget(label_two)

        btn_ok = QPushButton("Aceptar")
        btn_ok.clicked.connect(lambda: self.check_key(dialog))
        layout.addWidget(btn_ok)

        dialog.exec()

    def check_key(self, dialog):
        user_key = self.input_key.text()
        correct_key = "RAY-155-345-FGS"

        if user_key == correct_key:
            QMessageBox.information(self, "Registro exitoso", "La clave es correcta. ¡Bienvenido!")
            dialog.accept()
        else:
            QMessageBox.warning(self, "Error", "Clave incorrecta. Inténtelo nuevamente.")
            
#-------------------------FUNCIONES DE SELECCION JERARQUICA
    def show_sim_categories(self):
        self.disable_side_buttons() # Deshabilitar botones laterales
        self.clear_right_panel() # Limpiar panel derecho
        self.txt_oms.setHtml("<h3><center>Escoja sistema</center></h3>") # Titulo

        sistemas = [
            "Sistema respiratorio", "Sistema digestivo", "Sistema circulatorio",
            "Sistema nervioso", "Sistema endocrino", "Sistema inmunológico",
            "Sistema urinario", "Sistema tegumentario", "Sistema muscular",
            "Sistema óseo"
        ]

        for sistema in sistemas:
            btn = QPushButton(sistema)
            btn.setStyleSheet("font: 12pt 'Arial Black'; background-color: #e0f0ff;")
            btn.clicked.connect(lambda _, s=sistema: self.show_age_selection(s))
            self.lst_enf.addItem(f"{sistema}")
        self.txt_oms.append("<p>Seleccione un sistema para continuar.</p>")

    def show_age_selection(self, sistema):
        self.clear_right_panel()
        self.txt_oms.setHtml(f"<h3><center>Escoja edad ({sistema})</center></h3>")
        edades = ["10-12 años", "12-14 años", "14-16 años", "16-18 años"]
        self.lst_enf.clear()
        for edad in edades:
            item = f"{edad}"
            self.lst_enf.addItem(item)
        self.txt_oms.append(f"<p>Seleccione un grupo de edad para el sistema {sistema}.</p>")

        # Guardar sistema actual
        self.selected_system = sistema
        self.lst_enf.itemClicked.connect(lambda item: self.show_disease_selection(self.selected_system, item.text()))

    def show_disease_selection(self, sistema, edad):
        self.clear_right_panel()
        self.txt_oms.setHtml(f"<h3><center>Escoja enfermedad relacionado con el ({sistema}) en la edad de ({edad}).</center></h3>")

        # Ejemplo de enfermedades por sistema
        enfermedades_por_sistema = {
            "Sistema respiratorio": ["Asma", "Bronquitis", "Neumonía", "Gripe", "COVID-19", "Rinitis", "Sinusitis", "EPOC", "Tos ferina", "Tuberculosis"],
            "Sistema digestivo": ["Gastritis", "Colitis", "Hepatitis", "Úlcera péptica", "Apendicitis", "Reflujo gástrico", "Pancreatitis", "Celiaquía", "Diarrea", "Estreñimiento"],
            "Sistema nervioso": ["Epilepsia", "Parkinson", "Alzheimer", "Migraña", "Neuralgia", "Esclerosis múltiple", "Neuritis", "Meningitis", "TDAH", "Autismo"],
            "Sistema endocrino": ["Diabetes tipo 1", "Diabetes tipo 2", "Hipertiroidismo", "Hipotiroidismo", "Síndrome de Cushing", "Acromegalia", "Addison", "Pubertad precoz", "Gigantismo", "Bocio"],
            # Agrega más sistemas según desees
        }

        self.lst_enf.clear()
        enfermedades = enfermedades_por_sistema.get(sistema, [])
        for enf in enfermedades:
            self.lst_enf.addItem(f"{enf}")

        # Guardar info actual
        self.selected_age = edad
        self.lst_enf.itemClicked.connect(lambda item: self.on_disease_selected_hierarchy(item.text(), sistema, edad))

    def on_disease_selected_hierarchy(self, enfermedad, sistema, edad):
        ficha = (
            f"<b>{enfermedad}</b><br>"
            f"Sistema: {sistema}<br>"
            f"Edad: {edad}<br>"
            f"<p>Material educativo. No sustituye la evaluación médica profesional.</p>"
        )
        self.txt_oms.setHtml(ficha)
        self.gl_widget.apply_reaction(enfermedad)
        self.enable_side_buttons()

    # -------------------------FUNCIONES AUXILIARES
    def clear_right_panel(self):
        """Limpia el panel derecho para reutilizar."""
        self.txt_oms.clear()
        self.lst_enf.clear()

    def disable_side_buttons(self):
        for btn in (self.btn_book):
            btn.setEnabled(False)

    def enable_side_buttons(self):
        for btn in (self.btn_book):
            btn.setEnabled(True)
#-------------------------FIN DE FUNCIONES DE SELECCION JERARQUICA

    def show_settings(self):
        dlg = SettingsDialog(self, current_lang=self.meta.idioma)
        if dlg.exec() == QDialog.Accepted:
            vals = dlg.values()
            logger.info("Ajustes aplicados: %s", vals)
            if vals["fullscreen"]:
                self.showFullScreen()
            else:
                self.showNormal()
            self.meta.idioma = vals["lang"]

    def confirm_exit(self):
        resp = QMessageBox.question(self, "Life", "¿Desea salir?", QMessageBox.Yes | QMessageBox.No)
        if resp == QMessageBox.Yes:
            QMessageBox.information(self, "Life", "Lifeness Simulator | Simulation that transforms\nMuchas gracias por su tiempo.")
            logger.info("Shutting Down Life ..")
            logger.info("Success.")
            logger.info("Gracias Por Usar Lifeness Simulator. Version %s", self.meta.version)
            QApplication.instance().quit()

    def generate_report(self):
        rg = ReportGenerator(self.meta, self.parser.enfermedades)
        path = rg.generate()
        QMessageBox.information(self, "Success!", f"¡Exito! Reporte guardado en {path}.")

    def on_enfermedad_selected(self, item):
        text = item.text()
        name = text.split(" [")[0]
        e = next((x for x in self.parser.enfermedades if x.nombre.startswith(name)), None)
        if not e:
            if text.startswith("[Categoria]"):
                cat = text.replace("[Categoria] ", "")
                filt = [x for x in self.parser.enfermedades if x.categoria.lower() == cat.lower()]
                self.lst_enf.clear()
                for ent in filt[:10]:
                    self.lst_enf.addItem(f"{ent.nombre} [{ent.categoria}]")
                return
            return
        ficha = (
            f"<b>{e.nombre}</b><br>"
            f"Categoría: {e.categoria}<br>"
            f"Descripción: {e.descripcion}<br>"
            f"Prevención: {e.prevencion or 'No disponible.'}<br>"
            f"<i>Fuente: {os.path.basename(getattr(self.parser, 'path', '') ) or 'Demo'}</i><br>"
            f"<p style='color:darkred;'>Aplicacion evaluada profesionalmente. No sustituye evaluación médica.</p>"
        )
        self.txt_oms.setHtml(ficha)
        self.gl_widget.apply_reaction(e.id)

    def on_tratamiento_clicked(self):
        sel = self.lst_enf.currentItem()
        if not sel:
            QMessageBox.information(self, "Tratamiento", "Seleccione una enfermedad en la lista.")
            return
        name = sel.text().split(" [")[0]
        e = next((x for x in self.parser.enfermedades if x.nombre.startswith(name)), None)
        if not e:
            QMessageBox.information(self, "Tratamiento", "Enfermedad no encontrada.")
            return
        texto = (
            f"<b>Tratamientos sugeridos (generales)</b><br>"
            f"{e.nombre}<br>"
            f"Protocolos generales: {e.tratamiento or 'Manejo clínico estándar (sin dosis).'}<br>"
            "<i>Nota: no se incluyen dosificaciones. Consulte guías oficiales y personal médico autorizado.</i>"
        )
        self.txt_oms.setHtml(texto)

    # Timeline controls
    def on_play(self):
        if not self.timeline_playing:
            self.timeline_timer.start(int(1000 / self.timeline_speed))
            self.timeline_playing = True

    def on_pause(self):
        if self.timeline_playing:
            self.timeline_timer.stop()
            self.timeline_playing = False

    def on_speed_change(self, txt):
        self.timeline_speed = 0.5 if txt.startswith("0.5") else (2.0 if txt.startswith("2") else 1.0)
        if self.timeline_playing:
            self.timeline_timer.start(int(1000 / self.timeline_speed))

    def advance_timeline(self):
        val = self.tslider.value()
        if val < self.tslider.maximum():
            self.tslider.setValue(val + 1)
        else:
            self.tslider.setValue(0)

    def on_timeline_move(self, val):
        if val < 33:
            self.gl_widget.apply_reaction(None)
        elif val < 66:
            self.gl_widget.apply_reaction("phase_mid")
        else:
            self.gl_widget.apply_reaction("phase_high")

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def on_escape(self):
        if self.isFullScreen():
            self.showNormal()

# ---------------------------------------------------------------------------
class SplashWindow(QWidget):
    def __init__(self, meta: MetaProyecto):
        super().__init__()
        self.meta = meta
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.resize(800, 420)
        layout = QVBoxLayout(self)
        title = QLabel(self.meta.titulo)
        title.setFont(QFont("Arial Black", 22))
        title.setStyleSheet("color: white;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        sub = QLabel(f"{self.meta.descripcion}\n{self.meta.autores}\nVersión: {self.meta.version} {self.meta.fecha}")
        sub.setStyleSheet("color: #ddd;")
        sub.setAlignment(QtCore.Qt.AlignCenter)
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(sub)
        layout.addStretch()
        self.opacity = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity)

    def play(self):
        steps = 30
        for i in range(steps):
            self.opacity.setOpacity(i / (steps - 1))
            QApplication.processEvents()
            time.sleep(0.6 / steps)
        hold = 5.0 - 0.6 - 0.6
        time.sleep(max(0.0, hold))
        for i in range(steps):
            self.opacity.setOpacity(1.0 - (i / (steps - 1)))
            QApplication.processEvents()
            time.sleep(0.6 / steps)
        time.sleep(0.001)

# ---------------------------------------------------------------------------
def main():
    meta = MetaProyecto()
    enfermedades = [
        Enfermedad(id="e1", nombre="Influenza (Ejemplo)", categoria="Virus", descripcion="Infección respiratoria estacional."),
        Enfermedad(id="e2", nombre="Dengue (Ejemplo)", categoria="Virus", descripcion="Fiebre por arbovirus transmitido por mosquito."),
        Enfermedad(id="e3", nombre="Tuberculosis (Ejemplo)", categoria="Bacterias", descripcion="Infección bacteriana pulmonar."),
        Enfermedad(id="e4", nombre="Candidiasis (Ejemplo)", categoria="Hongos", descripcion="Infección por Candida."),
        Enfermedad(id="e5", nombre="Paludismo (Ejemplo)", categoria="Parásitos", descripcion="Enfermedad transmitida por mosquitos."),
        Enfermedad(id="e6", nombre="Creutzfeldt-Jakob (Ejemplo)", categoria="Priones", descripcion="Trastorno priónico neurológico."),
    ]
    class ParserFake:
        def __init__(self, meta, enfermedades):
            self.meta = meta
            self.enfermedades = enfermedades
            self.categorias = sorted(list({e.categoria for e in enfermedades}))
            self.path = ""
    parser = ParserFake(meta, enfermedades)
    app = QApplication(sys.argv)
    splash = SplashWindow(meta)
    splash.show()
    splash.play()
    splash.close()
    window = MainWindow(parser, meta)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()