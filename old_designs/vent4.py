import tkinter as tk  # Importamos la biblioteca gráfica Tkinter

# Creamos una clase que hereda de la ventana principal de Tkinter
class LifenessProject(tk.Tk):
    def __init__(self):
        super().__init__()  # Inicializa la ventana principal

        # Configuraciones generales de la ventana
        self.title("Lifeness Project")           # Título que aparece en la parte superior de la ventana
        self.geometry("600x450")                 # Tamaño inicial de la ventana (ancho x alto)
        self.minsize(400, 300)                   # Tamaño mínimo al que se puede reducir la ventana
        self.configure(bg="orange")               # Color de fondo (sirve como "borde llamativo")

        # Creamos un Frame (marco) en el centro de la ventana
        self.frame = tk.Frame(
            self,                                # Ventana donde se coloca el marco
            bg="cyan",                          # Fondo del marco
            bd=10,                               # Grosor del borde
            relief="sunken",                      # Estilo del borde (relieve)
            width=400,                           # Ancho del marco
            height=250                           # Alto del marco
        )
        # Colocamos el marco centrado en la ventana
        self.frame.place(relx=0.5, rely=0.5, anchor="center")

        # ---------- CONTENIDO DEL MARCO ----------
        # Título dentro del marco
        self.label_titulo = tk.Label(
            self.frame,
            text="Lifeness Project",
            bg="cyan",
            fg="darkgreen",
            font=("Arial", 18, "bold")
        )
        self.label_titulo.pack(pady=(10, 5))  # Espacio vertical

        # Texto informativo
        self.label_descripcion = tk.Label(
            self.frame,
            text="Simulador educativo para el aprendizaje\nde la salud, microbiología y plantas.",
            bg="cyan",
            fg="black",
            font=("Arial", 12),
            justify="center"
        )
        self.label_descripcion.pack(pady=5)

        # Otro texto explicativo
        self.label_info = tk.Label(
            self.frame,
            text="Este programa permite observar el crecimiento vegetal\ny entender enfermedades microbianas.",
            bg="cyan",
            fg="gray25",
            font=("Arial", 10),
            justify="center"
        )
        self.label_info.pack(pady=(5, 10))

        # Botón para cerrar la aplicación
        self.btn_cerrar = tk.Button(
            self.frame,
            text="Cerrar",
            bg="lightgray",
            command=self.destroy
        )
        self.btn_cerrar.pack()

        # Vinculamos el evento de redimensionar la ventana
        self.bind("<Configure>", self.reubicar_frame)

    # Esta función reubica el marco al centro si se cambia el tamaño de la ventana
    def reubicar_frame(self, event=None):
        self.frame.place(relx=0.5, rely=0.5, anchor="center")


# ------------- EJECUCIÓN DEL PROGRAMA -------------
if __name__ == "__main__":
    app = LifenessProject()  # Creamos una instancia de la ventana
    app.mainloop()           # Ejecutamos el bucle principal de la interfaz
