#!/usr/bin/env python3
"""
Prueba UART directa - Mensajes específicos SP:20,SM:21,Sm:19
Para verificar conexión con Raspberry Pi Pico
Es para verificar que exista conecion entre los pines de Pi y la Pico
"""

import serial
import time
import sys

def test_uart_direct():
    print("🔌 PRUEBA UART DIRECTO - MENSAJES ESPECÍFICOS")
    print("=" * 50)
    
    try:
        # Configurar conexión UART directa
        ser = serial.Serial(
            port='/dev/ttyS0',
            baudrate=115200,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1,
            xonxoff=False,
            rtscts=False
        )
        
        print("✅ UART directo conectado: /dev/ttyS0")
        print(f"📊 Configuración: 115200 bauds, 8N1")
        
        # Dar tiempo para estabilizar
        time.sleep(2)
        
        # Mensajes específicos solicitados
        test_messages = [
            "SP:20",
            "SM:21", 
            "Sm:19"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n--- Prueba {i}/{len(test_messages)} ---")
            print(f"📤 Enviando: '{message}'")
            
            # Enviar mensaje (añadir newline para que Pico lo detecte fácilmente)
            ser.write((message + '\n').encode())
            ser.flush()  # Forzar envío
            
            print("⏳ Esperando respuesta...")
            
            # Esperar y leer respuesta
            start_time = time.time()
            response_received = False
            
            while time.time() - start_time < 3:  # Timeout de 3 segundos
                if ser.in_waiting > 0:
                    response = ser.readline().decode('utf-8', errors='ignore').strip()
                    if response:
                        print(f"📥 Pico respondió: '{response}'")
                        response_received = True
                        break
                time.sleep(0.1)
            
            if not response_received:
                print("❌ Timeout - No hubo respuesta del Pico")
            
            time.sleep(1)  # Pausa entre mensajes
        
        ser.close()
        print("\n✅ Prueba UART directo completada")
        
    except serial.SerialException as e:
        print(f"❌ Error de serial: {e}")
        print("   Verifica:")
        print("   - Permisos: sudo usermod -a -G dialout $USER")
        print("   - UART habilitado en /boot/config.txt")
        print("   - Dispositivo /dev/ttyS0 existe")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

def check_uart_status():
    """Verificar estado del UART"""
    print("\n🔍 DIAGNÓSTICO UART:")
    
    import subprocess
    import os
    
    # Verificar dispositivo
    if os.path.exists('/dev/ttyS0'):
        print("✅ /dev/ttyS0 existe")
        
        # Verificar permisos
        perms = oct(os.stat('/dev/ttyS0').st_mode)[-3:]
        print(f"📝 Permisos: {perms}")
        
        # Verificar configuración
        try:
            result = subprocess.run(['stty', '-F', '/dev/ttyS0', '-a'], 
                                  capture_output=True, text=True)
            if '115200' in result.stdout:
                print("✅ Baudrate: 115200")
            else:
                print("❌ Baudrate no es 115200")
        except:
            print("⚠️ No se pudo verificar configuración")
    else:
        print("❌ /dev/ttyS0 no existe")

if __name__ == "__main__":
    print("🚀 PRUEBA CONEXIÓN RASPBERRY PI 4 → PICO")
    print("📨 Mensajes a enviar: SP:20, SM:21, Sm:19")
    print("💡 Asegúrate de:")
    print("   - RPi4 GPIO14 (Pin 8) → Pico GPIO1 (RX)")
    print("   - RPi4 GPIO15 (Pin 10) ← Pico GPIO0 (TX)")
    print("   - GND conectado")
    print("   - Pico ejecutando código de recepción UART")
    
    check_uart_status()
    
    input("\n🎯 Presiona Enter para iniciar prueba UART directo...")
    
    test_uart_direct()
    
    print("\n" + "=" * 50)
    print("📋 RESULTADO:")
    print("   - Si ves respuestas del Pico: ✅ CONEXIÓN OK")
    print("   - Si no hay respuestas: ❌ REVISAR CABLEADO/CÓDIGO PICO")
    print("   - Mensajes enviados: SP:20, SM:21, Sm:19")