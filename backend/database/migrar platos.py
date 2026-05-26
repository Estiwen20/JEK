"""
Ejecuta este script UNA SOLA VEZ para agregar las columnas categoria e icono
a la tabla platos sin perder los datos existentes.

Uso: python migrar_platos.py
"""
import sqlite3
import os

# Ajusta esta ruta si tu BD está en otro lugar
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "database", "restaurante.db")

def migrar():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Verificar si ya existen las columnas
    cols = [row[1] for row in cursor.execute("PRAGMA table_info(platos)").fetchall()]

    if "categoria" not in cols:
        cursor.execute("ALTER TABLE platos ADD COLUMN categoria TEXT NOT NULL DEFAULT 'Otros'")
        print("✅ Columna 'categoria' agregada.")
    else:
        print("ℹ️  Columna 'categoria' ya existe.")

    if "icono" not in cols:
        cursor.execute("ALTER TABLE platos ADD COLUMN icono TEXT NOT NULL DEFAULT '🍽️'")
        print("✅ Columna 'icono' agregada.")
    else:
        print("ℹ️  Columna 'icono' ya existe.")

    conn.commit()
    conn.close()
    print("\n✅ Migración completada correctamente.")

if __name__ == "__main__":
    migrar()