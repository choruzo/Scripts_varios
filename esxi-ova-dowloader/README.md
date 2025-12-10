# ESXi OVA Downloader

Aplicación web para descargar máquinas virtuales desde vCenter/ESXi como archivos OVA. Permite seleccionar múltiples VMs, apagarlas automáticamente y descargarlas de forma secuencial mediante la API de vCenter (HttpNfcLease).

## 🌟 Características

- ✅ **Conexión segura a vCenter** - Autenticación con credenciales en sesión (no se guardan)
- 📋 **Listado completo de VMs** - Visualiza todas las VMs con información detallada
- 🔍 **Filtros avanzados** - Filtra por Host, Cluster, Estado de energía y Folder
- ☑️ **Selección múltiple** - Selecciona una o varias VMs para descargar
- ⚡ **Apagado automático** - Apaga las VMs antes de exportar (opcional)
- 📦 **Exportación OVA** - Descarga usando HttpNfcLease con seguimiento de progreso
- 🔄 **Descarga secuencial** - Procesa las VMs una por una con cola visible
- 📊 **Seguimiento de progreso** - Barra de progreso en tiempo real para cada descarga
- 📁 **Organización automática** - Archivos guardados en carpetas por fecha (YYYYMMDD)
- 🌐 **Interfaz web moderna** - UI responsive con diseño intuitivo

## 📋 Requisitos

- Python 3.8 o superior
- Acceso a vCenter Server
- Permisos para exportar VMs y apagar/encender VMs
- Red accesible desde el servidor que ejecuta la aplicación hasta vCenter

## 🚀 Instalación

### 1. Clonar o descargar este proyecto

```powershell
cd esxi-ova-dowloader
```

### 2. Crear entorno virtual (recomendado)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 4. Configurar la aplicación

Copia el archivo de configuración de ejemplo:

```powershell
Copy-Item config.example.json config.json
```

Edita `config.json` según tus necesidades:

```json
{
  "download_directory": "./downloads",
  "timeout": 300,
  "verify_ssl": false,
  "chunk_size_mb": 1,
  "max_concurrent_downloads": 1
}
```

**Parámetros:**
- `download_directory`: Directorio donde se guardarán los archivos OVA
- `timeout`: Timeout en segundos para operaciones de vCenter
- `verify_ssl`: `false` para certificados autofirmados, `true` para certificados válidos
- `chunk_size_mb`: Tamaño de chunk para descargas (1 MB recomendado)
- `max_concurrent_downloads`: Número de descargas simultáneas (1 = secuencial)

## 🎯 Uso

### 1. Iniciar la aplicación

```powershell
python app.py
```

La aplicación se iniciará en `http://localhost:5000`

### 2. Conectar a vCenter

1. Abre tu navegador en `http://localhost:5000`
2. Ingresa los datos de conexión:
   - **Host vCenter**: Nombre o IP del vCenter (ej: `vcenter.empresa.com`)
   - **Usuario**: Usuario con permisos (ej: `administrator@vsphere.local`)
   - **Contraseña**: Contraseña del usuario
3. Click en **Conectar**

### 3. Seleccionar VMs

1. Una vez conectado, verás la lista de VMs disponibles
2. Usa los filtros para encontrar las VMs deseadas:
   - **Host**: Filtra por servidor ESXi
   - **Cluster**: Filtra por cluster
   - **Estado**: poweredOn, poweredOff, suspended
   - **Folder**: Filtra por carpeta de vCenter
3. Selecciona las VMs marcando los checkboxes
4. Puedes usar "Seleccionar todas" para marcar todas las VMs visibles

### 4. Descargar OVAs

1. Verifica que la opción **"Apagar VMs antes de exportar"** esté marcada
   - ⚠️ **Importante**: Las VMs deben estar apagadas para exportar como OVA
2. Click en **"Descargar Seleccionadas"**
3. Confirma la descarga en el diálogo
4. El panel de **Cola de Descargas** mostrará el progreso:
   - **Descarga Actual**: VM que se está procesando con barra de progreso
   - **En Cola**: VMs pendientes de descarga
   - **Historial Reciente**: Últimas 10 descargas completadas/fallidas

### 5. Archivos descargados

Los archivos OVA se guardan en:
```
downloads/
  └── YYYYMMDD/           # Carpeta con fecha (ej: 20251210)
      ├── VM1_20251210_143022.ova
      ├── VM2_20251210_143156.ova
      └── ...
```

## 🔧 Arquitectura Técnica

### Backend (Python)

- **Flask**: Framework web para servir la API REST
- **pyvmomi**: SDK oficial de VMware para Python
- **HttpNfcLease**: API de vCenter para exportación OVA con progreso
- **Descarga secuencial**: Cola FIFO que procesa VMs una por una

### Frontend (HTML/CSS/JavaScript)

