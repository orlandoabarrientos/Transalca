SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT;
SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS;
SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION;
SET NAMES utf8mb4;

DELIMITER $$

CREATE DEFINER=`root`@`localhost` FUNCTION `fn_calcular_total_orden` (`p_orden_id` INT, `p_tipo` VARCHAR(10)) RETURNS DECIMAL(12,2) DETERMINISTIC BEGIN
    DECLARE v_total DECIMAL(12,2) DEFAULT 0.00;
    SELECT COALESCE((SELECT SUM(subtotal) FROM detalle_orden_venta_productos WHERE orden_id = p_orden_id),0)
         + COALESCE((SELECT SUM(subtotal) FROM detalle_orden_venta_servicios WHERE orden_id = p_orden_id),0)
    INTO v_total;
    RETURN v_total;
END$$

CREATE DEFINER=`root`@`localhost` FUNCTION `fn_stock_disponible` (`p_producto_codigo` VARCHAR(50), `p_sucursal_id` INT) RETURNS INT(11) DETERMINISTIC BEGIN
            DECLARE v_stock INT DEFAULT 0;
            IF p_sucursal_id IS NULL THEN
                SELECT COALESCE(SUM(stock), 0) INTO v_stock FROM stock WHERE producto_codigo = p_producto_codigo;
            ELSE
                SELECT COALESCE(stock, 0) INTO v_stock FROM stock WHERE producto_codigo = p_producto_codigo AND sucursal_id = p_sucursal_id;
            END IF;
            RETURN v_stock;
        END$$

DELIMITER ;

