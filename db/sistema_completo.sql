CREATE DATABASE IF NOT EXISTS db_mantenimiento CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE db_mantenimiento;

CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(255),
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    cedula VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    direccion TEXT,
    password_hash VARCHAR(255) NOT NULL,
    tipo ENUM('cliente', 'empleado') NOT NULL DEFAULT 'cliente',
    foto_perfil VARCHAR(255) DEFAULT 'default.png',
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE usuario_rol (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    rol_id INT NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (rol_id) REFERENCES roles(id) ON DELETE CASCADE,
    UNIQUE KEY unique_usuario_rol (usuario_id, rol_id)
);

CREATE TABLE permisos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rol_id INT NOT NULL,
    modulo VARCHAR(100) NOT NULL,
    crear TINYINT(1) DEFAULT 0,
    leer TINYINT(1) DEFAULT 0,
    actualizar TINYINT(1) DEFAULT 0,
    eliminar TINYINT(1) DEFAULT 0,
    FOREIGN KEY (rol_id) REFERENCES roles(id) ON DELETE CASCADE,
    UNIQUE KEY unique_rol_modulo (rol_id, modulo)
);

CREATE TABLE bitacora (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    accion VARCHAR(50) NOT NULL,
    modulo VARCHAR(100) NOT NULL,
    descripcion TEXT,
    ip VARCHAR(45),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE tokens_recuperacion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    token VARCHAR(255) NOT NULL,
    expira DATETIME NOT NULL,
    usado TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

DELIMITER //
CREATE FUNCTION fn_verificar_credenciales(p_email VARCHAR(150), p_password VARCHAR(255))
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE v_id INT DEFAULT 0;
    SELECT id INTO v_id FROM usuarios WHERE email = p_email AND estado = 1 LIMIT 1;
    RETURN v_id;
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER trg_bitacora_usuario_insert
AFTER INSERT ON usuarios
FOR EACH ROW
BEGIN
    INSERT INTO bitacora (usuario_id, accion, modulo, descripcion, ip)
    VALUES (NEW.id, 'CREAR', 'USUARIOS', CONCAT('Usuario creado: ', NEW.nombre, ' ', NEW.apellido), '127.0.0.1');
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER trg_bitacora_usuario_update
AFTER UPDATE ON usuarios
FOR EACH ROW
BEGIN
    INSERT INTO bitacora (usuario_id, accion, modulo, descripcion, ip)
    VALUES (NEW.id, 'MODIFICAR', 'USUARIOS', CONCAT('Usuario modificado: ', NEW.nombre, ' ', NEW.apellido), '127.0.0.1');
END //
DELIMITER ;

DELIMITER //
CREATE PROCEDURE sp_crear_usuario(
    IN p_nombre VARCHAR(100),
    IN p_apellido VARCHAR(100),
    IN p_cedula VARCHAR(20),
    IN p_email VARCHAR(150),
    IN p_telefono VARCHAR(20),
    IN p_direccion TEXT,
    IN p_password VARCHAR(255),
    IN p_tipo ENUM('cliente', 'empleado')
)
BEGIN
    INSERT INTO usuarios (nombre, apellido, cedula, email, telefono, direccion, password_hash, tipo)
    VALUES (p_nombre, p_apellido, p_cedula, p_email, p_telefono, p_direccion, p_password, p_tipo);
END //
DELIMITER ;

INSERT INTO roles (nombre, descripcion) VALUES ('Administrador', 'Acceso total al sistema');
INSERT INTO roles (nombre, descripcion) VALUES ('Vendedor', 'Acceso a ventas e inventario');
INSERT INTO roles (nombre, descripcion) VALUES ('Cliente', 'Acceso al portal de compras');

INSERT INTO usuarios (nombre, apellido, cedula, email, telefono, direccion, password_hash, tipo)
VALUES ('Admin', 'Sistema', 'V-00000000', 'admin@transalca.com', '0424-0000000', 'Oficina Principal',
'scrypt:32768:8:1$NP7iU10YgSPJPmAh$a2320143ce75e7daa2bf829c27fde8a333c63b4f7b39ebd454d526818ae66be465d09334da3fd829335a11f6a7ff2ef3281c89929f965754d79d22a5f74d8f37', 'empleado');

INSERT INTO usuario_rol (usuario_id, rol_id) VALUES (1, 1);

INSERT INTO permisos (rol_id, modulo, crear, leer, actualizar, eliminar) VALUES
(1, 'usuarios', 1, 1, 1, 1),
(1, 'roles', 1, 1, 1, 1),
(1, 'productos', 1, 1, 1, 1),
(1, 'categorias', 1, 1, 1, 1),
(1, 'marcas', 1, 1, 1, 1),
(1, 'proveedores', 1, 1, 1, 1),
(1, 'mecanicos', 1, 1, 1, 1),
(1, 'inventario', 1, 1, 1, 1),
(1, 'servicios', 1, 1, 1, 1),
(1, 'promociones', 1, 1, 1, 1),
(1, 'ordenes', 1, 1, 1, 1),
(1, 'pagos', 1, 1, 1, 1),
(1, 'bitacora', 0, 1, 0, 0),
(1, 'reportes', 0, 1, 0, 0),
(1, 'respaldos', 1, 1, 0, 0),
(1, 'qr', 1, 1, 1, 1),
(1, 'sucursales', 1, 1, 1, 1),
(2, 'productos', 0, 1, 0, 0),
(2, 'categorias', 0, 1, 0, 0),
(2, 'marcas', 0, 1, 0, 0),
(2, 'inventario', 0, 1, 1, 0),
(2, 'servicios', 0, 1, 1, 0),
(2, 'ordenes', 1, 1, 1, 0),
(2, 'pagos', 0, 1, 1, 0),
(2, 'reportes', 0, 1, 0, 0);

CREATE DATABASE IF NOT EXISTS db_transalca CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE db_transalca;

CREATE TABLE sucursales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    direccion TEXT,
    telefono VARCHAR(20),
    email VARCHAR(150),
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categorias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    imagen VARCHAR(255) DEFAULT 'default_cat.png',
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE marcas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    logo VARCHAR(255) DEFAULT 'default_brand.png',
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE productos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    categoria_id INT,
    marca_id INT,
    sucursal_id INT,
    imagen VARCHAR(255) DEFAULT 'default_product.png',
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE SET NULL,
    FOREIGN KEY (marca_id) REFERENCES marcas(id) ON DELETE SET NULL,
    FOREIGN KEY (sucursal_id) REFERENCES sucursales(id) ON DELETE SET NULL
);

