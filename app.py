from flask import Flask, render_template, jsonify, request
import sqlite3
import os

# ⚠️ IMPORTANTE: Definir 'app' PRIMERO, antes de usarlo
app = Flask(__name__)

# Configuración de SQLite
DATABASE = 'buen_sabor.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

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
        print("✅ Base de datos SQLite creada.")

init_db()

@app.route('/')
def index():
    return render_template('Mobile.html')

@app.route('/historial')
def historial():
    return render_template('historial.html')

@app.route('/api/productos', methods=['GET'])
def get_productos():
    conn = get_db_connection()
    productos = conn.execute('SELECT * FROM productos').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in productos])

@app.route('/api/pedidos', methods=['POST'])
def crear_pedido():
    data = request.json
    items = data['items']
    total = float(data['total'])

    conn = get_db_connection()
    try:
        for item in items:
            stock_actual = conn.execute('SELECT stock FROM productos WHERE id = ?', (item['id'],)).fetchone()[0]
            if stock_actual < item['cantidad']:
                return jsonify({'success': False, 'error': f'Stock insuficiente para {item["nombre"]}'}), 400

        for item in items:
            conn.execute('UPDATE productos SET stock = stock - ? WHERE id = ?', (item['cantidad'], item['id']))

        detalles = ", ".join([f"{i['cantidad']}x {i['nombre']}" for i in items])
        conn.execute('INSERT INTO pedidos (total, detalles) VALUES (?, ?)', (total, detalles))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Pedido confirmado'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/historial', methods=['GET'])
def get_historial():
    conn = get_db_connection()
    pedidos = conn.execute('SELECT * FROM pedidos ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in pedidos])
# ===== RUTAS DE ADMINISTRACIÓN =====

@app.route('/admin')
def admin():
    return render_template('admin.html')

# API: Obtener todos los productos (para admin)
@app.route('/api/admin/productos', methods=['GET'])
def admin_get_productos():
    conn = get_db_connection()
    productos = conn.execute('SELECT * FROM productos ORDER BY id').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in productos])

# API: Agregar nuevo producto
@app.route('/api/admin/productos', methods=['POST'])
def admin_agregar_producto():
    data = request.json
    nombre = data['nombre']
    precio = float(data['precio'])
    stock = int(data['stock'])
    categoria = data['categoria']

    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO productos (nombre, precio, stock, categoria) VALUES (?, ?, ?, ?)',
            (nombre, precio, stock, categoria)
        )
        conn.commit()
        return jsonify({'success': True, 'message': 'Producto agregado'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

# API: Eliminar producto
@app.route('/api/admin/productos/<int:producto_id>', methods=['DELETE'])
def admin_eliminar_producto(producto_id):
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM productos WHERE id = ?', (producto_id,))
        conn.commit()
        return jsonify({'success': True, 'message': 'Producto eliminado'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

# API: Actualizar stock de producto
@app.route('/api/admin/productos/<int:producto_id>/stock', methods=['PUT'])
def admin_actualizar_stock(producto_id):
    data = request.json
    nuevo_stock = int(data['stock'])

    conn = get_db_connection()
    try:
        conn.execute('UPDATE productos SET stock = ? WHERE id = ?', (nuevo_stock, producto_id))
        conn.commit()
        return jsonify({'success': True, 'message': 'Stock actualizado'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)