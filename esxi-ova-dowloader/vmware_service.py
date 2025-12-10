#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VMware Service - Gestión de vCenter y VMs
Maneja conexión, listado de VMs, apagado y exportación OVA usando HttpNfcLease
"""

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim, vmodl
import ssl
import logging
import os
import time
import requests
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class VMwareService:
    """Servicio para interactuar con vCenter y ESXi"""
    
    def __init__(self, host, username, password, verify_ssl=False):
        """
        Inicializar servicio de VMware
        
        Args:
            host: Hostname o IP del vCenter
            username: Usuario de vCenter
            password: Contraseña
            verify_ssl: Verificar certificados SSL (False por defecto)
        """
        self.host = host
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.si = None  # Service Instance
        self.content = None
        
    def connect(self):
        """
        Conectar a vCenter
        
        Returns:
            bool: True si conexión exitosa, False en caso contrario
        """
        try:
            # Crear contexto SSL sin verificación si es necesario
            context = None
            if not self.verify_ssl:
                context = ssl._create_unverified_context()
            
            # Conectar a vCenter
            self.si = SmartConnect(
                host=self.host,
                user=self.username,
                pwd=self.password,
                sslContext=context
            )
            
            if self.si:
                self.content = self.si.RetrieveContent()
                logger.info(f"Conectado a vCenter: {self.host}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error conectando a vCenter: {str(e)}")
            return False
    
    def disconnect(self):
        """Desconectar de vCenter"""
        try:
            if self.si:
                Disconnect(self.si)
                self.si = None
                self.content = None
                logger.info("Desconectado de vCenter")
        except Exception as e:
            logger.error(f"Error desconectando: {str(e)}")
    
    def get_obj(self, vimtype, name=None):
        """
        Obtener objeto de vCenter por tipo y nombre
        
        Args:
            vimtype: Tipo de objeto (vim.VirtualMachine, vim.HostSystem, etc.)
            name: Nombre del objeto (None para obtener todos)
            
        Returns:
            Objeto o lista de objetos
        """
        obj = None
        container = self.content.viewManager.CreateContainerView(
            self.content.rootFolder, vimtype, True
        )
        
        if name:
            for c in container.view:
                if c.name == name:
                    obj = c
                    break
        else:
            obj = container.view
        
        container.Destroy()
        return obj
    
    def get_vms(self, filters=None):
        """
        Obtener lista de VMs con metadatos
        
        Args:
            filters: Dict con filtros opcionales (host, cluster, power_state, folder)
            
        Returns:
            Lista de diccionarios con información de VMs
        """
        try:
            vms = self.get_obj([vim.VirtualMachine])
            vm_list = []
            
            for vm in vms:
                try:
                    # Obtener información básica
                    vm_info = {
                        'name': vm.name,
                        'power_state': vm.runtime.powerState,
                        'host': vm.runtime.host.name if vm.runtime.host else 'N/A',
                        'folder': vm.parent.name if vm.parent else 'N/A',
                        'guest_os': vm.config.guestFullName if vm.config else 'N/A',
                        'num_cpu': vm.config.hardware.numCPU if vm.config else 0,
                        'memory_mb': vm.config.hardware.memoryMB if vm.config else 0,
                        'annotation': vm.config.annotation if vm.config and vm.config.annotation else ''
                    }
                    
                    # Obtener cluster
                    cluster = 'N/A'
                    if vm.runtime.host:
                        host_obj = vm.runtime.host
                        if hasattr(host_obj, 'parent') and host_obj.parent:
                            if isinstance(host_obj.parent, vim.ClusterComputeResource):
                                cluster = host_obj.parent.name
                    
                    vm_info['cluster'] = cluster
                    
                    # Obtener tamaño de disco
                    total_storage_gb = 0
                    if vm.config and vm.config.hardware.device:
                        for device in vm.config.hardware.device:
                            if isinstance(device, vim.vm.device.VirtualDisk):
                                total_storage_gb += device.capacityInBytes / (1024**3)
                    
                    vm_info['storage_gb'] = round(total_storage_gb, 2)
                    
                    # Aplicar filtros si existen
                    if filters:
                        if 'host' in filters and vm_info['host'] != filters['host']:
                            continue
                        if 'cluster' in filters and vm_info['cluster'] != filters['cluster']:
                            continue
                        if 'power_state' in filters and vm_info['power_state'] != filters['power_state']:
                            continue
                        if 'folder' in filters and vm_info['folder'] != filters['folder']:
                            continue
                    
                    vm_list.append(vm_info)
                    
                except Exception as e:
                    logger.warning(f"Error procesando VM: {str(e)}")
                    continue
            
            logger.info(f"Obtenidas {len(vm_list)} VMs")
            return vm_list
            
        except Exception as e:
            logger.error(f"Error obteniendo VMs: {str(e)}")
            return []
    
    def get_filter_options(self):
        """
        Obtener valores únicos para filtros
        
        Returns:
            Dict con listas de valores únicos para cada filtro
        """
        try:
            vms = self.get_vms()
            
            hosts = sorted(list(set([vm['host'] for vm in vms if vm['host'] != 'N/A'])))
            clusters = sorted(list(set([vm['cluster'] for vm in vms if vm['cluster'] != 'N/A'])))
            folders = sorted(list(set([vm['folder'] for vm in vms if vm['folder'] != 'N/A'])))
            power_states = sorted(list(set([vm['power_state'] for vm in vms])))
            
            return {
                'hosts': hosts,
                'clusters': clusters,
                'folders': folders,
                'power_states': power_states
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo opciones de filtro: {str(e)}")
            return {
                'hosts': [],
                'clusters': [],
                'folders': [],
                'power_states': []
            }
    
    def poweroff_vm(self, vm_name, wait=True, timeout=120):
        """
        Apagar una VM
        
        Args:
            vm_name: Nombre de la VM
            wait: Esperar a que se apague completamente
            timeout: Timeout en segundos para esperar
            
        Returns:
            Dict con success y mensaje
        """
        try:
            vm = self.get_obj([vim.VirtualMachine], vm_name)
            
            if not vm:
                return {
                    'success': False,
                    'error': f'VM no encontrada: {vm_name}'
                }
            
            # Verificar estado actual
            if vm.runtime.powerState == 'poweredOff':
                return {
                    'success': True,
                    'message': f'VM ya está apagada: {vm_name}'
                }
            
            logger.info(f"Apagando VM: {vm_name}")
            
            # Intentar apagado suave primero (guest shutdown)
            try:
                vm.ShutdownGuest()
                logger.info(f"Apagado suave iniciado para: {vm_name}")
                
                if wait:
                    start_time = time.time()
                    while time.time() - start_time < timeout:
                        if vm.runtime.powerState == 'poweredOff':
                            return {
                                'success': True,
                                'message': f'VM apagada exitosamente: {vm_name}'
                            }
                        time.sleep(2)
                    
                    # Si no se apagó, forzar
                    logger.warning(f"Timeout en apagado suave, forzando: {vm_name}")
                    task = vm.PowerOffVM_Task()
                    self._wait_for_task(task)
                
            except Exception as guest_error:
                # VMware tools no disponible, apagar directamente
                logger.info(f"VMware Tools no disponible, apagando directamente: {vm_name}")
                task = vm.PowerOffVM_Task()
                self._wait_for_task(task)
            
            return {
                'success': True,
                'message': f'VM apagada exitosamente: {vm_name}'
            }
            
        except Exception as e:
            logger.error(f"Error apagando VM {vm_name}: {str(e)}")
            return {
                'success': False,
                'error': f'Error apagando VM: {str(e)}'
            }
    
    def export_vm_as_ova(self, vm_name, download_dir, progress_callback=None):
        """
        Exportar VM como OVA usando HttpNfcLease
        
        Args:
            vm_name: Nombre de la VM
            download_dir: Directorio donde guardar el OVA
            progress_callback: Función callback(progress, message) para reportar progreso
            
        Returns:
            Dict con success, file_path y mensaje
        """
        try:
            vm = self.get_obj([vim.VirtualMachine], vm_name)
            
            if not vm:
                return {
                    'success': False,
                    'error': f'VM no encontrada: {vm_name}'
                }
            
            # Verificar que la VM esté apagada
            if vm.runtime.powerState != 'poweredOff':
                return {
                    'success': False,
                    'error': f'VM debe estar apagada para exportar: {vm_name}'
                }
            
            logger.info(f"Iniciando exportación de: {vm_name}")
            
            if progress_callback:
                progress_callback(5, 'Iniciando exportación...')
            
            # Crear HttpNfcLease para exportación
            lease = vm.ExportVm()
            
            # Esperar a que el lease esté listo
            state = self._wait_for_lease(lease)
            
            if state != vim.HttpNfcLease.State.ready:
                return {
                    'success': False,
                    'error': f'Error iniciando exportación, estado: {state}'
                }
            
            if progress_callback:
                progress_callback(10, 'Lease obtenido, descargando archivos...')
            
            # Obtener información de los archivos a descargar
            lease_info = lease.info
            
            # Crear directorio para archivos temporales
            temp_dir = os.path.join(download_dir, f"temp_{vm_name}_{int(time.time())}")
            os.makedirs(temp_dir, exist_ok=True)
            
            downloaded_files = []
            
            # Calcular total de bytes (con validación de None)
            total_bytes = 0
            for device in lease_info.deviceUrl:
                if device.fileSize:
                    total_bytes += device.fileSize
            
            # Si total_bytes es 0, usar valor aproximado para evitar división por cero
            if total_bytes == 0:
                total_bytes = 1024 * 1024 * 1024  # 1GB como estimación
            
            downloaded_bytes = 0
            
            try:
                # Descargar cada archivo (VMDK, OVF, etc.)
                for device_url in lease_info.deviceUrl:
                    url = device_url.url
                    
                    # Reemplazar * con el hostname del vCenter
                    if url.startswith('https://*'):
                        url = url.replace('*', self.host)
                    
                    file_name = device_url.targetId
                    if not file_name:
                        # Extraer nombre del archivo de la URL
                        file_name = os.path.basename(urlparse(url).path)
                    
                    local_path = os.path.join(temp_dir, file_name)
                    
                    # Validar fileSize
                    file_size = device_url.fileSize if device_url.fileSize else 0
                    
                    logger.info(f"Descargando: {file_name} ({file_size / (1024*1024):.2f} MB)")
                    
                    if progress_callback:
                        progress_pct = 10 + int((downloaded_bytes / total_bytes) * 70) if total_bytes > 0 else 10
                        progress_callback(
                            progress_pct,
                            f'Descargando {file_name}...'
                        )
                    
                    # Descargar archivo
                    self._download_file(
                        url=url,
                        local_path=local_path,
                        file_size=file_size,
                        lease=lease,
                        total_bytes=total_bytes,
                        downloaded_bytes=downloaded_bytes,
                        progress_callback=progress_callback
                    )
                    
                    downloaded_files.append(local_path)
                    downloaded_bytes += file_size
                
                # Crear archivo OVA (tar de los archivos descargados)
                if progress_callback:
                    progress_callback(85, 'Creando archivo OVA...')
                
                ova_filename = f"{vm_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ova"
                ova_path = os.path.join(download_dir, ova_filename)
                
                # Usar tar para crear OVA
                import tarfile
                with tarfile.open(ova_path, 'w') as tar:
                    for file_path in downloaded_files:
                        tar.add(file_path, arcname=os.path.basename(file_path))
                
                if progress_callback:
                    progress_callback(95, 'Limpiando archivos temporales...')
                
                # Limpiar archivos temporales
                for file_path in downloaded_files:
                    try:
                        os.remove(file_path)
                    except:
                        pass
                
                try:
                    os.rmdir(temp_dir)
                except:
                    pass
                
                # Completar el lease
                lease.HttpNfcLeaseComplete()
                
                if progress_callback:
                    progress_callback(100, 'Exportación completada')
                
                logger.info(f"Exportación completada: {ova_path}")
                
                return {
                    'success': True,
                    'file_path': ova_path,
                    'message': f'VM exportada exitosamente: {ova_filename}'
                }
                
            except Exception as download_error:
                # Abortar el lease en caso de error
                lease.HttpNfcLeaseAbort()
                raise download_error
                
        except Exception as e:
            logger.error(f"Error exportando VM {vm_name}: {str(e)}")
            return {
                'success': False,
                'error': f'Error exportando VM: {str(e)}'
            }
    
    def _wait_for_lease(self, lease, timeout=300):
        """
        Esperar a que el lease esté listo
        
        Args:
            lease: HttpNfcLease
            timeout: Timeout en segundos
            
        Returns:
            Estado del lease
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            state = lease.state
            
            if state == vim.HttpNfcLease.State.ready:
                return state
            elif state == vim.HttpNfcLease.State.error:
                logger.error(f"Error en lease: {lease.error}")
                return state
            
            time.sleep(1)
        
        logger.error("Timeout esperando lease")
        return lease.state
    
    def _download_file(self, url, local_path, file_size, lease, total_bytes, 
                       downloaded_bytes, progress_callback=None):
        """
        Descargar archivo desde URL con progreso
        
        Args:
            url: URL del archivo
            local_path: Ruta local donde guardar
            file_size: Tamaño del archivo
            lease: HttpNfcLease para actualizar progreso
            total_bytes: Total de bytes a descargar
            downloaded_bytes: Bytes descargados hasta ahora
            progress_callback: Callback para reportar progreso
        """
        headers = {
            'User-Agent': 'VMware-client'
        }
        
        # Autenticación básica
        auth = (self.username, self.password)
        
        # Descargar con streaming
        response = requests.get(
            url,
            headers=headers,
            auth=auth,
            verify=self.verify_ssl,
            stream=True
        )
        
        response.raise_for_status()
        
        chunk_size = 1024 * 1024  # 1 MB
        file_downloaded = 0
        
        # Asegurar que los valores no sean None
        total_bytes = total_bytes or 0
        downloaded_bytes = downloaded_bytes or 0
        file_size = file_size or 0
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    file_downloaded += len(chunk)
                    
                    # Actualizar progreso del lease
                    current_total = downloaded_bytes + file_downloaded
                    if total_bytes > 0:
                        progress_percent = int((current_total / total_bytes) * 100)
                        progress_percent = min(progress_percent, 100)  # No exceder 100%
                    else:
                        progress_percent = 0
                    
                    try:
                        lease.HttpNfcLeaseProgress(progress_percent)
                    except:
                        pass
                    
                    # Callback de progreso
                    if progress_callback:
                        if total_bytes > 0:
                            overall_progress = 10 + int((current_total / total_bytes) * 70)
                            overall_progress = min(overall_progress, 80)  # Max 80% durante descarga
                        else:
                            overall_progress = 10
                        
                        file_mb = file_downloaded / (1024 * 1024)
                        total_mb = file_size / (1024 * 1024) if file_size > 0 else 0
                        progress_callback(
                            overall_progress,
                            f'Descargando {os.path.basename(local_path)}: {file_mb:.1f}/{total_mb:.1f} MB'
                        )
    
    def _wait_for_task(self, task, timeout=300):
        """
        Esperar a que una tarea se complete
        
        Args:
            task: Tarea de vCenter
            timeout: Timeout en segundos
            
        Returns:
            bool: True si exitoso, False en caso contrario
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if task.info.state == vim.TaskInfo.State.success:
                return True
            elif task.info.state == vim.TaskInfo.State.error:
                logger.error(f"Error en tarea: {task.info.error}")
                return False
            
            time.sleep(1)
        
        logger.error("Timeout esperando tarea")
        return False