CREATE TABLE proveedores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    rif VARCHAR(20) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    email VARCHAR(150),
    direccion TEXT,
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE inventario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    producto_id INT NOT NULL,
    sucursal_id INT,
    stock INT DEFAULT 0,
    stock_minimo INT DEFAULT 5,
    ubicacion VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE,
    FOREIGN KEY (sucursal_id) REFERENCES sucursales(id) ON DELETE SET NULL,
    UNIQUE KEY unique_producto_sucursal (producto_id, sucursal_id)
);

CREATE TABLE ordenes_compra (
    id INT AUTO_INCREMENT PRIMARY KEY,
    proveedor_id INT NOT NULL,
    usuario_id INT NOT NULL,
    sucursal_id INT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(12,2) DEFAULT 0.00,
    estado ENUM('pendiente', 'recibida', 'cancelada') DEFAULT 'pendiente',
    observaciones TEXT,
    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id),
    FOREIGN KEY (sucursal_id) REFERENCES sucursales(id) ON DELETE SET NULL
);

CREATE TABLE detalle_orden_compra (
    id INT AUTO_INCREMENT PRIMARY KEY,
    orden_id INT NOT NULL,
    producto_id INT NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (orden_id) REFERENCES ordenes_compra(id) ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

CREATE TABLE ordenes_venta (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT NOT NULL,
    sucursal_id INT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(12,2) DEFAULT 0.00,
    estado ENUM('pendiente', 'aprobada', 'rechazada', 'entregada', 'cancelada') DEFAULT 'pendiente',
    metodo_pago VARCHAR(50),
    comprobante_url VARCHAR(255),
    observaciones TEXT,
    FOREIGN KEY (sucursal_id) REFERENCES sucursales(id) ON DELETE SET NULL
);

CREATE TABLE detalle_orden_venta (
    id INT AUTO_INCREMENT PRIMARY KEY,
    orden_id INT NOT NULL,
    producto_id INT,
    servicio_id INT,
    tipo ENUM('producto', 'servicio') DEFAULT 'producto',
    cantidad INT NOT NULL DEFAULT 1,
    precio_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (orden_id) REFERENCES ordenes_venta(id) ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

CREATE TABLE servicios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    duracion_estimada VARCHAR(50),
    sucursal_id INT,
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sucursal_id) REFERENCES sucursales(id) ON DELETE SET NULL
);

