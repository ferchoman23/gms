from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime
import logging
_logger = logging.getLogger(__name__)


class Viajes(models.Model):
    _name = 'gms.viaje'
    _description = 'Viaje'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    follower_ids = fields.Many2many('res.users', string='Followers')

    name = fields.Char(
    'Name', default=lambda self: _('New'),
    copy=False, readonly=True, tracking=True)

    agenda = fields.Many2one('gms.agenda', string='Agenda', tracking="1" )

    agenda_count = fields.Integer(string="Número de Agendas", compute="_compute_agenda_count")

    @api.depends('agenda')
    def _compute_agenda_count(self):
        for record in self:
            record.agenda_count = 1 if record.agenda else 0

    def action_view_agenda(self):
        self.ensure_one() 
        if self.agenda:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'gms.agenda',
                'view_mode': 'form',
                'res_id': self.agenda.id,
                'target': 'current',
            }
        else:
            raise UserError('No hay una agenda asociada a este viaje.')

    fecha_viaje = fields.Date(string='Fecha de viaje', tracking="1")

    origen = fields.Many2one('res.partner', 
                             string='Origen', 
                             tracking="1", 
                             domain="['&',('tipo', '!=', False),('parent_id','=',solicitante_id)]")
    
    destino = fields.Many2one('res.partner', string='Destino', tracking="1")

    camion_disponible_id = fields.Many2one('gms.camiones.disponibilidad', string='Camión Disponible', tracking="1")

    camion_id = fields.Many2one('gms.camiones', string='Camion', required=True , tracking="1")

    conductor_id = fields.Many2one('res.partner', string='Chofer', compute="_compute_conductor_transportista", tracking="1")

    solicitante_id = fields.Many2one('res.partner', string='Solicitante', tracking="1")
    
    # nuevos campos 
    tipo_viaje = fields.Selection([('entrada', 'Entrada'), ('salida', 'Salida')], string="Tipo de Viaje", tracking="1")

    numero_remito = fields.Char(string="Número de remito / Guía", tracking="1")
    
    transportista_id = fields.Many2one('res.partner', string="Transportista", compute="_compute_conductor_transportista", tracking="1")

    ruta_id = fields.Many2one('gms.rutas', 
                          string="Ruta", 
                          domain="[('direccion_origen_id', '=', origen),('direccion_destino_id', '=', destino)]",
                          tracking="1")

    albaran_id = fields.Many2one('stock.picking', string="Albarán", tracking="1")

    producto_transportado_id = fields.Many2one('product.product', string="Producto transportado", tracking="1")

    peso_bruto = fields.Float(string="Peso bruto", tracking="1")

    tara = fields.Float(string="Tara", tracking="1")

    peso_neto = fields.Float(string="Peso neto", compute="_compute_peso_neto", tracking="1",store=True)
    
    estado = fields.Char(string = "s")

    peso_neto_destino = fields.Float(string="Peso neto destino", tracking="1")

    peso_producto_seco = fields.Float(string="Peso producto seco", tracking="1")

    porcentaje_humedad_primer_muestra = fields.Float(string="Porcentaje humedad primer muestra", tracking="1")

    tolva_id = fields.Many2one('gms.tolva', string='Tolva', tracking="1")

    silo_id = fields.Many2one('stock.location', string="Silio", domain=[('usage', '=', 'internal')], tracking="1")

    prelimpieza_entrada = fields.Boolean(string="Prelimpieza Entrada", tracking=True)
    secado_entrada = fields.Boolean(string="Secado Entrada", tracking=True)

    kilometros_flete = fields.Float(string="Kilómetros flete", tracking="1")

    kilogramos_a_liquidar = fields.Float(string="Kilogramos a liquidar", compute="_compute_kilogramos_a_liquidar", store=True, tracking=True)

    pedido_venta_id = fields.Many2one('sale.order', string="Pedido de venta", tracking="1", readonly=True)

    pedido_compra_id = fields.Many2one('purchase.order', string="Pedido de compra", tracking="1", readonly=True)

    observaciones = fields.Text(string="Observaciones", tracking="1")

    albaran_count = fields.Integer(string="Número de Albaranes", compute="_compute_albaran_count")

    albaran_id = fields.Many2one('stock.picking', string="Albarán")

    purchase_order_id= fields.Many2one('purchase.order')

    medidas_propiedades_ids = fields.One2many('gms.medida.propiedad', 'viaje_id', string='Medidas de Propiedades')

    arribo = fields.Datetime(string="Arribo")
    partida = fields.Datetime(string="Partida")

    chacra = fields.Char(string='Chacra', tracking="1")
    remito = fields.Float(string='Remito', tracking="1")

    # prelimpieza_entrada_1 = fields.Selection([('si', 'Si'), ('no', 'No')], string="Prelimpieza entrada", tracking="1")

    # secado_entrada_1 = fields.Selection([('si', 'Si'), ('no', 'No')], string="Secado entrada", tracking="1")

    

    def write(self, vals):
        for record in self:
            if vals.get('state') == 'terminado' and 'partida' not in vals:
                vals['partida'] = fields.Datetime.now()
        return super(Viajes, self).write(vals)


   
    def _compute_albaran_count(self):
        for record in self:
            record.albaran_count = 1 if record.albaran_id else 0



    @api.onchange('camion_id')
    def _compute_conductor_transportista(self):
        for viaje in self:
            if viaje.camion_id:
                viaje.conductor_id = viaje.camion_id.conductor_id.id
                viaje.transportista_id = viaje.camion_id.transportista_id.id
                

    @api.depends('peso_bruto', 'tara')
    def _compute_peso_neto(self):
        for record in self:
            record.peso_neto = record.peso_bruto - record.tara



    @api.onchange('ruta_id')
    def _onchange_ruta_id(self):
         if self.ruta_id:   
             self.kilometros_flete = self.ruta_id.kilometros



    state = fields.Selection([
        ('cancelado', 'Cancelado'),
        ('borrador', 'Borrador'),
        ('coordinado', 'Coordinado'),
        ('proceso', 'Proceso'),
        ('terminado', 'Terminado'),
        ('liquidado', 'Liquidado')
    ], string='Estado', default='borrador', required=True)


    gastos_ids = fields.One2many('gms.gasto_viaje', 'viaje_id', string='Gastos')


    def action_proceso(self):
        self.write({'state': 'proceso'})


    def action_cancel(self):
        self.write({'state': 'cancelado'})

    def action_terminado(self):
        self.write({'state': 'terminado'})

        # Guarda la fecha y hora actual
        fecha_hora_actual = fields.Datetime.now()

        # Busca el registro en gms.historial que tenga la misma agenda_id que el nombre del viaje
        historial = self.env['gms.historial'].search([('agenda_id.name', '=', self.name)], limit=1)

        if historial:
            # Actualiza la fecha_hora_liberacion en el registro existente
            historial.write({'fecha_hora_liberacion': fecha_hora_actual})

        # Recupera el camión asociado a este viaje (si existe)
        camion_id = self.camion_disponible_id.camion_id.id if self.camion_disponible_id else False

         # Actualiza el estado del camión a 'disponible' si existe
        self.camion_disponible_id.estado = "disponible"
        self.camion_disponible_id.fecha_hora_liberacion = fecha_hora_actual
        

        # # Buscar la ubicación 'Partners/Vendors'
        # location_supplier_id = self.env['stock.location'].search([('usage', '=', 'supplier')], limit=1).id

        # # Buscar la ubicación 'Partners/Customers'
        # location_customer_id = self.env['stock.location'].search([('usage', '=', 'customer')], limit=1).id

        # if not location_supplier_id or not location_customer_id:
        #     raise UserError("No se encontraron las ubicaciones necesarias para crear el albarán.")

        # if self.tipo_viaje == 'entrada':
        #     location_id = location_supplier_id
        #     location_dest_id = self.silo_id.id  
        #     owner = self.solicitante_id

        #     # Buscar el tipo de operación "recepción" con el silo correspondiente
        #     picking_type = self.env['stock.picking.type'].search([
        #         ('code', '=', 'incoming'),
        #         ('default_location_dest_id', '=', self.silo_id.id)
        #     ], limit=1)
        # else:  # salida
        #     location_id = self.silo_id.id
        #     location_dest_id = location_customer_id

        #     # Buscar el tipo de operación "entrega" con el silo correspondiente
        #     picking_type = self.env['stock.picking.type'].search([
        #         ('code', '=', 'outgoing'),
        #         ('default_location_src_id', '=', self.silo_id.id)
        #     ], limit=1)

        # if not picking_type:
        #     raise UserError("No se encontró el tipo de operación necesario para crear el albarán.")

        # # Crear el albarán
        # picking_vals = {
        #     'location_id': location_id,
        #     'location_dest_id': location_dest_id,
        #     'origin': self.name,
        #     'picking_type_id': picking_type.id,
        #     'owner_id': owner.id if self.tipo_viaje == 'entrada' else False
        # }   

        # picking = self.env['stock.picking'].create(picking_vals)

        # # Agregar las líneas al albarán
        # picking.move_ids_without_package = [(0, 0, {
        #     'name': self.producto_transportado_id.name,
        #     'product_id': self.producto_transportado_id.id,
        #     'product_uom_qty': self.kilogramos_a_liquidar,
        #     'product_uom': self.producto_transportado_id.uom_id.id,
        #     'location_id': location_id,
        #     'location_dest_id': location_dest_id,
        # })]

        # self.albaran_id = picking


                
    def action_liquidado(self):
        self.write({'state': 'liquidado'})  
        
    def action_coordinado(self):
        self.write({'state': 'coordinado'})

    def action_borrador(self):
        self.write({'state': 'borrador'})

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('gms.viaje')
        record = super().create(vals)

        if record.agenda:
            record.message_post(body="Este viaje fue creado desde una agenda.",subtype_xmlid="mail.mt_note")

        return record
       


    def action_view_picking(self):
        self.ensure_one() 
        if self.albaran_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'view_mode': 'form',
                'res_id': self.albaran_id.id,
                'target': 'current',
            }
        else:
            raise UserError('No hay un albarán asociado a este viaje.')
    


    def action_generate_purchase_order(self):
        PurchaseOrder = self.env['purchase.order']

        # Agrupa los viajes por transportista
        grouped_trips_by_transportista = {}
        for trip in self:
            if trip.transportista_id not in grouped_trips_by_transportista:
                grouped_trips_by_transportista[trip.transportista_id] = []
            grouped_trips_by_transportista[trip.transportista_id].append(trip)

        # Por cada transportista, crea una orden de compra
        for transportista, trips in grouped_trips_by_transportista.items():
            po_vals = {
                'partner_id': transportista.id,
                'order_line': [],
            }

            # Guarda una relación entre gastos y líneas de compra
            gastos_and_po_lines = {}

            for trip in trips:
                for gasto in trip.gastos_ids:
                    if gasto.estado_compra == 'no_comprado':
                        po_line_vals = {
                            'product_id': gasto.producto_id.id,
                            'name': gasto.name or gasto.producto_id.name,
                            'product_qty': 1,
                            'price_unit': gasto.precio_total,
                            'product_uom': gasto.producto_id.uom_id.id,
                            'date_planned': fields.Date.today(),
                        }
                        po_vals['order_line'].append((0, 0, po_line_vals))
                        # Asociar el gasto con esta línea de orden de compra
                        gastos_and_po_lines[gasto] = po_line_vals

            if po_vals['order_line']:
                purchase_order = PurchaseOrder.create(po_vals)
                for trip in trips:
                    for gasto in trip.gastos_ids:
                        if gasto.estado_compra == 'no_comprado':
                            gasto.write({
                                'purchase_order_id': purchase_order.id,
                                'estado_compra': 'comprado'
                            })

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }



    



    @api.onchange('kilogramos_a_liquidar')
    def _onchange_kilogramos_a_liquidar(self):
        if self.albaran_id:
            # Obtener la primera línea del albarán (esto podría cambiar si hay múltiples líneas)
            move_line = self.albaran_id.move_ids_without_package[0]
            # Actualizar la demanda (product_uom_qty) de esa línea
            move_line.write({
                'quantity_done': self.kilogramos_a_liquidar
            })
        else:
            raise UserError('Este viaje no tiene un albarán asociado.')
        




   
    @api.depends('peso_neto', 'medidas_propiedades_ids.merma_kg')
    def _compute_kilogramos_a_liquidar(self):
        for record in self:
            _logger.info("Calculando kilogramos a liquidar para el viaje %s", record.name)
            _logger.info("Peso Neto: %s", record.peso_neto)
            
            total_mermas = sum(record.medidas_propiedades_ids.mapped('merma_kg'))
            _logger.info("Total Mermas: %s", total_mermas)
            
            record.kilogramos_a_liquidar = record.peso_neto - total_mermas
            _logger.info("Kilogramos a Liquidar Calculados: %s", record.kilogramos_a_liquidar)





    @api.onchange('ruta_id')
    def _onchange_ruta_id(self):
        # Encuentra y elimina la línea antigua si existe
        gastos_a_eliminar = self.gastos_ids.filtered(lambda g: g.es_de_ruta)
        self.gastos_ids -= gastos_a_eliminar

        if self.ruta_id:
            producto = self.ruta_id.gasto_viaje_id
            # Crear la nueva línea
            nuevo_gasto = {
                'name': 'Flete',
                'producto_id': producto.id,  # Asigna el ID del producto
                'proveedor_id': self.transportista_id.id,
                'estado_compra': 'no_comprado',
                'precio_total': producto.standard_price * self.ruta_id.kilometros,  # Accede directamente al precio estándar
                'es_de_ruta': True,
            }
            self.gastos_ids |= self.gastos_ids.new(nuevo_gasto)
 