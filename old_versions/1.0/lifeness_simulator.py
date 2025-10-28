"""

Lifeness Proyect | Lifeness Simulator: Life
Material educativo profesional. No sustituye la atencion medica real.

"""

import os
import sys
import time
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QSurfaceFormat
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton,
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QMessageBox,
    QListWidget, QTextEdit, QSlider
)
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *
from objloader import OBJ


# ---------------- Splash Screen ---------------- #
class SplashScreen(QWidget):
    """Pantalla de bienvenida por 5 segundos"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        title = QLabel("Lifeness Proyect")
        title.setFont(QFont("Arial Black", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Educative Simulator - Real Life' Internal Life")
        subtitle.setAlignment(Qt.AlignCenter)

        authors = QLabel("Autores: Matthias Jiménez; Jose Herbas; Diego Guerron; Juandiego Vizuete")
        authors.setAlignment(Qt.AlignCenter)

        version = QLabel("Versión 1.0 - 2025")
        version.setAlignment(Qt.AlignCenter)

        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(authors)
        layout.addWidget(version)
        layout.addStretch()

        self.setLayout(layout)


# ---------------- OpenGL Widget ---------------- #
class GLHumanWidget(QOpenGLWidget):
    """Render de modelo humano OBJ con reacciones"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.yaw = 0.0
        self.zoom = -6.0
        self.current_model = None
        self.model_male = OBJ(os.path.join("assets", "male.obj"))
        self.model_female = OBJ(os.path.join("assets", "female.obj"))
        self.current_model = self.model_male
        self.current_enfermedad_id = None
        self.reaction_start_time = 0.0

    def set_gender(self, g: str):
        """Cambiar modelo activo"""
        if g == "male":
            self.current_model = self.model_male
        else:
            self.current_model = self.model_female
        self.update()

    def initializeGL(self):
        glClearColor(0.2, 0.2, 0.2, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w / h if h != 0 else 1, 1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, -1.0, self.zoom)
        glRotatef(self.yaw, 0.0, 1.0, 0.0)

        # Reacción: parpadeo de color si hay enfermedad seleccionada
        if self.current_enfermedad_id is not None:
            elapsed = time.time() - self.reaction_start_time
            blink = abs((elapsed % 1.0) - 0.5) * 2
            glColor3f(1.0, blink, blink)
        else:
            glColor3f(0.9, 0.85, 0.8)

        if self.current_model:
            self.current_model.render()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.yaw += event.x() * 0.05
            self.update()

    def wheelEvent(self, event):
        self.zoom += event.angleDelta().y() / 120
        self.update()

    def aplicar_reaccion(self, enfermedad_id: str):
        """Simular reacción fisiológica"""
        self.current_enfermedad_id = enfermedad_id
        self.reaction_start_time = time.time()
        self.update()


# ---------------- Main Window ---------------- #
class MainWindow(QMainWindow):
    """Ventana principal del simulador"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Life")

        # Layout principal
        main_layout = QHBoxLayout()

        # Panel izquierdo: categorías
        self.categorias = QListWidget()
        self.categorias.addItems(["Bacterias", "Virus", "Hongos", "Parásitos", "Priones"])
        self.categorias.itemClicked.connect(self.mostrar_enfermedades)

        # Panel central: modelo 3D
        self.human_widget = GLHumanWidget()

        # Panel derecho: info OMS
        self.info_panel = QTextEdit()
        self.info_panel.setReadOnly(True)
        self.info_panel.setText("Información basada en OMS.\nMaterial educativo. No sustituye atención médica.")

        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.categorias)
        splitter.addWidget(self.human_widget)
        splitter.addWidget(self.info_panel)
        main_layout.addWidget(splitter)

        # Botones inferiores
        bottom_layout = QHBoxLayout()
        self.btn_info = QPushButton("Información")
        self.btn_settings = QPushButton("Ajustes")
        self.btn_exit = QPushButton("Salir")

        self.btn_info.clicked.connect(self.mostrar_info)
        self.btn_settings.clicked.connect(self.mostrar_ajustes)
        self.btn_exit.clicked.connect(self.confirmar_salida)

        bottom_layout.addWidget(self.btn_info)
        bottom_layout.addWidget(self.btn_settings)
        bottom_layout.addWidget(self.btn_exit)

        # Contenedor principal
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addLayout(main_layout)
        layout.addLayout(bottom_layout)
        self.setCentralWidget(container)

    # --- Funciones de botones --- #
    def mostrar_info(self):
        self.info_panel.setText(
            "Lifeness Proyect \n Autores: Mathias Jiménez\n Jose Herbas\n Diego Guerron\n Juandiego Vizuete"
            "Versión 1.0 - Lenguaje: Español\n"
            "Propósito: Simulador educativo.\n"
            "Nota: No sustituye la atención médica profesional."
        )

    def mostrar_ajustes(self):
        ajustes = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Brillo"))
        layout.addWidget(QSlider(Qt.Horizontal))
        layout.addWidget(QLabel("Contraste"))
        layout.addWidget(QSlider(Qt.Horizontal))
        layout.addWidget(QLabel("Volumen"))
        layout.addWidget(QSlider(Qt.Horizontal))
        ajustes.setLayout(layout)
        ajustes.setWindowTitle("Ajustes")
        ajustes.show()

    def confirmar_salida(self):
        reply = QMessageBox.question(
            self, "Confirmar salida",
            "¿Desea salir del simulador?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "Gracias", "Gracias por usar Lifeness Simulator.")
            QApplication.quit()

    def mostrar_enfermedades(self, item):
        categoria = item.text()
        self.info_panel.setText(f"Enfermedades de {categoria}.\nSeleccione una para simular reacción.")
        # Demo: aplicar reacción genérica
        self.human_widget.aplicar_reaccion(categoria)


# ---------------- Main App ---------------- #
def main():
    app = QApplication(sys.argv)

    # Splash screen
    splash = SplashScreen()
    splash.show()
    QTimer.singleShot(3000, splash.close)  # 3 segundos

    window = MainWindow()
    QTimer.singleShot(5000, window.show)  # Mostrar tras splash

    sys.exit(app.exec())


if __name__ == "__main__":
    main()