ALTER TABLE detalle_orden_venta
ADD CONSTRAINT fk_detalle_orden_venta_servicio
FOREIGN KEY (servicio_id) REFERENCES servicios(id) ON DELETE SET NULL;

CREATE TABLE mecanicos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    cedula VARCHAR(20) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    especialidad VARCHAR(200),
    foto_perfil VARCHAR(255) DEFAULT 'default.png',
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE servicio_mecanico (
    id INT AUTO_INCREMENT PRIMARY KEY,
    servicio_id INT NOT NULL,
    mecanico_id INT,
    orden_venta_id INT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado ENUM('asignado', 'en_proceso', 'completado', 'cancelado') DEFAULT 'asignado',
    observaciones TEXT,
    FOREIGN KEY (servicio_id) REFERENCES servicios(id),
    FOREIGN KEY (mecanico_id) REFERENCES mecanicos(id),
    FOREIGN KEY (orden_venta_id) REFERENCES ordenes_venta(id)
);

CREATE TABLE promociones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    tipo ENUM('puntos', 'descuento', 'gratis') DEFAULT 'puntos',
    puntos_requeridos INT DEFAULT 3,
    recompensa VARCHAR(255),
    imagen_tarjeta VARCHAR(255) DEFAULT 'default_card.png',
    estado TINYINT(1) DEFAULT 1,
    fecha_inicio DATE,
    fecha_fin DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tarjeta_fidelidad (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT NOT NULL,
    promocion_id INT NOT NULL,
    puntos_acumulados INT DEFAULT 0,
    canjeada TINYINT(1) DEFAULT 0,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (promocion_id) REFERENCES promociones(id)
);

CREATE TABLE historial_puntos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tarjeta_id INT NOT NULL,
    puntos INT NOT NULL,
    tipo ENUM('suma', 'resta', 'canje') DEFAULT 'suma',
    descripcion VARCHAR(255),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tarjeta_id) REFERENCES tarjeta_fidelidad(id) ON DELETE CASCADE
);

CREATE TABLE qr_codes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    tipo ENUM('promocion', 'servicio', 'info', 'pago') DEFAULT 'info',
    contenido TEXT,
    utilidad VARCHAR(255),
    estado TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE comprobantes_pago (
    id INT AUTO_INCREMENT PRIMARY KEY,
    orden_venta_id INT NOT NULL,
    imagen_url VARCHAR(255) NOT NULL,
    estado ENUM('pendiente', 'aprobado', 'rechazado') DEFAULT 'pendiente',
    revisado_por INT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    observaciones TEXT,
    FOREIGN KEY (orden_venta_id) REFERENCES ordenes_venta(id) ON DELETE CASCADE
);

CREATE TABLE carrito (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT NOT NULL,
    producto_id INT,
    servicio_id INT,
    tipo ENUM('producto', 'servicio') DEFAULT 'producto',
    cantidad INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE
);

CREATE TABLE configuracion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    clave VARCHAR(100) UNIQUE NOT NULL,
    valor TEXT
);

DELIMITER //
CREATE TRIGGER trg_stock_compra_recibida
AFTER INSERT ON detalle_orden_compra
FOR EACH ROW
BEGIN
    DECLARE v_suc INT;
    SELECT sucursal_id INTO v_suc FROM ordenes_compra WHERE id = NEW.orden_id LIMIT 1;
    IF EXISTS (SELECT 1 FROM inventario WHERE producto_id = NEW.producto_id AND (sucursal_id = v_suc OR (sucursal_id IS NULL AND v_suc IS NULL))) THEN
        UPDATE inventario SET stock = stock + NEW.cantidad WHERE producto_id = NEW.producto_id AND (sucursal_id = v_suc OR (sucursal_id IS NULL AND v_suc IS NULL));
    ELSE
        INSERT INTO inventario (producto_id, sucursal_id, stock) VALUES (NEW.producto_id, v_suc, NEW.cantidad);
    END IF;
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER trg_stock_venta_aprobada
AFTER INSERT ON detalle_orden_venta
FOR EACH ROW
BEGIN
    DECLARE v_suc INT;
    IF NEW.tipo = 'producto' AND NEW.producto_id IS NOT NULL THEN
        SELECT sucursal_id INTO v_suc FROM ordenes_venta WHERE id = NEW.orden_id LIMIT 1;
        UPDATE inventario SET stock = stock - NEW.cantidad WHERE producto_id = NEW.producto_id AND (sucursal_id = v_suc OR (sucursal_id IS NULL AND v_suc IS NULL));
    END IF;
