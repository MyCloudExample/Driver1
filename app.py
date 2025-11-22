from flask import Flask, render_template, redirect, url_for, Response, request, jsonify
from datetime import datetime
import os
import logging
import time
import select

app = Flask(__name__)

# Variables globales
target = 5
minimo = 4
maximo = 6

# Archivos de logs y estado
ruta_historial = "comandos_logs.csv"
ruta_estado = "current_state.csv"
ruta_conexiones = "flask_connections.log"
ruta_modulo = "/dev/rpi_uart"

# === CONFIGURAR LOGGING DE FLASK ===
logging.basicConfig(
    filename=ruta_conexiones,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger()

# Variable global para conexión driver
driver_fd = None

# === INICIALIZAR COMUNICACIÓN CON DRIVER ===
def inicializar_driver():
    global driver_fd
    try:
        driver_fd = os.open(ruta_modulo, os.O_RDWR)
        log.info("✅ Conectado al driver UART personalizado")
        return True
    except Exception as e:
        log.error(f"❌ Error conectando al driver: {str(e)}")
        driver_fd = None
        return False

# === VERIFICAR CONEXIÓN DRIVER ===
def verificar_conexion_driver():
    """Verificar que la conexión con el driver esté activa"""
    global driver_fd
    if driver_fd is None:
        return inicializar_driver()
    return True

# === ENVIAR POR DRIVER ===
def enviar_driver(comando):
    global driver_fd
    
    if not verificar_conexion_driver():
        return False
    
    try:
        comando_formateado = comando + '\n'
        bytes_escritos = os.write(driver_fd, comando_formateado.encode())
        log.info(f"📤 Driver enviado: {comando} ({bytes_escritos} bytes)")
        return True
    except Exception as e:
        log.error(f"❌ Error enviando por driver: {str(e)}")
        driver_fd = None
        return False

# === LEER RESPUESTA DEL DRIVER ===
def leer_respuesta_driver():
    global driver_fd
    try:
        # Intentar leer si hay datos disponibles
        time.sleep(0.1)  # Pequeña pausa para que lleguen datos
        if select.select([driver_fd], [], [], 0.1)[0]:
            respuesta = os.read(driver_fd, 1024).decode().strip()
            if respuesta:
                log.info(f"📥 Driver responde: {respuesta}")
                return respuesta
    except Exception as e:
        log.warning(f"⚠️ Error leyendo respuesta driver: {e}")
    return None

# === ENVIAR COMANDO SEGURO CON REINTENTOS ===
def enviar_comando_seguro(comando, max_reintentos=3):
    """Enviar comando con reintentos en caso de fallo"""
    for intento in range(max_reintentos):
        if enviar_driver(comando):
            return True
        else:
            log.warning(f"🔄 Reintentando envío driver ({intento + 1}/{max_reintentos})")
            time.sleep(0.5)
    
    log.error(f"❌ Fallo en envío driver después de {max_reintentos} intentos")
    return False

# Crear encabezado de CSV si no existe
if not os.path.exists(ruta_historial):
    with open(ruta_historial, "w") as f:
        f.write("timestamp,set_target,set_minimo,set_maximo\n")

# Intentar inicializar driver al inicio
inicializar_driver()

@app.route('/')
def index():
    log.info("Acceso a la página principal")
    return render_template('index.html', target=target, minimo=minimo, maximo=maximo)

# === TARGET ===
@app.route('/target/incrementar', methods=['POST'])
def target_inc():
    global target, minimo, maximo
    if target < 28:
        target += 1
        if minimo >= target:
            minimo = max(5, target - 1)
        if maximo <= target:
            maximo = min(33, target + 1)
    log.info(f"Incrementar TARGET → {target}")
    return redirect(url_for('index'))

@app.route('/target/decrementar', methods=['POST'])
def target_dec():
    global target, minimo, maximo
    if target > 5:
        target -= 1
        if minimo >= target:
            minimo = max(5, target - 1)
        if maximo <= target:
            maximo = min(33, target + 1)
    log.info(f"Decrementar TARGET → {target}")
    return redirect(url_for('index'))

# === MÍNIMO ===
@app.route('/minimo/incrementar', methods=['POST'])
def minimo_inc():
    global minimo, target
    if minimo < target - 1:
        minimo += 1
    log.info(f"Incrementar MINIMO → {minimo}")
    return redirect(url_for('index'))

@app.route('/minimo/decrementar', methods=['POST'])
def minimo_dec():
    global minimo
    if minimo > 5:
        minimo -= 1
    log.info(f"Decrementar MINIMO → {minimo}")
    return redirect(url_for('index'))

# === MÁXIMO ===
@app.route('/maximo/incrementar', methods=['POST'])
def maximo_inc():
    global maximo
    if maximo < 33:
        maximo += 1
    log.info(f"Incrementar MAXIMO → {maximo}")
    return redirect(url_for('index'))

@app.route('/maximo/decrementar', methods=['POST'])
def maximo_dec():
    global maximo, target
    if maximo > target + 1:
        maximo -= 1
    log.info(f"Decrementar MAXIMO → {maximo}")
    return redirect(url_for('index'))

# === EJECUTAR ===
@app.route('/ejecutar', methods=['POST'])
def ejecutar():
    global target, minimo, maximo
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Guardar en logs
    with open(ruta_historial, "a") as f:
        f.write(f"{timestamp},set target {target},set minimo {minimo},set maximo {maximo}\n")

    # Guardar estado actual
    with open(ruta_estado, "w") as f:
        f.write(f"set target {target}, set minimo {minimo}, set maximo {maximo}")

    # ENVÍO MEJORADO CON REINTENTOS
    comando = f"SP:{target},SM:{maximo},Sm:{minimo}"
    if enviar_comando_seguro(comando):
        log.info(f"✅ Comando enviado correctamente: {comando}")
        
        # Intentar leer respuesta del Pico
        time.sleep(0.2)  # Dar tiempo para respuesta
        respuesta = leer_respuesta_driver()
        if respuesta:
            log.info(f"✅ Pico confirmó: {respuesta}")
    else:
        log.error(f"❌ No se pudo enviar comando por driver: {comando}")

    log.info(f"EJECUTAR → target={target}, minimo={minimo}, maximo={maximo}")
    return redirect(url_for('index'))

# === COMANDO PERSONALIZADO ===
@app.route('/comando_personalizado', methods=['POST'])
def comando_personalizado():
    """Endpoint para enviar comandos personalizados como en el script Python"""
    comando = request.form.get('comando', '').strip()
    if comando:
        if enviar_comando_seguro(comando):
            log.info(f"✅ Comando personalizado enviado: {comando}")
            
            # Leer respuesta si existe
            time.sleep(0.2)
            respuesta = leer_respuesta_driver()
            
            return jsonify({
                "status": "success", 
                "message": f"Comando '{comando}' enviado",
                "respuesta": respuesta
            })
        else:
            return jsonify({"status": "error", "message": "Error al enviar comando"})
    return jsonify({"status": "error", "message": "Comando vacío"})

# === VER LOGS ===
@app.route('/logs')
def ver_logs():
    try:
        with open(ruta_historial, "r") as f:
            contenido = f.read()
        return Response(contenido, mimetype='text/plain')
    except Exception as e:
        return f"Error leyendo logs: {e}"

# === VER CONEXIONES ===
@app.route('/conexiones')
def ver_conexiones():
    try:
        with open(ruta_conexiones, "r") as f:
            contenido = f.read()
        return Response(contenido, mimetype='text/plain')
    except Exception as e:
        return f"Error leyendo conexiones: {e}"

# === ESTADO DEL SISTEMA ===
@app.route('/estado_sistema')
def estado_sistema():
    """Endpoint para verificar el estado del sistema"""
    estado_driver = "Conectado" if driver_fd is not None else "Desconectado"
    
    info_sistema = {
        "driver_estado": estado_driver,
        "puerto": ruta_modulo,
        "target_actual": target,
        "minimo_actual": minimo,
        "maximo_actual": maximo
    }
    
    return jsonify(info_sistema)

# === CERRAR DRIVER AL SALIR ===
import atexit

@atexit.register
def cerrar_driver():
    global driver_fd
    if driver_fd is not None:
        os.close(driver_fd)
        log.info("🔌 Conexión driver cerrada correctamente")

if __name__ == '__main__':
    log.info("🚀 Servidor Flask iniciado con soporte para driver personalizado")
    app.run(host='0.0.0.0', port=5002, debug=True)