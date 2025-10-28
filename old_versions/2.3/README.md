# 								              **Lifeness Project — Simulation that transforms**
###                                                            **Life**

## **Descripción general del programa**

**Lifeness Simulator (Life)** es un **simulador biomédico interactivo**, aprobado profesionalmente, desarrollado en **Python 3.12**, diseñado para transformar la enseñanza y el aprendizaje de la medicina mediante la integración de la **biotecnología, la simulación 3D y la informática aplicada**.
El proyecto ofrece un entorno digital donde los estudiantes pueden **visualizar, explorar y comprender enfermedades humanas** de forma dinámica, científica y educativa, convirtiendo el conocimiento anatómico y fisiológico en una experiencia inmersiva e intuitiva.

Su desarrollo está inspirado en la necesidad de **modernizar los recursos tecnológicos de la educación médica**, ofreciendo una herramienta accesible, ética y científicamente fundamentada que refuerza el aprendizaje previo a futuras especializaciones clínicas o biomédicas.

Su diseño busca ofrecer una experiencia educativa cercana a una aplicación moderna, 
permitiendo visualizar de manera clara las enfermedades más comunes, tanto en relación con los distintos sistemas del cuerpo humano, como con las etapas de desarrollo de los niños y adolescentes de hoy en día.

Las estadísticas que se presentan son reales y actualizadas, lo que garantiza un enfoque riguroso y confiable. Nuestro compromiso está enfocado en la educación de calidad, por lo que esperamos que este simulador sea de tu agrado y lo utilices con responsabilidad.
---

## **Nuestra vision**

> **Demostrar la utilidad del simulador como recurso tecnológico-científico que fortalezca las competencias formativas de los estudiantes, preparándolos para futuras especializaciones mediante la comprensión visual de patologías y analisis de enfermedades.**

## **Nuestra Mision**

> **Convertirse en la principal plataforma educativa de simulación biomédica interactiva, integrando tecnología 3D, inteligencia científica y biotecnología para transformar la enseñanza médica en una experiencia dinámica, accesible y globalmente innovadora.**

---

## **Características principales**

* **Interfaz moderna con PySide6 (Qt6):** entorno gráfico profesional y personalizable.
* **Visualizador 3D humano (PyOpenGL):** modelo anatómico rotativo, interactivo y con fondo dinámico.
* **Simulación educativa:** muestra la evolución de enfermedades según categorías (virus, bacterias, hongos, parásitos, priones).
* **Panel de información científica:** datos basados en fuentes académicas y contenido clínico educativo.
* **Gestín de ajustes:** control de brillo, contraste, idioma, pantalla completa y sensibilidad de rotación.
* **Generación automática de reportes (.docx):** documentación formateada con APA 7, exportada a la carpeta Documentos del usuario.
* **Pantalla de bienvenida animada:** introducción institucional con transiciones suaves.
* **Logs y registro de eventos:** control interno para monitoreo de uso y estabilidad.
* **Multiplataforma y empaquetable (.exe):** compatible con Windows 10+ (PyInstaller).

---

## **Arquitectura del sistema**

```
Life/
│
├── ui/             # Interfaces gráficas (PySide6)
├── core/           # Lógica principal y controladores
├── assets/         # Imágenes, íconos, GIFs , Modelos 3D y texturas.
├── export/         # Reportes generados (.docx)
├── docs/           # Documentación y plantillas
├── logs/           # Registros del sistema
└── life.py         # Archivo principal de ejecución
```

---

## **Flujo de la aplicación**

1. **Pantalla de bienvenida**
2. **Menú principal** 
3. **Interacción con el simulador**
4. **Consulta informativa**
5. **Generación de reporte**
6. **Salida controlada**

---

## **Dependencias  (Python)**

| Librería                        | Uso                                    |
| ------------------------------- | -------------------------------------- |
| **PySide6**                     | Interfaz gráfica (Qt6)                 |
| **PyOpenGL**                    | Renderizado del modelo 3D              |
| **Pillow (PIL)**                | Carga de imágenes y GIFs               |
| **platformdirs**                | Guardado de reportes en Documentos     |
| **python-docx**                 | Generación automática de reportes Word |
| **numpy / pandas / matplotlib** | Procesamiento numérico y visualización |
| **logging**                     | Registro de eventos y errores          |

Instalación rápida:
> **Inserte el disco oficial o vease el libro para poder instalar el software oficial y registrarlo.**

##  **Importancia académica**

**Lifeness Project** impulsa la formación biotecnologica y cientifica de las personas en estas 4 sencillas fases:

* Fomentar la **comprensión visual de procesos fisiológicos y patológicos**.
* Promover el uso de **tecnología ética y educativa en entornos clínicos**.
* Integrar el conocimiento médico con la **informática aplicada**.
* Servir como herramienta de apoyo para **docentes, estudiantes e investigadores**.

---

## **Nota ética**

> *El contenido incluido en Lifeness Project tiene fines estrictamente educativos y no sustituye la evaluación ni el diagnóstico médico profesional.*

---

**Supervisión académica:** Docentes y estudiantes.

**Año:** 2025

**Versión Final:** 3.1

---

## 💡 **Oficial Slogan**

> **“Simulation that transforms.”**

---

Si has llegado hasta aqui. Agradecemos profundamente tu interés en el proyecto y esperamos que esta herramienta contribuya significativamente a tu proceso de aprendizaje.

# 			Equipo de trabajo – Lifeness Project