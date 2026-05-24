# MATRIZ DE PRODUCTOS

menu = [
    ["Hamburguesa", "Comida Rapida", 25000],
    ["Pizza", "Comida Rapida", 42000],
    ["Ensalada", "Saludable", 18000],
    ["Pasta", "Italiana", 35000],
    ["Sushi", "Japonesa", 50000],
    ["Tacos", "Mexicana", 28000]
]

# FUNCION PARA CALCULAR DESCUENTO

def calcular_precio_final(categoria, precio):

    categoria_objetivo = "Comida Rapida"
    umbral = 30000

    if categoria == categoria_objetivo and precio > umbral:
        descuento = precio * 0.15
        precio_final = precio - descuento
    else:
        precio_final = precio

    return precio_final

# REPORTE FINAL

print("REPORTE DE PROMOCIONES")
print("-" * 50)

for producto in menu:

    nombre = producto[0]
    categoria = producto[1]
    precio = producto[2]

    precio_final = calcular_precio_final(categoria, precio)

    print("Producto:", nombre)
    print("Categoria:", categoria)
    print("Precio Base:", precio)
    print("Precio Final:", precio_final)
    print("-" * 50)