CREATE TABLE `bitacora_vehiculo` (
  `id` int(11) NOT NULL,
  `tipo_registro` varchar(30) DEFAULT 'servicio',
  `descripcion` text DEFAULT NULL,
  `kilometraje` int(11) DEFAULT NULL,
  `aceite_usado` varchar(200) DEFAULT NULL,
  `filtros_usados` text DEFAULT NULL,
  `refrigerante_usado` varchar(200) DEFAULT NULL,
  `cauchos_info` text DEFAULT NULL,
  `precio_servicio` decimal(10,2) DEFAULT 0.00,
  `precio_productos` decimal(10,2) DEFAULT 0.00,
  `proximo_mantenimiento` text DEFAULT NULL,
  `modo_registro` varchar(20) DEFAULT 'manual',
  `observaciones` text DEFAULT NULL,
  `fecha` timestamp NOT NULL DEFAULT current_timestamp(),
  `vehiculo_placa` varchar(20) NOT NULL,
  `servicio_mecanico_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `carrito` (
  `id` int(11) NOT NULL,
  `cliente_cedula` varchar(20) NOT NULL,
  `producto_codigo` varchar(50) DEFAULT NULL,
  `servicio_id` int(11) DEFAULT NULL,
  `tipo` varchar(20) NOT NULL DEFAULT 'producto',
  `cantidad` int(11) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `categorias` (
  `nombre` varchar(150) NOT NULL,
  `descripcion` varchar(500) DEFAULT NULL,
  `imagen` varchar(200) DEFAULT 'default_cat.png',
  `estado` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO `categorias` (`nombre`, `descripcion`, `imagen`, `estado`, `created_at`) VALUES
('Baterias', 'Baterias para vehiculos', 'default_cat.png', 1, '2026-04-30 04:18:56'),
('Cat afahcceddi', 'Prueba', 'default_cat.png', 0, '2026-05-08 02:43:38'),
('Cauchos', 'Neumaticos para todo tipo de vehiculos', 'default_cat.png', 1, '2026-04-30 04:18:56'),
('Combos', 'Combos de aceite, filtro y servicio', 'default_cat.png', 1, '2026-05-28 02:32:34'),
('Filtros', 'Filtros de aire, aceite y combustible', 'default_cat.png', 1, '2026-04-30 04:18:56'),
('Frenos', 'Pastillas, discos y sistemas de frenos', 'default_cat.png', 1, '2026-04-30 04:18:56'),
('Lubricantes', 'Aceites y lubricantes para motor y transmision', 'default_cat.png', 1, '2026-04-30 04:18:56'),
('Repuestos', 'Repuestos y autopartes en general', 'default_cat.png', 1, '2026-04-30 04:18:56'),
('TestCat0507224100', 'Prueba', 'default_cat.png', 0, '2026-05-08 02:41:00');

CREATE TABLE `clientes` (
  `cedula` varchar(20) NOT NULL,
  `cedula_prefijo` varchar(2) DEFAULT NULL,
  `tipo_cliente` varchar(20) NOT NULL DEFAULT 'persona',
  `nombre` varchar(100) NOT NULL,
  `apellido` varchar(100) NOT NULL,
  `telefono` varchar(20) NOT NULL,
  `email` varchar(150) DEFAULT NULL,
  `direccion` varchar(300) DEFAULT NULL,
  `estado` tinyint(1) DEFAULT 1,
  `origen_registro` varchar(20) DEFAULT 'cliente',
  `usuario_id` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO `clientes` (`cedula`, `cedula_prefijo`, `tipo_cliente`, `nombre`, `apellido`, `telefono`, `email`, `direccion`, `estado`, `origen_registro`, `usuario_id`, `created_at`, `updated_at`) VALUES
('V-00000000', 'V', 'persona', 'Admin', 'Sistema', '0424-0000000', 'admin@transalca.com', 'Oficina Principal', 1, 'cliente', NULL, '2026-05-18 04:29:47', '2026-05-28 06:14:49');


CREATE TABLE `comisiones_mecanico` (
  `id` int(11) NOT NULL,
  `servicio_mecanico_id` int(11) NOT NULL,
  `precio_servicio` decimal(10,2) NOT NULL,
  `porcentaje_comision` decimal(5,2) DEFAULT 30.00,
  `monto_comision` decimal(10,2) NOT NULL,
  `estado_pago` varchar(20) DEFAULT 'pendiente',
  `fecha_pago` date DEFAULT NULL,
  `fecha` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `comprobantes_pago` (
  `id` int(11) NOT NULL,
  `orden_venta_id` int(11) NOT NULL,
  `imagen_url` varchar(255) NOT NULL,
  `estado` varchar(30) NOT NULL DEFAULT 'pendiente',
  `revisado_por` varchar(20) DEFAULT NULL,
  `fecha` timestamp NOT NULL DEFAULT current_timestamp(),
  `observaciones` varchar(1000) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `configuracion` (
  `clave` varchar(100) NOT NULL,
  `valor` varchar(500) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `consumo_combustible` (
  `id` int(11) NOT NULL,
  `modo` varchar(20) DEFAULT 'manual',
  `consumo_estimado_lkm` decimal(6,2) DEFAULT NULL,
  `fuente_dato` varchar(500) DEFAULT NULL,
  `km_recorridos` int(11) DEFAULT NULL,
  `litros_consumidos` decimal(8,2) DEFAULT NULL,
  `precio_litro` decimal(10,2) DEFAULT NULL,
  `fecha` date DEFAULT NULL,
  `observaciones` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `vehiculo_placa` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `cotizaciones` (
  `id` int(11) NOT NULL,
  `cliente_cedula` varchar(20) NOT NULL,
  `tasa_cambio_id` int(11) DEFAULT NULL,
  `tasa_usada` decimal(12,4) NOT NULL,
  `tipo_tasa` varchar(20) NOT NULL,
  `total_usd` decimal(12,2) NOT NULL,
  `total_bs` decimal(14,2) NOT NULL,
  `vigente_hasta` datetime NOT NULL,
  `estado` varchar(20) DEFAULT 'vigente',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `cotizacion_items` (
  `id` int(11) NOT NULL,
  `cotizacion_id` int(11) NOT NULL,
  `producto_codigo` varchar(50) DEFAULT NULL,
  `servicio_id` int(11) DEFAULT NULL,
  `tipo` varchar(20) NOT NULL DEFAULT 'producto',
  `cantidad` int(11) DEFAULT 1,
  `precio_usd` decimal(10,2) NOT NULL,
  `precio_bs` decimal(12,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `detalle_orden_compra` (
  `id` int(11) NOT NULL,
  `orden_compra_id` int(11) NOT NULL,
  `producto_codigo` varchar(50) NOT NULL,
  `cantidad` int(11) NOT NULL DEFAULT 1,
  `precio_unitario` decimal(10,2) NOT NULL,
  `subtotal` decimal(12,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


CREATE TABLE `detalle_orden_venta_productos` (
  `id` int(11) NOT NULL,
  `orden_id` int(11) NOT NULL,
  `producto_codigo` varchar(50) NOT NULL,
  `cantidad` int(11) NOT NULL DEFAULT 1,
  `precio_unitario` decimal(10,2) NOT NULL,
  `subtotal` decimal(12,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

DELIMITER $$
CREATE TRIGGER `trg_stock_venta_aprobada` AFTER INSERT ON `detalle_orden_venta_productos` FOR EACH ROW BEGIN
    DECLARE v_suc INT;
    SELECT sucursal_id INTO v_suc FROM ordenes_venta WHERE id = NEW.orden_id LIMIT 1;
    UPDATE stock SET stock = stock - NEW.cantidad
    WHERE producto_codigo = NEW.producto_codigo AND sucursal_id = v_suc;
END
$$
DELIMITER ;

CREATE TABLE `detalle_orden_venta_servicios` (
  `id` int(11) NOT NULL,
  `orden_id` int(11) NOT NULL,
  `servicio_id` int(11) NOT NULL,
  `cantidad` int(11) NOT NULL DEFAULT 1,
  `precio_unitario` decimal(10,2) NOT NULL,
  `subtotal` decimal(12,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `empresas` (
  `cliente_cedula` varchar(20) NOT NULL,
  `rif` varchar(20) NOT NULL,
  `rif_prefijo` varchar(2) DEFAULT NULL,
  `razon_social` varchar(200) NOT NULL,
  `nombre_comercial` varchar(200) DEFAULT NULL,
  `representante_nombre` varchar(150) DEFAULT NULL,
  `representante_cedula_prefijo` varchar(2) DEFAULT NULL,
  `representante_cedula` varchar(20) DEFAULT NULL,
  `representante_telefono` varchar(20) DEFAULT NULL,
  `representante_email` varchar(150) DEFAULT NULL,
  `sector` varchar(150) DEFAULT NULL,
  `limite_credito` decimal(10,2) DEFAULT 0.00,
  `dias_credito` int(11) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `historial_puntos` (
  `id` int(11) NOT NULL,
  `tarjeta_id` int(11) NOT NULL,
  `puntos` int(11) NOT NULL,
  `tipo` varchar(30) NOT NULL DEFAULT 'suma',
  `descripcion` varchar(150) DEFAULT NULL,
  `fecha` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `mantenimientos_programados` (
  `id` int(11) NOT NULL,
  `regla_id` int(11) DEFAULT NULL,
  `tipo_mantenimiento` varchar(100) NOT NULL,
  `modo` varchar(20) DEFAULT 'manual',
  `km_proximo` int(11) DEFAULT NULL,
  `fecha_proxima` date DEFAULT NULL,
  `km_realizado` int(11) DEFAULT NULL,
  `fecha_realizado` date DEFAULT NULL,
  `estado` varchar(20) DEFAULT 'pendiente',
  `registrado_por` varchar(20) DEFAULT NULL,
  `observaciones` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `vehiculo_placa` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `marcas` (
  `nombre` varchar(150) NOT NULL,
  `descripcion` varchar(500) DEFAULT NULL,
  `logo` varchar(200) DEFAULT 'default_brand.png',
  `estado` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO `marcas` (`nombre`, `descripcion`, `logo`, `estado`, `created_at`) VALUES
('15W40 / 20W50 SEMI SINTETICO FC GARRAFA', 'Marca importada del catalogo real: 15W40 / 20W50 SEMI SINTETICO FC GARRAFA', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('15W40 SEMI SINTETICO VALVOLINE GARRAFA', 'Marca importada del catalogo real: 15W40 SEMI SINTETICO VALVOLINE GARRAFA', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('7.00R15 KOBATA', 'Marca importada del catalogo real: 7.00R15 KOBATA', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACDelco', 'Baterias y repuestos automotrices', 'default_brand.png', 1, '2026-05-27 14:10:55'),
('ACEITE 10W30 SEMI SINTETICO GULF', 'Marca importada del catalogo real: ACEITE 10W30 SEMI SINTETICO GULF', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 10W40 SEMI SINTETICO MOBIL', 'Marca importada del catalogo real: ACEITE 10W40 SEMI SINTETICO MOBIL', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 15W40 MINERAL FC', 'Marca importada del catalogo real: ACEITE 15W40 MINERAL FC', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 15W40 MINERAL GULF', 'Marca importada del catalogo real: ACEITE 15W40 MINERAL GULF', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 15W40 MINERAL INCA', 'Marca importada del catalogo real: ACEITE 15W40 MINERAL INCA', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 15W40 MINERAL MEXLUB', 'Marca importada del catalogo real: ACEITE 15W40 MINERAL MEXLUB', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 15W40 MINERAL RALOY', 'Marca importada del catalogo real: ACEITE 15W40 MINERAL RALOY', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 15W40 MINERAL ROSHFRANS', 'Marca importada del catalogo real: ACEITE 15W40 MINERAL ROSHFRANS', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 15W40 MINERAL VALVOLINE', 'Marca importada del catalogo real: ACEITE 15W40 MINERAL VALVOLINE', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 15W40 SEMI SINTETICO BOSS', 'Marca importada del catalogo real: ACEITE 15W40 SEMI SINTETICO BOSS', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 15W40 SEMI SINTETICO FC', 'Marca importada del catalogo real: ACEITE 15W40 SEMI SINTETICO FC', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 15W40 SEMI SINTETICO GULF', 'Marca importada del catalogo real: ACEITE 15W40 SEMI SINTETICO GULF', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 15W40 SEMI SINTETICO INCA', 'Marca importada del catalogo real: ACEITE 15W40 SEMI SINTETICO INCA', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 15W40 SEMI SINTETICO MEXLUB', 'Marca importada del catalogo real: ACEITE 15W40 SEMI SINTETICO MEXLUB', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 15W40 SEMI SINTETICO RALOY', 'Marca importada del catalogo real: ACEITE 15W40 SEMI SINTETICO RALOY', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 15W40 SEMI SINTETICO VALVOLINE', 'Marca importada del catalogo real: ACEITE 15W40 SEMI SINTETICO VALVOLINE', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 15W40 SEMI SINTETICO WOLF', 'Marca importada del catalogo real: ACEITE 15W40 SEMI SINTETICO WOLF', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 20W50 MINERAL BOSS', 'Marca importada del catalogo real: ACEITE 20W50 MINERAL BOSS', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 20W50 MINERAL FC', 'Marca importada del catalogo real: ACEITE 20W50 MINERAL FC', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 20W50 MINERAL GULF', 'Marca importada del catalogo real: ACEITE 20W50 MINERAL GULF', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 20W50 MINERAL INCA', 'Marca importada del catalogo real: ACEITE 20W50 MINERAL INCA', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 20W50 MINERAL MEXLUB', 'Marca importada del catalogo real: ACEITE 20W50 MINERAL MEXLUB', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 20W50 MINERAL MOBIL', 'Marca importada del catalogo real: ACEITE 20W50 MINERAL MOBIL', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 20W50 MINERAL MOTUL', 'Marca importada del catalogo real: ACEITE 20W50 MINERAL MOTUL', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 20W50 MINERAL RALOY', 'Marca importada del catalogo real: ACEITE 20W50 MINERAL RALOY', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 20W50 MINERAL ROSHFRANS', 'Marca importada del catalogo real: ACEITE 20W50 MINERAL ROSHFRANS', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 20W50 MINERAL VALVOLINE', 'Marca importada del catalogo real: ACEITE 20W50 MINERAL VALVOLINE', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 20W50 SEMI SINTETICO FC', 'Marca importada del catalogo real: ACEITE 20W50 SEMI SINTETICO FC', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 20W50 SEMI SINTETICO GULF', 'Marca importada del catalogo real: ACEITE 20W50 SEMI SINTETICO GULF', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 20W50 SEMI SINTETICO INCA', 'Marca importada del catalogo real: ACEITE 20W50 SEMI SINTETICO INCA', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 20W50 SEMI SINTETICO MEXLUB', 'Marca importada del catalogo real: ACEITE 20W50 SEMI SINTETICO MEXLUB', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 20W50 SEMI SINTETICO RALOY', 'Marca importada del catalogo real: ACEITE 20W50 SEMI SINTETICO RALOY', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 20W50 SEMI SINTETICO VALVOLINE', 'Marca importada del catalogo real: ACEITE 20W50 SEMI SINTETICO VALVOLINE', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 5W20 SINTETICO GULF', 'Marca importada del catalogo real: ACEITE 5W20 SINTETICO GULF', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 5W30 SINTETICO GULF', 'Marca importada del catalogo real: ACEITE 5W30 SINTETICO GULF', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ACEITE 5W40 SINTETICO GUL', 'Marca importada del catalogo real: ACEITE 5W40 SINTETICO GUL', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('AKRON', 'Marca importada del catalogo real: AKRON', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ALIX IMPACT AT PLUS', 'Marca importada del catalogo real: ALIX IMPACT AT PLUS', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ALIX IMPACT HT', 'Marca importada del catalogo real: ALIX IMPACT HT', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ALIX IMPACT HT PLUS', 'Marca importada del catalogo real: ALIX IMPACT HT PLUS', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ALIX VELOCE', 'Marca importada del catalogo real: ALIX VELOCE', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ALIX VEZETTA', 'Marca importada del catalogo real: ALIX VEZETTA', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ALIX VEZETTA PLUS', 'Marca importada del catalogo real: ALIX VEZETTA PLUS', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('AMBERSTONE MIXTO', 'Marca importada del catalogo real: AMBERSTONE MIXTO', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ANCHEE', 'Marca importada del catalogo real: ANCHEE', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ANCHEE MT', 'Marca importada del catalogo real: ANCHEE MT', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ANNAITE', 'Marca importada del catalogo real: ANNAITE', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ANNAITE DIRECCIONAL 14PR', 'Marca importada del catalogo real: ANNAITE DIRECCIONAL 14PR', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('AOQISHI A/T', 'Marca importada del catalogo real: AOQISHI A/T', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('AOQISHI MARVEL M/T', 'Marca importada del catalogo real: AOQISHI MARVEL M/T', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ARMAX', 'Marca importada del catalogo real: ARMAX', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ARO 24 - 1100', 'Marca importada del catalogo real: ARO 24 - 1100', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ARO 24R - 1100', 'Marca importada del catalogo real: ARO 24R - 1100', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ARO 315-1100 (TORNILLO)', 'Marca importada del catalogo real: ARO 315-1100 (TORNILLO)', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ARO 42-900 (42MR)', 'Marca importada del catalogo real: ARO 42-900 (42MR)', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ARO 42R-900 (42M)', 'Marca importada del catalogo real: ARO 42R-900 (42M)', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ARO 99R-700', 'Marca importada del catalogo real: ARO 99R-700', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ATLANTIC OIL', 'Marca importada del catalogo real: ATLANTIC OIL', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('BITOIL', 'Marca importada del catalogo real: BITOIL', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('Bosch', 'Filtros, frenos y componentes automotrices', 'default_brand.png', 1, '2026-05-27 14:10:55'),
('BOSS', 'Marca importada del catalogo real: BOSS', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('BRAVA', 'Marca importada del catalogo real: BRAVA', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('Castrol', 'Lubricantes y aceites', 'default_brand.png', 1, '2026-04-30 04:18:56'),
('CHENSHANG', 'Marca importada del catalogo real: CHENSHANG', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('CROSSLEADER WILDTIGER MT', 'Marca importada del catalogo real: CROSSLEADER WILDTIGER MT', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('DAUER', 'Marca importada del catalogo real: DAUER', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('DOUBLEKING', 'Marca importada del catalogo real: DOUBLEKING', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('DOUBLEKING DK306', 'Marca importada del catalogo real: DOUBLEKING DK306', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('DOUBLEKING DK306 10PR', 'Marca importada del catalogo real: DOUBLEKING DK306 10PR', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('DOUBLESTAR', 'Marca importada del catalogo real: DOUBLESTAR', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('DOUBLESTAR 16 PR', 'Marca importada del catalogo real: DOUBLESTAR 16 PR', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('DOUBLESTAR DH05', 'Marca importada del catalogo real: DOUBLESTAR DH05', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('DOUBLESTAR DS01', 'Marca importada del catalogo real: DOUBLESTAR DS01', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('DURACEL 34R - 1100', 'Marca importada del catalogo real: DURACEL 34R - 1100', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('DURACELL 24-1000 (24MR)', 'Marca importada del catalogo real: DURACELL 24-1000 (24MR)', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('DURACELL 24F-1000 (24M)', 'Marca importada del catalogo real: DURACELL 24F-1000 (24M)', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('DURACELL 31 - 1300S (TORNILLO)', 'Marca importada del catalogo real: DURACELL 31 - 1300S (TORNILLO)', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('DURACELL 34 - 1100', 'Marca importada del catalogo real: DURACELL 34 - 1100', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('DURACELL 42-900 (42MR)', 'Marca importada del catalogo real: DURACELL 42-900 (42MR)', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('DURACELL 42R-900 (42M)', 'Marca importada del catalogo real: DURACELL 42R-900 (42M)', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('DURACELL 99-650 (36MR)', 'Marca importada del catalogo real: DURACELL 99-650 (36MR)', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('DURINGON CROSSMAXX', 'Marca importada del catalogo real: DURINGON CROSSMAXX', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ECOSAVER DIRECCIONAL 18PR', 'Marca importada del catalogo real: ECOSAVER DIRECCIONAL 18PR', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('EVERLAND', 'Marca importada del catalogo real: EVERLAND', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('EXTREMA 24AD1000-A (24MR)', 'Marca importada del catalogo real: EXTREMA 24AD1000-A (24MR)', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('EXTREME 24BD-720 (42MR)', 'Marca importada del catalogo real: EXTREME 24BD-720 (42MR)', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('EXTREME 24BI-720 (42M)', 'Marca importada del catalogo real: EXTREME 24BI-720 (42M)', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('EXTREME 36DLM700 (36MR)', 'Marca importada del catalogo real: EXTREME 36DLM700 (36MR)', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('FC FAUCI', 'Marca importada del catalogo real: FC FAUCI', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('Firestone', 'Neumaticos americanos', 'default_brand.png', 1, '2026-04-30 04:18:56'),
('FIRESTONE DESTINATION H/T', 'Marca importada del catalogo real: FIRESTONE DESTINATION H/T', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('FIRESTONE FIREHAWK', 'Marca importada del catalogo real: FIRESTONE FIREHAWK', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('FIRESTONE MULTIHAWK', 'Marca importada del catalogo real: FIRESTONE MULTIHAWK', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('GONHER', 'Marca importada del catalogo real: GONHER', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('GULF', 'Marca importada del catalogo real: GULF', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('HABILEAD', 'Marca importada del catalogo real: HABILEAD', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('HABILEAD A/T', 'Marca importada del catalogo real: HABILEAD A/T', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('HABILEAD AT', 'Marca importada del catalogo real: HABILEAD AT', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('HABILEAD COMFORMAX', 'Marca importada del catalogo real: HABILEAD COMFORMAX', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('HAIDA 16PR DIRECCIONAL', 'Marca importada del catalogo real: HAIDA 16PR DIRECCIONAL', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('HEADWAY', 'Marca importada del catalogo real: HEADWAY', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('HILO - VANTAGE XU1', 'Marca importada del catalogo real: HILO - VANTAGE XU1', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('HILO DIRECCIONAL 14PR', 'Marca importada del catalogo real: HILO DIRECCIONAL 14PR', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('HILO GENESYS', 'Marca importada del catalogo real: HILO GENESYS', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('HILO GENESYS XP1', 'Marca importada del catalogo real: HILO GENESYS XP1', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('HILO HT', 'Marca importada del catalogo real: HILO HT', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('HILO X-TERRAIN MT1', 'Marca importada del catalogo real: HILO X-TERRAIN MT1', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('HONOUR 14PR DIRECCIONAL', 'Marca importada del catalogo real: HONOUR 14PR DIRECCIONAL', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('INCA', 'Marca importada del catalogo real: INCA', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('Marca afahcceddi', 'Prueba', 'default_brand.png', 0, '2026-05-08 02:43:38'),
('MAXTREK SU-830', 'Marca importada del catalogo real: MAXTREK SU-830', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('MEXLUB', 'Marca importada del catalogo real: MEXLUB', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('Michelin', 'Neumaticos franceses de alta calidad', 'default_brand.png', 1, '2026-04-30 04:18:56'),
('MILEKING MT', 'Marca importada del catalogo real: MILEKING MT', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('Mobil', 'Marca importada del catalogo real: MOBIL', 'default_brand.png', 1, '2026-04-30 04:18:56'),
('MOTORCRAFT', 'Marca importada del catalogo real: MOTORCRAFT', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('MOURA ME310FD (36MR)', 'Marca importada del catalogo real: MOURA ME310FD (36MR)', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('MOURA ME570GI (22M)', 'Marca importada del catalogo real: MOURA ME570GI (22M)', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('MOURA ME650RD (24MR)', 'Marca importada del catalogo real: MOURA ME650RD (24MR)', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('MOURA ME805D (36MR)', 'Marca importada del catalogo real: MOURA ME805D (36MR)', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('NGK', 'Bujias y componentes de encendido', 'default_brand.png', 1, '2026-05-27 14:10:55'),
('NOVAMAX STAR A/T', 'Marca importada del catalogo real: NOVAMAX STAR A/T', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('NOVAMAX WARRIOR TERRA T/A', 'Marca importada del catalogo real: NOVAMAX WARRIOR TERRA T/A', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('NOVAMAXX', 'Marca importada del catalogo real: NOVAMAXX', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('NOVAMAXX AT', 'Marca importada del catalogo real: NOVAMAXX AT', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('OILSTONE', 'Marca importada del catalogo real: OILSTONE', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('Pirelli', 'Neumaticos premium italianos', 'default_brand.png', 1, '2026-04-30 04:18:56'),
('POWERTAC ECOCOMFORT', 'Marca importada del catalogo real: POWERTAC ECOCOMFORT', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('POWERTRAC', 'Marca importada del catalogo real: POWERTRAC', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('POWERTRAC ADAMAS', 'Marca importada del catalogo real: POWERTRAC ADAMAS', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('POWERTRAC CITYROVER', 'Marca importada del catalogo real: POWERTRAC CITYROVER', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('POWERTRAC DIRECCIONAL', 'Marca importada del catalogo real: POWERTRAC DIRECCIONAL', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('POWERTRAC ECO SPORT X77', 'Marca importada del catalogo real: POWERTRAC ECO SPORT X77', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('POWERTRAC ECOCOMFORT', 'Marca importada del catalogo real: POWERTRAC ECOCOMFORT', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('POWERTRAC ECOCOMFORT X66', 'Marca importada del catalogo real: POWERTRAC ECOCOMFORT X66', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('POWERTRAC MIXTO', 'Marca importada del catalogo real: POWERTRAC MIXTO', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('POWERTRAC TRAC PRO (SET)', 'Marca importada del catalogo real: POWERTRAC TRAC PRO (SET)', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('POWERTRAC TRACCION', 'Marca importada del catalogo real: POWERTRAC TRACCION', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('POWERTRAC VANTOUR', 'Marca importada del catalogo real: POWERTRAC VANTOUR', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('POWERTRAC WILDRANGER A/T', 'Marca importada del catalogo real: POWERTRAC WILDRANGER A/T', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('POWERTRAC WILDRANGER AT', 'Marca importada del catalogo real: POWERTRAC WILDRANGER AT', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('POWERTRAC WILDRANGER M/T', 'Marca importada del catalogo real: POWERTRAC WILDRANGER M/T', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('POWERTRAC WILDRANGER MT', 'Marca importada del catalogo real: POWERTRAC WILDRANGER MT', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('RALOY', 'Marca importada del catalogo real: RALOY', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('RAPID', 'Marca importada del catalogo real: RAPID', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('RAPID ECOLANDER', 'Marca importada del catalogo real: RAPID ECOLANDER', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('RAPID ECOLANDER A/T', 'Marca importada del catalogo real: RAPID ECOLANDER A/T', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('RAPID ECOSAVER', 'Marca importada del catalogo real: RAPID ECOSAVER', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('RAPID MUD CONTENDER M/T', 'Marca importada del catalogo real: RAPID MUD CONTENDER M/T', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('RAPID P329', 'Marca importada del catalogo real: RAPID P329', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('RAPID P609', 'Marca importada del catalogo real: RAPID P609', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('RAPID SHARK Z02', 'Marca importada del catalogo real: RAPID SHARK Z02', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('RAPID TUFTRAIL A/T', 'Marca importada del catalogo real: RAPID TUFTRAIL A/T', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ROADSHINE 16PR DIRECCIONAL', 'Marca importada del catalogo real: ROADSHINE 16PR DIRECCIONAL', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ROCKBLADE 14PR DIRECCIONAL', 'Marca importada del catalogo real: ROCKBLADE 14PR DIRECCIONAL', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ROCKBLADE 787RT', 'Marca importada del catalogo real: ROCKBLADE 787RT', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ROCKBLADE H/T', 'Marca importada del catalogo real: ROCKBLADE H/T', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ROYAL BLACK', 'Marca importada del catalogo real: ROYAL BLACK', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('ROYAL BLACK A/T', 'Marca importada del catalogo real: ROYAL BLACK A/T', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('Shell', 'Lubricantes Shell Helix', 'default_brand.png', 1, '2026-04-30 04:18:56'),
('SHELL HELIX', 'Marca importada del catalogo real: SHELL HELIX', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('SKY', 'Marca importada del catalogo real: SKY', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('SUPERMEALLIR DIRECCIONAL', 'Marca importada del catalogo real: SUPERMEALLIR DIRECCIONAL', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('TAITONG 18 PR MIXTO HS268', 'Marca importada del catalogo real: TAITONG 18 PR MIXTO HS268', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('TDI TIRES R/T', 'Marca importada del catalogo real: TDI TIRES R/T', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('TestBrand0507224100', 'Prueba', 'default_brand.png', 0, '2026-05-08 02:41:00'),
('V-RICH A/T', 'Marca importada del catalogo real: V-RICH A/T', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('V-RICH ALL TERRAIN', 'Marca importada del catalogo real: V-RICH ALL TERRAIN', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('V-RICH AT', 'Marca importada del catalogo real: V-RICH AT', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('V-RICH AT 10PR', 'Marca importada del catalogo real: V-RICH AT 10PR', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('VALVOLINE', 'Marca importada del catalogo real: VALVOLINE', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('VM LUB', 'Marca importada del catalogo real: VM LUB', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('VM LUBRICANTES', 'Marca importada del catalogo real: VM LUBRICANTES', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('WIDEWAY', 'Marca importada del catalogo real: WIDEWAY', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('WIDEWAY A/T', 'Marca importada del catalogo real: WIDEWAY A/T', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('WIDEWAY AK3 6PR', 'Marca importada del catalogo real: WIDEWAY AK3 6PR', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('WIDEWAY SAFEWAY', 'Marca importada del catalogo real: WIDEWAY SAFEWAY', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('WIDEWAY WEYONE AK3', 'Marca importada del catalogo real: WIDEWAY WEYONE AK3', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('WIDEWAY XT ALL-TERRAIN', 'Marca importada del catalogo real: WIDEWAY XT ALL-TERRAIN', 'default_brand.png', 1, '2026-05-28 02:32:34'),
('WOLF', 'Marca importada del catalogo real: WOLF', 'default_brand.png', 1, '2026-05-28 02:32:34');

CREATE TABLE `mecanicos` (
  `cedula` varchar(20) NOT NULL,
  `cedula_prefijo` varchar(2) DEFAULT NULL,
  `nombre` varchar(100) NOT NULL,
  `apellido` varchar(100) NOT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `especialidad` varchar(200) DEFAULT NULL,
  `foto_perfil` varchar(200) DEFAULT 'default.png',
  `usuario_id` int(11) DEFAULT NULL,
  `estado` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `metodos_pago` (
  `id` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `datos` varchar(1000) NOT NULL,
  `permite_credito` tinyint(1) NOT NULL DEFAULT 0,
  `estado` tinyint(1) NOT NULL DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `notificaciones` (
  `id` int(11) NOT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `cliente_cedula` varchar(20) DEFAULT NULL,
  `tipo` varchar(30) NOT NULL DEFAULT 'sistema',
  `titulo` varchar(200) DEFAULT NULL,
  `mensaje` text DEFAULT NULL,
  `prioridad` varchar(20) DEFAULT 'media',
  `leida` tinyint(1) DEFAULT 0,
  `enlace` varchar(500) DEFAULT NULL,
  `referencia_id` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `ordenes_compra` (
  `id` int(11) NOT NULL,
  `proveedor_rif` varchar(20) NOT NULL,
  `sucursal_id` int(11) NOT NULL,
  `fecha` timestamp NOT NULL DEFAULT current_timestamp(),
  `total` decimal(12,2) DEFAULT 0.00,
  `estado` varchar(30) NOT NULL DEFAULT 'pendiente',
  `observaciones` varchar(1000) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `ordenes_venta` (
  `id` int(11) NOT NULL,
  `cliente_cedula` varchar(20) NOT NULL,
  `sucursal_id` int(11) DEFAULT NULL,
  `fecha` timestamp NOT NULL DEFAULT current_timestamp(),
  `total` decimal(12,2) DEFAULT 0.00,
  `monto_deuda` decimal(12,2) NOT NULL DEFAULT 0.00,
  `estado` varchar(30) NOT NULL DEFAULT 'pendiente',
  `metodo_pago_id` int(11) DEFAULT NULL,
  `tipo_pago` varchar(20) NOT NULL DEFAULT 'contado',
  `credito_estado` varchar(30) NOT NULL DEFAULT 'sin_credito',
  `fecha_inicio_credito` date DEFAULT NULL,
  `fecha_vencimiento_credito` date DEFAULT NULL,
  `credito_notificacion_7d` tinyint(1) DEFAULT 0,
  `credito_notificacion_2d` tinyint(1) DEFAULT 0,
  `credito_notificacion_vencido` tinyint(1) DEFAULT 0,
  `fecha_pago_credito` datetime DEFAULT NULL,
  `comprobante_url` varchar(255) DEFAULT NULL,
  `observaciones` varchar(1000) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `productos` (
  `codigo` varchar(50) NOT NULL,
  `nombre` varchar(200) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `precio` decimal(10,2) NOT NULL DEFAULT 0.00,
  `categoria` varchar(150) DEFAULT NULL,
  `marca` varchar(150) DEFAULT NULL,
  `imagen` varchar(200) DEFAULT 'default_product.png',
  `estado` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO `productos` (`codigo`, `nombre`, `descripcion`, `precio`, `categoria`, `marca`, `imagen`, `estado`, `created_at`, `updated_at`) VALUES
('BAT-000016', '600 AMP EXTREME 36DLM700 (36MR)', 'Bateria 600 AMP. EXTREME 36DLM700 (36MR)', 50.00, 'Baterias', 'EXTREME 36DLM700 (36MR)', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('BAT-000017', '650 AMP MOURA ME310FD (36MR)', 'Bateria 650 AMP. MOURA ME310FD (36MR)', 70.00, 'Baterias', 'MOURA ME310FD (36MR)', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('BAT-000018', '650 AMP DURACELL 99-650 (36MR)', 'Bateria 650 AMP. DURACELL 99-650 (36MR)', 65.00, 'Baterias', 'DURACELL 99-650 (36MR)', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('BAT-000019', '700 AMP ARO 99R-700', 'Bateria 700 AMP. ARO 99R-700', 62.00, 'Baterias', 'ARO 99R-700', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('BAT-000020', '650 AMP MOURA ME805D (36MR)', 'Bateria 650 AMP. MOURA ME805D (36MR)', 85.00, 'Baterias', 'MOURA ME805D (36MR)', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('BAT-000023', '800 AMP MOURA ME570GI (22M)', 'Bateria 800 AMP. MOURA ME570GI (22M)', 92.00, 'Baterias', 'MOURA ME570GI (22M)', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('BAT-000024', '850 AMP EXTREME 24BI-720 (42M)', 'Bateria 850 AMP. EXTREME 24BI-720 (42M)', 65.00, 'Baterias', 'EXTREME 24BI-720 (42M)', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('BAT-000025', '850 AMP EXTREME 24BD-720 (42MR)', 'Bateria 850 AMP. EXTREME 24BD-720 (42MR)', 65.00, 'Baterias', 'EXTREME 24BD-720 (42MR)', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('BAT-000033', '900 AMP DURACELL 42-900 (42MR)', 'Bateria 900 AMP. DURACELL 42-900 (42MR)', 81.00, 'Baterias', 'DURACELL 42-900 (42MR)', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('BAT-000034', '900 AMP DURACELL 42R-900 (42M)', 'Bateria 900 AMP. DURACELL 42R-900 (42M)', 81.00, 'Baterias', 'DURACELL 42R-900 (42M)', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('BAT-000035', '900 AMP ARO 42-900 (42MR)', 'Bateria 900 AMP. ARO 42-900 (42MR)', 80.00, 'Baterias', 'ARO 42-900 (42MR)', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('BAT-000036', '900 AMP ARO 42R-900 (42M)', 'Bateria 900 AMP. ARO 42R-900 (42M)', 80.00, 'Baterias', 'ARO 42R-900 (42M)', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('BAT-000039', '1000 AMP MOURA ME650RD (24MR)', 'Bateria 1000 AMP. MOURA ME650RD (24MR)', 122.00, 'Baterias', 'MOURA ME650RD (24MR)', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('BAT-000040', '1100 AMP ARO 315-1100 (TORNILLO)', 'Bateria 1100 AMP. ARO 315-1100 (TORNILLO)', 112.00, 'Baterias', 'ARO 315-1100 (TORNILLO)', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('BAT-000041', '1000 AMP DURACELL 24-1000 (24MR)', 'Bateria 1000 AMP. DURACELL 24-1000 (24MR)', 89.00, 'Baterias', 'DURACELL 24-1000 (24MR)', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('BAT-000042', '1000 AMP DURACELL 24F-1000 (24M)', 'Bateria 1000 AMP. DURACELL 24F-1000 (24M)', 89.00, 'Baterias', 'DURACELL 24F-1000 (24M)', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('BAT-000043', '1000 AMP EXTREMA 24AD1000-A (24MR)', 'Bateria 1000 AMP. EXTREMA 24AD1000-A (24MR)', 85.00, 'Baterias', 'EXTREMA 24AD1000-A (24MR)', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('BAT-000044', '1100 AMP ARO 24R - 1100', 'Bateria 1100 AMP. ARO 24R - 1100', 92.00, 'Baterias', 'ARO 24R - 1100', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('BAT-000045', '1100 AMP ARO 24 - 1100', 'Bateria 1100 AMP. ARO 24 - 1100', 92.00, 'Baterias', 'ARO 24 - 1100', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('BAT-000046', '1100 AMP DURACELL 34 - 1100', 'Bateria 1100 AMP. DURACELL 34 - 1100', 94.00, 'Baterias', 'DURACELL 34 - 1100', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('BAT-000047', '1100 AMP DURACEL 34R - 1100', 'Bateria 1100 AMP. DURACEL 34R - 1100', 94.00, 'Baterias', 'DURACEL 34R - 1100', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('BAT-000048', '1300 AMP DURACELL 31 - 1300S (TORNILLO)', 'Bateria 1300 AMP. DURACELL 31 - 1300S (TORNILLO)', 120.00, 'Baterias', 'DURACELL 31 - 1300S (TORNILLO)', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('BAT-ACD-75-650', 'ACDelco bateria 75-650 CCA 12V', 'Bateria automotriz 12V con 650 CCA para vehiculos medianos.', 120.00, 'Baterias', 'ACDelco', 'default_product.png', 0, '2026-05-27 14:10:55', '2026-05-28 02:32:34'),
('CAU-FIR-DEST-24570R16', 'Firestone Destination A/T2 245/70R16', 'Caucho all terrain para uso diario y caminos rurales.', 175.00, 'Cauchos', 'Firestone', 'default_product.png', 0, '2026-05-27 14:10:55', '2026-05-28 02:32:34'),
('CAU-MIC-LTX-26565R17', 'Michelin LTX A/T2 265/65R17', 'Caucho all terrain para camionetas, uso mixto carretera y terrenos irregulares.', 215.00, 'Cauchos', 'Michelin', 'default_product.png', 0, '2026-05-27 14:10:55', '2026-05-28 02:32:34'),
('CAU-PIR-SCORP-26570R16', 'Pirelli Scorpion All Terrain Plus 265/70R16', 'Caucho todo terreno con buen agarre en asfalto, tierra y lluvia.', 198.00, 'Cauchos', 'Pirelli', 'default_product.png', 0, '2026-05-27 14:10:55', '2026-05-28 02:32:34'),
('CMB-000004', 'ACEITE 20W50 MINERAL GULF', 'Combo de producto y servicio. GULF', 9.61, 'Combos', 'ACEITE 20W50 MINERAL GULF', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000005', 'ACEITE 20W50 SEMI SINTETICO GULF', 'Combo de producto y servicio. GULF', 11.95, 'Combos', 'ACEITE 20W50 SEMI SINTETICO GULF', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000006', 'ACEITE 15W40 MINERAL GULF', 'Combo de producto y servicio. GULF', 9.61, 'Combos', 'ACEITE 15W40 MINERAL GULF', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000007', 'ACEITE 15W40 SEMI SINTETICO GULF', 'Combo de producto y servicio. GULF', 11.95, 'Combos', 'ACEITE 15W40 SEMI SINTETICO GULF', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000008', 'ACEITE 10W30 SEMI SINTETICO GULF', 'Combo de producto y servicio. GULF', 12.05, 'Combos', 'ACEITE 10W30 SEMI SINTETICO GULF', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000009', 'ACEITE 5W20 SINTETICO GULF', 'Combo de producto y servicio. GULF', 13.22, 'Combos', 'ACEITE 5W20 SINTETICO GULF', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000010', 'ACEITE 5W30 SINTETICO GULF', 'Combo de producto y servicio. GULF', 13.22, 'Combos', 'ACEITE 5W30 SINTETICO GULF', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000011', 'ACEITE 5W40 SINTETICO GUL', 'Combo de producto y servicio. GULF', 13.22, 'Combos', 'ACEITE 5W40 SINTETICO GUL', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000016', 'ACEITE 20W50 MINERAL RALOY', 'Combo de producto y servicio. RALOY / INCA / BOSS', 7.69, 'Combos', 'ACEITE 20W50 MINERAL RALOY', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000017', 'ACEITE 20W50 MINERAL INCA', 'Combo de producto y servicio. RALOY / INCA / BOSS', 7.55, 'Combos', 'ACEITE 20W50 MINERAL INCA', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000018', 'ACEITE 20W50 SEMI SINTETICO RALOY', 'Combo de producto y servicio. RALOY / INCA / BOSS', 8.30, 'Combos', 'ACEITE 20W50 SEMI SINTETICO RALOY', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000019', 'ACEITE 20W50 SEMI SINTETICO INCA', 'Combo de producto y servicio. RALOY / INCA / BOSS', 8.11, 'Combos', 'ACEITE 20W50 SEMI SINTETICO INCA', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000020', 'ACEITE 15W40 MINERAL RALOY', 'Combo de producto y servicio. RALOY / INCA / BOSS', 7.69, 'Combos', 'ACEITE 15W40 MINERAL RALOY', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000021', 'ACEITE 15W40 MINERAL INCA', 'Combo de producto y servicio. RALOY / INCA / BOSS', 7.52, 'Combos', 'ACEITE 15W40 MINERAL INCA', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000022', 'ACEITE 15W40 SEMI SINTETICO RALOY', 'Combo de producto y servicio. RALOY / INCA / BOSS', 8.30, 'Combos', 'ACEITE 15W40 SEMI SINTETICO RALOY', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000023', 'ACEITE 15W40 SEMI SINTETICO INCA', 'Combo de producto y servicio. RALOY / INCA / BOSS', 8.04, 'Combos', 'ACEITE 15W40 SEMI SINTETICO INCA', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000024', 'ACEITE 20W50 MINERAL BOSS', 'Combo de producto y servicio. RALOY / INCA / BOSS', 5.15, 'Combos', 'ACEITE 20W50 MINERAL BOSS', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000025', 'ACEITE 15W40 SEMI SINTETICO BOSS', 'Combo de producto y servicio. RALOY / INCA / BOSS', 5.34, 'Combos', 'ACEITE 15W40 SEMI SINTETICO BOSS', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000030', 'ACEITE 20W50 MINERAL VALVOLINE', 'Combo de producto y servicio. VALVOLINE / FC', 8.20, 'Combos', 'ACEITE 20W50 MINERAL VALVOLINE', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000031', 'ACEITE 20W50 MINERAL FC', 'Combo de producto y servicio. VALVOLINE / FC', 5.66, 'Combos', 'ACEITE 20W50 MINERAL FC', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000032', 'ACEITE 20W50 MINERAL MOBIL', 'Combo de producto y servicio. VALVOLINE / FC', 6.38, 'Combos', 'ACEITE 20W50 MINERAL MOBIL', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000033', 'ACEITE 20W50 SEMI SINTETICO VALVOLINE', 'Combo de producto y servicio. VALVOLINE / FC', 8.34, 'Combos', 'ACEITE 20W50 SEMI SINTETICO VALVOLINE', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000034', 'ACEITE 20W50 SEMI SINTETICO FC', 'Combo de producto y servicio. VALVOLINE / FC', 8.34, 'Combos', 'ACEITE 20W50 SEMI SINTETICO FC', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000035', 'ACEITE 10W40 SEMI SINTETICO MOBIL', 'Combo de producto y servicio. VALVOLINE / FC', 7.93, 'Combos', 'ACEITE 10W40 SEMI SINTETICO MOBIL', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000036', 'ACEITE 15W40 MINERAL VALVOLINE', 'Combo de producto y servicio. VALVOLINE / FC', 8.20, 'Combos', 'ACEITE 15W40 MINERAL VALVOLINE', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000037', 'ACEITE 15W40 MINERAL FC', 'Combo de producto y servicio. VALVOLINE / FC', 5.66, 'Combos', 'ACEITE 15W40 MINERAL FC', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000038', 'ACEITE 15W40 SEMI SINTETICO VALVOLINE', 'Combo de producto y servicio. VALVOLINE / FC', 8.34, 'Combos', 'ACEITE 15W40 SEMI SINTETICO VALVOLINE', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000039', '15W40 SEMI SINTETICO VALVOLINE GARRAFA', 'Combo de producto y servicio. VALVOLINE / FC', 29.90, 'Combos', '15W40 SEMI SINTETICO VALVOLINE GARRAFA', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000040', 'ACEITE 15W40 SEMI SINTETICO FC', 'Combo de producto y servicio. VALVOLINE / FC', 6.45, 'Combos', 'ACEITE 15W40 SEMI SINTETICO FC', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000041', '15W40 / 20W50 SEMI SINTETICO FC GARRAFA', 'Combo de producto y servicio. VALVOLINE / FC', 23.23, 'Combos', '15W40 / 20W50 SEMI SINTETICO FC GARRAFA', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000046', 'ACEITE 20W50 MINERAL ROSHFRANS', 'Combo de producto y servicio. WOLF / MEXLUB / ROSHFRANS', 8.22, 'Combos', 'ACEITE 20W50 MINERAL ROSHFRANS', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000047', 'ACEITE 20W50 MINERAL MEXLUB', 'Combo de producto y servicio. WOLF / MEXLUB / ROSHFRANS', 8.92, 'Combos', 'ACEITE 20W50 MINERAL MEXLUB', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000048', 'ACEITE 20W50 SEMI SINTETICO MEXLUB', 'Combo de producto y servicio. WOLF / MEXLUB / ROSHFRANS', 8.67, 'Combos', 'ACEITE 20W50 SEMI SINTETICO MEXLUB', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000049', 'ACEITE 15W40 MINERAL ROSHFRANS', 'Combo de producto y servicio. WOLF / MEXLUB / ROSHFRANS', 8.22, 'Combos', 'ACEITE 15W40 MINERAL ROSHFRANS', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000050', 'ACEITE 15W40 MINERAL MEXLUB', 'Combo de producto y servicio. WOLF / MEXLUB / ROSHFRANS', 9.16, 'Combos', 'ACEITE 15W40 MINERAL MEXLUB', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000051', 'ACEITE 15W40 SEMI SINTETICO MEXLUB', 'Combo de producto y servicio. WOLF / MEXLUB / ROSHFRANS', 9.06, 'Combos', 'ACEITE 15W40 SEMI SINTETICO MEXLUB', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000052', 'ACEITE 15W40 SEMI SINTETICO WOLF', 'Combo de producto y servicio. WOLF / MEXLUB / ROSHFRANS', 8.22, 'Combos', 'ACEITE 15W40 SEMI SINTETICO WOLF', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('CMB-000053', 'ACEITE 20W50 MINERAL MOTUL', 'Combo de producto y servicio. WOLF / MEXLUB / ROSHFRANS', 10.63, 'Combos', 'ACEITE 20W50 MINERAL MOTUL', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('COD0507224100', 'Producto 0507224100', 'Producto prueba', 20.00, 'TestCat0507224100', 'TestBrand0507224100', 'default_product.png', 0, '2026-05-08 02:41:00', '2026-05-22 05:57:16'),
('DEDE', 'dede', 'dede', 3233.00, 'Baterias', '15W40 / 20W50 SEMI SINTETICO FC GARRAFA', 'default_product.png', 1, '2026-06-02 21:37:09', '2026-06-02 21:37:09'),
('FIL-BOS-AIR-COR', 'Bosch filtro de aire Toyota Corolla', 'Filtro de aire para Toyota Corolla 2009-2014.', 18.00, 'Filtros', 'Bosch', 'default_product.png', 0, '2026-05-27 14:10:55', '2026-05-28 02:32:34'),
('FIL-BOS-OIL-TOY', 'Bosch filtro de aceite Toyota', 'Filtro de aceite compatible con motores Toyota seleccionados.', 12.00, 'Filtros', 'Bosch', 'default_product.png', 0, '2026-05-27 14:10:55', '2026-05-28 02:32:34'),
('FRE-BOS-BP-COR', 'Bosch pastillas de freno Toyota Corolla', 'Juego de pastillas delanteras para Toyota Corolla 2009-2014.', 42.00, 'Frenos', 'Bosch', 'default_product.png', 0, '2026-05-27 14:10:55', '2026-05-28 02:32:34'),
('LUB-000005', '15W40 MINERAL BRAVA S/N', 'Lubricante 15W40 MINERAL. BRAVA', 7.00, 'Lubricantes', 'BRAVA', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000006', '15W40 MINERAL ARMAX', 'Lubricante 15W40 MINERAL. ARMAX', 5.00, 'Lubricantes', 'ARMAX', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000007', '15W40 MINERAL FC', 'Lubricante 15W40 MINERAL. FC FAUCI', 5.00, 'Lubricantes', 'FC FAUCI', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000008', '15W40 MINERAL GULF MAX GDI', 'Lubricante 15W40 MINERAL. GULF', 9.00, 'Lubricantes', 'GULF', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000009', '15W40 MINERAL DAUER', 'Lubricante 15W40 MINERAL. DAUER', 7.50, 'Lubricantes', 'DAUER', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000010', '15W40 MINERAL AKRON', 'Lubricante 15W40 MINERAL. AKRON', 7.50, 'Lubricantes', 'AKRON', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000011', '15W40 MINERAL INCA', 'Lubricante 15W40 MINERAL. INCA', 8.50, 'Lubricantes', 'INCA', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000012', '15W40 MINERAL VALVOLINE CLASSIC', 'Lubricante 15W40 MINERAL. VALVOLINE', 7.50, 'Lubricantes', 'VALVOLINE', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000013', '20W50 MINERAL ATLANTIC', 'Lubricante 20W50 MINERAL. ATLANTIC OIL', 4.50, 'Lubricantes', 'ATLANTIC OIL', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000014', '20W50 MINERAL FC', 'Lubricante 20W50 MINERAL. FC FAUCI', 6.00, 'Lubricantes', 'FC FAUCI', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000015', '15W40 MINERAL ARMAX', 'Lubricante 20W50 MINERAL. ARMAX', 5.00, 'Lubricantes', 'ARMAX', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000016', '20W50 MINERAL GONHER', 'Lubricante 20W50 MINERAL. GONHER', 6.50, 'Lubricantes', 'GONHER', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000017', '20W50 MINERAL AKRON', 'Lubricante 20W50 MINERAL. AKRON', 7.50, 'Lubricantes', 'AKRON', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000018', '20W50 MINERAL BITOIL', 'Lubricante 20W50 MINERAL. BITOIL', 4.00, 'Lubricantes', 'BITOIL', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000019', '20W50 MINERAL RALOY RACING OIL MULTIGRADE', 'Lubricante 20W50 MINERAL. RALOY', 7.00, 'Lubricantes', 'RALOY', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000020', '20W50 MINERAL DAUER', 'Lubricante 20W50 MINERAL. DAUER', 7.50, 'Lubricantes', 'DAUER', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000021', '20W50 MINERAL BRAVA S/N', 'Lubricante 20W50 MINERAL. BRAVA', 7.00, 'Lubricantes', 'BRAVA', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000022', '20W50 MINERAL GULF MAX GDI', 'Lubricante 20W50 MINERAL. GULF', 9.00, 'Lubricantes', 'GULF', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000023', '20W50 MINERAL INCA', 'Lubricante 20W50 MINERAL. INCA', 8.50, 'Lubricantes', 'INCA', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000024', '20W50 MINERAL MEXLUB RACING SL 946ML', 'Lubricante 20W50 MINERAL. MEXLUB', 6.00, 'Lubricantes', 'MEXLUB', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000025', '20W50 VALVOLINE MINERAL 0.946L', 'Lubricante 20W50 MINERAL. VALVOLINE', 7.50, 'Lubricantes', 'VALVOLINE', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000026', '20W50 MINERAL MOBIL SUPER 1000', 'Lubricante 20W50 MINERAL. MOBIL', 8.00, 'Lubricantes', 'MOBIL', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000027', '20W50 MINERAL VM LUB', 'Lubricante 20W50 MINERAL. VM LUB', 5.00, 'Lubricantes', 'VM LUB', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000028', '25W60 MINERAL BOSS', 'Lubricante 25W60 MINERAL. BOSS', 4.50, 'Lubricantes', 'BOSS', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000029', '10W30 SEMI SINTETICO GULF TEC GDI', 'Lubricante 10W30 SEMI SINTETICO. GULF', 11.00, 'Lubricantes', 'GULF', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000030', '10W30 SEMI SINTETICO VALVOLINE', 'Lubricante 10W30 SEMI SINTETICO. VALVOLINE', 7.50, 'Lubricantes', 'VALVOLINE', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000031', '10W30 SEMI SINTETICO DAUER', 'Lubricante 10W30 SEMI SINTETICO. DAUER', 9.00, 'Lubricantes', 'DAUER', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000032', '10W30 SEMI SINTETICO MOBIL', 'Lubricante 10W30 SEMI SINTETICO. MOBIL', 9.50, 'Lubricantes', 'MOBIL', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000033', '10W40 SEMI SINTETICO MOBIL SUPER 2000', 'Lubricante 10W40 SEMI SINTETICO. MOBIL', 10.00, 'Lubricantes', 'MOBIL', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000034', '15W40 SEMI SINTETICO BOSS', 'Lubricante 15W40 SEMI SINTETICO. BOSS', 5.00, 'Lubricantes', 'BOSS', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000035', 'ACEITE 20W50 SEMI SINTETICO BRAVA', 'Lubricante 15W40 SEMI SINTETICO. BRAVA', 7.40, 'Lubricantes', 'BRAVA', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000036', '15W40 SEMI SINTETICO ARMAX', 'Lubricante 15W40 SEMI SINTETICO. ARMAX', 5.00, 'Lubricantes', 'ARMAX', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000037', '15W40 SEMI SINTETICO GONHER', 'Lubricante 15W40 SEMI SINTETICO. GONHER', 8.00, 'Lubricantes', 'GONHER', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000038', '15W40 SEMI SINTETICO AKRON', 'Lubricante 15W40 SEMI SINTETICO. AKRON', 8.00, 'Lubricantes', 'AKRON', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000039', '15W40 SEMI SINTETICO BRAVA', 'Lubricante 15W40 SEMI SINTETICO. BRAVA', 7.00, 'Lubricantes', 'BRAVA', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000040', '15W40 SEMI SINTETICO FC', 'Lubricante 15W40 SEMI SINTETICO. FC FAUCI', 7.00, 'Lubricantes', 'FC FAUCI', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000041', '15W40 TEC GDI GULF SEMI-SINTETICO AVANZADO 1L', 'Lubricante 15W40 SEMI SINTETICO. GULF', 11.00, 'Lubricantes', 'GULF', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000042', '15W40 SEMI SINTETICO OILSTONE', 'Lubricante 15W40 SEMI SINTETICO. OILSTONE', 7.00, 'Lubricantes', 'OILSTONE', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000043', '15W40 SEMI SINTETICO DAUER', 'Lubricante 15W40 SEMI SINTETICO. DAUER', 8.00, 'Lubricantes', 'DAUER', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000044', '15W40 SEMI SINTETICO 3.78L VALVOLINE', 'Lubricante 15W40 SEMI SINTETICO. VALVOLINE', 29.00, 'Lubricantes', 'VALVOLINE', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000045', '15W40 VALVOLINE PREMIUM PROTETION SEMI-SINTETICO', 'Lubricante 15W40 SEMI SINTETICO. VALVOLINE', 7.50, 'Lubricantes', 'VALVOLINE', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000046', '15W40 SEMI SINTETICO INCA', 'Lubricante 15W40 SEMI SINTETICO. INCA', 9.00, 'Lubricantes', 'INCA', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000047', '15W40 SEMI SINTETICO VM LUB', 'Lubricante 15W40 SEMI SINTETICO. VM LUBRICANTES', 5.00, 'Lubricantes', 'VM LUBRICANTES', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000048', '15W40 EVOLUB SKY', 'Lubricante 15W40 SEMI SINTETICO. SKY', 8.00, 'Lubricantes', 'SKY', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000049', '20W50 PREMIUM BLEND VALVOLINE SEMI-SINTETICO 0.946L', 'Lubricante 20W50 SEMI SINTETICO. VALVOLINE', 7.50, 'Lubricantes', 'VALVOLINE', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000050', '20W50 SEMI SINTETICO FC', 'Lubricante 20W50 SEMI SINTETICO. FC FAUCI', 7.00, 'Lubricantes', 'FC FAUCI', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000051', '20W50 SEMI SINTETICO BRAVA', 'Lubricante 20W50 SEMI SINTETICO. BRAVA', 7.00, 'Lubricantes', 'BRAVA', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000052', '20W50 SEMI SINTETICO ARMAX', 'Lubricante 20W50 SEMI SINTETICO. ARMAX', 5.00, 'Lubricantes', 'ARMAX', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000053', '20W50 SEMI SINTETICO VM LUB', 'Lubricante 20W50 SEMI SINTETICO. VM LUBRICANTES', 5.00, 'Lubricantes', 'VM LUBRICANTES', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000054', '20W50 SEMI SINTETICO BOSS', 'Lubricante 20W50 SEMI SINTETICO. BOSS', 5.00, 'Lubricantes', 'BOSS', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000055', '20W50 SEMI SINTETICO DAUER', 'Lubricante 20W50 SEMI SINTETICO. DAUER', 8.00, 'Lubricantes', 'DAUER', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000056', '20W50 SEMI SINTETICO FC GALON 3.78L', 'Lubricante 20W50 SEMI SINTETICO. FC FAUCI', 22.00, 'Lubricantes', 'FC FAUCI', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000057', '20W50 MAX ULTRA GULF SEMI-SINTETICO', 'Lubricante 20W50 SEMI SINTETICO. GULF', 10.00, 'Lubricantes', 'GULF', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000058', '20W50 SEMI SINTETICO INCA', 'Lubricante 20W50 SEMI SINTETICO. INCA', 9.00, 'Lubricantes', 'INCA', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000059', '20W50 EVOLUB SKY SENI SINTETICO', 'Lubricante 20W50 SEMI SINTETICO. SKY', 8.00, 'Lubricantes', 'SKY', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000060', 'OW20 GONHER NANOTEK GOLD 100% SINTETICO 946 ML', 'Lubricante 0W20 SINTETICO. GONHER', 7.00, 'Lubricantes', 'GONHER', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000061', '5W20 GONHER SINTETICO NANOTEK GOLD DE 946ML', 'Lubricante 5W20 SINTETICO. GONHER', 7.00, 'Lubricantes', 'GONHER', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000062', '5W20 GULF ULTRASYNTH GDI', 'Lubricante 5W20 SINTETICO. GULF', 8.00, 'Lubricantes', 'GULF', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000063', '5W-20 SHELL HELIX HX7 SP SINTETICO 1L', 'Lubricante 5W20 SINTETICO. SHELL HELIX', 8.00, 'Lubricantes', 'SHELL HELIX', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000064', '5W30 GULF FORMULA CX FULL SINTETICO', 'Lubricante 5W30 SINTETICO. GULF', 8.00, 'Lubricantes', 'GULF', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000065', '5W30 FULL SINTETICO VALVOLINE', 'Lubricante 5W30 SINTETICO. VALVOLINE', 10.00, 'Lubricantes', 'VALVOLINE', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000066', '5W30 SINTETICO MOBIL', 'Lubricante 5W30 SINTETICO. MOBIL', 8.00, 'Lubricantes', 'MOBIL', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000067', '5W30 SINTETICO MOTORCRAFT', 'Lubricante 5W30 SINTETICO. MOTORCRAFT', 9.50, 'Lubricantes', 'MOTORCRAFT', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000068', '5W30 SINTETICO WOLF ECOTECH SP-RP G6', 'Lubricante 5W30 SINTETICO. WOLF', 11.00, 'Lubricantes', 'WOLF', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000069', '5W40 GULF FORMULA CX FULL SINTETICO', 'Lubricante 5W40 SINTETICO. GULF', 8.00, 'Lubricantes', 'GULF', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000070', '20W50 MINERAL GULF PRIDE 4T PLUS', 'Lubricante 20W50 4T MINERAL. GULF', 9.50, 'Lubricantes', 'GULF', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000071', '20W50 MINERAL 4T VM LUB', 'Lubricante 20W50 4T MINERAL. VM LUB', 4.50, 'Lubricantes', 'VM LUB', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000072', '20W50 4TCH VALVOLINE MINERAL', 'Lubricante 20W50 4T MINERAL. VALVOLINE', 7.00, 'Lubricantes', 'VALVOLINE', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000073', '10W40 4T SINTETICO GULF POWER TRACK', 'Lubricante 10W40 4T SINTETICO. GULF', 15.00, 'Lubricantes', 'GULF', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000074', '15W50 4T INCA', 'Lubricante 10W50 4T SINTETICO. INCA', 4.00, 'Lubricantes', 'INCA', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000075', 'ACEITE CK-4 10W30 RALOY GARRAFA 3.75L', 'Lubricante 10W30 DIESEL. RALOY', 26.00, 'Lubricantes', 'RALOY', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000076', 'ACEITE ATF DEXRON III BITOIL 1L', 'Lubricante DEXRON III. BITOIL', 4.00, 'Lubricantes', 'BITOIL', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000077', 'ACEITE SAE 15W40 BITOIL MINERAL', 'Lubricante DEXRON III. BITOIL', 3.98, 'Lubricantes', 'BITOIL', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000078', 'ATF DEXRON III BITOIL PAILA 19L', 'Lubricante DEXRON III. BITOIL', 51.00, 'Lubricantes', 'BITOIL', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000079', 'ACEITE HIDRAULICO ATF III DAUER', 'Lubricante DEXRON III. DAUER', 7.50, 'Lubricantes', 'DAUER', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000080', 'ATF DX III GULF CAJA DE ACEITE AUTOMATICO DE 1L', 'Lubricante DEXRON III. GULF', 8.00, 'Lubricantes', 'GULF', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000081', 'ACEITE ATF-3 MEXLUB PARA TRANSMISIONES AUT', 'Lubricante DEXRON III. MEXLUB', 7.00, 'Lubricantes', 'MEXLUB', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000082', 'VALVULINA 80W90 BITOIL 1L', 'Lubricante 89W90. BITOIL', 4.00, 'Lubricantes', 'BITOIL', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000083', 'VALVULINA 85W140 BITOIL 1L', 'Lubricante 89W90. BITOIL', 3.98, 'Lubricantes', 'BITOIL', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000084', 'ACEITE FC 20W50 SEMI SINTETICO', 'Lubricante 89W90. FC FAUCI', 5.84, 'Lubricantes', 'FC FAUCI', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000085', 'VALVULINA 80W90 GULF GEAR MP', 'Lubricante 89W90. GULF', 6.50, 'Lubricantes', 'GULF', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000086', 'VALVULINA 85W140 GULF GEAR MP', 'Lubricante 89W90. GULF', 6.48, 'Lubricantes', 'GULF', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000087', 'ACEITE INCA 15W40 SEMI SINTETICO', 'Lubricante 89W90. INCA', 7.44, 'Lubricantes', 'INCA', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000088', 'SAE 80W90 TRANSMISION RALOY EXTREMA PRESION', 'Lubricante 89W90. RALOY', 5.00, 'Lubricantes', 'RALOY', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000089', 'ACEITE 25W50 MINERAL MEXLUB ALTO KILOMETRAJE', 'Lubricante 89W90. MEXLUB', 7.59, 'Lubricantes', 'MEXLUB', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000090', 'VALVULINA 80W90 GL-5 MEXLUB', 'Lubricante 89W90. MEXLUB', 7.96, 'Lubricantes', 'MEXLUB', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000091', 'VALVULINA 85W140 GL-5 MEXLUB', 'Lubricante 89W90. MEXLUB', 7.96, 'Lubricantes', 'MEXLUB', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000092', 'ACEITE OILSTONE 20W50 SEMI SINTETICO', 'Lubricante 89W90. OILSTONE', 6.78, 'Lubricantes', 'OILSTONE', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000093', 'SAE 85W140 VALVULINA RALOY EXTREMA PRESION 946ML', 'Lubricante 85W140. RALOY', 6.00, 'Lubricantes', 'RALOY', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000094', 'ACEITE ARMAX SAE50 PAILA 20L', 'Lubricante SAE50 DIESEL. ARMAX', 80.00, 'Lubricantes', 'ARMAX', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000095', 'ACEITE SAE50 BITOIL PAILA 19L', 'Lubricante SAE50 DIESEL. BITOIL', 55.00, 'Lubricantes', 'BITOIL', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000096', 'ACEITE BOSS SAE50 PAILA 20 LITROS', 'Lubricante SAE50 DIESEL. BOSS', 65.00, 'Lubricantes', 'BOSS', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000097', 'ACEITE SAE50 FC PAILA 19L', 'Lubricante SAE50 DIESEL. FC FAUCI', 75.00, 'Lubricantes', 'FC FAUCI', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000098', 'ACEITE DE MOTOR MOBIL DIESEL DELVAC MODERN 15W40', 'Lubricante 15W40 DIESEL. MOBIL', 8.50, 'Lubricantes', 'MOBIL', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000099', 'ACEITE ARMAX 15W40 MINERAL DIESEL PAILA 20L', 'Lubricante 15W40 DIESEL. ARMAX', 80.00, 'Lubricantes', 'ARMAX', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000100', 'ACEITE 15W40 DIESEL MEXLUB 5L CL-4', 'Lubricante 15W40 DIESEL. MEXLUB', 33.00, 'Lubricantes', 'MEXLUB', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000101', 'ISO 68 HIDRALOY 300 ACEITE HIDRAULICO 68 RALOY PAILA 19L', 'Lubricante HIDRAULICO 68. RALOY', 71.00, 'Lubricantes', 'RALOY', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000102', 'SAE 15W40 SEMI SINTETICO TURBO RALOY API SN PLUS', 'Lubricante HIDRAULICO 68. RALOY', 7.31, 'Lubricantes', 'RALOY', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000103', 'TRANS-FLUID RDX-III RALOY P/TRANSMISION AUTOMATICA', 'Lubricante HIDRAULICO 68. RALOY', 5.65, 'Lubricantes', 'RALOY', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000104', 'SAE 20W50 RALOY TURBO SEMI-SINTETICO', 'Lubricante HIDRAULICO 68. RALOY', 7.50, 'Lubricantes', 'RALOY', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000105', 'SAE 20W50 RALOY RACING OIL MULTIGRADE', 'Lubricante HIDRAULICO 68. RALOY', 6.94, 'Lubricantes', 'RALOY', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000106', 'ACEITE SHELL HELIX HX8 PROFESIONAL SINTETICO', 'Lubricante HIDRAULICO 68. SHELL HELIX', 11.12, 'Lubricantes', 'SHELL HELIX', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000107', 'ACEITE ATF DEXRON 3 SHELL SPIRAX S3 MD3 1L', 'Lubricante HIDRAULICO 68. SHELL HELIX', 8.46, 'Lubricantes', 'SHELL HELIX', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000108', 'ACEITE VITALTECH 5W40 SINTETICO WOLF', 'Lubricante HIDRAULICO 68. WOLF', 11.00, 'Lubricantes', 'WOLF', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-000109', 'VALVULINA SINTETICA 75W90 GL-5 VITAL TECH WOLF', 'Lubricante HIDRAULICO 68. WOLF', 15.00, 'Lubricantes', 'WOLF', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('LUB-CAS-GTX-10W40-4L', 'Castrol GTX 10W-40 4L', 'Aceite multigrado para proteccion contra desgaste y lodos.', 32.00, 'Lubricantes', 'Castrol', 'default_product.png', 0, '2026-05-27 14:10:55', '2026-05-28 02:32:34'),
('LUB-MOB-5W30-4L', 'Mobil Super 3000 5W-30 4L', 'Aceite sintetico para motor gasolina de alto rendimiento.', 38.00, 'Lubricantes', 'Mobil', 'default_product.png', 0, '2026-05-27 14:10:55', '2026-05-28 02:32:34'),
('LUB-SHE-HELIX-15W40-4L', 'Shell Helix HX5 15W-40 4L', 'Aceite mineral reforzado para motores de alto kilometraje.', 29.00, 'Lubricantes', 'Shell', 'default_product.png', 0, '2026-05-27 14:10:55', '2026-05-28 02:32:34'),
('NEU-000013', '165/65R13 HILO GENESYS', 'Caucho 165/65R13. HILO GENESYS. seccion RIN 13 PCR', 35.00, 'Cauchos', 'HILO GENESYS', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000014', '165/70R13 FIRESTONE MULTIHAWK', 'Caucho 165/70R13. FIRESTONE MULTIHAWK. seccion RIN 13 PCR', 52.00, 'Cauchos', 'FIRESTONE MULTIHAWK', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000015', '165/70R13 POWERTRAC ECOCOMFORT', 'Caucho 165/70R13. POWERTRAC ECOCOMFORT. seccion RIN 13 PCR', 33.00, 'Cauchos', 'POWERTRAC ECOCOMFORT', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000016', '165/70R13 ALIX VEZETTA', 'Caucho 165/70R13. ALIX VEZETTA. seccion RIN 13 PCR', 39.00, 'Cauchos', 'ALIX VEZETTA', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000017', '165/70R13 ROYAL BLACK', 'Caucho 165/70R13. ROYAL BLACK. seccion RIN 13 PCR', 36.00, 'Cauchos', 'ROYAL BLACK', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000018', '175/70R13 ALIX VEZETTA', 'Caucho 175/70R13. ALIX VEZETTA. seccion RIN 13 PCR', 43.00, 'Cauchos', 'ALIX VEZETTA', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000019', '175/70R13 FIRESTONE MULTIHAWK', 'Caucho 175/70R13. FIRESTONE MULTIHAWK. seccion RIN 13 PCR', 57.00, 'Cauchos', 'FIRESTONE MULTIHAWK', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000020', '175/70R13 ROYAL BLACK', 'Caucho 175/70R13. ROYAL BLACK. seccion RIN 13 PCR', 34.00, 'Cauchos', 'ROYAL BLACK', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000021', '175/70R13 POWERTRAC ADAMAS', 'Caucho 175/70R13. POWERTRAC ADAMAS. seccion RIN 13 PCR', 32.00, 'Cauchos', 'POWERTRAC ADAMAS', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000022', '175/70R13 POWERTRAC ECOCOMFORT', 'Caucho 175/70R13. POWERTRAC ECOCOMFORT. seccion RIN 13 PCR', 32.00, 'Cauchos', 'POWERTRAC ECOCOMFORT', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000023', '175/70R13 HILO GENESYS XP1', 'Caucho 175/70R13. HILO GENESYS XP1. seccion RIN 13 PCR', 36.00, 'Cauchos', 'HILO GENESYS XP1', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000024', '175/70R13 DOUBLESTAR', 'Caucho 175/70R13. DOUBLESTAR. seccion RIN 13 PCR', 29.00, 'Cauchos', 'DOUBLESTAR', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000025', '175/70R13 RAPID P329', 'Caucho 175/70R13. RAPID P329. seccion RIN 13 PCR', 37.00, 'Cauchos', 'RAPID P329', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000026', '175/70R13 HILO GENESYS XP1', 'Caucho 175/70R13. HILO GENESYS XP1. seccion RIN 13 PCR', 36.00, 'Cauchos', 'HILO GENESYS XP1', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000028', '175/65R14 EVERLAND', 'Caucho 175/65R14. EVERLAND. seccion RIN 14 PCR', 38.00, 'Cauchos', 'EVERLAND', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000029', '175/65R14 POWERTRAC ADAMAS', 'Caucho 175/65R14. POWERTRAC ADAMAS. seccion RIN 14 PCR', 35.00, 'Cauchos', 'POWERTRAC ADAMAS', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000030', '175/65R14 ALIX VEZETTA', 'Caucho 175/65R14. ALIX VEZETTA. seccion RIN 14 PCR', 47.00, 'Cauchos', 'ALIX VEZETTA', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000031', '175/65R14 DOUBLESTAR', 'Caucho 175/65R14. DOUBLESTAR. seccion RIN 14 PCR', 32.00, 'Cauchos', 'DOUBLESTAR', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000032', '185/60R14 POWERTRAC ADAMAS', 'Caucho 185/60R14. POWERTRAC ADAMAS. seccion RIN 14 PCR', 36.00, 'Cauchos', 'POWERTRAC ADAMAS', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000033', '185/60R14 DOUBLESTAR', 'Caucho 185/60R14. DOUBLESTAR. seccion RIN 14 PCR', 33.50, 'Cauchos', 'DOUBLESTAR', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000034', '185/65R14 DOUBLESTAR', 'Caucho 185/65R14. DOUBLESTAR. seccion RIN 14 PCR', 35.00, 'Cauchos', 'DOUBLESTAR', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000035', '185/65R14 ALIX VEZETTA', 'Caucho 185/65R14. ALIX VEZETTA. seccion RIN 14 PCR', 53.00, 'Cauchos', 'ALIX VEZETTA', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000036', '185/65R14 WIDEWAY SAFEWAY', 'Caucho 185/65R14. WIDEWAY SAFEWAY. seccion RIN 14 PCR', 39.00, 'Cauchos', 'WIDEWAY SAFEWAY', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000037', '185/65R14 FIRESTONE MULTIHAWK', 'Caucho 185/65R14. FIRESTONE MULTIHAWK. seccion RIN 14 PCR', 66.00, 'Cauchos', 'FIRESTONE MULTIHAWK', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000038', '185/65R14 POWERTRAC ECOCOMFORT X66', 'Caucho 185/65R14. POWERTRAC ECOCOMFORT X66. seccion RIN 14 PCR', 38.00, 'Cauchos', 'POWERTRAC ECOCOMFORT X66', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000039', '185/65R14 ANCHEE', 'Caucho 185/65R14. ANCHEE. seccion RIN 14 PCR', 41.00, 'Cauchos', 'ANCHEE', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000040', '185/65R14 ANNAITE', 'Caucho 185/65R14. ANNAITE. seccion RIN 14 PCR', 45.00, 'Cauchos', 'ANNAITE', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000041', '185/65R14 RAPID P329', 'Caucho 185/65R14. RAPID P329. seccion RIN 14 PCR', 42.00, 'Cauchos', 'RAPID P329', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000042', '195/70R14 HABILEAD COMFORMAX', 'Caucho 195/70R14. HABILEAD COMFORMAX. seccion RIN 14 PCR', 45.00, 'Cauchos', 'HABILEAD COMFORMAX', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000043', '205/70R14 HABILEAD', 'Caucho 205/70R14. HABILEAD. seccion RIN 14 PCR', 55.00, 'Cauchos', 'HABILEAD', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000044', '195R14C WIDEWAY', 'Caucho 195R14C. WIDEWAY. seccion RIN 14 PCR', 75.00, 'Cauchos', 'WIDEWAY', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000046', '195/60R15 WIDEWAY', 'Caucho 195/60R15. WIDEWAY. seccion RIN 15 PCR', 50.00, 'Cauchos', 'WIDEWAY', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000047', '195/60R15 ALIX VEZETTA PLUS', 'Caucho 195/60R15. ALIX VEZETTA PLUS. seccion RIN 15 PCR', 68.00, 'Cauchos', 'ALIX VEZETTA PLUS', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000048', '195/60R15 RAPID', 'Caucho 195/60R15. RAPID. seccion RIN 15 PCR', 53.00, 'Cauchos', 'RAPID', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000049', '195/60R15 POWERTRAC ADAMAS', 'Caucho 195/60R15. POWERTRAC ADAMAS. seccion RIN 15 PCR', 47.00, 'Cauchos', 'POWERTRAC ADAMAS', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000050', '195/60R15 POWERTAC ECOCOMFORT', 'Caucho 195/60R15. POWERTAC ECOCOMFORT. seccion RIN 15 PCR', 47.00, 'Cauchos', 'POWERTAC ECOCOMFORT', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000051', '195/65R15 WIDEWAY SAFEWAY', 'Caucho 195/65R15. WIDEWAY SAFEWAY. seccion RIN 15 PCR', 52.00, 'Cauchos', 'WIDEWAY SAFEWAY', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000052', '195/65R15 POWERTRAC ADAMAS', 'Caucho 195/65R15. POWERTRAC ADAMAS. seccion RIN 15 PCR', 45.00, 'Cauchos', 'POWERTRAC ADAMAS', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000053', '195/65R15 RAPID', 'Caucho 195/65R15. RAPID. seccion RIN 15 PCR', 55.00, 'Cauchos', 'RAPID', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000054', '195/65R15 DOUBLESTAR', 'Caucho 195/65R15. DOUBLESTAR. seccion RIN 15 PCR', 41.00, 'Cauchos', 'DOUBLESTAR', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000055', '205/70R15 MAXTREK SU-830', 'Caucho 205/70R15. MAXTREK SU-830. seccion RIN 15 PCR', 65.00, 'Cauchos', 'MAXTREK SU-830', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000056', '205/70R15 FIRESTONE DESTINATION H/T', 'Caucho 205/70R15. FIRESTONE DESTINATION H/T. seccion RIN 15 PCR', 100.00, 'Cauchos', 'FIRESTONE DESTINATION H/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000057', '215/65R15 HEADWAY', 'Caucho 215/65R15. HEADWAY. seccion RIN 15 PCR', 40.00, 'Cauchos', 'HEADWAY', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000058', '215/70R15 WIDEWAY SAFEWAY', 'Caucho 215/70R15. WIDEWAY SAFEWAY. seccion RIN 15 PCR', 80.00, 'Cauchos', 'WIDEWAY SAFEWAY', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000059', '205/70R15C POWERTRAC VANTOUR', 'Caucho 205/70R15C. POWERTRAC VANTOUR. seccion RIN 15 PCR', 68.00, 'Cauchos', 'POWERTRAC VANTOUR', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000060', 'LT235/75R15 POWERTRAC WILDRANGER M/T', 'Caucho LT235/75R15. POWERTRAC WILDRANGER M/T. seccion RIN 15 PCR', 90.00, 'Cauchos', 'POWERTRAC WILDRANGER M/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000061', 'LT235/75R15 POWERTRAC WILDRANGER A/T', 'Caucho LT235/75R15. POWERTRAC WILDRANGER A/T. seccion RIN 15 PCR', 100.00, 'Cauchos', 'POWERTRAC WILDRANGER A/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000062', '235/75R15 NOVAMAXX AT', 'Caucho 235/75R15. NOVAMAXX AT. seccion RIN 15 PCR', 85.00, 'Cauchos', 'NOVAMAXX AT', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000063', 'P235/75R15 POWERTRAC WILDRANGER A/T', 'Caucho P235/75R15. POWERTRAC WILDRANGER A/T. seccion RIN 15 PCR', 90.00, 'Cauchos', 'POWERTRAC WILDRANGER A/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000064', '235/75R15 RAPID ECOSAVER', 'Caucho 235/75R15. RAPID ECOSAVER. seccion RIN 15 PCR', 90.00, 'Cauchos', 'RAPID ECOSAVER', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000065', '235/75R15 WIDEWAY AK3 6PR', 'Caucho 235/75R15. WIDEWAY AK3 6PR. seccion RIN 15 PCR', 130.00, 'Cauchos', 'WIDEWAY AK3 6PR', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000067', '235/75R15 HILO HT', 'Caucho 235/75R15. HILO HT. seccion RIN 15 PCR', 100.00, 'Cauchos', 'HILO HT', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000068', '235/75R15 NOVAMAXX', 'Caucho 235/75R15. NOVAMAXX. seccion RIN 15 PCR', 85.00, 'Cauchos', 'NOVAMAXX', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000069', 'P235/75R15 DOUBLEKING DK306', 'Caucho P235/75R15. DOUBLEKING DK306. seccion RIN 15 PCR', 80.00, 'Cauchos', 'DOUBLEKING DK306', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000070', 'LT235/75R15 DOUBLEKING DK306 10PR', 'Caucho LT235/75R15. DOUBLEKING DK306 10PR. seccion RIN 15 PCR', 90.00, 'Cauchos', 'DOUBLEKING DK306 10PR', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000071', '295/50R15 RAPID SHARK Z02', 'Caucho 295/50R15. RAPID SHARK Z02. seccion RIN 15 PCR', 127.00, 'Cauchos', 'RAPID SHARK Z02', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000072', '31X10.50R15 ANCHEE MT', 'Caucho 31X10.50R15. ANCHEE MT. seccion RIN 15 PCR', 165.00, 'Cauchos', 'ANCHEE MT', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000073', '31X10.50R15 HILO X-TERRAIN MT1', 'Caucho 31X10.50R15. HILO X-TERRAIN MT1. seccion RIN 15 PCR', 165.00, 'Cauchos', 'HILO X-TERRAIN MT1', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000074', '31X10.50R15 WIDEWAY A/T', 'Caucho 31X10.50R15. WIDEWAY A/T. seccion RIN 15 PCR', 165.00, 'Cauchos', 'WIDEWAY A/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000075', '31X10.50R15 V-RICH A/T', 'Caucho 31X10.50R15. V-RICH A/T. seccion RIN 15 PCR', 170.00, 'Cauchos', 'V-RICH A/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000076', '31X10.50R15 LT ROCKBLADE 787RT', 'Caucho 31X10.50R15 LT. ROCKBLADE 787RT. seccion RIN 15 PCR', 135.00, 'Cauchos', 'ROCKBLADE 787RT', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000077', '31X10.50R15 LT HABILEAD AT', 'Caucho 31X10.50R15 LT. HABILEAD AT. seccion RIN 15 PCR', 125.00, 'Cauchos', 'HABILEAD AT', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000078', '31X10.50R15 POWERTRAC WILDRANGER A/T', 'Caucho 31X10.50R15. POWERTRAC WILDRANGER A/T. seccion RIN 15 PCR', 130.00, 'Cauchos', 'POWERTRAC WILDRANGER A/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000079', '31X10.50R15 POWERTRAC WILDRANGER M/T', 'Caucho 31X10.50R15. POWERTRAC WILDRANGER M/T. seccion RIN 15 PCR', 137.00, 'Cauchos', 'POWERTRAC WILDRANGER M/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000081', '31X10.50R15 AOQISHI MARVEL M/T', 'Caucho 31X10.50R15. AOQISHI MARVEL M/T. seccion RIN 15 PCR', 140.00, 'Cauchos', 'AOQISHI MARVEL M/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000082', '31X10.50R15 DURINGON CROSSMAXX', 'Caucho 31X10.50R15. DURINGON CROSSMAXX. seccion RIN 15 PCR', 140.00, 'Cauchos', 'DURINGON CROSSMAXX', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000083', '31X10.50R15 CROSSLEADER WILDTIGER MT', 'Caucho 31X10.50R15. CROSSLEADER WILDTIGER MT. seccion RIN 15 PCR', 115.00, 'Cauchos', 'CROSSLEADER WILDTIGER MT', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000084', '31X10.50R15 RAPID TUFTRAIL A/T', 'Caucho 31X10.50R15. RAPID TUFTRAIL A/T. seccion RIN 15 PCR', 135.00, 'Cauchos', 'RAPID TUFTRAIL A/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000085', '31X10.50R15 RAPID MUD CONTENDER M/T', 'Caucho 31X10.50R15. RAPID MUD CONTENDER M/T. seccion RIN 15 PCR', 145.00, 'Cauchos', 'RAPID MUD CONTENDER M/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000086', 'LT32X11.5R15 HILO X-TERRAIN MT1', 'Caucho LT32X11.5R15. HILO X-TERRAIN MT1. seccion RIN 15 PCR', 200.00, 'Cauchos', 'HILO X-TERRAIN MT1', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34');
INSERT INTO `productos` (`codigo`, `nombre`, `descripcion`, `precio`, `categoria`, `marca`, `imagen`, `estado`, `created_at`, `updated_at`) VALUES
('NEU-000087', '33X12.5R15LT HILO X-TERRAIN MT1', 'Caucho 33X12.5R15LT. HILO X-TERRAIN MT1. seccion RIN 15 PCR', 210.00, 'Cauchos', 'HILO X-TERRAIN MT1', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000088', 'LT7.00R15 7.00R15 KOBATA', 'Caucho LT7.00R15. 7.00R15 KOBATA. seccion RIN 15 PCR', 95.00, 'Cauchos', '7.00R15 KOBATA', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000089', 'LT35X12.5R15 HILO X-TERRAIN MT1', 'Caucho LT35X12.5R15. HILO X-TERRAIN MT1. seccion RIN 15 PCR', 225.00, 'Cauchos', 'HILO X-TERRAIN MT1', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000091', '195/55R16 POWERTRAC ADAMAS', 'Caucho 195/55R16. POWERTRAC ADAMAS. seccion RIN 16 PCR', 45.00, 'Cauchos', 'POWERTRAC ADAMAS', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000092', '195/55R16 WIDEWAY', 'Caucho 195/55R16. WIDEWAY. seccion RIN 16 PCR', 58.00, 'Cauchos', 'WIDEWAY', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000093', '205/55R16 ANCHEE', 'Caucho 205/55R16. ANCHEE. seccion RIN 16 PCR', 53.00, 'Cauchos', 'ANCHEE', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000094', '205/55R16 ALIX VELOCE', 'Caucho 205/55R16. ALIX VELOCE. seccion RIN 16 PCR', 70.00, 'Cauchos', 'ALIX VELOCE', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000095', '205/55R16 POWERTRAC ECOCOMFORT X66', 'Caucho 205/55R16. POWERTRAC ECOCOMFORT X66. seccion RIN 16 PCR', 54.00, 'Cauchos', 'POWERTRAC ECOCOMFORT X66', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000096', '205/55R16 DOUBLESTAR DH05', 'Caucho 205/55R16. DOUBLESTAR DH05. seccion RIN 16 PCR', 41.00, 'Cauchos', 'DOUBLESTAR DH05', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000097', '215/60R16 POWERTRAC', 'Caucho 215/60R16. POWERTRAC. seccion RIN 16 PCR', 56.00, 'Cauchos', 'POWERTRAC', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000098', '235/60R16 ALIX IMPACT HT', 'Caucho 235/60R16. ALIX IMPACT HT. seccion RIN 16 PCR', 93.00, 'Cauchos', 'ALIX IMPACT HT', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000099', '235/60R16 POWERTRAC ADAMAS', 'Caucho 235/60R16. POWERTRAC ADAMAS. seccion RIN 16 PCR', 75.00, 'Cauchos', 'POWERTRAC ADAMAS', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000100', '235/70R16 NOVAMAXX AT', 'Caucho 235/70R16. NOVAMAXX AT. seccion RIN 16 PCR', 100.00, 'Cauchos', 'NOVAMAXX AT', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000101', '245/70R16 DOUBLESTAR DS01', 'Caucho 245/70R16. DOUBLESTAR DS01. seccion RIN 16 PCR', 87.00, 'Cauchos', 'DOUBLESTAR DS01', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000102', '245/70R16 POWERTRAC WILDRANGER A/T', 'Caucho 245/70R16. POWERTRAC WILDRANGER A/T. seccion RIN 16 PCR', 100.00, 'Cauchos', 'POWERTRAC WILDRANGER A/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000103', 'LT245/75R16 POWERTRAC WILDRANGER A/T', 'Caucho LT245/75R16. POWERTRAC WILDRANGER A/T. seccion RIN 16 PCR', 110.00, 'Cauchos', 'POWERTRAC WILDRANGER A/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000104', 'P255/70R16 ALIX IMPACT HT PLUS', 'Caucho P255/70R16. ALIX IMPACT HT PLUS. seccion RIN 16 PCR', 135.00, 'Cauchos', 'ALIX IMPACT HT PLUS', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000105', '255/70R16 TDI TIRES R/T', 'Caucho 255/70R16. TDI TIRES R/T. seccion RIN 16 PCR', 110.00, 'Cauchos', 'TDI TIRES R/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000106', 'LT265/70R16 V-RICH AT', 'Caucho LT265/70R16. V-RICH AT. seccion RIN 16 PCR', 175.00, 'Cauchos', 'V-RICH AT', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000107', 'LT265/75R16 POWERTRAC WILDRANGER A/T', 'Caucho LT265/75R16. POWERTRAC WILDRANGER A/T. seccion RIN 16 PCR', 145.00, 'Cauchos', 'POWERTRAC WILDRANGER A/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000108', 'P265/75R16 NOVAMAX WARRIOR TERRA T/A', 'Caucho P265/75R16. NOVAMAX WARRIOR TERRA T/A. seccion RIN 16 PCR', 140.00, 'Cauchos', 'NOVAMAX WARRIOR TERRA T/A', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000109', 'LT265/75R16 ROYAL BLACK A/T', 'Caucho LT265/75R16. ROYAL BLACK A/T. seccion RIN 16 PCR', 150.00, 'Cauchos', 'ROYAL BLACK A/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000110', '265/75R16 V-RICH AT 10PR', 'Caucho 265/75R16. V-RICH AT 10PR. seccion RIN 16 PCR', 195.00, 'Cauchos', 'V-RICH AT 10PR', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000112', 'P265/75R16 TDI TIRES R/T', 'Caucho P265/75R16. TDI TIRES R/T. seccion RIN 16 PCR', 127.00, 'Cauchos', 'TDI TIRES R/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000114', 'LT265/75R16 ALIX IMPACT AT PLUS', 'Caucho LT265/75R16. ALIX IMPACT AT PLUS. seccion RIN 16 PCR', 175.00, 'Cauchos', 'ALIX IMPACT AT PLUS', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000115', 'LT265/75R16 V-RICH ALL TERRAIN', 'Caucho LT265/75R16. V-RICH ALL TERRAIN. seccion RIN 16 PCR', 185.00, 'Cauchos', 'V-RICH ALL TERRAIN', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000116', 'LT265/75R16 HILO X-TERRAIN MT1', 'Caucho LT265/75R16. HILO X-TERRAIN MT1. seccion RIN 16 PCR', 200.00, 'Cauchos', 'HILO X-TERRAIN MT1', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000117', 'LT265/75R16 RAPID TUFTRAIL A/T', 'Caucho LT265/75R16. RAPID TUFTRAIL A/T. seccion RIN 16 PCR', 165.00, 'Cauchos', 'RAPID TUFTRAIL A/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000118', 'LT265/75R16 NOVAMAX STAR A/T', 'Caucho LT265/75R16. NOVAMAX STAR A/T. seccion RIN 16 PCR', 127.00, 'Cauchos', 'NOVAMAX STAR A/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000119', 'LT285/75R16 POWERTRAC WILDRANGER A/T', 'Caucho LT285/75R16. POWERTRAC WILDRANGER A/T. seccion RIN 16 PCR', 160.00, 'Cauchos', 'POWERTRAC WILDRANGER A/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000120', '285/75R16 V-RICH A/T', 'Caucho 285/75R16. V-RICH A/T. seccion RIN 16 PCR', 195.00, 'Cauchos', 'V-RICH A/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000121', '285/75R16 HILO X-TERRAIN MT1', 'Caucho 285/75R16. HILO X-TERRAIN MT1. seccion RIN 16 PCR', 210.00, 'Cauchos', 'HILO X-TERRAIN MT1', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000123', '285/75R16 RAPID ECOLANDER A/T', 'Caucho 285/75R16. RAPID ECOLANDER A/T. seccion RIN 16 PCR', 175.00, 'Cauchos', 'RAPID ECOLANDER A/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000124', 'LT285/75R16 AOQISHI A/T', 'Caucho LT285/75R16. AOQISHI A/T. seccion RIN 16 PCR', 160.00, 'Cauchos', 'AOQISHI A/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000126', 'LT285/75R16 WIDEWAY XT ALL-TERRAIN', 'Caucho LT285/75R16. WIDEWAY XT ALL-TERRAIN. seccion RIN 16 PCR', 200.00, 'Cauchos', 'WIDEWAY XT ALL-TERRAIN', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000127', '305/70R16 HILO X-TERRAIN MT1', 'Caucho 305/70R16. HILO X-TERRAIN MT1. seccion RIN 16 PCR', 220.00, 'Cauchos', 'HILO X-TERRAIN MT1', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000128', '315/75R16 POWERTRAC WILDRANGER M/T', 'Caucho 315/75R16. POWERTRAC WILDRANGER M/T. seccion RIN 16 PCR', 215.00, 'Cauchos', 'POWERTRAC WILDRANGER M/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000129', '315/75R16 HILO X-TERRAIN MT1', 'Caucho 315/75R16. HILO X-TERRAIN MT1. seccion RIN 16 PCR', 240.00, 'Cauchos', 'HILO X-TERRAIN MT1', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000131', '7.50R16 HILO DIRECCIONAL 14PR', 'Caucho 7.50R16. HILO DIRECCIONAL 14PR. seccion RIN 16 TBR', 120.00, 'Cauchos', 'HILO DIRECCIONAL 14PR', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000132', '7.50R16 ANNAITE DIRECCIONAL 14PR', 'Caucho 7.50R16. ANNAITE DIRECCIONAL 14PR. seccion RIN 16 TBR', 120.00, 'Cauchos', 'ANNAITE DIRECCIONAL 14PR', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000133', '7.50-16 POWERTRAC TRAC PRO (SET)', 'Caucho 7.50-16. POWERTRAC TRAC PRO (SET). seccion RIN 16 TBR', 126.00, 'Cauchos', 'POWERTRAC TRAC PRO (SET)', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000134', '7.50R16 HONOUR 14PR DIRECCIONAL', 'Caucho 7.50R16. HONOUR 14PR DIRECCIONAL. seccion RIN 16 TBR', 105.00, 'Cauchos', 'HONOUR 14PR DIRECCIONAL', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000135', '7.50R16 HAIDA 16PR DIRECCIONAL', 'Caucho 7.50R16. HAIDA 16PR DIRECCIONAL. seccion RIN 16 TBR', 135.00, 'Cauchos', 'HAIDA 16PR DIRECCIONAL', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000136', '7.50R16 ROCKBLADE 14PR DIRECCIONAL', 'Caucho 7.50R16. ROCKBLADE 14PR DIRECCIONAL. seccion RIN 16 TBR', 100.00, 'Cauchos', 'ROCKBLADE 14PR DIRECCIONAL', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000137', '7.50R16 ROADSHINE 16PR DIRECCIONAL', 'Caucho 7.50R16. ROADSHINE 16PR DIRECCIONAL. seccion RIN 16 TBR', 135.00, 'Cauchos', 'ROADSHINE 16PR DIRECCIONAL', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000139', '215/60R17 POWERTRAC CITYROVER', 'Caucho 215/60R17. POWERTRAC CITYROVER. seccion RIN 17 PCR', 70.00, 'Cauchos', 'POWERTRAC CITYROVER', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000140', '225/50ZR17 HILO - VANTAGE XU1', 'Caucho 225/50ZR17. HILO - VANTAGE XU1. seccion RIN 17 PCR', 90.00, 'Cauchos', 'HILO - VANTAGE XU1', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000141', '205/45R17 RAPID P609', 'Caucho 205/45R17. RAPID P609. seccion RIN 17 PCR', 80.00, 'Cauchos', 'RAPID P609', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000145', '215/45R17 RAPID P609', 'Caucho 215/45R17. RAPID P609. seccion RIN 17 PCR', 80.00, 'Cauchos', 'RAPID P609', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000146', '215/45R17 DOUBLESTAR', 'Caucho 215/45R17. DOUBLESTAR. seccion RIN 17 PCR', 60.00, 'Cauchos', 'DOUBLESTAR', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000147', '215/60R17 FIRESTONE FIREHAWK', 'Caucho 215/60R17. FIRESTONE FIREHAWK. seccion RIN 17 PCR', 109.00, 'Cauchos', 'FIRESTONE FIREHAWK', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000150', '245/65R17 DOUBLEKING', 'Caucho 245/65R17. DOUBLEKING. seccion RIN 17 PCR', 115.00, 'Cauchos', 'DOUBLEKING', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000151', '265/70R17 RAPID ECOLANDER', 'Caucho 265/70R17. RAPID ECOLANDER. seccion RIN 17 PCR', 145.00, 'Cauchos', 'RAPID ECOLANDER', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000152', 'LT265/70R17 V-RICH ALL TERRAIN', 'Caucho LT265/70R17. V-RICH ALL TERRAIN. seccion RIN 17 PCR', 180.00, 'Cauchos', 'V-RICH ALL TERRAIN', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000153', 'LT265/70R17 AOQISHI A/T', 'Caucho LT265/70R17. AOQISHI A/T. seccion RIN 17 PCR', 150.00, 'Cauchos', 'AOQISHI A/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000154', '275/70R17 AOQISHI A/T', 'Caucho 275/70R17. AOQISHI A/T. seccion RIN 17 PCR', 160.00, 'Cauchos', 'AOQISHI A/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000155', 'LT275/70R17 V-RICH ALL TERRAIN', 'Caucho LT275/70R17. V-RICH ALL TERRAIN. seccion RIN 17 PCR', 190.00, 'Cauchos', 'V-RICH ALL TERRAIN', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000157', 'LT285/70R17 POWERTRAC WILDRANGER AT', 'Caucho LT285/70R17. POWERTRAC WILDRANGER AT. seccion RIN 17 PCR', 170.00, 'Cauchos', 'POWERTRAC WILDRANGER AT', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000158', 'LT285/70R17 POWERTRAC WILDRANGER MT', 'Caucho LT285/70R17. POWERTRAC WILDRANGER MT. seccion RIN 17 PCR', 175.00, 'Cauchos', 'POWERTRAC WILDRANGER MT', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000159', 'LT285/70R17 HILO X-TERRAIN MT1', 'Caucho LT285/70R17. HILO X-TERRAIN MT1. seccion RIN 17 PCR', 210.00, 'Cauchos', 'HILO X-TERRAIN MT1', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000160', 'LT285/70R17 WIDEWAY XT ALL-TERRAIN', 'Caucho LT285/70R17. WIDEWAY XT ALL-TERRAIN. seccion RIN 17 PCR', 185.00, 'Cauchos', 'WIDEWAY XT ALL-TERRAIN', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000161', 'LT285/70R17 V-RICH ALL TERRAIN', 'Caucho LT285/70R17. V-RICH ALL TERRAIN. seccion RIN 17 PCR', 195.00, 'Cauchos', 'V-RICH ALL TERRAIN', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000162', 'LT315/70R17 V-RICH ALL TERRAIN', 'Caucho LT315/70R17. V-RICH ALL TERRAIN. seccion RIN 17 PCR', 220.00, 'Cauchos', 'V-RICH ALL TERRAIN', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000165', '215/75R17.5 POWERTRAC', 'Caucho 215/75R17.5. POWERTRAC. seccion RIN 17.5 TBR', 140.00, 'Cauchos', 'POWERTRAC', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000166', '235/75R17.5 POWERTRAC', 'Caucho 235/75R17.5. POWERTRAC. seccion RIN 17.5 TBR', 165.00, 'Cauchos', 'POWERTRAC', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000167', '235/75R17.5 CHENSHANG', 'Caucho 235/75R17.5. CHENSHANG. seccion RIN 17.5 TBR', 160.00, 'Cauchos', 'CHENSHANG', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000169', '225/40ZR18 POWERTRAC ECO SPORT X77', 'Caucho 225/40ZR18. POWERTRAC ECO SPORT X77. seccion RIN 18 PCR', 80.00, 'Cauchos', 'POWERTRAC ECO SPORT X77', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000170', '235/50ZR18 POWERTRAC ECO SPORT X77', 'Caucho 235/50ZR18. POWERTRAC ECO SPORT X77. seccion RIN 18 PCR', 85.00, 'Cauchos', 'POWERTRAC ECO SPORT X77', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000171', '245/60R18 POWERTRAC CITYROVER', 'Caucho 245/60R18. POWERTRAC CITYROVER. seccion RIN 18 PCR', 105.00, 'Cauchos', 'POWERTRAC CITYROVER', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000172', '35X12.50R18 WIDEWAY', 'Caucho 35X12.50R18. WIDEWAY. seccion RIN 18 PCR', 235.00, 'Cauchos', 'WIDEWAY', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000174', '265/60R18 HABILEAD A/T', 'Caucho 265/60R18. HABILEAD A/T. seccion RIN 18 PCR', 105.00, 'Cauchos', 'HABILEAD A/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000175', '265/60R18 ROCKBLADE H/T', 'Caucho 265/60R18. ROCKBLADE H/T. seccion RIN 18 PCR', 110.00, 'Cauchos', 'ROCKBLADE H/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000176', '37x13.5R18 MILEKING MT', 'Caucho 37x13.5R18. MILEKING MT. seccion RIN 18 PCR', 295.00, 'Cauchos', 'MILEKING MT', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000178', '275/55R20 WIDEWAY WEYONE AK3', 'Caucho 275/55R20. WIDEWAY WEYONE AK3. seccion RIN 20 PCR', 205.00, 'Cauchos', 'WIDEWAY WEYONE AK3', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000179', '275/55R20 V-RICH ALL TERRAIN', 'Caucho 275/55R20. V-RICH ALL TERRAIN. seccion RIN 20 PCR', 205.00, 'Cauchos', 'V-RICH ALL TERRAIN', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000181', '35X12.5R20 POWERTRAC WILDRANGER M/T', 'Caucho 35X12.5R20. POWERTRAC WILDRANGER M/T. seccion RIN 20 PCR', 250.00, 'Cauchos', 'POWERTRAC WILDRANGER M/T', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000182', '8.25R20 DOUBLESTAR 16 PR', 'Caucho 8.25R20. DOUBLESTAR 16 PR. seccion RIN 20 PCR', 150.00, 'Cauchos', 'DOUBLESTAR 16 PR', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000184', '295/80R22.5 TAITONG 18 PR MIXTO HS268', 'Caucho 295/80R22.5. TAITONG 18 PR MIXTO HS268. seccion RIN 22.5 TBR', 220.00, 'Cauchos', 'TAITONG 18 PR MIXTO HS268', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000185', '295/80R22.5 ECOSAVER DIRECCIONAL 18PR', 'Caucho 295/80R22.5. ECOSAVER DIRECCIONAL 18PR. seccion RIN 22.5 TBR', 200.00, 'Cauchos', 'ECOSAVER DIRECCIONAL 18PR', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000186', '295/80R22.5 POWERTRAC DIRECCIONAL', 'Caucho 295/80R22.5. POWERTRAC DIRECCIONAL. seccion RIN 22.5 TBR', 210.00, 'Cauchos', 'POWERTRAC DIRECCIONAL', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000187', '295/80R22.5 POWERTRAC MIXTO', 'Caucho 295/80R22.5. POWERTRAC MIXTO. seccion RIN 22.5 TBR', 220.00, 'Cauchos', 'POWERTRAC MIXTO', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000188', '295/80R22.5 POWERTRAC TRACCION', 'Caucho 295/80R22.5. POWERTRAC TRACCION. seccion RIN 22.5 TBR', 238.00, 'Cauchos', 'POWERTRAC TRACCION', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000190', '315/80R22.5 SUPERMEALLIR DIRECCIONAL', 'Caucho 315/80R22.5. SUPERMEALLIR DIRECCIONAL. seccion RIN 22.5 TBR', 200.00, 'Cauchos', 'SUPERMEALLIR DIRECCIONAL', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000191', '12RR2.5 POWERTRAC MIXTO', 'Caucho 12RR2.5. POWERTRAC MIXTO. seccion RIN 22.5 TBR', 230.00, 'Cauchos', 'POWERTRAC MIXTO', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000192', '315/80R22.5 SUPERMEALLIR DIRECCIONAL', 'Caucho 315/80R22.5. SUPERMEALLIR DIRECCIONAL. seccion RIN 22.5 TBR', 200.00, 'Cauchos', 'SUPERMEALLIR DIRECCIONAL', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000193', '315/80R22.5 AMBERSTONE MIXTO', 'Caucho 315/80R22.5. AMBERSTONE MIXTO. seccion RIN 22.5 TBR', 215.00, 'Cauchos', 'AMBERSTONE MIXTO', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('NEU-000194', '315/80R22.5 POWERTRAC DIRECCIONAL', 'Caucho 315/80R22.5. POWERTRAC DIRECCIONAL. seccion RIN 22.5 TBR', 235.00, 'Cauchos', 'POWERTRAC DIRECCIONAL', 'default_product.png', 1, '2026-05-28 02:32:34', '2026-05-28 02:32:34'),
('PC0507224338', 'Producto afahcceddi', 'Desc', 21.00, 'Cat afahcceddi', 'Marca afahcceddi', 'default_product.png', 0, '2026-05-08 02:43:38', '2026-05-22 06:32:48'),
('REP-NGK-BKR6E', 'NGK bujia BKR6E', 'Bujia de encendido para motores gasolina compatibles.', 6.50, 'Repuestos', 'NGK', 'default_product.png', 0, '2026-05-27 14:10:55', '2026-05-28 02:32:34');

CREATE TABLE `promociones` (
  `id` int(11) NOT NULL,
  `nombre` varchar(200) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `tipo` varchar(30) NOT NULL DEFAULT 'puntos',
  `puntos_requeridos` int(11) DEFAULT 3,
  `recompensa` varchar(200) DEFAULT NULL,
  `imagen_tarjeta` varchar(200) DEFAULT 'default_card.png',
  `compras_minimas` int(11) DEFAULT 0,
  `ticket_minimo_usd` decimal(10,2) DEFAULT 0.00,
  `monto_total_minimo` decimal(10,2) DEFAULT 0.00,
  `producto_requerido` varchar(50) DEFAULT NULL,
  `servicio_requerido` int(11) DEFAULT NULL,
  `beneficio_tipo` varchar(30) DEFAULT 'descuento_pct',
  `beneficio_valor` decimal(10,2) DEFAULT 0.00,
  `uso_maximo_cliente` int(11) DEFAULT 0,
  `uso_maximo_total` int(11) DEFAULT 0,
  `usos_actuales` int(11) DEFAULT 0,
  `estado` tinyint(1) DEFAULT 1,
  `fecha_inicio` date DEFAULT NULL,
  `fecha_fin` date DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `proveedores` (
  `rif` varchar(20) NOT NULL,
  `rif_prefijo` varchar(2) DEFAULT NULL,
  `nombre` varchar(200) NOT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `email` varchar(150) DEFAULT NULL,
  `direccion` varchar(300) DEFAULT NULL,
  `estado` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `qr_codes` (
  `id` int(11) NOT NULL,
  `usuario_cedula` varchar(20) NOT NULL,
  `tipo` varchar(30) NOT NULL DEFAULT 'info',
  `contenido` varchar(4300) DEFAULT NULL,
  `utilidad` varchar(150) DEFAULT NULL,
  `referencia_id` int(11) DEFAULT NULL COMMENT 'ID contextual según tipo (promocion_id, servicio_id, orden_venta_id)',
  `promocion_id` int(11) DEFAULT NULL,
  `servicio_id` int(11) DEFAULT NULL,
  `orden_venta_id` int(11) DEFAULT NULL,
  `estado` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `reglas_mantenimiento` (
  `id` int(11) NOT NULL,
  `nombre` varchar(200) NOT NULL,
  `tipo_servicio` varchar(100) NOT NULL,
  `intervalo_km` int(11) DEFAULT NULL,
  `intervalo_dias` int(11) DEFAULT NULL,
  `intervalo_servicios` int(11) DEFAULT NULL,
  `tipo_combustible` varchar(20) DEFAULT 'todos',
  `tipo_vehiculo` varchar(50) DEFAULT NULL,
  `descripcion` text DEFAULT NULL,
  `activo` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `servicios` (
  `id` int(11) NOT NULL,
  `nombre` varchar(200) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `precio` decimal(10,2) NOT NULL DEFAULT 0.00,
  `duracion_estimada` varchar(50) DEFAULT NULL,
  `estado` tinyint(1) DEFAULT 1,
  `permite_filtros` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `servicio_mecanico` (
  `id` int(11) NOT NULL,
  `servicio_id` int(11) NOT NULL,
  `mecanico_cedula` varchar(20) DEFAULT NULL,
  `orden_venta_id` int(11) DEFAULT NULL,
  `fecha` timestamp NOT NULL DEFAULT current_timestamp(),
  `estado` varchar(30) NOT NULL DEFAULT 'asignado',
  `observaciones` varchar(1000) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `servicio_sucursal` (
  `servicio_id` int(11) NOT NULL,
  `sucursal_id` int(11) NOT NULL,
  `estado` tinyint(1) NOT NULL DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `stock` (
  `producto_codigo` varchar(50) NOT NULL,
  `sucursal_id` int(11) NOT NULL,
  `stock` int(11) DEFAULT 0,
  `stock_minimo` int(11) DEFAULT 5,
  `ubicacion` varchar(100) DEFAULT NULL,
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `sucursales` (
  `id` int(11) NOT NULL,
  `nombre` varchar(200) NOT NULL,
  `direccion` varchar(300) DEFAULT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `email` varchar(150) DEFAULT NULL,
  `estado` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `tarjeta_fidelidad` (
  `id` int(11) NOT NULL,
  `cliente_cedula` varchar(20) NOT NULL,
  `promocion_id` int(11) NOT NULL,
  `puntos_acumulados` int(11) DEFAULT 0,
  `canjeada` tinyint(1) DEFAULT 0,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

DELIMITER $$
CREATE TRIGGER `trg_auto_canje_tarjeta` BEFORE UPDATE ON `tarjeta_fidelidad` FOR EACH ROW BEGIN
    DECLARE v_puntos_req INT DEFAULT 0;
    IF NEW.canjeada = 0 THEN
        SELECT puntos_requeridos INTO v_puntos_req FROM promociones WHERE id = NEW.promocion_id LIMIT 1;
        IF NEW.puntos_acumulados >= v_puntos_req THEN
            SET NEW.canjeada = 1;
        END IF;
    END IF;
END
$$
DELIMITER ;

CREATE TABLE `tasas_cambio` (
  `id` int(11) NOT NULL,
  `fecha` date NOT NULL,
  `tipo` varchar(20) NOT NULL DEFAULT 'bcv',
  `monto` decimal(12,4) NOT NULL,
  `fuente` varchar(100) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `tickets_soporte` (
  `id` int(11) NOT NULL,
  `cliente_cedula` varchar(20) NOT NULL,
  `asunto` varchar(300) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `estado` varchar(30) NOT NULL DEFAULT 'abierto',
  `prioridad` varchar(20) DEFAULT 'media',
  `referencia_tipo` varchar(20) NOT NULL DEFAULT 'general',
  `referencia_id` varchar(50) DEFAULT NULL,
  `asignado_a` varchar(20) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `ticket_respuestas` (
  `id` int(11) NOT NULL,
  `ticket_id` int(11) NOT NULL,
  `autor_id` int(11) NOT NULL,
  `autor_tipo` varchar(20) NOT NULL,
  `mensaje` text NOT NULL,
  `adjunto_url` varchar(255) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `vehiculos` (
  `cliente_cedula` varchar(20) NOT NULL,
  `marca` varchar(100) NOT NULL,
  `modelo` varchar(100) NOT NULL,
  `anio` smallint(6) DEFAULT NULL,
  `placa` varchar(20) NOT NULL,
  `color` varchar(50) DEFAULT NULL,
  `tipo_vehiculo` varchar(50) DEFAULT NULL,
  `tipo_combustible` varchar(20) DEFAULT 'gasolina',
  `kilometraje_actual` int(11) DEFAULT 0,
  `km_ultimo_servicio` int(11) DEFAULT 0,
  `fecha_ultimo_servicio` date DEFAULT NULL,
  `aceite_usado` varchar(200) DEFAULT NULL,
  `filtros_info` text DEFAULT NULL,
  `refrigerante_info` varchar(200) DEFAULT NULL,
  `observaciones` text DEFAULT NULL,
  `cauchos_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`cauchos_json`)),
  `titulo_vehiculo` varchar(255) DEFAULT NULL,
  `estado` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


