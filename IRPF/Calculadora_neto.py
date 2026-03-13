import sys

ANIO_EJERCICIO = 2026

# ─── HELPERS DE ENTRADA ────────────────────────────────────────────────────────

def input_numero(mensaje):
    while True:
        try:
            val = input(f"  {mensaje} ").strip()
            return float(val.replace(',', '.'))
        except ValueError:
            print("  ! Por favor, introduce un número válido (usa , o . como decimal).")

def input_si_no(mensaje):
    while True:
        val = input(f"  {mensaje} (S/N): ").strip().upper()
        if val in ['S', 'N']:
            return val
        print("  ! Responde S o N.")

def input_int(mensaje, minimo=0, maximo=999):
    while True:
        try:
            val = int(input(f"  {mensaje} ").strip())
            if minimo <= val <= maximo:
                return val
            print(f"  ! Valor fuera de rango ({minimo}-{maximo}).")
        except ValueError:
            print("  ! Por favor, introduce un número entero.")

def input_opcion(mensaje, opciones):
    while True:
        val = input(f"  {mensaje} ").strip().upper()
        if val in opciones:
            return val
        print(f"  ! Opción no válida. Elige entre: {', '.join(opciones)}")

def seccion(titulo):
    print(f"\n{'─'*56}")
    print(f"  {titulo}")
    print(f"{'─'*56}")

def linea(texto, valor, signo=""):
    etiqueta = f"{texto}:"
    print(f"  {etiqueta:<32} {signo}{valor:>12}")

# ─── TABLAS Y CONSTANTES (Algoritmo AEAT 2026, pág. 30) ───────────────────────

ESCALA_RETENCION = [
    (0.00,       0.00,      19.00),   # Hasta 12.450
    (12450.00,   2365.50,   24.00),   # De 12.450 a 20.200
    (20200.00,   4225.50,   30.00),   # De 20.200 a 35.200
    (35200.00,   8725.50,   37.00),   # De 35.200 a 60.000
    (60000.00,   17901.50,  45.00),   # De 60.000 a 300.000
    (300000.00,  125901.50, 47.00),   # Desde 300.000
]

# ─── CÁLCULO ───────────────────────────────────────────────────────────────────

def redondear(n):
    return round(n, 2)

def truncar(n):
    return int(n * 100) / 100.0

def calcular_escala(base):
    for i in range(len(ESCALA_RETENCION) - 1, -1, -1):
        if base >= ESCALA_RETENCION[i][0]:
            limite, cuota_base, pct = ESCALA_RETENCION[i]
            return cuota_base + (base - limite) * (pct / 100.0)
    return 0.0

# ─── PROGRAMA PRINCIPAL ────────────────────────────────────────────────────────

