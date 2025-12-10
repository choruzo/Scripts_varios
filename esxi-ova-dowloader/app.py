#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESXi OVA Downloader - Flask Application
Aplicación web para descargar VMs de vCenter como archivos OVA
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import json
import os
import logging
from datetime import datetime
from vmware_service import VMwareService

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Clave secreta para sesiones
CORS(app)

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar configuración
CONFIG_FILE = 'config.json'
config = {}

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
else:
    # Configuración por defecto
    config = {
        'download_directory': './downloads',
        'timeout': 300,
        'verify_ssl': False
    }

# Crear directorio de descargas si no existe
os.makedirs(config['download_directory'], exist_ok=True)

# Estado global de la aplicación
app_state = {
    'vmware_service': None,
    'download_queue': [],
    'current_download': None,
    'download_history': []
}


@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')


@app.route('/api/connect', methods=['POST'])
def connect():
    """
    Conectar a vCenter
    Body: {vcenter_host, username, password}
    """
    try:
        data = request.get_json()
        vcenter_host = data.get('vcenter_host')
        username = data.get('username')
        password = data.get('password')
        
        if not all([vcenter_host, username, password]):
            return jsonify({
                'success': False,
                'error': 'Todos los campos son requeridos'
            }), 400
        
        # Crear servicio de VMware
        vmware_service = VMwareService(
            host=vcenter_host,
            username=username,
            password=password,
            verify_ssl=config.get('verify_ssl', False)
        )
        
        # Intentar conectar
        if vmware_service.connect():
            # Guardar en sesión (solo referencia, no credenciales)
            session['connected'] = True
            session['vcenter_host'] = vcenter_host
            session['username'] = username
            
            # Guardar servicio en estado de la app
            app_state['vmware_service'] = vmware_service
            
            logger.info(f"Conectado exitosamente a vCenter: {vcenter_host}")
            
            return jsonify({
                'success': True,
                'message': f'Conectado exitosamente a {vcenter_host}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No se pudo conectar a vCenter. Verifica las credenciales.'
            }), 401
            
    except Exception as e:
        logger.error(f"Error en conexión: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error de conexión: {str(e)}'
        }), 500


@app.route('/api/disconnect', methods=['POST'])
def disconnect():
    """Desconectar de vCenter"""
    try:
        if app_state['vmware_service']:
            app_state['vmware_service'].disconnect()
            app_state['vmware_service'] = None
        
        session.clear()
        app_state['download_queue'] = []
        app_state['current_download'] = None
        
        return jsonify({
            'success': True,
            'message': 'Desconectado exitosamente'
        })
    except Exception as e:
        logger.error(f"Error en desconexión: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/vms', methods=['GET'])
def get_vms():
    """
    Obtener lista de VMs
    Query params: host, cluster, power_state, folder (opcionales para filtrar)
    """
    try:
        if not session.get('connected') or not app_state['vmware_service']:
            return jsonify({
                'success': False,
                'error': 'No conectado a vCenter'
            }), 401
        
        # Obtener parámetros de filtro
        filters = {
            'host': request.args.get('host'),
            'cluster': request.args.get('cluster'),
            'power_state': request.args.get('power_state'),
            'folder': request.args.get('folder')
        }
        
        # Remover filtros vacíos
        filters = {k: v for k, v in filters.items() if v}
        
        # Obtener VMs
        vms = app_state['vmware_service'].get_vms(filters)
        
        # Obtener valores únicos para los filtros
        filter_options = app_state['vmware_service'].get_filter_options()
        
        return jsonify({
            'success': True,
            'vms': vms,
            'filter_options': filter_options,
            'total': len(vms)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo VMs: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error obteniendo VMs: {str(e)}'
        }), 500


@app.route('/api/poweroff', methods=['POST'])
def poweroff_vm():
    """
    Apagar una VM
    Body: {vm_name}
    """
    try:
        if not session.get('connected') or not app_state['vmware_service']:
            return jsonify({
                'success': False,
                'error': 'No conectado a vCenter'
            }), 401
        
        data = request.get_json()
        vm_name = data.get('vm_name')
        
        if not vm_name:
            return jsonify({
                'success': False,
                'error': 'Nombre de VM requerido'
            }), 400
        
        result = app_state['vmware_service'].poweroff_vm(vm_name)
        
        if result['success']:
            logger.info(f"VM apagada exitosamente: {vm_name}")
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error apagando VM: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error: {str(e)}'
        }), 500


