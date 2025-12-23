#!/bin/bash

# Colores
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
WHITE='\033[1;37m'
MAGENTA='\033[0;35m'
ORANGE='\033[38;5;208m'
NC='\033[0m'

MES=$(date +%m)

case $MES in
    01) 
        TEMA="Enero: Año Nuevo 🥂"; COLOR=$WHITE; ART='  [ ✨ FELIZ AÑO NUEVO SUSE ✨ ]'
        LOGO='  ____  
 ____  _   _ ____  _____ 
/ ___|| | | / ___|| ____|
\___ \| | | \___ \|  _|  
 ___) | |_| |___) | |___ 
|____/ \___/|____/|_____|  

     |    . . o|
     |  o  .  .|
     | . o  .  |
     |o .  . o |
     |   .  .  |
      \  o .  /
       '. . .'
         ||
         ||
         ||
         ||
         ||
      .__||__.
      (___)___)' ;;
    02) 
        TEMA="Febrero: Kernel & Low Level 🛠️"; COLOR=$CYAN; ART='  [ COMPILING THE FUTURE... ]'
        LOGO='  __01__
 ____  _   _ ____  _____ 
/ ___|| | | / ___|| ____|
\___ \| | | \___ \|  _|  
 ___) | |_| |___) | |___ 
|____/ \___/|____/|_____|' ;;
    03) 
        TEMA="Marzo: Primavera 🌸"; COLOR=$MAGENTA; ART='  [ FLORECIENDO EN OPENSUSE ]'
        LOGO='  _🌸_  
 ____  _   _ ____  _____ 
/ ___|| | | / ___|| ____|
\___ \| | | \___ \|  _|  
 ___) | |_| |___) | |___ 
|____/ \___/|____/|_____|' ;;
    04) 
        TEMA="Abril: Lluvias ☔"; COLOR=$CYAN; ART='  [ CODIFICANDO BAJO LA LLUVIA ]'
        LOGO='  _💧_  
 ____  _   _ ____  _____ 
/ ___|| | | / ___|| ____|
\___ \| | | \___ \|  _|  
 ___) | |_| |___) | |___ 
|____/ \___/|____/|_____|
       .-"""-.
     .'       '.
    /           \
   |_____________|
         ||
         ||
         ||
         ||
        / |
       |__|' ;;
    05) 
        TEMA="Mayo: Flores 💐"; COLOR=$GREEN; ART='  [ MAYO EN PLENO RENDIMIENTO ]'
        LOGO='  _💐_  
 ____  _   _ ____  _____ 
/ ___|| | | / ___|| ____|
\___ \| | | \___ \|  _|  
 ___) | |_| |___) | |___ 
|____/ \___/|____/|_____|' ;;
    06) 
        TEMA="Junio: Orgullo/Verano 🌈"; COLOR=$YELLOW; ART='  [ VERANO DE CÓDIGO ABIERTO ]'
        LOGO='  _🌈_  
 ____  _   _ ____  _____ 
/ ___|| | | / ___|| ____|
\___ \| | | \___ \|  _|  
 ___) | |_| |___) | |___ 
|____/ \___/|____/|_____|' ;;
    07) 
        TEMA="Julio: Playa 🏖️"; COLOR=$ORANGE; ART='  [ SUSE BAJO EL SOL ]'
        LOGO='  _☀️_  
 ____  _   _ ____  _____ 
/ ___|| | | / ___|| ____|
\___ \| | | \___ \|  _|  
 ___) | |_| |___) | |___ 
|____/ \___/|____/|_____|
         |
       \ _ /
     -= (_) =-
       / \
         |' ;;
    08) 
        TEMA="Agosto: Vacaciones 🍦"; COLOR=$CYAN; ART='  [ MANTENIENDO EL SERVIDOR FRÍO ]'
        LOGO='  _🍦_  
 ____  _   _ ____  _____ 
/ ___|| | | / ___|| ____|
\___ \| | | \___ \|  _|  
 ___) | |_| |___) | |___ 
|____/ \___/|____/|_____|' ;;
    09) 
        TEMA="Septiembre: Vuelta al trabajo 📚"; COLOR=$YELLOW; ART='  [ RE-BOOTING KNOWLEDGE ]'
        LOGO='  _📖_  
 ____  _   _ ____  _____ 
/ ___|| | | / ___|| ____|
\___ \| | | \___ \|  _|  
 ___) | |_| |___) | |___ 
|____/ \___/|____/|_____|' ;;
    10) 
        TEMA="Octubre: Halloween 🎃"; COLOR=$ORANGE; ART='  [ SPOOKY OPENSUSE SYSTEM ]'
        LOGO='  _🎃_  
 ____  _   _ ____  _____ 
/ ___|| | | / ___|| ____|
\___ \| | | \___ \|  _|  
 ___) | |_| |___) | |___ 
|____/ \___/|____/|_____|
          _,\/_
        ,'     `.
       /  /\ /\  \
      |   \ \/ /  |
      |    \__/   |
      |  \____/   |
       \         /
        `._   _,'
           ```' ;;
    11) 
        TEMA="Noviembre: Otoño 🍂"; COLOR=$YELLOW; ART='  [ HOJAS CAEN, EL KERNEL NO ]'
        LOGO='  _🍂_  
 ____  _   _ ____  _____ 
/ ___|| | | / ___|| ____|
\___ \| | | \___ \|  _|  
 ___) | |_| |___) | |___ 
|____/ \___/|____/|_____|' ;;
    12) 
        TEMA="Diciembre: Navidad 🎄"; COLOR=$WHITE; ART='  [ FELICES FIESTAS GEEKO ]'
        LOGO='  _🎄_  
 ____  _   _ ____  _____ 
/ ___|| | | / ___|| ____|
\___ \| | | \___ \|  _|  
 ___) | |_| |___) | |___ 
|____/ \___/|____/|_____|
           *
          / \
         / . \
        / * o \
       / o . @ \
      / . @ * o \
     / * o . @ * \
    /_____________\
          | |
         _| |_' ;;
esac

# Mostrar el logo personalizado
echo -e "${COLOR}${LOGO}${NC}"
echo -e "${COLOR}$ART${NC}\n"

# Estadísticas del Sistema
UPTIME=$(uptime -p)
LOAD=$(cat /proc/loadavg | awk '{print $1 " [1m]"}')
MEM_USAGE=$(free -m | awk '/Mem:/ { printf("%3.1f%%", $3/$2*100) }')
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}')
LOCAL_IP=$(hostname -I | awk '{print $1}')

echo -e "${CYAN}---------------------------------------------------${NC}"
echo -e "  ${GREEN}IP LOCAL     :${NC} $LOCAL_IP"
echo -e "  ${GREEN}CARGA (1m)   :${NC} $LOAD"
echo -e "  ${GREEN}USO MEMORIA  :${NC} $MEM_USAGE"
echo -e "  ${GREEN}DISCO (/)    :${NC} $DISK_USAGE usado"
echo -e "  ${GREEN}UPTIME       :${NC} $UPTIME"
echo -e "${CYAN}---------------------------------------------------${NC}"


