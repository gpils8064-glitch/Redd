import edge_tts
import asyncio
import random
import os
import PIL.Image
import whisper
import sys
import platform 
# --- PARCHE COMPATIBILIDAD ---
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
# -----------------------------

from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, TextClip
from moviepy.config import change_settings

# ==============================================================================
# ⚠️ TU RUTA DE IMAGEMAGICK
# ==============================================================================

if platform.system() == "Windows":
    RUTA_IMAGEMAGICK = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
    if os.path.exists(RUTA_IMAGEMAGICK):
        change_settings({"IMAGEMAGICK_BINARY": RUTA_IMAGEMAGICK})
else:
    pass
    
def dividir_texto_inteligente(texto, max_palabras=600):
    palabras = texto.split()
    partes = []
    bloque_actual = []
    for palabra in palabras:
        bloque_actual.append(palabra)
        if len(bloque_actual) >= max_palabras and palabra[-1] in ['.', '!', '?', '"']:
            partes.append(" ".join(bloque_actual))
            bloque_actual = []
    if bloque_actual:
        partes.append(" ".join(bloque_actual))
    return partes

async def generar_audio_async(texto, voz, archivo_salida):
    print(f"   [TTS] Generando audio acelerado...")
    comunicate = edge_tts.Communicate(texto, voz, rate="+15%")
    await comunicate.save(archivo_salida)

def generar_audio(texto, voz, archivo_salida):
    asyncio.run(generar_audio_async(texto, voz, archivo_salida))

# --- GENERADOR DE SUBTÍTULOS (ESTILO IMPACT + DOBLE CAPA) ---
def generar_clips_subtitulos(audio_path):
    print("   [IA] 🧠 Analizando audio (Modelo Small - Español)...")
    
    try:
        model = whisper.load_model("small")
        result = model.transcribe(audio_path, word_timestamps=True, language="es")
    except Exception as e:
        print(f"❌ Error en Whisper: {e}")
        return []
    
    subs_clips = []
    todas_las_palabras = []

    for segment in result['segments']:
        for word_info in segment['words']:
            todas_las_palabras.append(word_info)

    # --- CONFIGURACIÓN ESTILO IMPACT ---
    PALABRAS_POR_GRUPO = 3
    FONT_SIZE = 90 
    FONT_TYPE = 'Impact' 
    GROSOR_BORDE = 8 

    for i in range(0, len(todas_las_palabras), PALABRAS_POR_GRUPO):
        grupo = todas_las_palabras[i:i+PALABRAS_POR_GRUPO]
        if not grupo: continue

        text = " ".join([w['word'] for w in grupo]).strip()
        
        start_time = grupo[0]['start']
        end_time = grupo[-1]['end']

        # 1. CAPA TRASERA (Borde Negro)
        clip_borde = (TextClip(text, 
                             fontsize=FONT_SIZE, 
                             color='black', 
                             font=FONT_TYPE,
                             stroke_color='black', 
                             stroke_width=GROSOR_BORDE, 
                             method='caption', size=(1000, None))
                    .set_position(('center', 1250))
                    .set_start(start_time)
                    .set_end(end_time))

        # 2. CAPA DELANTERA (Relleno Blanco)
        clip_relleno = (TextClip(text, 
                             fontsize=FONT_SIZE, 
                             color='white', 
                             font=FONT_TYPE,
                             stroke_width=0, 
                             method='caption', size=(1000, None))
                    .set_position(('center', 1250))
                    .set_start(start_time)
                    .set_end(end_time))

        subs_clips.append(clip_borde)
        subs_clips.append(clip_relleno)
        
    print(f"   [IA] ✅ Generados {int(len(subs_clips)/2)} subtítulos.")
    return subs_clips

