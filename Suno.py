import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import pyttsx3
import easyocr
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image, ImageTk
import cv2
import webbrowser
from translate import Translator
import threading

try:
    from pyzbar.pyzbar import decode
except ImportError:
    decode = None

PRIMARY_COLOR = "#7E57C2"
SECONDARY_COLOR = "#FFFFFF"
ACCENT_COLOR = "#B39DDB"
TEXT_COLOR = "#333333"
FONT_STYLE = ("Arial", 12)

class SunoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Suno 1.0")
        self.root.geometry("1000x700")
        self.root.configure(bg=SECONDARY_COLOR)
        
        self.reader = easyocr.Reader(['pt'])
        self.processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        self.model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        self.translator = Translator(to_lang="pt")

        self.qr_dict = {
            "leite": "Este alimento contém lactose. Cuidado para quem tem intolerância.",
            "amendoim": "Atenção: contém amendoim. Pode causar reações alérgicas.",
            "gluten": "Contém glúten. Não é adequado para pessoas com doença celíaca.",
            "suco": "Este é um suco natural. Sem adição de açúcar.",
        }
        self.main_container = tk.Frame(self.root, bg=SECONDARY_COLOR)
        self.main_container.pack(fill="both", expand=True)

        self.pages = {}
        
        self.create_home_page()
        self.create_text_reader_page()
        self.create_image_reader_page()
        self.create_image_interpreter_page()
        self.create_food_reader_page()
        
        self.show_page("home")
        
        self.camera_active = False
        self.cap = None
        self.current_image = None

        self.root.after(500, self.welcome_message)

    def welcome_message(self):
        msg = "Bem vindo ao Suno, um app de ajuda para pessoas com dificuldade em Leitura."
        self.read_text(msg, warn=False)

    def create_home_page(self):
     """Cria a página inicial com os 4 botões principais"""
     page = tk.Frame(self.main_container, bg="#EDE7F6")
     self.pages["home"] = page

     header_frame = tk.Frame(page, bg=PRIMARY_COLOR)
     header_frame.pack(fill="x", pady=(0, 30))

     title_label = tk.Label(
        header_frame,
        text="SUNO",
        font=("Arial", 28, "bold"),
        bg=PRIMARY_COLOR,
        fg=SECONDARY_COLOR,
        pady=20
     )
     title_label.pack()

     # Carregar ícones e aumentar tamanho
     def load_icon(path, size=(64, 64)):
        img = Image.open(path)
        img = img.resize(size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)

     self.icons = {
        "text": load_icon("assets/App/L_Textos.png"),
        "image": load_icon("assets/App/L_T_Imagens.png"),
        "interpret": load_icon("assets/App/I_Imagens.png"),
        "food": load_icon("assets/App/L_I_Alimentares.png")
     }

     # Botões principais
     buttons_frame = tk.Frame(page, bg="#EDE7F6")
     buttons_frame.pack(expand=True)

     options = [
        ("Leitor de Textos", self.show_text_reader, self.icons["text"]),
        ("Leitor de Textos em Imagens", self.show_image_reader, self.icons["image"]),
        ("Interpretador de Imagens", self.show_image_interpreter, self.icons["interpret"]),
        ("Leitor de Informações Alimentares", self.show_food_reader, self.icons["food"])
     ]

     for i, (text, command, icon) in enumerate(options):
        row, col = divmod(i, 2)
        btn = tk.Button(
            buttons_frame,
            text=text,
            image=icon,
            compound="left",
            command=command,
            bg=ACCENT_COLOR,
            fg=TEXT_COLOR,
            font=("Arial", 14, "bold"),
            relief="flat",
            padx=20,
            pady=20,
            width=280,
            anchor="w",
            borderwidth=0,           # Remove borda
            highlightthickness=0     # Remove destaque da borda
        )
        btn.grid(row=row, column=col, padx=30, pady=30, sticky="nsew")

     for i in range(2):
        buttons_frame.grid_columnconfigure(i, weight=1)
        buttons_frame.grid_rowconfigure(i, weight=1)

     # Footer
     footer_frame = tk.Frame(page, bg=PRIMARY_COLOR)
     footer_frame.pack(side="bottom", fill="x", pady=(30, 0))

     version_label = tk.Label(
        footer_frame,
        text="Versão 1.0",
        font=("Arial", 10),
        bg=PRIMARY_COLOR,
        fg=SECONDARY_COLOR
     )
     version_label.pack(pady=10)

   
    def create_text_reader_page(self):
        """Cria a página do leitor de textos"""
        page = tk.Frame(self.main_container, bg=SECONDARY_COLOR)
        self.pages["text_reader"] = page
        
        # Header
        header_frame = tk.Frame(page, bg=PRIMARY_COLOR)
        header_frame.pack(fill="x", pady=(0, 15))
        
        title_frame = tk.Frame(header_frame, bg=PRIMARY_COLOR)
        title_frame.pack()
        
        back_btn = tk.Button(title_frame,
                           text="←",
                           command=self.show_home,
                           bg=PRIMARY_COLOR,
                           fg=SECONDARY_COLOR,
                           font=("Arial", 14, "bold"),
                           relief=tk.FLAT)
        back_btn.pack(side="left", padx=10)
        
        title_label = tk.Label(title_frame,
                             text="Leitor de Textos",
                             font=("Arial", 20, "bold"),
                             bg=PRIMARY_COLOR,
                             fg=SECONDARY_COLOR)
        title_label.pack(side="left", padx=5)
        
        # Conteúdo
        content_frame = tk.Frame(page, bg=SECONDARY_COLOR, padx=20, pady=20)
        content_frame.pack(fill="both", expand=True)
        
        instruction_label = tk.Label(content_frame,
                                   text="Digite o texto que deseja ouvir:",
                                   font=("Arial", 12),
                                   bg=SECONDARY_COLOR,
                                   fg=TEXT_COLOR)
        instruction_label.pack(anchor="w", pady=(0, 10))
        
        self.text_entry = scrolledtext.ScrolledText(content_frame,
                                                  height=15,
                                                  width=80,
                                                  wrap=tk.WORD,
                                                  font=FONT_STYLE,
                                                  bg=SECONDARY_COLOR,
                                                  fg=TEXT_COLOR)
        self.text_entry.pack(fill="both", expand=True)
        
        # Botões
        buttons_frame = tk.Frame(content_frame, bg=SECONDARY_COLOR)
        buttons_frame.pack(pady=15)
        
        read_btn = tk.Button(buttons_frame,
                           text="Ouvir Texto",
                           command=lambda: self.read_text(self.text_entry.get("1.0", tk.END)),
                           bg=ACCENT_COLOR,
                           fg=TEXT_COLOR,
                           font=FONT_STYLE,
                           padx=20,
                           pady=5)
        read_btn.pack(side="left", padx=10)
        
    def create_image_reader_page(self):
        """Cria a página do leitor de textos em imagens"""
        page = tk.Frame(self.main_container, bg=SECONDARY_COLOR)
        self.pages["image_reader"] = page
        
        # Header
        header_frame = tk.Frame(page, bg=PRIMARY_COLOR)
        header_frame.pack(fill="x", pady=(0, 15))
        
        title_frame = tk.Frame(header_frame, bg=PRIMARY_COLOR)
        title_frame.pack()
        
        back_btn = tk.Button(title_frame,
                           text="←",
                           command=self.show_home,
                           bg=PRIMARY_COLOR,
                           fg=SECONDARY_COLOR,
                           font=("Arial", 14, "bold"),
                           relief=tk.FLAT)
        back_btn.pack(side="left", padx=10)
        
        title_label = tk.Label(title_frame,
                             text="Leitor de Textos em Imagens",
                             font=("Arial", 20, "bold"),
                             bg=PRIMARY_COLOR,
                             fg=SECONDARY_COLOR)
        title_label.pack(side="left", padx=5)
        
        # Conteúdo
        content_frame = tk.Frame(page, bg=SECONDARY_COLOR, padx=20, pady=10)
        content_frame.pack(fill="both", expand=True)
        
        # Frame para imagem e resultados
        display_frame = tk.Frame(content_frame, bg=SECONDARY_COLOR)
        display_frame.pack(fill="both", expand=True)
        
        # Canvas para imagem
        self.image_canvas = tk.Canvas(display_frame, bg="lightgray", height=300)
        self.image_canvas.pack(fill="x", pady=(0, 15))
        
        # Área de texto com scroll
        self.result_text = scrolledtext.ScrolledText(display_frame,
                                                   height=10,
                                                   width=80,
                                                   wrap=tk.WORD,
                                                   font=FONT_STYLE,
                                                   bg=SECONDARY_COLOR,
                                                   fg=TEXT_COLOR)
        self.result_text.pack(fill="both", expand=True)
        
        # Botõest55tytt44
        buttons_frame = tk.Frame(content_frame, bg=SECONDARY_COLOR)
        buttons_frame.pack(pady=10)
        
        select_btn = tk.Button(buttons_frame,
                             text="Selecionar Imagem",
                             command=self.select_image_for_reading,
                             bg=ACCENT_COLOR,
                             fg=TEXT_COLOR,
                             font=FONT_STYLE,
                             padx=20,
                             pady=5)
        select_btn.pack(side="left", padx=10)
        
        read_btn = tk.Button(buttons_frame,
                           text="Ouvir Texto",
                           command=lambda: self.read_text(self.result_text.get("1.0", tk.END)),
                           bg=ACCENT_COLOR,
                           fg=TEXT_COLOR,
                           font=FONT_STYLE,
                           padx=20,
                           pady=5)
        read_btn.pack(side="left", padx=10)
        
    def create_image_interpreter_page(self):
        """Cria a página do interpretador de imagens"""
        page = tk.Frame(self.main_container, bg=SECONDARY_COLOR)
        self.pages["image_interpreter"] = page
        
        # Header
        header_frame = tk.Frame(page, bg=PRIMARY_COLOR)
        header_frame.pack(fill="x", pady=(0, 15))
        
        title_frame = tk.Frame(header_frame, bg=PRIMARY_COLOR)
        title_frame.pack()
        
        back_btn = tk.Button(title_frame,
                           text="←",
                           command=self.show_home,
                           bg=PRIMARY_COLOR,
                           fg=SECONDARY_COLOR,
                           font=("Arial", 14, "bold"),
                           relief=tk.FLAT)
        back_btn.pack(side="left", padx=10)
        
        title_label = tk.Label(title_frame,
                             text="Interpretador de Imagens",
                             font=("Arial", 20, "bold"),
                             bg=PRIMARY_COLOR,
                             fg=SECONDARY_COLOR)
        title_label.pack(side="left", padx=5)
        
        # Conteúdo
        content_frame = tk.Frame(page, bg=SECONDARY_COLOR, padx=20, pady=10)
        content_frame.pack(fill="both", expand=True)
        
        # Frame para imagem e resultados
        display_frame = tk.Frame(content_frame, bg=SECONDARY_COLOR)
        display_frame.pack(fill="both", expand=True)
        
        # Canvas para imagem
        self.interpreter_canvas = tk.Canvas(display_frame, bg="lightgray", height=300)
        self.interpreter_canvas.pack(fill="x", pady=(0, 15))
        
        # Área de texto com scroll
        self.interpreter_text = scrolledtext.ScrolledText(display_frame,
                                                        height=10,
                                                        width=80,
                                                        wrap=tk.WORD,
                                                        font=FONT_STYLE,
                                                        bg=SECONDARY_COLOR,
                                                        fg=TEXT_COLOR)
        self.interpreter_text.pack(fill="both", expand=True)
        
        # Botões
        buttons_frame = tk.Frame(content_frame, bg=SECONDARY_COLOR)
        buttons_frame.pack(pady=10)
        
        select_btn = tk.Button(buttons_frame,
                             text="Selecionar Imagem",
                             command=self.select_image_for_interpretation,
                             bg=ACCENT_COLOR,
                             fg=TEXT_COLOR,
                             font=FONT_STYLE,
                             padx=20,
                             pady=5)
        select_btn.pack(side="left", padx=10)
        
        read_btn = tk.Button(buttons_frame,
                           text="Ouvir Descrição",
                           command=lambda: self.read_text(self.interpreter_text.get("1.0", tk.END)),
                           bg=ACCENT_COLOR,
                           fg=TEXT_COLOR,
                           font=FONT_STYLE,
                           padx=20,
                           pady=5)
        read_btn.pack(side="left", padx=10)
        
    def create_food_reader_page(self):
        """Cria a página do leitor de informações alimentares"""
        page = tk.Frame(self.main_container, bg=SECONDARY_COLOR)
        self.pages["food_reader"] = page
        
        # Header
        header_frame = tk.Frame(page, bg=PRIMARY_COLOR)
        header_frame.pack(fill="x", pady=(0, 15))
        
        title_frame = tk.Frame(header_frame, bg=PRIMARY_COLOR)
        title_frame.pack()
        
        back_btn = tk.Button(title_frame,
                           text="←",
                           command=self.show_home,
                           bg=PRIMARY_COLOR,
                           fg=SECONDARY_COLOR,
                           font=("Arial", 14, "bold"),
                           relief=tk.FLAT)
        back_btn.pack(side="left", padx=10)
        
        title_label = tk.Label(title_frame,
                             text="Leitor de Informações Alimentares",
                             font=("Arial", 20, "bold"),
                             bg=PRIMARY_COLOR,
                             fg=SECONDARY_COLOR)
        title_label.pack(side="left", padx=5)
        
        # Conteúdo
        content_frame = tk.Frame(page, bg=SECONDARY_COLOR, padx=20, pady=10)
        content_frame.pack(fill="both", expand=True)
        
        display_frame = tk.Frame(content_frame, bg=SECONDARY_COLOR)
        display_frame.pack(fill="both", expand=True)
        
        # Canvas maior e centralizado
        self.camera_canvas = tk.Canvas(display_frame, bg="lightgray", width=800, height=450)
        self.camera_canvas.pack(pady=(0, 15))

        # Área de texto menor
        self.food_text = scrolledtext.ScrolledText(display_frame,
                                         height=6,   # reduzido
                                         width=80,
                                         wrap=tk.WORD,
                                         font=FONT_STYLE,
                                         bg=SECONDARY_COLOR,
                                         fg=TEXT_COLOR)
        self.food_text.pack(fill="x", expand=False)

        
        buttons_frame = tk.Frame(content_frame, bg=SECONDARY_COLOR)
        buttons_frame.pack(pady=10)
        
        start_btn = tk.Button(buttons_frame,
                            text="Iniciar Câmera",
                            command=self.start_food_camera,
                            bg=ACCENT_COLOR,
                            fg=TEXT_COLOR,
                            font=FONT_STYLE,
                            padx=20,
                            pady=5)
        start_btn.pack(side="left", padx=10)
        
        stop_btn = tk.Button(buttons_frame,
                           text="Parar Câmera",
                           command=self.stop_camera,
                           bg=ACCENT_COLOR,
                           fg=TEXT_COLOR,
                           font=FONT_STYLE,
                           padx=20,
                           pady=5)
        stop_btn.pack(side="left", padx=10)

    # Métodos para navegação entre páginas
    def show_page(self, page_name):
        """Mostra uma página específica e esconde as outras"""
        for page in self.pages.values():
            page.pack_forget()
        self.pages[page_name].pack(fill="both", expand=True)
    
    def show_home(self):
        """Mostra a página inicial e para a câmera se estiver ativa"""
        self.stop_camera()
        self.show_page("home")
    
    def show_text_reader(self):
        """Mostra a página do leitor de textos"""
        self.text_entry.delete("1.0", tk.END)
        self.show_page("text_reader")
    
    def show_image_reader(self):
        """Mostra a página do leitor de textos em imagens"""
        self.image_canvas.delete("all")
        self.result_text.delete("1.0", tk.END)
        self.show_page("image_reader")
    
    def show_image_interpreter(self):
        """Mostra a página do interpretador de imagens"""
        self.interpreter_canvas.delete("all")
        self.interpreter_text.delete("1.0", tk.END)
        self.show_page("image_interpreter")
    
    def show_food_reader(self):
        """Mostra a página do leitor de informações alimentares"""
        self.camera_canvas.delete("all")
        self.food_text.delete("1.0", tk.END)
        self.show_page("food_reader")
    
    # Métodos de funcionalidade
    def read_text(self, text, warn=True):
        """Lê o texto em voz alta de forma thread-safe e reinicializando o engine."""
        def tts_thread():
            if text.strip():
                tts_engine = pyttsx3.init()
                voices = tts_engine.getProperty('voices')
                tts_engine.setProperty('voice', voices[0].id)
                tts_engine.say(text)
                tts_engine.runAndWait()
                tts_engine.stop()
            elif warn:
                messagebox.showwarning("Aviso", "Nenhum texto para ler.")
        threading.Thread(target=tts_thread, daemon=True).start()
    
    def select_image_for_reading(self):
        """Seleciona uma imagem para leitura de texto"""
        file_path = filedialog.askopenfilename(
            title="Selecione uma imagem com texto",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg")]
        )
        
        if file_path:
            self.process_image_for_text(file_path)
    
    def process_image_for_text(self, image_path):
        """Processa a imagem para extrair texto"""
        try:
            # Mostra a imagem no canvas
            img = Image.open(image_path)
            img.thumbnail((700, 300))
            self.current_image = ImageTk.PhotoImage(img)
            self.image_canvas.create_image((700 - img.width)/2, 0, anchor=tk.NW, image=self.current_image)
            
            # Processa o texto em uma thread separada
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert(tk.END, "Processando imagem...\n")
            
            threading.Thread(
                target=self._process_image_text_thread,
                args=(image_path,),
                daemon=True
            ).start()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a imagem: {str(e)}")
    
    def _process_image_text_thread(self, image_path):
        """Thread para processar o texto da imagem"""
        try:
            results = self.reader.readtext(image_path)
            extracted_text = ' '.join([item[1] for item in results])
            
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert(tk.END, extracted_text)
            
            if not extracted_text.strip():
                self.result_text.insert(tk.END, "Nenhum texto foi identificado na imagem.")
            else:
                self.read_text(extracted_text)
        except Exception as e:
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert(tk.END, f"Erro ao processar imagem: {str(e)}")
    
    def select_image_for_interpretation(self):
        """Seleciona uma imagem para interpretação"""
        file_path = filedialog.askopenfilename(
            title="Selecione uma imagem para interpretação",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg")]
        )
        
        if file_path:
            self.process_image_for_interpretation(file_path)
    
    def process_image_for_interpretation(self, image_path):
        """Processa a imagem para interpretação"""
        try:
            # Mostra a imagem no canvas
            img = Image.open(image_path)
            img.thumbnail((700, 300))
            self.current_image = ImageTk.PhotoImage(img)
            self.interpreter_canvas.create_image((700 - img.width)/2, 0, anchor=tk.NW, image=self.current_image)
            
            # Processa a interpretação em uma thread separada
            self.interpreter_text.delete("1.0", tk.END)
            self.interpreter_text.insert(tk.END, "Analisando imagem...\n")
            
            threading.Thread(
                target=self._process_image_interpretation_thread,
                args=(image_path,),
                daemon=True
            ).start()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a imagem: {str(e)}")
    
    def _process_image_interpretation_thread(self, image_path):
        """Thread para interpretar a imagem"""
        try:
            img = Image.open(image_path).convert("RGB")
            inputs = self.processor(img, return_tensors="pt")
            output = self.model.generate(**inputs)
            description_en = self.processor.decode(output[0], skip_special_tokens=True)
            description_pt = self.translator.translate(description_en)
            
            self.interpreter_text.delete("1.0", tk.END)
            self.interpreter_text.insert(tk.END, description_pt)
            self.read_text(description_pt)
        except Exception as e:
            self.interpreter_text.delete("1.0", tk.END)
            self.interpreter_text.insert(tk.END, f"Erro ao interpretar imagem: {str(e)}")
    
    def start_food_camera(self):
        """Inicia a câmera para leitura de informações alimentares"""
        if not self.camera_active:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                messagebox.showerror("Erro", "Não foi possível acessar a câmera.")
                return
            
            self.camera_active = True
            self.update_camera_feed()
    
    def update_camera_feed(self):
     """Atualiza o feed da câmera e verifica QR Codes"""
     if self.camera_active and self.cap.isOpened():
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Mantém proporção da imagem (exemplo: 800x450)
            target_width, target_height = 800, 450
            h, w, _ = frame.shape
            aspect = w / h
            if w > h:
                new_w = target_width
                new_h = int(target_width / aspect)
            else:
                new_h = target_height
                new_w = int(target_height * aspect)
            frame = cv2.resize(frame, (new_w, new_h))

            # Tenta decodificar QR Codes
            if decode:
                qr_codes = decode(frame)
                for qr in qr_codes:
                    self.process_qr_code(qr, frame)

            # Converte para PhotoImage e mostra no canvas centralizado
            img = Image.fromarray(frame)
            self.current_image = ImageTk.PhotoImage(img)
            x_offset = (target_width - new_w) // 2
            y_offset = (target_height - new_h) // 2
            self.camera_canvas.delete("all")
            self.camera_canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=self.current_image)

            # Agenda a próxima atualização
            self.root.after(100, self.update_camera_feed)
    
    def process_qr_code(self, qr, frame):
        """Processa um QR Code detectado"""
        data = qr.data.decode('utf-8').lower()
        
        self.food_text.delete("1.0", tk.END)
        self.food_text.insert(tk.END, f"QR Code detectado:\n{data}\n")

        # Verifica se o QR Code contém palavras-chave do dicionário
        found = False
        for key, message in self.qr_dict.items():
            if key in data:
                self.food_text.insert(tk.END, f"\n{message}")
                self.read_text(message)
                found = True
                break

        if not found:
            # Se não houver correspondência, apenas lê o texto do QR
            self.read_text(f"Informação alimentar: {data}")
        
        # Desenha a borda do QR Code
        pts = [tuple(pt) for pt in qr.polygon]
        for i in range(len(pts)):
            cv2.line(frame, pts[i], pts[(i+1) % len(pts)], (0, 255, 0), thickness=3)

    def stop_camera(self):
        """Para a visualização da câmera"""
        if self.camera_active:
            self.camera_active = False
            if self.cap:
                self.cap.release()
            self.camera_canvas.delete("all")
    
    def on_closing(self):
        """Fecha a aplicação corretamente"""
        self.stop_camera()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = SunoApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