ALTER TABLE `bitacora_vehiculo`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_bitacora_vehiculo_fecha` (`vehiculo_placa`,`fecha`),
  ADD KEY `fk_bitacora_servicio_mecanico` (`servicio_mecanico_id`);

ALTER TABLE `carrito`
  ADD PRIMARY KEY (`id`),
  ADD KEY `cliente_cedula` (`cliente_cedula`),
  ADD KEY `fk_carrito_producto` (`producto_codigo`),
  ADD KEY `fk_carrito_servicio` (`servicio_id`);

ALTER TABLE `categorias`
  ADD PRIMARY KEY (`nombre`);

ALTER TABLE `clientes`
  ADD PRIMARY KEY (`cedula`),
  ADD KEY `fk_clientes_usuario` (`usuario_id`);

ALTER TABLE `comisiones_mecanico`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_comision_servicio_mecanico` (`servicio_mecanico_id`);

ALTER TABLE `comprobantes_pago`
  ADD PRIMARY KEY (`id`),
  ADD KEY `orden_venta_id` (`orden_venta_id`),
  ADD KEY `estado` (`estado`),
  ADD KEY `fk_comprobantes_pago_revisor` (`revisado_por`);

ALTER TABLE `configuracion`
  ADD PRIMARY KEY (`clave`);

