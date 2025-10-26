# Life | Lifeness Simulator | MJ

# Utilities
from __future__ import annotations
import os
import sys
import json, webbrowser
import time
import math
import shutil
import logging
import subprocess
from pathlib import Path
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass, field
from PIL import Image, ImageSequence
from typing import List, Optional, Dict
from datetime import datetime
from platformdirs import user_documents_dir

# GUI / UI
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import (QApplication, QGraphicsOpacityEffect, QMainWindow, QLineEdit, QWidget, QLabel, QPushButton, QListWidget, QTextEdit, QHBoxLayout, QVBoxLayout, QSplitter, QSlider, QMessageBox, QDialog, QFormLayout, QComboBox)
from PySide6.QtGui import QFont, QAction, QIcon, QPixmap, QMovie
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QRect
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
ACTIVATION_FILE = os.path.join(BASE_LOG, "Lifeness Simulator", "activation.json")

os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

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
class MetaProyecto:
    titulo: str = "Lifeness Simulator"
    autores: str = "A Biomedic app made by the Lifeness Project Team."
    version: str = "3.1"
    fecha: str = "2025-12-10"
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

#----------------------------------------------------------------------------
class Activation: # Activador
    def save_activation(self, name, key):
        documents_dir = user_documents_dir()
        path = os.path.join(documents_dir, "Lifeness Simulator")
        os.makedirs(path, exist_ok=True)

        data = {"user": name, "key": key}
        with open(ACTIVATION_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        subprocess.call(['attrib', '+h', ACTIVATION_FILE])  # Oculta archivo activador en Windows
        logger.info("Producto activado para %s", name)

# ---------------------------------------------------------------------------
class GLHumanWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Modelos Humanos
        self.model_male_path = os.path.join("assets/anatomy", "male.obj")
        self.model_female_path = os.path.join("assets/anatomy", "female.obj")
        self.model_cientific_path = os.path.join("assets/anatomy", "medical.obj")
        # Modelos Patogenos
        self.model_corona_path = os.path.join("assets/patogens/covid_19", "coronavirus.obj")
        self.model_corona_intern_path = os.path.join("assets/patogens/covid_19", "coronavirus_interno.obj")
        # Modelos Extras
        self.model_heart_path = os.path.join("assets/extra_parts/heart", "heart.obj")
        self.model_sperm_path = os.path.join("assets/extra_parts/reproductive_sys", "sperm.obj")
        self.model_cell_path = os.path.join("assets/extra_parts/blood", "red_cells.obj")
        self.model_ear_path = os.path.join("assets/extra_parts/ear", "ear.obj")

        self.model_male = OBJ(self.model_male_path) if os.path.isfile(self.model_male_path) else None
        self.model_female = OBJ(self.model_female_path) if os.path.isfile(self.model_female_path) else None
        self.model_cientific = OBJ(self.model_cientific_path) if os.path.isfile(self.model_cientific_path) else None
        
        self.model_corona = OBJ(self.model_corona_path) if os.path.isfile(self.model_corona_path) else None
        self.model_corona_intern = OBJ(self.model_corona_intern_path) if os.path.isfile(self.model_corona_intern_path) else None
        
        self.model_heart = OBJ(self.model_heart_path) if os.path.isfile(self.model_hear_path) else None
        self.model_sperm = OBJ(self.model_sperm_path) if os.path.isfile(self.model_sperm_path) else None
        self.model_cell = OBJ(self.model_cell_path) if os.path.isfile(self.model_cell_path) else None
        self.model_ear = OBJ(self.model_ear_path) if os.path.isfile(self.model_ear_path) else None
        
        self.current_model = self.model_male #Se Define el modelo humano masculino al iniciar
        self.yaw = 0.0
        self.last_mouse_x = None
        self.zoom = -6.0
        self.bg_black = True
        self.reaction_id: Optional[str] = None
        self.reaction_start = 0.0
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(30)

        # Fondo GIF
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
    
    def load_model(self, model_path):     
        if not os.path.isfile(model_path):
            logger.warning(f"Modelo no encontrado: {model_path}")
            return
        try:
            self.current_model = OBJ(model_path)
            self.update()
            logger.info(f"Modelo actualizado: {model_path}")
        except Exception as e:
            logger.exception(f"Error al cargar modelo dinámico: {e}")

# ---------------------------------------------------------------------------
class SettingsDialog(QDialog):
    def __init__(self, parent=None, current_lang="es"):
        super().__init__(parent)
        self.setWindowTitle("Ajustes")
        self.resize(450, 200) # Ancho, Alto
        layout = QFormLayout(self)
        self.sldr_brightness = QSlider(QtCore.Qt.Horizontal)
        self.sldr_brightness.setRange(10, 200)  # 100 = normal, menos = oscuro, más = brillante
        self.sldr_brightness.setValue(100)
        self.sldr_brightness.valueChanged.connect(self.change_brightness)
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
class DiseasePatogen(QMainWindow):
    def __init__(self, enfermedad_actual):
        super().__init__()
        self.setWindowTitle("Life Analizer")
        ico_path = os.path.join(ASSETS_DIR, "pictures/icons", "ico2.ico")
        self.setWindowIcon(QIcon(ico_path))
        self.setGeometry(200, 100, 1100, 600)
        self.setFixedSize(1100, 600)

        screen = self.screen().availableGeometry()
        x = (screen.width() - self.width()) //2
        y = (screen.height() - self.height()) //2
        self.move(x, y)

        # Widget central
        central = QWidget()
        self.setCentralWidget(central)

        # Layout principal
        main_layout = QHBoxLayout(central)

        # Panel izquierdo (botones)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        label_title_2 = QLabel("AQUI DESCRIPCION MAX 10")
        label_title_2.setFont(QFont("Arial", 12, QFont.Bold))
        label_title_2.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(label_title_2)

        left_layout.addStretch()
        main_layout.addWidget(left_panel, 1)

        # Panel derecho (visualizador)
        right_panel = QWidget()
        right_panel.setStyleSheet("background-color: black; border: 0px solid #555;")
        right_layout = QVBoxLayout(right_panel)

        self.viewer = GLHumanWidget()
        right_layout.addWidget(self.viewer)

        self.desc_label = QLabel(f"{enfermedad_actual}")
        self.desc_label.setStyleSheet("color: white; padding: 10px;")
        self.desc_label.setFont(QFont("Segoe UI", 30, QFont.Bold))
        self.desc_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.desc_label)
        main_layout.addWidget(right_panel, 3)
            
