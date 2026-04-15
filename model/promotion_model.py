from model.connection import Connection


class PromotionModel(Connection):
    def __init__(self):
        super().__init__()

    def get_all(self):
        return self.fetch_all("transalca", "SELECT * FROM promociones ORDER BY id DESC")

    def get_active(self):
        return self.fetch_all("transalca",
            "SELECT * FROM promociones WHERE estado = 1 AND (fecha_fin IS NULL OR fecha_fin >= CURDATE()) ORDER BY nombre")

    def get_by_id(self, promo_id):
        return self.fetch_one("transalca", "SELECT * FROM promociones WHERE id = %s", (promo_id,))

    def create(self, data):
        return self.insert("transalca",
            "INSERT INTO promociones (nombre, descripcion, tipo, puntos_requeridos, recompensa, imagen_tarjeta, fecha_inicio, fecha_fin) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (data['nombre'], data.get('descripcion', ''), data.get('tipo', 'puntos'),
             data.get('puntos_requeridos', 3), data.get('recompensa', ''),
             data.get('imagen_tarjeta', 'default_card.png'),
             data.get('fecha_inicio'), data.get('fecha_fin')))

    def update_promotion(self, promo_id, data):
        return self.update("transalca",
            "UPDATE promociones SET nombre = %s, descripcion = %s, tipo = %s, puntos_requeridos = %s, recompensa = %s, fecha_inicio = %s, fecha_fin = %s WHERE id = %s",
            (data['nombre'], data.get('descripcion', ''), data.get('tipo', 'puntos'),
             data.get('puntos_requeridos', 3), data.get('recompensa', ''),
             data.get('fecha_inicio'), data.get('fecha_fin'), promo_id))

    def update_image(self, promo_id, filename):
        return self.update("transalca",
            "UPDATE promociones SET imagen_tarjeta = %s WHERE id = %s", (filename, promo_id))

    def delete_promotion(self, promo_id):
        return self.update("transalca",
            "UPDATE promociones SET estado = 0 WHERE id = %s", (promo_id,))

    def soft_delete(self, promo_id):
        return self.delete_promotion(promo_id)

    def assign_card_to_client(self, cliente_cedula, promocion_id):
        existing = self.fetch_one("transalca",
            "SELECT id FROM tarjeta_fidelidad WHERE cliente_cedula = %s AND promocion_id = %s AND canjeada = 0",
            (cliente_cedula, promocion_id))
        if existing:
            return existing['id']
        return self.insert("transalca",
            "INSERT INTO tarjeta_fidelidad (cliente_cedula, promocion_id) VALUES (%s, %s)",
            (cliente_cedula, promocion_id))

    def get_client_cards(self, cliente_cedula):
        cards = self.fetch_all("transalca",
            "SELECT tf.*, p.nombre as promo_nombre, p.descripcion as promo_descripcion, p.puntos_requeridos, p.recompensa, p.imagen_tarjeta, p.tipo FROM tarjeta_fidelidad tf INNER JOIN promociones p ON tf.promocion_id = p.id WHERE tf.cliente_cedula = %s ORDER BY tf.fecha_creacion DESC",
            (cliente_cedula,))
        return cards

    def add_point(self, tarjeta_id, descripcion=''):
        card = self.fetch_one("transalca",
            "SELECT tf.*, p.puntos_requeridos FROM tarjeta_fidelidad tf INNER JOIN promociones p ON tf.promocion_id = p.id WHERE tf.id = %s",
            (tarjeta_id,))
        if not card or card['canjeada']:
            return None
        new_points = card['puntos_acumulados'] + 1
        canjeada = 1 if new_points >= card['puntos_requeridos'] else 0
        self.update("transalca",
            "UPDATE tarjeta_fidelidad SET puntos_acumulados = %s, canjeada = %s WHERE id = %s",
            (new_points, canjeada, tarjeta_id))
        self.insert("transalca",
            "INSERT INTO historial_puntos (tarjeta_id, puntos, tipo, descripcion) VALUES (%s, 1, 'suma', %s)",
            (tarjeta_id, descripcion))
        return {"puntos_acumulados": new_points, "canjeada": canjeada}

    def get_card_history(self, tarjeta_id):
        return self.fetch_all("transalca",
            "SELECT * FROM historial_puntos WHERE tarjeta_id = %s ORDER BY fecha DESC",
            (tarjeta_id,))

    def get_all_cards(self):
        cards = self.fetch_all("transalca",
            "SELECT tf.*, p.nombre as promo_nombre, p.descripcion as promo_descripcion, p.puntos_requeridos, p.recompensa, p.imagen_tarjeta, p.tipo FROM tarjeta_fidelidad tf INNER JOIN promociones p ON tf.promocion_id = p.id ORDER BY tf.fecha_creacion DESC")
        for card in cards:
            client = self.fetch_one("mantenimiento",
                "SELECT nombre, apellido, cedula FROM usuarios WHERE cedula = %s", (card['cliente_cedula'],))
            if client:
                card['cliente_nombre'] = f"{client['nombre']} {client['apellido']}"
                card['cliente_cedula_display'] = client['cedula']
        return cards

    def get_card_by_id(self, card_id):
        card = self.fetch_one("transalca",
            "SELECT tf.*, p.nombre as promo_nombre, p.descripcion as promo_descripcion, p.puntos_requeridos, p.recompensa, p.imagen_tarjeta, p.tipo FROM tarjeta_fidelidad tf INNER JOIN promociones p ON tf.promocion_id = p.id WHERE tf.id = %s",
            (card_id,))
        if card:
            client = self.fetch_one("mantenimiento",
                "SELECT nombre, apellido, cedula, email, telefono FROM usuarios WHERE cedula = %s", (card['cliente_cedula'],))
            if client:
                card.update(client)
        return card