ALTER TABLE `consumo_combustible`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_consumo_vehiculo_fecha` (`vehiculo_placa`,`fecha`);

ALTER TABLE `cotizaciones`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_cotizacion_cliente` (`cliente_cedula`,`estado`),
  ADD KEY `fk_cotizacion_tasa` (`tasa_cambio_id`);

ALTER TABLE `cotizacion_items`
  ADD PRIMARY KEY (`id`),
  ADD KEY `cotizacion_id` (`cotizacion_id`),
  ADD KEY `fk_cotizacion_item_producto` (`producto_codigo`),
  ADD KEY `fk_cotizacion_item_servicio` (`servicio_id`);

ALTER TABLE `detalle_orden_compra`
  ADD PRIMARY KEY (`id`),
  ADD KEY `orden_compra_id` (`orden_compra_id`),
  ADD KEY `producto_codigo` (`producto_codigo`);

ALTER TABLE `detalle_orden_venta_productos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `orden_id` (`orden_id`),
  ADD KEY `producto_codigo` (`producto_codigo`);

ALTER TABLE `detalle_orden_venta_servicios`
  ADD PRIMARY KEY (`id`),
  ADD KEY `orden_id` (`orden_id`),
  ADD KEY `servicio_id` (`servicio_id`);

ALTER TABLE `empresas`
  ADD PRIMARY KEY (`cliente_cedula`),
  ADD UNIQUE KEY `rif` (`rif`);

ALTER TABLE `historial_puntos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `tarjeta_id` (`tarjeta_id`),
  ADD KEY `tipo` (`tipo`);