# ---------------------------------------------------------------------------
class AnimatedButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.original_geometry = None
        self.animation = None

    def enterEvent(self, event):
        # Guarda la geometría original
        self.original_geometry = self.geometry()

        # Expande el botón (zoom suave)
        new_geometry = QRect(
            self.original_geometry.x() - 3,
            self.original_geometry.y() - 3,
            self.original_geometry.width() + 6,
            self.original_geometry.height() + 6
        )

        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(150)
        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(new_geometry)
        self.animation.setEasingCurve(QEasingCurve.OutQuad)
        self.animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        # Vuelve al tamaño original
        if self.original_geometry:
            self.animation = QPropertyAnimation(self, b"geometry")
            self.animation.setDuration(150)
            self.animation.setStartValue(self.geometry())
            self.animation.setEndValue(self.original_geometry)
            self.animation.setEasingCurve(QEasingCurve.InQuad)
            self.animation.start()
        super().leaveEvent(event)

# ---------------------------------------------------------------------------
class ReportGenerator:
    def __init__(self, meta: MetaProyecto):
        self.meta = meta
    
        # Carpeta universal de documentos
        documents_dir = user_documents_dir()
        self.output_dir = os.path.join(documents_dir, "Lifeness Simulator/Reports")
        logger.info("Success!. Report saved correctly in Documents.")
        os.makedirs(self.output_dir, exist_ok=True)

        # Plantilla incluida en el exe (gracias a resource_path)
        self.out_path = os.path.join(self.output_dir, f"Life Report.docx")

    def generate(self) -> str:
        doc = Document(os.path.join(BASE_DIR, "docs", "life_report_template.docx"))
        today = datetime.today().strftime("%Y-%m-%d")

        # Ejemplo: reemplazo de campos "-" en tablas
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip() == "-":
                        if "Fecha" in row.cells[0].text:
                            cell.text = today
                        elif "enfermedades" in row.cells[0].text.lower():
                            cell.text = "3"
                        else:
                            cell.text = "OK"
        doc.save(self.out_path)
        return self.out_path

# ---------------------------------------------------------------------------
class AuthorsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Autores del Proyecto")
        self.setFixedSize(400, 500)
        self.setStyleSheet("background-color: #f5f5f5; border-radius: 10px;")

        # Datos de autores
        self.authors = [
            {
                "name": "Matthias Jiménez",
                "image": "author1.jpg",
                "desc": "Investigador principal y diseñador del simulador biomédico."
            },
            {
                "name": "Diego Guerron",
                "image": "author2.jpg",
                "desc": "Desarrolladora de la interfaz 3D y del módulo de visualización médica."
            },
            {
                "name": "Jose Herbas",
                "image": "author3.jpg",
                "desc": "Encargado del modelado 3D y del procesamiento de datos científicos."
            },
            {
                "name": "Oliver Vizuete",
                "image": "author4.jpg",
                "desc": "Especialista en documentación y diseño de materiales educativos."
            }
        ]

        self.index = 0  # autor actual

        # Widgets
        self.name_label = QLabel("", alignment=Qt.AlignCenter)
        self.name_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")

        self.photo_label = QLabel(alignment=Qt.AlignCenter)
        self.photo_label.setFixedSize(200, 200)
        self.photo_label.setStyleSheet("border-radius: 100px; border: 2px solid #aaa;")

        self.desc_label = QLabel("", alignment=Qt.AlignCenter)
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("font-size: 14px; color: #555; padding: 10px;")

        # Botones
        self.prev_btn = QPushButton("← Atrás")
        self.next_btn = QPushButton("Siguiente →")
        self.close_btn = QPushButton("Cerrar")

        self.prev_btn.clicked.connect(self.show_prev)
        self.next_btn.clicked.connect(self.show_next)
        self.close_btn.clicked.connect(self.close)

        # Layouts
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.prev_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.next_btn)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.name_label)
        main_layout.addWidget(self.photo_label)
        main_layout.addWidget(self.desc_label)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.close_btn, alignment=Qt.AlignCenter)

        self.setLayout(main_layout)
        self.update_author()

    # Mostrar autor actual
    def update_author(self):
        author = self.authors[self.index]
        self.name_label.setText(author["name"])
        self.desc_label.setText(author["desc"])

        pixmap = QPixmap(author["image"])
        if not pixmap.isNull():
            self.photo_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.photo_label.setText("(Foto no encontrada)")

        # Deshabilitar botones según el índice
        self.prev_btn.setEnabled(self.index > 0)
        self.next_btn.setEnabled(self.index < len(self.authors) - 1)

    def show_next(self):
        if self.index < len(self.authors) - 1:
            self.index += 1
            self.update_author()

    def show_prev(self):
        if self.index > 0:
            self.index -= 1
            self.update_author()