def main():
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║   CALCULADORA DE RETENCIÓN IRPF Y SALARIO NETO 2026  ║")
    print("║   Algoritmo Oficial AEAT · Ejercicio 2026             ║")
    print("╚══════════════════════════════════════════════════════╝")

    # ── 1. DATOS ECONÓMICOS ───────────────────────────────────────────────────
    seccion("1. DATOS ECONÓMICOS")

    retribuciones_totales = input_numero("Salario bruto anual total (€):")

    print()
    print("  Cotizaciones a la Seguridad Social:")
    print("  · Si las conoces, introdúcelas directamente.")
    print("  · Si no, escribe 0 y se estimará el 6,35% estándar.")
    ss_input = input_numero("Cotizaciones S.S. anuales (€, o 0 para estimar):")

    if ss_input == 0:
        gastos_ss = retribuciones_totales * 0.0635
        print(f"  → Cotizaciones estimadas al 6,35%: {gastos_ss:,.2f} €")
    else:
        gastos_ss = ss_input

    # ── 2. DATOS PERSONALES ───────────────────────────────────────────────────
    seccion("2. DATOS PERSONALES")

    anio_nacimiento = input_int(
        f"Año de nacimiento (entre 1926 y {ANIO_EJERCICIO}):",
        minimo=1926, maximo=ANIO_EJERCICIO
    )
    edad = ANIO_EJERCICIO - anio_nacimiento

    # Mínimo del contribuyente según edad (pág. 24)
    min_per   = 5550.00
    per_65    = 1150.00 if edad > 64 else 0.00   # +65PER
    per_75    = 1400.00 if edad > 74 else 0.00   # +75PER
    min_con   = min_per + per_65 + per_75

    tramo_edad = "menor de 65 años"
    if edad > 74:
        tramo_edad = "mayor de 75 años"
    elif edad > 64:
        tramo_edad = "entre 65 y 74 años"
    print(f"  → Edad calculada: {edad} años ({tramo_edad})")
    print(f"  → Mínimo personal del contribuyente: {min_con:,.2f} €")

    # ── 3. SITUACIÓN FAMILIAR ─────────────────────────────────────────────────
    seccion("3. SITUACIÓN FAMILIAR")

    print("  1. Monoparental: soltero/viudo/divorciado CON hijos a cargo")
    print("     y sin convivir con la otra parte progenitora.")
    print("  2. Casado/a con cónyuge sin ingresos (< 1.500 €/año).")
    print("  3. Resto de situaciones (la más habitual).")
    print()
    situacion = input_int("Situación familiar (1, 2 o 3):", minimo=1, maximo=3)

    # Hijos (aplica a todas las situaciones)
    num_hijos    = 0
    hijos_men_3  = 0

    tiene_hijos = input_si_no("¿Tienes hijos/descendientes menores de 25 años (o con discapacidad) a cargo?")
    if tiene_hijos == 'S':
        num_hijos   = input_int("Número total de hijos:", minimo=1, maximo=16)
        hijos_men_3 = input_int(
            f"De esos {num_hijos}, ¿cuántos son menores de 3 años?:",
            minimo=0, maximo=num_hijos
        )

    # Ascendientes
    asc_65_74 = 0
    asc_75    = 0
    tiene_asc = input_si_no("¿Convives con ascendientes (padres/abuelos) mayores de 65 años a tu cargo?")
    if tiene_asc == 'S':
        asc_65_74 = input_int("  · ¿Cuántos tienen entre 65 y 74 años?:", minimo=0, maximo=6)
        asc_75    = input_int("  · ¿Cuántos tienen 75 años o más?:",       minimo=0, maximo=6)

    # ── 4. TIPO DE CONTRATO ───────────────────────────────────────────────────
    seccion("4. TIPO DE CONTRATO")

    print("  G. General / indefinido")
    print("  T. Temporal (duración inferior a 1 año)")
    tipo_contrato = input_opcion("Tipo de contrato (G/T):", ["G", "T"])

    # ═════════════════════════════════════════════════════════════════════════
    #  CÁLCULO SEGÚN ALGORITMO AEAT 2026
    # ═════════════════════════════════════════════════════════════════════════

    # Gastos deducibles (pág. 22)
    gastos_generales = 2000.00
    otros_gastos = gastos_generales
    rend_previo = retribuciones_totales - gastos_ss
    if otros_gastos > rend_previo:
        otros_gastos = max(rend_previo, 0.0)

    # RNT (pág. 22): RETRIB − COTIZACIONES  (asumimos IRREGULAR1/2 = 0)
    rnt = max(retribuciones_totales - gastos_ss, 0.0)

    # RED20 (pág. 23 — art. 20 LIRPF / RD-Ley 4/2024)
    if rnt <= 14852.00:
        red20 = 7302.00
    elif rnt <= 17673.52:
        red20 = 7302.00 - 1.75 * (rnt - 14852.00)
    elif rnt < 19747.50:
        red20 = 2364.34 - 1.14 * (rnt - 17673.52)
    else:
        red20 = 0.00
    red20 = redondear(red20)

    # RNTREDU (pág. 23)
    rnt_redu = max(rnt - otros_gastos - red20, 0.0)

    # Mínimo por descendientes (pág. 24-25)
    min_des = 0.0
    for i in range(1, num_hijos + 1):
        if   i == 1: min_des += 2400.00
        elif i == 2: min_des += 2700.00
        elif i == 3: min_des += 4000.00
        else:        min_des += 4500.00
    min_des += hijos_men_3 * 2800.00   # plus < 3 años
    min_des = redondear(min_des)

    # Mínimo por ascendientes (pág. 25-26)
    min_as = redondear((asc_65_74 + asc_75) * 1150.00 + asc_75 * 1400.00)

    # MINPERFA total (pág. 28)
    min_per_fa = min_con + min_des + min_as

    # Reducciones adicionales (pág. 23)
    redu_hijos = 600.00 if num_hijos > 2 else 0.00  # más de 2 descendientes
    redu = redu_hijos  # (PENSION y DESEM se añadirían si se implementa SITUPER)

    # BASE (pág. 29)
    base_calculo = max(rnt_redu - redu, 0.0)

    # ── Límites excluyentes (Tabla 1, pág. 29) ────────────────────────────────
    if situacion == 1:
        lim_ex = 17644 if num_hijos <= 1 else 18694
    elif situacion == 2:
        lim_ex = {0: 17197, 1: 18130}.get(num_hijos, 19262)
    else:
        lim_ex = {0: 15876, 1: 16342}.get(num_hijos, 16867)

    if retribuciones_totales <= lim_ex:
        cuota_final = 0.0
        tipo_final  = 0.0
        es_exento   = True
    else:
        es_exento = False
        cuota_1 = calcular_escala(base_calculo)
        cuota_2 = calcular_escala(min_per_fa)
        cuota_final = max(cuota_1 - cuota_2, 0.0)

        # Límite del 43% (art. 85.3 RIRPF)
        if retribuciones_totales <= 35200.00:
            limite_43 = (retribuciones_totales - lim_ex) * 0.43
            cuota_final = min(cuota_final, limite_43)

        # Tipo de retención (pág. 33)
        tipo_final = truncar((cuota_final / retribuciones_totales) * 100)

        if tipo_contrato == 'T' and tipo_final < 2.00:
            tipo_final = 2.00
        if tipo_final > 47.00:
            tipo_final = 47.00

    # Importe y neto
    importe_retencion   = redondear((retribuciones_totales * tipo_final) / 100)
    salario_neto_anual  = retribuciones_totales - gastos_ss - importe_retencion
    neto_12             = salario_neto_anual / 12
    neto_14             = salario_neto_anual / 14

    # ═════════════════════════════════════════════════════════════════════════
    #  RESULTADOS
    # ═════════════════════════════════════════════════════════════════════════
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║              RESULTADOS ESTIMADOS 2026               ║")
    print("╚══════════════════════════════════════════════════════╝")

    # Desglose del cálculo
    seccion("Desglose del cálculo")
    linea("Salario bruto anual",          f"{retribuciones_totales:,.2f} €")
    linea("Cotizaciones S.S.",            f"{gastos_ss:,.2f} €",        "−")
    linea("Otros gastos deducibles",      f"{otros_gastos:,.2f} €",     "−")
    print(f"  {'─'*46}")
    linea("Rendimiento neto del trabajo", f"{rnt:,.2f} €")
    linea("Reducción art. 20 (RED20)",    f"{red20:,.2f} €",            "−")
    print(f"  {'─'*46}")
    linea("Rendimiento neto reducido",    f"{rnt_redu:,.2f} €")
    if redu > 0:
        linea("Reducción adicional (>2 hijos)", f"{redu:,.2f} €",      "−")
    linea("BASE de retención",            f"{base_calculo:,.2f} €")
    print()
    linea("Mínimo personal (MINCON)",     f"{min_con:,.2f} €")
    if min_des > 0:
        linea("  · Por descendientes",    f"{min_des:,.2f} €")
    if min_as > 0:
        linea("  · Por ascendientes",     f"{min_as:,.2f} €")
    linea("Mínimo personal y familiar",   f"{min_per_fa:,.2f} €")

    # Resultado final
    seccion("Resultado final")
    if es_exento:
        print("  ✓ Rentas EXENTAS de retención según tabla de límites AEAT.")
        print(f"  (Tu salario {retribuciones_totales:,.2f} € no supera el límite de {lim_ex:,} €)\n")

    linea("Salario bruto anual",          f"{retribuciones_totales:,.2f} €")
    linea("Cotizaciones S.S.",            f"{gastos_ss:,.2f} €",        "−")
    linea(f"Retención IRPF ({tipo_final:.2f} %)",  f"{importe_retencion:,.2f} €", "−")
    print(f"  {'═'*46}")
    print(f"  {'SALARIO NETO ANUAL:':<32} {salario_neto_anual:>12,.2f} €")
    print(f"  {'═'*46}")
    print()
    linea("Neto mensual (12 pagas)",      f"{neto_12:,.2f} €")
    linea("Neto mensual (14 pagas)",      f"{neto_14:,.2f} €")

    print()
    print("  NOTA: Estimación basada en el algoritmo oficial AEAT 2026.")
    print("  No incluye regularizaciones, pensiones compensatorias,")
    print("  discapacidad ni anualidades por alimentos. Consulta tu")
    print("  nómina o asesor fiscal para el dato definitivo.")
    print()

if __name__ == "__main__":
    main()