ALTER TABLE `mantenimientos_programados`
  ADD PRIMARY KEY (`id`),
  ADD KEY `regla_id` (`regla_id`),
  ADD KEY `idx_mant_vehiculo` (`estado`),
  ADD KEY `idx_mant_vehiculo_estado` (`vehiculo_placa`,`estado`);

ALTER TABLE `marcas`
  ADD PRIMARY KEY (`nombre`);

ALTER TABLE `mecanicos`
  ADD PRIMARY KEY (`cedula`),
  ADD KEY `fk_mecanicos_usuario` (`usuario_id`);

ALTER TABLE `metodos_pago`
  ADD PRIMARY KEY (`id`);

ALTER TABLE `notificaciones`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_notif_usuario_leida` (`usuario_id`,`leida`,`created_at`),
  ADD KEY `idx_notif_cliente_leida` (`cliente_cedula`,`leida`,`created_at`);

ALTER TABLE `ordenes_compra`
  ADD PRIMARY KEY (`id`),
  ADD KEY `proveedor_rif` (`proveedor_rif`),
  ADD KEY `sucursal_id` (`sucursal_id`);

ALTER TABLE `ordenes_venta`
  ADD PRIMARY KEY (`id`),
  ADD KEY `sucursal_id` (`sucursal_id`),
  ADD KEY `estado` (`estado`),
  ADD KEY `idx_ordenes_venta_cliente` (`cliente_cedula`),
  ADD KEY `fk_ordenes_venta_metodo_pago` (`metodo_pago_id`);

ALTER TABLE `productos`
  ADD PRIMARY KEY (`codigo`),
  ADD KEY `marca` (`marca`),
  ADD KEY `fk_productos_categoria` (`categoria`);

ALTER TABLE `promociones`
  ADD PRIMARY KEY (`id`),
  ADD KEY `tipo` (`tipo`);

ALTER TABLE `proveedores`
  ADD PRIMARY KEY (`rif`);

ALTER TABLE `qr_codes`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_qr_referencia` (`tipo`,`referencia_id`),
  ADD KEY `fk_qr_promocion` (`promocion_id`),
  ADD KEY `fk_qr_servicio` (`servicio_id`),
  ADD KEY `fk_qr_orden` (`orden_venta_id`),
  ADD KEY `fk_qr_usuario` (`usuario_cedula`);