# ---------------------------------------------------------------------------
class ExtraWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Life | Extras y Recursos")
        ico_path = os.path.join(ASSETS_DIR, "pictures/icons", "ico2.ico")
        self.setWindowIcon(QIcon(ico_path))
        self.setGeometry(200, 100, 1100, 600)
        self.setFixedSize(1100, 600)  # Tamaño fijo, no redimensionable

        screen = self.screen().availableGeometry()
        x = (screen.width() - self.width()) //2
        y = (screen.height() - self.height()) //2
        self.move(x, y)

        # Widget central
        central = QWidget()
        self.setCentralWidget(central)

        # Layout principal
        main_layout = QHBoxLayout(central)

        # Panel izquierdo (botones)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        label_title = QLabel("Modelos 3D Extras") # Título
        label_title.setFont(QFont("Arial", 14, QFont.Bold))
        label_title.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(label_title)

        # Botones de modelos
        self.buttons = {}
        models = {
            "Corazón": "heart.obj",
            "ADN": "dna.obj",
            "Oreja": "ear.obj",
            "Espermatozoide": "Sperm.obj"
        }

        for name, file in models.items():
            btn = AnimatedButton(name)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #0078D7;
                    color: white;
                    border-radius: 6px;
                    padding: 10px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #005A9E;
                }
            """)
            btn.clicked.connect(lambda checked, f=file, n=name: self.load_model(f, n))
            left_layout.addWidget(btn)
            self.buttons[name] = btn

        label_title_2 = QLabel("Anatomia Esqueletica") # Nuevo título
        label_title_2.setFont(QFont("Arial", 14, QFont.Bold))
        label_title_2.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(label_title_2)

        # Botones de modelos
        models_2 = {
            "Cerebro": "brain.obj",
            "Huesos": "bones.obj"
        }

        for name, file in models_2.items():
            btn = AnimatedButton(name)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #0078D7;
                    color: white;
                    border-radius: 6px;
                    padding: 10px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #005A9E;
                }
            """)
            btn.clicked.connect(lambda checked, f=file, n=name: self.load_model(f, n))
            left_layout.addWidget(btn)
            self.buttons[name] = btn

        left_layout.addStretch()
        main_layout.addWidget(left_panel, 1)

        # Panel derecho (visualizador)
        right_panel = QWidget()
        right_panel.setStyleSheet("background-color: black; border: 0px solid #555;")
        right_layout = QVBoxLayout(right_panel)

        self.viewer = GLHumanWidget()
        # self.viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_layout.addWidget(self.viewer)

        # Panel inferior (descripción)
        self.desc_label = QLabel("Seleccione un modelo para visualizar.")
        self.desc_label.setStyleSheet("color: white; padding: 10px;")
        right_layout.addWidget(self.desc_label)
        main_layout.addWidget(right_panel, 3)

        self.model_descriptions = {
            "Corazón": "Representación 3D del corazón humano, mostrando cavidades y arterias principales.",
            "ADN": "Modelo 3D de la doble hélice del ADN, base de la información genética.",
            "Huesos": "Estructura ósea básica del cuerpo humano, modelo anatómico de referencia.",
            "Cerebro": "Modelo 3D del cerebro humano con divisiones hemisféricas y lóbulos cerebrales.",
            "Espermatozoide": "Representación microscópica del espermatozoide humano, vista aumentada."
        }

    def load_model(self, model_file, name):
        try:
            model_path = os.path.join(BASE_DIR, f"assets/anatomy/extra_parts/{model_file}")
            self.viewer.load_model(model_path)
            self.desc_label.setText(self.model_descriptions.get(name, "Modelo cargado."))
        except Exception as e:
            self.desc_label.setText(f"Error al cargar {name}: {str(e)}")

