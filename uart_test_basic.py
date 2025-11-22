#!/usr/bin/env python3
"""
Prueba con DRIVER UART - Mensajes SP:20,SM:21,Sm:19
"""

import os
import time

def test_with_driver():
    print("🚀 PRUEBA CON DRIVER UART")
    print("=" * 40)
    print("Enviando: SP:20, SM:21, Sm:19")
    
    try:
        # Abrir el dispositivo de tu driver
        fd = os.open("/dev/rpi_uart", os.O_RDWR)
        print("✅ Driver UART abierto: /dev/rpi_uart")
        
        # Mensajes a enviar
        mensajes = ["SP:20", "SM:21", "Sm:19"]
        
        for i, msg in enumerate(mensajes, 1):
            print(f"\n--- Mensaje {i}/3 ---")
            print(f"📤 Enviando al driver: '{msg}'")
            
            # Enviar a través del driver
            bytes_escritos = os.write(fd, msg.encode())
            print(f"✅ Driver aceptó {bytes_escritos} bytes")
            
            # El driver debería enviar esto al UART físico
            # Y el Pico debería recibirlo
            
            # Intentar recibir (aunque el Pico no responda)
            print("📥 Intentando recibir del driver...")
            time.sleep(1)  # Dar tiempo
            
            try:
                # Leer con timeout
                data = os.read(fd, 1024)
                if data:
                    print(f"💬 Driver devolvió: {data.decode()}")
                else:
                    print("📭 Driver no tiene datos")
            except BlockingIOError:
                print("📭 No hay datos disponibles del driver")
            
            time.sleep(1)
        
        os.close(fd)
        print("\n✅ Prueba con driver completada")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Verificar que el driver existe
    if not os.path.exists("/dev/rpi_uart"):
        print("❌ Driver no encontrado. Ejecuta:")
        print("   sudo insmod uart_hardware.ko")
        exit(1)
    
    test_with_driver()
    
    print("\n" + "=" * 40)
    print("🎯 VERIFICACIÓN:")
    print("1. Revisa los logs del driver: sudo dmesg | grep RPI_UART")
    print("2. Confirma que el Pico recibe los mensajes")
    print("3. El driver debería mostrar los datos enviados/recibidos")