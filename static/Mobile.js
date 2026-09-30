/**
 * Mobile.js - Frontend conectado a Flask + SQLite + WhatsApp
 */

let carrito = [];
let todosLosProductos = [];
let filtroActual = 'todos';

// ⚠️ CONFIGURAR NÚMERO DEL DUEÑO (con código de país, sin + ni espacios)
// Ejemplo Argentina: 549 + código de área sin 0 ni 15 + número
// Ej: 5492611234567 (Mendoza)
const TELEFONO_DUEÑO = '543777635035'; // <-- CAMBIÁ ESTE NÚMERO

document.addEventListener('DOMContentLoaded', async () => {
    await cargarProductos();
});

async function cargarProductos() {
    try {
        const respuesta = await fetch('/api/productos');
        todosLosProductos = await respuesta.json();
        renderizarProductos();
    } catch (error) {
        mostrarToast('❌ Error al conectar con el servidor', 'error');
        console.error(error);
    }
}

function renderizarProductos() {
    const container = document.getElementById('productos-container');
    container.innerHTML = '';

    const productosFiltrados = filtroActual === 'todos'
        ? todosLosProductos
        : todosLosProductos.filter(p => p.categoria === filtroActual);

    if (productosFiltrados.length === 0) {
        container.innerHTML = '<p class="cargando">No hay productos en esta categoría.</p>';
        return;
    }

    productosFiltrados.forEach(p => {
        const btn = document.createElement('button');
        btn.className = 'btn-producto';

        if (p.stock <= 0) {
            btn.disabled = true;
            btn.innerHTML = `<span>${p.nombre}</span><span class="stock">SIN STOCK</span>`;
        } else {
            btn.innerHTML = `<span>${p.nombre} - $${p.precio}</span><span class="stock">Stock: ${p.stock}</span>`;
            btn.onclick = () => agregarAlCarrito(p.id);
        }
        container.appendChild(btn);
    });
}

function filtrar(categoria) {
    filtroActual = categoria;
    renderizarProductos();
    document.querySelectorAll('.btn-filtro').forEach(b => {
        b.classList.remove('activo');
        if (b.textContent.toLowerCase().includes(categoria) || (categoria === 'todos' && b.textContent === 'Todos')) {
            b.classList.add('activo');
        }
    });
}

function agregarAlCarrito(productoId) {
    const producto = todosLosProductos.find(p => p.id === productoId);
    const itemEnCarrito = carrito.find(c => c.id === productoId);
    const cantidadActual = itemEnCarrito ? itemEnCarrito.cantidad : 0;

    if (cantidadActual >= producto.stock) {
        mostrarToast(`⚠️ Stock máximo alcanzado`, 'error');
        return;
    }

    if (itemEnCarrito) {
        itemEnCarrito.cantidad++;
    } else {
        carrito.push({ id: producto.id, nombre: producto.nombre, precio: producto.precio, cantidad: 1 });
    }

    mostrarToast(`✅ ${producto.nombre} agregado`, 'success');
    renderizarCarrito();
}

function cambiarCantidad(index, delta) {
    const item = carrito[index];
    const productoReal = todosLosProductos.find(p => p.id === item.id);

    if (delta > 0 && item.cantidad >= productoReal.stock) {
        mostrarToast(`⚠️ Stock máximo alcanzado`, 'error');
        return;
    }

    item.cantidad += delta;
    if (item.cantidad <= 0) {
        carrito.splice(index, 1);
    }
    renderizarCarrito();
}