# ---------------------------------------------------------------------------
class MainWindow(QMainWindow): # Constructor o init
    def __init__(self, parser, meta: MetaProyecto):
        super().__init__()
        self.parser = parser
        self.meta = meta
        self.setWindowTitle("Life")
        ico_path = os.path.join(ASSETS_DIR, "pictures/icons", "ico1.ico")
        self.setWindowIcon(QIcon(ico_path))
        self.showMaximized()
        self.resize(1290, 690)
        self.setFixedSize(self.size())
        self.setWindowFlags(self.windowFlags() & -Qt.WindowMaximizeButtonHint)
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.center_window()

    def center_window(self): # Proceso para centrar una ventana
        screen = self.screen().availableGeometry()
        x = (screen.width() - self.width()) //2
        y = (screen.height() - self.height()) //2
        self.move(x, y)

        # Estilo global para toda la app usado mediante la propiedad setStyleSheet
        self.setStyleSheet("""
            QWidget{
                background-color: #FFFFFF;
                color: black;
            }
            QPushButton{
                background-color: #0078D7;
                color: white;
                font: bold 12pt "Segoe UI";
                border-radius: 10px;
                padding: 8px 16px;
            }
            QPushButton:hover{
                background-color: #0BD4D4;
            }
            QPushButton:pressed{
                background-color: #ABABAB;
            }
            QLabel{
                font: 12pt "Segoe UI";
            }
        """)

        # MENÚ SUPERIOR
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar{
                background-color: #4F4F4F;
                color: white;
                font: bold 10pt "Segoe UI";
            }
            QMenuBar::item:selected{
                background-color: #BFD1DE;
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
        sec_ajustes_dim = QAction("Ajustes Interactive 3D", self)
        sec_ajustes.triggered.connect(self.show_settings)
        sec_ajustes_dim.triggered.connect(self.show_settings_dim)

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
        menu_second.addSeparator()
        menu_second.addAction(sec_ajustes_dim)
        menu_third.addAction(third_reg)
        menu_fourth.addAction(fourth_info)
        menu_fourth.addSeparator()
        menu_fourth.addAction(fourth_version)
        menu_fifth.addAction(fifth_exit)
        menu_first.addAction(first_report)

        main_split = QSplitter(QtCore.Qt.Horizontal)
        main_split.setHandleWidth(0)

        # BOTÓN DESLIZANTE MODO OSCURO
        self.dark_mode = False  # Por defecto: modo claro
        self.toggle_button = AnimatedButton("🌞 Modo Claro", self)
        self.toggle_button.setCheckable(True)
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

        # Botones del menú lateral
        self.btn_sim=AnimatedButton("Analisis de Patologias", self)
        self.btn_book=AnimatedButton("Lifenesss Booklet", self)
        self.btn_change=AnimatedButton("Cambiar modelo 3D", self)
        self.btn_extras=AnimatedButton("Extras y Recursos", self)
        self.btn_author = AnimatedButton("Agradecimientos", self)
        self.btn_help=AnimatedButton("Ayuda y Soporte", self)
        # Tooltips (descripciones emergentes)
        self.btn_sim.setToolTip("Analiza y aprende acerca de las enfermedades más comunes y sus efectos en el cuerpo humano.")
        self.btn_author.setToolTip("Ver la lista de colaboradores y autores del proyecto")
        self.btn_book.setToolTip("Descubre como conseguir el manual oficial")
        self.btn_change.setToolTip("Cambia entre modelo masculino y femenino")
        self.btn_extras.setToolTip("Recursos exclusivos\nmodelos, texturas, etc..")
        self.btn_help.setToolTip("Resuelve problemas con el equipo de soporte")

        self.menu_buttons = [self.btn_sim, self.btn_book, self.btn_change]
        self.act_buttons=[self.btn_extras, self.btn_help, self.btn_author]

        for btn in (self.menu_buttons):
            btn.setMinimumHeight(56)
            btn.setFont(QFont("Verdana", 13))
            left_layout.addWidget(btn)
        for btn in (self.act_buttons):
            btn.setMinimumHeight(56)
            btn.setFont(QFont("Verdana", 13))
            left_layout.addWidget(btn)

        # Agregamos espacios para el boton final de autores.
        left_layout.addWidget(self.btn_author, alignment=Qt.AlignTop)

        left_layout.addStretch()
        left_scroll = QtWidgets.QScrollArea()
        left_scroll.setWidget(left_widget)
        left_scroll.setWidgetResizable(True)
        left_scroll.setFixedWidth(320)
        main_split.addWidget(left_scroll)

        center_widget = QWidget() # Panel central
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(6, 6, 6, 6)

        title_lbl = QLabel("Interactive 3D | Life") # Titulo central
        title_lbl.setFont(QFont("Comic Sans", 15))
        title_lbl.setAlignment(QtCore.Qt.AlignCenter)
        center_layout.addWidget(title_lbl)

        self.gl_widget = GLHumanWidget() # Widget OpenGL
        center_layout.addWidget(self.gl_widget, 1)

        timeline_bar = QWidget()
        t_layout = QHBoxLayout(timeline_bar)
        self.btn_play = AnimatedButton("Play")
        self.btn_pause = AnimatedButton("Pause")
        self.cmb_speed = QComboBox()
        self.cmb_speed.addItems(["0.5x", "1x", "2x"])
        self.cmb_speed.setCurrentText("1x")
        self.tslider = QSlider(QtCore.Qt.Horizontal)
        self.tslider.setRange(0, 100); self.tslider.setValue(0) # Agergamos valores al Deslizante, en este caso esta en 0
        self.tslider.valueChanged.connect(self.on_model_slider_changed)
        t_layout.addWidget(self.btn_play)
        t_layout.addWidget(self.btn_pause)
        t_layout.addWidget(self.cmb_speed)
        t_layout.addWidget(self.tslider)
        center_layout.addWidget(timeline_bar)
        main_split.addWidget(center_widget)

        right_widget = QWidget() # Panel derecho
        self.right_layout = QVBoxLayout(right_widget)
        self.right_layout.setContentsMargins(6, 6, 6, 6)
        self.txt_oms = QTextEdit()
        self.txt_wait = QTextEdit()
        self.txt_oms.setReadOnly(True)
        self.txt_wait.setReadOnly(True)
        self.txt_wait.setHtml("<b><center>Life Analizer</center></b>"
                              "<p><center>¡Espere un momento! Estamos preparando lo mejor para usted ..</center></p>")
        
        if os.path.exists(ACTIVATION_FILE): # Verificar activación
            self.txt_oms.setHtml("<b><center>OMS Referencias</center></b>"
                                 "<p><center>La OMS define la salud como un estado de completo bienestar físico, mental "
                                 "y social, y no solamente la ausencia de afecciones o enfermedades. Esta definición, "
                                 "que se remonta a 1948, enfatiza que la salud es un concepto integral que va "
                                 "más allá de la simple falta de enfermedad e incluye el bienestar "
                                 "integral del individuo.</center></p>")
        else:
            self.txt_oms.setHtml("<b><center>OMS Referencias</center></b>"
                                 "<p>Aplicacion evaluada profesionalmente. Para más informacion registre el producto (Life).</p>")
            
        self.right_layout.addWidget(self.txt_oms, 1)
        self.newlabel=QLabel("Sistemas y Enfermedades")
        self.newlabel.setAlignment(QtCore.Qt.AlignCenter)
        self.right_layout.addWidget(self.newlabel)
        self.right_layout.addWidget(self.txt_wait, 1)
        main_split.addWidget(right_widget)
        main_split.setStretchFactor(1, 2)
        main_split.setFixedWidth(225)

        central = QWidget() # Contenedor central
        central_layout = QHBoxLayout(central)
        central_layout.addWidget(main_split)
        self.setCentralWidget(central)

        # Conexiones
        self.btn_book.clicked.connect(self.show_booklet)
        self.btn_sim.clicked.connect(self.show_sim_categories)
        self.btn_author.clicked.connect(self.author_regards)
        self.btn_change.clicked.connect(self.change_model)
        self.btn_extras.clicked.connect(self.show_extras)
        self.btn_help.clicked.connect(self.show_help)
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

        self.timeline_playing = False
        self.timeline_speed = 1.0
        self.timeline_timer = QtCore.QTimer()
        self.timeline_timer.timeout.connect(self.advance_timeline)
        self.toggle_button.setGeometry(1128, 0, 132, 30)  # posición aprox.

        if os.path.exists(ACTIVATION_FILE): # Verificar activación
            self.enable_act_buttons()
            third_reg.setEnabled(False)
        else:
            self.disable_act_buttons()

    def toggle_dark_mode(self):
        if self.toggle_button.isChecked():
            self.dark_mode = True
            self.toggle_button.setText("🌙 Modo Oscuro")
            self.setStyleSheet("""
                QWidget {
                    background-color: #383636;
                    color: white;
                }
                QPushButton{
                    background-color: #0078D7;
                    color: white;
                    font: bold 12pt "Segoe UI";
                    border-radius: 10px;
                    padding: 8px 16px;
                }
                QPushButton:hover{
                    background-color: #0BD4D4;
                }
                QLabel{
                    font: 12pt "Segoe UI";
                    color: white;
                }
            """)
        else:
            self.dark_mode = False
            self.toggle_button.setText("🌞 Modo Claro")
            self.setStyleSheet("""
                QWidget{
                    background-color: #FFFFFF;
                    color: black;
                }
                QPushButton{
                    background-color: #0078D7;
                    color: white;
                    font: bold 12pt "Segoe UI";
                    border-radius: 10px;
                    padding: 8px 16px;
                }
                QPushButton:hover{
                    background-color: #0BD4D4;
                }
                QPushButton:pressed{
                    background-color: #ABABAB;
                }
                QLabel{
                    font: 12pt "Segoe UI";
                    color: black;
                }
            """)
    #-------------------------FUNCIONES DE SELECCION JERARQUICA
    def show_sim_categories(self):
        self.txt_oms.clear();self.txt_wait.clear();self.clear_right_panel() # Se limpian los paneles
        self.disable_side_buttons();self.disable_act_buttons()              # Se desactivan ambas listas de botones
        self.txt_oms.setHtml("<h2><center>Seleccione el Sistema Inicial</center></h2>")

        # Crear lista de sistemas
        self.lista = QListWidget()
        sistemas = [
            "Sistema respiratorio", "Sistema digestivo", "Sistema circulatorio",
            "Sistema nervioso", "Sistema endocrino", "Sistema inmunológico",
            "Sistema urinario", "Sistema tegumentario", "Sistema muscular",
            "Sistema óseo"
        ]
        self.lista.addItems(sistemas)
        self.lista.itemClicked.connect(self.selected_sys)
        self.right_layout.addWidget(self.txt_oms, 1)
        self.right_layout.addSpacing(10)
        self.right_layout.addWidget(self.lista)

        self.btn_tratamiento = AnimatedButton("Seleccion de Sistema")
        self.right_layout.addWidget(self.btn_tratamiento)
        self.btn_tratamiento.clicked.connect(self.seleccionar_sistema)
    def selected_sys(self, item):                           # Al hacer clic en un item
        actual_sys = item.text()
        self.btn_tratamiento.setText(f"{actual_sys}")
    def seleccionar_sistema(self):
        item = self.lista.currentItem()
        if not item:
            QMessageBox.warning(self, "Aviso", "Seleccione un sistema primero.")
            return
        self.sistema_actual = item.text()
        self.show_age_selection()

    def show_age_selection(self):
        self.clear_right_panel()
        self.clear_right_panel()
        self.txt_oms.setHtml("<h2><center>Seleccione el Grupo etario</center></h2>"
                             f"<p><center>Preferente para el {self.sistema_actual}.</center></p>")

        self.lista = QListWidget()
        edades = ["12-15 años", "15-18 años"]
        self.lista.addItems(edades)
        self.lista.itemClicked.connect(self.selected_age)
        self.right_layout.addWidget(self.txt_oms, 1)
        self.right_layout.addSpacing(10)
        self.right_layout.addWidget(self.lista)

        self.btn_tratamiento = AnimatedButton("Seleccion de Grupo etario")
        self.btn_tratamiento.clicked.connect(self.seleccionar_edad)
        self.right_layout.addWidget(self.btn_tratamiento)
    def selected_age(self, item): 
        actual_age = item.text()
        self.btn_tratamiento.setText(f"{actual_age}")
    def seleccionar_edad(self):
        item = self.lista.currentItem()
        if not item:
            QMessageBox.warning(self, "Aviso", "Seleccione el grupo etario primero.")
            return
        self.edad_actual = item.text()
        self.show_disease_selection()

    def show_disease_selection(self):
        self.clear_right_panel()
        self.clear_right_panel()
        self.txt_oms.setHtml("<h2><center>Finalmente Seleccione</center></h2>"
                             "<h2><center>La enfermedad</center></h2>"
                             f"<p><center>Del {self.sistema_actual}, mas común a la edad de {self.edad_actual}.</center></p>")

        enfermedades_sistemas = {
            "Sistema respiratorio": "COVID-19",
            "Sistema digestivo": "Hepatitis",
            "Sistema circulatorio": "Anemia",
            "Sistema nervioso": "Epilepsia",
            "Sistema endocrino": "Obesidad",
            "Sistema inmunológico": "Esclerosis múltiple",
            "Sistema urinario": "Síndrome nefrótico",
            "Sistema tegumentario": "Dermatitis",
            "Sistema muscular": "Tétanos",
            "Sistema óseo": "Osteoporosis"
        }
        enfermedades_descripcion = {
            "COVID-19": "",
            "Hepatitis": "",
            "Anemia": "",
            "Epilepsia": "",
            "Obesidad": "",
            "Esclerosis múltiple": "",
            "Síndrome nefrótico": "",
            "Dermatitis": "",
            "Tétanos": "",
            "Osteoporosis": ""
        }
    
        self.lista = QListWidget()
        enfermedades = enfermedades_sistemas.get(self.sistema_actual, ["No se encontraron enfermedades"])
        self.lista.addItems(enfermedades)
        self.lista.itemClicked.connect(self.selected_dis)
        self.right_layout.addWidget(self.txt_oms, 1)
        self.right_layout.addSpacing(10)
        self.right_layout.addWidget(self.lista)

        self.btn_tratamiento = AnimatedButton("¡Enfermedad encontrada!")
        self.btn_tratamiento.clicked.connect(self.mostrar_tratamiento)
        self.right_layout.addWidget(self.btn_tratamiento)
    def selected_dis(self, item):                          # Al hacer clic en un item
        self.actual_dis = item.text()
        self.btn_tratamiento.setText(f"{self.actual_dis}")

    def mostrar_tratamiento(self):
        item = self.lista.currentItem()
        if not item:
            QMessageBox.warning(self, "Aviso", "Seleccione una enfermedad primero.")
            return
        self.enfermedad_actual = item.text()

        QMessageBox.information(
            self,
            "Life - Datos Recopilados",
            f"Enfermedad a Analizar: {self.enfermedad_actual}\n"
            f"{self.sistema_actual} | Edad: {self.edad_actual}\n"
            "Recomendación: descanso, hidratación y control médico profesional.\n"
        )

        self.clear_right_panel()
        self.clear_right_panel()
        self.txt_oms.setHtml("<h2><center>Patogeno Listo</center></h2>"
                             f"<h2><center>{self.enfermedad_actual}\n</center></h2>"
                             "<p><center>Informacion breve de la enfermedad</center></p>"
                             "<p><center>Si desea analizar de nuevo con parametros diferentes, simplemente haga click en el boton Analisis de Patologias</center></p>")
        self.txt_wait.setHtml("<b><center>¡Listo! Datos encontrados para el</center></b>"
                              f"<p><center>{self.sistema_actual} | Edad: {self.edad_actual}</center></p>")
        self.right_layout.addWidget(self.txt_oms, 1)
        self.right_layout.addWidget(self.newlabel)
        self.right_layout.addWidget(self.txt_wait, 1)
        if os.path.exists(ACTIVATION_FILE): # Verificar activación
            self.enable_act_buttons()
            self.enable_side_buttons()
        else:
            self.enable_side_buttons()
        enfermedad_actual=self.enfermedad_actual
        self.disease_win = DiseasePatogen(enfermedad_actual)
        self.disease_win.show()

    #-------------------------FIN DE FUNCIONES DE SELECCION JERARQUICA

    #-------------------------FUNCIONES AUXILIARES
    def show_info(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Lifeness Simulator Version 3.5")
        dialog.setMinimumSize(600, 500)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #141414;
                color: #e0e0e0;
                font-family: 'Segoe UI';
            }
            QLabel#title {
                font-size: 22px;
                font-weight: bold;
                color: #00b7ff;
                margin-bottom: 10px;
            
            QTextEdit {
                background-color: #1e1e1e;
                color: #d6d6d6;
                border: none;
                font-size: 13px;
                line-height: 1.4;
                padding: 10px;
            }
            QPushButton {
                background-color: #2d2d2d;
                border-radius: 8px;
                padding: 6px 14px;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #404040;
            }
        """)

        banner_label = QLabel()
        banner_pixmap = QPixmap("assets/pictures/banner_lifeness.png")  # Ruta del banner
        if not banner_pixmap.isNull():
            banner_pixmap = banner_pixmap.scaledToWidth(640, Qt.SmoothTransformation)
        banner_label.setPixmap(banner_pixmap)
        banner_label.setAlignment(Qt.AlignCenter)
        banner_label.setStyleSheet("border: none; margin-bottom: 8px;")

    # --- Título debajo del banner ---
        title = QLabel("Información Técnica")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)

        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        info_text.setPlainText("""
            📖 DESCRIPCIÓN GENERAL
            Lifeness Project es un simulador biomédico interactivo 3D diseñado para el aprendizaje práctico 
            de los estudiantes en áreas científicas y tecnológicas. Su enfoque está basado en la 
            visualización dinámica del cuerpo humano, sus sistemas y enfermedades, integrando elementos 
            de biología, anatomía, y tecnología aplicada.

            🧬 PROPÓSITO ACADÉMICO
            El propósito del simulador es fomentar el pensamiento crítico y la comprensión de procesos 
            fisiológicos a través de la simulación visual. Es una herramienta educativa moderna que 
            permite explorar enfermedades, visualizar reacciones del cuerpo y analizar respuestas biológicas 
            de manera interactiva.

            ⚙️ FUNCIONALIDADES PRINCIPALES
            - Exploración 3D de modelos anatómicos masculinos y femeninos.
            - Simulación de sistemas humanos (respiratorio, nervioso, muscular, óseo, etc.).
    - Visualización por edad y relación con enfermedades.
    - Generación automática de reportes en formato DOCX y JSON.
    - Registro de usuario y activación personalizada.
    - Modo oscuro, animaciones suaves, y paneles interactivos.
    - Módulo “Extras” con visualización de órganos 3D específicos.

    🏛️ INSTITUCIONAL Y CIENTÍFICO
    El proyecto se desarrolla con fines educativos, alineado con estándares de la OMS y 
    recomendaciones pedagógicas actuales para el aprendizaje STEM (Ciencia, Tecnología, 
    Ingeniería y Matemáticas). Lifeness Project promueve la integración entre informática 
    y biomedicina.

    🔧 DESARROLLO TÉCNICO
    - Lenguaje: Python 3.12
    - Librerías principales: PySide6, OpenGL, Numpy, PyQtGraph.
    - Arquitectura: Modelo orientado a clases con GUI modular.
    - Exportaciones automáticas: JSON y DOCX.
    - Interfaz optimizada para Windows 10/11 (x64).

    👩‍💻 EQUIPO DE DESARROLLO
    El equipo de Lifeness Project está conformado por estudiantes e investigadores en informática 
    biomédica, comprometidos con la innovación educativa y la accesibilidad del conocimiento 
    científico mediante simulaciones digitales interactivas.

    📅 VERSIÓN Y FECHA
    Versión: 1.0.0
    Fecha de desarrollo: Octubre 2025

    📘 DERECHOS Y LICENCIA
    Este software está protegido bajo uso educativo. Su reproducción parcial o total sin 
    autorización académica está prohibida. Proyecto desarrollado para instituciones de 
    educación superior y centros científicos.

    🌐 CONTACTO Y SOPORTE
    Para soporte técnico o información adicional:
    Correo institucional: support@lifenessproject.org
    Página web oficial: www.lifenessproject.edu
        """)
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(dialog.close)

        layout = QVBoxLayout(dialog)
        layout.addWidget(banner_label)
        layout.addWidget(title)
        layout.addWidget(info_text)
        layout.addWidget(btn_close, alignment=Qt.AlignRight)

        dialog.setLayout(layout)
        dialog.exec()

    def show_credits(self):
        dlg = AuthorsDialog()
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

    def change_model(self):
        current_gender = "male" if self.gl_widget.current_model == self.gl_widget.model_male else "female"
        new_gender = "female" if current_gender == "male" else "male"
        self.gl_widget.set_gender_model(new_gender)
        QMessageBox.information(self, "Modelo 3D", f"Modelo cambiado a {new_gender}.")
    
    def show_extras(self):
        self.extra_window = ExtraWindow(self)
        self.extra_window.show()
    
    def show_help(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Ayuda y Soporte")
        help_text = ("""
        <h2>🧭 Guía rápida del simulador</h2>
        <ul>
            <li>Selecciona un sistema (respiratorio, nervioso, etc.)</li>
            <li>Escoge la edad del paciente</li>
            <li>Selecciona una enfermedad</li>
            <li>Visualiza el modelo 3D y su descripción interactiva</li>
        </ul>

        <h3>⚙️ Controles del visualizador 3D</h3>
        <ul>
            <li>Click izquierdo: rotar el modelo</li>
            <li>Rueda del ratón: acercar / alejar</li>
            <li>Doble clic: centrar el modelo</li>
        </ul>

        <h3>🧠 Atajos del simulador</h3>
        <ul>
            <li><b>Ctrl + R</b>: Reiniciar vista</li>
            <li><b>Ctrl + S</b>: Guardar reporte</li>
            <li><b>Esc</b>: Salir</li>
        </ul>

        <h3>👨‍💻 Acerca de</h3>
        <p><b>Lifeness Simulator v1.0</b><br>
        Simulador biomédico educativo desarrollado con Python y PySide6.<br>
        Desarrollado por el equipo <b>Lifeness Project</b>.</p>
        """)
        dlg.setText(help_text)
        dlg.exec()
        
    def show_registration(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Life | Clave de registro")
        dialog.setFixedSize(900, 525)
        layout = QVBoxLayout(dialog)
        pict=QLabel()
        acces_lab=QLabel("Registre el producto y obtenga el acceso EXCLUSIVO")
        acces_lab.setFont(QFont("Comic Sans", 20))
        acces_lab.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(acces_lab) # Titulo centrado

        pict.setPixmap(QPixmap(os.path.join(ASSETS_DIR, "pictures/logos", "modern_logo.png")).scaled(225, 225, QtCore.Qt.KeepAspectRatio))
        layout.addWidget(pict, alignment=QtCore.Qt.AlignCenter) # Agregamos y centramos la imagen
        label = QLabel("Registre su producto para obtener soporte técnico, acceso a recursos exclusivos,\n"
                       "modelos nuevos y mensajes especiales por parte del equipo.")
        layout.addWidget(label) # Agregamos texto informativo

        self.input_key = QLineEdit()
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Ingrese su nombre")
        self.input_key.setPlaceholderText("XXX-XXX-XXX-XXX")
        self.input_key.setEchoMode(QLineEdit.Password)

        layout.addWidget(self.input_name) # Campo de entrada para el nombre
        layout.addWidget(self.input_key) # Campo de entrada para la clave

        label_two= QLabel("Para registrar el producto, y obtener el acceso completo, consulte el libro 'Lifeness Booklet'\n"
                          "o bien contacte con su docente guia para completar el proceso de registro.")
        layout.addWidget(label_two) # Texto adicional

        btn_ok = AnimatedButton("Aceptar")
        btn_ok.clicked.connect(lambda: self.check_key(dialog))
        layout.addWidget(btn_ok)
        dialog.exec()

    def author_regards(self):
        dlg = AuthorsDialog()
        dlg.exec()

    def check_key(self, dialog):
        correct_key = "RAY-155-345-FGS"
        name = self.input_name.text().strip()
        key = self.input_key.text().strip()
        if not name or not key:
            QMessageBox.warning(dialog, "Error", "Complete nombre y clave.")
            return
        # simple check
        if key != correct_key:
            QMessageBox.warning(self, "Error", "Clave de producto incorrecta.")
            self.input_key.clear()
            self.input_key.setFocus()
            return
        try:
            activate=Activation()
            activate.save_activation(name, key)
            QMessageBox.information(self, "Life | Exito de Registro", f"Producto Registrado con Exito\nBienvenido {name}.")
            self.enable_act_buttons()
            dialog.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo guardar: {e}")
    
    def clear_right_panel(self):
        while self.right_layout.count():
            child = self.right_layout.takeAt(0)
            if child.widget():
                child.widget().destroy()

    def disable_act_buttons(self):
        for button in self.act_buttons:
            button.setEnabled(False)
            button.setStyleSheet("""
                QPushButton{
                    background-color: #3A3E4A;
                    color: white;
                    font: bold 12pt "Segoe UI";
                    border-radius: 10px;
                    padding: 8px 16px;
                }
                QPushButton:hover{
                    background-color: #0BD4D4;
                }
                QPushButton:pressed{
                    background-color: #ABABAB;
                }
                QLabel{
                    font: 12pt "Segoe UI";
                }
            """)
    
    def enable_act_buttons(self):
        for button in self.act_buttons:
            button.setEnabled(True)
            button.setStyleSheet("""
                QPushButton{
                    background-color: #0078D7;
                    color: white;
                    font: bold 12pt "Segoe UI";
                    border-radius: 10px;
                    padding: 8px 16px;
                }
                QPushButton:hover{
                    background-color: #0BD4D4;
                }
                QPushButton:pressed{
                    background-color: #ABABAB;
                }
                QLabel{
                    font: 12pt "Segoe UI";
                }
            """)
    
    def disable_side_buttons(self):
        for button in self.menu_buttons:
            button.setEnabled(False)
            button.setStyleSheet("""
                QPushButton{
                    background-color: #3A3E4A;
                    color: white;
                    font: bold 12pt "Segoe UI";
                    border-radius: 10px;
                    padding: 8px 16px;
                }
                QPushButton:hover{
                    background-color: #0BD4D4;
                }
                QPushButton:pressed{
                    background-color: #ABABAB;
                }
                QLabel{
                    font: 12pt "Segoe UI";
                }
            """)

    def enable_side_buttons(self):
        for button in self.menu_buttons:
            button.setEnabled(True)
            button.setStyleSheet("""
                QPushButton{
                    background-color: #0078D7;
                    color: white;
                    font: bold 12pt "Segoe UI";
                    border-radius: 10px;
                    padding: 8px 16px;
                }
                QPushButton:hover{
                    background-color: #0BD4D4;
                }
                QPushButton:pressed{
                    background-color: #ABABAB;
                }
                QLabel{
                    font: 12pt "Segoe UI";
                }
            """)
 
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

    def show_settings_dim(self):
        dlg = SettingsDialog(self, current_lang=self.meta.idioma)
        if dlg.exec() == QDialog.Accepted:
            vals = dlg.values()
            logger.info("Ajustes aplicados en Interactive: %s", vals)

    def confirm_exit(self):
        resp = QMessageBox.question(self, "Life", "¿Desea salir?", QMessageBox.Yes | QMessageBox.No)
        if resp == QMessageBox.Yes:
            QMessageBox.information(self, "Life", "Lifeness Simulator | Simulation that transforms\nMuchas gracias por su tiempo.")
            logger.info("Shutting Down Life ..")
            logger.info("Success.")
            logger.info("Gracias Por Usar Lifeness Simulator. Version %s", self.meta.version)
            QApplication.instance().quit()

    def generate_report(self):
        rg = ReportGenerator(self.meta)
        path = rg.generate()
        answer = QMessageBox.question(self, "Life", f"Reporte listo. \n¿Desea guardarlo en {path}?.", QMessageBox.Yes | QMessageBox.No)
        if answer == QMessageBox.Yes:
            QMessageBox.information(self, "Success", "¡Excelente! Reporte exitosamente guardado.")
    
    def on_play(self):  # Timeline Controls
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

    def on_model_slider_changed(self, value):
        if value < 33:
            model_path = "assets/models/humano.obj"
        elif value < 66:
            model_path = "assets/models/musculo.obj"
        else:
            model_path = "assets/models/esqueleto.obj"

        if getattr(self, "_current_model", None) == model_path:
            return
        self.current_model = model_path
        self.animate_model_transition(model_path)

    def animate_model_transition(self, model_path):
        effect = QGraphicsOpacityEffect(self.gl_widget)
        self.gl_widget.setGraphicsEffect(effect)

        fade_out = QPropertyAnimation(effect, b"opacity")
        fade_out.setDuration(700)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)

        def on_fade_out_finished():
            self.gl_widget.load_model(model_path)
            fade_in = QPropertyAnimation(effect, b"opacity")
            fade_in.setDuration(700)
            fade_in.setStartValue(0.0)
            fade_in.setEndValue(1.0)
            fade_in.start()

        fade_out.finished.connect(on_fade_out_finished)
        fade_out.start()

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def on_escape(self):
        if self.isFullScreen():
            self.showNormal()
 #-------------------------FIN DE FUNCIONES AUXILIARES

# ---------------------------------------------------------------------------
class SplashWindow(QWidget):
    def __init__(self, meta: MetaProyecto):
        super().__init__()
        self.meta = meta
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)

        ico_path = os.path.join(ASSETS_DIR, "pictures/icons", "ico1.ico") # Ícono de la ventana
        self.setWindowIcon(QIcon(ico_path))

        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.resize(800, 420)
        layout = QVBoxLayout(self)
        title = QLabel(self.meta.titulo)
        title.setFont(QFont("Montserrat Semibold", 30))
        title.setStyleSheet("color: white;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        sub = QLabel(f"{self.meta.descripcion}\n\n\n{self.meta.autores}\nVersión: {self.meta.version}\n{self.meta.fecha}")
        sub.setStyleSheet("color: #ddd;")
        sub.setAlignment(QtCore.Qt.AlignCenter)
        sub.setFont(QFont("Open Sans", 10))
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
class WelcomeScreen(QWidget):
    def __init__(self, main_window_class, user):
        super().__init__()
        self.main_window_class = main_window_class
        self.user_name = user

        # Ventana sin bordes, tamaño fijo
        self.setWindowTitle("Life | Licenced to: "+(self.user_name if self.user_name else "Demo N/A"))
        self.setWindowFlag(Qt.FramelessWindowHint) # Sin bordes
        self.setFixedSize(500, 500)

        ico_path = os.path.join(ASSETS_DIR, "pictures/icons", "ico1.ico") # Ícono de la ventana
        self.setWindowIcon(QIcon(ico_path))

        # Fondo GIF (tú colocas el tuyo)
        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, 800, 500)
        gif_path = os.path.join(ASSETS_DIR, "backgrounds", "bg5.gif")
        self.movie = QMovie(gif_path)
        self.bg_label.setMovie(self.movie)
        self.movie.start()

        self.text = QLabel("Bienvenido(a) a Lifeness Simulator\n"+(self.user_name if self.user_name else ""))
        self.text.setAlignment(Qt.AlignCenter)
        self.text.setStyleSheet("color: white;")
        self.text.setFont(QFont("Comic Sans", 20))

        # Botones (ocultos al inicio)
        self.btn_readme = AnimatedButton("Abrir README.md")
        self.btn_start = AnimatedButton("Continuar a Life")
        self.btn_exit = AnimatedButton("Salir")
        for btn in (self.btn_readme, self.btn_start, self.btn_exit):
            btn.setFixedWidth(200)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 180);
                    color: white;
                    border: 1px solid white;
                    padding: 10px; border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: rgba(100, 100, 100, 180);
                }
            """)

        self.btn_readme.clicked.connect(self.abrir_readme)
        self.btn_start.clicked.connect(self.continuar)
        self.btn_exit.clicked.connect(QApplication.instance().quit)

        # Layout general
        layout = QVBoxLayout(self)
        
        layout.addWidget(self.text, alignment=Qt.AlignCenter)
        layout.addSpacing(25)
        layout.addWidget(self.btn_start, alignment=Qt.AlignCenter)
        layout.addWidget(self.btn_readme, alignment=Qt.AlignCenter)
        layout.addWidget(self.btn_exit, alignment=Qt.AlignCenter)
        self.setLayout(layout)

    def abrir_readme(self):
        documents_dir = user_documents_dir()
        path = os.path.join(documents_dir, "Lifeness Simulator")
        os.makedirs(path, exist_ok=True)
        dst= os.path.join(path, "README HERE AND NOW.md")
        src_readme= os.path.join(BASE_DIR, "docs", "README.md")

        try:
            shutil.copyfile(src_readme, dst)
            webbrowser.open(f"file:///{dst}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo abrir el README.md: {e}")

    def continuar(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Bienvenido(a) "+(self.user_name if self.user_name else "")+" a Life")
        dialog.setFixedSize(800, 425)
        layout = QVBoxLayout(dialog)
        pict=QLabel()
        acces_lab=QLabel("L I F E")
        acces_lab.setFont(QFont("Verdana", 24))
        acces_lab.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(acces_lab) # Titulo centrado

        pict.setPixmap(QPixmap(os.path.join(ASSETS_DIR, "pictures", "modern_logo.png")).scaled(225, 225, QtCore.Qt.KeepAspectRatio))
        layout.addWidget(pict, alignment=QtCore.Qt.AlignCenter) # Agregamos y centramos la imagen

        label = QLabel("Donde la simulacion se transforma, nosotros ya habremos manejado los cambios")
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setFont(QFont("Arial", 15))
        layout.addWidget(label) # Agregamos texto informativo

        dialog.exec()
        self.close()

# ---------------------------------------------------------------------------
class AppController: # Controla el flujo de la aplicación
    def __init__(self):
        meta=MetaProyecto()
        self.splash=SplashWindow(meta)

    def run(self):
        self.splash.show()
        self.splash.play()
        self.splash.close()
        self.open_main()
        self.show_welcome()
        
    def show_welcome(self):
        if os.path.exists(ACTIVATION_FILE):  # Leer usuario registrado
            with open(ACTIVATION_FILE, "r", encoding="utf-8") as f:
                self.data = json.load(f)
                user = self.data.get("user")
        else:
            user=""
        self.welcome = WelcomeScreen(MainWindow, user)
        self.welcome.show()

    def open_main(self):
        meta=MetaProyecto()
        class ParserFake:
            def __init__(self, meta):
                self.meta=meta
        parser=ParserFake(meta)
        self.main_window = MainWindow(parser, meta)
        self.main_window.show()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    controller=AppController()
    controller.run()
    sys.exit(app.exec())