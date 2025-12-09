import sys

def input_numero(mensaje):
    """Solicita un número (float) al usuario."""
    while True:
        try:
            val = input(mensaje)
            return float(val.replace(',', '.'))
        except ValueError:
            print("Por favor, introduce un número válido.")

def input_si_no(mensaje):
    """Solicita una respuesta S/N."""
    while True:
        val = input(mensaje + " (S/N): ").strip().upper()
        if val in ['S', 'N']:
            return val
        print("Por favor, responde 'S' para Sí o 'N' para No.")

def input_int(mensaje):
    """Solicita un número entero."""
    while True:
        try:
            val = input(mensaje)
            return int(val)
        except ValueError:
            print("Por favor, introduce un número entero.")

def redondear(numero):
    """Redondeo a 2 decimales según normativa euro."""
    return round(numero, 2)

def truncar(numero):
    """Trunca a 2 decimales sin redondear (usado para el tipo de retención)."""
    return int(numero * 100) / 100.0

# --- TABLAS Y CONSTANTES (SEGÚN DOCUMENTO PDF PAG 30) ---
ESCALA_RETENCION = [
    (0.00, 0.00, 19.00),         # Hasta 12.450 (tramo 1 implícito)
    (12450.00, 2365.50, 24.00),  # De 12.450 a 20.200
    (20200.00, 4225.50, 30.00),  # De 20.200 a 35.200
    (35200.00, 8725.50, 37.00),  # De 35.200 a 60.000
    (60000.00, 17901.50, 45.00), # De 60.000 a 300.000
    (300000.00, 125901.50, 47.00)# De 300.000 en adelante
]

# --- LÓGICA DE CÁLCULO ---

def calcular_escala(base):
    """Función ESCALA (BASE...) descrita en Página 30 - Tabla 2"""
    cuota = 0.0
    resto = 0.0
    
    # Encontrar el tramo
    tramo_actual = None
    for i in range(len(ESCALA_RETENCION) - 1, -1, -1):
        if base >= ESCALA_RETENCION[i][0]:
            tramo_actual = ESCALA_RETENCION[i]
            break
            
    if tramo_actual:
        limite_inferior, cuota_base, porcentaje = tramo_actual
        resto = base - limite_inferior
        cuota = cuota_base + (resto * (porcentaje / 100.0))
        
    return cuota

