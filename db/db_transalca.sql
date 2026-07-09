
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


DROP TABLE IF EXISTS `bitacora_prediccion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `bitacora_prediccion` (
  `id_bitacora_prediccion` int(11) NOT NULL AUTO_INCREMENT,
  `vehiculo_placa` varchar(20) NOT NULL,
  `tipo_prediccion` varchar(50) NOT NULL,
  `referencia_detalle` varchar(255) DEFAULT NULL,
  `fecha_base` date DEFAULT NULL,
  `fecha_estimada` date NOT NULL,
  `base_calculo` varchar(255) DEFAULT NULL,
  `prioridad_prediccion` varchar(20) DEFAULT 'media',
  `estado` varchar(20) DEFAULT 'activa',
  `notificado` tinyint(1) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id_bitacora_prediccion`),
  UNIQUE KEY `uq_prediccion` (`vehiculo_placa`,`tipo_prediccion`),
  KEY `idx_prediccion_fecha` (`fecha_estimada`,`estado`),
  CONSTRAINT `fk_prediccion_vehiculo` FOREIGN KEY (`vehiculo_placa`) REFERENCES `vehiculos` (`placa_vehiculo`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `bitacora_prediccion` WRITE;
/*!40000 ALTER TABLE `bitacora_prediccion` DISABLE KEYS */;
INSERT INTO `bitacora_prediccion` VALUES (1,'AB123CD','servicio_general','Servicio general','2026-06-11','2026-12-08','Ultimo servicio 2026-06-11 + 6 meses; 2 servicios en historial','baja','activa',0,'2026-06-11 03:39:05','2026-06-11 06:15:22'),(2,'DADADA','servicio_general','Servicio general','2026-06-10','2026-12-07','Ultimo servicio 2026-06-10 + 6 meses; 1 servicios en historial','baja','activa',0,'2026-06-11 03:39:05','2026-06-11 03:39:05'),(3,'AB123CD','bateria','600 AMP EXTREME 36DLM700 (36MR) x1','2026-06-11','2028-05-31','Ultimo registro 2026-06-11 + 24 meses de vida util estimada (baterias)','baja','activa',0,'2026-06-11 06:16:10','2026-06-11 06:16:10');
/*!40000 ALTER TABLE `bitacora_prediccion` ENABLE KEYS */;
UNLOCK TABLES;


DROP TABLE IF EXISTS `bitacora_vehiculo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `bitacora_vehiculo` (
  `id_bitacora_vehiculo` int(11) NOT NULL AUTO_INCREMENT,
  `descripcion_bitacora` text DEFAULT NULL,
  `kilometraje` int(11) DEFAULT NULL,
  `aceite_usado` varchar(200) DEFAULT NULL,
  `filtros_usados` text DEFAULT NULL,
  `refrigerante_usado` varchar(200) DEFAULT NULL,
  `productos_usados` text DEFAULT NULL,
  `cauchos_usados` text DEFAULT NULL,
  `proximo_mantenimiento` text DEFAULT NULL,
  `observaciones_bitacora` text DEFAULT NULL,
  `fecha_bitacora` timestamp NOT NULL DEFAULT current_timestamp(),
  `vehiculo_placa` varchar(20) NOT NULL,
  `servicio_mecanico_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_bitacora_vehiculo`),
  KEY `idx_bitacora_vehiculo_fecha` (`vehiculo_placa`,`fecha_bitacora`),
  KEY `fk_bitacora_servicio_mecanico` (`servicio_mecanico_id`),
  CONSTRAINT `fk_bitacora_servicio_mecanico` FOREIGN KEY (`servicio_mecanico_id`) REFERENCES `servicio_mecanico` (`id_servicio_mecanico`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_bitacora_vehiculo` FOREIGN KEY (`vehiculo_placa`) REFERENCES `vehiculos` (`placa_vehiculo`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `bitacora_vehiculo` WRITE;
/*!40000 ALTER TABLE `bitacora_vehiculo` DISABLE KEYS */;
INSERT INTO `bitacora_vehiculo` VALUES (1,'Servicio realizado: ALINEACION CAMIONETA PEQ.',0,NULL,NULL,NULL,'','',NULL,NULL,'2026-06-02 22:13:00','AB123CD',5),(2,'Servicio realizado: ALINEACION CAMION (22.5 )',3333,NULL,NULL,NULL,'','',NULL,NULL,'2026-06-10 21:09:00','DADADA',6),(4,'Servicio realizado: ALINEACION CAMION (22.5 )',0,NULL,NULL,NULL,'600 AMP EXTREME 36DLM700 (36MR) x1','',NULL,NULL,'2026-06-11 06:15:22','AB123CD',7);
/*!40000 ALTER TABLE `bitacora_vehiculo` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_bitacora_vehiculo_insert` AFTER INSERT ON bitacora_vehiculo FOR EACH ROW BEGIN
        INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (COALESCE(@current_usuario_id, 1), 'CREAR', 'VEHICULOS', CONCAT('Registro de servicio para placa: ', NEW.vehiculo_placa), COALESCE(@current_ip, '127.0.0.1'));
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;


DROP TABLE IF EXISTS `carrito_compra`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `carrito_compra` (
  `id_carrito_compra` int(11) NOT NULL AUTO_INCREMENT,
  `cliente_cedula` varchar(20) NOT NULL,
  `producto_codigo` varchar(50) DEFAULT NULL,
  `servicio_id` int(11) DEFAULT NULL,
  `tipo_carrito` tinyint(4) NOT NULL DEFAULT 0,
  `cantidad_carrito` int(11) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_carrito_compra`),
  KEY `cliente_cedula` (`cliente_cedula`),
  KEY `fk_carrito_producto` (`producto_codigo`),
  KEY `fk_carrito_servicio` (`servicio_id`),
  CONSTRAINT `carrito_ibfk_1` FOREIGN KEY (`cliente_cedula`) REFERENCES `cliente` (`identificador_cliente`) ON UPDATE CASCADE,
  CONSTRAINT `fk_carrito_producto` FOREIGN KEY (`producto_codigo`) REFERENCES `productos` (`codigo`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_carrito_servicio` FOREIGN KEY (`servicio_id`) REFERENCES `servicios` (`id_servicio`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `carrito_compra` WRITE;
/*!40000 ALTER TABLE `carrito_compra` DISABLE KEYS */;
/*!40000 ALTER TABLE `carrito_compra` ENABLE KEYS */;
UNLOCK TABLES;


DROP TABLE IF EXISTS `categorias`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `categorias` (
  `nombre_categoria` varchar(150) NOT NULL,
  `descripcion_categoria` varchar(500) DEFAULT NULL,
  `imagen_categoria` varchar(200) DEFAULT 'product-default-parts.png',
  `estado` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`nombre_categoria`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `categorias` WRITE;
/*!40000 ALTER TABLE `categorias` DISABLE KEYS */;
INSERT INTO `categorias` VALUES ('Baterias','Baterias para vehiculos','product-default-battery.png',1,'2026-04-30 04:18:56'),('Cat afahcceddi','Prueba','product-default-parts.png',0,'2026-05-08 02:43:38'),('Cauchos','Neumaticos para todo tipo de vehiculos','product-default-tire.png',1,'2026-04-30 04:18:56'),('Combos','Combos de aceite, filtro y servicio','product-default-parts.png',1,'2026-05-28 02:32:34'),('Filtros','Filtros de aire, aceite y combustible','product-default-filter.png',1,'2026-04-30 04:18:56'),('Frenos','Pastillas, discos y sistemas de frenos','product-default-parts.png',1,'2026-04-30 04:18:56'),('Lubricantes','Aceites y lubricantes para motor y transmision','product-default-lubricant.png',1,'2026-04-30 04:18:56'),('Repuestos','Repuestos y autopartes en general','product-default-parts.png',1,'2026-04-30 04:18:56'),('TestCat0507224100','Prueba','product-default-parts.png',0,'2026-05-08 02:41:00');
/*!40000 ALTER TABLE `categorias` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_categorias_insert` AFTER INSERT ON categorias FOR EACH ROW BEGIN
        INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (COALESCE(@current_usuario_id, 1), 'CREAR', 'CATEGORIAS', CONCAT('Categoria creada: ', NEW.nombre_categoria), COALESCE(@current_ip, '127.0.0.1'));
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_categorias_update` AFTER UPDATE ON categorias FOR EACH ROW BEGIN
        IF OLD.estado = 1 AND NEW.estado = 0 THEN
            INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
            VALUES (COALESCE(@current_usuario_id, 1), 'ELIMINAR', 'CATEGORIAS', CONCAT('Categoria desactivada: ', NEW.nombre_categoria), COALESCE(@current_ip, '127.0.0.1'));
        ELSE
            INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
            VALUES (COALESCE(@current_usuario_id, 1), 'MODIFICAR', 'CATEGORIAS', CONCAT('Categoria modificada: ', OLD.nombre_categoria, ' -> ', NEW.nombre_categoria), COALESCE(@current_ip, '127.0.0.1'));
        END IF;
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;


DROP TABLE IF EXISTS `cliente`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cliente` (
  `id_cliente` int(11) NOT NULL AUTO_INCREMENT,
  `nombre_cliente` varchar(200) NOT NULL,
  `correo_cliente` varchar(150) DEFAULT NULL,
  `identificador_cliente` varchar(20) NOT NULL,
  `telefono_cliente` varchar(20) DEFAULT NULL,
  `direccion_cliente` varchar(300) DEFAULT NULL,
  `tipo_cliente` varchar(20) NOT NULL DEFAULT 'natural',
  `estado` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id_cliente`),
  UNIQUE KEY `uq_cliente_identificador` (`identificador_cliente`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `cliente` WRITE;
/*!40000 ALTER TABLE `cliente` DISABLE KEYS */;
INSERT INTO `cliente` VALUES (1,'Orlando Barrientos','orlandoabarrientos@gmail.com','30396029','04122397209','','natural',1,'2026-05-01 01:36:53','2026-05-28 14:51:31'),(2,'dede dede','deded@gmail.com','314141341','34141414','dqada','natural',1,'2026-04-30 23:44:31','2026-05-28 14:51:31'),(3,'dede dede','deded@gmail.com','dede','34141414','dede','natural',1,'2026-04-30 23:45:04','2026-05-28 14:51:31'),(4,'cxxgx','business@tanqueteodigital.com','J-55656666-5','04122397209','cgfcgfxgx','juridica',1,'2026-05-29 07:01:17','2026-05-29 07:01:17'),(5,'Admin Sistema','admin@transalca.com','V-00000000','0424-0000000','Oficina Principal','natural',1,'2026-05-18 04:29:47','2026-05-28 06:14:49'),(6,'Carlos Prueba','cli0507224100@mail.com','V-07224100','04121234567','Dir cliente','natural',1,'2026-05-08 02:41:00','2026-05-28 06:14:49'),(7,'Carlos Cliente','c0507224338@mail.com','V-07224350','04121234567','Dir cliente','natural',0,'2026-05-08 02:43:38','2026-05-28 06:14:49'),(8,'dede dede','fderf@gmail.com','V-3131333','04122222222',NULL,'natural',1,'2026-06-07 17:04:20','2026-06-07 17:04:20'),(9,'dede dede','business@tanqueteodigital.com','V-31423434','04122397209',NULL,'natural',1,'2026-06-07 16:54:48','2026-06-07 16:54:48');
/*!40000 ALTER TABLE `cliente` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_bitacora_cliente_insert AFTER INSERT ON cliente FOR EACH ROW BEGIN INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip) VALUES (COALESCE(@current_usuario_id, 1), 'CREAR', 'CLIENTES', CONCAT('Cliente registrado: ', NEW.identificador_cliente), COALESCE(@current_ip, '127.0.0.1')); END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_bitacora_cliente_update AFTER UPDATE ON cliente FOR EACH ROW BEGIN INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip) VALUES (COALESCE(@current_usuario_id, 1), 'MODIFICAR', 'CLIENTES', CONCAT('Cliente modificado: ', NEW.identificador_cliente), COALESCE(@current_ip, '127.0.0.1')); END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;


DROP TABLE IF EXISTS `cliente_juridico`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cliente_juridico` (
  `id_juridica` int(11) NOT NULL AUTO_INCREMENT,
  `id_cliente` int(11) NOT NULL,
  `sector` varchar(150) DEFAULT NULL,
  `limite_credito` decimal(10,2) DEFAULT 0.00,
  `dias_credito` int(11) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id_juridica`),
  UNIQUE KEY `uq_juridica_cliente` (`id_cliente`),
  CONSTRAINT `fk_juridica_cliente` FOREIGN KEY (`id_cliente`) REFERENCES `cliente` (`id_cliente`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `cliente_juridico` WRITE;
/*!40000 ALTER TABLE `cliente_juridico` DISABLE KEYS */;
INSERT INTO `cliente_juridico` VALUES (1,4,'cycy',0.00,0,'2026-05-29 07:01:17','2026-05-29 07:01:17');
/*!40000 ALTER TABLE `cliente_juridico` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_bitacora_juridica_insert AFTER INSERT ON cliente_juridico FOR EACH ROW BEGIN INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip) VALUES (COALESCE(@current_usuario_id, 1), 'CREAR', 'EMPRESAS', CONCAT('Empresa registrada id cliente: ', NEW.id_cliente), COALESCE(@current_ip, '127.0.0.1')); END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_bitacora_juridica_update AFTER UPDATE ON cliente_juridico FOR EACH ROW BEGIN INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip) VALUES (COALESCE(@current_usuario_id, 1), 'MODIFICAR', 'EMPRESAS', CONCAT('Empresa modificada id cliente: ', NEW.id_cliente), COALESCE(@current_ip, '127.0.0.1')); END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;


DROP TABLE IF EXISTS `cliente_natural`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cliente_natural` (
  `id_natural` int(11) NOT NULL AUTO_INCREMENT,
  `id_cliente` int(11) NOT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `origen_registro` varchar(20) DEFAULT 'cliente',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id_natural`),
  UNIQUE KEY `uq_natural_cliente` (`id_cliente`),
  KEY `fk_natural_usuario` (`usuario_id`),
  CONSTRAINT `fk_natural_cliente` FOREIGN KEY (`id_cliente`) REFERENCES `cliente` (`id_cliente`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_natural_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `db_mantenimiento`.`usuarios` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `cliente_natural` WRITE;
/*!40000 ALTER TABLE `cliente_natural` DISABLE KEYS */;
INSERT INTO `cliente_natural` VALUES (1,1,4,'cliente','2026-05-01 01:36:53','2026-05-28 14:51:31'),(2,2,NULL,'admin','2026-04-30 23:44:31','2026-05-28 14:51:31'),(3,3,NULL,'admin','2026-04-30 23:45:04','2026-05-28 14:51:31'),(4,5,NULL,'cliente','2026-05-18 04:29:47','2026-05-28 06:14:49'),(5,6,NULL,'admin','2026-05-08 02:41:00','2026-05-28 06:14:49'),(6,7,NULL,'admin','2026-05-08 02:43:38','2026-05-28 06:14:49'),(7,8,NULL,'admin','2026-06-07 17:04:20','2026-06-07 17:04:20'),(8,9,NULL,'admin','2026-06-07 16:54:48','2026-06-07 16:54:48');
/*!40000 ALTER TABLE `cliente_natural` ENABLE KEYS */;
UNLOCK TABLES;


DROP TABLE IF EXISTS `cliente_vehiculo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cliente_vehiculo` (
  `id_cliente_vehiculo` int(11) NOT NULL AUTO_INCREMENT,
  `cliente_cedula` varchar(20) NOT NULL,
  `vehiculo_placa` varchar(20) NOT NULL,
  `estado` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id_cliente_vehiculo`),
  UNIQUE KEY `uk_cliente_vehiculo` (`cliente_cedula`,`vehiculo_placa`),
  KEY `fk_cv_vehiculo` (`vehiculo_placa`),
  CONSTRAINT `fk_cv_cliente` FOREIGN KEY (`cliente_cedula`) REFERENCES `cliente` (`identificador_cliente`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_cv_vehiculo` FOREIGN KEY (`vehiculo_placa`) REFERENCES `vehiculos` (`placa_vehiculo`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `cliente_vehiculo` WRITE;
/*!40000 ALTER TABLE `cliente_vehiculo` DISABLE KEYS */;
INSERT INTO `cliente_vehiculo` VALUES (1,'dede','AB123CD',1,'2026-05-01 01:04:53','2026-05-01 01:04:53'),(2,'V-07224350','AB4338CD',1,'2026-05-08 02:43:38','2026-05-08 02:43:38'),(8,'V-00000000','DADADA',1,'2026-06-10 22:24:01','2026-06-10 22:24:01'),(9,'V-00000000','DEDED',1,'2026-06-10 22:24:32','2026-06-10 22:24:32');
/*!40000 ALTER TABLE `cliente_vehiculo` ENABLE KEYS */;
UNLOCK TABLES;


DROP TABLE IF EXISTS `comisiones_mecanico`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `comisiones_mecanico` (
  `servicio_mecanico_id` int(11) NOT NULL,
  `precio_servicio_comision` decimal(10,2) NOT NULL,
  `porcentaje_comision` decimal(5,2) DEFAULT 30.00,
  PRIMARY KEY (`servicio_mecanico_id`),
  CONSTRAINT `comisiones_mecanico_ibfk_2` FOREIGN KEY (`servicio_mecanico_id`) REFERENCES `servicio_mecanico` (`id_servicio_mecanico`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `comisiones_mecanico` WRITE;
/*!40000 ALTER TABLE `comisiones_mecanico` DISABLE KEYS */;
INSERT INTO `comisiones_mecanico` VALUES (5,10.50,30.00),(7,20.00,25.00);
/*!40000 ALTER TABLE `comisiones_mecanico` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_bitacora_comisiones_mecanico_insert AFTER INSERT ON comisiones_mecanico FOR EACH ROW BEGIN INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip) VALUES (COALESCE(@current_usuario_id, 1), 'CREAR', 'COMISIONES', CONCAT('Comision registrada servicio-mecanico: ', NEW.servicio_mecanico_id), COALESCE(@current_ip, '127.0.0.1')); END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_bitacora_comisiones_mecanico_update AFTER UPDATE ON comisiones_mecanico FOR EACH ROW BEGIN INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip) VALUES (COALESCE(@current_usuario_id, 1), 'MODIFICAR', 'COMISIONES', CONCAT('Comision actualizada servicio-mecanico: ', NEW.servicio_mecanico_id), COALESCE(@current_ip, '127.0.0.1')); END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;


DROP TABLE IF EXISTS `comprobantes_pago`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `comprobantes_pago` (
  `id_comprobante_pago` int(11) NOT NULL AUTO_INCREMENT,
  `orden_venta_id` int(11) NOT NULL,
  `imagen_url` varchar(255) NOT NULL,
  `estado` varchar(30) NOT NULL DEFAULT 'pendiente',
  `fecha_comprobante` timestamp NOT NULL DEFAULT current_timestamp(),
  `observaciones` varchar(1000) DEFAULT NULL,
  PRIMARY KEY (`id_comprobante_pago`),
  KEY `orden_venta_id` (`orden_venta_id`),
  KEY `estado` (`estado`),
  KEY `idx_comprobante_estado_fecha` (`estado`,`fecha_comprobante`),
  CONSTRAINT `comprobantes_pago_ibfk_1` FOREIGN KEY (`orden_venta_id`) REFERENCES `ordenes_venta` (`id_orden_venta`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `comprobantes_pago` WRITE;
/*!40000 ALTER TABLE `comprobantes_pago` DISABLE KEYS */;
INSERT INTO `comprobantes_pago` VALUES (1,1,'comp_V-00000000_hero.png','verificado','2026-05-18 04:33:01',NULL),(2,2,'comp_V-00000000_hero.png','rechazado','2026-05-21 06:08:02','onon'),(3,9,'comp_V-00000000_jugo_parchita.webp','rechazado','2026-06-03 15:39:55','poruq eis'),(4,11,'comp_V-00000000_CocaCola_de_botella.jpg','verificado','2026-06-08 21:17:57',NULL),(5,12,'comp_V-00000000_cocacola_1l.jpg','pendiente','2026-06-10 21:09:31',NULL),(6,13,'test.png','verificado','2026-06-11 06:14:43',NULL);
/*!40000 ALTER TABLE `comprobantes_pago` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_bitacora_comprobantes_pago_insert AFTER INSERT ON comprobantes_pago FOR EACH ROW BEGIN INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip) VALUES (COALESCE(@current_usuario_id, 1), 'CREAR', 'PAGOS', CONCAT('Comprobante de pago registrado orden ID: ', NEW.orden_venta_id), COALESCE(@current_ip, '127.0.0.1')); END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_bitacora_comprobantes_pago_update AFTER UPDATE ON comprobantes_pago FOR EACH ROW BEGIN INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip) VALUES (COALESCE(@current_usuario_id, 1), CASE WHEN NEW.estado='verificado' THEN 'aceptado' WHEN NEW.estado='rechazado' THEN 'rechazado' ELSE 'MODIFICAR' END, 'PAGOS', CONCAT('Comprobante de pago orden ID: ', NEW.orden_venta_id, ' Estado: ', NEW.estado), COALESCE(@current_ip, '127.0.0.1')); END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;


DROP TABLE IF EXISTS `configuracion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `configuracion` (
  `clave` varchar(100) NOT NULL,
  `valor` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`clave`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `configuracion` WRITE;
/*!40000 ALTER TABLE `configuracion` DISABLE KEYS */;
INSERT INTO `configuracion` VALUES ('direccion_empresa','Direccion Principal'),('email_empresa','info@transalca.com'),('moneda','USD'),('nombre_empresa','Transalca C.A.'),('rif_empresa','J-00000000-0'),('telefono_empresa','0424-0000000'),('umbral_stock_bajo','5'),('vida_util_aceite_km','5000'),('vida_util_aceite_meses','6'),('vida_util_bateria_meses','24'),('vida_util_cauchos_meses','24'),('vida_util_filtros_meses','6'),('vida_util_frenos_meses','18'),('vida_util_refrigerante_meses','24'),('vida_util_servicio_general_meses','6');
/*!40000 ALTER TABLE `configuracion` ENABLE KEYS */;
UNLOCK TABLES;


DROP TABLE IF EXISTS `creditos_orden_venta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `creditos_orden_venta` (
  `id_credito` int(11) NOT NULL AUTO_INCREMENT,
  `orden_venta_id` int(11) NOT NULL,
  `fecha_inicio_credito` date DEFAULT NULL,
  `fecha_vencimiento_credito` date DEFAULT NULL,
  `fecha_pago_credito` datetime DEFAULT NULL,
  `estado_credito` varchar(30) NOT NULL DEFAULT 'activo',
  `notificacion_7d` tinyint(1) DEFAULT 0,
  `notificacion_2d` tinyint(1) DEFAULT 0,
  `notificacion_vencido` tinyint(1) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_credito`),
  UNIQUE KEY `uq_credito_orden` (`orden_venta_id`),
  CONSTRAINT `fk_credito_orden_venta` FOREIGN KEY (`orden_venta_id`) REFERENCES `ordenes_venta` (`id_orden_venta`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `creditos_orden_venta` WRITE;
/*!40000 ALTER TABLE `creditos_orden_venta` DISABLE KEYS */;
INSERT INTO `creditos_orden_venta` VALUES (1,8,'2026-05-29','2026-05-31',NULL,'vencido',1,1,1,'2026-05-29 08:15:01'),(2,10,'2026-06-08','2026-06-23',NULL,'activo',0,0,0,'2026-06-08 07:57:20'),(4,14,'2026-06-11','2026-07-11',NULL,'activo',0,0,0,'2026-06-11 06:17:58');
/*!40000 ALTER TABLE `creditos_orden_venta` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_bitacora_creditos_insert AFTER INSERT ON creditos_orden_venta FOR EACH ROW BEGIN INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip) VALUES (COALESCE(@current_usuario_id, 1), 'CREAR', 'CREDITO', CONCAT('Credito registrado orden: ', NEW.orden_venta_id), COALESCE(@current_ip, '127.0.0.1')); END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_bitacora_creditos_update AFTER UPDATE ON creditos_orden_venta FOR EACH ROW BEGIN INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip) VALUES (COALESCE(@current_usuario_id, 1), 'MODIFICAR', 'CREDITO', CASE WHEN NEW.estado_credito='pagado' THEN CONCAT('Credito pagado orden: ', NEW.orden_venta_id) ELSE CONCAT('Credito actualizado orden: ', NEW.orden_venta_id) END, COALESCE(@current_ip, '127.0.0.1')); END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;


DROP TABLE IF EXISTS `detalle_orden_compra`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `detalle_orden_compra` (
  `id_detalle_orden_compra` int(11) NOT NULL AUTO_INCREMENT,
  `orden_compra_id` int(11) NOT NULL,
  `producto_codigo` varchar(50) NOT NULL,
  `cantidad` int(11) NOT NULL DEFAULT 1,
  `precio_unitario_compra` decimal(10,2) NOT NULL,
  `subtotal` decimal(12,2) NOT NULL,
  PRIMARY KEY (`id_detalle_orden_compra`),
  KEY `orden_compra_id` (`orden_compra_id`),
  KEY `producto_codigo` (`producto_codigo`),
  CONSTRAINT `detalle_orden_compra_ibfk_1` FOREIGN KEY (`orden_compra_id`) REFERENCES `ordenes_compra` (`id_orden_compra`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `detalle_orden_compra_ibfk_2` FOREIGN KEY (`producto_codigo`) REFERENCES `productos` (`codigo`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `detalle_orden_compra` WRITE;
/*!40000 ALTER TABLE `detalle_orden_compra` DISABLE KEYS */;
INSERT INTO `detalle_orden_compra` VALUES (1,1,'BAT-000042',10,89.00,890.00);
/*!40000 ALTER TABLE `detalle_orden_compra` ENABLE KEYS */;
UNLOCK TABLES;


DROP TABLE IF EXISTS `detalle_orden_venta_productos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `detalle_orden_venta_productos` (
  `id_detalle_orden_venta_producto` int(11) NOT NULL AUTO_INCREMENT,
  `orden_id` int(11) NOT NULL,
  `producto_codigo` varchar(50) NOT NULL,
  `cantidad_detalle_orden_venta_producto` int(11) NOT NULL DEFAULT 1,
  `precio_unitario_producto` decimal(10,2) NOT NULL,
  PRIMARY KEY (`id_detalle_orden_venta_producto`),
  KEY `orden_id` (`orden_id`),
  KEY `producto_codigo` (`producto_codigo`),
  CONSTRAINT `detalle_orden_venta_productos_ibfk_1` FOREIGN KEY (`orden_id`) REFERENCES `ordenes_venta` (`id_orden_venta`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `detalle_orden_venta_productos_ibfk_2` FOREIGN KEY (`producto_codigo`) REFERENCES `productos` (`codigo`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `detalle_orden_venta_productos` WRITE;
/*!40000 ALTER TABLE `detalle_orden_venta_productos` DISABLE KEYS */;
INSERT INTO `detalle_orden_venta_productos` VALUES (1,1,'PC0507224338',2,21.00),(3,2,'COD0507224100',1,20.00),(4,9,'BAT-000041',1,89.00),(5,11,'BAT-000043',7,85.00),(6,13,'BAT-000016',1,50.00);
/*!40000 ALTER TABLE `detalle_orden_venta_productos` ENABLE KEYS */;
UNLOCK TABLES;


DROP TABLE IF EXISTS `detalle_orden_venta_servicios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `detalle_orden_venta_servicios` (
  `id_detalle_orden_venta_servicio` int(11) NOT NULL AUTO_INCREMENT,
  `orden_id` int(11) NOT NULL,
  `servicio_id` int(11) NOT NULL,
  `cantidad_detalle_orden_venta_servicio` int(11) NOT NULL DEFAULT 1,
  `precio_unitario_servicio` decimal(10,2) NOT NULL,
  PRIMARY KEY (`id_detalle_orden_venta_servicio`),
  KEY `orden_id` (`orden_id`),
  KEY `servicio_id` (`servicio_id`),
  CONSTRAINT `detalle_orden_venta_servicios_ibfk_1` FOREIGN KEY (`orden_id`) REFERENCES `ordenes_venta` (`id_orden_venta`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `detalle_orden_venta_servicios_ibfk_2` FOREIGN KEY (`servicio_id`) REFERENCES `servicios` (`id_servicio`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `detalle_orden_venta_servicios` WRITE;
/*!40000 ALTER TABLE `detalle_orden_venta_servicios` DISABLE KEYS */;
INSERT INTO `detalle_orden_venta_servicios` VALUES (2,2,1,1,15.00),(3,12,22,1,20.00),(4,13,22,1,20.00);
/*!40000 ALTER TABLE `detalle_orden_venta_servicios` ENABLE KEYS */;
UNLOCK TABLES;


DROP TABLE IF EXISTS `representante`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `representante` (
  `id_empresa_representante` int(11) NOT NULL AUTO_INCREMENT,
  `empresa_rif` varchar(20) NOT NULL,
  `representante_cedula` varchar(20) NOT NULL,
  `nombre_representante` varchar(100) NOT NULL,
  `apellido_representante` varchar(100) NOT NULL DEFAULT '',
  `telefono_representante` varchar(20) DEFAULT NULL,
  `email_representante` varchar(150) DEFAULT NULL,
  `cargo` varchar(50) NOT NULL DEFAULT 'Otro',
  `estado` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id_empresa_representante`),
  UNIQUE KEY `uk_representante_cedula` (`representante_cedula`),
  CONSTRAINT `fk_er_empresa` FOREIGN KEY (`empresa_rif`) REFERENCES `cliente` (`identificador_cliente`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `representante` WRITE;
/*!40000 ALTER TABLE `representante` DISABLE KEYS */;
INSERT INTO `representante` VALUES (2,'J-55656666-5','V-00000000','Admin','Sistema','0424-0000000','admin@transalca.com','Encargado de flota',1,'2026-06-07 14:58:45','2026-06-07 14:58:45'),(5,'J-55656666-5','V-31423434','dede','dede','04122397209','business@tanqueteodigital.com','Representante legal',1,'2026-06-07 16:54:48','2026-06-07 16:54:48'),(9,'J-55656666-5','V-3131333','dede','dede','04122222222','fderf@gmail.com','Encargado de flota',1,'2026-06-07 17:04:20','2026-06-07 17:04:20');
/*!40000 ALTER TABLE `representante` ENABLE KEYS */;
UNLOCK TABLES;


DROP TABLE IF EXISTS `empresa_vehiculo_representante`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `empresa_vehiculo_representante` (
  `id_empresa_vehiculo_representante` int(11) NOT NULL AUTO_INCREMENT,
  `empresa_representante_id` int(11) NOT NULL,
  `vehiculo_placa` varchar(20) NOT NULL,
  `tipo_operacion` varchar(50) NOT NULL DEFAULT 'registro',
  `fecha_operacion` timestamp NOT NULL DEFAULT current_timestamp(),
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id_empresa_vehiculo_representante`),
  KEY `fk_evr_vehiculo` (`vehiculo_placa`),
  KEY `fk_evr_empresa_representante` (`empresa_representante_id`),
  CONSTRAINT `fk_evr_empresa_representante` FOREIGN KEY (`empresa_representante_id`) REFERENCES `representante` (`id_empresa_representante`) ON UPDATE CASCADE,
  CONSTRAINT `fk_evr_vehiculo` FOREIGN KEY (`vehiculo_placa`) REFERENCES `vehiculos` (`placa_vehiculo`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `empresa_vehiculo_representante` WRITE;
/*!40000 ALTER TABLE `empresa_vehiculo_representante` DISABLE KEYS */;
/*!40000 ALTER TABLE `empresa_vehiculo_representante` ENABLE KEYS */;
UNLOCK TABLES;


DROP TABLE IF EXISTS `historial_puntos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `historial_puntos` (
  `id_historial_punto` int(11) NOT NULL AUTO_INCREMENT,
  `tarjeta_id` int(11) NOT NULL,
  `puntos` int(11) NOT NULL,
  `tipo_historial_punto` varchar(30) NOT NULL DEFAULT 'suma',
  `descripcion_historial_punto` varchar(150) DEFAULT NULL,
  `fecha_historial_punto` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_historial_punto`),
  KEY `tarjeta_id` (`tarjeta_id`),
  KEY `tipo` (`tipo_historial_punto`),
  CONSTRAINT `historial_puntos_ibfk_1` FOREIGN KEY (`tarjeta_id`) REFERENCES `tarjeta_fidelidad` (`id_tarjeta_fidelidad`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `historial_puntos` WRITE;
/*!40000 ALTER TABLE `historial_puntos` DISABLE KEYS */;
INSERT INTO `historial_puntos` VALUES (1,2,1,'suma','Registro de tarjeta y primer punto via escaneo QR','2026-06-03 16:59:09'),(2,2,1,'suma','Punto acumulado via escaneo QR','2026-06-03 17:01:36'),(3,2,1,'suma','Punto acumulado via escaneo QR','2026-06-03 17:01:57');
/*!40000 ALTER TABLE `historial_puntos` ENABLE KEYS */;
UNLOCK TABLES;


DROP TABLE IF EXISTS `marcas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `marcas` (
  `nombre_marca` varchar(150) NOT NULL,
  `descripcion_marca` varchar(500) DEFAULT NULL,
  `estado` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`nombre_marca`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `marcas` WRITE;
/*!40000 ALTER TABLE `marcas` DISABLE KEYS */;
INSERT INTO `marcas` VALUES ('15W40 / 20W50 SEMI SINTETICO FC GARRAFA','Marca importada del catalogo real: 15W40 / 20W50 SEMI SINTETICO FC GARRAFA',1,'2026-05-28 02:32:34'),('15W40 SEMI SINTETICO VALVOLINE GARRAFA','Marca importada del catalogo real: 15W40 SEMI SINTETICO VALVOLINE GARRAFA',1,'2026-05-28 02:32:34'),('7.00R15 KOBATA','Marca importada del catalogo real: 7.00R15 KOBATA',1,'2026-05-28 02:32:34'),('ACDelco','Baterias y repuestos automotrices',1,'2026-05-27 14:10:55'),('ACEITE 10W30 SEMI SINTETICO GULF','Marca importada del catalogo real: ACEITE 10W30 SEMI SINTETICO GULF',1,'2026-05-28 02:32:34'),('ACEITE 10W40 SEMI SINTETICO MOBIL','Marca importada del catalogo real: ACEITE 10W40 SEMI SINTETICO MOBIL',1,'2026-05-28 02:32:34'),('ACEITE 15W40 MINERAL FC','Marca importada del catalogo real: ACEITE 15W40 MINERAL FC',1,'2026-05-28 02:32:34'),('ACEITE 15W40 MINERAL GULF','Marca importada del catalogo real: ACEITE 15W40 MINERAL GULF',1,'2026-05-28 02:32:34'),('ACEITE 15W40 MINERAL INCA','Marca importada del catalogo real: ACEITE 15W40 MINERAL INCA',1,'2026-05-28 02:32:34'),('ACEITE 15W40 MINERAL MEXLUB','Marca importada del catalogo real: ACEITE 15W40 MINERAL MEXLUB',1,'2026-05-28 02:32:34'),('ACEITE 15W40 MINERAL RALOY','Marca importada del catalogo real: ACEITE 15W40 MINERAL RALOY',1,'2026-05-28 02:32:34'),('ACEITE 15W40 MINERAL ROSHFRANS','Marca importada del catalogo real: ACEITE 15W40 MINERAL ROSHFRANS',1,'2026-05-28 02:32:34'),('ACEITE 15W40 MINERAL VALVOLINE','Marca importada del catalogo real: ACEITE 15W40 MINERAL VALVOLINE',1,'2026-05-28 02:32:34'),('ACEITE 15W40 SEMI SINTETICO BOSS','Marca importada del catalogo real: ACEITE 15W40 SEMI SINTETICO BOSS',1,'2026-05-28 02:32:34'),('ACEITE 15W40 SEMI SINTETICO FC','Marca importada del catalogo real: ACEITE 15W40 SEMI SINTETICO FC',1,'2026-05-28 02:32:34'),('ACEITE 15W40 SEMI SINTETICO GULF','Marca importada del catalogo real: ACEITE 15W40 SEMI SINTETICO GULF',1,'2026-05-28 02:32:34'),('ACEITE 15W40 SEMI SINTETICO INCA','Marca importada del catalogo real: ACEITE 15W40 SEMI SINTETICO INCA',1,'2026-05-28 02:32:34'),('ACEITE 15W40 SEMI SINTETICO MEXLUB','Marca importada del catalogo real: ACEITE 15W40 SEMI SINTETICO MEXLUB',1,'2026-05-28 02:32:34'),('ACEITE 15W40 SEMI SINTETICO RALOY','Marca importada del catalogo real: ACEITE 15W40 SEMI SINTETICO RALOY',1,'2026-05-28 02:32:34'),('ACEITE 15W40 SEMI SINTETICO VALVOLINE','Marca importada del catalogo real: ACEITE 15W40 SEMI SINTETICO VALVOLINE',1,'2026-05-28 02:32:34'),('ACEITE 15W40 SEMI SINTETICO WOLF','Marca importada del catalogo real: ACEITE 15W40 SEMI SINTETICO WOLF',1,'2026-05-28 02:32:34'),('ACEITE 20W50 MINERAL BOSS','Marca importada del catalogo real: ACEITE 20W50 MINERAL BOSS',1,'2026-05-28 02:32:34'),('ACEITE 20W50 MINERAL FC','Marca importada del catalogo real: ACEITE 20W50 MINERAL FC',1,'2026-05-28 02:32:34'),('ACEITE 20W50 MINERAL GULF','Marca importada del catalogo real: ACEITE 20W50 MINERAL GULF',1,'2026-05-28 02:32:34'),('ACEITE 20W50 MINERAL INCA','Marca importada del catalogo real: ACEITE 20W50 MINERAL INCA',1,'2026-05-28 02:32:34'),('ACEITE 20W50 MINERAL MEXLUB','Marca importada del catalogo real: ACEITE 20W50 MINERAL MEXLUB',1,'2026-05-28 02:32:34'),('ACEITE 20W50 MINERAL MOBIL','Marca importada del catalogo real: ACEITE 20W50 MINERAL MOBIL',1,'2026-05-28 02:32:34'),('ACEITE 20W50 MINERAL MOTUL','Marca importada del catalogo real: ACEITE 20W50 MINERAL MOTUL',1,'2026-05-28 02:32:34'),('ACEITE 20W50 MINERAL RALOY','Marca importada del catalogo real: ACEITE 20W50 MINERAL RALOY',1,'2026-05-28 02:32:34'),('ACEITE 20W50 MINERAL ROSHFRANS','Marca importada del catalogo real: ACEITE 20W50 MINERAL ROSHFRANS',1,'2026-05-28 02:32:34'),('ACEITE 20W50 MINERAL VALVOLINE','Marca importada del catalogo real: ACEITE 20W50 MINERAL VALVOLINE',1,'2026-05-28 02:32:34'),('ACEITE 20W50 SEMI SINTETICO FC','Marca importada del catalogo real: ACEITE 20W50 SEMI SINTETICO FC',1,'2026-05-28 02:32:34'),('ACEITE 20W50 SEMI SINTETICO GULF','Marca importada del catalogo real: ACEITE 20W50 SEMI SINTETICO GULF',1,'2026-05-28 02:32:34'),('ACEITE 20W50 SEMI SINTETICO INCA','Marca importada del catalogo real: ACEITE 20W50 SEMI SINTETICO INCA',1,'2026-05-28 02:32:34'),('ACEITE 20W50 SEMI SINTETICO MEXLUB','Marca importada del catalogo real: ACEITE 20W50 SEMI SINTETICO MEXLUB',1,'2026-05-28 02:32:34'),('ACEITE 20W50 SEMI SINTETICO RALOY','Marca importada del catalogo real: ACEITE 20W50 SEMI SINTETICO RALOY',1,'2026-05-28 02:32:34'),('ACEITE 20W50 SEMI SINTETICO VALVOLINE','Marca importada del catalogo real: ACEITE 20W50 SEMI SINTETICO VALVOLINE',1,'2026-05-28 02:32:34'),('ACEITE 5W20 SINTETICO GULF','Marca importada del catalogo real: ACEITE 5W20 SINTETICO GULF',1,'2026-05-28 02:32:34'),('ACEITE 5W30 SINTETICO GULF','Marca importada del catalogo real: ACEITE 5W30 SINTETICO GULF',1,'2026-05-28 02:32:34'),('ACEITE 5W40 SINTETICO GUL','Marca importada del catalogo real: ACEITE 5W40 SINTETICO GUL',1,'2026-05-28 02:32:34'),('AKRON','Marca importada del catalogo real: AKRON',1,'2026-05-28 02:32:34'),('ALIX IMPACT AT PLUS','Marca importada del catalogo real: ALIX IMPACT AT PLUS',1,'2026-05-28 02:32:34'),('ALIX IMPACT HT','Marca importada del catalogo real: ALIX IMPACT HT',1,'2026-05-28 02:32:34'),('ALIX IMPACT HT PLUS','Marca importada del catalogo real: ALIX IMPACT HT PLUS',1,'2026-05-28 02:32:34'),('ALIX VELOCE','Marca importada del catalogo real: ALIX VELOCE',1,'2026-05-28 02:32:34'),('ALIX VEZETTA','Marca importada del catalogo real: ALIX VEZETTA',1,'2026-05-28 02:32:34'),('ALIX VEZETTA PLUS','Marca importada del catalogo real: ALIX VEZETTA PLUS',1,'2026-05-28 02:32:34'),('AMBERSTONE MIXTO','Marca importada del catalogo real: AMBERSTONE MIXTO',1,'2026-05-28 02:32:34'),('ANCHEE','Marca importada del catalogo real: ANCHEE',1,'2026-05-28 02:32:34'),('ANCHEE MT','Marca importada del catalogo real: ANCHEE MT',1,'2026-05-28 02:32:34'),('ANNAITE','Marca importada del catalogo real: ANNAITE',1,'2026-05-28 02:32:34'),('ANNAITE DIRECCIONAL 14PR','Marca importada del catalogo real: ANNAITE DIRECCIONAL 14PR',1,'2026-05-28 02:32:34'),('AOQISHI A/T','Marca importada del catalogo real: AOQISHI A/T',1,'2026-05-28 02:32:34'),('AOQISHI MARVEL M/T','Marca importada del catalogo real: AOQISHI MARVEL M/T',1,'2026-05-28 02:32:34'),('ARMAX','Marca importada del catalogo real: ARMAX',1,'2026-05-28 02:32:34'),('ARO 24 - 1100','Marca importada del catalogo real: ARO 24 - 1100',1,'2026-05-28 02:32:34'),('ARO 24R - 1100','Marca importada del catalogo real: ARO 24R - 1100',1,'2026-05-28 02:32:34'),('ARO 315-1100 (TORNILLO)','Marca importada del catalogo real: ARO 315-1100 (TORNILLO)',1,'2026-05-28 02:32:34'),('ARO 42-900 (42MR)','Marca importada del catalogo real: ARO 42-900 (42MR)',1,'2026-05-28 02:32:34'),('ARO 42R-900 (42M)','Marca importada del catalogo real: ARO 42R-900 (42M)',1,'2026-05-28 02:32:34'),('ARO 99R-700','Marca importada del catalogo real: ARO 99R-700',1,'2026-05-28 02:32:34'),('ATLANTIC OIL','Marca importada del catalogo real: ATLANTIC OIL',1,'2026-05-28 02:32:34'),('BITOIL','Marca importada del catalogo real: BITOIL',1,'2026-05-28 02:32:34'),('Bosch','Filtros, frenos y componentes automotrices',1,'2026-05-27 14:10:55'),('BOSS','Marca importada del catalogo real: BOSS',1,'2026-05-28 02:32:34'),('BRAVA','Marca importada del catalogo real: BRAVA',1,'2026-05-28 02:32:34'),('Castrol','Lubricantes y aceites',1,'2026-04-30 04:18:56'),('CHENSHANG','Marca importada del catalogo real: CHENSHANG',1,'2026-05-28 02:32:34'),('CROSSLEADER WILDTIGER MT','Marca importada del catalogo real: CROSSLEADER WILDTIGER MT',1,'2026-05-28 02:32:34'),('DAUER','Marca importada del catalogo real: DAUER',1,'2026-05-28 02:32:34'),('DOUBLEKING','Marca importada del catalogo real: DOUBLEKING',1,'2026-05-28 02:32:34'),('DOUBLEKING DK306','Marca importada del catalogo real: DOUBLEKING DK306',1,'2026-05-28 02:32:34'),('DOUBLEKING DK306 10PR','Marca importada del catalogo real: DOUBLEKING DK306 10PR',1,'2026-05-28 02:32:34'),('DOUBLESTAR','Marca importada del catalogo real: DOUBLESTAR',1,'2026-05-28 02:32:34'),('DOUBLESTAR 16 PR','Marca importada del catalogo real: DOUBLESTAR 16 PR',1,'2026-05-28 02:32:34'),('DOUBLESTAR DH05','Marca importada del catalogo real: DOUBLESTAR DH05',1,'2026-05-28 02:32:34'),('DOUBLESTAR DS01','Marca importada del catalogo real: DOUBLESTAR DS01',1,'2026-05-28 02:32:34'),('DURACEL 34R - 1100','Marca importada del catalogo real: DURACEL 34R - 1100',1,'2026-05-28 02:32:34'),('DURACELL 24-1000 (24MR)','Marca importada del catalogo real: DURACELL 24-1000 (24MR)',1,'2026-05-28 02:32:34'),('DURACELL 24F-1000 (24M)','Marca importada del catalogo real: DURACELL 24F-1000 (24M)',1,'2026-05-28 02:32:34'),('DURACELL 31 - 1300S (TORNILLO)','Marca importada del catalogo real: DURACELL 31 - 1300S (TORNILLO)',1,'2026-05-28 02:32:34'),('DURACELL 34 - 1100','Marca importada del catalogo real: DURACELL 34 - 1100',1,'2026-05-28 02:32:34'),('DURACELL 42-900 (42MR)','Marca importada del catalogo real: DURACELL 42-900 (42MR)',1,'2026-05-28 02:32:34'),('DURACELL 42R-900 (42M)','Marca importada del catalogo real: DURACELL 42R-900 (42M)',1,'2026-05-28 02:32:34'),('DURACELL 99-650 (36MR)','Marca importada del catalogo real: DURACELL 99-650 (36MR)',1,'2026-05-28 02:32:34'),('DURINGON CROSSMAXX','Marca importada del catalogo real: DURINGON CROSSMAXX',1,'2026-05-28 02:32:34'),('ECOSAVER DIRECCIONAL 18PR','Marca importada del catalogo real: ECOSAVER DIRECCIONAL 18PR',1,'2026-05-28 02:32:34'),('EVERLAND','Marca importada del catalogo real: EVERLAND',1,'2026-05-28 02:32:34'),('EXTREMA 24AD1000-A (24MR)','Marca importada del catalogo real: EXTREMA 24AD1000-A (24MR)',1,'2026-05-28 02:32:34'),('EXTREME 24BD-720 (42MR)','Marca importada del catalogo real: EXTREME 24BD-720 (42MR)',1,'2026-05-28 02:32:34'),('EXTREME 24BI-720 (42M)','Marca importada del catalogo real: EXTREME 24BI-720 (42M)',1,'2026-05-28 02:32:34'),('EXTREME 36DLM700 (36MR)','Marca importada del catalogo real: EXTREME 36DLM700 (36MR)',1,'2026-05-28 02:32:34'),('FC FAUCI','Marca importada del catalogo real: FC FAUCI',1,'2026-05-28 02:32:34'),('Firestone','Neumaticos americanos',1,'2026-04-30 04:18:56'),('FIRESTONE DESTINATION H/T','Marca importada del catalogo real: FIRESTONE DESTINATION H/T',1,'2026-05-28 02:32:34'),('FIRESTONE FIREHAWK','Marca importada del catalogo real: FIRESTONE FIREHAWK',1,'2026-05-28 02:32:34'),('FIRESTONE MULTIHAWK','Marca importada del catalogo real: FIRESTONE MULTIHAWK',1,'2026-05-28 02:32:34'),('GONHER','Marca importada del catalogo real: GONHER',1,'2026-05-28 02:32:34'),('GULF','Marca importada del catalogo real: GULF',1,'2026-05-28 02:32:34'),('HABILEAD','Marca importada del catalogo real: HABILEAD',1,'2026-05-28 02:32:34'),('HABILEAD A/T','Marca importada del catalogo real: HABILEAD A/T',1,'2026-05-28 02:32:34'),('HABILEAD AT','Marca importada del catalogo real: HABILEAD AT',1,'2026-05-28 02:32:34'),('HABILEAD COMFORMAX','Marca importada del catalogo real: HABILEAD COMFORMAX',1,'2026-05-28 02:32:34'),('HAIDA 16PR DIRECCIONAL','Marca importada del catalogo real: HAIDA 16PR DIRECCIONAL',1,'2026-05-28 02:32:34'),('HEADWAY','Marca importada del catalogo real: HEADWAY',1,'2026-05-28 02:32:34'),('HILO - VANTAGE XU1','Marca importada del catalogo real: HILO - VANTAGE XU1',1,'2026-05-28 02:32:34'),('HILO DIRECCIONAL 14PR','Marca importada del catalogo real: HILO DIRECCIONAL 14PR',1,'2026-05-28 02:32:34'),('HILO GENESYS','Marca importada del catalogo real: HILO GENESYS',1,'2026-05-28 02:32:34'),('HILO GENESYS XP1','Marca importada del catalogo real: HILO GENESYS XP1',1,'2026-05-28 02:32:34'),('HILO HT','Marca importada del catalogo real: HILO HT',1,'2026-05-28 02:32:34'),('HILO X-TERRAIN MT1','Marca importada del catalogo real: HILO X-TERRAIN MT1',1,'2026-05-28 02:32:34'),('HONOUR 14PR DIRECCIONAL','Marca importada del catalogo real: HONOUR 14PR DIRECCIONAL',1,'2026-05-28 02:32:34'),('INCA','Marca importada del catalogo real: INCA',1,'2026-05-28 02:32:34'),('Marca afahcceddi','Prueba',0,'2026-05-08 02:43:38'),('MAXTREK SU-830','Marca importada del catalogo real: MAXTREK SU-830',1,'2026-05-28 02:32:34'),('MEXLUB','Marca importada del catalogo real: MEXLUB',1,'2026-05-28 02:32:34'),('Michelin','Neumaticos franceses de alta calidad',1,'2026-04-30 04:18:56'),('MILEKING MT','Marca importada del catalogo real: MILEKING MT',1,'2026-05-28 02:32:34'),('Mobil','Marca importada del catalogo real: MOBIL',1,'2026-04-30 04:18:56'),('MOTORCRAFT','Marca importada del catalogo real: MOTORCRAFT',1,'2026-05-28 02:32:34'),('MOURA ME310FD (36MR)','Marca importada del catalogo real: MOURA ME310FD (36MR)',1,'2026-05-28 02:32:34'),('MOURA ME570GI (22M)','Marca importada del catalogo real: MOURA ME570GI (22M)',1,'2026-05-28 02:32:34'),('MOURA ME650RD (24MR)','Marca importada del catalogo real: MOURA ME650RD (24MR)',1,'2026-05-28 02:32:34'),('MOURA ME805D (36MR)','Marca importada del catalogo real: MOURA ME805D (36MR)',1,'2026-05-28 02:32:34'),('NGK','Bujias y componentes de encendido',1,'2026-05-27 14:10:55'),('NOVAMAX STAR A/T','Marca importada del catalogo real: NOVAMAX STAR A/T',1,'2026-05-28 02:32:34'),('NOVAMAX WARRIOR TERRA T/A','Marca importada del catalogo real: NOVAMAX WARRIOR TERRA T/A',1,'2026-05-28 02:32:34'),('NOVAMAXX','Marca importada del catalogo real: NOVAMAXX',1,'2026-05-28 02:32:34'),('NOVAMAXX AT','Marca importada del catalogo real: NOVAMAXX AT',1,'2026-05-28 02:32:34'),('OILSTONE','Marca importada del catalogo real: OILSTONE',1,'2026-05-28 02:32:34'),('Pirelli','Neumaticos premium italianos',1,'2026-04-30 04:18:56'),('POWERTAC ECOCOMFORT','Marca importada del catalogo real: POWERTAC ECOCOMFORT',1,'2026-05-28 02:32:34'),('POWERTRAC','Marca importada del catalogo real: POWERTRAC',1,'2026-05-28 02:32:34'),('POWERTRAC ADAMAS','Marca importada del catalogo real: POWERTRAC ADAMAS',1,'2026-05-28 02:32:34'),('POWERTRAC CITYROVER','Marca importada del catalogo real: POWERTRAC CITYROVER',1,'2026-05-28 02:32:34'),('POWERTRAC DIRECCIONAL','Marca importada del catalogo real: POWERTRAC DIRECCIONAL',1,'2026-05-28 02:32:34'),('POWERTRAC ECO SPORT X77','Marca importada del catalogo real: POWERTRAC ECO SPORT X77',1,'2026-05-28 02:32:34'),('POWERTRAC ECOCOMFORT','Marca importada del catalogo real: POWERTRAC ECOCOMFORT',1,'2026-05-28 02:32:34'),('POWERTRAC ECOCOMFORT X66','Marca importada del catalogo real: POWERTRAC ECOCOMFORT X66',1,'2026-05-28 02:32:34'),('POWERTRAC MIXTO','Marca importada del catalogo real: POWERTRAC MIXTO',1,'2026-05-28 02:32:34'),('POWERTRAC TRAC PRO (SET)','Marca importada del catalogo real: POWERTRAC TRAC PRO (SET)',1,'2026-05-28 02:32:34'),('POWERTRAC TRACCION','Marca importada del catalogo real: POWERTRAC TRACCION',1,'2026-05-28 02:32:34'),('POWERTRAC VANTOUR','Marca importada del catalogo real: POWERTRAC VANTOUR',1,'2026-05-28 02:32:34'),('POWERTRAC WILDRANGER A/T','Marca importada del catalogo real: POWERTRAC WILDRANGER A/T',1,'2026-05-28 02:32:34'),('POWERTRAC WILDRANGER AT','Marca importada del catalogo real: POWERTRAC WILDRANGER AT',1,'2026-05-28 02:32:34'),('POWERTRAC WILDRANGER M/T','Marca importada del catalogo real: POWERTRAC WILDRANGER M/T',1,'2026-05-28 02:32:34'),('POWERTRAC WILDRANGER MT','Marca importada del catalogo real: POWERTRAC WILDRANGER MT',1,'2026-05-28 02:32:34'),('RALOY','Marca importada del catalogo real: RALOY',1,'2026-05-28 02:32:34'),('RAPID','Marca importada del catalogo real: RAPID',1,'2026-05-28 02:32:34'),('RAPID ECOLANDER','Marca importada del catalogo real: RAPID ECOLANDER',1,'2026-05-28 02:32:34'),('RAPID ECOLANDER A/T','Marca importada del catalogo real: RAPID ECOLANDER A/T',1,'2026-05-28 02:32:34'),('RAPID ECOSAVER','Marca importada del catalogo real: RAPID ECOSAVER',1,'2026-05-28 02:32:34'),('RAPID MUD CONTENDER M/T','Marca importada del catalogo real: RAPID MUD CONTENDER M/T',1,'2026-05-28 02:32:34'),('RAPID P329','Marca importada del catalogo real: RAPID P329',1,'2026-05-28 02:32:34'),('RAPID P609','Marca importada del catalogo real: RAPID P609',1,'2026-05-28 02:32:34'),('RAPID SHARK Z02','Marca importada del catalogo real: RAPID SHARK Z02',1,'2026-05-28 02:32:34'),('RAPID TUFTRAIL A/T','Marca importada del catalogo real: RAPID TUFTRAIL A/T',1,'2026-05-28 02:32:34'),('ROADSHINE 16PR DIRECCIONAL','Marca importada del catalogo real: ROADSHINE 16PR DIRECCIONAL',1,'2026-05-28 02:32:34'),('ROCKBLADE 14PR DIRECCIONAL','Marca importada del catalogo real: ROCKBLADE 14PR DIRECCIONAL',1,'2026-05-28 02:32:34'),('ROCKBLADE 787RT','Marca importada del catalogo real: ROCKBLADE 787RT',1,'2026-05-28 02:32:34'),('ROCKBLADE H/T','Marca importada del catalogo real: ROCKBLADE H/T',1,'2026-05-28 02:32:34'),('ROYAL BLACK','Marca importada del catalogo real: ROYAL BLACK',1,'2026-05-28 02:32:34'),('ROYAL BLACK A/T','Marca importada del catalogo real: ROYAL BLACK A/T',1,'2026-05-28 02:32:34'),('Shell','Lubricantes Shell Helix',1,'2026-04-30 04:18:56'),('SHELL HELIX','Marca importada del catalogo real: SHELL HELIX',1,'2026-05-28 02:32:34'),('SKY','Marca importada del catalogo real: SKY',1,'2026-05-28 02:32:34'),('SUPERMEALLIR DIRECCIONAL','Marca importada del catalogo real: SUPERMEALLIR DIRECCIONAL',1,'2026-05-28 02:32:34'),('TAITONG 18 PR MIXTO HS268','Marca importada del catalogo real: TAITONG 18 PR MIXTO HS268',1,'2026-05-28 02:32:34'),('TDI TIRES R/T','Marca importada del catalogo real: TDI TIRES R/T',1,'2026-05-28 02:32:34'),('TestBrand0507224100','Prueba',0,'2026-05-08 02:41:00'),('V-RICH A/T','Marca importada del catalogo real: V-RICH A/T',1,'2026-05-28 02:32:34'),('V-RICH ALL TERRAIN','Marca importada del catalogo real: V-RICH ALL TERRAIN',1,'2026-05-28 02:32:34'),('V-RICH AT','Marca importada del catalogo real: V-RICH AT',1,'2026-05-28 02:32:34'),('V-RICH AT 10PR','Marca importada del catalogo real: V-RICH AT 10PR',1,'2026-05-28 02:32:34'),('VALVOLINE','Marca importada del catalogo real: VALVOLINE',1,'2026-05-28 02:32:34'),('VM LUB','Marca importada del catalogo real: VM LUB',1,'2026-05-28 02:32:34'),('VM LUBRICANTES','Marca importada del catalogo real: VM LUBRICANTES',1,'2026-05-28 02:32:34'),('WIDEWAY','Marca importada del catalogo real: WIDEWAY',1,'2026-05-28 02:32:34'),('WIDEWAY A/T','Marca importada del catalogo real: WIDEWAY A/T',1,'2026-05-28 02:32:34'),('WIDEWAY AK3 6PR','Marca importada del catalogo real: WIDEWAY AK3 6PR',1,'2026-05-28 02:32:34'),('WIDEWAY SAFEWAY','Marca importada del catalogo real: WIDEWAY SAFEWAY',1,'2026-05-28 02:32:34'),('WIDEWAY WEYONE AK3','Marca importada del catalogo real: WIDEWAY WEYONE AK3',1,'2026-05-28 02:32:34'),('WIDEWAY XT ALL-TERRAIN','Marca importada del catalogo real: WIDEWAY XT ALL-TERRAIN',1,'2026-05-28 02:32:34'),('WOLF','Marca importada del catalogo real: WOLF',1,'2026-05-28 02:32:34');
/*!40000 ALTER TABLE `marcas` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_marcas_insert` AFTER INSERT ON marcas FOR EACH ROW BEGIN
        INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (COALESCE(@current_usuario_id, 1), 'CREAR', 'MARCAS', CONCAT('Marca creada: ', NEW.nombre_marca), COALESCE(@current_ip, '127.0.0.1'));
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_marcas_update` AFTER UPDATE ON marcas FOR EACH ROW BEGIN
        IF OLD.estado = 1 AND NEW.estado = 0 THEN
            INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
            VALUES (COALESCE(@current_usuario_id, 1), 'ELIMINAR', 'MARCAS', CONCAT('Marca desactivada: ', NEW.nombre_marca), COALESCE(@current_ip, '127.0.0.1'));
        ELSE
            INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
            VALUES (COALESCE(@current_usuario_id, 1), 'MODIFICAR', 'MARCAS', CONCAT('Marca modificada: ', OLD.nombre_marca, ' -> ', NEW.nombre_marca), COALESCE(@current_ip, '127.0.0.1'));
        END IF;
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;


DROP TABLE IF EXISTS `mecanicos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mecanicos` (
  `cedula_mecanico` varchar(20) NOT NULL,
  `cedula_prefijo` varchar(2) DEFAULT NULL,
  `nombre_mecanico` varchar(100) NOT NULL,
  `apellido_mecanico` varchar(100) NOT NULL,
  `telefono_mecanico` varchar(20) DEFAULT NULL,
  `especialidad_mecanico` varchar(200) DEFAULT NULL,
  `foto_perfil_mecanico` varchar(200) DEFAULT 'default.png',
  `usuario_id` int(11) DEFAULT NULL,
  `estado` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`cedula_mecanico`),
  KEY `fk_mecanicos_usuario` (`usuario_id`),
  CONSTRAINT `fk_mecanicos_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `db_mantenimiento`.`usuarios` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `mecanicos` WRITE;
/*!40000 ALTER TABLE `mecanicos` DISABLE KEYS */;
INSERT INTO `mecanicos` VALUES ('V-07224157','V','Carlos','Mendoza','04121234567','Alineacion','default.png',NULL,1,'2026-05-08 02:41:57'),('V-07224236','V','Carlos','Mendoza','04121234567','Alineacion','default.png',NULL,1,'2026-05-08 02:42:30'),('V-07224351','V','Mario','Mecanico','04121234567','Frenos','default.png',NULL,1,'2026-05-08 02:43:38');
/*!40000 ALTER TABLE `mecanicos` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_mecanicos_insert` AFTER INSERT ON mecanicos FOR EACH ROW BEGIN
        INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (COALESCE(@current_usuario_id, 1), 'CREAR', 'MECANICOS', CONCAT('Mecanico creado: ', NEW.cedula_mecanico), COALESCE(@current_ip, '127.0.0.1'));
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_mecanicos_update` AFTER UPDATE ON mecanicos FOR EACH ROW BEGIN
        IF OLD.estado = 1 AND NEW.estado = 0 THEN
            INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
            VALUES (COALESCE(@current_usuario_id, 1), 'MODIFICAR', 'MECANICOS', CONCAT('Estado mecanico cambiado: ', NEW.cedula_mecanico), COALESCE(@current_ip, '127.0.0.1'));
        ELSE
            INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
            VALUES (COALESCE(@current_usuario_id, 1), 'MODIFICAR', 'MECANICOS', CONCAT('Mecanico modificado: ', OLD.cedula_mecanico), COALESCE(@current_ip, '127.0.0.1'));
        END IF;
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;


DROP TABLE IF EXISTS `metodos_pago`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `metodos_pago` (
  `id_metodo_pago` int(11) NOT NULL AUTO_INCREMENT,
  `nombre_metodo_pago` varchar(100) NOT NULL,
  `permite_credito` tinyint(1) NOT NULL DEFAULT 0,
  `estado` tinyint(1) NOT NULL DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `moneda` varchar(10) NOT NULL DEFAULT 'usd',
  `datos_metodo_pago` varchar(80) NOT NULL DEFAULT '',
  PRIMARY KEY (`id_metodo_pago`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `metodos_pago` WRITE;
/*!40000 ALTER TABLE `metodos_pago` DISABLE KEYS */;
INSERT INTO `metodos_pago` VALUES (1,'transferencia',0,1,'2026-05-27 10:09:22','2026-06-03 15:51:04','bs','Banco Mercantil, Cuenta Corriente: 0105-0105-11-1111111111'),(2,'pago_movil',1,1,'2026-05-27 10:09:22','2026-06-03 16:32:39','bs','CI 12345678\n0412-1234567\nBanesco'),(3,'efectivo',0,1,'2026-05-27 10:09:22','2026-06-03 16:14:41','usd','Pago en tienda'),(4,'zelle',0,1,'2026-05-27 10:09:22','2026-06-03 15:51:04','usd','zelle@transalca.com, Transalca C.A.'),(5,'binance',0,1,'2026-05-27 10:09:22','2026-06-03 15:51:04','usd','binance_pay_id: 99887766, transalca@binance'),(6,'tarjeta',0,1,'2026-05-27 10:09:22','2026-06-03 16:14:41','bs','Pago con tarjeta'),(7,'Pago movil',0,1,'2026-05-28 22:44:14','2026-06-03 16:28:28','usd','CI 12345678\n0412-1234567\nBanesco'),(8,'Credito empresa',1,1,'2026-05-28 22:44:14','2026-06-03 16:14:41','usd','Compra a credito para empresas aprobadas.'),(12,'dede',0,1,'2026-06-02 21:37:41','2026-06-03 16:14:41','usd','30396029\n2013013\n312093183781'),(13,'test_temp_method_updated',1,0,'2026-06-03 16:16:13','2026-06-03 16:16:13','usd','Test payment details 123 updated'),(14,'test_temp_method_updated',1,0,'2026-06-03 16:23:20','2026-06-03 16:23:20','usd','Test payment details 123 updated');
/*!40000 ALTER TABLE `metodos_pago` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_metodos_pago_insert` AFTER INSERT ON metodos_pago FOR EACH ROW BEGIN
        INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (COALESCE(@current_usuario_id, 1), 'CREAR', 'METODOS_PAGO', CONCAT('Método de pago creado: ', NEW.nombre_metodo_pago), COALESCE(@current_ip, '127.0.0.1'));
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_metodos_pago_update` AFTER UPDATE ON metodos_pago FOR EACH ROW BEGIN
        IF OLD.estado = 1 AND NEW.estado = 0 THEN
            INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
            VALUES (COALESCE(@current_usuario_id, 1), 'ELIMINAR', 'METODOS_PAGO', CONCAT('Método de pago eliminado: ', NEW.nombre_metodo_pago), COALESCE(@current_ip, '127.0.0.1'));
        ELSE
            INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
            VALUES (COALESCE(@current_usuario_id, 1), 'MODIFICAR', 'METODOS_PAGO', CONCAT('Método de pago modificado: ', NEW.nombre_metodo_pago), COALESCE(@current_ip, '127.0.0.1'));
        END IF;
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;


DROP TABLE IF EXISTS `notificaciones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notificaciones` (
  `id_notificacion` int(11) NOT NULL AUTO_INCREMENT,
  `usuario_id` int(11) DEFAULT NULL,
  `cliente_cedula` varchar(20) DEFAULT NULL,
  `tipo_notificacion` varchar(30) NOT NULL DEFAULT 'sistema',
  `titulo_notificacion` varchar(200) DEFAULT NULL,
  `mensaje_notificacion` text DEFAULT NULL,
  `prioridad_notificacion` varchar(20) DEFAULT 'media',
  `leida` tinyint(1) DEFAULT 0,
  `enlace` varchar(500) DEFAULT NULL,
  `referencia` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_notificacion`),
  KEY `idx_notif_usuario_leida` (`usuario_id`,`leida`,`created_at`),
  KEY `idx_notif_cliente_leida` (`cliente_cedula`,`leida`,`created_at`),
  CONSTRAINT `fk_notificaciones_cliente` FOREIGN KEY (`cliente_cedula`) REFERENCES `cliente` (`identificador_cliente`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=482 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `notificaciones` WRITE;
/*!40000 ALTER TABLE `notificaciones` DISABLE KEYS */;
INSERT INTO `notificaciones` VALUES (9,NULL,'V-00000000','pago','Pago aprobado: pedido #11','Tu pago del pedido #11 fue aprobado. Ya puedes revisar el estado y el QR de factura en Mis pedidos.','media',0,NULL,NULL,'2026-06-08 21:18:28'),(10,NULL,'V-00000000','pago','Pago rechazado: pedido #9','Tu pago del pedido #9 fue rechazado. Motivo: poruq eis. Revisa el detalle del pedido y carga un comprobante valido si corresponde.','alta',0,NULL,NULL,'2026-06-08 21:18:39'),(11,NULL,'30396029','pago','Pago aprobado: pedido #13','Tu pago del pedido #13 fue aprobado. Ya puedes revisar el estado y el QR de factura en Mis pedidos.','media',0,NULL,NULL,'2026-06-11 06:15:22'),(246,1,NULL,'sistema','Stock bajo: LT285/70R17 POWERTRAC WILDRANGER AT','El producto LT285/70R17 POWERTRAC WILDRANGER AT (NEU-000157) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(247,1,NULL,'sistema','Stock bajo: ACEITE SAE 15W40 BITOIL MINERAL','El producto ACEITE SAE 15W40 BITOIL MINERAL (LUB-000077) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(248,1,NULL,'sistema','Stock bajo: LT265/75R16 ROYAL BLACK A/T','El producto LT265/75R16 ROYAL BLACK A/T (NEU-000109) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(249,1,NULL,'sistema','Stock bajo: ATF DX III GULF CAJA DE ACEITE AUTOMATICO DE 1L','El producto ATF DX III GULF CAJA DE ACEITE AUTOMATICO DE 1L (LUB-000080) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(250,1,NULL,'sistema','Stock bajo: P265/75R16 NOVAMAX WARRIOR TERRA T/A','El producto P265/75R16 NOVAMAX WARRIOR TERRA T/A (NEU-000108) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(251,1,NULL,'sistema','Stock bajo: VALVULINA 80W90 BITOIL 1L','El producto VALVULINA 80W90 BITOIL 1L (LUB-000082) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(252,1,NULL,'sistema','Stock bajo: VALVULINA 85W140 BITOIL 1L','El producto VALVULINA 85W140 BITOIL 1L (LUB-000083) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(253,1,NULL,'sistema','Stock bajo: ACEITE FC 20W50 SEMI SINTETICO','El producto ACEITE FC 20W50 SEMI SINTETICO (LUB-000084) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(254,1,NULL,'sistema','Stock bajo: VALVULINA 85W140 GULF GEAR MP','El producto VALVULINA 85W140 GULF GEAR MP (LUB-000086) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(255,1,NULL,'sistema','Stock bajo: ACEITE INCA 15W40 SEMI SINTETICO','El producto ACEITE INCA 15W40 SEMI SINTETICO (LUB-000087) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(256,1,NULL,'sistema','Stock bajo: LT265/70R16 V-RICH AT','El producto LT265/70R16 V-RICH AT (NEU-000106) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(257,1,NULL,'sistema','Stock bajo: ACEITE 25W50 MINERAL MEXLUB ALTO KILOMETRAJE','El producto ACEITE 25W50 MINERAL MEXLUB ALTO KILOMETRAJE (LUB-000089) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(258,1,NULL,'sistema','Stock bajo: VALVULINA 80W90 GL-5 MEXLUB','El producto VALVULINA 80W90 GL-5 MEXLUB (LUB-000090) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(259,1,NULL,'sistema','Stock bajo: VALVULINA 85W140 GL-5 MEXLUB','El producto VALVULINA 85W140 GL-5 MEXLUB (LUB-000091) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(260,1,NULL,'sistema','Stock bajo: ACEITE OILSTONE 20W50 SEMI SINTETICO','El producto ACEITE OILSTONE 20W50 SEMI SINTETICO (LUB-000092) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(261,1,NULL,'sistema','Stock bajo: SAE 85W140 VALVULINA RALOY EXTREMA PRESION 946ML','El producto SAE 85W140 VALVULINA RALOY EXTREMA PRESION 946ML (LUB-000093) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(262,1,NULL,'sistema','Stock bajo: ACEITE ARMAX SAE50 PAILA 20L','El producto ACEITE ARMAX SAE50 PAILA 20L (LUB-000094) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(263,1,NULL,'sistema','Stock bajo: 265/75R16 V-RICH AT 10PR','El producto 265/75R16 V-RICH AT 10PR (NEU-000110) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(264,1,NULL,'sistema','Stock bajo: LT265/75R16 HILO X-TERRAIN MT1','El producto LT265/75R16 HILO X-TERRAIN MT1 (NEU-000116) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(265,1,NULL,'sistema','Stock bajo: 15W50 4T INCA','El producto 15W50 4T INCA (LUB-000074) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(266,1,NULL,'sistema','Stock bajo: LT265/70R17 V-RICH ALL TERRAIN','El producto LT265/70R17 V-RICH ALL TERRAIN (NEU-000152) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(267,1,NULL,'sistema','Stock bajo: 15W40 SEMI SINTETICO 3.78L VALVOLINE','El producto 15W40 SEMI SINTETICO 3.78L VALVOLINE (LUB-000044) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(268,1,NULL,'sistema','Stock bajo: 15W40 SEMI SINTETICO INCA','El producto 15W40 SEMI SINTETICO INCA (LUB-000046) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(269,1,NULL,'sistema','Stock bajo: 15W40 SEMI SINTETICO VM LUB','El producto 15W40 SEMI SINTETICO VM LUB (LUB-000047) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(270,1,NULL,'sistema','Stock bajo: 15W40 EVOLUB SKY','El producto 15W40 EVOLUB SKY (LUB-000048) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(271,1,NULL,'sistema','Stock bajo: 20W50 SEMI SINTETICO ARMAX','El producto 20W50 SEMI SINTETICO ARMAX (LUB-000052) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(272,1,NULL,'sistema','Stock bajo: 20W50 SEMI SINTETICO VM LUB','El producto 20W50 SEMI SINTETICO VM LUB (LUB-000053) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(273,1,NULL,'sistema','Stock bajo: 215/45R17 RAPID P609','El producto 215/45R17 RAPID P609 (NEU-000145) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(274,1,NULL,'sistema','Stock bajo: 20W50 SEMI SINTETICO FC GALON 3.78L','El producto 20W50 SEMI SINTETICO FC GALON 3.78L (LUB-000056) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(275,1,NULL,'sistema','Stock bajo: 225/50ZR17 HILO - VANTAGE XU1','El producto 225/50ZR17 HILO - VANTAGE XU1 (NEU-000140) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(276,1,NULL,'sistema','Stock bajo: 7.50-16 POWERTRAC TRAC PRO (SET)','El producto 7.50-16 POWERTRAC TRAC PRO (SET) (NEU-000133) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:53'),(277,1,NULL,'sistema','Stock bajo: 7.50R16 HILO DIRECCIONAL 14PR','El producto 7.50R16 HILO DIRECCIONAL 14PR (NEU-000131) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(278,1,NULL,'sistema','Stock bajo: 315/75R16 POWERTRAC WILDRANGER M/T','El producto 315/75R16 POWERTRAC WILDRANGER M/T (NEU-000128) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(279,1,NULL,'sistema','Stock bajo: 305/70R16 HILO X-TERRAIN MT1','El producto 305/70R16 HILO X-TERRAIN MT1 (NEU-000127) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(280,1,NULL,'sistema','Stock bajo: LT285/75R16 AOQISHI A/T','El producto LT285/75R16 AOQISHI A/T (NEU-000124) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(281,1,NULL,'sistema','Stock bajo: LT285/75R16 POWERTRAC WILDRANGER A/T','El producto LT285/75R16 POWERTRAC WILDRANGER A/T (NEU-000119) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(282,1,NULL,'sistema','Stock bajo: ACEITE SAE50 BITOIL PAILA 19L','El producto ACEITE SAE50 BITOIL PAILA 19L (LUB-000095) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(283,1,NULL,'sistema','Stock bajo: ACEITE BOSS SAE50 PAILA 20 LITROS','El producto ACEITE BOSS SAE50 PAILA 20 LITROS (LUB-000096) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(284,1,NULL,'sistema','Stock bajo: ACEITE SAE50 FC PAILA 19L','El producto ACEITE SAE50 FC PAILA 19L (LUB-000097) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(285,1,NULL,'sistema','Stock bajo: 175/65R14 ALIX VEZETTA','El producto 175/65R14 ALIX VEZETTA (NEU-000030) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(286,1,NULL,'sistema','Stock bajo: 205/55R16 ANCHEE','El producto 205/55R16 ANCHEE (NEU-000093) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(287,1,NULL,'sistema','Stock bajo: 185/65R14 WIDEWAY SAFEWAY','El producto 185/65R14 WIDEWAY SAFEWAY (NEU-000036) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(288,1,NULL,'sistema','Stock bajo: 185/65R14 ANCHEE','El producto 185/65R14 ANCHEE (NEU-000039) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(289,1,NULL,'sistema','Stock bajo: 185/65R14 ANNAITE','El producto 185/65R14 ANNAITE (NEU-000040) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(290,1,NULL,'sistema','Stock bajo: 185/65R14 RAPID P329','El producto 185/65R14 RAPID P329 (NEU-000041) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(291,1,NULL,'sistema','Stock bajo: 195/55R16 POWERTRAC ADAMAS','El producto 195/55R16 POWERTRAC ADAMAS (NEU-000091) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(292,1,NULL,'sistema','Stock bajo: 195/60R15 WIDEWAY','El producto 195/60R15 WIDEWAY (NEU-000046) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(293,1,NULL,'sistema','Stock bajo: LT35X12.5R15 HILO X-TERRAIN MT1','El producto LT35X12.5R15 HILO X-TERRAIN MT1 (NEU-000089) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(294,1,NULL,'sistema','Stock bajo: 33X12.5R15LT HILO X-TERRAIN MT1','El producto 33X12.5R15LT HILO X-TERRAIN MT1 (NEU-000087) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(295,1,NULL,'sistema','Stock bajo: 31X10.50R15 POWERTRAC WILDRANGER A/T','El producto 31X10.50R15 POWERTRAC WILDRANGER A/T (NEU-000078) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(296,1,NULL,'sistema','Stock bajo: 31X10.50R15 WIDEWAY A/T','El producto 31X10.50R15 WIDEWAY A/T (NEU-000074) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(297,1,NULL,'sistema','Stock bajo: 205/70R15C POWERTRAC VANTOUR','El producto 205/70R15C POWERTRAC VANTOUR (NEU-000059) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(298,1,NULL,'sistema','Stock bajo: LT235/75R15 POWERTRAC WILDRANGER M/T','El producto LT235/75R15 POWERTRAC WILDRANGER M/T (NEU-000060) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(299,1,NULL,'sistema','Stock bajo: 31X10.50R15 HILO X-TERRAIN MT1','El producto 31X10.50R15 HILO X-TERRAIN MT1 (NEU-000073) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(300,1,NULL,'sistema','Stock bajo: 31X10.50R15 ANCHEE MT','El producto 31X10.50R15 ANCHEE MT (NEU-000072) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(301,1,NULL,'sistema','Stock bajo: 175/65R14 POWERTRAC ADAMAS','El producto 175/65R14 POWERTRAC ADAMAS (NEU-000029) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(302,1,NULL,'sistema','Stock bajo: 175/65R14 EVERLAND','El producto 175/65R14 EVERLAND (NEU-000028) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(303,1,NULL,'sistema','Stock bajo: 175/70R13 HILO GENESYS XP1','El producto 175/70R13 HILO GENESYS XP1 (NEU-000026) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(304,1,NULL,'sistema','Stock bajo: ACEITE ARMAX 15W40 MINERAL DIESEL PAILA 20L','El producto ACEITE ARMAX 15W40 MINERAL DIESEL PAILA 20L (LUB-000099) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(305,1,NULL,'sistema','Stock bajo: ACEITE 15W40 DIESEL MEXLUB 5L CL-4','El producto ACEITE 15W40 DIESEL MEXLUB 5L CL-4 (LUB-000100) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(306,1,NULL,'sistema','Stock bajo: P255/70R16 ALIX IMPACT HT PLUS','El producto P255/70R16 ALIX IMPACT HT PLUS (NEU-000104) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(307,1,NULL,'sistema','Stock bajo: SAE 15W40 SEMI SINTETICO TURBO RALOY API SN PLUS','El producto SAE 15W40 SEMI SINTETICO TURBO RALOY API SN PLUS (LUB-000102) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(308,1,NULL,'sistema','Stock bajo: TRANS-FLUID RDX-III RALOY P/TRANSMISION AUTOMATICA','El producto TRANS-FLUID RDX-III RALOY P/TRANSMISION AUTOMATICA (LUB-000103) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(309,1,NULL,'sistema','Stock bajo: SAE 20W50 RALOY TURBO SEMI-SINTETICO','El producto SAE 20W50 RALOY TURBO SEMI-SINTETICO (LUB-000104) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(310,1,NULL,'sistema','Stock bajo: SAE 20W50 RALOY RACING OIL MULTIGRADE','El producto SAE 20W50 RALOY RACING OIL MULTIGRADE (LUB-000105) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(311,1,NULL,'sistema','Stock bajo: ACEITE SHELL HELIX HX8 PROFESIONAL SINTETICO','El producto ACEITE SHELL HELIX HX8 PROFESIONAL SINTETICO (LUB-000106) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(312,1,NULL,'sistema','Stock bajo: ACEITE ATF DEXRON 3 SHELL SPIRAX S3 MD3 1L','El producto ACEITE ATF DEXRON 3 SHELL SPIRAX S3 MD3 1L (LUB-000107) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(313,1,NULL,'sistema','Stock bajo: ACEITE VITALTECH 5W40 SINTETICO WOLF','El producto ACEITE VITALTECH 5W40 SINTETICO WOLF (LUB-000108) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(314,1,NULL,'sistema','Stock bajo: VALVULINA SINTETICA 75W90 GL-5 VITAL TECH WOLF','El producto VALVULINA SINTETICA 75W90 GL-5 VITAL TECH WOLF (LUB-000109) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(315,1,NULL,'sistema','Stock bajo: 245/70R16 POWERTRAC WILDRANGER A/T','El producto 245/70R16 POWERTRAC WILDRANGER A/T (NEU-000102) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(316,1,NULL,'sistema','Stock bajo: 165/70R13 ROYAL BLACK','El producto 165/70R13 ROYAL BLACK (NEU-000017) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(317,1,NULL,'sistema','Stock bajo: 175/70R13 POWERTRAC ADAMAS','El producto 175/70R13 POWERTRAC ADAMAS (NEU-000021) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(318,1,NULL,'sistema','Stock bajo: 175/70R13 DOUBLESTAR','El producto 175/70R13 DOUBLESTAR (NEU-000024) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(319,1,NULL,'sistema','Stock bajo: 235/75R15 NOVAMAXX','El producto 235/75R15 NOVAMAXX (NEU-000068) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(320,1,NULL,'sistema','Stock bajo: 15W40 SEMI SINTETICO ARMAX','El producto 15W40 SEMI SINTETICO ARMAX (LUB-000036) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(321,1,NULL,'sistema','Stock bajo: ACEITE 20W50 SEMI SINTETICO RALOY','El producto ACEITE 20W50 SEMI SINTETICO RALOY (CMB-000018) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(322,1,NULL,'sistema','Stock bajo: ACEITE 15W40 SEMI SINTETICO GULF','El producto ACEITE 15W40 SEMI SINTETICO GULF (CMB-000007) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(323,1,NULL,'sistema','Stock bajo: ACEITE 10W30 SEMI SINTETICO GULF','El producto ACEITE 10W30 SEMI SINTETICO GULF (CMB-000008) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(324,1,NULL,'sistema','Stock bajo: ACEITE 5W20 SINTETICO GULF','El producto ACEITE 5W20 SINTETICO GULF (CMB-000009) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(325,1,NULL,'sistema','Stock bajo: ACEITE 5W30 SINTETICO GULF','El producto ACEITE 5W30 SINTETICO GULF (CMB-000010) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(326,1,NULL,'sistema','Stock bajo: ACEITE 5W40 SINTETICO GUL','El producto ACEITE 5W40 SINTETICO GUL (CMB-000011) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(327,1,NULL,'sistema','Stock bajo: ACEITE 20W50 MINERAL RALOY','El producto ACEITE 20W50 MINERAL RALOY (CMB-000016) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(328,1,NULL,'sistema','Stock bajo: ACEITE 20W50 MINERAL INCA','El producto ACEITE 20W50 MINERAL INCA (CMB-000017) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(329,1,NULL,'sistema','Stock bajo: 315/80R22.5 POWERTRAC DIRECCIONAL','El producto 315/80R22.5 POWERTRAC DIRECCIONAL (NEU-000194) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(330,1,NULL,'sistema','Stock bajo: ACEITE 20W50 SEMI SINTETICO INCA','El producto ACEITE 20W50 SEMI SINTETICO INCA (CMB-000019) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(331,1,NULL,'sistema','Stock bajo: ACEITE 15W40 MINERAL RALOY','El producto ACEITE 15W40 MINERAL RALOY (CMB-000020) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(332,1,NULL,'sistema','Stock bajo: ACEITE 15W40 MINERAL INCA','El producto ACEITE 15W40 MINERAL INCA (CMB-000021) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(333,1,NULL,'sistema','Stock bajo: ACEITE 15W40 SEMI SINTETICO RALOY','El producto ACEITE 15W40 SEMI SINTETICO RALOY (CMB-000022) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(334,1,NULL,'sistema','Stock bajo: ACEITE 15W40 SEMI SINTETICO INCA','El producto ACEITE 15W40 SEMI SINTETICO INCA (CMB-000023) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(335,1,NULL,'sistema','Stock bajo: ACEITE 20W50 MINERAL BOSS','El producto ACEITE 20W50 MINERAL BOSS (CMB-000024) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(336,1,NULL,'sistema','Stock bajo: ACEITE 15W40 SEMI SINTETICO BOSS','El producto ACEITE 15W40 SEMI SINTETICO BOSS (CMB-000025) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(337,1,NULL,'sistema','Stock bajo: ACEITE 20W50 MINERAL VALVOLINE','El producto ACEITE 20W50 MINERAL VALVOLINE (CMB-000030) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(338,1,NULL,'sistema','Stock bajo: ACEITE 15W40 MINERAL GULF','El producto ACEITE 15W40 MINERAL GULF (CMB-000006) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(339,1,NULL,'sistema','Stock bajo: ACEITE 20W50 SEMI SINTETICO GULF','El producto ACEITE 20W50 SEMI SINTETICO GULF (CMB-000005) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(340,1,NULL,'sistema','Stock bajo: ACEITE 20W50 MINERAL GULF','El producto ACEITE 20W50 MINERAL GULF (CMB-000004) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(341,1,NULL,'sistema','Stock bajo: 315/80R22.5 AMBERSTONE MIXTO','El producto 315/80R22.5 AMBERSTONE MIXTO (NEU-000193) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(342,1,NULL,'sistema','Stock bajo: 315/80R22.5 SUPERMEALLIR DIRECCIONAL','El producto 315/80R22.5 SUPERMEALLIR DIRECCIONAL (NEU-000192) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(343,1,NULL,'sistema','Stock bajo: 295/80R22.5 POWERTRAC TRACCION','El producto 295/80R22.5 POWERTRAC TRACCION (NEU-000188) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(344,1,NULL,'sistema','Stock bajo: 900 AMP DURACELL 42-900 (42MR)','El producto 900 AMP DURACELL 42-900 (42MR) (BAT-000033) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(345,1,NULL,'sistema','Stock bajo: 295/80R22.5 POWERTRAC MIXTO','El producto 295/80R22.5 POWERTRAC MIXTO (NEU-000187) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(346,1,NULL,'sistema','Stock bajo: 295/80R22.5 POWERTRAC DIRECCIONAL','El producto 295/80R22.5 POWERTRAC DIRECCIONAL (NEU-000186) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(347,1,NULL,'sistema','Stock bajo: 900 AMP ARO 42R-900 (42M)','El producto 900 AMP ARO 42R-900 (42M) (BAT-000036) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(348,1,NULL,'sistema','Stock bajo: 295/80R22.5 ECOSAVER DIRECCIONAL 18PR','El producto 295/80R22.5 ECOSAVER DIRECCIONAL 18PR (NEU-000185) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(349,1,NULL,'sistema','Stock bajo: 1100 AMP ARO 315-1100 (TORNILLO)','El producto 1100 AMP ARO 315-1100 (TORNILLO) (BAT-000040) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(350,1,NULL,'sistema','Stock bajo: 1000 AMP DURACELL 24-1000 (24MR)','El producto 1000 AMP DURACELL 24-1000 (24MR) (BAT-000041) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(351,1,NULL,'sistema','Stock bajo: 35X12.5R20 POWERTRAC WILDRANGER M/T','El producto 35X12.5R20 POWERTRAC WILDRANGER M/T (NEU-000181) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(352,1,NULL,'sistema','Stock bajo: 275/55R20 V-RICH ALL TERRAIN','El producto 275/55R20 V-RICH ALL TERRAIN (NEU-000179) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(353,1,NULL,'sistema','Stock bajo: 37x13.5R18 MILEKING MT','El producto 37x13.5R18 MILEKING MT (NEU-000176) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(354,1,NULL,'sistema','Stock bajo: 35X12.50R18 WIDEWAY','El producto 35X12.50R18 WIDEWAY (NEU-000172) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(355,1,NULL,'sistema','Stock bajo: 245/60R18 POWERTRAC CITYROVER','El producto 245/60R18 POWERTRAC CITYROVER (NEU-000171) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(356,1,NULL,'sistema','Stock bajo: ACEITE 20W50 MINERAL FC','El producto ACEITE 20W50 MINERAL FC (CMB-000031) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(357,1,NULL,'sistema','Stock bajo: ACEITE 20W50 MINERAL MOBIL','El producto ACEITE 20W50 MINERAL MOBIL (CMB-000032) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(358,1,NULL,'sistema','Stock bajo: 235/50ZR18 POWERTRAC ECO SPORT X77','El producto 235/50ZR18 POWERTRAC ECO SPORT X77 (NEU-000170) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(359,1,NULL,'sistema','Stock bajo: 15W40 MINERAL GULF MAX GDI','El producto 15W40 MINERAL GULF MAX GDI (LUB-000008) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(360,1,NULL,'sistema','Stock bajo: 225/40ZR18 POWERTRAC ECO SPORT X77','El producto 225/40ZR18 POWERTRAC ECO SPORT X77 (NEU-000169) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(361,1,NULL,'sistema','Stock bajo: 20W50 MINERAL ATLANTIC','El producto 20W50 MINERAL ATLANTIC (LUB-000013) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(362,1,NULL,'sistema','Stock bajo: 20W50 MINERAL FC','El producto 20W50 MINERAL FC (LUB-000014) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(363,1,NULL,'sistema','Stock bajo: 15W40 MINERAL ARMAX','El producto 15W40 MINERAL ARMAX (LUB-000015) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(364,1,NULL,'sistema','Stock bajo: 20W50 MINERAL AKRON','El producto 20W50 MINERAL AKRON (LUB-000017) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(365,1,NULL,'sistema','Stock bajo: 20W50 MINERAL BITOIL','El producto 20W50 MINERAL BITOIL (LUB-000018) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(366,1,NULL,'sistema','Stock bajo: 235/75R17.5 POWERTRAC','El producto 235/75R17.5 POWERTRAC (NEU-000166) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(367,1,NULL,'sistema','Stock bajo: 215/75R17.5 POWERTRAC','El producto 215/75R17.5 POWERTRAC (NEU-000165) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(368,1,NULL,'sistema','Stock bajo: LT285/70R17 WIDEWAY XT ALL-TERRAIN','El producto LT285/70R17 WIDEWAY XT ALL-TERRAIN (NEU-000160) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(369,1,NULL,'sistema','Stock bajo: LT285/70R17 HILO X-TERRAIN MT1','El producto LT285/70R17 HILO X-TERRAIN MT1 (NEU-000159) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(370,1,NULL,'sistema','Stock bajo: 20W50 MINERAL VM LUB','El producto 20W50 MINERAL VM LUB (LUB-000027) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(371,1,NULL,'sistema','Stock bajo: LT285/70R17 POWERTRAC WILDRANGER MT','El producto LT285/70R17 POWERTRAC WILDRANGER MT (NEU-000158) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(372,1,NULL,'sistema','Stock bajo: 10W30 SEMI SINTETICO VALVOLINE','El producto 10W30 SEMI SINTETICO VALVOLINE (LUB-000030) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(373,1,NULL,'sistema','Stock bajo: 15W40 SEMI SINTETICO BOSS','El producto 15W40 SEMI SINTETICO BOSS (LUB-000034) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(374,1,NULL,'sistema','Stock bajo: ACEITE 20W50 MINERAL MOTUL','El producto ACEITE 20W50 MINERAL MOTUL (CMB-000053) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(375,1,NULL,'sistema','Stock bajo: ACEITE 15W40 SEMI SINTETICO FC','El producto ACEITE 15W40 SEMI SINTETICO FC (CMB-000040) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(376,1,NULL,'sistema','Stock bajo: 15W40 SEMI SINTETICO VALVOLINE GARRAFA','El producto 15W40 SEMI SINTETICO VALVOLINE GARRAFA (CMB-000039) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(377,1,NULL,'sistema','Stock bajo: ACEITE 15W40 SEMI SINTETICO VALVOLINE','El producto ACEITE 15W40 SEMI SINTETICO VALVOLINE (CMB-000038) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(378,1,NULL,'sistema','Stock bajo: ACEITE 15W40 MINERAL FC','El producto ACEITE 15W40 MINERAL FC (CMB-000037) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(379,1,NULL,'sistema','Stock bajo: ACEITE 15W40 MINERAL VALVOLINE','El producto ACEITE 15W40 MINERAL VALVOLINE (CMB-000036) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(380,1,NULL,'sistema','Stock bajo: ACEITE 10W40 SEMI SINTETICO MOBIL','El producto ACEITE 10W40 SEMI SINTETICO MOBIL (CMB-000035) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(381,1,NULL,'sistema','Stock bajo: ACEITE 20W50 SEMI SINTETICO FC','El producto ACEITE 20W50 SEMI SINTETICO FC (CMB-000034) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(382,1,NULL,'sistema','Stock bajo: ACEITE 20W50 SEMI SINTETICO VALVOLINE','El producto ACEITE 20W50 SEMI SINTETICO VALVOLINE (CMB-000033) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(383,1,NULL,'sistema','Stock bajo: 15W40 / 20W50 SEMI SINTETICO FC GARRAFA','El producto 15W40 / 20W50 SEMI SINTETICO FC GARRAFA (CMB-000041) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(384,1,NULL,'sistema','Stock bajo: ACEITE 20W50 MINERAL ROSHFRANS','El producto ACEITE 20W50 MINERAL ROSHFRANS (CMB-000046) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(385,1,NULL,'sistema','Stock bajo: ACEITE 20W50 SEMI SINTETICO BRAVA','El producto ACEITE 20W50 SEMI SINTETICO BRAVA (LUB-000035) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(386,1,NULL,'sistema','Stock bajo: ACEITE 15W40 SEMI SINTETICO WOLF','El producto ACEITE 15W40 SEMI SINTETICO WOLF (CMB-000052) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(387,1,NULL,'sistema','Stock bajo: ACEITE 15W40 SEMI SINTETICO MEXLUB','El producto ACEITE 15W40 SEMI SINTETICO MEXLUB (CMB-000051) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(388,1,NULL,'sistema','Stock bajo: ACEITE 15W40 MINERAL MEXLUB','El producto ACEITE 15W40 MINERAL MEXLUB (CMB-000050) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(389,1,NULL,'sistema','Stock bajo: ACEITE 15W40 MINERAL ROSHFRANS','El producto ACEITE 15W40 MINERAL ROSHFRANS (CMB-000049) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(390,1,NULL,'sistema','Stock bajo: ACEITE 20W50 SEMI SINTETICO MEXLUB','El producto ACEITE 20W50 SEMI SINTETICO MEXLUB (CMB-000048) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(391,1,NULL,'sistema','Stock bajo: ACEITE 20W50 MINERAL MEXLUB','El producto ACEITE 20W50 MINERAL MEXLUB (CMB-000047) tiene stock bajo en Sede Principal: 0 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(392,1,NULL,'sistema','Stock bajo: 12RR2.5 POWERTRAC MIXTO','El producto 12RR2.5 POWERTRAC MIXTO (NEU-000191) tiene stock bajo en Sede Principal: 1 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(393,1,NULL,'sistema','Stock bajo: 295/80R22.5 TAITONG 18 PR MIXTO HS268','El producto 295/80R22.5 TAITONG 18 PR MIXTO HS268 (NEU-000184) tiene stock bajo en Sede Principal: 1 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(394,1,NULL,'sistema','Stock bajo: 215/60R16 POWERTRAC','El producto 215/60R16 POWERTRAC (NEU-000097) tiene stock bajo en Sede Principal: 1 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(395,1,NULL,'sistema','Stock bajo: 7.50R16 HONOUR 14PR DIRECCIONAL','El producto 7.50R16 HONOUR 14PR DIRECCIONAL (NEU-000134) tiene stock bajo en Sede Principal: 1 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(396,1,NULL,'sistema','Stock bajo: 900 AMP DURACELL 42R-900 (42M)','El producto 900 AMP DURACELL 42R-900 (42M) (BAT-000034) tiene stock bajo en Sede Principal: 1 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(397,1,NULL,'sistema','Stock bajo: 15W40 SEMI SINTETICO AKRON','El producto 15W40 SEMI SINTETICO AKRON (LUB-000038) tiene stock bajo en Sede Principal: 1 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(398,1,NULL,'sistema','Stock bajo: 5W30 SINTETICO WOLF ECOTECH SP-RP G6','El producto 5W30 SINTETICO WOLF ECOTECH SP-RP G6 (LUB-000068) tiene stock bajo en Sede Principal: 1 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(399,1,NULL,'sistema','Stock bajo: 900 AMP ARO 42-900 (42MR)','El producto 900 AMP ARO 42-900 (42MR) (BAT-000035) tiene stock bajo en Sede Principal: 1 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(400,1,NULL,'sistema','Stock bajo: 1100 AMP ARO 24R - 1100','El producto 1100 AMP ARO 24R - 1100 (BAT-000044) tiene stock bajo en Sede Principal: 1 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(401,1,NULL,'sistema','Stock bajo: 20W50 4TCH VALVOLINE MINERAL','El producto 20W50 4TCH VALVOLINE MINERAL (LUB-000072) tiene stock bajo en Sede Principal: 1 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(402,1,NULL,'sistema','Stock bajo: 1000 AMP EXTREMA 24AD1000-A (24MR)','El producto 1000 AMP EXTREMA 24AD1000-A (24MR) (BAT-000043) tiene stock bajo en Sede Principal: 1 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(403,1,NULL,'sistema','Stock bajo: 1100 AMP ARO 24 - 1100','El producto 1100 AMP ARO 24 - 1100 (BAT-000045) tiene stock bajo en Sede Principal: 1 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(404,1,NULL,'sistema','Stock bajo: 650 AMP MOURA ME310FD (36MR)','El producto 650 AMP MOURA ME310FD (36MR) (BAT-000017) tiene stock bajo en Sede Principal: 1 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(405,1,NULL,'sistema','Stock bajo: 1100 AMP DURACEL 34R - 1100','El producto 1100 AMP DURACEL 34R - 1100 (BAT-000047) tiene stock bajo en Sede Principal: 1 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(406,1,NULL,'sistema','Stock bajo: 1100 AMP DURACELL 34 - 1100','El producto 1100 AMP DURACELL 34 - 1100 (BAT-000046) tiene stock bajo en Sede Principal: 1 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(407,1,NULL,'sistema','Stock bajo: ACEITE ATF-3 MEXLUB PARA TRANSMISIONES AUT','El producto ACEITE ATF-3 MEXLUB PARA TRANSMISIONES AUT (LUB-000081) tiene stock bajo en Sede Principal: 1 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(408,1,NULL,'sistema','Stock bajo: 800 AMP MOURA ME570GI (22M)','El producto 800 AMP MOURA ME570GI (22M) (BAT-000023) tiene stock bajo en Sede Principal: 1 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(409,1,NULL,'sistema','Stock bajo: 650 AMP MOURA ME805D (36MR)','El producto 650 AMP MOURA ME805D (36MR) (BAT-000020) tiene stock bajo en Sede Principal: 1 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(410,1,NULL,'sistema','Stock bajo: 650 AMP DURACELL 99-650 (36MR)','El producto 650 AMP DURACELL 99-650 (36MR) (BAT-000018) tiene stock bajo en Sede Principal: 1 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(411,1,NULL,'sistema','Stock bajo: 20W50 SEMI SINTETICO BOSS','El producto 20W50 SEMI SINTETICO BOSS (LUB-000054) tiene stock bajo en Sede Principal: 1 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(412,1,NULL,'sistema','Stock bajo: 5W-20 SHELL HELIX HX7 SP SINTETICO 1L','El producto 5W-20 SHELL HELIX HX7 SP SINTETICO 1L (LUB-000063) tiene stock bajo en Sede Principal: 1 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(413,1,NULL,'sistema','Stock bajo: 700 AMP ARO 99R-700','El producto 700 AMP ARO 99R-700 (BAT-000019) tiene stock bajo en Sede Principal: 1 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(414,1,NULL,'sistema','Stock bajo: ISO 68 HIDRALOY 300 ACEITE HIDRAULICO 68 RALOY PAILA 19L','El producto ISO 68 HIDRALOY 300 ACEITE HIDRAULICO 68 RALOY PAILA 19L (LUB-000101) tiene stock bajo en Sede Principal: 2 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(415,1,NULL,'sistema','Stock bajo: 20W50 MINERAL MOBIL SUPER 1000','El producto 20W50 MINERAL MOBIL SUPER 1000 (LUB-000026) tiene stock bajo en Sede Principal: 2 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(416,1,NULL,'sistema','Stock bajo: LT265/70R17 AOQISHI A/T','El producto LT265/70R17 AOQISHI A/T (NEU-000153) tiene stock bajo en Sede Principal: 2 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(417,1,NULL,'sistema','Stock bajo: 245/65R17 DOUBLEKING','El producto 245/65R17 DOUBLEKING (NEU-000150) tiene stock bajo en Sede Principal: 2 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(418,1,NULL,'sistema','Stock bajo: 1300 AMP DURACELL 31 - 1300S (TORNILLO)','El producto 1300 AMP DURACELL 31 - 1300S (TORNILLO) (BAT-000048) tiene stock bajo en Sede Principal: 2 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(419,1,NULL,'sistema','Stock bajo: 205/45R17 RAPID P609','El producto 205/45R17 RAPID P609 (NEU-000141) tiene stock bajo en Sede Principal: 2 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(420,1,NULL,'sistema','Stock bajo: 285/75R16 V-RICH A/T','El producto 285/75R16 V-RICH A/T (NEU-000120) tiene stock bajo en Sede Principal: 2 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(421,1,NULL,'sistema','Stock bajo: 235/75R17.5 CHENSHANG','El producto 235/75R17.5 CHENSHANG (NEU-000167) tiene stock bajo en Sede Principal: 2 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(422,1,NULL,'sistema','Stock bajo: 20W50 EVOLUB SKY SENI SINTETICO','El producto 20W50 EVOLUB SKY SENI SINTETICO (LUB-000059) tiene stock bajo en Sede Principal: 2 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(423,1,NULL,'sistema','Stock bajo: 5W30 FULL SINTETICO VALVOLINE','El producto 5W30 FULL SINTETICO VALVOLINE (LUB-000065) tiene stock bajo en Sede Principal: 2 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(424,1,NULL,'sistema','Stock bajo: LT265/75R16 ALIX IMPACT AT PLUS','El producto LT265/75R16 ALIX IMPACT AT PLUS (NEU-000114) tiene stock bajo en Sede Principal: 2 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(425,1,NULL,'sistema','Stock bajo: 265/60R18 ROCKBLADE H/T','El producto 265/60R18 ROCKBLADE H/T (NEU-000175) tiene stock bajo en Sede Principal: 2 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(426,1,NULL,'sistema','Stock bajo: 31X10.50R15 LT ROCKBLADE 787RT','El producto 31X10.50R15 LT ROCKBLADE 787RT (NEU-000076) tiene stock bajo en Sede Principal: 2 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(427,1,NULL,'sistema','Stock bajo: 205/70R15 FIRESTONE DESTINATION H/T','El producto 205/70R15 FIRESTONE DESTINATION H/T (NEU-000056) tiene stock bajo en Sede Principal: 2 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(428,1,NULL,'sistema','Stock bajo: 31X10.50R15 POWERTRAC WILDRANGER M/T','El producto 31X10.50R15 POWERTRAC WILDRANGER M/T (NEU-000079) tiene stock bajo en Sede Principal: 2 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(429,1,NULL,'sistema','Stock bajo: 20W50 MINERAL RALOY RACING OIL MULTIGRADE','El producto 20W50 MINERAL RALOY RACING OIL MULTIGRADE (LUB-000019) tiene stock bajo en Sede Principal: 2 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(430,1,NULL,'sistema','Stock bajo: 31X10.50R15 AOQISHI MARVEL M/T','El producto 31X10.50R15 AOQISHI MARVEL M/T (NEU-000081) tiene stock bajo en Sede Principal: 2 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(431,1,NULL,'sistema','Stock bajo: LT7.00R15 7.00R15 KOBATA','El producto LT7.00R15 7.00R15 KOBATA (NEU-000088) tiene stock bajo en Sede Principal: 2 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(432,1,NULL,'sistema','Stock bajo: 1000 AMP MOURA ME650RD (24MR)','El producto 1000 AMP MOURA ME650RD (24MR) (BAT-000039) tiene stock bajo en Sede Principal: 2 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(433,1,NULL,'sistema','Stock bajo: 175/70R13 RAPID P329','El producto 175/70R13 RAPID P329 (NEU-000025) tiene stock bajo en Sede Principal: 2 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(434,1,NULL,'sistema','Stock bajo: 10W40 4T SINTETICO GULF POWER TRACK','El producto 10W40 4T SINTETICO GULF POWER TRACK (LUB-000073) tiene stock bajo en Sede Principal: 2 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(435,1,NULL,'sistema','Stock bajo: LT235/75R15 POWERTRAC WILDRANGER A/T','El producto LT235/75R15 POWERTRAC WILDRANGER A/T (NEU-000061) tiene stock bajo en Sede Principal: 2 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(436,1,NULL,'sistema','Stock bajo: P235/75R15 POWERTRAC WILDRANGER A/T','El producto P235/75R15 POWERTRAC WILDRANGER A/T (NEU-000063) tiene stock bajo en Sede Principal: 2 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(437,1,NULL,'sistema','Stock bajo: 275/55R20 WIDEWAY WEYONE AK3','El producto 275/55R20 WIDEWAY WEYONE AK3 (NEU-000178) tiene stock bajo en Sede Principal: 2 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:54'),(438,1,NULL,'sistema','Stock bajo: 235/75R15 WIDEWAY AK3 6PR','El producto 235/75R15 WIDEWAY AK3 6PR (NEU-000065) tiene stock bajo en Sede Principal: 2 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(439,1,NULL,'sistema','Stock bajo: 205/70R15 MAXTREK SU-830','El producto 205/70R15 MAXTREK SU-830 (NEU-000055) tiene stock bajo en Sede Principal: 2 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(440,1,NULL,'sistema','Stock bajo: 215/60R17 FIRESTONE FIREHAWK','El producto 215/60R17 FIRESTONE FIREHAWK (NEU-000147) tiene stock bajo en Sede Principal: 3 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(441,1,NULL,'sistema','Stock bajo: 20W50 VALVOLINE MINERAL 0.946L','El producto 20W50 VALVOLINE MINERAL 0.946L (LUB-000025) tiene stock bajo en Sede Principal: 3 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(442,1,NULL,'sistema','Stock bajo: ATF DEXRON III BITOIL PAILA 19L','El producto ATF DEXRON III BITOIL PAILA 19L (LUB-000078) tiene stock bajo en Sede Principal: 3 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(443,1,NULL,'sistema','Stock bajo: 20W50 MINERAL MEXLUB RACING SL 946ML','El producto 20W50 MINERAL MEXLUB RACING SL 946ML (LUB-000024) tiene stock bajo en Sede Principal: 3 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(444,1,NULL,'sistema','Stock bajo: 195R14C WIDEWAY','El producto 195R14C WIDEWAY (NEU-000044) tiene stock bajo en Sede Principal: 3 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(445,1,NULL,'sistema','Stock bajo: 15W40 MINERAL FC','El producto 15W40 MINERAL FC (LUB-000007) tiene stock bajo en Sede Principal: 3 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(446,1,NULL,'sistema','Stock bajo: SAE 80W90 TRANSMISION RALOY EXTREMA PRESION','El producto SAE 80W90 TRANSMISION RALOY EXTREMA PRESION (LUB-000088) tiene stock bajo en Sede Principal: 3 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(447,1,NULL,'sistema','Stock bajo: LT285/70R17 V-RICH ALL TERRAIN','El producto LT285/70R17 V-RICH ALL TERRAIN (NEU-000161) tiene stock bajo en Sede Principal: 4 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(448,1,NULL,'sistema','Stock bajo: 235/75R15 HILO HT','El producto 235/75R15 HILO HT (NEU-000067) tiene stock bajo en Sede Principal: 4 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(449,1,NULL,'sistema','Stock bajo: 15W40 MINERAL INCA','El producto 15W40 MINERAL INCA (LUB-000011) tiene stock bajo en Sede Principal: 4 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(450,1,NULL,'sistema','Stock bajo: 275/70R17 AOQISHI A/T','El producto 275/70R17 AOQISHI A/T (NEU-000154) tiene stock bajo en Sede Principal: 4 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(451,1,NULL,'sistema','Stock bajo: LT315/70R17 V-RICH ALL TERRAIN','El producto LT315/70R17 V-RICH ALL TERRAIN (NEU-000162) tiene stock bajo en Sede Principal: 4 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(452,1,NULL,'sistema','Stock bajo: 10W30 SEMI SINTETICO GULF TEC GDI','El producto 10W30 SEMI SINTETICO GULF TEC GDI (LUB-000029) tiene stock bajo en Sede Principal: 4 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(453,1,NULL,'sistema','Stock bajo: LT275/70R17 V-RICH ALL TERRAIN','El producto LT275/70R17 V-RICH ALL TERRAIN (NEU-000155) tiene stock bajo en Sede Principal: 4 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(454,1,NULL,'sistema','Stock bajo: LT245/75R16 POWERTRAC WILDRANGER A/T','El producto LT245/75R16 POWERTRAC WILDRANGER A/T (NEU-000103) tiene stock bajo en Sede Principal: 4 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(455,1,NULL,'sistema','Stock bajo: 235/70R16 NOVAMAXX AT','El producto 235/70R16 NOVAMAXX AT (NEU-000100) tiene stock bajo en Sede Principal: 4 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(456,1,NULL,'sistema','Stock bajo: 235/60R16 POWERTRAC ADAMAS','El producto 235/60R16 POWERTRAC ADAMAS (NEU-000099) tiene stock bajo en Sede Principal: 4 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(457,1,NULL,'sistema','Stock bajo: 195/65R15 WIDEWAY SAFEWAY','El producto 195/65R15 WIDEWAY SAFEWAY (NEU-000051) tiene stock bajo en Sede Principal: 4 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(458,1,NULL,'sistema','Stock bajo: 195/65R15 RAPID','El producto 195/65R15 RAPID (NEU-000053) tiene stock bajo en Sede Principal: 4 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(459,1,NULL,'sistema','Stock bajo: LT32X11.5R15 HILO X-TERRAIN MT1','El producto LT32X11.5R15 HILO X-TERRAIN MT1 (NEU-000086) tiene stock bajo en Sede Principal: 4 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(460,1,NULL,'sistema','Stock bajo: 31X10.50R15 RAPID MUD CONTENDER M/T','El producto 31X10.50R15 RAPID MUD CONTENDER M/T (NEU-000085) tiene stock bajo en Sede Principal: 4 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(461,1,NULL,'sistema','Stock bajo: 31X10.50R15 DURINGON CROSSMAXX','El producto 31X10.50R15 DURINGON CROSSMAXX (NEU-000082) tiene stock bajo en Sede Principal: 4 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(462,1,NULL,'sistema','Stock bajo: 31X10.50R15 V-RICH A/T','El producto 31X10.50R15 V-RICH A/T (NEU-000075) tiene stock bajo en Sede Principal: 4 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(463,1,NULL,'sistema','Stock bajo: LT265/75R16 POWERTRAC WILDRANGER A/T','El producto LT265/75R16 POWERTRAC WILDRANGER A/T (NEU-000107) tiene stock bajo en Sede Principal: 4 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(464,1,NULL,'sistema','Stock bajo: ACEITE ATF DEXRON III BITOIL 1L','El producto ACEITE ATF DEXRON III BITOIL 1L (LUB-000076) tiene stock bajo en Sede Principal: 4 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(465,1,NULL,'sistema','Stock bajo: LT265/75R16 V-RICH ALL TERRAIN','El producto LT265/75R16 V-RICH ALL TERRAIN (NEU-000115) tiene stock bajo en Sede Principal: 4 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(466,1,NULL,'sistema','Stock bajo: 15W40 SEMI SINTETICO DAUER','El producto 15W40 SEMI SINTETICO DAUER (LUB-000043) tiene stock bajo en Sede Principal: 4 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(467,1,NULL,'sistema','Stock bajo: 5W20 GONHER SINTETICO NANOTEK GOLD DE 946ML','El producto 5W20 GONHER SINTETICO NANOTEK GOLD DE 946ML (LUB-000061) tiene stock bajo en Sede Principal: 4 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(468,1,NULL,'sistema','Stock bajo: 7.50R16 ANNAITE DIRECCIONAL 14PR','El producto 7.50R16 ANNAITE DIRECCIONAL 14PR (NEU-000132) tiene stock bajo en Sede Principal: 4 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(469,1,NULL,'sistema','Stock bajo: 315/75R16 HILO X-TERRAIN MT1','El producto 315/75R16 HILO X-TERRAIN MT1 (NEU-000129) tiene stock bajo en Sede Principal: 4 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(470,1,NULL,'sistema','Stock bajo: 295/50R15 RAPID SHARK Z02','El producto 295/50R15 RAPID SHARK Z02 (NEU-000071) tiene stock bajo en Sede Principal: 4 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(471,1,NULL,'sistema','Stock bajo: 285/75R16 HILO X-TERRAIN MT1','El producto 285/75R16 HILO X-TERRAIN MT1 (NEU-000121) tiene stock bajo en Sede Principal: 4 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(472,1,NULL,'sistema','Stock bajo: LT265/75R16 NOVAMAX STAR A/T','El producto LT265/75R16 NOVAMAX STAR A/T (NEU-000118) tiene stock bajo en Sede Principal: 4 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(473,1,NULL,'sistema','Stock bajo: LT265/75R16 RAPID TUFTRAIL A/T','El producto LT265/75R16 RAPID TUFTRAIL A/T (NEU-000117) tiene stock bajo en Sede Principal: 4 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(474,1,NULL,'sistema','Stock bajo: ACEITE CK-4 10W30 RALOY GARRAFA 3.75L','El producto ACEITE CK-4 10W30 RALOY GARRAFA 3.75L (LUB-000075) tiene stock bajo en Sede Principal: 4 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(475,1,NULL,'sistema','Stock bajo: 185/65R14 DOUBLESTAR','El producto 185/65R14 DOUBLESTAR (NEU-000034) tiene stock bajo en Sede Principal: 5 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(476,1,NULL,'sistema','Stock bajo: 850 AMP EXTREME 24BI-720 (42M)','El producto 850 AMP EXTREME 24BI-720 (42M) (BAT-000024) tiene stock bajo en Sede Principal: 5 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(477,1,NULL,'sistema','Stock bajo: 165/70R13 FIRESTONE MULTIHAWK','El producto 165/70R13 FIRESTONE MULTIHAWK (NEU-000014) tiene stock bajo en Sede Principal: 5 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(478,1,NULL,'sistema','Stock bajo: 20W50 MINERAL GULF PRIDE 4T PLUS','El producto 20W50 MINERAL GULF PRIDE 4T PLUS (LUB-000070) tiene stock bajo en Sede Principal: 5 unidades (umbral: 5). Considere reponer inventario.','alta',0,NULL,NULL,'2026-06-11 06:57:55'),(479,NULL,'30396029','pago','Pago aprobado: pedido #16','Tu pago del pedido #16 fue aprobado. Ya puedes revisar el estado y el QR de factura en Mis pedidos.','media',0,NULL,NULL,'2026-06-11 07:00:35'),(480,NULL,'30396029','pago','Pago rechazado: pedido #17','Tu pago del pedido #17 fue rechazado. Motivo: ilegible. Revisa el detalle del pedido y carga un comprobante valido si corresponde.','alta',0,NULL,NULL,'2026-06-11 07:00:35'),(481,4,NULL,'ticket','Ticket #5 actualizado','Su ticket \'E2E ticket\' cambio a: en_revision','media',0,NULL,NULL,'2026-06-11 07:01:22');
/*!40000 ALTER TABLE `notificaciones` ENABLE KEYS */;
UNLOCK TABLES;


DROP TABLE IF EXISTS `ordenes_compra`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ordenes_compra` (
  `id_orden_compra` int(11) NOT NULL AUTO_INCREMENT,
  `proveedor_rif` varchar(20) NOT NULL,
  `sucursal_id` int(11) NOT NULL,
  `fecha_orden_compra` timestamp NOT NULL DEFAULT current_timestamp(),
  `total_orden_compra` decimal(12,2) DEFAULT 0.00,
  `estado` varchar(30) NOT NULL DEFAULT 'pendiente',
  `observaciones_orden_compra` varchar(1000) DEFAULT NULL,
  PRIMARY KEY (`id_orden_compra`),
  KEY `proveedor_rif` (`proveedor_rif`),
  KEY `sucursal_id` (`sucursal_id`),
  CONSTRAINT `ordenes_compra_ibfk_1` FOREIGN KEY (`proveedor_rif`) REFERENCES `proveedores` (`rif_proveedor`) ON UPDATE CASCADE,
  CONSTRAINT `ordenes_compra_ibfk_2` FOREIGN KEY (`sucursal_id`) REFERENCES `sucursales` (`id_sucursal`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `ordenes_compra` WRITE;
/*!40000 ALTER TABLE `ordenes_compra` DISABLE KEYS */;
INSERT INTO `ordenes_compra` VALUES (1,'J-50722410-0',1,'2026-06-02 23:38:42',890.00,'comprado','');
/*!40000 ALTER TABLE `ordenes_compra` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_ordenes_compra_insert` AFTER INSERT ON ordenes_compra FOR EACH ROW BEGIN
        INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (COALESCE(@current_usuario_id, 1), 'CREAR', 'ORDEN_COMPRA', CONCAT('Orden de compra creada ID: ', NEW.id_orden_compra), COALESCE(@current_ip, '127.0.0.1'));
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_ordenes_compra_update` AFTER UPDATE ON ordenes_compra FOR EACH ROW BEGIN
        INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (COALESCE(@current_usuario_id, 1), 'MODIFICAR', 'ORDEN_COMPRA', CONCAT('Orden de compra modificada ID: ', NEW.id_orden_compra), COALESCE(@current_ip, '127.0.0.1'));
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;


DROP TABLE IF EXISTS `ordenes_venta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ordenes_venta` (
  `id_orden_venta` int(11) NOT NULL AUTO_INCREMENT,
  `cliente_cedula` varchar(20) NOT NULL,
  `sucursal_id` int(11) DEFAULT NULL,
  `fecha_orden_venta` timestamp NOT NULL DEFAULT current_timestamp(),
  `total_orden_venta` decimal(12,2) DEFAULT 0.00,
  `estado` varchar(30) NOT NULL DEFAULT 'pendiente',
  `metodo_pago_id` int(11) DEFAULT NULL,
  `tasa_cambio_id` int(11) DEFAULT NULL,
  `tipo_pago` varchar(20) NOT NULL DEFAULT 'contado',
  PRIMARY KEY (`id_orden_venta`),
  KEY `sucursal_id` (`sucursal_id`),
  KEY `estado` (`estado`),
  KEY `idx_ordenes_venta_cliente` (`cliente_cedula`),
  KEY `fk_ordenes_venta_metodo_pago` (`metodo_pago_id`),
  KEY `fk_ordenes_venta_tasa_cambio` (`tasa_cambio_id`),
  KEY `idx_orden_estado_fecha` (`estado`,`fecha_orden_venta`),
  CONSTRAINT `fk_ordenes_venta_metodo_pago` FOREIGN KEY (`metodo_pago_id`) REFERENCES `metodos_pago` (`id_metodo_pago`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_ordenes_venta_tasa_cambio` FOREIGN KEY (`tasa_cambio_id`) REFERENCES `tasas_cambio` (`id_tasa_cambio`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `ordenes_venta_ibfk_1` FOREIGN KEY (`cliente_cedula`) REFERENCES `cliente` (`identificador_cliente`) ON UPDATE CASCADE,
  CONSTRAINT `ordenes_venta_ibfk_2` FOREIGN KEY (`sucursal_id`) REFERENCES `sucursales` (`id_sucursal`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `ordenes_venta` WRITE;
/*!40000 ALTER TABLE `ordenes_venta` DISABLE KEYS */;
INSERT INTO `ordenes_venta` VALUES (1,'V-00000000',NULL,'2026-05-18 04:33:01',42.00,'aprobada',2,5,'contado'),(2,'V-00000000',NULL,'2026-05-21 06:08:01',35.00,'rechazada',1,7,'contado'),(8,'J-55656666-5',NULL,'2026-05-29 08:15:01',777777.00,'pendiente',NULL,9,'credito'),(9,'V-00000000',NULL,'2026-06-03 15:39:55',89.00,'rechazada',1,11,'contado'),(10,'J-55656666-5',NULL,'2026-06-08 07:57:20',333333.00,'pendiente',NULL,15,'credito'),(11,'V-00000000',NULL,'2026-06-08 21:17:57',595.00,'aprobada',7,15,'contado'),(12,'V-00000000',NULL,'2026-06-10 21:09:31',20.00,'pendiente',7,16,'contado'),(13,'30396029',1,'2026-06-11 06:14:42',70.00,'aprobada',3,16,'contado'),(14,'J-55656666-5',NULL,'2026-06-11 06:17:58',100.00,'pendiente',NULL,16,'credito');
/*!40000 ALTER TABLE `ordenes_venta` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_bitacora_ordenes_venta_insert AFTER INSERT ON ordenes_venta FOR EACH ROW BEGIN INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip) VALUES (COALESCE(@current_usuario_id, 1), 'CREAR', 'ORDENES', CONCAT('Orden registrada ID: ', NEW.id_orden_venta), COALESCE(@current_ip, '127.0.0.1')); END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_stock_orden_aprobada AFTER UPDATE ON ordenes_venta FOR EACH ROW
        BEGIN
            IF NEW.estado = 'aprobada' AND OLD.estado IN ('pendiente', 'procesando') THEN
                UPDATE stock s
                INNER JOIN detalle_orden_venta_productos d ON d.producto_codigo = s.producto_codigo
                    AND d.orden_id = NEW.id_orden_venta
                SET s.stock = s.stock - d.cantidad_detalle_orden_venta_producto
                WHERE (NEW.sucursal_id IS NULL OR s.sucursal_id = NEW.sucursal_id);
            ELSEIF OLD.estado = 'aprobada' AND NEW.estado IN ('rechazada', 'cancelada', 'anulada') THEN
                UPDATE stock s
                INNER JOIN detalle_orden_venta_productos d ON d.producto_codigo = s.producto_codigo
                    AND d.orden_id = NEW.id_orden_venta
                SET s.stock = s.stock + d.cantidad_detalle_orden_venta_producto
                WHERE (NEW.sucursal_id IS NULL OR s.sucursal_id = NEW.sucursal_id);
            END IF;
        END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_bitacora_ordenes_venta_update AFTER UPDATE ON ordenes_venta FOR EACH ROW BEGIN INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip) VALUES (COALESCE(@current_usuario_id, 1), 'MODIFICAR', 'ORDENES', CONCAT('Orden modificada ID: ', NEW.id_orden_venta), COALESCE(@current_ip, '127.0.0.1')); END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;


DROP TABLE IF EXISTS `pagos_credito`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `pagos_credito` (
  `id_pago_credito` int(11) NOT NULL AUTO_INCREMENT,
  `id_credito` int(11) NOT NULL,
  `monto_pago` decimal(12,2) NOT NULL,
  `fecha_pago` timestamp NOT NULL DEFAULT current_timestamp(),
  `observaciones_pago` varchar(500) DEFAULT NULL,
  `revertido` tinyint(1) NOT NULL DEFAULT 0,
  `fecha_reversion` datetime DEFAULT NULL,
  PRIMARY KEY (`id_pago_credito`),
  KEY `fk_pago_credito` (`id_credito`),
  CONSTRAINT `fk_pago_credito` FOREIGN KEY (`id_credito`) REFERENCES `creditos_orden_venta` (`id_credito`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `pagos_credito` WRITE;
/*!40000 ALTER TABLE `pagos_credito` DISABLE KEYS */;
INSERT INTO `pagos_credito` VALUES (1,1,555755.00,'2026-06-11 01:06:33','Migracion: abonos previos consolidados',0,NULL);
/*!40000 ALTER TABLE `pagos_credito` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_bitacora_pagos_credito_insert AFTER INSERT ON pagos_credito FOR EACH ROW BEGIN INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip) VALUES (COALESCE(@current_usuario_id, 1), 'CREAR', 'CREDITO', CONCAT('Abono registrado credito: ', NEW.id_credito, ' por $', NEW.monto_pago), COALESCE(@current_ip, '127.0.0.1')); END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;


DROP TABLE IF EXISTS `productos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `productos` (
  `codigo` varchar(50) NOT NULL,
  `nombre_producto` varchar(200) NOT NULL,
  `descripcion_producto` text DEFAULT NULL,
  `precio_producto` decimal(10,2) NOT NULL DEFAULT 0.00,
  `categoria` varchar(150) DEFAULT NULL,
  `marca` varchar(150) DEFAULT NULL,
  `imagen_producto` varchar(200) DEFAULT 'default_product.png',
  `estado` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`codigo`),
  KEY `marca` (`marca`),
  KEY `fk_productos_categoria` (`categoria`),
  CONSTRAINT `fk_productos_categoria` FOREIGN KEY (`categoria`) REFERENCES `categorias` (`nombre_categoria`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `productos_ibfk_2` FOREIGN KEY (`marca`) REFERENCES `marcas` (`nombre_marca`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `productos` WRITE;
/*!40000 ALTER TABLE `productos` DISABLE KEYS */;
INSERT INTO `productos` VALUES ('BAT-000016','600 AMP EXTREME 36DLM700 (36MR)','Bateria 600 AMP. EXTREME 36DLM700 (36MR)',50.00,'Baterias','EXTREME 36DLM700 (36MR)','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('BAT-000017','650 AMP MOURA ME310FD (36MR)','Bateria 650 AMP. MOURA ME310FD (36MR)',70.00,'Baterias','MOURA ME310FD (36MR)','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('BAT-000018','650 AMP DURACELL 99-650 (36MR)','Bateria 650 AMP. DURACELL 99-650 (36MR)',65.00,'Baterias','DURACELL 99-650 (36MR)','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('BAT-000019','700 AMP ARO 99R-700','Bateria 700 AMP. ARO 99R-700',62.00,'Baterias','ARO 99R-700','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('BAT-000020','650 AMP MOURA ME805D (36MR)','Bateria 650 AMP. MOURA ME805D (36MR)',85.00,'Baterias','MOURA ME805D (36MR)','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('BAT-000023','800 AMP MOURA ME570GI (22M)','Bateria 800 AMP. MOURA ME570GI (22M)',92.00,'Baterias','MOURA ME570GI (22M)','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('BAT-000024','850 AMP EXTREME 24BI-720 (42M)','Bateria 850 AMP. EXTREME 24BI-720 (42M)',65.00,'Baterias','EXTREME 24BI-720 (42M)','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('BAT-000025','850 AMP EXTREME 24BD-720 (42MR)','Bateria 850 AMP. EXTREME 24BD-720 (42MR)',65.00,'Baterias','EXTREME 24BD-720 (42MR)','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('BAT-000033','900 AMP DURACELL 42-900 (42MR)','Bateria 900 AMP. DURACELL 42-900 (42MR)',81.00,'Baterias','DURACELL 42-900 (42MR)','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('BAT-000034','900 AMP DURACELL 42R-900 (42M)','Bateria 900 AMP. DURACELL 42R-900 (42M)',81.00,'Baterias','DURACELL 42R-900 (42M)','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('BAT-000035','900 AMP ARO 42-900 (42MR)','Bateria 900 AMP. ARO 42-900 (42MR)',80.00,'Baterias','ARO 42-900 (42MR)','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('BAT-000036','900 AMP ARO 42R-900 (42M)','Bateria 900 AMP. ARO 42R-900 (42M)',80.00,'Baterias','ARO 42R-900 (42M)','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('BAT-000039','1000 AMP MOURA ME650RD (24MR)','Bateria 1000 AMP. MOURA ME650RD (24MR)',122.00,'Baterias','MOURA ME650RD (24MR)','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('BAT-000040','1100 AMP ARO 315-1100 (TORNILLO)','Bateria 1100 AMP. ARO 315-1100 (TORNILLO)',112.00,'Baterias','ARO 315-1100 (TORNILLO)','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('BAT-000041','1000 AMP DURACELL 24-1000 (24MR)','Bateria 1000 AMP. DURACELL 24-1000 (24MR)',89.00,'Baterias','DURACELL 24-1000 (24MR)','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('BAT-000042','1000 AMP DURACELL 24F-1000 (24M)','Bateria 1000 AMP. DURACELL 24F-1000 (24M)',89.00,'Baterias','DURACELL 24F-1000 (24M)','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('BAT-000043','1000 AMP EXTREMA 24AD1000-A (24MR)','Bateria 1000 AMP. EXTREMA 24AD1000-A (24MR)',85.00,'Baterias','EXTREMA 24AD1000-A (24MR)','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('BAT-000044','1100 AMP ARO 24R - 1100','Bateria 1100 AMP. ARO 24R - 1100',92.00,'Baterias','ARO 24R - 1100','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('BAT-000045','1100 AMP ARO 24 - 1100','Bateria 1100 AMP. ARO 24 - 1100',92.00,'Baterias','ARO 24 - 1100','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('BAT-000046','1100 AMP DURACELL 34 - 1100','Bateria 1100 AMP. DURACELL 34 - 1100',94.00,'Baterias','DURACELL 34 - 1100','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('BAT-000047','1100 AMP DURACEL 34R - 1100','Bateria 1100 AMP. DURACEL 34R - 1100',94.00,'Baterias','DURACEL 34R - 1100','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('BAT-000048','1300 AMP DURACELL 31 - 1300S (TORNILLO)','Bateria 1300 AMP. DURACELL 31 - 1300S (TORNILLO)',120.00,'Baterias','DURACELL 31 - 1300S (TORNILLO)','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('BAT-ACD-75-650','ACDelco bateria 75-650 CCA 12V','Bateria automotriz 12V con 650 CCA para vehiculos medianos.',120.00,'Baterias','ACDelco','default_product.png',0,'2026-05-27 14:10:55','2026-05-28 02:32:34'),('CAU-FIR-DEST-24570R16','Firestone Destination A/T2 245/70R16','Caucho all terrain para uso diario y caminos rurales.',175.00,'Cauchos','Firestone','default_product.png',0,'2026-05-27 14:10:55','2026-05-28 02:32:34'),('CAU-MIC-LTX-26565R17','Michelin LTX A/T2 265/65R17','Caucho all terrain para camionetas, uso mixto carretera y terrenos irregulares.',215.00,'Cauchos','Michelin','default_product.png',0,'2026-05-27 14:10:55','2026-05-28 02:32:34'),('CAU-PIR-SCORP-26570R16','Pirelli Scorpion All Terrain Plus 265/70R16','Caucho todo terreno con buen agarre en asfalto, tierra y lluvia.',198.00,'Cauchos','Pirelli','default_product.png',0,'2026-05-27 14:10:55','2026-05-28 02:32:34'),('CMB-000004','ACEITE 20W50 MINERAL GULF','Combo de producto y servicio. GULF',9.61,'Combos','ACEITE 20W50 MINERAL GULF','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000005','ACEITE 20W50 SEMI SINTETICO GULF','Combo de producto y servicio. GULF',11.95,'Combos','ACEITE 20W50 SEMI SINTETICO GULF','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000006','ACEITE 15W40 MINERAL GULF','Combo de producto y servicio. GULF',9.61,'Combos','ACEITE 15W40 MINERAL GULF','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000007','ACEITE 15W40 SEMI SINTETICO GULF','Combo de producto y servicio. GULF',11.95,'Combos','ACEITE 15W40 SEMI SINTETICO GULF','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000008','ACEITE 10W30 SEMI SINTETICO GULF','Combo de producto y servicio. GULF',12.05,'Combos','ACEITE 10W30 SEMI SINTETICO GULF','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000009','ACEITE 5W20 SINTETICO GULF','Combo de producto y servicio. GULF',13.22,'Combos','ACEITE 5W20 SINTETICO GULF','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000010','ACEITE 5W30 SINTETICO GULF','Combo de producto y servicio. GULF',13.22,'Combos','ACEITE 5W30 SINTETICO GULF','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000011','ACEITE 5W40 SINTETICO GUL','Combo de producto y servicio. GULF',13.22,'Combos','ACEITE 5W40 SINTETICO GUL','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000016','ACEITE 20W50 MINERAL RALOY','Combo de producto y servicio. RALOY / INCA / BOSS',7.69,'Combos','ACEITE 20W50 MINERAL RALOY','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000017','ACEITE 20W50 MINERAL INCA','Combo de producto y servicio. RALOY / INCA / BOSS',7.55,'Combos','ACEITE 20W50 MINERAL INCA','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000018','ACEITE 20W50 SEMI SINTETICO RALOY','Combo de producto y servicio. RALOY / INCA / BOSS',8.30,'Combos','ACEITE 20W50 SEMI SINTETICO RALOY','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000019','ACEITE 20W50 SEMI SINTETICO INCA','Combo de producto y servicio. RALOY / INCA / BOSS',8.11,'Combos','ACEITE 20W50 SEMI SINTETICO INCA','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000020','ACEITE 15W40 MINERAL RALOY','Combo de producto y servicio. RALOY / INCA / BOSS',7.69,'Combos','ACEITE 15W40 MINERAL RALOY','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000021','ACEITE 15W40 MINERAL INCA','Combo de producto y servicio. RALOY / INCA / BOSS',7.52,'Combos','ACEITE 15W40 MINERAL INCA','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000022','ACEITE 15W40 SEMI SINTETICO RALOY','Combo de producto y servicio. RALOY / INCA / BOSS',8.30,'Combos','ACEITE 15W40 SEMI SINTETICO RALOY','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000023','ACEITE 15W40 SEMI SINTETICO INCA','Combo de producto y servicio. RALOY / INCA / BOSS',8.04,'Combos','ACEITE 15W40 SEMI SINTETICO INCA','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000024','ACEITE 20W50 MINERAL BOSS','Combo de producto y servicio. RALOY / INCA / BOSS',5.15,'Combos','ACEITE 20W50 MINERAL BOSS','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000025','ACEITE 15W40 SEMI SINTETICO BOSS','Combo de producto y servicio. RALOY / INCA / BOSS',5.34,'Combos','ACEITE 15W40 SEMI SINTETICO BOSS','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000030','ACEITE 20W50 MINERAL VALVOLINE','Combo de producto y servicio. VALVOLINE / FC',8.20,'Combos','ACEITE 20W50 MINERAL VALVOLINE','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000031','ACEITE 20W50 MINERAL FC','Combo de producto y servicio. VALVOLINE / FC',5.66,'Combos','ACEITE 20W50 MINERAL FC','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000032','ACEITE 20W50 MINERAL MOBIL','Combo de producto y servicio. VALVOLINE / FC',6.38,'Combos','ACEITE 20W50 MINERAL MOBIL','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000033','ACEITE 20W50 SEMI SINTETICO VALVOLINE','Combo de producto y servicio. VALVOLINE / FC',8.34,'Combos','ACEITE 20W50 SEMI SINTETICO VALVOLINE','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000034','ACEITE 20W50 SEMI SINTETICO FC','Combo de producto y servicio. VALVOLINE / FC',8.34,'Combos','ACEITE 20W50 SEMI SINTETICO FC','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000035','ACEITE 10W40 SEMI SINTETICO MOBIL','Combo de producto y servicio. VALVOLINE / FC',7.93,'Combos','ACEITE 10W40 SEMI SINTETICO MOBIL','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000036','ACEITE 15W40 MINERAL VALVOLINE','Combo de producto y servicio. VALVOLINE / FC',8.20,'Combos','ACEITE 15W40 MINERAL VALVOLINE','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000037','ACEITE 15W40 MINERAL FC','Combo de producto y servicio. VALVOLINE / FC',5.66,'Combos','ACEITE 15W40 MINERAL FC','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000038','ACEITE 15W40 SEMI SINTETICO VALVOLINE','Combo de producto y servicio. VALVOLINE / FC',8.34,'Combos','ACEITE 15W40 SEMI SINTETICO VALVOLINE','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000039','15W40 SEMI SINTETICO VALVOLINE GARRAFA','Combo de producto y servicio. VALVOLINE / FC',29.90,'Combos','15W40 SEMI SINTETICO VALVOLINE GARRAFA','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000040','ACEITE 15W40 SEMI SINTETICO FC','Combo de producto y servicio. VALVOLINE / FC',6.45,'Combos','ACEITE 15W40 SEMI SINTETICO FC','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000041','15W40 / 20W50 SEMI SINTETICO FC GARRAFA','Combo de producto y servicio. VALVOLINE / FC',23.23,'Combos','15W40 / 20W50 SEMI SINTETICO FC GARRAFA','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000046','ACEITE 20W50 MINERAL ROSHFRANS','Combo de producto y servicio. WOLF / MEXLUB / ROSHFRANS',8.22,'Combos','ACEITE 20W50 MINERAL ROSHFRANS','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000047','ACEITE 20W50 MINERAL MEXLUB','Combo de producto y servicio. WOLF / MEXLUB / ROSHFRANS',8.92,'Combos','ACEITE 20W50 MINERAL MEXLUB','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000048','ACEITE 20W50 SEMI SINTETICO MEXLUB','Combo de producto y servicio. WOLF / MEXLUB / ROSHFRANS',8.67,'Combos','ACEITE 20W50 SEMI SINTETICO MEXLUB','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000049','ACEITE 15W40 MINERAL ROSHFRANS','Combo de producto y servicio. WOLF / MEXLUB / ROSHFRANS',8.22,'Combos','ACEITE 15W40 MINERAL ROSHFRANS','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000050','ACEITE 15W40 MINERAL MEXLUB','Combo de producto y servicio. WOLF / MEXLUB / ROSHFRANS',9.16,'Combos','ACEITE 15W40 MINERAL MEXLUB','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000051','ACEITE 15W40 SEMI SINTETICO MEXLUB','Combo de producto y servicio. WOLF / MEXLUB / ROSHFRANS',9.06,'Combos','ACEITE 15W40 SEMI SINTETICO MEXLUB','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000052','ACEITE 15W40 SEMI SINTETICO WOLF','Combo de producto y servicio. WOLF / MEXLUB / ROSHFRANS',8.22,'Combos','ACEITE 15W40 SEMI SINTETICO WOLF','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('CMB-000053','ACEITE 20W50 MINERAL MOTUL','Combo de producto y servicio. WOLF / MEXLUB / ROSHFRANS',10.63,'Combos','ACEITE 20W50 MINERAL MOTUL','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('COD0507224100','Producto 0507224100','Producto prueba',20.00,'TestCat0507224100','TestBrand0507224100','default_product.png',0,'2026-05-08 02:41:00','2026-05-22 05:57:16'),('DEDE','dede','dede',3233.00,'Baterias','15W40 / 20W50 SEMI SINTETICO FC GARRAFA','default_product.png',1,'2026-06-02 21:37:09','2026-06-02 21:37:09'),('FIL-BOS-AIR-COR','Bosch filtro de aire Toyota Corolla','Filtro de aire para Toyota Corolla 2009-2014.',18.00,'Filtros','Bosch','default_product.png',0,'2026-05-27 14:10:55','2026-05-28 02:32:34'),('FIL-BOS-OIL-TOY','Bosch filtro de aceite Toyota','Filtro de aceite compatible con motores Toyota seleccionados.',12.00,'Filtros','Bosch','default_product.png',0,'2026-05-27 14:10:55','2026-05-28 02:32:34'),('FRE-BOS-BP-COR','Bosch pastillas de freno Toyota Corolla','Juego de pastillas delanteras para Toyota Corolla 2009-2014.',42.00,'Frenos','Bosch','default_product.png',0,'2026-05-27 14:10:55','2026-05-28 02:32:34'),('LUB-000005','15W40 MINERAL BRAVA S/N','Lubricante 15W40 MINERAL. BRAVA',7.00,'Lubricantes','BRAVA','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000006','15W40 MINERAL ARMAX','Lubricante 15W40 MINERAL. ARMAX',5.00,'Lubricantes','ARMAX','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000007','15W40 MINERAL FC','Lubricante 15W40 MINERAL. FC FAUCI',5.00,'Lubricantes','FC FAUCI','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000008','15W40 MINERAL GULF MAX GDI','Lubricante 15W40 MINERAL. GULF',9.00,'Lubricantes','GULF','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000009','15W40 MINERAL DAUER','Lubricante 15W40 MINERAL. DAUER',7.50,'Lubricantes','DAUER','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000010','15W40 MINERAL AKRON','Lubricante 15W40 MINERAL. AKRON',7.50,'Lubricantes','AKRON','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000011','15W40 MINERAL INCA','Lubricante 15W40 MINERAL. INCA',8.50,'Lubricantes','INCA','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000012','15W40 MINERAL VALVOLINE CLASSIC','Lubricante 15W40 MINERAL. VALVOLINE',7.50,'Lubricantes','VALVOLINE','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000013','20W50 MINERAL ATLANTIC','Lubricante 20W50 MINERAL. ATLANTIC OIL',4.50,'Lubricantes','ATLANTIC OIL','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000014','20W50 MINERAL FC','Lubricante 20W50 MINERAL. FC FAUCI',6.00,'Lubricantes','FC FAUCI','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000015','15W40 MINERAL ARMAX','Lubricante 20W50 MINERAL. ARMAX',5.00,'Lubricantes','ARMAX','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000016','20W50 MINERAL GONHER','Lubricante 20W50 MINERAL. GONHER',6.50,'Lubricantes','GONHER','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000017','20W50 MINERAL AKRON','Lubricante 20W50 MINERAL. AKRON',7.50,'Lubricantes','AKRON','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000018','20W50 MINERAL BITOIL','Lubricante 20W50 MINERAL. BITOIL',4.00,'Lubricantes','BITOIL','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000019','20W50 MINERAL RALOY RACING OIL MULTIGRADE','Lubricante 20W50 MINERAL. RALOY',7.00,'Lubricantes','RALOY','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000020','20W50 MINERAL DAUER','Lubricante 20W50 MINERAL. DAUER',7.50,'Lubricantes','DAUER','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000021','20W50 MINERAL BRAVA S/N','Lubricante 20W50 MINERAL. BRAVA',7.00,'Lubricantes','BRAVA','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000022','20W50 MINERAL GULF MAX GDI','Lubricante 20W50 MINERAL. GULF',9.00,'Lubricantes','GULF','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000023','20W50 MINERAL INCA','Lubricante 20W50 MINERAL. INCA',8.50,'Lubricantes','INCA','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000024','20W50 MINERAL MEXLUB RACING SL 946ML','Lubricante 20W50 MINERAL. MEXLUB',6.00,'Lubricantes','MEXLUB','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000025','20W50 VALVOLINE MINERAL 0.946L','Lubricante 20W50 MINERAL. VALVOLINE',7.50,'Lubricantes','VALVOLINE','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000026','20W50 MINERAL MOBIL SUPER 1000','Lubricante 20W50 MINERAL. MOBIL',8.00,'Lubricantes','MOBIL','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000027','20W50 MINERAL VM LUB','Lubricante 20W50 MINERAL. VM LUB',5.00,'Lubricantes','VM LUB','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000028','25W60 MINERAL BOSS','Lubricante 25W60 MINERAL. BOSS',4.50,'Lubricantes','BOSS','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000029','10W30 SEMI SINTETICO GULF TEC GDI','Lubricante 10W30 SEMI SINTETICO. GULF',11.00,'Lubricantes','GULF','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000030','10W30 SEMI SINTETICO VALVOLINE','Lubricante 10W30 SEMI SINTETICO. VALVOLINE',7.50,'Lubricantes','VALVOLINE','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000031','10W30 SEMI SINTETICO DAUER','Lubricante 10W30 SEMI SINTETICO. DAUER',9.00,'Lubricantes','DAUER','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000032','10W30 SEMI SINTETICO MOBIL','Lubricante 10W30 SEMI SINTETICO. MOBIL',9.50,'Lubricantes','MOBIL','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000033','10W40 SEMI SINTETICO MOBIL SUPER 2000','Lubricante 10W40 SEMI SINTETICO. MOBIL',10.00,'Lubricantes','MOBIL','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000034','15W40 SEMI SINTETICO BOSS','Lubricante 15W40 SEMI SINTETICO. BOSS',5.00,'Lubricantes','BOSS','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000035','ACEITE 20W50 SEMI SINTETICO BRAVA','Lubricante 15W40 SEMI SINTETICO. BRAVA',7.40,'Lubricantes','BRAVA','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000036','15W40 SEMI SINTETICO ARMAX','Lubricante 15W40 SEMI SINTETICO. ARMAX',5.00,'Lubricantes','ARMAX','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000037','15W40 SEMI SINTETICO GONHER','Lubricante 15W40 SEMI SINTETICO. GONHER',8.00,'Lubricantes','GONHER','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000038','15W40 SEMI SINTETICO AKRON','Lubricante 15W40 SEMI SINTETICO. AKRON',8.00,'Lubricantes','AKRON','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000039','15W40 SEMI SINTETICO BRAVA','Lubricante 15W40 SEMI SINTETICO. BRAVA',7.00,'Lubricantes','BRAVA','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000040','15W40 SEMI SINTETICO FC','Lubricante 15W40 SEMI SINTETICO. FC FAUCI',7.00,'Lubricantes','FC FAUCI','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000041','15W40 TEC GDI GULF SEMI-SINTETICO AVANZADO 1L','Lubricante 15W40 SEMI SINTETICO. GULF',11.00,'Lubricantes','GULF','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000042','15W40 SEMI SINTETICO OILSTONE','Lubricante 15W40 SEMI SINTETICO. OILSTONE',7.00,'Lubricantes','OILSTONE','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000043','15W40 SEMI SINTETICO DAUER','Lubricante 15W40 SEMI SINTETICO. DAUER',8.00,'Lubricantes','DAUER','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000044','15W40 SEMI SINTETICO 3.78L VALVOLINE','Lubricante 15W40 SEMI SINTETICO. VALVOLINE',29.00,'Lubricantes','VALVOLINE','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000045','15W40 VALVOLINE PREMIUM PROTETION SEMI-SINTETICO','Lubricante 15W40 SEMI SINTETICO. VALVOLINE',7.50,'Lubricantes','VALVOLINE','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000046','15W40 SEMI SINTETICO INCA','Lubricante 15W40 SEMI SINTETICO. INCA',9.00,'Lubricantes','INCA','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000047','15W40 SEMI SINTETICO VM LUB','Lubricante 15W40 SEMI SINTETICO. VM LUBRICANTES',5.00,'Lubricantes','VM LUBRICANTES','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000048','15W40 EVOLUB SKY','Lubricante 15W40 SEMI SINTETICO. SKY',8.00,'Lubricantes','SKY','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000049','20W50 PREMIUM BLEND VALVOLINE SEMI-SINTETICO 0.946L','Lubricante 20W50 SEMI SINTETICO. VALVOLINE',7.50,'Lubricantes','VALVOLINE','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000050','20W50 SEMI SINTETICO FC','Lubricante 20W50 SEMI SINTETICO. FC FAUCI',7.00,'Lubricantes','FC FAUCI','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000051','20W50 SEMI SINTETICO BRAVA','Lubricante 20W50 SEMI SINTETICO. BRAVA',7.00,'Lubricantes','BRAVA','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000052','20W50 SEMI SINTETICO ARMAX','Lubricante 20W50 SEMI SINTETICO. ARMAX',5.00,'Lubricantes','ARMAX','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000053','20W50 SEMI SINTETICO VM LUB','Lubricante 20W50 SEMI SINTETICO. VM LUBRICANTES',5.00,'Lubricantes','VM LUBRICANTES','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000054','20W50 SEMI SINTETICO BOSS','Lubricante 20W50 SEMI SINTETICO. BOSS',5.00,'Lubricantes','BOSS','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000055','20W50 SEMI SINTETICO DAUER','Lubricante 20W50 SEMI SINTETICO. DAUER',8.00,'Lubricantes','DAUER','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000056','20W50 SEMI SINTETICO FC GALON 3.78L','Lubricante 20W50 SEMI SINTETICO. FC FAUCI',22.00,'Lubricantes','FC FAUCI','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000057','20W50 MAX ULTRA GULF SEMI-SINTETICO','Lubricante 20W50 SEMI SINTETICO. GULF',10.00,'Lubricantes','GULF','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000058','20W50 SEMI SINTETICO INCA','Lubricante 20W50 SEMI SINTETICO. INCA',9.00,'Lubricantes','INCA','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000059','20W50 EVOLUB SKY SENI SINTETICO','Lubricante 20W50 SEMI SINTETICO. SKY',8.00,'Lubricantes','SKY','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000060','OW20 GONHER NANOTEK GOLD 100% SINTETICO 946 ML','Lubricante 0W20 SINTETICO. GONHER',7.00,'Lubricantes','GONHER','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000061','5W20 GONHER SINTETICO NANOTEK GOLD DE 946ML','Lubricante 5W20 SINTETICO. GONHER',7.00,'Lubricantes','GONHER','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000062','5W20 GULF ULTRASYNTH GDI','Lubricante 5W20 SINTETICO. GULF',8.00,'Lubricantes','GULF','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000063','5W-20 SHELL HELIX HX7 SP SINTETICO 1L','Lubricante 5W20 SINTETICO. SHELL HELIX',8.00,'Lubricantes','SHELL HELIX','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000064','5W30 GULF FORMULA CX FULL SINTETICO','Lubricante 5W30 SINTETICO. GULF',8.00,'Lubricantes','GULF','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000065','5W30 FULL SINTETICO VALVOLINE','Lubricante 5W30 SINTETICO. VALVOLINE',10.00,'Lubricantes','VALVOLINE','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000066','5W30 SINTETICO MOBIL','Lubricante 5W30 SINTETICO. MOBIL',8.00,'Lubricantes','MOBIL','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000067','5W30 SINTETICO MOTORCRAFT','Lubricante 5W30 SINTETICO. MOTORCRAFT',9.50,'Lubricantes','MOTORCRAFT','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000068','5W30 SINTETICO WOLF ECOTECH SP-RP G6','Lubricante 5W30 SINTETICO. WOLF',11.00,'Lubricantes','WOLF','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000069','5W40 GULF FORMULA CX FULL SINTETICO','Lubricante 5W40 SINTETICO. GULF',8.00,'Lubricantes','GULF','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000070','20W50 MINERAL GULF PRIDE 4T PLUS','Lubricante 20W50 4T MINERAL. GULF',9.50,'Lubricantes','GULF','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000071','20W50 MINERAL 4T VM LUB','Lubricante 20W50 4T MINERAL. VM LUB',4.50,'Lubricantes','VM LUB','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000072','20W50 4TCH VALVOLINE MINERAL','Lubricante 20W50 4T MINERAL. VALVOLINE',7.00,'Lubricantes','VALVOLINE','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000073','10W40 4T SINTETICO GULF POWER TRACK','Lubricante 10W40 4T SINTETICO. GULF',15.00,'Lubricantes','GULF','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000074','15W50 4T INCA','Lubricante 10W50 4T SINTETICO. INCA',4.00,'Lubricantes','INCA','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000075','ACEITE CK-4 10W30 RALOY GARRAFA 3.75L','Lubricante 10W30 DIESEL. RALOY',26.00,'Lubricantes','RALOY','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000076','ACEITE ATF DEXRON III BITOIL 1L','Lubricante DEXRON III. BITOIL',4.00,'Lubricantes','BITOIL','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000077','ACEITE SAE 15W40 BITOIL MINERAL','Lubricante DEXRON III. BITOIL',3.98,'Lubricantes','BITOIL','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000078','ATF DEXRON III BITOIL PAILA 19L','Lubricante DEXRON III. BITOIL',51.00,'Lubricantes','BITOIL','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000079','ACEITE HIDRAULICO ATF III DAUER','Lubricante DEXRON III. DAUER',7.50,'Lubricantes','DAUER','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000080','ATF DX III GULF CAJA DE ACEITE AUTOMATICO DE 1L','Lubricante DEXRON III. GULF',8.00,'Lubricantes','GULF','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000081','ACEITE ATF-3 MEXLUB PARA TRANSMISIONES AUT','Lubricante DEXRON III. MEXLUB',7.00,'Lubricantes','MEXLUB','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000082','VALVULINA 80W90 BITOIL 1L','Lubricante 89W90. BITOIL',4.00,'Lubricantes','BITOIL','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000083','VALVULINA 85W140 BITOIL 1L','Lubricante 89W90. BITOIL',3.98,'Lubricantes','BITOIL','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000084','ACEITE FC 20W50 SEMI SINTETICO','Lubricante 89W90. FC FAUCI',5.84,'Lubricantes','FC FAUCI','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000085','VALVULINA 80W90 GULF GEAR MP','Lubricante 89W90. GULF',6.50,'Lubricantes','GULF','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000086','VALVULINA 85W140 GULF GEAR MP','Lubricante 89W90. GULF',6.48,'Lubricantes','GULF','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000087','ACEITE INCA 15W40 SEMI SINTETICO','Lubricante 89W90. INCA',7.44,'Lubricantes','INCA','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000088','SAE 80W90 TRANSMISION RALOY EXTREMA PRESION','Lubricante 89W90. RALOY',5.00,'Lubricantes','RALOY','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000089','ACEITE 25W50 MINERAL MEXLUB ALTO KILOMETRAJE','Lubricante 89W90. MEXLUB',7.59,'Lubricantes','MEXLUB','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000090','VALVULINA 80W90 GL-5 MEXLUB','Lubricante 89W90. MEXLUB',7.96,'Lubricantes','MEXLUB','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000091','VALVULINA 85W140 GL-5 MEXLUB','Lubricante 89W90. MEXLUB',7.96,'Lubricantes','MEXLUB','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000092','ACEITE OILSTONE 20W50 SEMI SINTETICO','Lubricante 89W90. OILSTONE',6.78,'Lubricantes','OILSTONE','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000093','SAE 85W140 VALVULINA RALOY EXTREMA PRESION 946ML','Lubricante 85W140. RALOY',6.00,'Lubricantes','RALOY','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000094','ACEITE ARMAX SAE50 PAILA 20L','Lubricante SAE50 DIESEL. ARMAX',80.00,'Lubricantes','ARMAX','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000095','ACEITE SAE50 BITOIL PAILA 19L','Lubricante SAE50 DIESEL. BITOIL',55.00,'Lubricantes','BITOIL','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000096','ACEITE BOSS SAE50 PAILA 20 LITROS','Lubricante SAE50 DIESEL. BOSS',65.00,'Lubricantes','BOSS','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000097','ACEITE SAE50 FC PAILA 19L','Lubricante SAE50 DIESEL. FC FAUCI',75.00,'Lubricantes','FC FAUCI','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000098','ACEITE DE MOTOR MOBIL DIESEL DELVAC MODERN 15W40','Lubricante 15W40 DIESEL. MOBIL',8.50,'Lubricantes','MOBIL','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000099','ACEITE ARMAX 15W40 MINERAL DIESEL PAILA 20L','Lubricante 15W40 DIESEL. ARMAX',80.00,'Lubricantes','ARMAX','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000100','ACEITE 15W40 DIESEL MEXLUB 5L CL-4','Lubricante 15W40 DIESEL. MEXLUB',33.00,'Lubricantes','MEXLUB','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000101','ISO 68 HIDRALOY 300 ACEITE HIDRAULICO 68 RALOY PAILA 19L','Lubricante HIDRAULICO 68. RALOY',71.00,'Lubricantes','RALOY','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000102','SAE 15W40 SEMI SINTETICO TURBO RALOY API SN PLUS','Lubricante HIDRAULICO 68. RALOY',7.31,'Lubricantes','RALOY','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000103','TRANS-FLUID RDX-III RALOY P/TRANSMISION AUTOMATICA','Lubricante HIDRAULICO 68. RALOY',5.65,'Lubricantes','RALOY','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000104','SAE 20W50 RALOY TURBO SEMI-SINTETICO','Lubricante HIDRAULICO 68. RALOY',7.50,'Lubricantes','RALOY','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000105','SAE 20W50 RALOY RACING OIL MULTIGRADE','Lubricante HIDRAULICO 68. RALOY',6.94,'Lubricantes','RALOY','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000106','ACEITE SHELL HELIX HX8 PROFESIONAL SINTETICO','Lubricante HIDRAULICO 68. SHELL HELIX',11.12,'Lubricantes','SHELL HELIX','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000107','ACEITE ATF DEXRON 3 SHELL SPIRAX S3 MD3 1L','Lubricante HIDRAULICO 68. SHELL HELIX',8.46,'Lubricantes','SHELL HELIX','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000108','ACEITE VITALTECH 5W40 SINTETICO WOLF','Lubricante HIDRAULICO 68. WOLF',11.00,'Lubricantes','WOLF','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-000109','VALVULINA SINTETICA 75W90 GL-5 VITAL TECH WOLF','Lubricante HIDRAULICO 68. WOLF',15.00,'Lubricantes','WOLF','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('LUB-CAS-GTX-10W40-4L','Castrol GTX 10W-40 4L','Aceite multigrado para proteccion contra desgaste y lodos.',32.00,'Lubricantes','Castrol','default_product.png',0,'2026-05-27 14:10:55','2026-05-28 02:32:34'),('LUB-MOB-5W30-4L','Mobil Super 3000 5W-30 4L','Aceite sintetico para motor gasolina de alto rendimiento.',38.00,'Lubricantes','Mobil','default_product.png',0,'2026-05-27 14:10:55','2026-05-28 02:32:34'),('LUB-SHE-HELIX-15W40-4L','Shell Helix HX5 15W-40 4L','Aceite mineral reforzado para motores de alto kilometraje.',29.00,'Lubricantes','Shell','default_product.png',0,'2026-05-27 14:10:55','2026-05-28 02:32:34'),('NEU-000013','165/65R13 HILO GENESYS','Caucho 165/65R13. HILO GENESYS. seccion RIN 13 PCR',35.00,'Cauchos','HILO GENESYS','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000014','165/70R13 FIRESTONE MULTIHAWK','Caucho 165/70R13. FIRESTONE MULTIHAWK. seccion RIN 13 PCR',52.00,'Cauchos','FIRESTONE MULTIHAWK','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000015','165/70R13 POWERTRAC ECOCOMFORT','Caucho 165/70R13. POWERTRAC ECOCOMFORT. seccion RIN 13 PCR',33.00,'Cauchos','POWERTRAC ECOCOMFORT','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000016','165/70R13 ALIX VEZETTA','Caucho 165/70R13. ALIX VEZETTA. seccion RIN 13 PCR',39.00,'Cauchos','ALIX VEZETTA','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000017','165/70R13 ROYAL BLACK','Caucho 165/70R13. ROYAL BLACK. seccion RIN 13 PCR',36.00,'Cauchos','ROYAL BLACK','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000018','175/70R13 ALIX VEZETTA','Caucho 175/70R13. ALIX VEZETTA. seccion RIN 13 PCR',43.00,'Cauchos','ALIX VEZETTA','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000019','175/70R13 FIRESTONE MULTIHAWK','Caucho 175/70R13. FIRESTONE MULTIHAWK. seccion RIN 13 PCR',57.00,'Cauchos','FIRESTONE MULTIHAWK','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000020','175/70R13 ROYAL BLACK','Caucho 175/70R13. ROYAL BLACK. seccion RIN 13 PCR',34.00,'Cauchos','ROYAL BLACK','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000021','175/70R13 POWERTRAC ADAMAS','Caucho 175/70R13. POWERTRAC ADAMAS. seccion RIN 13 PCR',32.00,'Cauchos','POWERTRAC ADAMAS','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000022','175/70R13 POWERTRAC ECOCOMFORT','Caucho 175/70R13. POWERTRAC ECOCOMFORT. seccion RIN 13 PCR',32.00,'Cauchos','POWERTRAC ECOCOMFORT','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000023','175/70R13 HILO GENESYS XP1','Caucho 175/70R13. HILO GENESYS XP1. seccion RIN 13 PCR',36.00,'Cauchos','HILO GENESYS XP1','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000024','175/70R13 DOUBLESTAR','Caucho 175/70R13. DOUBLESTAR. seccion RIN 13 PCR',29.00,'Cauchos','DOUBLESTAR','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000025','175/70R13 RAPID P329','Caucho 175/70R13. RAPID P329. seccion RIN 13 PCR',37.00,'Cauchos','RAPID P329','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000026','175/70R13 HILO GENESYS XP1','Caucho 175/70R13. HILO GENESYS XP1. seccion RIN 13 PCR',36.00,'Cauchos','HILO GENESYS XP1','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000028','175/65R14 EVERLAND','Caucho 175/65R14. EVERLAND. seccion RIN 14 PCR',38.00,'Cauchos','EVERLAND','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000029','175/65R14 POWERTRAC ADAMAS','Caucho 175/65R14. POWERTRAC ADAMAS. seccion RIN 14 PCR',35.00,'Cauchos','POWERTRAC ADAMAS','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000030','175/65R14 ALIX VEZETTA','Caucho 175/65R14. ALIX VEZETTA. seccion RIN 14 PCR',47.00,'Cauchos','ALIX VEZETTA','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000031','175/65R14 DOUBLESTAR','Caucho 175/65R14. DOUBLESTAR. seccion RIN 14 PCR',32.00,'Cauchos','DOUBLESTAR','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000032','185/60R14 POWERTRAC ADAMAS','Caucho 185/60R14. POWERTRAC ADAMAS. seccion RIN 14 PCR',36.00,'Cauchos','POWERTRAC ADAMAS','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000033','185/60R14 DOUBLESTAR','Caucho 185/60R14. DOUBLESTAR. seccion RIN 14 PCR',33.50,'Cauchos','DOUBLESTAR','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000034','185/65R14 DOUBLESTAR','Caucho 185/65R14. DOUBLESTAR. seccion RIN 14 PCR',35.00,'Cauchos','DOUBLESTAR','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000035','185/65R14 ALIX VEZETTA','Caucho 185/65R14. ALIX VEZETTA. seccion RIN 14 PCR',53.00,'Cauchos','ALIX VEZETTA','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000036','185/65R14 WIDEWAY SAFEWAY','Caucho 185/65R14. WIDEWAY SAFEWAY. seccion RIN 14 PCR',39.00,'Cauchos','WIDEWAY SAFEWAY','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000037','185/65R14 FIRESTONE MULTIHAWK','Caucho 185/65R14. FIRESTONE MULTIHAWK. seccion RIN 14 PCR',66.00,'Cauchos','FIRESTONE MULTIHAWK','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000038','185/65R14 POWERTRAC ECOCOMFORT X66','Caucho 185/65R14. POWERTRAC ECOCOMFORT X66. seccion RIN 14 PCR',38.00,'Cauchos','POWERTRAC ECOCOMFORT X66','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000039','185/65R14 ANCHEE','Caucho 185/65R14. ANCHEE. seccion RIN 14 PCR',41.00,'Cauchos','ANCHEE','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000040','185/65R14 ANNAITE','Caucho 185/65R14. ANNAITE. seccion RIN 14 PCR',45.00,'Cauchos','ANNAITE','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000041','185/65R14 RAPID P329','Caucho 185/65R14. RAPID P329. seccion RIN 14 PCR',42.00,'Cauchos','RAPID P329','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000042','195/70R14 HABILEAD COMFORMAX','Caucho 195/70R14. HABILEAD COMFORMAX. seccion RIN 14 PCR',45.00,'Cauchos','HABILEAD COMFORMAX','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000043','205/70R14 HABILEAD','Caucho 205/70R14. HABILEAD. seccion RIN 14 PCR',55.00,'Cauchos','HABILEAD','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000044','195R14C WIDEWAY','Caucho 195R14C. WIDEWAY. seccion RIN 14 PCR',75.00,'Cauchos','WIDEWAY','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000046','195/60R15 WIDEWAY','Caucho 195/60R15. WIDEWAY. seccion RIN 15 PCR',50.00,'Cauchos','WIDEWAY','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000047','195/60R15 ALIX VEZETTA PLUS','Caucho 195/60R15. ALIX VEZETTA PLUS. seccion RIN 15 PCR',68.00,'Cauchos','ALIX VEZETTA PLUS','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000048','195/60R15 RAPID','Caucho 195/60R15. RAPID. seccion RIN 15 PCR',53.00,'Cauchos','RAPID','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000049','195/60R15 POWERTRAC ADAMAS','Caucho 195/60R15. POWERTRAC ADAMAS. seccion RIN 15 PCR',47.00,'Cauchos','POWERTRAC ADAMAS','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000050','195/60R15 POWERTAC ECOCOMFORT','Caucho 195/60R15. POWERTAC ECOCOMFORT. seccion RIN 15 PCR',47.00,'Cauchos','POWERTAC ECOCOMFORT','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000051','195/65R15 WIDEWAY SAFEWAY','Caucho 195/65R15. WIDEWAY SAFEWAY. seccion RIN 15 PCR',52.00,'Cauchos','WIDEWAY SAFEWAY','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000052','195/65R15 POWERTRAC ADAMAS','Caucho 195/65R15. POWERTRAC ADAMAS. seccion RIN 15 PCR',45.00,'Cauchos','POWERTRAC ADAMAS','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000053','195/65R15 RAPID','Caucho 195/65R15. RAPID. seccion RIN 15 PCR',55.00,'Cauchos','RAPID','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000054','195/65R15 DOUBLESTAR','Caucho 195/65R15. DOUBLESTAR. seccion RIN 15 PCR',41.00,'Cauchos','DOUBLESTAR','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000055','205/70R15 MAXTREK SU-830','Caucho 205/70R15. MAXTREK SU-830. seccion RIN 15 PCR',65.00,'Cauchos','MAXTREK SU-830','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000056','205/70R15 FIRESTONE DESTINATION H/T','Caucho 205/70R15. FIRESTONE DESTINATION H/T. seccion RIN 15 PCR',100.00,'Cauchos','FIRESTONE DESTINATION H/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000057','215/65R15 HEADWAY','Caucho 215/65R15. HEADWAY. seccion RIN 15 PCR',40.00,'Cauchos','HEADWAY','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000058','215/70R15 WIDEWAY SAFEWAY','Caucho 215/70R15. WIDEWAY SAFEWAY. seccion RIN 15 PCR',80.00,'Cauchos','WIDEWAY SAFEWAY','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000059','205/70R15C POWERTRAC VANTOUR','Caucho 205/70R15C. POWERTRAC VANTOUR. seccion RIN 15 PCR',68.00,'Cauchos','POWERTRAC VANTOUR','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000060','LT235/75R15 POWERTRAC WILDRANGER M/T','Caucho LT235/75R15. POWERTRAC WILDRANGER M/T. seccion RIN 15 PCR',90.00,'Cauchos','POWERTRAC WILDRANGER M/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000061','LT235/75R15 POWERTRAC WILDRANGER A/T','Caucho LT235/75R15. POWERTRAC WILDRANGER A/T. seccion RIN 15 PCR',100.00,'Cauchos','POWERTRAC WILDRANGER A/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000062','235/75R15 NOVAMAXX AT','Caucho 235/75R15. NOVAMAXX AT. seccion RIN 15 PCR',85.00,'Cauchos','NOVAMAXX AT','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000063','P235/75R15 POWERTRAC WILDRANGER A/T','Caucho P235/75R15. POWERTRAC WILDRANGER A/T. seccion RIN 15 PCR',90.00,'Cauchos','POWERTRAC WILDRANGER A/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000064','235/75R15 RAPID ECOSAVER','Caucho 235/75R15. RAPID ECOSAVER. seccion RIN 15 PCR',90.00,'Cauchos','RAPID ECOSAVER','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000065','235/75R15 WIDEWAY AK3 6PR','Caucho 235/75R15. WIDEWAY AK3 6PR. seccion RIN 15 PCR',130.00,'Cauchos','WIDEWAY AK3 6PR','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000067','235/75R15 HILO HT','Caucho 235/75R15. HILO HT. seccion RIN 15 PCR',100.00,'Cauchos','HILO HT','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000068','235/75R15 NOVAMAXX','Caucho 235/75R15. NOVAMAXX. seccion RIN 15 PCR',85.00,'Cauchos','NOVAMAXX','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000069','P235/75R15 DOUBLEKING DK306','Caucho P235/75R15. DOUBLEKING DK306. seccion RIN 15 PCR',80.00,'Cauchos','DOUBLEKING DK306','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000070','LT235/75R15 DOUBLEKING DK306 10PR','Caucho LT235/75R15. DOUBLEKING DK306 10PR. seccion RIN 15 PCR',90.00,'Cauchos','DOUBLEKING DK306 10PR','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000071','295/50R15 RAPID SHARK Z02','Caucho 295/50R15. RAPID SHARK Z02. seccion RIN 15 PCR',127.00,'Cauchos','RAPID SHARK Z02','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000072','31X10.50R15 ANCHEE MT','Caucho 31X10.50R15. ANCHEE MT. seccion RIN 15 PCR',165.00,'Cauchos','ANCHEE MT','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000073','31X10.50R15 HILO X-TERRAIN MT1','Caucho 31X10.50R15. HILO X-TERRAIN MT1. seccion RIN 15 PCR',165.00,'Cauchos','HILO X-TERRAIN MT1','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000074','31X10.50R15 WIDEWAY A/T','Caucho 31X10.50R15. WIDEWAY A/T. seccion RIN 15 PCR',165.00,'Cauchos','WIDEWAY A/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000075','31X10.50R15 V-RICH A/T','Caucho 31X10.50R15. V-RICH A/T. seccion RIN 15 PCR',170.00,'Cauchos','V-RICH A/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000076','31X10.50R15 LT ROCKBLADE 787RT','Caucho 31X10.50R15 LT. ROCKBLADE 787RT. seccion RIN 15 PCR',135.00,'Cauchos','ROCKBLADE 787RT','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000077','31X10.50R15 LT HABILEAD AT','Caucho 31X10.50R15 LT. HABILEAD AT. seccion RIN 15 PCR',125.00,'Cauchos','HABILEAD AT','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000078','31X10.50R15 POWERTRAC WILDRANGER A/T','Caucho 31X10.50R15. POWERTRAC WILDRANGER A/T. seccion RIN 15 PCR',130.00,'Cauchos','POWERTRAC WILDRANGER A/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000079','31X10.50R15 POWERTRAC WILDRANGER M/T','Caucho 31X10.50R15. POWERTRAC WILDRANGER M/T. seccion RIN 15 PCR',137.00,'Cauchos','POWERTRAC WILDRANGER M/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000081','31X10.50R15 AOQISHI MARVEL M/T','Caucho 31X10.50R15. AOQISHI MARVEL M/T. seccion RIN 15 PCR',140.00,'Cauchos','AOQISHI MARVEL M/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000082','31X10.50R15 DURINGON CROSSMAXX','Caucho 31X10.50R15. DURINGON CROSSMAXX. seccion RIN 15 PCR',140.00,'Cauchos','DURINGON CROSSMAXX','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000083','31X10.50R15 CROSSLEADER WILDTIGER MT','Caucho 31X10.50R15. CROSSLEADER WILDTIGER MT. seccion RIN 15 PCR',115.00,'Cauchos','CROSSLEADER WILDTIGER MT','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000084','31X10.50R15 RAPID TUFTRAIL A/T','Caucho 31X10.50R15. RAPID TUFTRAIL A/T. seccion RIN 15 PCR',135.00,'Cauchos','RAPID TUFTRAIL A/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000085','31X10.50R15 RAPID MUD CONTENDER M/T','Caucho 31X10.50R15. RAPID MUD CONTENDER M/T. seccion RIN 15 PCR',145.00,'Cauchos','RAPID MUD CONTENDER M/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000086','LT32X11.5R15 HILO X-TERRAIN MT1','Caucho LT32X11.5R15. HILO X-TERRAIN MT1. seccion RIN 15 PCR',200.00,'Cauchos','HILO X-TERRAIN MT1','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000087','33X12.5R15LT HILO X-TERRAIN MT1','Caucho 33X12.5R15LT. HILO X-TERRAIN MT1. seccion RIN 15 PCR',210.00,'Cauchos','HILO X-TERRAIN MT1','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000088','LT7.00R15 7.00R15 KOBATA','Caucho LT7.00R15. 7.00R15 KOBATA. seccion RIN 15 PCR',95.00,'Cauchos','7.00R15 KOBATA','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000089','LT35X12.5R15 HILO X-TERRAIN MT1','Caucho LT35X12.5R15. HILO X-TERRAIN MT1. seccion RIN 15 PCR',225.00,'Cauchos','HILO X-TERRAIN MT1','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000091','195/55R16 POWERTRAC ADAMAS','Caucho 195/55R16. POWERTRAC ADAMAS. seccion RIN 16 PCR',45.00,'Cauchos','POWERTRAC ADAMAS','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000092','195/55R16 WIDEWAY','Caucho 195/55R16. WIDEWAY. seccion RIN 16 PCR',58.00,'Cauchos','WIDEWAY','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000093','205/55R16 ANCHEE','Caucho 205/55R16. ANCHEE. seccion RIN 16 PCR',53.00,'Cauchos','ANCHEE','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000094','205/55R16 ALIX VELOCE','Caucho 205/55R16. ALIX VELOCE. seccion RIN 16 PCR',70.00,'Cauchos','ALIX VELOCE','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000095','205/55R16 POWERTRAC ECOCOMFORT X66','Caucho 205/55R16. POWERTRAC ECOCOMFORT X66. seccion RIN 16 PCR',54.00,'Cauchos','POWERTRAC ECOCOMFORT X66','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000096','205/55R16 DOUBLESTAR DH05','Caucho 205/55R16. DOUBLESTAR DH05. seccion RIN 16 PCR',41.00,'Cauchos','DOUBLESTAR DH05','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000097','215/60R16 POWERTRAC','Caucho 215/60R16. POWERTRAC. seccion RIN 16 PCR',56.00,'Cauchos','POWERTRAC','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000098','235/60R16 ALIX IMPACT HT','Caucho 235/60R16. ALIX IMPACT HT. seccion RIN 16 PCR',93.00,'Cauchos','ALIX IMPACT HT','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000099','235/60R16 POWERTRAC ADAMAS','Caucho 235/60R16. POWERTRAC ADAMAS. seccion RIN 16 PCR',75.00,'Cauchos','POWERTRAC ADAMAS','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000100','235/70R16 NOVAMAXX AT','Caucho 235/70R16. NOVAMAXX AT. seccion RIN 16 PCR',100.00,'Cauchos','NOVAMAXX AT','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000101','245/70R16 DOUBLESTAR DS01','Caucho 245/70R16. DOUBLESTAR DS01. seccion RIN 16 PCR',87.00,'Cauchos','DOUBLESTAR DS01','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000102','245/70R16 POWERTRAC WILDRANGER A/T','Caucho 245/70R16. POWERTRAC WILDRANGER A/T. seccion RIN 16 PCR',100.00,'Cauchos','POWERTRAC WILDRANGER A/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000103','LT245/75R16 POWERTRAC WILDRANGER A/T','Caucho LT245/75R16. POWERTRAC WILDRANGER A/T. seccion RIN 16 PCR',110.00,'Cauchos','POWERTRAC WILDRANGER A/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000104','P255/70R16 ALIX IMPACT HT PLUS','Caucho P255/70R16. ALIX IMPACT HT PLUS. seccion RIN 16 PCR',135.00,'Cauchos','ALIX IMPACT HT PLUS','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000105','255/70R16 TDI TIRES R/T','Caucho 255/70R16. TDI TIRES R/T. seccion RIN 16 PCR',110.00,'Cauchos','TDI TIRES R/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000106','LT265/70R16 V-RICH AT','Caucho LT265/70R16. V-RICH AT. seccion RIN 16 PCR',175.00,'Cauchos','V-RICH AT','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000107','LT265/75R16 POWERTRAC WILDRANGER A/T','Caucho LT265/75R16. POWERTRAC WILDRANGER A/T. seccion RIN 16 PCR',145.00,'Cauchos','POWERTRAC WILDRANGER A/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000108','P265/75R16 NOVAMAX WARRIOR TERRA T/A','Caucho P265/75R16. NOVAMAX WARRIOR TERRA T/A. seccion RIN 16 PCR',140.00,'Cauchos','NOVAMAX WARRIOR TERRA T/A','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000109','LT265/75R16 ROYAL BLACK A/T','Caucho LT265/75R16. ROYAL BLACK A/T. seccion RIN 16 PCR',150.00,'Cauchos','ROYAL BLACK A/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000110','265/75R16 V-RICH AT 10PR','Caucho 265/75R16. V-RICH AT 10PR. seccion RIN 16 PCR',195.00,'Cauchos','V-RICH AT 10PR','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000112','P265/75R16 TDI TIRES R/T','Caucho P265/75R16. TDI TIRES R/T. seccion RIN 16 PCR',127.00,'Cauchos','TDI TIRES R/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000114','LT265/75R16 ALIX IMPACT AT PLUS','Caucho LT265/75R16. ALIX IMPACT AT PLUS. seccion RIN 16 PCR',175.00,'Cauchos','ALIX IMPACT AT PLUS','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000115','LT265/75R16 V-RICH ALL TERRAIN','Caucho LT265/75R16. V-RICH ALL TERRAIN. seccion RIN 16 PCR',185.00,'Cauchos','V-RICH ALL TERRAIN','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000116','LT265/75R16 HILO X-TERRAIN MT1','Caucho LT265/75R16. HILO X-TERRAIN MT1. seccion RIN 16 PCR',200.00,'Cauchos','HILO X-TERRAIN MT1','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000117','LT265/75R16 RAPID TUFTRAIL A/T','Caucho LT265/75R16. RAPID TUFTRAIL A/T. seccion RIN 16 PCR',165.00,'Cauchos','RAPID TUFTRAIL A/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000118','LT265/75R16 NOVAMAX STAR A/T','Caucho LT265/75R16. NOVAMAX STAR A/T. seccion RIN 16 PCR',127.00,'Cauchos','NOVAMAX STAR A/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000119','LT285/75R16 POWERTRAC WILDRANGER A/T','Caucho LT285/75R16. POWERTRAC WILDRANGER A/T. seccion RIN 16 PCR',160.00,'Cauchos','POWERTRAC WILDRANGER A/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000120','285/75R16 V-RICH A/T','Caucho 285/75R16. V-RICH A/T. seccion RIN 16 PCR',195.00,'Cauchos','V-RICH A/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000121','285/75R16 HILO X-TERRAIN MT1','Caucho 285/75R16. HILO X-TERRAIN MT1. seccion RIN 16 PCR',210.00,'Cauchos','HILO X-TERRAIN MT1','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000123','285/75R16 RAPID ECOLANDER A/T','Caucho 285/75R16. RAPID ECOLANDER A/T. seccion RIN 16 PCR',175.00,'Cauchos','RAPID ECOLANDER A/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000124','LT285/75R16 AOQISHI A/T','Caucho LT285/75R16. AOQISHI A/T. seccion RIN 16 PCR',160.00,'Cauchos','AOQISHI A/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000126','LT285/75R16 WIDEWAY XT ALL-TERRAIN','Caucho LT285/75R16. WIDEWAY XT ALL-TERRAIN. seccion RIN 16 PCR',200.00,'Cauchos','WIDEWAY XT ALL-TERRAIN','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000127','305/70R16 HILO X-TERRAIN MT1','Caucho 305/70R16. HILO X-TERRAIN MT1. seccion RIN 16 PCR',220.00,'Cauchos','HILO X-TERRAIN MT1','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000128','315/75R16 POWERTRAC WILDRANGER M/T','Caucho 315/75R16. POWERTRAC WILDRANGER M/T. seccion RIN 16 PCR',215.00,'Cauchos','POWERTRAC WILDRANGER M/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000129','315/75R16 HILO X-TERRAIN MT1','Caucho 315/75R16. HILO X-TERRAIN MT1. seccion RIN 16 PCR',240.00,'Cauchos','HILO X-TERRAIN MT1','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000131','7.50R16 HILO DIRECCIONAL 14PR','Caucho 7.50R16. HILO DIRECCIONAL 14PR. seccion RIN 16 TBR',120.00,'Cauchos','HILO DIRECCIONAL 14PR','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000132','7.50R16 ANNAITE DIRECCIONAL 14PR','Caucho 7.50R16. ANNAITE DIRECCIONAL 14PR. seccion RIN 16 TBR',120.00,'Cauchos','ANNAITE DIRECCIONAL 14PR','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000133','7.50-16 POWERTRAC TRAC PRO (SET)','Caucho 7.50-16. POWERTRAC TRAC PRO (SET). seccion RIN 16 TBR',126.00,'Cauchos','POWERTRAC TRAC PRO (SET)','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000134','7.50R16 HONOUR 14PR DIRECCIONAL','Caucho 7.50R16. HONOUR 14PR DIRECCIONAL. seccion RIN 16 TBR',105.00,'Cauchos','HONOUR 14PR DIRECCIONAL','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000135','7.50R16 HAIDA 16PR DIRECCIONAL','Caucho 7.50R16. HAIDA 16PR DIRECCIONAL. seccion RIN 16 TBR',135.00,'Cauchos','HAIDA 16PR DIRECCIONAL','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000136','7.50R16 ROCKBLADE 14PR DIRECCIONAL','Caucho 7.50R16. ROCKBLADE 14PR DIRECCIONAL. seccion RIN 16 TBR',100.00,'Cauchos','ROCKBLADE 14PR DIRECCIONAL','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000137','7.50R16 ROADSHINE 16PR DIRECCIONAL','Caucho 7.50R16. ROADSHINE 16PR DIRECCIONAL. seccion RIN 16 TBR',135.00,'Cauchos','ROADSHINE 16PR DIRECCIONAL','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000139','215/60R17 POWERTRAC CITYROVER','Caucho 215/60R17. POWERTRAC CITYROVER. seccion RIN 17 PCR',70.00,'Cauchos','POWERTRAC CITYROVER','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000140','225/50ZR17 HILO - VANTAGE XU1','Caucho 225/50ZR17. HILO - VANTAGE XU1. seccion RIN 17 PCR',90.00,'Cauchos','HILO - VANTAGE XU1','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000141','205/45R17 RAPID P609','Caucho 205/45R17. RAPID P609. seccion RIN 17 PCR',80.00,'Cauchos','RAPID P609','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000145','215/45R17 RAPID P609','Caucho 215/45R17. RAPID P609. seccion RIN 17 PCR',80.00,'Cauchos','RAPID P609','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000146','215/45R17 DOUBLESTAR','Caucho 215/45R17. DOUBLESTAR. seccion RIN 17 PCR',60.00,'Cauchos','DOUBLESTAR','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000147','215/60R17 FIRESTONE FIREHAWK','Caucho 215/60R17. FIRESTONE FIREHAWK. seccion RIN 17 PCR',109.00,'Cauchos','FIRESTONE FIREHAWK','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000150','245/65R17 DOUBLEKING','Caucho 245/65R17. DOUBLEKING. seccion RIN 17 PCR',115.00,'Cauchos','DOUBLEKING','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000151','265/70R17 RAPID ECOLANDER','Caucho 265/70R17. RAPID ECOLANDER. seccion RIN 17 PCR',145.00,'Cauchos','RAPID ECOLANDER','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000152','LT265/70R17 V-RICH ALL TERRAIN','Caucho LT265/70R17. V-RICH ALL TERRAIN. seccion RIN 17 PCR',180.00,'Cauchos','V-RICH ALL TERRAIN','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000153','LT265/70R17 AOQISHI A/T','Caucho LT265/70R17. AOQISHI A/T. seccion RIN 17 PCR',150.00,'Cauchos','AOQISHI A/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000154','275/70R17 AOQISHI A/T','Caucho 275/70R17. AOQISHI A/T. seccion RIN 17 PCR',160.00,'Cauchos','AOQISHI A/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000155','LT275/70R17 V-RICH ALL TERRAIN','Caucho LT275/70R17. V-RICH ALL TERRAIN. seccion RIN 17 PCR',190.00,'Cauchos','V-RICH ALL TERRAIN','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000157','LT285/70R17 POWERTRAC WILDRANGER AT','Caucho LT285/70R17. POWERTRAC WILDRANGER AT. seccion RIN 17 PCR',170.00,'Cauchos','POWERTRAC WILDRANGER AT','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000158','LT285/70R17 POWERTRAC WILDRANGER MT','Caucho LT285/70R17. POWERTRAC WILDRANGER MT. seccion RIN 17 PCR',175.00,'Cauchos','POWERTRAC WILDRANGER MT','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000159','LT285/70R17 HILO X-TERRAIN MT1','Caucho LT285/70R17. HILO X-TERRAIN MT1. seccion RIN 17 PCR',210.00,'Cauchos','HILO X-TERRAIN MT1','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000160','LT285/70R17 WIDEWAY XT ALL-TERRAIN','Caucho LT285/70R17. WIDEWAY XT ALL-TERRAIN. seccion RIN 17 PCR',185.00,'Cauchos','WIDEWAY XT ALL-TERRAIN','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000161','LT285/70R17 V-RICH ALL TERRAIN','Caucho LT285/70R17. V-RICH ALL TERRAIN. seccion RIN 17 PCR',195.00,'Cauchos','V-RICH ALL TERRAIN','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000162','LT315/70R17 V-RICH ALL TERRAIN','Caucho LT315/70R17. V-RICH ALL TERRAIN. seccion RIN 17 PCR',220.00,'Cauchos','V-RICH ALL TERRAIN','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000165','215/75R17.5 POWERTRAC','Caucho 215/75R17.5. POWERTRAC. seccion RIN 17.5 TBR',140.00,'Cauchos','POWERTRAC','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000166','235/75R17.5 POWERTRAC','Caucho 235/75R17.5. POWERTRAC. seccion RIN 17.5 TBR',165.00,'Cauchos','POWERTRAC','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000167','235/75R17.5 CHENSHANG','Caucho 235/75R17.5. CHENSHANG. seccion RIN 17.5 TBR',160.00,'Cauchos','CHENSHANG','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000169','225/40ZR18 POWERTRAC ECO SPORT X77','Caucho 225/40ZR18. POWERTRAC ECO SPORT X77. seccion RIN 18 PCR',80.00,'Cauchos','POWERTRAC ECO SPORT X77','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000170','235/50ZR18 POWERTRAC ECO SPORT X77','Caucho 235/50ZR18. POWERTRAC ECO SPORT X77. seccion RIN 18 PCR',85.00,'Cauchos','POWERTRAC ECO SPORT X77','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000171','245/60R18 POWERTRAC CITYROVER','Caucho 245/60R18. POWERTRAC CITYROVER. seccion RIN 18 PCR',105.00,'Cauchos','POWERTRAC CITYROVER','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000172','35X12.50R18 WIDEWAY','Caucho 35X12.50R18. WIDEWAY. seccion RIN 18 PCR',235.00,'Cauchos','WIDEWAY','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000174','265/60R18 HABILEAD A/T','Caucho 265/60R18. HABILEAD A/T. seccion RIN 18 PCR',105.00,'Cauchos','HABILEAD A/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000175','265/60R18 ROCKBLADE H/T','Caucho 265/60R18. ROCKBLADE H/T. seccion RIN 18 PCR',110.00,'Cauchos','ROCKBLADE H/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000176','37x13.5R18 MILEKING MT','Caucho 37x13.5R18. MILEKING MT. seccion RIN 18 PCR',295.00,'Cauchos','MILEKING MT','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000178','275/55R20 WIDEWAY WEYONE AK3','Caucho 275/55R20. WIDEWAY WEYONE AK3. seccion RIN 20 PCR',205.00,'Cauchos','WIDEWAY WEYONE AK3','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000179','275/55R20 V-RICH ALL TERRAIN','Caucho 275/55R20. V-RICH ALL TERRAIN. seccion RIN 20 PCR',205.00,'Cauchos','V-RICH ALL TERRAIN','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000181','35X12.5R20 POWERTRAC WILDRANGER M/T','Caucho 35X12.5R20. POWERTRAC WILDRANGER M/T. seccion RIN 20 PCR',250.00,'Cauchos','POWERTRAC WILDRANGER M/T','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000182','8.25R20 DOUBLESTAR 16 PR','Caucho 8.25R20. DOUBLESTAR 16 PR. seccion RIN 20 PCR',150.00,'Cauchos','DOUBLESTAR 16 PR','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000184','295/80R22.5 TAITONG 18 PR MIXTO HS268','Caucho 295/80R22.5. TAITONG 18 PR MIXTO HS268. seccion RIN 22.5 TBR',220.00,'Cauchos','TAITONG 18 PR MIXTO HS268','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000185','295/80R22.5 ECOSAVER DIRECCIONAL 18PR','Caucho 295/80R22.5. ECOSAVER DIRECCIONAL 18PR. seccion RIN 22.5 TBR',200.00,'Cauchos','ECOSAVER DIRECCIONAL 18PR','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000186','295/80R22.5 POWERTRAC DIRECCIONAL','Caucho 295/80R22.5. POWERTRAC DIRECCIONAL. seccion RIN 22.5 TBR',210.00,'Cauchos','POWERTRAC DIRECCIONAL','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000187','295/80R22.5 POWERTRAC MIXTO','Caucho 295/80R22.5. POWERTRAC MIXTO. seccion RIN 22.5 TBR',220.00,'Cauchos','POWERTRAC MIXTO','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000188','295/80R22.5 POWERTRAC TRACCION','Caucho 295/80R22.5. POWERTRAC TRACCION. seccion RIN 22.5 TBR',238.00,'Cauchos','POWERTRAC TRACCION','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000190','315/80R22.5 SUPERMEALLIR DIRECCIONAL','Caucho 315/80R22.5. SUPERMEALLIR DIRECCIONAL. seccion RIN 22.5 TBR',200.00,'Cauchos','SUPERMEALLIR DIRECCIONAL','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000191','12RR2.5 POWERTRAC MIXTO','Caucho 12RR2.5. POWERTRAC MIXTO. seccion RIN 22.5 TBR',230.00,'Cauchos','POWERTRAC MIXTO','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000192','315/80R22.5 SUPERMEALLIR DIRECCIONAL','Caucho 315/80R22.5. SUPERMEALLIR DIRECCIONAL. seccion RIN 22.5 TBR',200.00,'Cauchos','SUPERMEALLIR DIRECCIONAL','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000193','315/80R22.5 AMBERSTONE MIXTO','Caucho 315/80R22.5. AMBERSTONE MIXTO. seccion RIN 22.5 TBR',215.00,'Cauchos','AMBERSTONE MIXTO','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('NEU-000194','315/80R22.5 POWERTRAC DIRECCIONAL','Caucho 315/80R22.5. POWERTRAC DIRECCIONAL. seccion RIN 22.5 TBR',235.00,'Cauchos','POWERTRAC DIRECCIONAL','default_product.png',1,'2026-05-28 02:32:34','2026-05-28 02:32:34'),('PC0507224338','Producto afahcceddi','Desc',21.00,'Cat afahcceddi','Marca afahcceddi','default_product.png',0,'2026-05-08 02:43:38','2026-05-22 06:32:48'),('REP-NGK-BKR6E','NGK bujia BKR6E','Bujia de encendido para motores gasolina compatibles.',6.50,'Repuestos','NGK','default_product.png',0,'2026-05-27 14:10:55','2026-05-28 02:32:34');
/*!40000 ALTER TABLE `productos` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_productos_insert` AFTER INSERT ON productos FOR EACH ROW BEGIN
        INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (COALESCE(@current_usuario_id, 1), 'CREAR', 'PRODUCTOS', CONCAT('Producto creado: ', NEW.nombre_producto), COALESCE(@current_ip, '127.0.0.1'));
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_productos_update` AFTER UPDATE ON productos FOR EACH ROW BEGIN
        IF OLD.estado = 1 AND NEW.estado = 0 THEN
            INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
            VALUES (COALESCE(@current_usuario_id, 1), 'MODIFICAR', 'PRODUCTOS', CONCAT('Estado producto cambiado: ', NEW.codigo), COALESCE(@current_ip, '127.0.0.1'));
        ELSE
            INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
            VALUES (COALESCE(@current_usuario_id, 1), 'MODIFICAR', 'PRODUCTOS', CONCAT('Producto modificado: ', OLD.codigo), COALESCE(@current_ip, '127.0.0.1'));
        END IF;
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;


DROP TABLE IF EXISTS `promociones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `promociones` (
  `id_promocion` int(11) NOT NULL AUTO_INCREMENT,
  `nombre_promocion` varchar(200) NOT NULL,
  `descripcion_promocion` text DEFAULT NULL,
  `tipo_promocion` varchar(30) NOT NULL DEFAULT 'puntos',
  `puntos_requeridos` int(11) DEFAULT 3,
  `recompensa_promocion` varchar(200) DEFAULT NULL,
  `imagen_tarjeta` varchar(200) DEFAULT 'default_card.png',
  `estado` tinyint(1) DEFAULT 1,
  `fecha_inicio_promocion` date DEFAULT NULL,
  `fecha_fin_promocion` date DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_promocion`),
  KEY `tipo` (`tipo_promocion`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `promociones` WRITE;
/*!40000 ALTER TABLE `promociones` DISABLE KEYS */;
INSERT INTO `promociones` VALUES (1,'Promo afahcceddi','Promo test','puntos',3,'Descuento','promo_1_hero.png',1,NULL,NULL,'2026-05-08 02:43:38'),(2,'ded','dede','puntos',5,'','promo_2_cocacola_1l.jpg',1,NULL,NULL,'2026-05-21 02:47:42'),(3,'dede','dede','descuento',5,'dede','promo_3_hero.png',1,'2026-06-01','2026-06-02','2026-06-02 21:35:32'),(4,'fsfsfsf','fsfsfsf','descuento',5,'quesillo','promo_4_cocacola_1l.jpg',1,'2026-06-02','2026-06-30','2026-06-08 07:08:48'),(5,'grwegewgr','gergege','puntos',5,'quesillo','promo_5_CocaCola_de_botella.jpg',1,'2026-06-01','2026-06-30','2026-06-08 08:17:06');
/*!40000 ALTER TABLE `promociones` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_promociones_insert` AFTER INSERT ON promociones FOR EACH ROW BEGIN
        INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (COALESCE(@current_usuario_id, 1), 'CREAR', 'PROMOCIONES', CONCAT('Promocion creada: ', NEW.nombre_promocion), COALESCE(@current_ip, '127.0.0.1'));
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_promociones_update` AFTER UPDATE ON promociones FOR EACH ROW BEGIN
        IF OLD.estado = 1 AND NEW.estado = 0 THEN
            INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
            VALUES (COALESCE(@current_usuario_id, 1), 'MODIFICAR', 'PROMOCIONES', CONCAT('Estado promocion cambiado ID: ', NEW.id_promocion), COALESCE(@current_ip, '127.0.0.1'));
        ELSE
            INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
            VALUES (COALESCE(@current_usuario_id, 1), 'MODIFICAR', 'PROMOCIONES', CONCAT('Promocion modificada ID: ', NEW.id_promocion), COALESCE(@current_ip, '127.0.0.1'));
        END IF;
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;


DROP TABLE IF EXISTS `proveedores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `proveedores` (
  `rif_proveedor` varchar(20) NOT NULL,
  `rif_prefijo` varchar(2) DEFAULT NULL,
  `nombre_proveedor` varchar(200) NOT NULL,
  `telefono_proveedor` varchar(20) DEFAULT NULL,
  `email_proveedor` varchar(150) DEFAULT NULL,
  `direccion_proveedor` varchar(300) DEFAULT NULL,
  `estado` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`rif_proveedor`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `proveedores` WRITE;
/*!40000 ALTER TABLE `proveedores` DISABLE KEYS */;
INSERT INTO `proveedores` VALUES ('J-33333333-3','J','Proveedor afahcceddi','04122397209','business@tanqueteodigital.com','dddd',1,'2026-06-03 06:04:46'),('J-50722410-0','J','Proveedor 0507224100','04121234567','prov0507224100@mail.com','Dir prueba',1,'2026-05-08 02:41:00'),('J-50722434-9','J','Proveedor afahcceddi','04121234567','p0507224338@mail.com','Dir',0,'2026-05-08 02:43:38');
/*!40000 ALTER TABLE `proveedores` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_proveedores_insert` AFTER INSERT ON proveedores FOR EACH ROW BEGIN
        INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (COALESCE(@current_usuario_id, 1), 'CREAR', 'PROVEEDORES', CONCAT('Proveedor creado: ', NEW.rif_proveedor), COALESCE(@current_ip, '127.0.0.1'));
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_proveedores_update` AFTER UPDATE ON proveedores FOR EACH ROW BEGIN
        IF OLD.estado = 1 AND NEW.estado = 0 THEN
            INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
            VALUES (COALESCE(@current_usuario_id, 1), 'ELIMINAR', 'PROVEEDORES', CONCAT('Proveedor desactivado: ', NEW.rif_proveedor), COALESCE(@current_ip, '127.0.0.1'));
        ELSE
            INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
            VALUES (COALESCE(@current_usuario_id, 1), 'MODIFICAR', 'PROVEEDORES', CONCAT('Proveedor modificado: ', NEW.rif_proveedor), COALESCE(@current_ip, '127.0.0.1'));
        END IF;
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;


DROP TABLE IF EXISTS `qr_codes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `qr_codes` (
  `id_qr_code` int(11) NOT NULL AUTO_INCREMENT,
  `usuario_cedula` varchar(20) NOT NULL,
  `tipo_qr_code` tinyint(4) NOT NULL DEFAULT 0,
  `contenido` varchar(4300) DEFAULT NULL,
  `utilidad` varchar(150) DEFAULT NULL,
  `referencia_qr_code` int(11) DEFAULT NULL,
  `promocion_id` int(11) DEFAULT NULL,
  `servicio_id` int(11) DEFAULT NULL,
  `orden_venta_id` int(11) DEFAULT NULL,
  `estado` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_qr_code`),
  KEY `idx_qr_referencia` (`tipo_qr_code`,`referencia_qr_code`),
  KEY `fk_qr_promocion` (`promocion_id`),
  KEY `fk_qr_servicio` (`servicio_id`),
  KEY `fk_qr_orden` (`orden_venta_id`),
  KEY `fk_qr_usuario` (`usuario_cedula`),
  CONSTRAINT `fk_qr_orden` FOREIGN KEY (`orden_venta_id`) REFERENCES `ordenes_venta` (`id_orden_venta`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_qr_promocion` FOREIGN KEY (`promocion_id`) REFERENCES `promociones` (`id_promocion`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_qr_servicio` FOREIGN KEY (`servicio_id`) REFERENCES `servicios` (`id_servicio`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `qr_codes` WRITE;
/*!40000 ALTER TABLE `qr_codes` DISABLE KEYS */;
INSERT INTO `qr_codes` VALUES (1,'V-00000000',1,'{\"kind\": \"factura\", \"orden_id\": 1, \"estado\": \"cumplida\", \"fulfilled_at\": \"2026-06-03T02:24:20\"}','factura',1,NULL,NULL,1,0,'2026-05-18 04:33:01'),(2,'V-00000000',1,'{\"kind\": \"factura\", \"orden_id\": 2}','factura',2,NULL,NULL,2,0,'2026-05-21 06:08:02'),(3,'V-00000000',2,'{\"kind\": \"promocion\", \"utilidad\": \"promocion\", \"referencia_id\": 1, \"estado\": \"activa\", \"assigned_at\": \"2026-06-03T01:54:22\", \"expires_at\": \"2026-06-03T02:04:22\", \"fulfilled_at\": null, \"nota\": \"\"}','promocion',1,1,NULL,NULL,0,'2026-06-03 05:54:22'),(4,'V-00000000',0,'{\"kind\": \"validar_pago\", \"utilidad\": \"validar_pago\", \"referencia_id\": null, \"estado\": \"activa\", \"assigned_at\": \"2026-06-03T10:51:02\", \"expires_at\": \"2026-06-03T11:01:02\", \"fulfilled_at\": null, \"nota\": \"\"}','validar_pago',NULL,NULL,NULL,NULL,0,'2026-06-03 14:51:02'),(5,'V-00000000',0,'{\"kind\": \"validar_pago\", \"utilidad\": \"validar_pago\", \"referencia_id\": null, \"estado\": \"activa\", \"assigned_at\": \"2026-06-03T10:51:33\", \"expires_at\": \"2026-06-03T11:01:33\", \"fulfilled_at\": null, \"nota\": \"ferfef\"}','validar_pago',NULL,NULL,NULL,NULL,1,'2026-06-03 14:51:33'),(6,'V-00000000',1,'{\"kind\": \"factura\", \"orden_id\": 1, \"estado\": \"cumplida\", \"fulfilled_at\": \"2026-06-03T10:55:42\"}','factura',1,NULL,NULL,1,1,'2026-06-03 14:54:44'),(7,'V-00000000',1,'{\"kind\": \"factura\", \"orden_id\": 9}','factura',9,NULL,NULL,9,1,'2026-06-03 15:39:55'),(8,'V-00000000',0,'{\"kind\": \"promocion\", \"utilidad\": \"promocion\", \"referencia_id\": 1, \"estado\": \"cumplida\", \"assigned_at\": \"2026-06-03T13:01:50\", \"expires_at\": \"2026-06-03T13:11:50\", \"fulfilled_at\": \"2026-06-03T13:01:57\", \"nota\": \"dede\", \"expired_at\": \"2026-06-03T12:58:43\"}','promocion',1,1,NULL,NULL,1,'2026-06-03 16:38:09'),(9,'V-00000000',1,'{\"kind\": \"factura\", \"orden_id\": 11}','factura',11,NULL,NULL,11,1,'2026-06-08 21:17:57'),(10,'V-00000000',1,'{\"kind\": \"factura\", \"orden_id\": 12}','factura',12,NULL,NULL,12,1,'2026-06-10 21:09:31'),(11,'30396029',1,'{\"kind\": \"factura\", \"orden_id\": 13}','factura',13,NULL,NULL,13,1,'2026-06-11 06:14:42');
/*!40000 ALTER TABLE `qr_codes` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_qr_codes_insert` AFTER INSERT ON qr_codes FOR EACH ROW BEGIN
        INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (COALESCE(@current_usuario_id, 1), 'CREAR', 'QR', CONCAT('Codigo QR creado: ', NEW.utilidad), COALESCE(@current_ip, '127.0.0.1'));
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_qr_codes_update` AFTER UPDATE ON qr_codes FOR EACH ROW BEGIN
        IF OLD.estado = 1 AND NEW.estado = 0 THEN
            INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
            VALUES (COALESCE(@current_usuario_id, 1), 'ELIMINAR', 'QR', CONCAT('Codigo QR eliminado: ', NEW.utilidad), COALESCE(@current_ip, '127.0.0.1'));
        ELSE
            INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
            VALUES (COALESCE(@current_usuario_id, 1), 'MODIFICAR', 'QR', CONCAT('Codigo QR modificado: ', NEW.utilidad), COALESCE(@current_ip, '127.0.0.1'));
        END IF;
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;


DROP TABLE IF EXISTS `servicio_mecanico`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `servicio_mecanico` (
  `id_servicio_mecanico` int(11) NOT NULL AUTO_INCREMENT,
  `servicio_id` int(11) NOT NULL,
  `mecanico_cedula` varchar(20) DEFAULT NULL,
  `orden_venta_id` int(11) DEFAULT NULL,
  `fecha_servicio` timestamp NOT NULL DEFAULT current_timestamp(),
  `estado_servicio` varchar(30) NOT NULL DEFAULT 'sin_asignar',
  `observaciones_servicio` varchar(1000) DEFAULT NULL,
  `cliente_cedula` varchar(20) DEFAULT NULL,
  `vehiculo_placa` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id_servicio_mecanico`),
  KEY `servicio_id` (`servicio_id`),
  KEY `mecanico_cedula` (`mecanico_cedula`),
  KEY `orden_venta_id` (`orden_venta_id`),
  KEY `estado` (`estado_servicio`),
  KEY `cliente_cedula` (`cliente_cedula`),
  KEY `vehiculo_placa` (`vehiculo_placa`),
  CONSTRAINT `fk_servicio_mecanico_cliente` FOREIGN KEY (`cliente_cedula`) REFERENCES `cliente` (`identificador_cliente`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_servicio_mecanico_vehiculo` FOREIGN KEY (`vehiculo_placa`) REFERENCES `vehiculos` (`placa_vehiculo`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `servicio_mecanico_ibfk_1` FOREIGN KEY (`servicio_id`) REFERENCES `servicios` (`id_servicio`) ON UPDATE CASCADE,
  CONSTRAINT `servicio_mecanico_ibfk_2` FOREIGN KEY (`mecanico_cedula`) REFERENCES `mecanicos` (`cedula_mecanico`) ON UPDATE CASCADE,
  CONSTRAINT `servicio_mecanico_ibfk_3` FOREIGN KEY (`orden_venta_id`) REFERENCES `ordenes_venta` (`id_orden_venta`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `servicio_mecanico` WRITE;
/*!40000 ALTER TABLE `servicio_mecanico` DISABLE KEYS */;
INSERT INTO `servicio_mecanico` VALUES (1,8,'V-07224236',NULL,'2026-05-08 02:42:30','completado','Asignacion valida',NULL,NULL),(2,9,'V-07224351',NULL,'2026-05-08 02:43:38','en_proceso','Asignado',NULL,NULL),(3,4,'V-07224236',1,'2026-05-18 04:35:49','asignado','fwfw',NULL,NULL),(4,1,NULL,2,'2026-05-21 06:08:02','completado','Pendiente de asignacion de mecanico',NULL,NULL),(5,18,'V-07224157',8,'2026-06-02 22:13:00','completado','frfrfr','dede','AB123CD'),(6,22,NULL,12,'2026-06-10 21:09:00','completado','Pendiente de asignacion de mecanico','V-00000000','DADADA'),(7,22,'V-07224157',13,'2026-06-11 06:15:22','completado','','30396029','AB123CD');
/*!40000 ALTER TABLE `servicio_mecanico` ENABLE KEYS */;
UNLOCK TABLES;


DROP TABLE IF EXISTS `servicio_sucursal`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `servicio_sucursal` (
  `servicio_id` int(11) NOT NULL,
  `sucursal_id` int(11) NOT NULL,
  `estado` tinyint(1) NOT NULL DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`servicio_id`,`sucursal_id`),
  KEY `sucursal_id` (`sucursal_id`),
  CONSTRAINT `servicio_sucursal_ibfk_1` FOREIGN KEY (`servicio_id`) REFERENCES `servicios` (`id_servicio`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `servicio_sucursal_ibfk_2` FOREIGN KEY (`sucursal_id`) REFERENCES `sucursales` (`id_sucursal`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `servicio_sucursal` WRITE;
/*!40000 ALTER TABLE `servicio_sucursal` DISABLE KEYS */;
INSERT INTO `servicio_sucursal` VALUES (1,1,1,'2026-05-28 22:46:02'),(2,1,1,'2026-05-28 22:46:02'),(3,1,1,'2026-05-28 22:46:02'),(4,1,1,'2026-05-28 22:46:02'),(5,2,1,'2026-05-28 22:46:02'),(6,2,1,'2026-05-28 22:46:02'),(11,1,1,'2026-05-28 22:46:02'),(12,1,1,'2026-05-28 22:46:02'),(13,2,1,'2026-05-28 22:46:02'),(14,1,1,'2026-05-28 22:46:02'),(15,2,1,'2026-05-28 22:46:02'),(16,1,1,'2026-05-28 22:46:02'),(17,1,1,'2026-06-03 06:00:52'),(18,1,1,'2026-05-28 22:46:02'),(19,1,1,'2026-05-28 22:46:02'),(20,1,1,'2026-05-28 22:46:02'),(21,1,1,'2026-05-28 22:46:02'),(22,1,1,'2026-05-28 22:46:02'),(23,1,1,'2026-05-28 22:46:02'),(24,1,1,'2026-05-28 22:46:02'),(25,1,1,'2026-05-28 22:46:02'),(26,1,1,'2026-05-28 22:46:02'),(27,1,1,'2026-05-28 22:46:02'),(28,1,1,'2026-05-28 22:46:02'),(29,1,1,'2026-05-28 22:46:02'),(30,1,1,'2026-05-28 22:46:02'),(31,1,1,'2026-05-28 22:46:02'),(32,1,1,'2026-05-28 22:46:02'),(33,1,1,'2026-05-28 22:46:02'),(34,1,1,'2026-05-28 22:46:02'),(35,1,1,'2026-05-28 22:46:02'),(36,1,1,'2026-05-28 22:46:02'),(37,1,1,'2026-05-28 22:46:02'),(38,1,1,'2026-05-28 22:46:02'),(39,1,1,'2026-05-28 22:46:02'),(40,1,1,'2026-05-28 22:46:02'),(41,1,1,'2026-05-28 22:46:02'),(42,1,1,'2026-05-28 22:46:02'),(43,1,1,'2026-05-28 22:46:02'),(44,1,1,'2026-05-28 22:46:02'),(45,1,1,'2026-05-28 22:46:02'),(46,1,1,'2026-05-28 22:46:02'),(47,1,1,'2026-05-28 22:46:02'),(48,1,1,'2026-05-28 22:46:02'),(49,1,1,'2026-05-28 22:46:02'),(50,1,1,'2026-05-28 22:46:02'),(51,1,1,'2026-05-28 22:46:02'),(52,1,1,'2026-05-28 22:46:02'),(53,1,1,'2026-05-28 22:46:02'),(54,1,1,'2026-05-28 22:46:02'),(55,1,1,'2026-05-28 22:46:02'),(56,1,1,'2026-05-28 22:46:02'),(57,1,1,'2026-05-28 22:46:02'),(58,1,1,'2026-05-28 22:46:02'),(59,1,1,'2026-05-28 22:46:02'),(60,1,1,'2026-05-28 22:46:02'),(61,1,1,'2026-05-28 22:46:02');
/*!40000 ALTER TABLE `servicio_sucursal` ENABLE KEYS */;
UNLOCK TABLES;


DROP TABLE IF EXISTS `servicios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `servicios` (
  `id_servicio` int(11) NOT NULL AUTO_INCREMENT,
  `nombre_servicio` varchar(200) NOT NULL,
  `descripcion_servicio` text DEFAULT NULL,
  `precio_servicio` decimal(10,2) NOT NULL DEFAULT 0.00,
  `duracion_estimada` varchar(50) DEFAULT NULL,
  `estado` tinyint(1) DEFAULT 1,
  `permite_filtros` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `tipo_servicio` varchar(50) NOT NULL DEFAULT 'general',
  PRIMARY KEY (`id_servicio`)
) ENGINE=InnoDB AUTO_INCREMENT=63 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `servicios` WRITE;
/*!40000 ALTER TABLE `servicios` DISABLE KEYS */;
INSERT INTO `servicios` VALUES (1,'Alineacion','Alineacion computarizada de ruedas',15.00,'30 min',0,1,'2026-04-30 04:18:56','general'),(2,'Balanceo','Balanceo dinamico de ruedas',10.00,'20 min',0,1,'2026-04-30 04:18:56','general'),(3,'Rotacion de cauchos','Rotacion de 4 cauchos',8.00,'25 min',0,1,'2026-04-30 04:18:56','general'),(4,'Cambio de aceite','CAMBIO DE ACEITE',50.00,'60',1,1,'2026-04-30 04:18:56','general'),(5,'Cambio de frenos','Cambio de pastillas de freno',25.00,'45 min',0,1,'2026-04-30 04:18:56','general'),(6,'Revision general','Revision completa del vehiculo',20.00,'60 min',0,1,'2026-04-30 04:18:56','general'),(7,'Servicio 0507224100','Servicio de prueba',15.50,'45',0,1,'2026-05-08 02:41:00','general'),(8,'Servicio afahcceccj','Servicio prueba',30.00,'30',0,1,'2026-05-08 02:42:29','general'),(9,'Servicio afahcceddi','Desc',15.00,'40',0,1,'2026-05-08 02:43:38','general'),(11,'Montaje de cauchos','Montaje profesional de cauchos con revision de valvulas.',18.00,'35',0,1,'2026-05-27 14:10:55','general'),(12,'Diagnostico con scanner automotriz','Lectura de codigos de falla y diagnostico electronico basico.',22.00,'40',0,1,'2026-05-27 14:10:55','general'),(13,'Limpieza de inyectores','Servicio de limpieza preventiva de inyectores.',30.00,'60',0,1,'2026-05-27 14:10:55','general'),(14,'Reemplazo de bateria','Instalacion y verificacion de bateria automotriz.',8.00,'20',0,1,'2026-05-27 14:10:55','general'),(15,'Revision de sistema de frenos','Revision de pastillas, discos, liga y ruidos del sistema de frenos.',18.00,'40',0,1,'2026-05-27 14:10:55','general'),(16,'ALINEACION AUTOMOVIL','ALINEACION AUTOMOVIL',10.50,'60',0,1,'2026-05-28 02:32:34','general'),(17,'ALINEACION AUTO GRA.','ddd',333.00,'60',0,1,'2026-05-28 02:32:34','general'),(18,'ALINEACION CAMIONETA PEQ.','ALINEACION CAMIONETA PEQ.',15.00,'60',1,1,'2026-05-28 02:32:34','general'),(19,'ALINEACION CAMIONETA GRANDE','ALINEACION CAMIONETA GRANDE',17.00,'60',1,1,'2026-05-28 02:32:34','general'),(20,'ALINEACION CAMIONETA GRAND.PLUS','ALINEACION CAMIONETA GRAND.PLUS',20.00,'60',1,1,'2026-05-28 02:32:34','general'),(21,'ALINEACION CAMION (16 17.5 )','ALINEACION CAMION (16 17.5 )',20.00,'60',0,1,'2026-05-28 02:32:34','general'),(22,'ALINEACION CAMION (22.5 )','ALINEACION CAMION (22.5 )',20.00,'60',1,1,'2026-05-28 02:32:34','general'),(23,'MONTURA AUTOMOVIL (POR RUEDA)','MONTURA AUTOMOVIL (POR RUEDA)',3.00,'60',1,1,'2026-05-28 02:32:34','general'),(24,'MONTURA CAMIONETA (POR RUEDA)','MONTURA CAMIONETA (POR RUEDA)',2.00,'60',1,1,'2026-05-28 02:32:34','general'),(25,'MONTURA CAMION (16 17.5 ) (POR RUEDA )','MONTURA CAMION (16 17.5 ) (POR RUEDA )',3.50,'60',1,1,'2026-05-28 02:32:34','general'),(26,'MONTURA CAMION (22.5 20 ) (POR RUEDA)','MONTURA CAMION (22.5 20 ) (POR RUEDA)',5.00,'60',1,1,'2026-05-28 02:32:34','general'),(27,'BALANCEO AUTOMOVIL (POR RUEDA)','BALANCEO AUTOMOVIL (POR RUEDA)',2.00,'60',1,1,'2026-05-28 02:32:34','general'),(28,'BALANCEO AUTOMOVIL ADHESIVO (POR RUEDA)','BALANCEO AUTOMOVIL ADHESIVO (POR RUEDA)',5.00,'60',1,1,'2026-05-28 02:32:34','general'),(29,'BALANCEO CAMIONETA (POR RUEDA)','BALANCEO CAMIONETA (POR RUEDA)',2.00,'60',1,1,'2026-05-28 02:32:34','general'),(30,'BALANCEO CAMIONETA ADHESIVO (POR RUEDA)','BALANCEO CAMIONETA ADHESIVO (POR RUEDA)',6.00,'60',1,1,'2026-05-28 02:32:34','general'),(31,'BALANCEO CAMION (16\" 17.5\") (POR RUEDA)','BALANCEO CAMION (16\" 17.5\") (POR RUEDA)',8.00,'60',1,1,'2026-05-28 02:32:34','general'),(32,'BALANCEO DINAMICO AUTO/CAMIONETA (POR RUEDA)','BALANCEO DINAMICO AUTO/CAMIONETA (POR RUEDA)',8.00,'60',1,1,'2026-05-28 02:32:34','general'),(33,'BALANCEO DINAMICO CAMION (16 17.5 ) (POR RUEDA)','BALANCEO DINAMICO CAMION (16 17.5 ) (POR RUEDA)',15.00,'60',1,1,'2026-05-28 02:32:34','general'),(34,'BALANCEO DINAMICO CAMION (20 22.5 ) (POR RUEDA)','BALANCEO DINAMICO CAMION (20 22.5 ) (POR RUEDA)',10.00,'60',1,1,'2026-05-28 02:32:34','general'),(35,'ROTACION AUTOMOVIL','ROTACION AUTOMOVIL',2.00,'60',1,1,'2026-05-28 02:32:34','general'),(36,'ROTACION CAMIONETA','ROTACION CAMIONETA',3.00,'60',1,1,'2026-05-28 02:32:34','general'),(37,'ROTACION CAMION (MOROCHA)','ROTACION CAMION (MOROCHA)',4.50,'60',1,1,'2026-05-28 02:32:34','general'),(38,'REVISION AUTOMOVIL PEQUENO','REVISION AUTOMOVIL PEQUENO',2.00,'60',1,1,'2026-05-28 02:32:34','general'),(39,'REVISION AUTOMOVIL GRANDE','REVISION AUTOMOVIL GRANDE',3.00,'60',1,1,'2026-05-28 02:32:34','general'),(40,'REVISION CAMIONETA','REVISION CAMIONETA',3.50,'60',1,1,'2026-05-28 02:32:34','general'),(41,'REVISION CAMION','REVISION CAMION',4.00,'60',1,1,'2026-05-28 02:32:34','general'),(42,'REPARACION SENCILLA','REPARACION SENCILLA',6.00,'60',1,1,'2026-05-28 02:32:34','general'),(43,'VALVULA TR413 N','VALVULA TR413 N',1.50,'60',1,1,'2026-05-28 02:32:34','general'),(44,'VALVULA TR413 HIERRO','VALVULA TR413 HIERRO',5.00,'60',1,1,'2026-05-28 02:32:34','general'),(45,'VALVULA TR413 HIERRO CURVA','VALVULA TR413 HIERRO CURVA',5.00,'60',1,1,'2026-05-28 02:32:34','general'),(46,'VALVULA TR415 N','VALVULA TR415 N',3.00,'60',1,1,'2026-05-28 02:32:34','general'),(47,'VALVULA TR415 HIERRO','VALVULA TR415 HIERRO',5.00,'60',1,1,'2026-05-28 02:32:34','general'),(48,'VALVULA 17.5 BRONCE','VALVULA 17.5 BRONCE',8.00,'60',1,1,'2026-05-28 02:32:34','general'),(49,'VALVULA 22.5 BRONCE','VALVULA 22.5 BRONCE',10.00,'60',1,1,'2026-05-28 02:32:34','general'),(50,'COMPACTO BASICO','BAL GANCHO, CALIBRACION AIRE, ROTACION',10.00,'60',1,1,'2026-05-28 02:32:34','general'),(51,'COMPACTO FULL','BAL PEGA, CALIBRACION AIRE, ROTACION, VALVULAS 5 RUEDAS, MANT. PESTANAS',15.00,'60',1,1,'2026-05-28 02:32:34','general'),(52,'CARRO GRANDE-CAMIONETA PEQ BASICO','BAL GANCHO, CALIBRACION AIRE, ROTACION',12.00,'60',1,1,'2026-05-28 02:32:34','general'),(53,'CARRO GRANDE-CAMIONETA PEQ FULL','BAL PEGA, CALIBRACION AIRE, ROTACION, VALVULAS 5 RUEDAS, MANT. PESTANAS',20.00,'60',1,1,'2026-05-28 02:32:34','general'),(54,'CAMIONETA GRANDE BASICO','BAL GANCHO, CALIBRACION AIRE, ROTACION',16.00,'60',1,1,'2026-05-28 02:32:34','general'),(55,'CAMIONETA GRANDE FULL','BAL PEGA, CALIBRACION AIRE, ROTACION, VALVULAS 5 RUEDAS, MANT. PESTANAS',35.00,'60',1,1,'2026-05-28 02:32:34','general'),(56,'BALANCEO CAMIONETA PEQ. (POR RUEDA)','BALANCEO CAMIONETA PEQ. (POR RUEDA)',4.00,'60',1,1,'2026-05-28 02:32:34','general'),(57,'BALANCEO CAMIONETA PEQ. ADHESIVO (POR RUEDA)','BALANCEO CAMIONETA PEQ. ADHESIVO (POR RUEDA)',6.00,'60',1,1,'2026-05-28 02:32:34','general'),(58,'BALANCEO CAMIONETA GRANDE (POR RUEDA)','BALANCEO CAMIONETA GRANDE (POR RUEDA)',8.00,'60',1,1,'2026-05-28 02:32:34','general'),(59,'BALANCEO CAMIONETA GR. ADHESIVO (POR RUEDA)','BALANCEO CAMIONETA GR. ADHESIVO (POR RUEDA)',10.00,'60',1,1,'2026-05-28 02:32:34','general'),(60,'VALVULA TR413 NEGRA','VALVULA TR413 NEGRA',1.00,'60',1,1,'2026-05-28 02:32:34','general'),(61,'VALVULA TR415 NEGRA','VALVULA TR415 NEGRA',3.00,'60',1,1,'2026-05-28 02:32:34','general');
/*!40000 ALTER TABLE `servicios` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_servicios_insert` AFTER INSERT ON servicios FOR EACH ROW BEGIN
        INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (COALESCE(@current_usuario_id, 1), 'CREAR', 'SERVICIOS', CONCAT('Servicio creado: ', NEW.nombre_servicio), COALESCE(@current_ip, '127.0.0.1'));
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_servicios_update` AFTER UPDATE ON servicios FOR EACH ROW BEGIN
        IF OLD.estado = 1 AND NEW.estado = 0 THEN
            INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
            VALUES (COALESCE(@current_usuario_id, 1), 'ELIMINAR', 'SERVICIOS', CONCAT('Servicio desactivado: ', NEW.id_servicio), COALESCE(@current_ip, '127.0.0.1'));
        ELSE
            INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
            VALUES (COALESCE(@current_usuario_id, 1), 'MODIFICAR', 'SERVICIOS', CONCAT('Servicio modificado: ', OLD.id_servicio), COALESCE(@current_ip, '127.0.0.1'));
        END IF;
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;


DROP TABLE IF EXISTS `solicitudes_validacion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `solicitudes_validacion` (
  `id_validacion` int(11) NOT NULL AUTO_INCREMENT,
  `tipo` varchar(50) NOT NULL,
  `comprobante_pago_id` int(11) NOT NULL,
  `estado_validacion` varchar(20) NOT NULL DEFAULT 'pendiente',
  `alerta_vista` tinyint(1) NOT NULL DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_validacion`),
  KEY `fk_sv_comprobante` (`comprobante_pago_id`),
  CONSTRAINT `fk_sv_comprobante` FOREIGN KEY (`comprobante_pago_id`) REFERENCES `comprobantes_pago` (`id_comprobante_pago`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `solicitudes_validacion` WRITE;
/*!40000 ALTER TABLE `solicitudes_validacion` DISABLE KEYS */;
INSERT INTO `solicitudes_validacion` VALUES (1,'factura',1,'aprobada',0,'2026-06-03 14:53:01'),(2,'factura',1,'pendiente',0,'2026-06-03 14:53:57');
/*!40000 ALTER TABLE `solicitudes_validacion` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_bitacora_solicitudes_validacion_update AFTER UPDATE ON solicitudes_validacion FOR EACH ROW BEGIN INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip) VALUES (COALESCE(@current_usuario_id, 1), 'MODIFICAR', 'ESCANER', CONCAT('Solicitud validacion ID ', NEW.id_validacion, ' respondida como ', NEW.estado_validacion), COALESCE(@current_ip, '127.0.0.1')); END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;


DROP TABLE IF EXISTS `stock`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `stock` (
  `producto_codigo` varchar(50) NOT NULL,
  `sucursal_id` int(11) NOT NULL,
  `stock` int(11) DEFAULT 0,
  `stock_minimo` int(11) DEFAULT 5,
  `ubicacion_stock` varchar(100) DEFAULT NULL,
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`producto_codigo`,`sucursal_id`),
  KEY `sucursal_id` (`sucursal_id`),
  CONSTRAINT `stock_ibfk_1` FOREIGN KEY (`producto_codigo`) REFERENCES `productos` (`codigo`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `stock_ibfk_2` FOREIGN KEY (`sucursal_id`) REFERENCES `sucursales` (`id_sucursal`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `stock` WRITE;
/*!40000 ALTER TABLE `stock` DISABLE KEYS */;
INSERT INTO `stock` VALUES ('BAT-000016',1,11,2,'650 - 700','2026-06-11 07:00:35'),('BAT-000017',1,1,2,'650 - 700','2026-05-28 02:32:34'),('BAT-000018',1,1,2,'650 - 700','2026-05-28 02:32:34'),('BAT-000019',1,1,2,'650 - 700','2026-05-28 02:32:34'),('BAT-000020',1,1,2,'650 - 700','2026-05-28 02:32:34'),('BAT-000023',1,1,2,'800','2026-05-28 02:32:34'),('BAT-000024',1,5,2,'800','2026-05-28 02:32:34'),('BAT-000025',1,6,2,'800','2026-05-28 02:32:34'),('BAT-000033',1,0,2,'900','2026-05-28 02:32:34'),('BAT-000034',1,1,2,'900','2026-05-28 02:32:34'),('BAT-000035',1,1,2,'900','2026-05-28 02:32:34'),('BAT-000036',1,0,2,'900','2026-05-28 02:32:34'),('BAT-000039',1,2,2,'1000 - 1350','2026-05-28 02:32:34'),('BAT-000040',1,0,2,'1000 - 1350','2026-05-28 02:32:34'),('BAT-000041',1,0,2,'1000 - 1350','2026-05-28 02:32:34'),('BAT-000042',1,10,2,'1000 - 1350','2026-06-02 23:43:11'),('BAT-000043',1,1,2,'1000 - 1350','2026-05-28 02:32:34'),('BAT-000044',1,1,2,'1000 - 1350','2026-05-28 02:32:34'),('BAT-000045',1,1,2,'1000 - 1350','2026-05-28 02:32:34'),('BAT-000046',1,1,2,'1000 - 1350','2026-05-28 02:32:34'),('BAT-000047',1,1,2,'1000 - 1350','2026-05-28 02:32:34'),('BAT-000048',1,2,2,'1000 - 1350','2026-05-28 02:32:34'),('CMB-000004',1,0,2,'GULF','2026-05-28 02:32:34'),('CMB-000005',1,0,2,'GULF','2026-05-28 02:32:34'),('CMB-000006',1,0,2,'GULF','2026-05-28 02:32:34'),('CMB-000007',1,0,2,'GULF','2026-05-28 02:32:34'),('CMB-000008',1,0,2,'GULF','2026-05-28 02:32:34'),('CMB-000009',1,0,2,'GULF','2026-05-28 02:32:34'),('CMB-000010',1,0,2,'GULF','2026-05-28 02:32:34'),('CMB-000011',1,0,2,'GULF','2026-05-28 02:32:34'),('CMB-000016',1,0,2,'RALOY / INCA / BOSS','2026-05-28 02:32:34'),('CMB-000017',1,0,2,'RALOY / INCA / BOSS','2026-05-28 02:32:34'),('CMB-000018',1,0,2,'RALOY / INCA / BOSS','2026-05-28 02:32:34'),('CMB-000019',1,0,2,'RALOY / INCA / BOSS','2026-05-28 02:32:34'),('CMB-000020',1,0,2,'RALOY / INCA / BOSS','2026-05-28 02:32:34'),('CMB-000021',1,0,2,'RALOY / INCA / BOSS','2026-05-28 02:32:34'),('CMB-000022',1,0,2,'RALOY / INCA / BOSS','2026-05-28 02:32:34'),('CMB-000023',1,0,2,'RALOY / INCA / BOSS','2026-05-28 02:32:34'),('CMB-000024',1,0,2,'RALOY / INCA / BOSS','2026-05-28 02:32:34'),('CMB-000025',1,0,2,'RALOY / INCA / BOSS','2026-05-28 02:32:34'),('CMB-000030',1,0,2,'VALVOLINE / FC','2026-05-28 02:32:34'),('CMB-000031',1,0,2,'VALVOLINE / FC','2026-05-28 02:32:34'),('CMB-000032',1,0,2,'VALVOLINE / FC','2026-05-28 02:32:34'),('CMB-000033',1,0,2,'VALVOLINE / FC','2026-05-28 02:32:34'),('CMB-000034',1,0,2,'VALVOLINE / FC','2026-05-28 02:32:34'),('CMB-000035',1,0,2,'VALVOLINE / FC','2026-05-28 02:32:34'),('CMB-000036',1,0,2,'VALVOLINE / FC','2026-05-28 02:32:34'),('CMB-000037',1,0,2,'VALVOLINE / FC','2026-05-28 02:32:34'),('CMB-000038',1,0,2,'VALVOLINE / FC','2026-05-28 02:32:34'),('CMB-000039',1,0,2,'VALVOLINE / FC','2026-05-28 02:32:34'),('CMB-000040',1,0,2,'VALVOLINE / FC','2026-05-28 02:32:34'),('CMB-000041',1,0,2,'VALVOLINE / FC','2026-05-28 02:32:34'),('CMB-000046',1,0,2,'WOLF / MEXLUB / ROSHFRANS','2026-05-28 02:32:34'),('CMB-000047',1,0,2,'WOLF / MEXLUB / ROSHFRANS','2026-05-28 02:32:34'),('CMB-000048',1,0,2,'WOLF / MEXLUB / ROSHFRANS','2026-05-28 02:32:34'),('CMB-000049',1,0,2,'WOLF / MEXLUB / ROSHFRANS','2026-05-28 02:32:34'),('CMB-000050',1,0,2,'WOLF / MEXLUB / ROSHFRANS','2026-05-28 02:32:34'),('CMB-000051',1,0,2,'WOLF / MEXLUB / ROSHFRANS','2026-05-28 02:32:34'),('CMB-000052',1,0,2,'WOLF / MEXLUB / ROSHFRANS','2026-05-28 02:32:34'),('CMB-000053',1,0,2,'WOLF / MEXLUB / ROSHFRANS','2026-05-28 02:32:34'),('LUB-000005',1,25,2,'15W40 MINERAL','2026-05-28 02:32:34'),('LUB-000006',1,0,2,'15W40 MINERAL','2026-05-28 02:32:34'),('LUB-000007',1,3,2,'15W40 MINERAL','2026-05-28 02:32:34'),('LUB-000008',1,0,2,'15W40 MINERAL','2026-05-28 02:32:34'),('LUB-000009',1,17,2,'15W40 MINERAL','2026-05-28 02:32:34'),('LUB-000010',1,12,2,'15W40 MINERAL','2026-05-28 02:32:34'),('LUB-000011',1,4,2,'15W40 MINERAL','2026-05-28 02:32:34'),('LUB-000012',1,39,2,'15W40 MINERAL','2026-05-28 02:32:34'),('LUB-000013',1,0,2,'20W50 MINERAL','2026-05-28 02:32:34'),('LUB-000014',1,0,2,'20W50 MINERAL','2026-05-28 02:32:34'),('LUB-000015',1,0,2,'20W50 MINERAL','2026-05-28 02:32:34'),('LUB-000016',1,11,2,'20W50 MINERAL','2026-05-28 02:32:34'),('LUB-000017',1,0,2,'20W50 MINERAL','2026-05-28 02:32:34'),('LUB-000018',1,0,2,'20W50 MINERAL','2026-05-28 02:32:34'),('LUB-000019',1,2,2,'20W50 MINERAL','2026-05-28 02:32:34'),('LUB-000020',1,11,2,'20W50 MINERAL','2026-05-28 02:32:34'),('LUB-000021',1,14,2,'20W50 MINERAL','2026-05-28 02:32:34'),('LUB-000022',1,11,2,'20W50 MINERAL','2026-05-28 02:32:34'),('LUB-000023',1,12,2,'20W50 MINERAL','2026-05-28 02:32:34'),('LUB-000024',1,3,2,'20W50 MINERAL','2026-05-28 02:32:34'),('LUB-000025',1,3,2,'20W50 MINERAL','2026-05-28 02:32:34'),('LUB-000026',1,2,2,'20W50 MINERAL','2026-05-28 02:32:34'),('LUB-000027',1,0,2,'20W50 MINERAL','2026-05-28 02:32:34'),('LUB-000028',1,7,2,'25W60 MINERAL','2026-05-28 02:32:34'),('LUB-000029',1,4,2,'10W30 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000030',1,0,2,'10W30 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000031',1,12,2,'10W30 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000032',1,16,2,'10W30 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000033',1,26,2,'10W40 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000034',1,0,2,'15W40 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000035',1,0,2,'15W40 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000036',1,0,2,'15W40 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000037',1,12,2,'15W40 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000038',1,1,2,'15W40 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000039',1,37,2,'15W40 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000040',1,9,2,'15W40 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000041',1,11,2,'15W40 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000042',1,7,2,'15W40 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000043',1,4,2,'15W40 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000044',1,0,2,'15W40 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000045',1,202,2,'15W40 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000046',1,0,2,'15W40 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000047',1,0,2,'15W40 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000048',1,0,2,'15W40 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000049',1,37,2,'20W50 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000050',1,21,2,'20W50 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000051',1,14,2,'20W50 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000052',1,0,2,'20W50 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000053',1,0,2,'20W50 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000054',1,1,2,'20W50 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000055',1,23,2,'20W50 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000056',1,0,2,'20W50 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000057',1,10,2,'20W50 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000058',1,20,2,'20W50 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000059',1,2,2,'20W50 SEMI SINTETICO','2026-05-28 02:32:34'),('LUB-000060',1,12,2,'0W20 SINTETICO','2026-05-28 02:32:34'),('LUB-000061',1,4,2,'5W20 SINTETICO','2026-05-28 02:32:34'),('LUB-000062',1,18,2,'5W20 SINTETICO','2026-05-28 02:32:34'),('LUB-000063',1,1,2,'5W20 SINTETICO','2026-05-28 02:32:34'),('LUB-000064',1,9,2,'5W30 SINTETICO','2026-05-28 02:32:34'),('LUB-000065',1,2,2,'5W30 SINTETICO','2026-05-28 02:32:34'),('LUB-000066',1,6,2,'5W30 SINTETICO','2026-05-28 02:32:34'),('LUB-000067',1,8,2,'5W30 SINTETICO','2026-05-28 02:32:34'),('LUB-000068',1,1,2,'5W30 SINTETICO','2026-05-28 02:32:34'),('LUB-000069',1,9,2,'5W40 SINTETICO','2026-05-28 02:32:34'),('LUB-000070',1,5,2,'20W50 4T MINERAL','2026-05-28 02:32:34'),('LUB-000071',1,23,2,'20W50 4T MINERAL','2026-05-28 02:32:34'),('LUB-000072',1,1,2,'20W50 4T MINERAL','2026-05-28 02:32:34'),('LUB-000073',1,2,2,'10W40 4T SINTETICO','2026-05-28 02:32:34'),('LUB-000074',1,0,2,'10W50 4T SINTETICO','2026-05-28 02:32:34'),('LUB-000075',1,4,2,'10W30 DIESEL','2026-05-28 02:32:34'),('LUB-000076',1,4,2,'DEXRON III','2026-05-28 02:32:34'),('LUB-000077',1,0,2,'DEXRON III','2026-05-28 02:32:34'),('LUB-000078',1,3,2,'DEXRON III','2026-05-28 02:32:34'),('LUB-000079',1,6,2,'DEXRON III','2026-05-28 02:32:34'),('LUB-000080',1,0,2,'DEXRON III','2026-05-28 02:32:34'),('LUB-000081',1,1,2,'DEXRON III','2026-05-28 02:32:34'),('LUB-000082',1,0,2,'89W90','2026-05-28 02:32:34'),('LUB-000083',1,0,2,'89W90','2026-05-28 02:32:34'),('LUB-000084',1,0,2,'89W90','2026-05-28 02:32:34'),('LUB-000085',1,10,2,'89W90','2026-05-28 02:32:34'),('LUB-000086',1,0,2,'89W90','2026-05-28 02:32:34'),('LUB-000087',1,0,2,'89W90','2026-05-28 02:32:34'),('LUB-000088',1,3,2,'89W90','2026-05-28 02:32:34'),('LUB-000089',1,0,2,'89W90','2026-05-28 02:32:34'),('LUB-000090',1,0,2,'89W90','2026-05-28 02:32:34'),('LUB-000091',1,0,2,'89W90','2026-05-28 02:32:34'),('LUB-000092',1,0,2,'89W90','2026-05-28 02:32:34'),('LUB-000093',1,0,2,'85W140','2026-05-28 02:32:34'),('LUB-000094',1,0,2,'SAE50 DIESEL','2026-05-28 02:32:34'),('LUB-000095',1,0,2,'SAE50 DIESEL','2026-05-28 02:32:34'),('LUB-000096',1,0,2,'SAE50 DIESEL','2026-05-28 02:32:34'),('LUB-000097',1,0,2,'SAE50 DIESEL','2026-05-28 02:32:34'),('LUB-000098',1,12,2,'15W40 DIESEL','2026-05-28 02:32:34'),('LUB-000099',1,0,2,'15W40 DIESEL','2026-05-28 02:32:34'),('LUB-000100',1,0,2,'15W40 DIESEL','2026-05-28 02:32:34'),('LUB-000101',1,2,2,'HIDRAULICO 68','2026-05-28 02:32:34'),('LUB-000102',1,0,2,'HIDRAULICO 68','2026-05-28 02:32:34'),('LUB-000103',1,0,2,'HIDRAULICO 68','2026-05-28 02:32:34'),('LUB-000104',1,0,2,'HIDRAULICO 68','2026-05-28 02:32:34'),('LUB-000105',1,0,2,'HIDRAULICO 68','2026-05-28 02:32:34'),('LUB-000106',1,0,2,'HIDRAULICO 68','2026-05-28 02:32:34'),('LUB-000107',1,0,2,'HIDRAULICO 68','2026-05-28 02:32:34'),('LUB-000108',1,0,2,'HIDRAULICO 68','2026-05-28 02:32:34'),('LUB-000109',1,0,2,'HIDRAULICO 68','2026-05-28 02:32:34'),('NEU-000013',1,7,2,'RIN 13 PCR','2026-05-28 02:32:34'),('NEU-000014',1,5,2,'RIN 13 PCR','2026-05-28 02:32:34'),('NEU-000015',1,17,2,'RIN 13 PCR','2026-05-28 02:32:34'),('NEU-000016',1,8,2,'RIN 13 PCR','2026-05-28 02:32:34'),('NEU-000017',1,0,2,'RIN 13 PCR','2026-05-28 02:32:34'),('NEU-000018',1,13,2,'RIN 13 PCR','2026-05-28 02:32:34'),('NEU-000019',1,8,2,'RIN 13 PCR','2026-05-28 02:32:34'),('NEU-000020',1,7,2,'RIN 13 PCR','2026-05-28 02:32:34'),('NEU-000021',1,0,2,'RIN 13 PCR','2026-05-28 02:32:34'),('NEU-000022',1,19,2,'RIN 13 PCR','2026-05-28 02:32:34'),('NEU-000023',1,0,2,'RIN 13 PCR','2026-05-28 02:32:34'),('NEU-000024',1,0,2,'RIN 13 PCR','2026-05-28 02:32:34'),('NEU-000025',1,2,2,'RIN 13 PCR','2026-05-28 02:32:34'),('NEU-000026',1,0,2,'RIN 13 PCR','2026-05-28 02:32:34'),('NEU-000028',1,0,2,'RIN 14 PCR','2026-05-28 02:32:34'),('NEU-000029',1,0,2,'RIN 14 PCR','2026-05-28 02:32:34'),('NEU-000030',1,0,2,'RIN 14 PCR','2026-05-28 02:32:34'),('NEU-000031',1,137,2,'RIN 14 PCR','2026-05-28 02:32:34'),('NEU-000032',1,21,2,'RIN 14 PCR','2026-05-28 02:32:34'),('NEU-000033',1,172,2,'RIN 14 PCR','2026-05-28 02:32:34'),('NEU-000034',1,5,2,'RIN 14 PCR','2026-05-28 02:32:34'),('NEU-000035',1,20,2,'RIN 14 PCR','2026-05-28 02:32:34'),('NEU-000036',1,0,2,'RIN 14 PCR','2026-05-28 02:32:34'),('NEU-000037',1,8,2,'RIN 14 PCR','2026-05-28 02:32:34'),('NEU-000038',1,16,2,'RIN 14 PCR','2026-05-28 02:32:34'),('NEU-000039',1,0,2,'RIN 14 PCR','2026-05-28 02:32:34'),('NEU-000040',1,0,2,'RIN 14 PCR','2026-05-28 02:32:34'),('NEU-000041',1,0,2,'RIN 14 PCR','2026-05-28 02:32:34'),('NEU-000042',1,20,2,'RIN 14 PCR','2026-05-28 02:32:34'),('NEU-000043',1,18,2,'RIN 14 PCR','2026-05-28 02:32:34'),('NEU-000044',1,3,2,'RIN 14 PCR','2026-05-28 02:32:34'),('NEU-000046',1,0,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000047',1,13,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000048',1,19,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000049',1,10,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000050',1,7,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000051',1,4,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000052',1,19,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000053',1,4,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000054',1,32,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000055',1,2,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000056',1,2,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000057',1,30,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000058',1,6,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000059',1,0,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000060',1,0,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000061',1,2,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000062',1,14,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000063',1,2,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000064',1,10,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000065',1,2,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000067',1,4,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000068',1,0,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000069',1,40,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000070',1,40,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000071',1,4,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000072',1,0,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000073',1,0,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000074',1,0,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000075',1,4,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000076',1,2,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000077',1,12,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000078',1,0,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000079',1,2,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000081',1,2,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000082',1,4,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000083',1,18,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000084',1,8,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000085',1,4,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000086',1,4,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000087',1,0,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000088',1,2,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000089',1,0,2,'RIN 15 PCR','2026-05-28 02:32:34'),('NEU-000091',1,0,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000092',1,8,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000093',1,0,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000094',1,8,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000095',1,17,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000096',1,165,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000097',1,1,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000098',1,6,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000099',1,4,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000100',1,4,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000101',1,50,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000102',1,0,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000103',1,4,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000104',1,0,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000105',1,12,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000106',1,0,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000107',1,4,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000108',1,0,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000109',1,0,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000110',1,0,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000112',1,8,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000114',1,2,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000115',1,4,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000116',1,0,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000117',1,4,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000118',1,4,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000119',1,0,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000120',1,2,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000121',1,4,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000123',1,8,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000124',1,0,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000126',1,6,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000127',1,0,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000128',1,0,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000129',1,4,2,'RIN 16 PCR','2026-05-28 02:32:34'),('NEU-000131',1,0,2,'RIN 16 TBR','2026-05-28 02:32:34'),('NEU-000132',1,4,2,'RIN 16 TBR','2026-05-28 02:32:34'),('NEU-000133',1,0,2,'RIN 16 TBR','2026-05-28 02:32:34'),('NEU-000134',1,1,2,'RIN 16 TBR','2026-05-28 02:32:34'),('NEU-000135',1,24,2,'RIN 16 TBR','2026-05-28 02:32:34'),('NEU-000136',1,40,2,'RIN 16 TBR','2026-05-28 02:32:34'),('NEU-000137',1,11,2,'RIN 16 TBR','2026-05-28 02:32:34'),('NEU-000139',1,6,2,'RIN 17 PCR','2026-05-28 02:32:34'),('NEU-000140',1,0,2,'RIN 17 PCR','2026-05-28 02:32:34'),('NEU-000141',1,2,2,'RIN 17 PCR','2026-05-28 02:32:34'),('NEU-000145',1,0,2,'RIN 17 PCR','2026-05-28 02:32:34'),('NEU-000146',1,6,2,'RIN 17 PCR','2026-05-28 02:32:34'),('NEU-000147',1,3,2,'RIN 17 PCR','2026-05-28 02:32:34'),('NEU-000150',1,2,2,'RIN 17 PCR','2026-05-28 02:32:34'),('NEU-000151',1,8,2,'RIN 17 PCR','2026-05-28 02:32:34'),('NEU-000152',1,0,2,'RIN 17 PCR','2026-05-28 02:32:34'),('NEU-000153',1,2,2,'RIN 17 PCR','2026-05-28 02:32:34'),('NEU-000154',1,4,2,'RIN 17 PCR','2026-05-28 02:32:34'),('NEU-000155',1,4,2,'RIN 17 PCR','2026-05-28 02:32:34'),('NEU-000157',1,0,2,'RIN 17 PCR','2026-05-28 02:32:34'),('NEU-000158',1,0,2,'RIN 17 PCR','2026-05-28 02:32:34'),('NEU-000159',1,0,2,'RIN 17 PCR','2026-05-28 02:32:34'),('NEU-000160',1,0,2,'RIN 17 PCR','2026-05-28 02:32:34'),('NEU-000161',1,4,2,'RIN 17 PCR','2026-05-28 02:32:34'),('NEU-000162',1,4,2,'RIN 17 PCR','2026-05-28 02:32:34'),('NEU-000165',1,0,2,'RIN 17.5 TBR','2026-05-28 02:32:34'),('NEU-000166',1,0,2,'RIN 17.5 TBR','2026-05-28 02:32:34'),('NEU-000167',1,2,2,'RIN 17.5 TBR','2026-05-28 02:32:34'),('NEU-000169',1,0,2,'RIN 18 PCR','2026-05-28 02:32:34'),('NEU-000170',1,0,2,'RIN 18 PCR','2026-05-28 02:32:34'),('NEU-000171',1,0,2,'RIN 18 PCR','2026-05-28 02:32:34'),('NEU-000172',1,0,2,'RIN 18 PCR','2026-05-28 02:32:34'),('NEU-000174',1,8,2,'RIN 18 PCR','2026-05-28 02:32:34'),('NEU-000175',1,2,2,'RIN 18 PCR','2026-05-28 02:32:34'),('NEU-000176',1,0,2,'RIN 18 PCR','2026-05-28 02:32:34'),('NEU-000178',1,2,2,'RIN 20 PCR','2026-05-28 02:32:34'),('NEU-000179',1,0,2,'RIN 20 PCR','2026-05-28 02:32:34'),('NEU-000181',1,0,2,'RIN 20 PCR','2026-05-28 02:32:34'),('NEU-000182',1,200,2,'RIN 20 PCR','2026-05-28 02:32:34'),('NEU-000184',1,1,2,'RIN 22.5 TBR','2026-05-28 02:32:34'),('NEU-000185',1,0,2,'RIN 22.5 TBR','2026-05-28 02:32:34'),('NEU-000186',1,0,2,'RIN 22.5 TBR','2026-05-28 02:32:34'),('NEU-000187',1,0,2,'RIN 22.5 TBR','2026-05-28 02:32:34'),('NEU-000188',1,0,2,'RIN 22.5 TBR','2026-05-28 02:32:34'),('NEU-000190',1,0,2,'RIN 22.5 TBR','2026-05-28 02:32:34'),('NEU-000191',1,1,2,'RIN 22.5 TBR','2026-05-28 02:32:34'),('NEU-000192',1,0,2,'RIN 22.5 TBR','2026-05-28 02:32:34'),('NEU-000193',1,0,2,'RIN 22.5 TBR','2026-05-28 02:32:34'),('NEU-000194',1,0,2,'RIN 22.5 TBR','2026-05-28 02:32:34');
/*!40000 ALTER TABLE `stock` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_stock_update` AFTER UPDATE ON stock FOR EACH ROW BEGIN
        INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (COALESCE(@current_usuario_id, 1), 'MODIFICAR', 'INVENTARIO', CONCAT('Inventario modificado: ', NEW.producto_codigo, ' (nueva cantidad: ', NEW.stock, ')'), COALESCE(@current_ip, '127.0.0.1'));
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;


DROP TABLE IF EXISTS `sucursales`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sucursales` (
  `id_sucursal` int(11) NOT NULL AUTO_INCREMENT,
  `nombre_sucursal` varchar(200) NOT NULL,
  `direccion_sucursal` varchar(300) DEFAULT NULL,
  `telefono_sucursal` varchar(20) DEFAULT NULL,
  `email_sucursal` varchar(150) DEFAULT NULL,
  `estado` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_sucursal`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `sucursales` WRITE;
/*!40000 ALTER TABLE `sucursales` DISABLE KEYS */;
INSERT INTO `sucursales` VALUES (1,'Sede Principal','Av. Principal, Local 1','04240000000','principal@transalca.com',1,'2026-04-30 04:18:56'),(2,'Sucursal Norte','Calle Norte, Centro Comercial X','04241111111','norte@transalca.com',1,'2026-04-30 04:18:56');
/*!40000 ALTER TABLE `sucursales` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_sucursales_insert` AFTER INSERT ON sucursales FOR EACH ROW BEGIN
        INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (COALESCE(@current_usuario_id, 1), 'CREAR', 'SUCURSALES', CONCAT('Sucursal creada: ', NEW.nombre_sucursal), COALESCE(@current_ip, '127.0.0.1'));
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_sucursales_update` AFTER UPDATE ON sucursales FOR EACH ROW BEGIN
        IF OLD.estado = 1 AND NEW.estado = 0 THEN
            INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
            VALUES (COALESCE(@current_usuario_id, 1), 'ELIMINAR', 'SUCURSALES', CONCAT('Sucursal desactivada: ', NEW.id_sucursal), COALESCE(@current_ip, '127.0.0.1'));
        ELSE
            INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
            VALUES (COALESCE(@current_usuario_id, 1), 'MODIFICAR', 'SUCURSALES', CONCAT('Sucursal modificada: ', NEW.nombre_sucursal), COALESCE(@current_ip, '127.0.0.1'));
        END IF;
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;


DROP TABLE IF EXISTS `tarjeta_fidelidad`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tarjeta_fidelidad` (
  `id_tarjeta_fidelidad` int(11) NOT NULL AUTO_INCREMENT,
  `cliente_cedula` varchar(20) NOT NULL,
  `promocion_id` int(11) NOT NULL,
  `puntos_acumulados` int(11) DEFAULT 0,
  `canjeada` tinyint(1) DEFAULT 0,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_tarjeta_fidelidad`),
  KEY `cliente_cedula` (`cliente_cedula`),
  KEY `promocion_id` (`promocion_id`),
  CONSTRAINT `tarjeta_fidelidad_ibfk_1` FOREIGN KEY (`cliente_cedula`) REFERENCES `cliente` (`identificador_cliente`) ON UPDATE CASCADE,
  CONSTRAINT `tarjeta_fidelidad_ibfk_2` FOREIGN KEY (`promocion_id`) REFERENCES `promociones` (`id_promocion`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `tarjeta_fidelidad` WRITE;
/*!40000 ALTER TABLE `tarjeta_fidelidad` DISABLE KEYS */;
INSERT INTO `tarjeta_fidelidad` VALUES (2,'V-00000000',1,3,1,'2026-06-03 16:59:09'),(3,'30396029',1,0,0,'2026-06-08 08:13:32'),(15,'V-00000000',2,0,0,'2026-06-08 08:22:48'),(16,'V-00000000',4,0,0,'2026-06-08 08:22:48'),(17,'V-00000000',5,0,0,'2026-06-08 08:22:48'),(18,'V-00000000',1,0,0,'2026-06-08 08:22:48');
/*!40000 ALTER TABLE `tarjeta_fidelidad` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_tarjeta_fidelidad_insert` AFTER INSERT ON tarjeta_fidelidad FOR EACH ROW BEGIN
        INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (COALESCE(@current_usuario_id, 1), 'CREAR', 'PROMOCIONES', CONCAT('Tarjeta de fidelidad asignada a: ', NEW.cliente_cedula), COALESCE(@current_ip, '127.0.0.1'));
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_auto_canje_tarjeta` BEFORE UPDATE ON tarjeta_fidelidad FOR EACH ROW BEGIN
    DECLARE v_puntos_req INT DEFAULT 0;
    IF NEW.canjeada = 0 THEN
        SELECT puntos_requeridos INTO v_puntos_req FROM promociones WHERE id = NEW.promocion_id LIMIT 1;
        IF NEW.puntos_acumulados >= v_puntos_req THEN
            SET NEW.canjeada = 1;
        END IF;
    END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;


DROP TABLE IF EXISTS `tasas_cambio`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tasas_cambio` (
  `id_tasa_cambio` int(11) NOT NULL AUTO_INCREMENT,
  `fecha_tasa_cambio` date NOT NULL,
  `tipo_tasa_cambio` varchar(20) NOT NULL DEFAULT 'bcv',
  `monto` decimal(12,4) NOT NULL,
  `fuente` varchar(100) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_tasa_cambio`),
  KEY `idx_tasas_cambio_fecha_tipo` (`fecha_tasa_cambio`,`tipo_tasa_cambio`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `tasas_cambio` WRITE;
/*!40000 ALTER TABLE `tasas_cambio` DISABLE KEYS */;
INSERT INTO `tasas_cambio` VALUES (1,'2026-04-30','bcv',489.5547,'BCV automatico','2026-05-01 01:44:34'),(2,'2026-05-07','bcv',499.8608,'BCV automatico','2026-05-08 02:50:57'),(3,'2026-05-08','bcv',499.8608,'BCV automatico','2026-05-08 20:39:17'),(4,'2026-05-17','bcv',517.9619,'BCV automatico','2026-05-17 20:00:37'),(5,'2026-05-18','bcv',517.9619,'BCV automatico','2026-05-18 04:36:38'),(6,'2026-05-20','bcv',523.6750,'BCV automatico','2026-05-21 02:47:59'),(7,'2026-05-21','bcv',523.6750,'BCV automatico','2026-05-21 04:47:47'),(8,'2026-05-27','bcv',544.5794,'BCV automatico','2026-05-28 01:41:51'),(9,'2026-05-28','bcv',549.3716,'BCV automatico','2026-05-28 22:26:55'),(10,'2026-06-02','bcv',558.6436,'BCV automatico','2026-06-02 21:35:53'),(11,'2026-06-03','bcv',560.3753,'BCV automatico','2026-06-03 05:40:51'),(12,'2026-06-05','bcv',567.6828,'BCV automatico','2026-06-06 00:29:15'),(13,'2026-06-06','bcv',567.6828,'BCV automatico','2026-06-06 20:01:09'),(14,'2026-06-07','bcv',567.6828,'BCV automatico','2026-06-07 20:01:25'),(15,'2026-06-08','bcv',567.6828,'BCV automatico','2026-06-08 20:01:26'),(16,'2026-06-10','bcv',577.5461,'BCV automatico','2026-06-10 20:43:24');
/*!40000 ALTER TABLE `tasas_cambio` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_tasas_cambio_insert` AFTER INSERT ON tasas_cambio FOR EACH ROW BEGIN
        INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (COALESCE(@current_usuario_id, 1), 'CREAR', 'TASA_CAMBIO', CONCAT('Tasa de cambio creada ID: ', NEW.id_tasa_cambio), COALESCE(@current_ip, '127.0.0.1'));
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_tasas_cambio_update` AFTER UPDATE ON tasas_cambio FOR EACH ROW BEGIN
        INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (COALESCE(@current_usuario_id, 1), 'MODIFICAR', 'TASA_CAMBIO', CONCAT('Tasa de cambio modificada ID: ', NEW.id_tasa_cambio), COALESCE(@current_ip, '127.0.0.1'));
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;


DROP TABLE IF EXISTS `ticket_respuestas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ticket_respuestas` (
  `id_ticket_respuesta` int(11) NOT NULL AUTO_INCREMENT,
  `ticket_id` int(11) NOT NULL,
  `autor_id` int(11) NOT NULL,
  `autor_tipo` varchar(20) NOT NULL,
  `mensaje_ticket_respuesta` text NOT NULL,
  `adjunto_url` varchar(255) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_ticket_respuesta`),
  KEY `ticket_id` (`ticket_id`),
  CONSTRAINT `ticket_respuestas_ibfk_1` FOREIGN KEY (`ticket_id`) REFERENCES `tickets_soporte` (`id_ticket_soporte`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `ticket_respuestas` WRITE;
/*!40000 ALTER TABLE `ticket_respuestas` DISABLE KEYS */;
INSERT INTO `ticket_respuestas` VALUES (1,1,1,'admin','Hola!',NULL,'2026-05-01 01:38:25');
/*!40000 ALTER TABLE `ticket_respuestas` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_ticket_respuestas_insert` AFTER INSERT ON ticket_respuestas FOR EACH ROW BEGIN
        INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (COALESCE(@current_usuario_id, 1), 'CREAR', 'TICKETS', CONCAT('Respuesta a ticket registrada para ticket ID: ', NEW.ticket_id), COALESCE(@current_ip, '127.0.0.1'));
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;


DROP TABLE IF EXISTS `tickets_soporte`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tickets_soporte` (
  `id_ticket_soporte` int(11) NOT NULL AUTO_INCREMENT,
  `cliente_cedula` varchar(20) NOT NULL,
  `asunto` varchar(300) NOT NULL,
  `descripcion_ticket_soporte` text DEFAULT NULL,
  `estado` varchar(30) NOT NULL DEFAULT 'abierto',
  `prioridad_ticket` varchar(20) DEFAULT 'media',
  `referencia_tipo` varchar(20) NOT NULL DEFAULT 'general',
  `referencia_id` varchar(50) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id_ticket_soporte`),
  KEY `idx_ticket_cliente` (`cliente_cedula`),
  CONSTRAINT `tickets_soporte_ibfk_1` FOREIGN KEY (`cliente_cedula`) REFERENCES `cliente` (`identificador_cliente`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `tickets_soporte` WRITE;
/*!40000 ALTER TABLE `tickets_soporte` DISABLE KEYS */;
INSERT INTO `tickets_soporte` VALUES (1,'30396029','Cambio de caucho','dedede','abierto','critica','general',NULL,'2026-05-01 01:38:00','2026-05-01 01:38:00'),(2,'V-07224350','Necesito ayuda','Prueba ticket','cerrado','media','general',NULL,'2026-05-08 02:43:38','2026-05-17 15:30:37');
/*!40000 ALTER TABLE `tickets_soporte` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_tickets_soporte_insert` AFTER INSERT ON tickets_soporte FOR EACH ROW BEGIN
        INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (COALESCE(@current_usuario_id, 1), 'CREAR', 'TICKETS', CONCAT('Ticket creado ID: ', NEW.id_ticket_soporte), COALESCE(@current_ip, '127.0.0.1'));
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_tickets_soporte_update` AFTER UPDATE ON tickets_soporte FOR EACH ROW BEGIN
        INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (COALESCE(@current_usuario_id, 1), 'MODIFICAR', 'TICKETS', CONCAT('Ticket modificado ID: ', NEW.id_ticket_soporte), COALESCE(@current_ip, '127.0.0.1'));
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;


DROP TABLE IF EXISTS `vehiculos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `vehiculos` (
  `marca_vehiculo` varchar(100) NOT NULL,
  `modelo_vehiculo` varchar(100) NOT NULL,
  `anio_vehiculo` smallint(6) DEFAULT NULL,
  `placa_vehiculo` varchar(20) NOT NULL,
  `color_vehiculo` varchar(50) DEFAULT NULL,
  `tipo_vehiculo` varchar(50) DEFAULT NULL,
  `tipo_combustible` varchar(20) DEFAULT 'gasolina',
  `kilometraje_actual` int(11) DEFAULT 0,
  `aceite_info` varchar(200) DEFAULT NULL,
  `filtros_info` text DEFAULT NULL,
  `refrigerante_info` varchar(200) DEFAULT NULL,
  `observaciones_vehiculo` text DEFAULT NULL,
  `cauchos_vehiculo` longtext DEFAULT NULL,
  `titulo_vehiculo` varchar(255) DEFAULT NULL,
  `estado` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`placa_vehiculo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `vehiculos` WRITE;
/*!40000 ALTER TABLE `vehiculos` DISABLE KEYS */;
INSERT INTO `vehiculos` VALUES ('Toyota','Corolla',2012,'AB123CD','Gris Plata','Sedan','gasolina',0,'','','','',NULL,'carnet_1_1777597493861.png',1,'2026-05-01 01:04:53','2026-05-01 01:04:53'),('Toyota','Corolla',2012,'AB4338CD','Gris','Sedan','gasolina',120000,'','','','',NULL,NULL,1,'2026-05-08 02:43:38','2026-05-08 02:43:38'),('fewsfesf','fsfsfs',1999,'DADADA','afafa','dadada','gasolina',3333,'','','','',NULL,NULL,1,'2026-06-10 22:24:01','2026-06-10 22:24:01'),('fsfsfs','fsfssf',1988,'DEDED','dede','dede','gasolina',22222,'','','','',NULL,NULL,1,'2026-06-10 22:24:32','2026-06-10 22:24:32');
/*!40000 ALTER TABLE `vehiculos` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_vehiculos_insert` AFTER INSERT ON vehiculos FOR EACH ROW BEGIN
        INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
        VALUES (COALESCE(@current_usuario_id, 1), 'CREAR', 'VEHICULOS', CONCAT('Vehiculo registrado placa: ', NEW.placa_vehiculo), COALESCE(@current_ip, '127.0.0.1'));
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_bitacora_vehiculos_update` AFTER UPDATE ON vehiculos FOR EACH ROW BEGIN
        IF OLD.estado = 1 AND NEW.estado = 0 THEN
            INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
            VALUES (COALESCE(@current_usuario_id, 1), 'ELIMINAR', 'VEHICULOS', CONCAT('Vehiculo desactivado placa: ', NEW.placa_vehiculo), COALESCE(@current_ip, '127.0.0.1'));
        ELSE
            INSERT INTO db_mantenimiento.bitacora (usuario_id, accion, modulo, descripcion, ip)
            VALUES (COALESCE(@current_usuario_id, 1), 'MODIFICAR', 'VEHICULOS', CONCAT('Vehiculo modificado placa: ', NEW.placa_vehiculo), COALESCE(@current_ip, '127.0.0.1'));
        END IF;
    END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
/*!50003 DROP FUNCTION IF EXISTS `fn_calcular_total_orden` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` FUNCTION `fn_calcular_total_orden`(p_orden_id INT, p_tipo VARCHAR(10)) RETURNS decimal(12,2)
    DETERMINISTIC
BEGIN
            DECLARE v_total DECIMAL(12,2) DEFAULT 0.00;
            SELECT COALESCE((SELECT SUM(cantidad_detalle_orden_venta_producto * precio_unitario_producto) FROM detalle_orden_venta_productos WHERE orden_id = p_orden_id),0)
                 + COALESCE((SELECT SUM(cantidad_detalle_orden_venta_servicio * precio_unitario_servicio) FROM detalle_orden_venta_servicios WHERE orden_id = p_orden_id),0)
            INTO v_total;
            RETURN v_total;
        END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_AUTO_VALUE_ON_ZERO' */ ;
/*!50003 DROP FUNCTION IF EXISTS `fn_stock_disponible` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` FUNCTION `fn_stock_disponible`(`p_producto_codigo` VARCHAR(50), `p_sucursal_id` INT) RETURNS int(11)
    DETERMINISTIC
BEGIN
            DECLARE v_stock INT DEFAULT 0;
            IF p_sucursal_id IS NULL THEN
                SELECT COALESCE(SUM(stock), 0) INTO v_stock FROM stock WHERE producto_codigo = p_producto_codigo;
            ELSE
                SELECT COALESCE(stock, 0) INTO v_stock FROM stock WHERE producto_codigo = p_producto_codigo AND sucursal_id = p_sucursal_id;
            END IF;
            RETURN v_stock;
        END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
DROP VIEW IF EXISTS `vw_reporte_pagos`;
CREATE VIEW `vw_reporte_pagos` AS
SELECT cp.id_comprobante_pago AS id, ov.cliente_cedula, cp.orden_venta_id AS orden_id,
  CONCAT('IMG-', cp.id_comprobante_pago) AS referencia,
  ov.total_orden_venta AS monto, COALESCE(mp.moneda, 'USD') AS moneda,
  mp.nombre_metodo_pago AS metodo,
  cp.fecha_comprobante AS fecha_ts,
  DATE_FORMAT(cp.fecha_comprobante, '%Y-%m-%dT%H:%i:%s') AS fecha,
  cp.estado,
  c.nombre_cliente AS nombre, '' AS apellido, c.tipo_cliente, c.nombre_cliente AS razon_social
FROM comprobantes_pago cp
INNER JOIN ordenes_venta ov ON cp.orden_venta_id = ov.id_orden_venta
LEFT JOIN metodos_pago mp ON mp.id_metodo_pago = ov.metodo_pago_id
LEFT JOIN cliente c ON ov.cliente_cedula = c.identificador_cliente;

DROP VIEW IF EXISTS `vw_reporte_ventas`;
CREATE VIEW `vw_reporte_ventas` AS
SELECT ov.id_orden_venta AS id, ov.cliente_cedula,
  ov.fecha_orden_venta AS fecha_ts,
  DATE_FORMAT(ov.fecha_orden_venta, '%Y-%m-%dT%H:%i:%s') AS fecha,
  ov.total_orden_venta AS total, ov.estado,
  c.nombre_cliente AS nombre, '' AS apellido, c.tipo_cliente, c.nombre_cliente AS razon_social
FROM ordenes_venta ov
LEFT JOIN cliente c ON ov.cliente_cedula = c.identificador_cliente;

DROP VIEW IF EXISTS `vw_stock_detalle`;
CREATE VIEW `vw_stock_detalle` AS
SELECT i.*, p.nombre_producto AS producto_nombre, p.codigo, p.precio_producto AS precio,
  p.categoria AS categoria_nombre, s.nombre_sucursal AS sucursal_nombre, i.ubicacion_stock AS ubicacion
FROM stock i
INNER JOIN productos p ON i.producto_codigo = p.codigo
LEFT JOIN sucursales s ON i.sucursal_id = s.id_sucursal;

DROP PROCEDURE IF EXISTS `sp_aprobar_pago`;
DELIMITER ;;
CREATE PROCEDURE `sp_aprobar_pago`(IN p_comprobante_id INT)
BEGIN
    DECLARE v_orden INT DEFAULT NULL;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
    START TRANSACTION;
    SELECT orden_venta_id INTO v_orden FROM comprobantes_pago WHERE id_comprobante_pago = p_comprobante_id;
    UPDATE comprobantes_pago SET estado = 'verificado' WHERE id_comprobante_pago = p_comprobante_id;
    UPDATE ordenes_venta SET estado = 'aprobada' WHERE id_orden_venta = v_orden;
    UPDATE solicitudes_validacion sv INNER JOIN comprobantes_pago cp ON cp.id_comprobante_pago = sv.comprobante_pago_id
      SET sv.estado_validacion = 'aprobada' WHERE sv.estado_validacion = 'pendiente' AND cp.orden_venta_id = v_orden;
    COMMIT;
END ;;
DELIMITER ;

DROP PROCEDURE IF EXISTS `sp_rechazar_pago`;
DELIMITER ;;
CREATE PROCEDURE `sp_rechazar_pago`(IN p_comprobante_id INT, IN p_observaciones VARCHAR(500))
BEGIN
    DECLARE v_orden INT DEFAULT NULL;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
    START TRANSACTION;
    SELECT orden_venta_id INTO v_orden FROM comprobantes_pago WHERE id_comprobante_pago = p_comprobante_id;
    UPDATE comprobantes_pago SET estado = 'rechazado', observaciones = p_observaciones WHERE id_comprobante_pago = p_comprobante_id;
    UPDATE ordenes_venta SET estado = 'rechazada' WHERE id_orden_venta = v_orden;
    UPDATE solicitudes_validacion sv INNER JOIN comprobantes_pago cp ON cp.id_comprobante_pago = sv.comprobante_pago_id
      SET sv.estado_validacion = 'rechazada' WHERE sv.estado_validacion = 'pendiente' AND cp.orden_venta_id = v_orden;
    COMMIT;
END ;;
DELIMITER ;

/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
