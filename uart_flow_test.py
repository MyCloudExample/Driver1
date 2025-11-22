#!/usr/bin/env python3
"""
Aplicación para enviar comandos a Raspberry Pi Pico
"""

import os
import time
import threading

class PicoUARTApplication:
    def __init__(self):
        self.fd = None
        
    def open_driver(self):
        """Abrir conexión con el driver"""
        try:
            self.fd = os.open("/dev/rpi_uart", os.O_RDWR)
            print("✅ Conectado al driver UART hardware")
            return True
        except Exception as e:
            print(f"❌ Error conectando al driver: {e}")
            return False
            
    def close_driver(self):
        """Cerrar conexión"""
        if self.fd:
            os.close(self.fd)
            print("✅ Desconectado del driver")
            
    def send_pico_command(self, command):
        """Enviar comando a la Pico con formato correcto"""
        if not self.fd:
            return False
            
        try:
            # AGREGAR CARACTER DE FIN DE LÍNEA - LA PICO LO NECESITA
            full_command = command + "\n"  # También puedes usar "\r" o "\r\n"
            print(f"📤 Enviando a Pico: {command}")
            written = os.write(self.fd, full_command.encode())
            print(f"✅ Driver aceptó {written} bytes")
            return True
        except Exception as e:
            print(f"❌ Error enviando: {e}")
            return False
            
    def receive_from_pico(self, timeout=2.0):
        """Recibir mensaje de la Pico"""
        if not self.fd:
            return None
            
        try:
            print("📥 Esperando respuesta de la Pico...")
            data = os.read(self.fd, 1024)
            if data:
                message = data.decode('utf-8', errors='ignore')
                print(f"💬 Pico respondió: {message.strip()}")
                return message
            else:
                print("⏳ No hay datos de la Pico")
                return None
        except Exception as e:
            print(f"❌ Error recibiendo: {e}")
            return None
            
    def test_pico_commands(self):
        """Probar comandos específicos para la Pico"""
        pico_commands = [
            "SP:20,SM:21,Sm:19",
            "SP:15,SM:18,Sm:12", 
            "SP:25,SM:28,Sm:22"
        ]
        
        for cmd in pico_commands:
            print(f"\n--- Enviando comando: '{cmd}' ---")
            
            # Enviar comando a la Pico
            if not self.send_pico_command(cmd):
                continue
                
            # Esperar respuesta
            time.sleep(1.0)
            self.receive_from_pico()

def main():
    print("🚀 COMUNICACIÓN CON RASPBERRY PICO")
    print("=" * 50)
    print("Enviando comandos de setpoint a la Pico")
    print("Formato: SP:valor,SM:valor,Sm:valor")
    print("")
    
    app = PicoUARTApplication()
    
    if not app.open_driver():
        return
        
    try:
        # Probar comandos de prueba
        app.test_pico_commands()
        
        # Modo interactivo
        print("\n" + "=" * 50)
        print("MODO INTERACTIVO - Envia comandos a la Pico:")
        print("Ejemplo: SP:20,SM:21,Sm:19")
        
        while True:
            command = input("\n📝 Comando (o 'quit' para salir): ").strip()
            if command.lower() == 'quit':
                break
                
            # Validar formato básico
            if "SP:" in command and "SM:" in command and "Sm:" in command:
                app.send_pico_command(command)
                time.sleep(1.0)
                app.receive_from_pico()
            else:
                print("❌ Formato incorrecto. Usa: SP:valor,SM:valor,Sm:valor")
                
    except KeyboardInterrupt:
        print("\n🛑 Aplicación interrumpida")
    finally:
        app.close_driver()

if __name__ == "__main__":
    main()