def main():
    print("##########################################################")
    print("#   CALCULADORA DE RETENCIÓN IRPF Y SALARIO NETO 2025    #")
    print("#   Basado en el Algoritmo Oficial de la AEAT (Nov 2025) #")
    print("##########################################################\n")

    # 1. DATOS DE ENTRADA (Páginas 5 y 40)
    print("--- DATOS ECONÓMICOS ---")
    retribuciones_totales = input_numero("Introduce tu Salario Bruto Anual Total (RETRIB): ")
    
    # Gastos deducibles: Seguridad Social
    print("\nNecesitamos estimar tus gastos de Seguridad Social (Cotizaciones).")
    print("Si lo sabes exacto, introdúcelo. Si no, pon 0 y estimaremos un 6.35% estándar.")
    ss_input = input_numero("Gastos de Seguridad Social anuales (pon 0 para estimar): ")
    
    if ss_input == 0:
        gastos_ss = retribuciones_totales * 0.0635
        print(f"   -> Seguridad Social estimada: {gastos_ss:.2f} €")
    else:
        gastos_ss = ss_input

    # 2. SITUACIÓN FAMILIAR (Página 39)
    print("\n--- SITUACIÓN FAMILIAR (SITUFAM) ---")
    print("1. Soltero/Viudo/Divorciado CON hijos menores de 18 (o discapacitados) y SIN convivir con la otra parte.")
    print("2. Casado y no separado, cuyo cónyuge obtiene rentas < 1.500€ anuales.")
    print("3. Otros (Solteros sin hijos, Casados con cónyuge que trabaja, etc.) - Opción más común.")
    
    situacion = 0
    while situacion not in [1, 2, 3]:
        situacion = input_int("Elige tu situación (1, 2 o 3): ")

    # Datos adicionales hijos
    num_hijos = 0
    hijos_menores_3 = 0
    
    if situacion == 1 or situacion == 3: # En sit 2 también puede haber hijos, pero pedimos siempre
       tiene_hijos = input_si_no("¿Tienes descendientes (hijos) menores de 25 años o con discapacidad?")
       if tiene_hijos == 'S':
           num_hijos = input_int("¿Cuántos hijos en total?: ")
           if num_hijos > 0:
               hijos_menores_3 = input_int(f"De esos {num_hijos}, ¿cuántos son menores de 3 años?: ")

    # Ascendientes (Simplificado para el script)
    ascendientes_mayores_65 = 0
    convive_ascendientes = input_si_no("¿Convives con ascendientes (padres/abuelos) mayores de 65 años a tu cargo?")
    if convive_ascendientes == 'S':
        ascendientes_mayores_65 = input_int("¿Cuántos ascendientes mayores de 65 años?: ")

    # Contrato (Página 33 y 36 para límites mínimos)
    print("\n--- TIPO DE CONTRATO ---")
    print("G. General (Indefinido)")
    print("T. Temporal inferior a 1 año")
    tipo_contrato = input("Tipo de contrato (G/T): ").strip().upper()

    # 3. CÁLCULO DE GASTOS DEDUCIBLES (Página 22)
    gastos_generales = 2000.00
    otros_gastos = gastos_generales # Aquí se podrían sumar incrementos por movilidad o discapacidad
    
    # Límite de gastos (Página 22: Si OTROSGASTOS > RETRIB - COTIZACIONES...)
    rendimiento_neto_previo = retribuciones_totales - gastos_ss
    if otros_gastos > rendimiento_neto_previo:
        otros_gastos = rendimiento_neto_previo
        if otros_gastos < 0: otros_gastos = 0
        
    gastos_totales = gastos_ss + otros_gastos
    
    # 4. RENDIMIENTO NETO DEL TRABAJO (RNT) (Página 22)
    # Asumimos IRREGULAR1 y 2 en 0 para simplificar
    rnt = retribuciones_totales - gastos_ss
    if rnt < 0: rnt = 0

    # 5. REDUCCIÓN ART 20 LIRPF (Página 23 - Algoritmo complejo)
    # Se aplica sobre el RNT (Bruto - SS)
    red20 = 0.0
    
    if rnt <= 14852.00:
        red20 = 7302.00
    elif 14852.00 < rnt <= 17673.52:
        red20 = 7302.00 - (1.75 * (rnt - 14852.00))
    elif 17673.52 < rnt < 19747.50:
        red20 = 2364.34 - (1.14 * (rnt - 17673.52))
    else:
        red20 = 0.00
        
    red20 = redondear(red20) # Función REDONDEAR1 del documento

    # 6. RENDIMIENTO NETO REDUCIDO (Página 22/23)
    # RNTREDU = RNT - OTROSGASTOS - RED20
    # Nota: RNT arriba lo calculé como (Bruto - SS). El algoritmo dice RNT = RETRIB - GASTOS. 
    # Corrección estricta: RNT del algoritmo (pag 22) = Retrib - Reducciones irregulares - Cotizaciones.
    # Luego RNTREDU = RNT - OtrosGastos (2000) - Red20.
    
    rnt_redu = rnt - otros_gastos - red20
    if rnt_redu < 0: rnt_redu = 0

    # 7. MÍNIMO PERSONAL Y FAMILIAR (Páginas 24 - 28)
    # A. Mínimo del contribuyente
    min_per = 5550.00
    # Asumimos < 65 años para simplificar, o preguntar edad:
    # edad = input_int("Tu edad: ") ... lógica 65PER
    
    # B. Mínimo por descendientes (Simplificado caso general)
    min_des = 0.0
    for i in range(1, num_hijos + 1):
        if i == 1: min_des += 2400.00
        elif i == 2: min_des += 2700.00
        elif i == 3: min_des += 4000.00
        else: min_des += 4500.00
    
    # Plus menores de 3 años
    if hijos_menores_3 > 0:
        min_des += (hijos_menores_3 * 2800.00)
        
    # C. Mínimo ascendientes
    min_as = 0.0
    if ascendientes_mayores_65 > 0:
        min_as += (ascendientes_mayores_65 * 1150.00) # Asumimos >65 y <75. Si >75 es 1150+1400.

    # Total Mínimo Personal y Familiar (MINPERFA)
    # Asumimos sin discapacidad para simplificar, salvo que se añada la lógica
    min_per_fa = min_per + min_des + min_as 
    
    # 8. BASE PARA CALCULAR EL TIPO (Página 29)
    # BASE = RNTREDU - Reducciones (Pensión, Hijos, etc. asumimos 0)
    base_calculo = rnt_redu
    if base_calculo < 0: base_calculo = 0

    # 9. CUOTA DE RETENCIÓN (Página 29-31)
    # A. Límites excluyentes (Página 29 - Tabla 1)
    # Simplificación de la lógica de exclusión
    limite_excluyente = 0
    if situacion == 1:
        limite_excluyente = 17644 if num_hijos <= 1 else 18694
    elif situacion == 2:
        if num_hijos == 0: limite_excluyente = 17197
        elif num_hijos == 1: limite_excluyente = 18130
        else: limite_excluyente = 19262
    else: # Situacion 3
        if num_hijos == 0: limite_excluyente = 15876
        elif num_hijos == 1: limite_excluyente = 16342
        else: limite_excluyente = 16867
        
    es_exento = False
    if retribuciones_totales <= limite_excluyente:
        es_exento = True
        cuota_final = 0.0
        tipo_final = 0.0
    else:
        # B. Cálculo de Cuotas (Página 31)
        # Cuota 1 = Escala(Base)
        cuota_1 = calcular_escala(base_calculo)
        
        # Cuota 2 = Escala(Mínimo Personal y Familiar)
        cuota_2 = calcular_escala(min_per_fa)
        
        # Cuota Líquida
        cuota_final = cuota_1 - cuota_2
        if cuota_final < 0: cuota_final = 0.0
        
        # Límite del 43% (Art 85.3 RIRPF)
        # Si retrib <= 35.200, la cuota tiene un techo máximo
        if retribuciones_totales <= 35200.00:
            limite_43 = (retribuciones_totales - limite_excluyente) * 0.43
            if cuota_final > limite_43:
                cuota_final = limite_43

        # 10. TIPO DE RETENCIÓN (Página 33)
        # Tipo = (Cuota / Retribuciones) * 100
        tipo_calculado = (cuota_final / retribuciones_totales) * 100
        tipo_truncado = truncar(tipo_calculado) # Se trunca a 2 decimales
        
        # Mínimos por contrato (Página 33)
        tipo_final = tipo_truncado
        if tipo_contrato == 'T': # Inferior a un año
            if tipo_final < 2.00:
                tipo_final = 2.00
        
        # Máximo legal general
        if tipo_final > 47.00:
            tipo_final = 47.00

    # 11. CÁLCULO FINAL IMPORTE (Página 33)
    importe_anual_retencion = (retribuciones_totales * tipo_final) / 100
    importe_anual_retencion = redondear(importe_anual_retencion)
    
    salario_neto_anual = retribuciones_totales - gastos_ss - importe_anual_retencion
    salario_neto_mensual_12 = salario_neto_anual / 12
    salario_neto_mensual_14 = salario_neto_anual / 14

    # --- RESULTADOS ---
    print("\n" + "="*40)
    print(f"      RESULTADOS ESTIMADOS 2025")
    print("="*40)
    print(f"Salario Bruto Anual:      {retribuciones_totales:10.2f} €")
    print(f"Seguridad Social (est.):  -{gastos_ss:9.2f} €")
    print(f"IRPF Anual ({tipo_final:.2f}%):      -{importe_anual_retencion:9.2f} €")
    print("-" * 40)
    print(f"SALARIO NETO ANUAL:       {salario_neto_anual:10.2f} €")
    print("="*40)
    print(f"Neto Mensual (12 pagas):  {salario_neto_mensual_12:10.2f} €")
    print(f"Neto Mensual (14 pagas):  {salario_neto_mensual_14:10.2f} €")
    print("\nNOTA: Estos cálculos son una estimación basada en el algoritmo")
    print("general (Enero-Nov 2025). No incluye regularizaciones por pagos")
    print("de hipoteca (anteriores a 2013), pensiones compensatorias, etc.")
    print("Revisa tu nómina oficial para el dato exacto.")

if __name__ == "__main__":
    main()