ALTER TABLE `reglas_mantenimiento`
  ADD PRIMARY KEY (`id`);

ALTER TABLE `servicios`
  ADD PRIMARY KEY (`id`);

ALTER TABLE `servicio_mecanico`
  ADD PRIMARY KEY (`id`),
  ADD KEY `servicio_id` (`servicio_id`),
  ADD KEY `mecanico_cedula` (`mecanico_cedula`),
  ADD KEY `orden_venta_id` (`orden_venta_id`),
  ADD KEY `estado` (`estado`);

ALTER TABLE `servicio_sucursal`
  ADD PRIMARY KEY (`servicio_id`,`sucursal_id`),
  ADD KEY `sucursal_id` (`sucursal_id`);

ALTER TABLE `stock`
  ADD PRIMARY KEY (`producto_codigo`,`sucursal_id`),
  ADD KEY `sucursal_id` (`sucursal_id`);

ALTER TABLE `sucursales`
  ADD PRIMARY KEY (`id`);

ALTER TABLE `tarjeta_fidelidad`
  ADD PRIMARY KEY (`id`),
  ADD KEY `cliente_cedula` (`cliente_cedula`),
  ADD KEY `promocion_id` (`promocion_id`);

ALTER TABLE `tasas_cambio`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_tasas_cambio_fecha_tipo` (`fecha`,`tipo`);

ALTER TABLE `tickets_soporte`
  ADD PRIMARY KEY (`id`),
  ADD KEY `asignado_a` (`asignado_a`),
  ADD KEY `idx_ticket_cliente` (`cliente_cedula`);

ALTER TABLE `ticket_respuestas`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ticket_id` (`ticket_id`);