- **Vanilla JavaScript**: Sin frameworks, código ligero y rápido
- **Polling de estado**: Actualización cada 2 segundos del progreso
- **Filtros dinámicos**: Carga opciones automáticamente desde vCenter
- **UI Responsive**: Funciona en desktop y dispositivos móviles

### Flujo de Exportación

1. **Conexión**: Autenticación con vCenter usando pyvmomi
2. **Listado**: Obtención de VMs con metadatos completos
3. **Selección**: Usuario selecciona VMs desde la UI
4. **Cola**: VMs agregadas a cola de descarga secuencial
5. **Apagado** (si está marcado):
   - Intento de apagado suave (ShutdownGuest)
   - Si falla/timeout: apagado forzado (PowerOff)
6. **Exportación**:
   - Crear HttpNfcLease para la VM
   - Descargar archivos (VMDK, OVF, etc.)
   - Empaquetar en archivo TAR (formato OVA)
   - Actualizar progreso en tiempo real
7. **Siguiente**: Procesar siguiente VM en cola

## ⚠️ Consideraciones Importantes

### Apagado de VMs

- **Las VMs DEBEN estar apagadas** para exportar como OVA
- La opción "Apagar VMs antes de exportar" está marcada por defecto
- El sistema intenta apagado suave primero, luego forzado si es necesario
- **Planifica las descargas** para evitar interrupciones en producción

### Rendimiento

- Las exportaciones pueden ser **lentas** dependiendo de:
  - Tamaño de la VM (discos grandes = más tiempo)
  - Velocidad de red entre la app y vCenter
  - Carga del storage/datastore
- Ejemplo: VM de 100GB puede tardar 30-60 minutos
- La descarga secuencial evita saturar vCenter/red

### Espacio en Disco

- Asegúrate de tener **suficiente espacio** en `download_directory`
- Los archivos OVA ocupan aproximadamente el tamaño de los discos de la VM
- Ejemplo: VM con 3 discos de 50GB = ~150GB de OVA

### Seguridad

- **Credenciales en sesión**: No se guardan en disco
- **SSL**: Usa `verify_ssl: false` solo en entornos de confianza
- **Permisos**: El usuario debe tener permisos de exportación en vCenter
- **Puerto 5000**: Considera usar HTTPS en producción

## 🐛 Troubleshooting

### Error: "No se pudo conectar a vCenter"

- Verifica el hostname/IP del vCenter
- Comprueba que el puerto 443 esté accesible
- Revisa usuario y contraseña
- Si usa certificado autofirmado: `verify_ssl: false`

### Error: "VM debe estar apagada para exportar"

- Marca la opción "Apagar VMs antes de exportar"
- O apaga la VM manualmente antes de exportar

### Error: "Timeout esperando lease"

- La VM puede estar en uso o bloqueada
- Aumenta el `timeout` en `config.json`
- Verifica que no haya snapshots en progreso

### Descarga muy lenta

- Normal para VMs grandes (>100GB)
- Verifica velocidad de red
- Considera descargar fuera de horario pico

### Error: "Error descargando archivo"

- Puede ser problema de red intermitente
- Reintenta la descarga
- Verifica logs en consola del servidor

## 📝 Logs

Los logs se muestran en la consola donde ejecutaste `python app.py`:

```
2025-12-10 14:30:22 - INFO - Conectado a vCenter: vcenter.empresa.com
2025-12-10 14:30:25 - INFO - Obtenidas 45 VMs
2025-12-10 14:31:10 - INFO - Agregadas 3 VMs a la cola de descarga
2025-12-10 14:31:12 - INFO - Iniciando descarga de: WebServer-01
2025-12-10 14:31:15 - INFO - Apagado suave iniciado para: WebServer-01
2025-12-10 14:31:45 - INFO - WebServer-01: 15% - Descargando disk-0.vmdk: 12.5/80.0 MB
...
2025-12-10 14:45:33 - INFO - Descarga completada: WebServer-01
```

## 🔄 Actualización

Para actualizar las dependencias:

```powershell
pip install --upgrade -r requirements.txt
```

## 📄 Licencia

Este proyecto es de código abierto. Úsalo y modifícalo según tus necesidades.

## 👨‍💻 Soporte

Para reportar problemas o sugerencias, revisa los logs y verifica:
1. Conectividad de red con vCenter
2. Permisos del usuario en vCenter
3. Espacio disponible en disco
4. Configuración de `config.json`

## 🎓 Referencias

- [Documentación de pyvmomi](https://github.com/vmware/pyvmomi)
- [vSphere API Reference](https://developer.vmware.com/apis/vsphere-automation/latest/)
- [HttpNfcLease Documentation](https://vdc-repo.vmware.com/vmwb-repository/dcr-public/fe86d9b8-a400-4e19-aae0-71fb7d1ed798/b97d7eae-eaca-4338-93b6-bb7ffedbe449/vim.HttpNfcLease.html)

---

**Desarrollado para automatización de backups de máquinas virtuales VMware** 🖥️✨
