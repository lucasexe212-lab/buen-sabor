from flask import Flask, render_template, jsonify, request
import sqlite3
import os

app = Flask(__name__)

# Configuración de SQLite (Se guarda en un archivo local)
DATABASE = 'buen_sabor.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row # Permite acceder a las columnas por nombre
    return conn

# Función para inicializar la base de datos si no existe
def init_db():
    if not os.path.exists(DATABASE):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.executescript('''
            CREATE TABLE productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                precio REAL NOT NULL,
                stock INTEGER NOT NULL,
                categoria TEXT NOT NULL
            );
            CREATE TABLE pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total REAL NOT NULL,
                detalles TEXT NOT NULL
            );
            INSERT INTO productos (nombre, precio, stock, categoria) VALUES
            ('Hamburguesa Clásica', 4500.00, 15, 'comidas'),
            ('Papas Fritas Grandes', 2500.00, 20, 'comidas'),
            ('Gaseosa 500ml', 1500.00, 30, 'bebidas'),
            ('Ensalada César', 3800.00, 5, 'comidas'),
            ('Agua Mineral', 1000.00, 0, 'bebidas'),
            ('Cerveza Artesanal', 2800.00, 12, 'bebidas');
        ''')
        conn.commit()
        conn.close()
        print("✅ Base de datos SQLite creada e inicializada con éxito.")

# Inicializar DB al arrancar el servidor
init_db()

# Ruta principal
@app.route('/')
def index():
    return render_template('Mobile.html')

# Ruta del Historial
@app.route('/historial')
def historial():
    return render_template('historial.html')

# API: Obtener productos
@app.route('/api/productos', methods=['GET'])
def get_productos():
    conn = get_db_connection()
    productos = conn.execute('SELECT * FROM productos').fetchall()
    conn.close()
    # Convertir a diccionarios para JSON
    return jsonify([dict(ix) for ix in productos])

# API: Crear pedido y descontar stock
@app.route('/api/pedidos', methods=['POST'])
def crear_pedido():
    data = request.json
    items = data['items']
    total = float(data['total'])

    conn = get_db_connection()
    try:
        # 1. Validar stock
        for item in items:
            stock_actual = conn.execute('SELECT stock FROM productos WHERE id = ?', (item['id'],)).fetchone()[0]
            if stock_actual < item['cantidad']:
                return jsonify({'success': False, 'error': f'Stock insuficiente para {item["nombre"]}'}), 400

        # 2. Descontar stock
        for item in items:
            conn.execute('UPDATE productos SET stock = stock - ? WHERE id = ?', (item['cantidad'], item['id']))

        # 3. Guardar pedido
        detalles = ", ".join([f"{i['cantidad']}x {i['nombre']}" for i in items])
        conn.execute('INSERT INTO pedidos (total, detalles) VALUES (?, ?)', (total, detalles))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Pedido confirmado'})

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

# API: Obtener historial
@app.route('/api/historial', methods=['GET'])
def get_historial():
    conn = get_db_connection()
    pedidos = conn.execute('SELECT * FROM pedidos ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in pedidos])

if __name__ == '__main__':
    # host='0.0.0.0' permite acceso desde la red local (celulares en el mismo WiFi)
    app.run(debug=True, host='0.0.0.0', port=5000)