ALTER TABLE `vehiculos`
  ADD PRIMARY KEY (`placa`),
  ADD KEY `idx_vehiculo_cliente` (`cliente_cedula`);

ALTER TABLE `bitacora_vehiculo`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `carrito`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `comisiones_mecanico`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `comprobantes_pago`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `consumo_combustible`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `cotizaciones`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `cotizacion_items`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `detalle_orden_compra`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `detalle_orden_venta_productos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `detalle_orden_venta_servicios`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `historial_puntos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `mantenimientos_programados`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `metodos_pago`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `notificaciones`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `ordenes_compra`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `ordenes_venta`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `promociones`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `qr_codes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `reglas_mantenimiento`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `servicios`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `servicio_mecanico`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `sucursales`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `tarjeta_fidelidad`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `tasas_cambio`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `tickets_soporte`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `ticket_respuestas`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `bitacora_vehiculo`
  ADD CONSTRAINT `fk_bitacora_servicio_mecanico` FOREIGN KEY (`servicio_mecanico_id`) REFERENCES `servicio_mecanico` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_bitacora_vehiculo` FOREIGN KEY (`vehiculo_placa`) REFERENCES `vehiculos` (`placa`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `carrito`
  ADD CONSTRAINT `carrito_ibfk_1` FOREIGN KEY (`cliente_cedula`) REFERENCES `clientes` (`cedula`) ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_carrito_producto` FOREIGN KEY (`producto_codigo`) REFERENCES `productos` (`codigo`) ON DELETE SET NULL ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_carrito_servicio` FOREIGN KEY (`servicio_id`) REFERENCES `servicios` (`id`) ON DELETE SET NULL;

ALTER TABLE `clientes`
  ADD CONSTRAINT `fk_clientes_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `db_mantenimiento`.`usuarios` (`id`) ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE `comisiones_mecanico`
  ADD CONSTRAINT `comisiones_mecanico_ibfk_2` FOREIGN KEY (`servicio_mecanico_id`) REFERENCES `servicio_mecanico` (`id`);

ALTER TABLE `comprobantes_pago`
  ADD CONSTRAINT `comprobantes_pago_ibfk_1` FOREIGN KEY (`orden_venta_id`) REFERENCES `ordenes_venta` (`id`) ON DELETE CASCADE;

ALTER TABLE `consumo_combustible`
  ADD CONSTRAINT `fk_consumo_vehiculo` FOREIGN KEY (`vehiculo_placa`) REFERENCES `vehiculos` (`placa`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `cotizaciones`
  ADD CONSTRAINT `cotizaciones_ibfk_1` FOREIGN KEY (`cliente_cedula`) REFERENCES `clientes` (`cedula`) ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_cotizacion_tasa` FOREIGN KEY (`tasa_cambio_id`) REFERENCES `tasas_cambio` (`id`) ON DELETE SET NULL;

ALTER TABLE `cotizacion_items`
  ADD CONSTRAINT `cotizacion_items_ibfk_1` FOREIGN KEY (`cotizacion_id`) REFERENCES `cotizaciones` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_cotizacion_item_producto` FOREIGN KEY (`producto_codigo`) REFERENCES `productos` (`codigo`) ON DELETE SET NULL ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_cotizacion_item_servicio` FOREIGN KEY (`servicio_id`) REFERENCES `servicios` (`id`) ON DELETE SET NULL;

ALTER TABLE `detalle_orden_compra`
  ADD CONSTRAINT `detalle_orden_compra_ibfk_1` FOREIGN KEY (`orden_compra_id`) REFERENCES `ordenes_compra` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `detalle_orden_compra_ibfk_2` FOREIGN KEY (`producto_codigo`) REFERENCES `productos` (`codigo`) ON UPDATE CASCADE;

ALTER TABLE `detalle_orden_venta_productos`
  ADD CONSTRAINT `detalle_orden_venta_productos_ibfk_1` FOREIGN KEY (`orden_id`) REFERENCES `ordenes_venta` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `detalle_orden_venta_productos_ibfk_2` FOREIGN KEY (`producto_codigo`) REFERENCES `productos` (`codigo`) ON UPDATE CASCADE;

ALTER TABLE `detalle_orden_venta_servicios`
  ADD CONSTRAINT `detalle_orden_venta_servicios_ibfk_1` FOREIGN KEY (`orden_id`) REFERENCES `ordenes_venta` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `detalle_orden_venta_servicios_ibfk_2` FOREIGN KEY (`servicio_id`) REFERENCES `servicios` (`id`);

ALTER TABLE `empresas`
  ADD CONSTRAINT `fk_empresas_cliente` FOREIGN KEY (`cliente_cedula`) REFERENCES `clientes` (`cedula`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `historial_puntos`
  ADD CONSTRAINT `historial_puntos_ibfk_1` FOREIGN KEY (`tarjeta_id`) REFERENCES `tarjeta_fidelidad` (`id`) ON DELETE CASCADE;

ALTER TABLE `mantenimientos_programados`
  ADD CONSTRAINT `fk_mantenimientos_vehiculo` FOREIGN KEY (`vehiculo_placa`) REFERENCES `vehiculos` (`placa`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `mantenimientos_programados_ibfk_2` FOREIGN KEY (`regla_id`) REFERENCES `reglas_mantenimiento` (`id`) ON DELETE SET NULL;

ALTER TABLE `mecanicos`
  ADD CONSTRAINT `fk_mecanicos_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `db_mantenimiento`.`usuarios` (`id`) ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE `notificaciones`
  ADD CONSTRAINT `fk_notificaciones_cliente` FOREIGN KEY (`cliente_cedula`) REFERENCES `clientes` (`cedula`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `ordenes_compra`
  ADD CONSTRAINT `ordenes_compra_ibfk_1` FOREIGN KEY (`proveedor_rif`) REFERENCES `proveedores` (`rif`) ON UPDATE CASCADE,
  ADD CONSTRAINT `ordenes_compra_ibfk_2` FOREIGN KEY (`sucursal_id`) REFERENCES `sucursales` (`id`);

ALTER TABLE `ordenes_venta`
  ADD CONSTRAINT `fk_ordenes_venta_metodo_pago` FOREIGN KEY (`metodo_pago_id`) REFERENCES `metodos_pago` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `ordenes_venta_ibfk_1` FOREIGN KEY (`cliente_cedula`) REFERENCES `clientes` (`cedula`) ON UPDATE CASCADE,
  ADD CONSTRAINT `ordenes_venta_ibfk_2` FOREIGN KEY (`sucursal_id`) REFERENCES `sucursales` (`id`) ON DELETE SET NULL;

ALTER TABLE `productos`
  ADD CONSTRAINT `fk_productos_categoria` FOREIGN KEY (`categoria`) REFERENCES `categorias` (`nombre`) ON DELETE SET NULL ON UPDATE CASCADE,
  ADD CONSTRAINT `productos_ibfk_2` FOREIGN KEY (`marca`) REFERENCES `marcas` (`nombre`) ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE `qr_codes`
  ADD CONSTRAINT `fk_qr_orden` FOREIGN KEY (`orden_venta_id`) REFERENCES `ordenes_venta` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_qr_promocion` FOREIGN KEY (`promocion_id`) REFERENCES `promociones` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_qr_servicio` FOREIGN KEY (`servicio_id`) REFERENCES `servicios` (`id`) ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE `servicio_mecanico`
  ADD CONSTRAINT `servicio_mecanico_ibfk_1` FOREIGN KEY (`servicio_id`) REFERENCES `servicios` (`id`),
  ADD CONSTRAINT `servicio_mecanico_ibfk_2` FOREIGN KEY (`mecanico_cedula`) REFERENCES `mecanicos` (`cedula`) ON UPDATE CASCADE,
  ADD CONSTRAINT `servicio_mecanico_ibfk_3` FOREIGN KEY (`orden_venta_id`) REFERENCES `ordenes_venta` (`id`);

ALTER TABLE `servicio_sucursal`
  ADD CONSTRAINT `servicio_sucursal_ibfk_1` FOREIGN KEY (`servicio_id`) REFERENCES `servicios` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `servicio_sucursal_ibfk_2` FOREIGN KEY (`sucursal_id`) REFERENCES `sucursales` (`id`) ON DELETE CASCADE;

ALTER TABLE `stock`
  ADD CONSTRAINT `stock_ibfk_1` FOREIGN KEY (`producto_codigo`) REFERENCES `productos` (`codigo`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `stock_ibfk_2` FOREIGN KEY (`sucursal_id`) REFERENCES `sucursales` (`id`);

ALTER TABLE `tarjeta_fidelidad`
  ADD CONSTRAINT `tarjeta_fidelidad_ibfk_1` FOREIGN KEY (`cliente_cedula`) REFERENCES `clientes` (`cedula`) ON UPDATE CASCADE,
  ADD CONSTRAINT `tarjeta_fidelidad_ibfk_2` FOREIGN KEY (`promocion_id`) REFERENCES `promociones` (`id`);

ALTER TABLE `tickets_soporte`
  ADD CONSTRAINT `tickets_soporte_ibfk_1` FOREIGN KEY (`cliente_cedula`) REFERENCES `clientes` (`cedula`) ON UPDATE CASCADE,
  ADD CONSTRAINT `tickets_soporte_ibfk_4` FOREIGN KEY (`asignado_a`) REFERENCES `mecanicos` (`cedula`) ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE `ticket_respuestas`
  ADD CONSTRAINT `ticket_respuestas_ibfk_1` FOREIGN KEY (`ticket_id`) REFERENCES `tickets_soporte` (`id`) ON DELETE CASCADE;

ALTER TABLE `vehiculos`
  ADD CONSTRAINT `vehiculos_ibfk_1` FOREIGN KEY (`cliente_cedula`) REFERENCES `clientes` (`cedula`) ON UPDATE CASCADE;
COMMIT;

SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT;
SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS;
SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION;