@app.route('/api/export', methods=['POST'])
def export_vms():
    """
    Exportar VMs seleccionadas como OVA
    Body: {vm_names: [list], poweroff_before_export: bool}
    """
    try:
        if not session.get('connected') or not app_state['vmware_service']:
            return jsonify({
                'success': False,
                'error': 'No conectado a vCenter'
            }), 401
        
        data = request.get_json()
        vm_names = data.get('vm_names', [])
        poweroff_before = data.get('poweroff_before_export', True)
        
        if not vm_names:
            return jsonify({
                'success': False,
                'error': 'No se seleccionaron VMs'
            }), 400
        
        # Agregar a la cola de descarga
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        download_dir = os.path.join(
            config['download_directory'],
            datetime.now().strftime('%Y%m%d')
        )
        os.makedirs(download_dir, exist_ok=True)
        
        for vm_name in vm_names:
            app_state['download_queue'].append({
                'vm_name': vm_name,
                'status': 'pending',
                'progress': 0,
                'poweroff_before': poweroff_before,
                'download_dir': download_dir,
                'timestamp': timestamp
            })
        
        logger.info(f"Agregadas {len(vm_names)} VMs a la cola de descarga")
        
        # Iniciar descarga si no hay una en progreso
        if not app_state['current_download']:
            _process_next_download()
        
        return jsonify({
            'success': True,
            'message': f'{len(vm_names)} VM(s) agregadas a la cola',
            'queue_size': len(app_state['download_queue'])
        })
        
    except Exception as e:
        logger.error(f"Error iniciando exportación: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error: {str(e)}'
        }), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    """Obtener estado de descarga actual y cola"""
    try:
        return jsonify({
            'success': True,
            'current_download': app_state['current_download'],
            'queue': app_state['download_queue'],
            'queue_size': len(app_state['download_queue']),
            'history': app_state['download_history'][-10:]  # Últimas 10
        })
    except Exception as e:
        logger.error(f"Error obteniendo estado: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/cancel', methods=['POST'])
def cancel_download():
    """Cancelar descarga actual y limpiar cola"""
    try:
        app_state['download_queue'] = []
        
        if app_state['current_download']:
            app_state['current_download']['status'] = 'cancelled'
        
        logger.info("Cola de descargas cancelada")
        
        return jsonify({
            'success': True,
            'message': 'Descarga cancelada'
        })
    except Exception as e:
        logger.error(f"Error cancelando descarga: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _process_next_download():
    """Procesar siguiente descarga en la cola"""
    if not app_state['download_queue']:
        app_state['current_download'] = None
        return
    
    # Obtener siguiente descarga
    download_item = app_state['download_queue'].pop(0)
    app_state['current_download'] = download_item
    download_item['status'] = 'processing'
    
    try:
        vm_name = download_item['vm_name']
        download_dir = download_item['download_dir']
        poweroff_before = download_item['poweroff_before']
        
        logger.info(f"Iniciando descarga de: {vm_name}")
        
        # Apagar VM si es necesario
        if poweroff_before:
            download_item['status'] = 'powering_off'
            poweroff_result = app_state['vmware_service'].poweroff_vm(vm_name)
            
            if not poweroff_result['success']:
                raise Exception(f"Error apagando VM: {poweroff_result.get('error')}")
        
        # Exportar VM
        download_item['status'] = 'downloading'
        
        def progress_callback(progress, message):
            """Callback para actualizar progreso"""
            download_item['progress'] = progress
            download_item['message'] = message
            logger.info(f"{vm_name}: {progress}% - {message}")
        
        result = app_state['vmware_service'].export_vm_as_ova(
            vm_name=vm_name,
            download_dir=download_dir,
            progress_callback=progress_callback
        )
        
        if result['success']:
            download_item['status'] = 'completed'
            download_item['progress'] = 100
            download_item['file_path'] = result.get('file_path')
            download_item['message'] = 'Descarga completada'
            logger.info(f"Descarga completada: {vm_name}")
        else:
            download_item['status'] = 'failed'
            download_item['error'] = result.get('error')
            logger.error(f"Error descargando {vm_name}: {result.get('error')}")
        
    except Exception as e:
        download_item['status'] = 'failed'
        download_item['error'] = str(e)
        logger.error(f"Error procesando descarga de {download_item['vm_name']}: {str(e)}")
    
    finally:
        # Mover a historial
        app_state['download_history'].append(download_item)
        
        # Procesar siguiente
        app_state['current_download'] = None
        if app_state['download_queue']:
            _process_next_download()


if __name__ == '__main__':
    print("=" * 60)
    print("ESXi OVA Downloader - Iniciando servidor")
    print("=" * 60)
    print(f"Directorio de descargas: {config['download_directory']}")
    print(f"Accede a la aplicación en: http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