END //
DELIMITER ;

DELIMITER //
CREATE FUNCTION fn_stock_disponible(p_producto_id INT, p_sucursal_id INT)
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE v_stock INT DEFAULT 0;
    IF p_sucursal_id IS NULL THEN
        SELECT COALESCE(SUM(stock), 0) INTO v_stock FROM inventario WHERE producto_id = p_producto_id;
    ELSE
        SELECT COALESCE(stock, 0) INTO v_stock FROM inventario WHERE producto_id = p_producto_id AND sucursal_id = p_sucursal_id;
    END IF;
    RETURN v_stock;
END //
DELIMITER ;

DELIMITER //
CREATE FUNCTION fn_calcular_total_orden(p_orden_id INT, p_tipo VARCHAR(10))
RETURNS DECIMAL(12,2)
DETERMINISTIC
BEGIN
    DECLARE v_total DECIMAL(12,2) DEFAULT 0.00;
    IF p_tipo = 'compra' THEN
        SELECT COALESCE(SUM(subtotal), 0) INTO v_total FROM detalle_orden_compra WHERE orden_id = p_orden_id;
    ELSE
        SELECT COALESCE(SUM(subtotal), 0) INTO v_total FROM detalle_orden_venta WHERE orden_id = p_orden_id;
    END IF;
    RETURN v_total;
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER trg_auto_canje_tarjeta
BEFORE UPDATE ON tarjeta_fidelidad
FOR EACH ROW
BEGIN
    DECLARE v_puntos_req INT DEFAULT 0;
    IF NEW.canjeada = 0 THEN
        SELECT puntos_requeridos INTO v_puntos_req FROM promociones WHERE id = NEW.promocion_id LIMIT 1;
        IF NEW.puntos_acumulados >= v_puntos_req THEN
            SET NEW.canjeada = 1;
        END IF;
    END IF;
END //
DELIMITER ;

INSERT INTO sucursales (nombre, direccion, telefono, email) VALUES
('Sede Principal', 'Av. Principal, Local 1', '0424-0000000', 'principal@transalca.com'),
('Sucursal Norte', 'Calle Norte, Centro Comercial X', '0424-1111111', 'norte@transalca.com');

INSERT INTO categorias (nombre, descripcion) VALUES
('Cauchos', 'Neumaticos para todo tipo de vehiculos'),
('Lubricantes', 'Aceites y lubricantes para motor y transmision'),
('Repuestos', 'Repuestos y autopartes en general'),
('Filtros', 'Filtros de aire, aceite y combustible'),
('Frenos', 'Pastillas, discos y sistemas de frenos'),
('Baterias', 'Baterias para vehiculos');

INSERT INTO marcas (nombre, descripcion) VALUES
('Pirelli', 'Neumaticos premium italianos'),
('Michelin', 'Neumaticos franceses de alta calidad'),
('Firestone', 'Neumaticos americanos'),
('Mobil', 'Lubricantes de alta gama'),
('Castrol', 'Lubricantes y aceites'),
('Shell', 'Lubricantes Shell Helix');

INSERT INTO servicios (nombre, descripcion, precio, duracion_estimada, sucursal_id) VALUES
('Alineacion', 'Alineacion computarizada de ruedas', 15.00, '30 min', 1),
('Balanceo', 'Balanceo dinamico de ruedas', 10.00, '20 min', 1),
('Rotacion de cauchos', 'Rotacion de 4 cauchos', 8.00, '25 min', 1),
('Cambio de aceite', 'Cambio de aceite de motor', 12.00, '30 min', 1),
('Cambio de frenos', 'Cambio de pastillas de freno', 25.00, '45 min', 2),
('Revision general', 'Revision completa del vehiculo', 20.00, '60 min', 2);

INSERT INTO configuracion (clave, valor) VALUES
('nombre_empresa', 'Transalca C.A.'),
('rif_empresa', 'J-00000000-0'),
('telefono_empresa', '0424-0000000'),
('direccion_empresa', 'Direccion Principal'),
('email_empresa', 'info@transalca.com'),
('moneda', 'USD');

