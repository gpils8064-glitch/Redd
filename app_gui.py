# -*- coding: utf-8 -*-
import customtkinter as ctk
from tkinter import filedialog
import threading
import os
import logic

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class RedditBotApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("TikTok Maker - Historias Reddit")
        self.geometry("950x800") 
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.ruta_imagen_titulo = None

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=180, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=4, sticky="nsew")
        ctk.CTkLabel(self.sidebar, text="Reddit Maker", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=20)
        ctk.CTkLabel(self.sidebar, text="Modo Series Auto", font=("Arial", 12), text_color="gray").grid(row=1, column=0, padx=20, pady=5)

        # Panel Principal
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.crear_interfaz()

    def crear_interfaz(self):
        # Titulo
        ctk.CTkLabel(self.main_frame, text="1. Nombre del Archivo:", font=("Arial", 14, "bold")).pack(pady=(20, 5), padx=20, anchor="w")
        self.entry_titulo = ctk.CTkEntry(self.main_frame, placeholder_text="Ej: Ejemplo de titulo", width=400)
        self.entry_titulo.pack(pady=5, padx=20, anchor="w")

        # Voz
        ctk.CTkLabel(self.main_frame, text="2. Seleccionar Voz:", font=("Arial", 14, "bold")).pack(pady=(20, 5), padx=20, anchor="w")
        
        # He quitado las tildes de los nombres para evitar errores de codificacion en Windows
        voces = [
            "Mexicano - Jorge (Narrador Clasico)", 
            "Argentino - Tomas (Joven)", 
            "Espanol - Alvaro (Documental)", 
            "USA Latino - Alonso (Neutro)"
        ]
        
        self.combo_voz = ctk.CTkComboBox(self.main_frame, values=voces, width=400, state="readonly")
        self.combo_voz.set("Mexicano - Jorge (Narrador Clasico)")
        self.combo_voz.pack(pady=5, padx=20, anchor="w")
        
        # Imagen
        ctk.CTkLabel(self.main_frame, text="3. (Opcional) Imagen del Post:", font=("Arial", 14, "bold")).pack(pady=(20, 5), padx=20, anchor="w")
        self.img_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.img_frame.pack(pady=5, padx=20, anchor="w", fill="x")
        self.btn_img = ctk.CTkButton(self.img_frame, text="Seleccionar Imagen", command=self.seleccionar_imagen, width=150)
        self.btn_img.pack(side="left", padx=(0, 10))
        self.lbl_ruta_img = ctk.CTkLabel(self.img_frame, text="Ninguna", text_color="gray")
        self.lbl_ruta_img.pack(side="left")

        # Historia
        ctk.CTkLabel(self.main_frame, text="4. Pega tu historia aqui:", font=("Arial", 14, "bold")).pack(pady=(20, 5), padx=20, anchor="w")
        self.txt_historia = ctk.CTkTextbox(self.main_frame, width=600, height=150)
        self.txt_historia.pack(pady=5, padx=20, fill="x")

        # Boton
        self.btn_generar = ctk.CTkButton(self.main_frame, text="RENDERIZAR SERIE", height=50, fg_color="#D32F2F", font=("Arial", 16, "bold"), command=self.iniciar_proceso)
        self.btn_generar.pack(pady=30, padx=20, fill="x")

        # Consola
        self.lbl_log = ctk.CTkLabel(self.main_frame, text="Consola:", font=("Arial", 12))
        self.lbl_log.pack(pady=(10, 0), padx=20, anchor="w")
        self.log_box = ctk.CTkTextbox(self.main_frame, height=100)
        self.log_box.pack(pady=5, padx=20, fill="x")
        self.log_box.configure(state="disabled")

    def log(self, mensaje):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"> {mensaje}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def seleccionar_imagen(self):
        ruta = filedialog.askopenfilename(filetypes=[("Imagenes", "*.png *.jpg")])
        if ruta:
            self.ruta_imagen_titulo = ruta
            self.lbl_ruta_img.configure(text=f"OK: {os.path.basename(ruta)}", text_color="green")

    def iniciar_proceso(self):
        threading.Thread(target=self.proceso_backend).start()

    def proceso_backend(self):
        try:
            titulo = self.entry_titulo.get().strip()
            historia = self.txt_historia.get("1.0", "end").strip()
            if not titulo or len(historia) < 5:
                self.log("[ERROR] Falta titulo o historia.")
                return

            mapa_voces = {
                "Mexicano - Jorge (Narrador Clasico)": "es-MX-JorgeNeural",
                "Argentino - Tomas (Joven)": "es-AR-TomasNeural",
                "Espanol - Alvaro (Documental)": "es-ES-AlvaroNeural",
                "USA Latino - Alonso (Neutro)": "es-US-AlonsoNeural"
            }
            voz_code = mapa_voces.get(self.combo_voz.get(), "es-MX-JorgeNeural")
            
            self.log("------------------------------------------------")
            self.log("Analizando longitud de historia...")
            
            if not os.path.exists("output"): os.makedirs("output")
            if not os.path.exists("assets/backgrounds"): os.makedirs("assets/backgrounds")

            # LLAMADA A LOGIC
            logic.procesar_historia_en_serie(
                historia, 
                titulo, 
                voz_code, 
                "assets/backgrounds", 
                self.ruta_imagen_titulo
            )
            
            self.log(f"PROCESO TERMINADO! Revisa output.")
            self.log("------------------------------------------------")
            self.ruta_imagen_titulo = None
            self.lbl_ruta_img.configure(text="Ninguna", text_color="gray")

        except Exception as e:
            self.log(f"[ERROR CRITICO] {str(e)}")
            print(f"Error detallado: {e}")

if __name__ == "__main__":
    app = RedditBotApp()
    app.mainloop()
