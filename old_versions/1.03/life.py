# Lifeness Simulator

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
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QListWidget,
    QTextEdit, QHBoxLayout, QVBoxLayout, QSplitter, QSlider, QMessageBox,
    QDialog, QFormLayout, QComboBox
)
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

LOG_FILE = os.path.join(LOGS_DIR, "life_app.log")
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
logger.info("Init Life Proccess..")

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
    autores: str = "Matthias Jimenez, Jose Herbas, Diego Guerron, Juandiego Vizuete"
    version: str = "1.02"
    fecha: str = "2025-10-03"
    idioma: str = "es"
    descripcion: str = "Simulador educativo."

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
                logger.info("OBJ cargado: %s (v:%d f:%d)", filename, len(self.vertices), len(self.faces))
            except Exception as e:
                logger.exception("Error cargando OBJ %s: %s", filename, e)
        else:
            logger.warning("OBJ no encontrado: %s", filename)

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
            logger.exception("Error creando GL list para %s: %s", self.filename, e)
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
        self.model_male_path = os.path.join(ASSETS_DIR, "male.obj")
        self.model_female_path = os.path.join(ASSETS_DIR, "female.obj")
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
        self.frame_delay = 0.1  # 100 ms entre frames

    # Interacción mouse
    def mousePressEvent(self, event):
        try:
            self.last_mouse_x = event.position().x()
        except AttributeError:
            # fallback para versiones que usan event.x()
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

        # Intentar cargar gif, pero manejar ausencia
        gif_path = os.path.join(ASSETS_DIR, "backgrounds", "bg.gif")
        if not os.path.isfile(gif_path):
            # intentar ruta base assets
            gif_path = os.path.join(ASSETS_DIR, "backgrounds", "bg.gif")
        if os.path.isfile(gif_path):
            try:
                self.load_gif(gif_path)
            except Exception as e:
                logger.warning("No se pudo cargar GIF de fondo: %s", e)
                self.bg_frames = []
        else:
            logger.info("No se encontró GIF de fondo en assets; se usará fondo sólido.")
            self.bg_frames = []
        logger.debug("initializeGL OK")

    def load_gif(self, path):
        """Carga un GIF animado y lo convierte en texturas OpenGL"""
        if not os.path.isfile(path):
            logger.warning("load_gif: archivo no existe: %s", path)
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
        logger.info("GIF cargado con %d frames", len(self.bg_frames))

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h if h > 0 else 1)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(50.0, w / max(1.0, h), 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # --- Fondo (GIF animado) ---
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
            # fondo sólido (ej. gris oscuro)
            glClearColor(0.05, 0.05, 0.06, 1.0)

        # --- Modelo 3D encima del fondo ---
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glLoadIdentity()
        # mantener el objeto centrado y rotarlo en su sitio
        glTranslatef(0.0, 0.0, self.zoom)
        glRotatef(self.yaw, 0.0, 1.0, 0.0)

        # efecto reacción pulsante (definición temprana, usado en coloring)
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
        self.resize(420, 200)
        layout = QFormLayout(self)
        self.sldr_brightness = QSlider(QtCore.Qt.Horizontal)
        self.sldr_brightness.setRange(0, 100); self.sldr_brightness.setValue(50)
        self.sldr_contrast = QSlider(QtCore.Qt.Horizontal)
        self.sldr_contrast.setRange(0, 100); self.sldr_contrast.setValue(50)
        self.chk_fullscreen = QtWidgets.QCheckBox("Pantalla completa")
        self.cmb_lang = QComboBox(); self.cmb_lang.addItems(["es", "en"]); self.cmb_lang.setCurrentText(current_lang)
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
        self.output_dir = os.path.join(documents_dir, "Lifeness Simulator")
        os.makedirs(self.output_dir, exist_ok=True)

        # Plantilla incluida en el exe (gracias a resource_path)
        self.out_path = os.path.join(self.output_dir, "life_report.docx")

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
        # asignar parser y meta al inicio para evitar referencias antes de inicializar
        self.parser = parser
        self.meta = meta

        self.setWindowTitle(f"{self.meta.titulo} — Lifeness Project")
        # intentar icono (silencioso si no existe)
        ico_path = os.path.join(ASSETS_DIR, "icons", "ico1.ico")
        if not os.path.isfile(ico_path):
            ico_path = os.path.join(ASSETS_DIR, "icons", "ico1.ico")
        if os.path.isfile(ico_path):
            self.setWindowIcon(QIcon(ico_path))

        self.resize(1400, 820)
        main_split = QSplitter(QtCore.Qt.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(6, 6, 6, 6)

        self.btn_info = QPushButton("Creditos")
        self.btn_sim = QPushButton("Enfermedades")
        self.btn_ajustes = QPushButton("Ajustes")
        self.btn_report = QPushButton("Generar Reporte")
        self.btn_exit = QPushButton("Salir")
        for btn in (self.btn_info, self.btn_sim, self.btn_ajustes, self.btn_report, self.btn_exit):
            btn.setMinimumHeight(56)
            btn.setFont(QFont("Arial", 11))
            btn.setToolTip("Haga clic para ejecutar la acción")
            left_layout.addWidget(btn)
        left_layout.addStretch()

        left_scroll = QtWidgets.QScrollArea()
        left_scroll.setWidget(left_widget)
        left_scroll.setWidgetResizable(True)
        left_scroll.setFixedWidth(320)
        main_split.addWidget(left_scroll)

        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(6, 6, 6, 6)

        title_lbl = QLabel(self.meta.titulo)
        title_lbl.setFont(QFont("Arial Black", 18))
        title_lbl.setAlignment(QtCore.Qt.AlignCenter)
        center_layout.addWidget(title_lbl)

        self.gl_widget = GLHumanWidget()
        center_layout.addWidget(self.gl_widget, 1)

        timeline_bar = QWidget()
        t_layout = QHBoxLayout(timeline_bar)
        self.btn_play = QPushButton("Play")
        self.btn_pause = QPushButton("Pause")
        self.cmb_speed = QComboBox(); self.cmb_speed.addItems(["0.5x", "1x", "2x"]); self.cmb_speed.setCurrentText("1x")
        self.tslider = QSlider(QtCore.Qt.Horizontal); self.tslider.setRange(0, 100); self.tslider.setValue(0)
        t_layout.addWidget(self.btn_play); t_layout.addWidget(self.btn_pause); t_layout.addWidget(self.cmb_speed); t_layout.addWidget(self.tslider)
        center_layout.addWidget(timeline_bar)
        main_split.addWidget(center_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(6, 6, 6, 6)
        self.txt_oms = QTextEdit()
        self.txt_oms.setReadOnly(True)
        self.txt_oms.setHtml("<b>OMS - Recursos y referencias</b><p>Este simulador es material educativo. No sustituye atención médica profesional.</p>")
        right_layout.addWidget(self.txt_oms, 1)
        self.lst_enf = QListWidget()
        right_layout.addWidget(QLabel("Enfermedades (seleccione):"))
        right_layout.addWidget(self.lst_enf, 1)
        self.btn_tratamiento = QPushButton("Tratamiento")
        right_layout.addWidget(self.btn_tratamiento)
        main_split.addWidget(right_widget)
        main_split.setStretchFactor(1, 2)

        central = QWidget()
        central_layout = QHBoxLayout(central)
        central_layout.addWidget(main_split)
        self.setCentralWidget(central)

        # Conexiones
        self.btn_info.clicked.connect(self.show_info)
        self.btn_sim.clicked.connect(self.show_sim_categories)
        self.btn_ajustes.clicked.connect(self.show_settings)
        self.btn_exit.clicked.connect(self.confirm_exit)
        self.btn_report.clicked.connect(self.generate_report)
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

        # Poblamos categorias y enfermedades iniciales desde parser (ahora interno)
        self.populate_categories()

        self.timeline_playing = False
        self.timeline_speed = 1.0
        self.timeline_timer = QtCore.QTimer()
        self.timeline_timer.timeout.connect(self.advance_timeline)

    # ---- UI helpers y acciones ----
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
        dlg.setWindowTitle("Creditos")
        info = (
            f"<b>{self.meta.titulo}</b><br>"
            f"Autores: {self.meta.autores}<br>"
            f"Versión: {self.meta.version}    Fecha: {self.meta.fecha}<br>"
            f"Idioma: {self.meta.idioma}<br><br>"
            f"{self.meta.descripcion}<br><br>"
            "Nota: Material educativo. No sustituye evaluación médica profesional."
        )
        dlg.setText(info)
        dlg.exec()

    def show_sim_categories(self):
        self.lst_enf.clear()
        cats = getattr(self.parser, "categorias", [])
        for cat in cats:
            self.lst_enf.addItem(f"[Categoria] {cat}")
            item = self.lst_enf.item(self.lst_enf.count() - 1)
            item.setToolTip(f"Mostrar enfermedades de {cat}")
        self.gl_widget.apply_reaction(None)

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
        resp = QMessageBox.question(self, "Lifeness Simulator", "¿Desea salir?", QMessageBox.Yes | QMessageBox.No)
        if resp == QMessageBox.Yes:
            QMessageBox.information(self, "Exit", "Lifeness Simulator.\nMaterial educativo.")
            logger.info("Shutting Down Life ..")
            logger.info("Success.")
            logger.info("Gracias Por Usar Lifeness Simulator. Version %s", self.meta.version)
            QApplication.instance().quit()

    def generate_report(self):
        rg = ReportGenerator(self.meta, self.parser.enfermedades)
        path = rg.generate()
        QMessageBox.information(self, "Reporte exitoso", f"Reporte guardado en: {path}")

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
            f"<p style='color:darkred;'>Advertencia: Material educativo - No sustituye la evaluación médica profesional.</p>"
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
        sub = QLabel(f"{self.meta.descripcion}\nAutores: {self.meta.autores}\nVersión: {self.meta.version} {self.meta.fecha}")
        sub.setStyleSheet("color: #FFFFFF; font-size:28px; font-weight:bold;")
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
    # Definir metadatos y datos internos (ya no dependemos de Doc1.docx)
    meta = MetaProyecto()
    # Ejemplos de enfermedades (puedes editar/añadir)
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