# --- RENDERIZADOR ---
def renderizar_clip(audio_path, background_folder, output_path, image_path=None):
    voz_clip = AudioFileClip(audio_path)
    duracion_necesaria = voz_clip.duration + 0.5
    
    videos = [f for f in os.listdir(background_folder) if f.endswith(".mp4")]
    if not videos: raise Exception("Carpeta backgrounds vacía")
    
    bg_name = random.choice(videos)
    ruta_fondo = os.path.join(background_folder, bg_name)
    fondo_original = VideoFileClip(ruta_fondo)
    
    if fondo_original.duration > duracion_necesaria:
        max_start = fondo_original.duration - duracion_necesaria
        random_start = random.uniform(0, max_start)
        print(f"   [Video] 🎲 Fondo random desde: {int(random_start // 60)}m {int(random_start % 60)}s")
        bg = fondo_original.subclip(random_start, random_start + duracion_necesaria)
    else:
        bg = fondo_original.loop(duration=duracion_necesaria)
    
    bg = bg.resize(height=1920)
    bg = bg.crop(width=1080, height=1920, x_center=bg.w/2, y_center=bg.h/2)
    
    # Subtítulos
    clips_subtitulos = generar_clips_subtitulos(audio_path)

    capas = [bg] + clips_subtitulos
    
    if image_path and os.path.exists(image_path):
        print(f"   [Overlay] Añadiendo imagen de portada...")
        try:
            img = ImageClip(image_path)
            if img.w > 900: img = img.resize(width=900)
            img = img.set_duration(4).set_start(0).set_position("center")
            capas.append(img) 
        except Exception as e:
            print(f"   [Error Overlay] {e}")

    visual_final = CompositeVideoClip(capas, size=(1080,1920)).set_duration(duracion_necesaria)
    final = visual_final.set_audio(voz_clip)
    
    final.write_videofile(output_path, fps=30, codec="libx264", audio_codec="aac", ffmpeg_params=['-pix_fmt', 'yuv420p'], threads=4)
    
    voz_clip.close()
    fondo_original.close()
    bg.close()
    final.close()

# --- FUNCIÓN MAESTRA (MEJORADA PARA NOMBRES) ---
def procesar_historia_en_serie(historia_completa, nombre_entrada, voz_code, bg_folder, img_path=None):
    # 1. TÍTULO HABLADO (Para el TTS): Quitamos guiones y dejamos espacios
    # "Tu_Padre_Falso" -> "Tu Padre Falso"
    titulo_hablado = nombre_entrada.replace("_", " ").replace("-", " ")
    
    # 2. NOMBRE DE ARCHIVO (Para guardar): Quitamos espacios y ponemos guiones
    # "Tu Padre Falso" -> "Tu_Padre_Falso"
    nombre_archivo_base = titulo_hablado.replace(" ", "_")

    palabras_total = len(historia_completa.split())
    LIMITE = 600 
    
    if palabras_total <= LIMITE:
        print(f"--- MODO VIDEO ÚNICO ---")
        texto_final = f"{titulo_hablado}. ... {historia_completa}"
        audio_temp = "temp_audio_single.mp3"
        generar_audio(texto_final, voz_code, audio_temp)
        
        # Usamos el nombre limpio con guiones para el archivo
        renderizar_clip(audio_temp, bg_folder, f"output/{nombre_archivo_base}.mp4", img_path)
        
        if os.path.exists(audio_temp): os.remove(audio_temp)
    else:
        print(f"--- MODO SERIE ({palabras_total} palabras) ---")
        partes = dividir_texto_inteligente(historia_completa, LIMITE)
        for i, texto_parte in enumerate(partes):
            numero_parte = i + 1
            es_ultimo = (numero_parte == len(partes))
            texto_final = texto_parte
            if numero_parte == 1:
                intro = f"{titulo_hablado}. ... "
                texto_final = intro + texto_final
                if not es_ultimo: texto_final += " ... ... Dale like para parte 2."
            else:
                intro = f"{titulo_hablado}. Parte {numero_parte}. ... "
                texto_final = intro + texto_final
                if not es_ultimo: texto_final += f" ... ... Busca la parte {numero_parte + 1}."

            print(f"\n🎬 Parte {numero_parte}...")
            # Usamos el nombre limpio con guiones para el archivo
            nombre_archivo = f"output/{nombre_archivo_base}_parte{numero_parte}.mp4"
            audio_temp = f"temp_part_{numero_parte}.mp3"
            
            generar_audio(texto_final, voz_code, audio_temp)
            renderizar_clip(audio_temp, bg_folder, nombre_archivo, img_path)
            if os.path.exists(audio_temp): os.remove(audio_temp)
            print(f"✅ Parte {numero_parte} lista.")
