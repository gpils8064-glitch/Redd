from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import logic
import os
import time

app = Flask(__name__)
CORS(app) # Importante: Permite que Lovable se conecte contigo

@app.route('/render', methods=['POST'])
def render_video():
    try:
        data = request.json
        # Datos que vienen de Lovable
        titulo = data.get('title', 'Video_Reddit')
        historia = data.get('storyContent', '')
        voz = data.get('voice', 'es-MX-JorgeNeural')
        
        if not historia:
            return jsonify({"error": "No enviaste la historia"}), 400

        # Directorios de trabajo
        base_dir = os.getcwd()
        output_folder = os.path.join(base_dir, "output")
        bg_folder = os.path.join(base_dir, "assets", "backgrounds")
        
        # Asegurar que existan las carpetas
        os.makedirs(output_folder, exist_ok=True)
        if not os.path.exists(bg_folder):
            return jsonify({"error": "No se encontraron los backgrounds en el servidor"}), 500

        # Limpiar titulo para nombre de archivo
        safe_title = "".join([c for c in titulo if c.isalnum() or c in (' ','-','_')]).strip().replace(" ", "_")
        output_filename = f"{safe_title}.mp4"
        output_path = os.path.join(output_folder, output_filename)

        print(f"--- Iniciando Render: {titulo} ---")
        
        # LLAMADA A TU LÓGICA (logic.py)
        # Nota: logic.procesar_historia_en_serie guarda el archivo, aquí calculamos dónde quedó
        logic.procesar_historia_en_serie(
            historia, 
            titulo, 
            voz, 
            bg_folder, 
            None # Sin imagen de portada por ahora
        )

        # Buscamos el archivo generado más reciente en la carpeta output
        # (Porque tu logic.py a veces le agrega "_parte1" al nombre)
        files = [os.path.join(output_folder, f) for f in os.listdir(output_folder) if f.endswith('.mp4')]
        if not files:
            return jsonify({"error": "El video no se generó correctamente"}), 500
            
        latest_file = max(files, key=os.path.getctime)
        
        # Enviamos el archivo de vuelta a Lovable para descargarlo
        return send_file(latest_file, as_attachment=True)

    except Exception as e:
        print(f"ERROR: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def health_check():
    return "El Bot de Reddit está VIVO", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)