function renderizarCarrito() {
    const lista = document.getElementById('lista-carrito');
    lista.innerHTML = '';
    let total = 0;

    if (carrito.length === 0) {
        lista.innerHTML = '<li class="vacio">No hay productos agregados.</li>';
        document.getElementById('total-pedido').innerText = '0';
        return;
    }

    carrito.forEach((item, index) => {
        const subtotal = item.precio * item.cantidad;
        total += subtotal;

        const li = document.createElement('li');
        li.className = 'item-carrito';
        li.innerHTML = `
            <div class="info-item">
                <span class="nombre-item">${item.nombre}</span>
                <span class="precio-item">$${subtotal}</span>
            </div>
            <div class="controles">
                <button class="btn-control" onclick="cambiarCantidad(${index}, -1)">-</button>
                <span class="cantidad">${item.cantidad}</span>
                <button class="btn-control" onclick="cambiarCantidad(${index}, 1)">+</button>
            </div>
        `;
        lista.appendChild(li);
    });

    document.getElementById('total-pedido').innerText = total.toLocaleString('es-AR');
}

// ===== FUNCIÓN NUEVA: Enviar WhatsApp =====
function enviarWhatsApp() {
    const productosTexto = carrito.map(item => 
        `${item.cantidad}x ${item.nombre}`
    ).join(', ');
    
    const total = document.getElementById('total-pedido').innerText;
    const hora = new Date().toLocaleString('es-AR');
    
    const mensaje = `🍔 *NUEVO PEDIDO - EL BUEN SABOR*%0A%0A` +
                   `📦 *Productos:*%0A${productosTexto}%0A%0A` +
                   `💰 *Total:* $${total}%0A%0A` +
                   `⏰ *Hora:* ${hora}`;
    
    window.open(`https://wa.me/${TELEFONO_DUEÑO}?text=${mensaje}`, '_blank');
}

// Confirmar pedido con WhatsApp
document.getElementById('btn-confirmar').addEventListener('click', async () => {
    if (carrito.length === 0) {
        mostrarToast("⚠️ El pedido está vacío", 'error');
        return;
    }

    const total = document.getElementById('total-pedido').innerText;

    try {
        const respuesta = await fetch('/api/pedidos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ items: carrito, total: total })
        });

        const resultado = await respuesta.json();

        if (resultado.success) {
            mostrarToast(`✅ Pedido confirmado: $${total}`, 'success');
            
            // Abrir WhatsApp después de 1 segundo
            setTimeout(() => {
                enviarWhatsApp();
            }, 1000);
            
            carrito = [];
            renderizarCarrito();
            await cargarProductos();
        } else {
            mostrarToast(`❌ ${resultado.error}`, 'error');
        }
    } catch (error) {
        mostrarToast('❌ Error de conexión con el backend', 'error');
    }
});

function mostrarToast(mensaje, tipo = 'success') {
    const toast = document.getElementById('toast');
    toast.innerText = mensaje;
    toast.className = `toast show ${tipo}`;
    setTimeout(() => { toast.className = toast.className.replace('show', ''); }, 2500);
}

// Historial de pedidos
if (document.getElementById('lista-pedidos')) {
    cargarHistorial();
}

async function cargarHistorial() {
    const container = document.getElementById('lista-pedidos');
    
    try {
        const respuesta = await fetch('/api/historial');
        const pedidos = await respuesta.json();
        container.innerHTML = '';

        if (pedidos.length === 0) {
            container.innerHTML = '<p class="cargando">No hay pedidos registrados aún.</p>';
            return;
        }

        pedidos.forEach(p => {
            const card = document.createElement('div');
            card.className = 'pedido-card';
            
            const fecha = new Date(p.fecha).toLocaleString('es-AR', { 
                day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' 
            });

            card.innerHTML = `
                <div class="pedido-header">
                    <span class="pedido-id">Pedido #${p.id}</span>
                    <span class="pedido-fecha">${fecha} hs</span>
                </div>
                <div class="pedido-detalles">${p.detalles}</div>
                <div class="pedido-total">Total: $${p.total.toLocaleString('es-AR')}</div>
            `;
            container.appendChild(card);
        });
    } catch (error) {
        console.error(error);
        container.innerHTML = '<p class="cargando">Error al conectar con el servidor.</p>';
    }
}